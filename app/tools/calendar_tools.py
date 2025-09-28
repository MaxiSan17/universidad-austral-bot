from typing import Dict, Any, Optional
from app.tools.n8n_manager import N8NManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CalendarTools:
    """Herramientas de calendario que se conectan con n8n webhooks"""

    def __init__(self):
        self.n8n_manager = N8NManager()

    async def consultar_examenes(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta fechas de exámenes

        Webhook n8n: {N8N_BASE_URL}/calendar/examenes

        Parámetros esperados por n8n:
        - alumno_id: ID del alumno
        - materia: (opcional) Materia específica
        - tipo_examen: (opcional) "parcial" | "final" | "recuperatorio"

        Respuesta esperada de n8n:
        {
            "examenes": [
                {
                    "materia": "Nativa Digital",
                    "tipo": "Parcial 1",
                    "fecha": "2024-11-15",
                    "hora": "14:00",
                    "aula": "R3",
                    "duracion": "2 horas",
                    "modalidad": "Presencial"
                }
            ],
            "total_examenes": 3
        }
        """
        try:
            webhook_path = "calendar/examenes"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook consultar_examenes: {e}")
            return None

    async def calendario_academico(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta el calendario académico

        Webhook n8n: {N8N_BASE_URL}/calendar/eventos

        Parámetros esperados por n8n:
        - tipo_evento: (opcional) "inicio_clases" | "finales" | "feriados" | "inscripciones"
        - fecha_inicio: (opcional) Fecha desde en formato YYYY-MM-DD
        - fecha_fin: (opcional) Fecha hasta en formato YYYY-MM-DD

        Respuesta esperada de n8n:
        {
            "eventos": [
                {
                    "nombre": "Inicio de Clases 2do Cuatrimestre",
                    "fecha": "2024-08-05",
                    "tipo": "inicio_clases",
                    "descripcion": "Comienzan las clases del segundo cuatrimestre"
                },
                {
                    "nombre": "Día del Trabajador",
                    "fecha": "2024-05-01",
                    "tipo": "feriado",
                    "descripcion": "Feriado nacional - No hay clases"
                }
            ],
            "proximos_eventos": [
                {
                    "nombre": "Exámenes Finales",
                    "fecha": "2024-12-02",
                    "dias_restantes": 25
                }
            ]
        }
        """
        try:
            webhook_path = "calendar/eventos"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook calendario_academico: {e}")
            return None

    async def consultar_feriados(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta feriados y días no laborables

        Webhook n8n: {N8N_BASE_URL}/calendar/feriados

        Parámetros esperados por n8n:
        - año: (opcional) Año específico (default: año actual)
        - mes: (opcional) Mes específico

        Respuesta esperada de n8n:
        {
            "feriados": [
                {
                    "fecha": "2024-12-25",
                    "nombre": "Navidad",
                    "tipo": "nacional",
                    "hay_clases": false
                },
                {
                    "fecha": "2024-12-24",
                    "nombre": "Nochebuena",
                    "tipo": "institucional",
                    "hay_clases": false
                }
            ],
            "proximo_feriado": {
                "fecha": "2024-12-25",
                "nombre": "Navidad",
                "dias_restantes": 35
            }
        }
        """
        try:
            webhook_path = "calendar/feriados"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook consultar_feriados: {e}")
            return None

    async def inscripciones_fechas(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta fechas de inscripciones

        Webhook n8n: {N8N_BASE_URL}/calendar/inscripciones

        Parámetros esperados por n8n:
        - tipo_inscripcion: (opcional) "materias" | "examenes" | "actividades"
        - cuatrimestre: (opcional) "1" | "2"

        Respuesta esperada de n8n:
        {
            "inscripciones": [
                {
                    "tipo": "Inscripción a Materias",
                    "fecha_inicio": "2024-11-15",
                    "fecha_fin": "2024-11-30",
                    "estado": "abierta",
                    "cuatrimestre": "1er Cuatrimestre 2025",
                    "url_inscripcion": "https://inscripciones.austral.edu.ar"
                }
            ],
            "proximas_inscripciones": [
                {
                    "tipo": "Exámenes Finales",
                    "fecha_apertura": "2024-11-01",
                    "dias_restantes": 5
                }
            ]
        }
        """
        try:
            webhook_path = "calendar/inscripciones"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook inscripciones_fechas: {e}")
            return None