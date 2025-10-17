"""
Configuración consolidada de la aplicación usando Pydantic Settings
Migrado desde app/config.py + app/core/config.py original
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.
    
    Las variables de entorno se cargan automáticamente desde .env
    Soporta tanto snake_case como UPPER_CASE para compatibilidad
    """
    
    # ==========================================
    # INFORMACIÓN DE LA APLICACIÓN
    # ==========================================
    app_name: str = "Universidad Austral Bot"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # ==========================================
    # MODELOS LLM
    # ==========================================
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1000
    
    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # ==========================================
    # SUPABASE
    # ==========================================
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None  # Alias para SUPABASE_ANON_KEY
    supabase_jwt_secret: Optional[str] = None
    
    # ==========================================
    # CHATWOOT
    # ==========================================
    chatwoot_url: Optional[str] = None
    chatwoot_api_token: Optional[str] = None
    chatwoot_account_id: Optional[str] = None
    chatwoot_inbox_id: Optional[str] = None
    chatwoot_webhook_secret: Optional[str] = None
    
    # ==========================================
    # N8N
    # ==========================================
    n8n_webhook_url: str = "https://n8n.tucbbs.com.ar/webhook"
    n8n_webhook_base_url: str = "https://n8n.tucbbs.com.ar/webhook"
    n8n_api_key: Optional[str] = None
    n8n_api_base_url: str = "https://n8n.tucbbs.com.ar/webhook"
    
    # ==========================================
    # WHATSAPP
    # ==========================================
    whatsapp_verify_token: str = "universidad_austral_token"
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    
    # ==========================================
    # BASE DE DATOS
    # ==========================================
    database_url: str = "postgresql://postgres:password@localhost:5432/universidad_austral"
    
    # ==========================================
    # REDIS (CACHING)
    # ==========================================
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = False
    cache_ttl_seconds: int = 300  # 5 minutos
    
    # ==========================================
    # SESIONES
    # ==========================================
    session_ttl_minutes: int = 60  # Para session_manager
    session_ttl_hours: int = 2  # Para phone authentication
    max_conversation_history: int = 50
    
    # ==========================================
    # SECURITY / JWT
    # ==========================================
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # ==========================================
    # RATE LIMITING
    # ==========================================
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 500
    
    # ==========================================
    # LOGGING
    # ==========================================
    log_level: str = "INFO"
    log_format: str = "json"  # "json" o "text"
    log_file: Optional[str] = "logs/bot.log"
    
    # ==========================================
    # LANGSMITH (OBSERVABILIDAD)
    # ==========================================
    langchain_tracing_v2: Optional[str] = Field(None, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(None, env="LANGCHAIN_API_KEY")
    langchain_project: str = Field("universidad-austral-bot", env="LANGCHAIN_PROJECT")
    langchain_endpoint: str = Field("https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT")
    
    # ==========================================
    # SENTRY (ERROR TRACKING)
    # ==========================================
    sentry_dsn: Optional[str] = None
    sentry_environment: Optional[str] = None
    sentry_traces_sample_rate: float = 1.0
    
    # ==========================================
    # SERVIDOR
    # ==========================================
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    
    # ==========================================
    # TIMEOUTS
    # ==========================================
    http_timeout: int = 30
    llm_timeout: int = 60
    database_timeout: int = 10
    
    # ==========================================
    # MONITORING
    # ==========================================
    prometheus_enabled: bool = True
    
    # ==========================================
    # FEATURES FLAGS
    # ==========================================
    enable_academic_tools: bool = True
    enable_calendar_tools: bool = True
    enable_financial_tools: bool = False
    enable_policies_tools: bool = False
    
    # ==========================================
    # UNIVERSIDAD ESPECÍFICO
    # ==========================================
    universidad_nombre: str = "Universidad Austral"
    universidad_ubicacion: str = "Pilar, Buenos Aires, Argentina"
    creditos_vu_requeridos: int = 10
    
    # Configuración de Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Acepta tanto MAYÚSCULAS como minúsculas
        extra="ignore"  # Ignorar variables de entorno extra
    )
    
    # ==========================================
    # PROPIEDADES CALCULADAS
    # ==========================================
    
    @property
    def is_production(self) -> bool:
        """Verifica si está en producción"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Verifica si está en desarrollo"""
        return self.environment == "development"
    
    @property
    def llm_config(self) -> dict:
        """Retorna configuración del LLM"""
        return {
            "model": self.llm_model,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens
        }

    @property
    def langsmith_enabled(self) -> bool:
        """Verifica si LangSmith está habilitado"""
        return (
            self.langchain_tracing_v2 == "true"
            and self.langchain_api_key is not None
            and len(self.langchain_api_key) > 0
        )

    def setup_langsmith(self):
        """Configura LangSmith si está habilitado"""
        if self.langsmith_enabled:
            import os
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.langchain_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langchain_project
            os.environ["LANGCHAIN_ENDPOINT"] = self.langchain_endpoint
            # Usar logging básico para evitar dependencias circulares
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"✅ LangSmith tracing habilitado - Proyecto: {self.langchain_project}")
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("⚠️ LangSmith tracing deshabilitado (falta configuración)")
    
    # ==========================================
    # ALIASES PARA COMPATIBILIDAD (UPPERCASE)
    # ==========================================
    # Estos properties permiten acceder con nombres en mayúsculas
    # para compatibilidad con código legacy que usa MAYÚSCULAS
    
    @property
    def ENVIRONMENT(self) -> str:
        return self.environment
    
    @property
    def DEBUG(self) -> bool:
        return self.debug
    
    @property
    def LLM_MODEL(self) -> str:
        return self.llm_model
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return self.openai_api_key
    
    @property
    def ANTHROPIC_API_KEY(self) -> Optional[str]:
        return self.anthropic_api_key
    
    @property
    def GOOGLE_API_KEY(self) -> Optional[str]:
        return self.google_api_key
    
    @property
    def SUPABASE_URL(self) -> Optional[str]:
        return self.supabase_url
    
    @property
    def SUPABASE_ANON_KEY(self) -> Optional[str]:
        return self.supabase_anon_key
    
    @property
    def CHATWOOT_URL(self) -> Optional[str]:
        return self.chatwoot_url
    
    @property
    def CHATWOOT_API_TOKEN(self) -> Optional[str]:
        return self.chatwoot_api_token
    
    @property
    def CHATWOOT_ACCOUNT_ID(self) -> Optional[str]:
        return self.chatwoot_account_id
    
    @property
    def CHATWOOT_WEBHOOK_SECRET(self) -> Optional[str]:
        return self.chatwoot_webhook_secret
    
    @property
    def N8N_WEBHOOK_URL(self) -> str:
        return self.n8n_webhook_url
    
    @property
    def N8N_API_KEY(self) -> Optional[str]:
        return self.n8n_api_key
    
    @property
    def N8N_WEBHOOK_BASE_URL(self) -> str:
        return self.n8n_webhook_base_url
    
    @property
    def N8N_API_BASE_URL(self) -> str:
        return self.n8n_api_base_url
    
    @property
    def WHATSAPP_VERIFY_TOKEN(self) -> str:
        return self.whatsapp_verify_token
    
    @property
    def WHATSAPP_ACCESS_TOKEN(self) -> Optional[str]:
        return self.whatsapp_access_token
    
    @property
    def DATABASE_URL(self) -> str:
        return self.database_url
    
    @property
    def REDIS_URL(self) -> str:
        return self.redis_url
    
    @property
    def SESSION_TTL_MINUTES(self) -> int:
        return self.session_ttl_minutes
    
    @property
    def SECRET_KEY(self) -> str:
        return self.secret_key
    
    @property
    def ALGORITHM(self) -> str:
        return self.algorithm
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.access_token_expire_minutes
    
    @property
    def RATE_LIMIT_PER_MINUTE(self) -> int:
        return self.rate_limit_per_minute
    
    @property
    def LOG_LEVEL(self) -> str:
        return self.log_level
    
    @property
    def LANGCHAIN_TRACING_V2(self) -> Optional[str]:
        return self.langchain_tracing_v2
    
    @property
    def LANGCHAIN_API_KEY(self) -> Optional[str]:
        return self.langchain_api_key
    
    @property
    def LANGCHAIN_PROJECT(self) -> str:
        return self.langchain_project
    
    @property
    def PROMETHEUS_ENABLED(self) -> bool:
        return self.prometheus_enabled


@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la instancia singleton de settings.

    Usa lru_cache para asegurar que solo se carga una vez.
    """
    settings_instance = Settings()
    settings_instance.setup_langsmith()
    return settings_instance


# Instancia global para importar fácilmente
settings = get_settings()
