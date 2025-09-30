from typing import Annotated, Literal, Dict, Any, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from app.config import settings
from app.core.llm_factory import llm_factory
from app.session.session_manager import session_manager
from app.utils.logger import get_logger
from app.agents.academic_agent import AcademicAgent
from app.agents.financial_agent import FinancialAgent
from app.agents.policies_agent import PoliciesAgent
from app.agents.calendar_agent import CalendarAgent
import json

logger = get_logger(__name__)

class AgentState(TypedDict):
    """Estado compartido entre todos los agentes"""
    messages: Annotated[List[BaseMessage], add_messages]
    next: str
    user_info: Dict[str, Any]
    session_id: str
    agent_scratchpad: Dict[str, Any]
    escalation_requested: bool
    confidence_score: float

class SupervisorAgent:
    """Supervisor LangGraph que orquesta agentes especializados"""

    def __init__(self):
        # Usar LLM factory con abstracción completa
        self.llm = llm_factory.create_for_agent("supervisor")

        # Inicializar agentes especializados
        self.agents = {
            "academic": AcademicAgent(),
            "financial": FinancialAgent(),
            "policies": PoliciesAgent(),
            "calendar": CalendarAgent()
        }

        # Checkpointing para persistencia (compatible con LangGraph v1)
        memory = SqliteSaver.from_conn_string(":memory:")

        # Construir el grafo
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=memory)

    def _build_workflow(self) -> StateGraph:
        """Construye el workflow LangGraph"""

        workflow = StateGraph(AgentState)

        # Nodos principales
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("authentication", self._authentication_node)
        workflow.add_node("academic", self._academic_node)
        workflow.add_node("financial", self._financial_node)
        workflow.add_node("policies", self._policies_node)
        workflow.add_node("calendar", self._calendar_node)
        workflow.add_node("escalation", self._escalation_node)

        # Punto de entrada
        workflow.add_edge(START, "authentication")

        # Flujo de autenticación
        workflow.add_conditional_edges(
            "authentication",
            self._should_authenticate,
            {
                "supervisor": "supervisor",
                "authentication": "authentication",
                "END": END
            }
        )

        # Supervisor decide el siguiente agente
        workflow.add_conditional_edges(
            "supervisor",
            self._route_to_agent,
            {
                "academic": "academic",
                "financial": "financial",
                "policies": "policies",
                "calendar": "calendar",
                "escalation": "escalation",
                "END": END
            }
        )

        # Todos los agentes regresan al supervisor
        for agent in ["academic", "financial", "policies", "calendar"]:
            workflow.add_conditional_edges(
                agent,
                self._should_continue,
                {
                    "supervisor": "supervisor",
                    "escalation": "escalation",
                    "END": END
                }
            )

        # Escalación termina la conversación
        workflow.add_edge("escalation", END)

        return workflow

    async def _authentication_node(self, state: AgentState) -> AgentState:
        """Nodo de autenticación"""
        session_id = state["session_id"]

        # Verificar si ya está autenticado
        if session_manager.is_authenticated(session_id):
            user = session_manager.get_user(session_id)
            state["user_info"] = {
                "id": user.id,
                "nombre": user.nombre,
                "legajo": user.legajo,
                "tipo": user.tipo
            }
            state["next"] = "supervisor"
            return state

        # Proceso de autenticación por DNI
        last_message = state["messages"][-1].content if state["messages"] else ""

        # Buscar DNI en el mensaje
        import re
        dni_pattern = r'\b\d{8}\b'
        dni_match = re.search(dni_pattern, last_message)

        if dni_match:
            dni = dni_match.group()
            # Simular autenticación (aquí iría la integración real)
            user = await self._authenticate_user(dni)

            if user:
                session_manager.authenticate_user(session_id, user)
                state["user_info"] = {
                    "id": user.id,
                    "nombre": user.nombre,
                    "legajo": user.legajo,
                    "tipo": user.tipo
                }

                response = f"¡Perfecto, {user.nombre}! 😊 Ya te reconocí.\n\n¿En qué te puedo ayudar hoy?"
                state["messages"].append(AIMessage(content=response))
                state["next"] = "supervisor"
            else:
                response = "Lo siento, no reconozco ese DNI en nuestra base de datos. 😅\n\nPor favor verificá el número."
                state["messages"].append(AIMessage(content=response))
                state["next"] = "authentication"
        else:
            response = "¡Hola! 👋 Para ayudarte necesito que me pases tu DNI (solo números)."
            state["messages"].append(AIMessage(content=response))
            state["next"] = "authentication"

        return state

    async def _supervisor_node(self, state: AgentState) -> AgentState:
        """Nodo supervisor que decide la estrategia"""

        system_prompt = """Eres el supervisor de un sistema de agentes para la Universidad Austral.

        Tu rol es analizar la consulta del usuario y decidir qué agente especializado debe manejarla:

        - academic: Consultas sobre horarios, materias, profesores, aulas
        - financial: Consultas sobre estado de cuenta, pagos, créditos VU
        - policies: Consultas sobre reglamentos, syllabus, políticas académicas
        - calendar: Consultas sobre fechas de exámenes, calendario académico
        - escalation: Cuando necesitas derivar a un humano

        Analiza el último mensaje del usuario y decide el agente más apropiado.
        Responde SOLO con el nombre del agente: academic, financial, policies, calendar, o escalation.

        Si la consulta no está clara o es general, usa 'academic' como default.
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["messages"][-1].content)
        ]

        response = await self.llm.ainvoke(messages)
        agent_choice = response.content.strip().lower()

        # Validar la respuesta
        valid_agents = ["academic", "financial", "policies", "calendar", "escalation"]
        if agent_choice not in valid_agents:
            agent_choice = "academic"  # Default

        state["next"] = agent_choice
        state["agent_scratchpad"]["supervisor_choice"] = agent_choice
        state["agent_scratchpad"]["supervisor_reasoning"] = f"Elegí {agent_choice} para: {state['messages'][-1].content[:100]}"

        logger.info(f"Supervisor eligió agente: {agent_choice}")
        return state

    async def _academic_node(self, state: AgentState) -> AgentState:
        """Nodo del agente académico"""
        try:
            user_message = state["messages"][-1].content
            response = await self.agents["academic"].process_query(
                query=user_message,
                user_info=state["user_info"],
                context=state["agent_scratchpad"]
            )

            state["messages"].append(AIMessage(content=response))
            state["confidence_score"] = 0.9  # Alta confianza en respuestas académicas
            state["next"] = "END"

        except Exception as e:
            logger.error(f"Error en agente académico: {e}")
            state["escalation_requested"] = True
            state["next"] = "escalation"

        return state

    async def _financial_node(self, state: AgentState) -> AgentState:
        """Nodo del agente financiero"""
        try:
            user_message = state["messages"][-1].content
            response = await self.agents["financial"].process_query(
                query=user_message,
                user_info=state["user_info"],
                context=state["agent_scratchpad"]
            )

            state["messages"].append(AIMessage(content=response))
            state["confidence_score"] = 0.95  # Muy alta confianza en datos financieros
            state["next"] = "END"

        except Exception as e:
            logger.error(f"Error en agente financiero: {e}")
            state["escalation_requested"] = True
            state["next"] = "escalation"

        return state

    async def _policies_node(self, state: AgentState) -> AgentState:
        """Nodo del agente de políticas"""
        try:
            user_message = state["messages"][-1].content
            response = await self.agents["policies"].process_query(
                query=user_message,
                user_info=state["user_info"],
                context=state["agent_scratchpad"]
            )

            state["messages"].append(AIMessage(content=response))
            state["confidence_score"] = 0.85  # Buena confianza en políticas
            state["next"] = "END"

        except Exception as e:
            logger.error(f"Error en agente de políticas: {e}")
            state["escalation_requested"] = True
            state["next"] = "escalation"

        return state

    async def _calendar_node(self, state: AgentState) -> AgentState:
        """Nodo del agente de calendario"""
        try:
            user_message = state["messages"][-1].content
            response = await self.agents["calendar"].process_query(
                query=user_message,
                user_info=state["user_info"],
                context=state["agent_scratchpad"]
            )

            state["messages"].append(AIMessage(content=response))
            state["confidence_score"] = 0.9  # Alta confianza en fechas
            state["next"] = "END"

        except Exception as e:
            logger.error(f"Error en agente de calendario: {e}")
            state["escalation_requested"] = True
            state["next"] = "escalation"

        return state

    async def _escalation_node(self, state: AgentState) -> AgentState:
        """Nodo de escalación a humanos"""
        user_name = state["user_info"].get("nombre", "Usuario")

        response = f"""¡Hola {user_name}! 👥

