"""
Universidad Austral Bot - Sistema de Agentes Jerárquicos
Punto de entrada principal de la aplicación
"""

import sys
import os
import uvicorn
from pathlib import Path

# Agregar el directorio src al Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.api.main import app
from src.config.settings import settings

if __name__ == "__main__":
    print("🎓 Universidad Austral Bot - Iniciando servidor...")
    print(f"📍 Ambiente: {'desarrollo' if settings.debug else 'producción'}")
    print(f"🔗 API disponible en: http://localhost:8000")
    print(f"📚 Documentación: http://localhost:8000/docs")
    print("=" * 50)

    # Configuración del servidor
    config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": settings.debug,
        "log_level": "info" if not settings.debug else "debug",
        "access_log": True
    }

    # Ejecutar servidor
    uvicorn.run(**config)