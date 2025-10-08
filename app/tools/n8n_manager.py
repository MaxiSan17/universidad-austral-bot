from typing import Dict, Any, Optional
import httpx
import asyncio
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class N8NManager:
    """Gestor central para todas las comunicaciones con n8n"""

    def __init__(self):
        self.base_url = settings.N8N_WEBHOOK_BASE_URL
        self.api_key = settings.N8N_API_KEY
        self.timeout = 30.0

    async def call_webhook(self, webhook_path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Llama a un webhook de n8n de forma asíncrona

        Args:
            webhook_path: Ruta del webhook (ej: "academic/horarios")
            params: Parámetros a enviar al webhook

        Returns:
            Respuesta del webhook o None si hay error

        Estructura del webhook URL:
        {N8N_WEBHOOK_BASE_URL}/{webhook_path}

        Headers automáticos:
        - Content-Type: application/json
        - Authorization: Bearer {N8N_API_KEY} (si está configurada)
        - X-Timestamp: timestamp actual
        - X-Source: universidad-austral-bot
        """
        try:
            # Construir URL completa
            url = f"{self.base_url.rstrip('/')}/{webhook_path}"

            # Headers estándar
            headers = {
                "Content-Type": "application/json",
                "X-Source": "universidad-austral-bot",
                "X-Timestamp": str(int(asyncio.get_event_loop().time()))
            }

            # Agregar API key si está configurada
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Payload con metadatos
            payload = {
                "data": params,
                "metadata": {
                    "timestamp": headers["X-Timestamp"],
                    "source": "universidad-austral-bot",
                    "webhook_path": webhook_path
                }
            }

            logger.info(f"Llamando webhook n8n: {url}")
            logger.debug(f"Payload: {payload}")

            # Realizar llamada HTTP
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )

                # Verificar status code
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Webhook {webhook_path} exitoso")
                    return result

                elif response.status_code == 404:
                    logger.warning(f"Webhook {webhook_path} no encontrado (404)")
                    return None

                elif response.status_code >= 500:
                    logger.error(f"Error del servidor n8n: {response.status_code}")
                    return None

                else:
                    logger.warning(f"Respuesta inesperada del webhook: {response.status_code}")
                    return None

        except httpx.TimeoutException:
            logger.error(f"Timeout llamando webhook {webhook_path}")
            return None

        except httpx.RequestError as e:
            logger.error(f"Error de conexión con n8n: {e}")
            return None

        except Exception as e:
            logger.error(f"Error inesperado llamando webhook {webhook_path}: {e}")
            return None

    async def test_webhook(self, webhook_path: str) -> bool:
        """
        Prueba si un webhook está disponible

        Args:
            webhook_path: Ruta del webhook a probar

        Returns:
            True si el webhook responde, False caso contrario
        """
        try:
            test_params = {"test": True, "timestamp": int(asyncio.get_event_loop().time())}
            result = await self.call_webhook(webhook_path, test_params)
            return result is not None

        except Exception as e:
            logger.error(f"Error probando webhook {webhook_path}: {e}")
            return False

    async def get_available_webhooks(self) -> Dict[str, bool]:
        """
        Verifica qué webhooks están disponibles

        Returns:
            Diccionario con estado de cada webhook
        """
        webhooks = {
            # Académico
            "academic/consultar-horarios": False,
            "academic/inscripciones": False,
            "academic/profesores": False,
            "academic/aulas": False,
            "academic/notas": False,

            # Financiero
            "financial/estado-cuenta": False,
            "financial/creditos-vu": False,
            "financial/pagos": False,

            # Políticas
            "policies/syllabus": False,
            "policies/reglamentos": False,

            # Calendario
            "calendar/examenes": False,
            "calendar/eventos": False,
            "calendar/feriados": False
        }

        # Probar cada webhook
        for webhook_path in webhooks.keys():
            webhooks[webhook_path] = await self.test_webhook(webhook_path)

        logger.info(f"Estado de webhooks: {webhooks}")
        return webhooks

    def get_mock_response(self, webhook_path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Provee respuestas mock para desarrollo cuando n8n no está disponible

        Esta función permite desarrollar y probar sin tener n8n corriendo.
        En producción, las respuestas vendrán directamente de n8n.
        """
        mock_responses = {
            "academic/consultar-horarios": {
                "consultar-horarios": [
                    {
                        "materia": "Nativa Digital",
                        "dia": "Lunes",
                        "hora_inicio": "14:00",
                        "hora_fin": "16:00",
                        "aula": "R3",
                        "modalidad": "Presencial",
                        "profesor": "García Martínez"
                    },
                    {
                        "materia": "Programación I",
                        "dia": "Miércoles",
                        "hora_inicio": "16:00",
                        "hora_fin": "18:00",
                        "aula": "A4",
                        "modalidad": "Presencial",
                        "profesor": "Rodríguez"
                    }
                ]
            },

            "academic/inscripciones": {
                "materias": [
                    {
                        "nombre": "Nativa Digital",
                        "comision": "Comisión A",
                        "creditos": 6,
                        "estado": "Cursando"
                    },
                    {
                        "nombre": "Programación I",
                        "comision": "Comisión B",
                        "creditos": 6,
                        "estado": "Cursando"
                    }
                ]
            },

            "academic/profesores": {
                "profesor": "Prof. García Martínez",
                "email": "garcia.martinez@austral.edu.ar",
                "materias": ["Nativa Digital", "Desarrollo Web"]
            },

            "academic/aulas": {
                "aula": "Aula R3",
                "edificio": "Edificio Central",
                "piso": "Planta Baja",
                "capacidad": 30
            },

            "financial/estado-cuenta": {
                "deudas": [],
                "proximo_vencimiento": "2024-12-15",
                "monto_pendiente": 0,
                "estado": "Al día"
            },

            "financial/creditos-vu": {
                "creditos_actuales": 8,
                "creditos_necesarios": 10,
                "actividades": [
                    {"nombre": "Taller de Teatro", "creditos": 3, "estado": "Completado"},
                    {"nombre": "Voluntariado", "creditos": 5, "estado": "Completado"}
                ]
            },

            "calendar/examenes": {
                "examenes": [
                    {
                        "materia": "Nativa Digital",
                        "tipo": "Parcial 1",
                        "fecha": "2024-11-15",
                        "hora": "14:00",
                        "aula": "R3"
                    }
                ]
            }
        }

        response = mock_responses.get(webhook_path)
        if response:
            logger.info(f"Usando respuesta mock para {webhook_path}")
            return response

        logger.warning(f"No hay respuesta mock para {webhook_path}")
        return None