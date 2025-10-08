from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Configuration settings using Pydantic v2"""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # LLM Configuration
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # LangSmith Configuration
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "universidad-austral-bot"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/universidad_austral"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # Chatwoot Integration
    CHATWOOT_URL: Optional[str] = None
    CHATWOOT_API_TOKEN: Optional[str] = None
    CHATWOOT_ACCOUNT_ID: Optional[str] = None
    CHATWOOT_WEBHOOK_SECRET: Optional[str] = None

    # WhatsApp Configuration
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None

    # n8n Integration
    N8N_WEBHOOK_BASE_URL: str = "https://n8n.tucbbs.com.ar/webhook"
    N8N_WEBHOOK_URL: str = "https://n8n.tucbbs.com.ar/webhook"
    N8N_API_KEY: Optional[str] = None
    N8N_API_BASE_URL: str = "http://localhost:5678/api/v1"

    # Session Management
    SESSION_TTL_MINUTES: int = 60
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()