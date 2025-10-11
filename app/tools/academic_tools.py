"""
Herramientas académicas usando Pydantic Models
"""
from typing import Dict, Any, Optional
from app.database.academic_repository import academic_repository
from app.models import (
    HorariosRequest,
    HorariosResponse,
    InscripcionesRequest,
    InscripcionesResponse,
    ProfesorRequest,
    ProfesorResponse,
    AulaRequest,
    AulaResponse,
    CreditosVURequest,
    CreditosVUResponse
)
from app.utils.logger import get_logger
from pydantic import ValidationError

logger = get_logger(__name__)


class AcademicTools:
    """
    Herramientas académicas que usan Pydantic para validación
    """

    def __init__(self):
        self.repository = academic_repository

    async def consultar_horarios(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta horarios del alumno

        Parámetros esperados:
        - alumno_id: ID del alumno (requerido)
        - materia_nombre: (opcional) Nombre específico de materia
        - dia_semana: (opcional) Día específico de la semana (1-7)

        Respuesta:
        {
            "horarios": [
                {
                    "dia_semana": 1,
                    "materia_nombre": "Nativa Digital",
                    "materia_codigo": "ND-2025",
                    "comision": "COM-A",
                    "hora_inicio": "14:00",
                    "hora_fin": "16:00",
                    "aula": "R3",
                    "edificio": "Campus Principal",
                    "modalidad": "presencial",
                    "profesor_nombre": "García Martínez"
                }
            ],
            "total": 4
        }
        """
        try:
            # Crear Request Pydantic (con validación automática)
            request = HorariosRequest(
                alumno_id=params.get('alumno_id'),
                materia_nombre=params.get('materia_nombre'),
                dia_semana=params.get('dia_semana')
            )
            
            logger.info(f"Consultando horarios: alumno_id={request.alumno_id}")
            
            # Llamar al repository con el request validado
            response: HorariosResponse = await self.repository.get_horarios_alumno(request)
            
            # Convertir response a dict para mantener compatibilidad
            return response.dict()
            
        except ValidationError as e:
            logger.error(f"Error de validación en consultar_horarios: {e}")
            return None
        except Exception as e:
            logger.error(f"Error en consultar_horarios: {e}")
            return None

    async def ver_inscripciones(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ver inscripciones del alumno

        Parámetros esperados:
        - alumno_id: ID del alumno
        - estado: (opcional) Filtrar por estado

        Respuesta:
        {
            "materias": [
                {
                    "materia_id": "uuid",
                    "materia_nombre": "Nativa Digital",
                    "materia_codigo": "ND-2025",
                    "comision_id": "uuid",
                    "comision_codigo": "COM-A",
                    "estado": "cursando",
                    "fecha_inscripcion": "2025-08-01"
                }
            ],
            "total": 2
        }
        """
        try:
            # Crear Request Pydantic
            request = InscripcionesRequest(
                alumno_id=params.get('alumno_id'),
                estado=params.get('estado')
            )
            
            logger.info(f"Consultando inscripciones: alumno_id={request.alumno_id}")
            
            # Llamar al repository
            response: InscripcionesResponse = await self.repository.get_inscripciones(request)
            
            # Convertir a dict
            return response.dict()
            
        except ValidationError as e:
            logger.error(f"Error de validación en ver_inscripciones: {e}")
            return None
        except Exception as e:
            logger.error(f"Error en ver_inscripciones: {e}")
            return None

    async def buscar_profesor(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Buscar información de profesor

        Parámetros esperados:
        - profesor_nombre: (opcional) Nombre del profesor
        - materia_nombre: (opcional) Nombre de la materia

        Respuesta:
        {
            "profesor": {
                "id": "uuid",
                "nombre": "Juan Pérez",
                "email": "juan.perez@austral.edu.ar",
                "departamento": "Informática",
                "materias": ["Nativa Digital"]
            },
            "encontrado": true
        }
        """
        try:
            # Crear Request Pydantic
            request = ProfesorRequest(
                profesor_nombre=params.get('profesor_nombre') or params.get('nombre_profesor'),
                materia_nombre=params.get('materia') or params.get('materia_nombre')
            )
            
            logger.info(f"Buscando profesor: nombre={request.profesor_nombre}, materia={request.materia_nombre}")
            
            # Llamar al repository
            response: ProfesorResponse = await self.repository.get_profesor_info(request)
            
            # Convertir a dict
            return response.dict()
            
        except ValidationError as e:
            logger.error(f"Error de validación en buscar_profesor: {e}")
            return None
        except Exception as e:
            logger.error(f"Error en buscar_profesor: {e}")
            return None

    async def consultar_aula(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consultar información de aula

        Parámetros esperados:
        - aula: (opcional) Código del aula
        - materia_nombre: (opcional) Nombre de la materia

        Respuesta:
        {
            "aula": {
                "codigo_aula": "R3",
                "edificio": "Campus Principal",
                "capacidad": 40,
                "tipo": "Teórico",
                "materias": ["Nativa Digital"]
            },
            "encontrada": true
        }
        """
        try:
            # Crear Request Pydantic
            request = AulaRequest(
                aula=params.get('aula'),
                materia_nombre=params.get('materia') or params.get('materia_nombre')
            )
            
            logger.info(f"Consultando aula: aula={request.aula}, materia={request.materia_nombre}")
            
            # Llamar al repository
            response: AulaResponse = await self.repository.get_aula_info(request)
            
            # Convertir a dict
            return response.dict()
            
        except ValidationError as e:
            logger.error(f"Error de validación en consultar_aula: {e}")
            return None
        except Exception as e:
            logger.error(f"Error en consultar_aula: {e}")
            return None

    async def consultar_creditos_vu(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consultar créditos de Vida Universitaria
        
        Parámetros esperados:
        - alumno_id: ID del alumno

        Respuesta:
        {
            "creditos": {
                "creditos_actuales": 8,
                "creditos_necesarios": 10,
                "creditos_faltantes": 2,
                "porcentaje_completado": 80,
                "cumple_requisito": false
            }
        }
        """
        try:
            # Crear Request Pydantic
            request = CreditosVURequest(
                alumno_id=params.get('alumno_id')
            )
            
            logger.info(f"Consultando créditos VU: alumno_id={request.alumno_id}")
            
            # Llamar al repository
            response: CreditosVUResponse = await self.repository.get_creditos_vu(request)
            
            # Convertir a dict
            return response.dict()
            
        except ValidationError as e:
            logger.error(f"Error de validación en consultar_creditos_vu: {e}")
            return None
        except Exception as e:
            logger.error(f"Error en consultar_creditos_vu: {e}")
            return None