Te estoy derivando con nuestro equipo de atención que te va a poder ayudar mejor.

Te van a contactar en breve para resolver tu consulta. 📞

¿Hay algo más en lo que te pueda asistir mientras tanto?"""

        state["messages"].append(AIMessage(content=response))
        state["next"] = "END"

        logger.info(f"Escalación activada para usuario: {user_name}")
        return state

    def _should_authenticate(self, state: AgentState) -> Literal["supervisor", "authentication", "END"]:
        """Decide si necesita autenticación"""
        return state["next"]

    def _route_to_agent(self, state: AgentState) -> Literal["academic", "financial", "policies", "calendar", "escalation", "END"]:
        """Enruta al agente correspondiente"""
        return state["next"]

    def _should_continue(self, state: AgentState) -> Literal["supervisor", "escalation", "END"]:
        """Decide si continuar, escalar o terminar"""
        if state.get("escalation_requested", False):
            return "escalation"

        # Si la confianza es baja, podría requerir supervisor
        if state.get("confidence_score", 1.0) < 0.5:
            return "supervisor"

        return "END"

    async def _authenticate_user(self, dni: str):
        """Simula autenticación de usuario (mock)"""
        # Mock users para desarrollo
        mock_users = {
            "12345678": {
                "id": 1,
                "nombre": "Juan Pérez",
                "legajo": "L001",
                "tipo": "alumno",
                "dni": "12345678"
            },
            "87654321": {
                "id": 2,
                "nombre": "María González",
                "legajo": "L002",
                "tipo": "alumno",
                "dni": "87654321"
            }
        }

        user_data = mock_users.get(dni)
        if user_data:
            from types import SimpleNamespace
            return SimpleNamespace(**user_data)
        return None

    async def process_message(self, message: str, session_id: str) -> str:
        """Procesa un mensaje a través del workflow LangGraph"""
        try:
            # Estado inicial
            initial_state: AgentState = {
                "messages": [HumanMessage(content=message)],
                "next": "authentication",
                "user_info": {},
                "session_id": session_id,
                "agent_scratchpad": {},
                "escalation_requested": False,
                "confidence_score": 1.0
            }

            # Configuración del thread
            config = {"configurable": {"thread_id": session_id}}

            # Ejecutar el workflow
            result = await self.app.ainvoke(initial_state, config)

            # Extraer la última respuesta
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            if ai_messages:
                return ai_messages[-1].content
            else:
                return "Lo siento, hubo un problema procesando tu mensaje."

        except Exception as e:
            logger.error(f"Error en SupervisorAgent: {e}")
            return "Hubo un error técnico. Por favor intentá de nuevo."

# Instancia global del supervisor
supervisor_agent = SupervisorAgent()