from typing import Dict, Any, Optional
from app.database.calendar_repository import calendar_repository
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CalendarTools:
    """
    Herramientas de calendario que llaman directamente a Supabase
    (sin pasar por n8n)
    """

    def __init__(self):
        self.repository = calendar_repository

    async def consultar_examenes(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta fechas de exámenes del alumno

        Parámetros esperados:
        - alumno_id: ID del alumno (requerido)
        - materia_nombre: (opcional) Nombre específico de materia
        - fecha_desde: (opcional) Fecha desde (YYYY-MM-DD)
        - fecha_hasta: (opcional) Fecha hasta (YYYY-MM-DD)

        Respuesta:
        {
            "examenes": [
                {
                    "materia": "Nativa Digital",
                    "tipo": "parcial",
                    "numero": 1,
                    "nombre": "Parcial 1",
                    "fecha": "2025-11-15",
                    "hora_inicio": "14:00:00",
                    "hora_fin": "16:00:00",
                    "aula": "R3",
                    "edificio": "Edificio Central",
                    "modalidad": "presencial",
                    "observaciones": "Temas 1 a 4"
                }
            ],
            "total": 8
        }
        """
        try:
            alumno_id = params.get('alumno_id')
            materia_nombre = params.get('materia_nombre') or params.get('materia')
            fecha_desde = params.get('fecha_desde')
            fecha_hasta = params.get('fecha_hasta')
            
            logger.info(f"Consultando exámenes: alumno_id={alumno_id}, materia={materia_nombre}")
            
            return await self.repository.get_examenes_alumno(
                alumno_id=alumno_id,
                materia_nombre=materia_nombre,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
        except Exception as e:
            logger.error(f"Error en consultar_examenes: {e}")
            return None

    async def calendario_academico(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta calendario académico general

        Parámetros esperados:
        - tipo_evento: (opcional) Tipo de evento a buscar
        - fecha_desde: (opcional) Fecha desde (YYYY-MM-DD)
        - fecha_hasta: (opcional) Fecha hasta (YYYY-MM-DD)

        Respuesta:
        {
            "eventos": [
                {
                    "tipo": "inicio_clases",
                    "titulo": "Inicio de Clases 2do Cuatrimestre",
                    "descripcion": "Comienza el segundo cuatrimestre...",
                    "fecha": "2025-08-01",
                    "metadata": {...}
                }
            ],
            "total": 5
        }
        """
        try:
            tipo_evento = params.get('tipo_evento')
            fecha_desde = params.get('fecha_desde') or params.get('fecha_inicio')
            fecha_hasta = params.get('fecha_hasta') or params.get('fecha_fin')
            
            logger.info(f"Consultando calendario: tipo={tipo_evento}, desde={fecha_desde}, hasta={fecha_hasta}")
            
            return await self.repository.get_calendario_academico(
                tipo_evento=tipo_evento,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
        except Exception as e:
            logger.error(f"Error en calendario_academico: {e}")
            return None

    async def proximos_examenes(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta los próximos exámenes del alumno (próximos 7 días por defecto)

        Parámetros esperados:
        - alumno_id: ID del alumno (requerido)
        - dias: (opcional) Cantidad de días a futuro (default: 7)

        Respuesta: Similar a consultar_examenes pero filtrado por fecha
        """
        try:
            alumno_id = params.get('alumno_id')
            dias = params.get('dias', 7)
            
            logger.info(f"Consultando próximos exámenes: alumno_id={alumno_id}, días={dias}")
            
            return await self.repository.get_proximos_examenes(
                alumno_id=alumno_id,
                dias=dias
            )
        except Exception as e:
            logger.error(f"Error en proximos_examenes: {e}")
            return None
