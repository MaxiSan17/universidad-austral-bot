"""
LLM Response Generator - Generador principal de respuestas naturales con LLM.

Este módulo reemplaza los formatters de templates rígidos con generación
dinámica usando LLM, permitiendo respuestas contextuales, empáticas y
que responden exactamente lo que el usuario preguntó.
"""

from typing import Dict, Any, Optional
import json
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseChatModel

from app.core.llm_factory import llm_factory
from app.models.context import ConversationContext, ResponseStrategy
from app.prompts.system_prompts import (
    build_system_prompt,
    build_user_prompt,
    get_suggested_length
)
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class LLMResponseGenerator:
    """
    Generador de respuestas naturales usando LLM.

    Toma datos brutos + contexto conversacional y genera respuestas
    empáticas, contextuales y que responden exactamente lo preguntado.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 500
    ):
        """
        Inicializa el generador de respuestas.

        Args:
            model: Modelo LLM a usar (None = usar config)
            temperature: Temperatura para generación (0.5 por defecto para naturalidad)
            max_tokens: Máximo de tokens en la respuesta
        """
        self.model = model or getattr(settings, "LLM_RESPONSE_MODEL", settings.LLM_MODEL)
        self.temperature = temperature
        self.max_tokens = max_tokens
        logger.info(f"LLMResponseGenerator inicializado: model={self.model}, temp={self.temperature}")

    def _create_llm(self) -> BaseChatModel:
        """Crea instancia del LLM configurado"""
        return llm_factory.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

    async def generate_response(
        self,
        data: Any,  # Pydantic Model o Dict con los datos
        context: ConversationContext,
        strategy: ResponseStrategy,
        agent_type: str = "academic",
        response_type: str = "general"
    ) -> str:
        """
        Genera una respuesta natural usando LLM.

        Args:
            data: Datos disponibles (Pydantic Model o Dict)
            context: Contexto conversacional enriquecido
            strategy: Estrategia de respuesta determinada
            agent_type: Tipo de agente (academic, calendar, etc)
            response_type: Tipo específico de respuesta (horarios, examenes, etc)

        Returns:
            Respuesta generada por el LLM

        Raises:
            Exception: Si hay error en la generación
        """
        try:
            logger.info(f"🤖 Generando respuesta con LLM: agent={agent_type}, type={response_type}")

            # Convertir data a formato serializable
            data_dict = self._serialize_data(data)

            # Construir prompts
            system_prompt = build_system_prompt(
                agent_type=agent_type,
                response_type=response_type,
                context=context,
                strategy=strategy
            )

            user_prompt = build_user_prompt(
                original_query=context.current_query,
                data_available=data_dict,
                context=context,
                strategy=strategy
            )

            # Log de prompts (solo en debug)
            logger.debug(f"System Prompt:\n{system_prompt}\n")
            logger.debug(f"User Prompt:\n{user_prompt}\n")

            # Crear LLM y generar respuesta
            llm = self._create_llm()

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # Invocar LLM
            logger.info("📤 Enviando request al LLM...")
            response = await llm.ainvoke(messages)

            # Extraer contenido
            generated_response = response.content.strip()

            logger.info(f"✅ Respuesta generada ({len(generated_response)} chars)")
            logger.debug(f"Respuesta completa:\n{generated_response}\n")

            return generated_response

        except Exception as e:
            logger.error(f"❌ Error generando respuesta con LLM: {e}", exc_info=True)
            # Fallback a respuesta genérica
            return self._get_fallback_response(context.user_name, str(e))

    def _serialize_data(self, data: Any) -> Dict[str, Any]:
        """
        Serializa datos a formato JSON-compatible.

        Args:
            data: Pydantic Model, Dict, o cualquier objeto serializable

        Returns:
            Dict serializable
        """
        try:
            # Si es Pydantic Model
            if isinstance(data, BaseModel):
                return data.model_dump(mode='json')

            # Si es Dict
            elif isinstance(data, dict):
                return data

            # Si es List
            elif isinstance(data, list):
                return {"items": data}

            # Intentar convertir a dict
            else:
                return {"data": str(data)}

        except Exception as e:
            logger.warning(f"Error serializando data: {e}")
            return {"error": "No se pudo serializar data", "raw": str(data)}

    def _get_fallback_response(self, user_name: str, error_msg: str) -> str:
        """
        Genera respuesta de fallback cuando el LLM falla.

        Args:
            user_name: Nombre del usuario
            error_msg: Mensaje de error

        Returns:
            Respuesta de fallback
        """
        logger.warning(f"⚠️ Usando fallback response para {user_name}")
        return f"""¡Hola {user_name}! 😅

Tuve un pequeño problema técnico al procesar tu consulta.

