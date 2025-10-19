from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# CRITICAL: Setup LangSmith ANTES de cualquier import de LangChain
import os
from dotenv import load_dotenv
load_dotenv()

# Configurar LangSmith explícitamente ANTES de imports
# IMPORTANTE: Usar AMBOS formatos (LANGSMITH_* y LANGCHAIN_*)
raw_tracing_langsmith = os.getenv("LANGSMITH_TRACING", "false")
raw_tracing_langchain = os.getenv("LANGCHAIN_TRACING_V2", "false")

print(f"🔍 LangSmith Debug - RAW VALUES:")
print(f"  LANGSMITH_TRACING from .env: '{raw_tracing_langsmith}'")
print(f"  LANGCHAIN_TRACING_V2 from .env: '{raw_tracing_langchain}'")

# Normalizar ambos
tracing_enabled = False
if str(raw_tracing_langsmith).lower().strip() in ["true", "1", "yes", "on"]:
    tracing_enabled = True
if str(raw_tracing_langchain).lower().strip() in ["true", "1", "yes", "on"]:
    tracing_enabled = True

# Setear AMBOS formatos
if tracing_enabled:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    print(f"  ✅ ENABLED - Setting both to 'true'")
else:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    print(f"  ❌ DISABLED")

# API Key (puede estar en cualquiera de los dos formatos)
api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGSMITH_API_KEY"] = api_key
os.environ["LANGCHAIN_API_KEY"] = api_key

# Project
project = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT", "universidad-austral-bot")
os.environ["LANGSMITH_PROJECT"] = project
os.environ["LANGCHAIN_PROJECT"] = project

# Endpoint
endpoint = os.getenv("LANGSMITH_ENDPOINT") or os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
os.environ["LANGSMITH_ENDPOINT"] = endpoint
os.environ["LANGCHAIN_ENDPOINT"] = endpoint

print(f"\n🔍 LangSmith Final Config:")
print(f"  LANGSMITH_TRACING: {os.environ.get('LANGSMITH_TRACING')}")
print(f"  LANGCHAIN_TRACING_V2: {os.environ.get('LANGCHAIN_TRACING_V2')}")
print(f"  API_KEY: {api_key[:25]}... (len: {len(api_key)})")
print(f"  PROJECT: {project}")
print(f"  ENDPOINT: {endpoint}")
print(f"  Enabled: {tracing_enabled}\n")

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
        "langsmith_enabled": os.environ.get("LANGSMITH_TRACING") == "true"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Universidad Austral Bot iniciando...")
    logger.info(f"Ambiente: {settings.ENVIRONMENT}")
    
    # Verificar LangSmith
    if os.environ.get("LANGSMITH_TRACING") == "true":
        logger.info("✅ LangSmith tracing ACTIVO")
        logger.info(f"   Proyecto: {os.environ.get('LANGSMITH_PROJECT')}")
        logger.info(f"   Endpoint: {os.environ.get('LANGSMITH_ENDPOINT')}")
    else:
        logger.warning("⚠️ LangSmith tracing DESHABILITADO")

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
