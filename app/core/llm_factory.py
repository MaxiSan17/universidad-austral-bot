"""
Factory para crear instancias de LLM con abstracción completa.
Soporta múltiples proveedores: OpenAI, Anthropic, Google, etc.
Compatible con LangChain v0.3+
"""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Clase abstracta para proveedores de LLM"""

    @abstractmethod
    def create_llm(self, **kwargs) -> BaseChatModel:
        """Crea una instancia del LLM"""
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """Retorna el modelo por defecto"""
        pass


class OpenAIProvider(LLMProvider):
    """Proveedor de OpenAI"""

    def get_default_model(self) -> str:
        return "gpt-4o-mini"

    def create_llm(self, **kwargs) -> BaseChatModel:
        # Extraer parámetros específicos antes de pasar kwargs
        model = kwargs.pop("model", self.get_default_model())
        temperature = kwargs.pop("temperature", 0.1)
        api_key = kwargs.pop("api_key", settings.OPENAI_API_KEY)

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            **kwargs  # Resto de argumentos
        )


class AnthropicProvider(LLMProvider):
    """Proveedor de Anthropic"""

    def get_default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    def create_llm(self, **kwargs) -> BaseChatModel:
        # Extraer parámetros específicos antes de pasar kwargs
        model = kwargs.pop("model", self.get_default_model())
        temperature = kwargs.pop("temperature", 0.1)
        api_key = kwargs.pop("api_key", settings.ANTHROPIC_API_KEY)

        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )


class GoogleProvider(LLMProvider):
    """Proveedor de Google"""

    def get_default_model(self) -> str:
        return "gemini-1.5-pro"

    def create_llm(self, **kwargs) -> BaseChatModel:
        # Extraer parámetros específicos antes de pasar kwargs
        model = kwargs.pop("model", self.get_default_model())
        temperature = kwargs.pop("temperature", 0.1)
        api_key = kwargs.pop("google_api_key", settings.GOOGLE_API_KEY)

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            **kwargs
        )


class LLMFactory:
    """Factory para crear instancias de LLM con abstracción"""

    _providers: Dict[str, LLMProvider] = {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "google": GoogleProvider(),
    }

    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> BaseChatModel:
        """
        Crea una instancia de LLM basada en la configuración.

        Args:
            provider: Proveedor específico (openai, anthropic, google)
            model: Modelo específico a usar
            temperature: Temperatura para el modelo
            **kwargs: Argumentos adicionales para el LLM

        Returns:
            Instancia de BaseChatModel
        """
        # Determinar proveedor
        if provider is None:
            provider = cls._infer_provider_from_config()

        provider = provider.lower()

        if provider not in cls._providers:
            logger.warning(f"Proveedor desconocido: {provider}. Usando OpenAI por defecto.")
            provider = "openai"

        provider_instance = cls._providers[provider]

        # Determinar modelo
        if model is None:
            model = provider_instance.get_default_model()

        logger.info(f"Creando LLM: provider={provider}, model={model}, temperature={temperature}")

        # Log adicional para verificar API keys
        if provider == "anthropic":
            api_key_present = settings.ANTHROPIC_API_KEY is not None and len(settings.ANTHROPIC_API_KEY or "") > 0
            logger.info(f"🔑 ANTHROPIC_API_KEY configurada: {api_key_present}")
            if api_key_present:
                logger.info(f"🔑 ANTHROPIC_API_KEY (primeros 20 chars): {settings.ANTHROPIC_API_KEY[:20]}...")
        elif provider == "openai":
            api_key_present = settings.OPENAI_API_KEY is not None and len(settings.OPENAI_API_KEY or "") > 0
            logger.info(f"🔑 OPENAI_API_KEY configurada: {api_key_present}")

        try:
            # Crear kwargs combinados
            combined_kwargs = {
                "model": model,
                "temperature": temperature,
                **kwargs
            }

            logger.info(f"📤 Intentando crear LLM con provider '{provider}'...")
            result = provider_instance.create_llm(**combined_kwargs)
            logger.info(f"✅ LLM de {provider} creado exitosamente")
            return result

        except Exception as e:
            logger.error(f"❌ Error creando LLM de {provider}: {e}", exc_info=True)
            logger.error(f"❌ Tipo de error: {type(e).__name__}")
            logger.error(f"❌ Detalles completos del error: {str(e)}")

            # Fallback a OpenAI con configuración mínima
            logger.warning("⚠️ Haciendo fallback a OpenAI debido al error anterior")
            try:
                return cls._providers["openai"].create_llm(
                    model="gpt-4o-mini",
                    temperature=temperature
                )
            except Exception as fallback_error:
                logger.error(f"❌ Error en fallback a OpenAI: {fallback_error}", exc_info=True)
                raise

    @classmethod
    def _infer_provider_from_config(cls) -> str:
        """Infiere el proveedor desde la configuración"""
        model = settings.LLM_MODEL.lower()

        logger.info(f"🔍 Detectando provider desde LLM_MODEL: {settings.LLM_MODEL}")

        if "gpt" in model or "openai" in model:
            logger.info(f"✅ Provider detectado: openai (model={settings.LLM_MODEL})")
            return "openai"
        elif "claude" in model or "anthropic" in model:
            logger.info(f"✅ Provider detectado: anthropic (model={settings.LLM_MODEL})")
            return "anthropic"
        elif "gemini" in model or "google" in model:
            logger.info(f"✅ Provider detectado: google (model={settings.LLM_MODEL})")
            return "google"
        else:
            logger.warning(f"⚠️ No se detectó provider conocido en '{settings.LLM_MODEL}', usando openai por defecto")
            return "openai"  # Default

    @classmethod
    def create_for_agent(cls, agent_type: str, **kwargs) -> BaseChatModel:
        """
        Crea un LLM optimizado para un tipo de agente específico.

        Args:
            agent_type: Tipo de agente (supervisor, academic, financial, etc.)
            **kwargs: Argumentos adicionales

        Returns:
            Instancia de BaseChatModel configurada
        """
        # Configuraciones específicas por tipo de agente
        agent_configs = {
            "supervisor": {
                "temperature": 0.3,  # Aumentado para mejor clasificación
                "model": settings.LLM_MODEL
            },
            "academic": {
                "temperature": 0.3,
                "model": settings.LLM_MODEL
            },
            "financial": {
                "temperature": 0.0,
                "model": settings.LLM_MODEL
            },
            "policies": {
                "temperature": 0.2,
                "model": settings.LLM_MODEL
            },
            "calendar": {
                "temperature": 0.1,
                "model": settings.LLM_MODEL
            }
        }

        config = agent_configs.get(agent_type, {"temperature": 0.1})
        # Merge con kwargs, dando prioridad a kwargs
        config.update(kwargs)

        return cls.create(**config)

    @classmethod
    def register_provider(cls, name: str, provider: LLMProvider):
        """Registra un nuevo proveedor de LLM"""
        cls._providers[name.lower()] = provider
        logger.info(f"Proveedor registrado: {name}")


# Instancia global para facilitar el uso
llm_factory = LLMFactory()
