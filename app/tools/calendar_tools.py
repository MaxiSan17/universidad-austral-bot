"""
Herramientas de calendario usando Pydantic Models
"""
from typing import Dict, Any, Optional
from datetime import datetime
from app.database.calendar_repository import calendar_repository
from app.models import (
    ExamenesRequest,
    ExamenesResponse,
    CalendarioAcademicoRequest,
    CalendarioAcademicoResponse,
    ProximosExamenesRequest,
    TipoExamen
)
from app.utils.logger import get_logger
from pydantic import ValidationError

logger = get_logger(__name__)


class CalendarTools:
    """
    Herramientas de calendario que usan Pydantic para validación
    """

    def __init__(self):
        self.repository = calendar_repository

    async def consultar_examenes(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta fechas de exámenes del alumno

        Parámetros esperados:
        - alumno_id: ID del alumno (requerido)
        - materia_nombre: (opcional) Nombre específico de materia
        - fecha_desde: (opcional) Fecha desde (YYYY-MM-DD o date object)
        - fecha_hasta: (opcional) Fecha hasta (YYYY-MM-DD o date object)
        - tipo_examen: (opcional) Tipo de examen

        Respuesta:
        {
            "examenes": [
                {
                    "materia": "Nativa Digital",
                    "materia_codigo": "ND-2025",
                    "comision": "COM-A",
                    "tipo": "parcial",
                    "numero": 1,
                    "nombre": "Parcial 1",
                    "fecha": "2025-11-15",
                    "hora_inicio": "14:00",
                    "hora_fin": "16:00",
                    "aula": "R3",
                    "edificio": "Campus Principal",
                    "modalidad": "presencial",
                    "observaciones": "Temas 1 a 4"
                }
            ],
            "total": 8
        }
        """
        try:
            # Parsear fechas si vienen como string
            fecha_desde = params.get('fecha_desde')
            fecha_hasta = params.get('fecha_hasta')
            
            if fecha_desde and isinstance(fecha_desde, str):
                try:
                    fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                except ValueError:
                    fecha_desde = None
            
            if fecha_hasta and isinstance(fecha_hasta, str):
                try:
                    fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                except ValueError:
                    fecha_hasta = None
            
            # Parsear tipo de examen si viene como string
            tipo_examen = params.get('tipo_examen')
            if tipo_examen and isinstance(tipo_examen, str):
                try:
                    tipo_examen = TipoExamen(tipo_examen)
                except ValueError:
                    tipo_examen = None
            
            # Crear Request Pydantic (con validación automática)
            request = ExamenesRequest(
                alumno_id=params.get('alumno_id'),
                materia_nombre=params.get('materia_nombre') or params.get('materia'),
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                tipo_examen=tipo_examen
            )
            
            logger.info(f"Consultando exámenes: alumno_id={request.alumno_id}, materia={request.materia_nombre}")
            
            # Llamar al repository con el request validado
            response: ExamenesResponse = await self.repository.get_examenes_alumno(request)
            
            # Convertir response a dict para mantener compatibilidad
            return response.dict()
            
        except ValidationError as e:
            logger.error(f"Error de validación en consultar_examenes: {e}")
            return None
        except Exception as e:
            logger.error(f"Error en consultar_examenes: {e}")
            return None

    async def calendario_academico(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta calendario académico general

        Parámetros esperados:
        - tipo_evento: (opcional) Tipo de evento a buscar
        - fecha_desde: (opcional) Fecha desde (YYYY-MM-DD o date object)
        - fecha_hasta: (opcional) Fecha hasta (YYYY-MM-DD o date object)

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
            # Parsear fechas si vienen como string
            fecha_desde = params.get('fecha_desde') or params.get('fecha_inicio')
            fecha_hasta = params.get('fecha_hasta') or params.get('fecha_fin')
            
            if fecha_desde and isinstance(fecha_desde, str):
                try:
                    fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                except ValueError:
                    fecha_desde = None
            
            if fecha_hasta and isinstance(fecha_hasta, str):
                try:
                    fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                except ValueError:
                    fecha_hasta = None
            
            # Crear Request Pydantic
            request = CalendarioAcademicoRequest(
                tipo_evento=params.get('tipo_evento'),
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
            
            logger.info(f"Consultando calendario: tipo={request.tipo_evento}, desde={request.fecha_desde}, hasta={request.fecha_hasta}")
            
            # Llamar al repository
            response: CalendarioAcademicoResponse = await self.repository.get_calendario_academico(request)
            
            # Convertir a dict
            return response.dict()
            
        except ValidationError as e:
            logger.error(f"Error de validación en calendario_academico: {e}")
            return None
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
            # Crear Request Pydantic
            request = ProximosExamenesRequest(
                alumno_id=params.get('alumno_id'),
                dias=params.get('dias', 7)
            )
            
            logger.info(f"Consultando próximos exámenes: alumno_id={request.alumno_id}, días={request.dias}")
            
            # Llamar al repository
            response: ExamenesResponse = await self.repository.get_proximos_examenes(request)
            
            # Convertir a dict
            return response.dict()
            
        except ValidationError as e:
            logger.error(f"Error de validación en proximos_examenes: {e}")
            return None
        except Exception as e:
            logger.error(f"Error en proximos_examenes: {e}")
            return None
