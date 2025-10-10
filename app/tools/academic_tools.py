from typing import Dict, Any, Optional
from app.database.academic_repository import academic_repository
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AcademicTools:
    """
    Herramientas académicas que ahora llaman directamente a Supabase
    (sin pasar por n8n)
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
                    "materia_nombre": "Nativa Digital",
                    "dia_semana": 1,
                    "hora_inicio": "14:00",
                    "hora_fin": "16:00",
                    "aula": "R3",
                    "edificio": "Edificio Central",
                    "modalidad": "presencial",
                    "tipo_clase": "teorica",
                    "profesor_nombre": "Profesor por confirmar"
                }
            ],
            "total": 4
        }
        """
        try:
            alumno_id = params.get('alumno_id')
            materia_nombre = params.get('materia_nombre')
            dia_semana = params.get('dia_semana')
            
            logger.info(f"Consultando horarios: alumno_id={alumno_id}, materia={materia_nombre}, dia={dia_semana}")
            
            return await self.repository.get_horarios_alumno(
                alumno_id=alumno_id,
                materia_nombre=materia_nombre,
                dia_semana=dia_semana
            )
        except Exception as e:
            logger.error(f"Error en consultar_horarios: {e}")
            return None

    async def ver_inscripciones(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ver inscripciones del alumno

        Parámetros esperados:
        - alumno_id: ID del alumno

        Respuesta:
        {
            "materias": [
                {
                    "nombre": "Nativa Digital",
                    "codigo": "ND-2025",
                    "comision": "COM-A",
                    "carrera": "Negocios Digitales",
                    "cuatrimestre": 2,
                    "estado": "cursando",
                    "asistencia": 100,
                    "nota_cursada": null
                }
            ],
            "total": 2
        }
        """
        try:
            alumno_id = params.get('alumno_id')
            
            logger.info(f"Consultando inscripciones: alumno_id={alumno_id}")
            
            return await self.repository.get_inscripciones(alumno_id=alumno_id)
        except Exception as e:
            logger.error(f"Error en ver_inscripciones: {e}")
            return None

    async def buscar_profesor(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Buscar información de profesor

        Parámetros esperados:
        - profesor_nombre: (opcional) Nombre del profesor
        - materia: (opcional) Nombre de la materia

        Respuesta:
        {
            "profesores": [
                {
                    "nombre": "Juan",
                    "apellido": "Pérez",
                    "nombre_completo": "Juan Pérez",
                    "email": "juan.perez@austral.edu.ar",
                    "telefono": "+54...",
                    "materia": "Nativa Digital",
                    "comision": "COM-A"
                }
            ],
            "total": 1
        }
        """
        try:
            profesor_nombre = params.get('profesor_nombre') or params.get('nombre_profesor')
            materia_nombre = params.get('materia') or params.get('materia_nombre')
            
            logger.info(f"Buscando profesor: nombre={profesor_nombre}, materia={materia_nombre}")
            
            return await self.repository.get_profesor_info(
                profesor_nombre=profesor_nombre,
                materia_nombre=materia_nombre
            )
        except Exception as e:
            logger.error(f"Error en buscar_profesor: {e}")
            return None

    async def consultar_aula(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consultar información de aula

        Parámetros esperados:
        - aula: (opcional) Código del aula
        - materia: (opcional) Nombre de la materia
        - alumno_id: (opcional) ID del alumno

        Respuesta:
        {
            "aulas": [
                {
                    "aula": "R3",
                    "edificio": "Edificio Central",
                    "materias": ["Nativa Digital"]
                }
            ],
            "total": 1
        }
        """
        try:
            aula = params.get('aula')
            materia_nombre = params.get('materia') or params.get('materia_nombre')
            alumno_id = params.get('alumno_id')
            
            logger.info(f"Consultando aula: aula={aula}, materia={materia_nombre}, alumno={alumno_id}")
            
            return await self.repository.get_aula_info(
                aula=aula,
                materia_nombre=materia_nombre,
                alumno_id=alumno_id
            )
        except Exception as e:
            logger.error(f"Error en consultar_aula: {e}")
            return None

    async def consultar_notas(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consultar notas del alumno
        
        NOTA: Esta tool aún no está implementada en el repository.
        Devuelve un placeholder por ahora.
        """
        logger.warning("consultar_notas aún no implementado")
        return {
            "notas": [],
            "total": 0,
            "message": "Función en desarrollo"
        }