¿Podrías intentar de nuevo o reformular tu pregunta? Estoy acá para ayudarte."""

    async def generate_from_template_data(
        self,
        template_data: Dict[str, Any],
        original_query: str,
        user_name: str,
        agent_type: str = "academic",
        response_type: str = "general",
        context: Optional[ConversationContext] = None,
        strategy: Optional[ResponseStrategy] = None
    ) -> str:
        """
        Genera respuesta desde datos de template legacy.

        Útil para migración gradual desde templates a LLM generation.

        Args:
            template_data: Datos en formato de template antiguo
            original_query: Query original del usuario
            user_name: Nombre del usuario
            agent_type: Tipo de agente
            response_type: Tipo de respuesta
            context: Contexto conversacional (opcional, se crea uno básico si no se provee)
            strategy: Estrategia de respuesta (opcional, se crea una básica)

        Returns:
            Respuesta generada
        """
        # Crear contexto básico si no se provee
        if context is None:
            from app.models.context import ConversationContext, EmotionalState
            context = ConversationContext(
                current_query=original_query,
                query_type=response_type,
                user_name=user_name,
                emotional_state=EmotionalState()
            )

        # Crear estrategia básica si no se provee
        if strategy is None:
            from app.models.context import ResponseStrategy
            strategy = ResponseStrategy(
                length="auto",
                tone="neutral"
            )

        # Generar respuesta
        return await self.generate_response(
            data=template_data,
            context=context,
            strategy=strategy,
            agent_type=agent_type,
            response_type=response_type
        )


# ============================================================
# FUNCIONES DE AYUDA
# ============================================================

def determine_data_complexity(data: Any) -> str:
    """
    Determina la complejidad de los datos para sugerir longitud de respuesta.

    Args:
        data: Datos a analizar

    Returns:
        "simple", "moderate", o "complex"
    """
    try:
        # Convertir a dict si es Pydantic
        if isinstance(data, BaseModel):
            data_dict = data.model_dump()
        elif isinstance(data, dict):
            data_dict = data
        else:
            return "simple"

        # Contar items
        total_items = 0

        if isinstance(data_dict, dict):
            # Si hay listas, contar elementos
            for value in data_dict.values():
                if isinstance(value, list):
                    total_items += len(value)
                elif isinstance(value, dict):
                    total_items += len(value)

        # Determinar complejidad
        if total_items == 0 or total_items == 1:
            return "simple"
        elif total_items <= 5:
            return "moderate"
        else:
            return "complex"

    except Exception as e:
        logger.warning(f"Error determinando complejidad: {e}")
        return "moderate"


def should_use_llm_generation() -> bool:
    """
    Determina si se debe usar LLM generation o templates.

    Basado en configuración del ambiente.

    Returns:
        True si se debe usar LLM generation
    """
    mode = getattr(settings, "RESPONSE_GENERATION_MODE", "llm")
    return mode == "llm"


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

# Crear instancia global con configuración por defecto
llm_response_generator = LLMResponseGenerator(
    temperature=getattr(settings, "LLM_RESPONSE_TEMPERATURE", 0.5),
    max_tokens=getattr(settings, "MAX_RESPONSE_TOKENS", 500)
)


# ============================================================
# HELPER FUNCTION PARA MIGRACIÓN FÁCIL
# ============================================================

async def generate_natural_response(
    data: Any,
    original_query: str,
    user_name: str,
    query_type: str = "general",
    agent_type: str = "academic",
    context: Optional[ConversationContext] = None,
    strategy: Optional[ResponseStrategy] = None
) -> str:
    """
    Función helper para generar respuestas naturales fácilmente.

    Esta función simplifica la API para migración gradual desde templates.

    Args:
        data: Datos disponibles (Pydantic Model o Dict)
        original_query: Query original del usuario
        user_name: Nombre del usuario
        query_type: Tipo de query (horarios, examenes, etc)
        agent_type: Tipo de agente (academic, calendar, etc)
        context: Contexto conversacional (opcional)
        strategy: Estrategia de respuesta (opcional)

    Returns:
        Respuesta generada naturalmente

    Example:
        ```python
        response = await generate_natural_response(
            data=horarios_response,
            original_query="¿En qué aula tengo ética?",
            user_name="Juan",
            query_type="horarios",
            agent_type="academic"
        )
        ```
    """
    # Crear contexto básico si no se provee
    if context is None:
        from app.models.context import ConversationContext, EmotionalState
        context = ConversationContext(
            current_query=original_query,
            query_type=query_type,
            user_name=user_name,
            emotional_state=EmotionalState()
        )

    # Crear estrategia básica si no se provee
    if strategy is None:
        from app.models.context import ResponseStrategy

        # Determinar complejidad y longitud sugerida
        complexity = determine_data_complexity(data)
        length = get_suggested_length(complexity)

        strategy = ResponseStrategy(
            length=length,
            tone="neutral"
        )

    # Usar el generator global
    return await llm_response_generator.generate_response(
        data=data,
        context=context,
        strategy=strategy,
        agent_type=agent_type,
        response_type=query_type
    )
