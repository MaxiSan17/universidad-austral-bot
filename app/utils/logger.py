import logging
import sys
from typing import Optional
from app.core.config import settings

def setup_logging() -> None:
    """Configura el sistema de logging global"""

    # Configurar el formato
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configurar el nivel de logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configurar el logger raíz
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", encoding="utf-8")
        ]
    )

    # Silenciar loggers ruidosos
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configurado - Nivel: {settings.LOG_LEVEL}")

def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger con el nombre especificado"""
    return logging.getLogger(name)