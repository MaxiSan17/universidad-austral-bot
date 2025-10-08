from typing import Dict, Any, Optional
from app.tools.n8n_manager import N8NManager
from app.utils.logger import get_logger

N8N_BASE_URL = "https://n8n.tucbbs.com.ar/webhook"

logger = get_logger(__name__)

class AcademicTools:
    """Herramientas académicas que se conectan con n8n webhooks"""

    def __init__(self):
        self.n8n_manager = N8NManager()

    async def consultar_horarios(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta horarios del alumno

        Webhook n8n: {N8N_BASE_URL}/academic/consultar-horarios

        Parámetros esperados por n8n:
        - alumno_id: ID del alumno
        - materia_nombre: (opcional) Nombre específico de materia
        - dia: (opcional) Día específico de la semana

        Respuesta esperada de n8n:
        {
            "horarios": [
                {
                    "materia": "Nativa Digital",
                    "dia": "Lunes",
                    "hora_inicio": "14:00",
                    "hora_fin": "16:00",
                    "aula": "R3",
                    "modalidad": "Presencial",
                    "profesor": "García Martínez"
                }
            ]
        }
        """
        try:
            webhook_path = "consultar-horarios"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook consultar_horarios: {e}")
            return None

    async def ver_inscripciones(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ver inscripciones del alumno

        Webhook n8n: {N8N_BASE_URL}/academic/inscripciones

        Parámetros esperados por n8n:
        - alumno_id: ID del alumno

        Respuesta esperada de n8n:
        {
            "materias": [
                {
                    "nombre": "Nativa Digital",
                    "comision": "Comisión A",
                    "creditos": 6,
                    "estado": "Cursando"
                }
            ]
        }
        """
        try:
            webhook_path = "academic/inscripciones"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook ver_inscripciones: {e}")
            return None

    async def buscar_profesor(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Buscar información de profesor

        Webhook n8n: {N8N_BASE_URL}/academic/profesores

        Parámetros esperados por n8n:
        - materia: (opcional) Nombre de la materia
        - nombre_profesor: (opcional) Nombre del profesor

        Respuesta esperada de n8n:
        {
            "profesor": "Prof. García Martínez",
            "email": "garcia.martinez@austral.edu.ar",
            "materias": ["Nativa Digital", "Desarrollo Web"]
        }
        """
        try:
            webhook_path = "academic/profesores"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook buscar_profesor: {e}")
            return None

    async def consultar_aula(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consultar ubicación de aula

        Webhook n8n: {N8N_BASE_URL}/academic/aulas

        Parámetros esperados por n8n:
        - materia: (opcional) Nombre de la materia
        - aula: (opcional) Nombre específico del aula

        Respuesta esperada de n8n:
        {
            "aula": "Aula R3",
            "edificio": "Edificio Central",
            "piso": "Planta Baja",
            "capacidad": 30
        }
        """
        try:
            webhook_path = "academic/aulas"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook consultar_aula: {e}")
            return None

    async def consultar_notas(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consultar notas del alumno

        Webhook n8n: {N8N_BASE_URL}/academic/notas

        Parámetros esperados por n8n:
        - alumno_id: ID del alumno
        - materia: (opcional) Materia específica

        Respuesta esperada de n8n:
        {
            "notas": [
                {
                    "materia": "Nativa Digital",
                    "tipo": "Parcial 1",
                    "nota": 8.5,
                    "fecha": "2024-10-15"
                }
            ]
        }
        """
        try:
            webhook_path = "academic/notas"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook consultar_notas: {e}")
            return None