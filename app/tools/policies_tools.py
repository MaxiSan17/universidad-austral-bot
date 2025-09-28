from typing import Dict, Any, Optional
from app.tools.n8n_manager import N8NManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

class PoliciesTools:
    """Herramientas de políticas y reglamentos que se conectan con n8n webhooks"""

    def __init__(self):
        self.n8n_manager = N8NManager()

    async def buscar_syllabus(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca información específica en el syllabus de una materia

        Webhook n8n: {N8N_BASE_URL}/policies/syllabus

        Parámetros esperados por n8n:
        - materia: Nombre de la materia
        - consulta_especifica: (opcional) Consulta específica sobre el syllabus

        Respuesta esperada de n8n:
        {
            "materia": "Nativa Digital",
            "contenido": {
                "objetivos": "Desarrollar aplicaciones web modernas...",
                "evaluacion": "2 parciales (70%) + Trabajos prácticos (30%)",
                "bibliografia": [
                    "JavaScript: The Good Parts - Douglas Crockford",
                    "React Documentation"
                ],
                "temas": [
                    "Introducción a React",
                    "Estado y Props",
                    "Hooks"
                ]
            },
            "url_completo": "https://syllabus.austral.edu.ar/nativa-digital"
        }
        """
        try:
            webhook_path = "policies/syllabus"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook buscar_syllabus: {e}")
            return None

    async def consultar_reglamento(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta reglamentos académicos

        Webhook n8n: {N8N_BASE_URL}/policies/reglamentos

        Parámetros esperados por n8n:
        - tipo_reglamento: "academico" | "evaluacion" | "asistencia" | "general"
        - consulta_especifica: (opcional) Consulta específica

        Respuesta esperada de n8n:
        {
            "tipo": "academico",
            "seccion": "Evaluaciones",
            "contenido": "Los exámenes parciales...",
            "articulos": [
                {
                    "numero": "Art. 15",
                    "texto": "La asistencia mínima requerida es del 75%"
                }
            ],
            "url_completo": "https://reglamentos.austral.edu.ar/academico"
        }
        """
        try:
            webhook_path = "policies/reglamentos"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook consultar_reglamento: {e}")
            return None

    async def buscar_procedimiento(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca procedimientos administrativos

        Webhook n8n: {N8N_BASE_URL}/policies/procedimientos

        Parámetros esperados por n8n:
        - tipo_procedimiento: "inscripcion" | "certificados" | "cambio_materia" | "baja"
        - detalles: (opcional) Detalles específicos del procedimiento

        Respuesta esperada de n8n:
        {
            "procedimiento": "Solicitud de Certificado",
            "pasos": [
                "1. Completar formulario online",
                "2. Adjuntar documentación requerida",
                "3. Pagar arancel correspondiente",
                "4. Esperar confirmación por email"
            ],
            "requisitos": [
                "Estar al día con las cuotas",
                "Tener materias aprobadas"
            ],
            "tiempo_estimado": "5-7 días hábiles",
            "costo": "$25000",
            "formulario_url": "https://formularios.austral.edu.ar/certificados"
        }
        """
        try:
            webhook_path = "policies/procedimientos"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook buscar_procedimiento: {e}")
            return None

    async def consultar_becas(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta información sobre becas disponibles

        Webhook n8n: {N8N_BASE_URL}/policies/becas

        Parámetros esperados por n8n:
        - tipo_beca: (opcional) "merito" | "necesidad" | "deporte" | "todas"
        - alumno_id: (opcional) ID del alumno para consultas personalizadas

        Respuesta esperada de n8n:
        {
            "becas_disponibles": [
                {
                    "nombre": "Beca por Mérito Académico",
                    "descripcion": "Para estudiantes con promedio superior a 8.5",
                    "porcentaje_descuento": 50,
                    "requisitos": [
                        "Promedio mínimo 8.5",
                        "Materias al día"
                    ],
                    "fecha_limite": "2024-12-01",
                    "estado_postulacion": "Abierta"
                }
            ],
            "becas_del_alumno": [
                {
                    "nombre": "Beca Deportiva",
                    "estado": "Activa",
                    "descuento": 30,
                    "vigencia": "2024-12-31"
                }
            ]
        }
        """
        try:
            webhook_path = "policies/becas"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook consultar_becas: {e}")
            return None