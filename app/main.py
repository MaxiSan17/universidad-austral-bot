from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# CRITICAL: Setup LangSmith ANTES de cualquier import de LangChain
import os
from dotenv import load_dotenv
load_dotenv()

# Configurar LangSmith explícitamente ANTES de imports
# IMPORTANTE: Normalizar el valor de TRACING_V2 a string "true" o "false"
raw_tracing = os.getenv("LANGCHAIN_TRACING_V2", "false")
tracing_value = str(raw_tracing).lower().strip()

print(f"🔍 LangSmith Debug - RAW VALUES:")
print(f"  RAW from .env: '{raw_tracing}' (type: {type(raw_tracing).__name__})")
print(f"  After lower/strip: '{tracing_value}'")

if tracing_value in ["true", "1", "yes", "on"]:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    print(f"  ✅ SET TO: 'true'")
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    print(f"  ❌ SET TO: 'false' (was: '{tracing_value}')")

os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "universidad-austral-bot")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

print(f"\n🔍 LangSmith Config:")
print(f"  LANGCHAIN_TRACING_V2: {os.environ.get('LANGCHAIN_TRACING_V2')}")
print(f"  LANGCHAIN_API_KEY: {os.environ.get('LANGCHAIN_API_KEY', '')[:25]}... (len: {len(os.environ.get('LANGCHAIN_API_KEY', ''))})")
print(f"  LANGCHAIN_PROJECT: {os.environ.get('LANGCHAIN_PROJECT')}")
print(f"  LANGCHAIN_ENDPOINT: {os.environ.get('LANGCHAIN_ENDPOINT')}")
print(f"  Enabled check: {os.environ.get('LANGCHAIN_TRACING_V2') == 'true'}\n")

# AHORA sí importar el resto
from app.core.config import settings
from app.integrations.webhook_handlers import webhook_router
from app.utils.logger import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universidad Austral Bot",
    description="Sistema de agentes LangGraph para atención estudiantil",
    version="2.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/webhook")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "langsmith_enabled": os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Universidad Austral Bot iniciando...")
    logger.info(f"Ambiente: {settings.ENVIRONMENT}")
    
    # Verificar LangSmith
    if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
        logger.info("✅ LangSmith tracing ACTIVO")
        logger.info(f"   Proyecto: {os.environ.get('LANGCHAIN_PROJECT')}")
        logger.info(f"   Endpoint: {os.environ.get('LANGCHAIN_ENDPOINT')}")
    else:
        logger.warning("⚠️ LangSmith tracing DESHABILITADO")
        logger.warning(f"   Valor actual: '{os.environ.get('LANGCHAIN_TRACING_V2')}'")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Universidad Austral Bot finalizando...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
