from typing import Annotated, Literal, Dict, Any, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from app.core.config import settings
from app.core.llm_factory import llm_factory
from app.session.session_manager import session_manager
from app.utils.logger import get_logger
from app.agents.academic_agent import AcademicAgent
from app.agents.financial_agent import FinancialAgent
from app.agents.policies_agent import PoliciesAgent
from app.agents.calendar_agent import CalendarAgent
from app.agents.query_classifier import query_classifier
from datetime import datetime
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
    """
    Supervisor LangGraph que orquesta agentes especializados.
    Compatible con LangGraph v1.0 y LangChain v1.0
    """

    def __init__(self):
        logger.info("Inicializando SupervisorAgent...")
        
        # Usar LLM factory con abstracción completa
        try:
            self.llm = llm_factory.create_for_agent("supervisor")
            logger.info("LLM del supervisor inicializado correctamente")

            # Habilitar streaming
            if hasattr(self.llm, "streaming"):
                self.llm.streaming = True
                logger.info("✅ Streaming habilitado en LLM del supervisor")
        except Exception as e:
            logger.error(f"Error inicializando LLM del supervisor: {e}")
            # Fallback a configuración básica
            self.llm = llm_factory.create(temperature=0.0)

        # Inicializar agentes especializados
        try:
            self.agents = {
                "academic": AcademicAgent(),
                "financial": FinancialAgent(),
                "policies": PoliciesAgent(),
                "calendar": CalendarAgent()
            }
            logger.info(f"Agentes especializados inicializados: {list(self.agents.keys())}")
        except Exception as e:
            logger.error(f"Error inicializando agentes especializados: {e}")
            self.agents = {}

        # Checkpointing en memoria (LangGraph v1.0)
        try:
            self.memory = MemorySaver()
            logger.info("Checkpointer en memoria inicializado")
        except Exception as e:
            logger.error(f"Error inicializando checkpointer: {e}")
            self.memory = None

        # Construir el grafo
        try:
            self.workflow = self._build_workflow()
            self.app = self.workflow.compile(checkpointer=self.memory)
            logger.info("Workflow de LangGraph compilado exitosamente")
        except Exception as e:
            logger.error(f"Error construyendo workflow: {e}")
            raise

    def _build_workflow(self) -> StateGraph:
        """Construye el workflow LangGraph compatible con v1.0"""

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

        # Todos los agentes terminan directamente (sin volver al supervisor)
        for agent in ["academic", "financial", "policies", "calendar"]:
            workflow.add_edge(agent, END)

        # Escalación termina la conversación
        workflow.add_edge("escalation", END)

        return workflow

    async def _authentication_node(self, state: AgentState) -> AgentState:
        """Nodo de autenticación con persistencia por teléfono"""
        session_id = state["session_id"]

        # Verificar si ya está autenticado en la sesión actual (memoria en RAM)
        if session_manager.is_authenticated(session_id):
            user = session_manager.get_user(session_id)
            state["user_info"] = {
                "id": user.id,
                "nombre": user.nombre,
                "legajo": user.legajo,
                "tipo": user.tipo
            }
            # Usuario autenticado - ir directo al supervisor
            state["next"] = "supervisor"
            return state

        # NUEVO: Buscar si este teléfono tiene usuario asociado en BD
        from app.database import phone_repository, user_repository
        
        logger.info(f"🔍 Buscando asociación persistente para teléfono {session_id}")
        usuario_id = await phone_repository.get_user_by_phone(session_id)
        
        if usuario_id:
            # Auto-autenticar usando el usuario_id almacenado
            logger.info(f"✅ Asociación encontrada! Auto-autenticando usuario {usuario_id}")
            user = await user_repository.get_user_by_id(usuario_id)
            
            if user:
                session_manager.authenticate_user(session_id, user)
                state["user_info"] = {
                    "id": user.id,
                    "nombre": user.nombre,
                    "legajo": user.legajo,
                    "tipo": user.tipo
                }
                
                response = f"¡Hola de nuevo, {user.nombre}! 👋\n\n¿En qué te puedo ayudar hoy?"
                state["messages"].append(AIMessage(content=response))
                state["next"] = "supervisor"
                return state
            else:
                logger.error(f"⚠️ Usuario {usuario_id} no encontrado en BD. Eliminando asociación inválida.")
                await phone_repository.delete_phone_mapping(session_id)

        # Proceso de autenticación por DNI
        last_message = state["messages"][-1].content if state["messages"] else ""

        # Detectar comando de logout/olvidar
        if any(word in last_message.lower() for word in ["olvidar", "logout", "cerrar sesion", "cerrar sesión"]):
            await phone_repository.delete_phone_mapping(session_id)
            logger.info(f"🛡️ Usuario solicitó olvidar su información")
            response = "He olvidado tu información. 🛡️\n\nLa próxima vez te pediré tu DNI nuevamente.\n\n¿Hay algo más en lo que te pueda ayudar?"
            state["messages"].append(AIMessage(content=response))
            state["next"] = "END"
            return state

        # Buscar DNI en el mensaje
        import re
        dni_pattern = r'\b\d{8}\b'
        dni_match = re.search(dni_pattern, last_message)

        if dni_match:
            dni = dni_match.group()
            # Autenticar usuario
            user = await self._authenticate_user(dni)

            if user:
                session_manager.authenticate_user(session_id, user)
                state["user_info"] = {
                    "id": user.id,
                    "nombre": user.nombre,
                    "legajo": user.legajo,
                    "tipo": user.tipo
                }

                # NUEVO: Guardar asociación teléfono → usuario en BD
                logger.info(f"💾 Guardando asociación persistente: {session_id} → {user.id}")
                await phone_repository.save_phone_user_mapping(session_id, user.id)

                response = f"¡Perfecto, {user.nombre}! Ya te reconocí.\n\n¿En qué te puedo ayudar hoy?"
                state["messages"].append(AIMessage(content=response))
                # Terminar aquí - NO ir al supervisor automáticamente
                state["next"] = "END"
            else:
                response = "Lo siento, no reconozco ese DNI en nuestra base de datos.\n\nPor favor verificá el número."
                state["messages"].append(AIMessage(content=response))
                state["next"] = "END"
        else:
            response = "¡Hola! Para ayudarte necesito que me pases tu DNI (solo números)."
            state["messages"].append(AIMessage(content=response))
            state["next"] = "END"

        return state

    async def _supervisor_node(self, state: AgentState) -> AgentState:
        """Nodo supervisor que decide la estrategia con clasificación mejorada"""

        system_prompt = """Eres el supervisor de un sistema de agentes para la Universidad Austral.

Tu trabajo es analizar cada consulta del usuario y clasificarla en UNA de estas categorías:

## 🎓 ACADEMIC (Agente Académico)
Responsable de:
- Horarios de clases y cursada
- Materias inscriptas y disponibles
- Información de profesores
- Ubicación de aulas y salones
- Créditos de Vida Universitaria (VU)
- Inscripciones a materias
- Comisiones y grupos de clase

Ejemplos de consultas:
- "¿Cuándo tengo clases?"
- "¿A qué hora curso [materia]?"
- "¿En qué aula tengo clase?"
- "¿Quién es el profesor de [materia]?"
- "¿En qué materias estoy inscripto?"
- "¿Cuántos créditos VU tengo?"
- "¿Dónde es la clase de mañana?"
- "Horario de [materia]"

## 📅 CALENDAR (Agente de Calendario)
Responsable de:
- Fechas de exámenes (parciales, finales, recuperatorios)
- Calendario académico
- Eventos universitarios
- Feriados y días no laborables
- Fechas de inscripción
- Inicio y fin de cuatrimestre

Ejemplos de consultas:
- "¿Cuándo es el parcial/final de [materia]?"
- "¿Qué exámenes tengo esta semana?"
- "¿Cuándo empiezan las clases?"
- "¿Hay feriados próximos?"
- "Calendario de exámenes"
- "¿Cuándo es el próximo evento?"
- "Fechas importantes"

## 💰 FINANCIAL (Agente Financiero)
Responsable de:
- Estado de cuenta
- Pagos y deudas
- Cuotas y vencimientos
- Facturación
- Aranceles
- Consultas sobre montos

Ejemplos de consultas:
- "¿Tengo deudas?"
- "¿Cuánto debo?"
- "¿Cuándo vence mi próximo pago?"
- "Estado de mi cuenta"
- "¿Cómo pago?"
- "Información de facturación"

## 📚 POLICIES (Agente de Políticas)
Responsable de:
- Reglamentos universitarios
- Syllabi y programas de materias
- Políticas académicas
- Requisitos de carrera
- Bibliografía
- Contenidos de materias
- FAQs institucionales

Ejemplos de consultas:
- "¿Qué temas vemos en [materia]?"
- "¿Cómo se evalúa en [materia]?"
- "¿Cuál es el reglamento de asistencia?"
- "¿Qué bibliografía usa [materia]?"
- "Programa de la materia"
- "Requisitos para [trámite]"

## 🆘 ESCALATION (Derivar a Humano)
Cuando:
- El usuario pide explícitamente hablar con una persona
- La consulta es muy compleja o sensible
- Hay frustración evidente (>3 intentos fallidos)
- Temas de privacidad o confidencialidad
- Problemas técnicos no resolubles

---

## INSTRUCCIONES DE CLASIFICACIÓN:

1. **Lee la consulta completa** del usuario
2. **Identifica las palabras clave** más importantes
3. **Detecta la intención principal** (¿qué quiere saber/hacer?)
4. **Considera el contexto temporal**:
   - "cuándo" + "parcial/final/examen" → calendar
   - "cuándo" + "clase/horario" → academic
5. **Elige el agente MÁS específico** que puede responder
6. **Si hay duda entre dos agentes**, prioriza:
   - calendar > academic (si menciona exámenes o fechas)
   - academic > policies (si menciona info práctica vs teórica)
   - financial siempre tiene prioridad si menciona dinero

## RESPUESTA:

Responde SOLO con UNA palabra (el nombre del agente):
- academic
- calendar
- financial
- policies
- escalation

NO agregues explicaciones, puntos, o texto adicional.
"""

        try:
            # Usar el último mensaje HUMANO, ignorando mensajes previos del bot
            human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
            user_query = human_messages[-1].content if human_messages else state["messages"][-1].content
            
            # PASO 1: Intentar clasificación rápida con keywords
            agent_choice, confidence, method = query_classifier.classify(user_query)
            
            # PASO 2: Si no hay resultado claro, usar LLM
            if agent_choice is None or confidence < 0.5:
                logger.info(f"🤖 Usando LLM para clasificación (method={method}, conf={confidence})")
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_query)
                ]

                response = await self.llm.ainvoke(messages)
                agent_choice = response.content.strip().lower()
                method = "llm"
                confidence = 0.85  # Asumimos alta confianza del LLM

            # Validar la respuesta
            valid_agents = ["academic", "financial", "policies", "calendar", "escalation"]
            if agent_choice not in valid_agents:
                logger.warning(f"⚠️ Agente inválido: {agent_choice}. Usando 'academic' como fallback")
                agent_choice = "academic"  # Default
                confidence = 0.3
                method = "fallback"

            state["next"] = agent_choice
            state["confidence_score"] = confidence
            state["agent_scratchpad"]["supervisor_choice"] = agent_choice
            state["agent_scratchpad"]["classification_method"] = method
            state["agent_scratchpad"]["classification_confidence"] = confidence
            state["agent_scratchpad"]["supervisor_reasoning"] = f"Elegí {agent_choice} [{method}] (conf: {confidence:.2f}) para: {user_query[:100]}"

            logger.info(f"🎯 Supervisor → {agent_choice.upper()} [{method}] (confianza: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error en supervisor node: {e}")
            # Fallback a agente académico
            state["next"] = "academic"
            
        return state

    async def _academic_node(self, state: AgentState) -> AgentState:
        """Nodo del agente académico"""
        try:
            if "academic" not in self.agents:
                raise Exception("Agente académico no disponible")

            # Obtener el último mensaje HUMANO (ignorar AIMessages intermedios)
            human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
            user_message = human_messages[-1].content if human_messages else state["messages"][-1].content

            response = await self.agents["academic"].process_query(
                query=user_message,
                user_info=state["user_info"],
                context=state["agent_scratchpad"]
            )

            state["messages"].append(AIMessage(content=response))
            state["confidence_score"] = 0.9
            state["next"] = "END"

        except Exception as e:
            logger.error(f"Error en agente académico: {e}")
            state["escalation_requested"] = True
            state["next"] = "escalation"

        return state

    async def _financial_node(self, state: AgentState) -> AgentState:
        """Nodo del agente financiero"""
        try:
            if "financial" not in self.agents:
                raise Exception("Agente financiero no disponible")

            # Obtener el último mensaje HUMANO (ignorar AIMessages intermedios)
            human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
            user_message = human_messages[-1].content if human_messages else state["messages"][-1].content

            response = await self.agents["financial"].process_query(
                query=user_message,
                user_info=state["user_info"],
                context=state["agent_scratchpad"]
            )

            state["messages"].append(AIMessage(content=response))
            state["confidence_score"] = 0.95
            state["next"] = "END"

        except Exception as e:
            logger.error(f"Error en agente financiero: {e}")
            state["escalation_requested"] = True
            state["next"] = "escalation"

        return state

    async def _policies_node(self, state: AgentState) -> AgentState:
        """Nodo del agente de políticas"""
        try:
            if "policies" not in self.agents:
                raise Exception("Agente de políticas no disponible")

            # Obtener el último mensaje HUMANO (ignorar AIMessages intermedios)
            human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
            user_message = human_messages[-1].content if human_messages else state["messages"][-1].content

            response = await self.agents["policies"].process_query(
                query=user_message,
                user_info=state["user_info"],
                context=state["agent_scratchpad"]
            )

            state["messages"].append(AIMessage(content=response))
            state["confidence_score"] = 0.85
            state["next"] = "END"

        except Exception as e:
            logger.error(f"Error en agente de políticas: {e}")
            state["escalation_requested"] = True
            state["next"] = "escalation"

        return state

    async def _calendar_node(self, state: AgentState) -> AgentState:
        """Nodo del agente de calendario"""
        try:
            if "calendar" not in self.agents:
                raise Exception("Agente de calendario no disponible")

            # Obtener el último mensaje HUMANO (ignorar AIMessages intermedios)
            human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
            user_message = human_messages[-1].content if human_messages else state["messages"][-1].content

            response = await self.agents["calendar"].process_query(
                query=user_message,
                user_info=state["user_info"],
                context=state["agent_scratchpad"]
            )

            state["messages"].append(AIMessage(content=response))
            state["confidence_score"] = 0.9
            state["next"] = "END"

        except Exception as e:
            logger.error(f"Error en agente de calendario: {e}")
            state["escalation_requested"] = True
            state["next"] = "escalation"

        return state

    async def _escalation_node(self, state: AgentState) -> AgentState:
        """Nodo de escalación a humanos"""
        user_name = state["user_info"].get("nombre", "Usuario")

        response = f"""¡Hola {user_name}!

Te estoy derivando con nuestro equipo de atención que te va a poder ayudar mejor.

Te van a contactar en breve para resolver tu consulta.

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
        """Autentica usuario usando Supabase"""
        try:
            from app.database import user_repository
            user = await user_repository.get_user_by_dni(dni)
            return user
        except Exception as e:
            logger.error(f"Error autenticando usuario: {e}")
            return None

    async def process_message(self, message: str, session_id: str) -> str:
        """
        Procesa un mensaje a través del workflow LangGraph.
        
        Args:
            message: Mensaje del usuario
            session_id: ID de sesión único
            
        Returns:
            Respuesta del sistema
        """
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

            # Configuración del thread con límite de recursión (compatible con LangGraph v1.0)
            config = {
                "configurable": {"thread_id": session_id},
                "recursion_limit": 10  # Reducir límite de recursión
            }

            # Ejecutar el workflow
            result = await self.app.ainvoke(initial_state, config)

            # Extraer la última respuesta
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            if ai_messages:
                return ai_messages[-1].content
            else:
                return "Lo siento, hubo un problema procesando tu mensaje."

        except Exception as e:
            logger.error(f"Error en SupervisorAgent.process_message: {e}", exc_info=True)
            return "Hubo un error técnico. Por favor intentá de nuevo."

    async def process_message_stream(self, message: str, session_id: str) -> str:
        """
        Procesa un mensaje a través del workflow LangGraph.
        Usa ainvoke directamente (más confiable que astream_events para este caso).

        Args:
            message: Mensaje del usuario
            session_id: ID de sesión único

        Returns:
            Respuesta completa del sistema
        """
        try:
            logger.info(f"🚀 Procesando con streaming (sesión: {session_id})")
            
            # Delegar al método process_message que funciona correctamente
            return await self.process_message(message, session_id)

        except Exception as e:
            logger.error(f"❌ Error en process_message_stream: {e}", exc_info=True)
            return "Hubo un error técnico. Por favor intentá de nuevo."

# Instancia global del supervisor
supervisor_agent = SupervisorAgent()
