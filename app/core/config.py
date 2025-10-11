"""
Configuración de la aplicación usando Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.
    
    Las variables de entorno se cargan automáticamente desde .env
    """
    
    # ==========================================
    # INFORMACIÓN DE LA APLICACIÓN
    # ==========================================
    app_name: str = "Universidad Austral Bot"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False
    
    # ==========================================
    # MODELOS LLM
    # ==========================================
    llm_model: str = "claude-sonnet-4-20250514"
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
    supabase_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None
    
    # ==========================================
    # CHATWOOT
    # ==========================================
    chatwoot_url: str = "https://app.chatwoot.com"
    chatwoot_api_token: Optional[str] = None
    chatwoot_account_id: Optional[str] = None
    chatwoot_inbox_id: Optional[str] = None
    
    # ==========================================
    # N8N (LEGACY - Mantenido por compatibilidad)
    # ==========================================
    n8n_webhook_url: str = "http://localhost:5678/webhook"
    n8n_api_key: Optional[str] = None
    
    # ==========================================
    # WHATSAPP
    # ==========================================
    whatsapp_verify_token: str = "universidad_austral_token"
    whatsapp_phone_number_id: Optional[str] = None
    
    # ==========================================
    # BASE DE DATOS
    # ==========================================
    database_url: Optional[str] = None  # PostgreSQL directo (si se usa)
    
    # ==========================================
    # REDIS (CACHING)
    # ==========================================
    redis_url: Optional[str] = "redis://localhost:6379"
    redis_enabled: bool = False
    cache_ttl_seconds: int = 300  # 5 minutos
    
    # ==========================================
    # SESIONES
    # ==========================================
    session_ttl_hours: int = 2
    max_conversation_history: int = 50
    
    # ==========================================
    # RATE LIMITING
    # ==========================================
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 30
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
    langchain_tracing_v2: bool = True
    langchain_api_key: Optional[str] = None
    langchain_project: str = "universidad-austral-bot"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    
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
        case_sensitive=False,
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


@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la instancia singleton de settings.
    
    Usa lru_cache para asegurar que solo se carga una vez.
    """
    return Settings()


# Instancia global para importar fácilmente
settings = get_settings()
