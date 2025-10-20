from typing import Dict, Any, Optional
import httpx
from app.utils.logger import get_logger

logger = get_logger(__name__)

class PoliciesTools:
    """
    Herramientas de políticas y reglamentos con búsqueda vectorial en Supabase

    Este módulo se conecta a un flujo n8n que:
    1. Vectoriza la consulta del usuario
    2. Busca por similitud semántica en la base vectorizada de Supabase
    3. Procesa la respuesta con un LLM integrado
    4. Retorna la respuesta final formateada
    """

    def __init__(self):
        # Webhook específico con LLM + búsqueda vectorial integrada
        self.webhook_url = "https://n8n.tucbbs.com.ar/webhook/a4c5728a-9853-424d-bb8d-44d2ec68d87e"
        self.timeout = 60.0  # 60s porque incluye vectorización + LLM

    async def consultar_politicas(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta políticas, reglamentos y syllabi mediante búsqueda vectorial

        Este método envía la consulta del usuario a n8n, que:
        - Vectoriza la pregunta usando embeddings
        - Busca documentos similares en Supabase (vector similarity search)
        - Procesa los resultados con un LLM para generar respuesta contextual
        - Retorna respuesta final con fuentes

        Parámetros esperados:
        - consulta: Pregunta del usuario (requerido)
        - alumno_id: (opcional) ID del alumno para contexto personalizado
        - materia: (opcional) Filtrar por materia específica
        - tipo: (opcional) Tipo de documento ("syllabus", "reglamento", "procedimiento")

        Respuesta esperada de n8n:
        {
            "respuesta": "Texto de respuesta generado por LLM con contexto",
            "fuentes": [
                {
                    "documento": "Reglamento Académico 2025",
                    "seccion": "Artículo 15 - Asistencias",
                    "similitud": 0.92,
                    "url": "https://docs.austral.edu.ar/reglamento-2025"
                }
            ],
            "confidence": 0.89,
            "documentos_encontrados": 3
        }

        Ejemplos de consultas:
        - "¿Cuál es la asistencia mínima requerida?"
        - "¿Qué temas se ven en el syllabus de Nativa Digital?"
        - "¿Cómo solicito un certificado de alumno regular?"
        """
        try:
            # Validar que venga la consulta
            if not params.get('consulta'):
                logger.error("Falta parámetro 'consulta' en consultar_politicas")
                return {
                    "error": "Parámetro 'consulta' es requerido",
                    "respuesta": "No se pudo procesar la consulta porque falta el texto de la pregunta."
                }

            logger.info(f"🔍 Consultando políticas con búsqueda vectorial: {params.get('consulta')[:100]}...")

            # Construir payload para n8n
            payload = {
                "consulta": params.get('consulta'),
                "alumno_id": params.get('alumno_id'),
                "materia": params.get('materia'),
                "tipo": params.get('tipo'),
                "timestamp": str(int(__import__('time').time()))
            }

            # Headers
            headers = {
                "Content-Type": "application/json",
                "X-Source": "universidad-austral-bot"
            }

            # Llamada HTTP a n8n con timeout extendido
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers
                )

                logger.info(f"Status code de n8n (políticas): {response.status_code}")
                logger.debug(f"Response body completo: {response.text[:500]}")

                if response.status_code == 200:
                    try:
                        # n8n puede retornar array o objeto, manejar ambos casos
                        result = response.json()

                        # Si es un array, tomar el primer elemento
                        if isinstance(result, list):
                            if len(result) > 0:
                                result = result[0]
                                logger.info(f"📦 n8n retornó array, usando primer elemento")
                            else:
                                logger.error("❌ n8n retornó array vacío")
                                return {
                                    "error": "empty_array",
                                    "respuesta": "No encontré información relevante sobre tu consulta. ¿Podés reformular la pregunta?"
                                }

                        # Normalizar estructura: n8n retorna {"output": "..."}
                        # pero necesitamos {"respuesta": "..."}
                        if 'output' in result and 'respuesta' not in result:
                            logger.info("📝 Normalizando estructura: output → respuesta")
                            result['respuesta'] = result['output']

                        # Validar que tenga respuesta
                        if not result.get('respuesta'):
                            logger.error(f"❌ Respuesta sin campo 'respuesta' ni 'output': {result}")
                            return {
                                "error": "missing_response_field",
                                "respuesta": "No pude obtener una respuesta del sistema. Por favor, intenta de nuevo."
                            }

                        logger.info(f"✅ Búsqueda vectorial exitosa - Respuesta: {len(result['respuesta'])} chars")
                        return result

                    except ValueError as e:
                        logger.error(f"❌ Error parseando JSON de n8n: {e}")
                        logger.error(f"Response text: {response.text}")
                        return {
                            "error": "json_parse_error",
                            "respuesta": "Hubo un error procesando la respuesta. Por favor, intenta de nuevo."
                        }
                else:
                    logger.error(f"Error en webhook políticas: {response.status_code} - {response.text}")
                    return {
                        "error": f"Error del servidor: {response.status_code}",
                        "respuesta": "No pude procesar tu consulta en este momento. Por favor, intenta de nuevo."
                    }

        except httpx.TimeoutException:
            logger.error(f"Timeout en consultar_politicas (>{self.timeout}s)")
            return {
                "error": "timeout",
                "respuesta": "La búsqueda está tardando más de lo esperado. Por favor, intenta con una consulta más específica."
            }
        except Exception as e:
            logger.error(f"Error en consultar_politicas: {e}", exc_info=True)
            return {
                "error": str(e),
                "respuesta": "Ocurrió un error al procesar tu consulta. Por favor, intenta de nuevo."
            }

    # ==========================================
    # MÉTODOS LEGACY (mantener por compatibilidad)
    # ==========================================

    async def buscar_syllabus(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        LEGACY: Usa consultar_politicas() con tipo='syllabus'

        Busca información específica en el syllabus de una materia
        """
        try:
            logger.info(f"Redirigiendo buscar_syllabus a consultar_politicas")

            # Construir consulta para búsqueda vectorial
            materia = params.get('materia', '')
            consulta_especifica = params.get('consulta_especifica', '')

            consulta = f"Buscar información del syllabus de {materia}"
            if consulta_especifica:
                consulta += f": {consulta_especifica}"

            return await self.consultar_politicas({
                'consulta': consulta,
                'materia': materia,
                'tipo': 'syllabus',
                'alumno_id': params.get('alumno_id')
            })

        except Exception as e:
            logger.error(f"Error en buscar_syllabus: {e}")
            return None

    async def consultar_reglamento(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        LEGACY: Usa consultar_politicas() con tipo='reglamento'

        Consulta reglamentos académicos
        """
        try:
            logger.info(f"Redirigiendo consultar_reglamento a consultar_politicas")

            tipo_reglamento = params.get('tipo_reglamento', 'general')
            consulta_especifica = params.get('consulta_especifica', '')

            consulta = f"Buscar en reglamento {tipo_reglamento}"
            if consulta_especifica:
                consulta += f": {consulta_especifica}"

            return await self.consultar_politicas({
                'consulta': consulta,
                'tipo': 'reglamento',
                'alumno_id': params.get('alumno_id')
            })

        except Exception as e:
            logger.error(f"Error en consultar_reglamento: {e}")
            return None

    async def buscar_procedimiento(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        LEGACY: Usa consultar_politicas() con tipo='procedimiento'

        Busca procedimientos administrativos
        """
        try:
            logger.info(f"Redirigiendo buscar_procedimiento a consultar_politicas")

            tipo_procedimiento = params.get('tipo_procedimiento', '')
            detalles = params.get('detalles', '')

            consulta = f"Buscar procedimiento: {tipo_procedimiento}"
            if detalles:
                consulta += f". {detalles}"

            return await self.consultar_politicas({
                'consulta': consulta,
                'tipo': 'procedimiento',
                'alumno_id': params.get('alumno_id')
            })

        except Exception as e:
            logger.error(f"Error en buscar_procedimiento: {e}")
            return None

    async def consultar_becas(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        LEGACY: Usa consultar_politicas() con tipo='becas'

        Consulta información sobre becas disponibles
        """
        try:
            logger.info(f"Redirigiendo consultar_becas a consultar_politicas")

            tipo_beca = params.get('tipo_beca', 'todas')

            consulta = f"Información sobre becas: {tipo_beca}"

            return await self.consultar_politicas({
                'consulta': consulta,
                'tipo': 'becas',
                'alumno_id': params.get('alumno_id')
            })

        except Exception as e:
            logger.error(f"Error en consultar_becas: {e}")
            return None