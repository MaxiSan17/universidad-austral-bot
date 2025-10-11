"""
Repositorio de datos académicos - Consultas a Supabase con Pydantic Models
"""
from typing import Optional, List
from app.database.supabase_client import SupabaseClient
from app.utils.logger import get_logger
from app.models import (
    HorariosRequest,
    HorariosResponse,
    HorarioInfo,
    InscripcionesRequest,
    InscripcionesResponse,
    InscripcionInfo,
    ProfesorRequest,
    ProfesorResponse,
    ProfesorInfo,
    AulaRequest,
    AulaResponse,
    AulaInfo,
    CreditosVURequest,
    CreditosVUResponse,
    CreditosVUInfo,
    Modalidad,
    EstadoInscripcion
)
from app.core import (
    ValidationError,
    InvalidUUIDError,
    SupabaseError,
    RecordNotFoundError
)

logger = get_logger(__name__)


class AcademicRepository:
    """Repositorio para consultas académicas a Supabase usando Pydantic"""

    def __init__(self):
        self.client = SupabaseClient.get_client()

    # =====================================================
    # TOOL 1: GET HORARIOS ALUMNO
    # =====================================================

    async def get_horarios_alumno(self, request: HorariosRequest) -> HorariosResponse:
        """
        Obtiene los horarios del alumno usando la función SQL de Supabase
        
        Args:
            request: HorariosRequest validado con Pydantic
            
        Returns:
            HorariosResponse con horarios del alumno
            
        Raises:
            InvalidUUIDError: Si alumno_id es inválido
            SupabaseError: Si hay error en la consulta
        """
        try:
            logger.info(f"Consultando horarios para alumno {request.alumno_id}")
            
            # Llamar a la función SQL de Supabase
            response = self.client.rpc(
                'get_horarios_alumno',
                {'p_alumno_id': request.alumno_id}
            ).execute()
            
            if not response.data:
                logger.info(f"No se encontraron horarios para alumno {request.alumno_id}")
                return HorariosResponse(horarios=[], total=0)
            
            horarios_raw = response.data
            
            # Filtro por materia (si se especificó)
            if request.materia_nombre:
                horarios_raw = [
                    h for h in horarios_raw 
                    if request.materia_nombre.lower() in h.get('materia_nombre', '').lower()
                ]
            
            # Filtro por día (si se especificó)
            if request.dia_semana:
                horarios_raw = [
                    h for h in horarios_raw 
                    if h.get('dia_semana') == request.dia_semana
                ]
            
            # Convertir a modelos Pydantic
            horarios = []
            for h in horarios_raw:
                try:
                    horario = HorarioInfo(
                        dia_semana=h.get('dia_semana', 1),
                        materia_nombre=h.get('materia_nombre', 'N/A'),
                        materia_codigo=h.get('materia_codigo', 'N/A'),
                        comision=h.get('comision', 'N/A'),
                        hora_inicio=h.get('hora_inicio', '00:00'),
                        hora_fin=h.get('hora_fin', '00:00'),
                        aula=h.get('aula', 'N/A'),
                        edificio=h.get('edificio', 'Campus Principal'),
                        modalidad=Modalidad(h.get('modalidad', 'presencial')),
                        profesor_nombre=h.get('profesor_nombre')
                    )
                    horarios.append(horario)
                except Exception as e:
                    logger.error(f"Error creando HorarioInfo: {e}")
                    continue
            
            logger.info(f"Se encontraron {len(horarios)} horarios")
            
            return HorariosResponse(horarios=horarios, total=len(horarios))
            
        except Exception as e:
            logger.error(f"Error obteniendo horarios: {e}", exc_info=True)
            raise SupabaseError(str(e), operation="get_horarios_alumno")

    # =====================================================
    # TOOL 2: GET INSCRIPCIONES
    # =====================================================

    async def get_inscripciones(self, request: InscripcionesRequest) -> InscripcionesResponse:
        """
        Obtiene las materias en las que está inscripto el alumno
        
        Args:
            request: InscripcionesRequest validado
            
        Returns:
            InscripcionesResponse con inscripciones
        """
        try:
            logger.info(f"Consultando inscripciones para alumno {request.alumno_id}")
            
            # Obtener inscripciones
            query = self.client.table('inscripciones') \
                .select('id, estado, comision_id, asistencia_porcentaje, nota_cursada, fecha_inscripcion') \
                .eq('alumno_id', request.alumno_id)
            
            # Filtrar por estado si se especificó
            if request.estado:
                # Manejar tanto string como enum
                estado_value = request.estado.value if hasattr(request.estado, 'value') else request.estado
                query = query.eq('estado', estado_value)
            
            inscripciones = query.execute()
            
            if not inscripciones.data:
                logger.info(f"No se encontraron inscripciones para alumno {request.alumno_id}")
                return InscripcionesResponse(materias=[], total=0)
            
            logger.info(f"Encontradas {len(inscripciones.data)} inscripciones")
            
            materias = []
            for insc in inscripciones.data:
                try:
                    # Obtener comisión
                    comision_response = self.client.table('comisiones') \
                        .select('id, codigo_comision, materia_id, cuatrimestre') \
                        .eq('id', insc['comision_id']) \
                        .execute()
                    
                    if not comision_response.data or len(comision_response.data) == 0:
                        logger.warning(f"No se encontró comisión {insc['comision_id']}")
                        continue
                    
                    comision = comision_response.data[0]
                    
                    # Obtener materia
                    materia_response = self.client.table('materias') \
                        .select('id, nombre, codigo, carrera') \
                        .eq('id', comision['materia_id']) \
                        .execute()
                    
                    if not materia_response.data or len(materia_response.data) == 0:
                        logger.warning(f"No se encontró materia {comision['materia_id']}")
                        continue
                    
                    materia = materia_response.data[0]
                    
                    # Crear modelo Pydantic
                    inscripcion_info = InscripcionInfo(
                        materia_id=materia['id'],
                        materia_nombre=materia.get('nombre', 'N/A'),
                        materia_codigo=materia.get('codigo', 'N/A'),
                        comision_id=comision['id'],
                        comision_codigo=comision.get('codigo_comision', 'N/A'),
                        estado=EstadoInscripcion(insc.get('estado', 'cursando')),
                        fecha_inscripcion=insc.get('fecha_inscripcion')
                    )
                    
                    materias.append(inscripcion_info)
                    
                except Exception as e:
                    logger.error(f"Error procesando inscripción {insc.get('id')}: {e}")
                    continue
            
            logger.info(f"Se encontraron {len(materias)} materias válidas")
            return InscripcionesResponse(materias=materias, total=len(materias))
            
        except Exception as e:
            logger.error(f"Error obteniendo inscripciones: {e}", exc_info=True)
            raise SupabaseError(str(e), operation="get_inscripciones")

    # =====================================================
    # TOOL 3: GET PROFESOR INFO
    # =====================================================

    async def get_profesor_info(self, request: ProfesorRequest) -> ProfesorResponse:
        """
        Busca información de profesores
        
        Args:
            request: ProfesorRequest validado
            
        Returns:
            ProfesorResponse con información del profesor
        """
        try:
            logger.info(f"Buscando profesor: nombre={request.profesor_nombre}, materia={request.materia_nombre}")
            
            # TODO: Implementar búsqueda real cuando se tenga la estructura de BD
            # Por ahora devolver respuesta vacía
            
            return ProfesorResponse(
                profesor=None,
                encontrado=False
            )
            
        except Exception as e:
            logger.error(f"Error buscando profesor: {e}", exc_info=True)
            raise SupabaseError(str(e), operation="get_profesor_info")

    # =====================================================
    # TOOL 4: GET AULA INFO
    # =====================================================

    async def get_aula_info(self, request: AulaRequest) -> AulaResponse:
        """
        Consulta información sobre aulas
        
        Args:
            request: AulaRequest validado
            
        Returns:
            AulaResponse con información del aula
        """
        try:
            logger.info(f"Buscando aula: aula={request.aula}, materia={request.materia_nombre}")
            
            # TODO: Implementar búsqueda real cuando se tenga la estructura de BD
            # Por ahora devolver respuesta vacía
            
            return AulaResponse(
                aula=None,
                encontrada=False
            )
            
        except Exception as e:
            logger.error(f"Error buscando aula: {e}", exc_info=True)
            raise SupabaseError(str(e), operation="get_aula_info")

    # =====================================================
    # TOOL 5: GET CRÉDITOS VU
    # =====================================================

    async def get_creditos_vu(self, request: CreditosVURequest) -> CreditosVUResponse:
        """
        Obtiene los créditos de Vida Universitaria del alumno
        
        Args:
            request: CreditosVURequest validado
            
        Returns:
            CreditosVUResponse con créditos VU
        """
        try:
            logger.info(f"Consultando créditos VU para alumno {request.alumno_id}")
            
            # Consultar estado académico
            response = self.client.table('estado_academico') \
                .select('creditos_vu_totales, creditos_vu_requeridos') \
                .eq('alumno_id', request.alumno_id) \
                .execute()
            
            if not response.data or len(response.data) == 0:
                logger.info(f"No se encontró estado académico para alumno {request.alumno_id}")
                # Valores por defecto si no existe registro
                creditos_info = CreditosVUInfo(
                    creditos_actuales=0,
                    creditos_necesarios=10,
                    creditos_faltantes=10,
                    porcentaje_completado=0,
                    cumple_requisito=False
                )
                return CreditosVUResponse(creditos=creditos_info)
            
            estado = response.data[0]
            creditos_actuales = estado.get('creditos_vu_totales', 0) or 0
            creditos_necesarios = estado.get('creditos_vu_requeridos', 10) or 10
            creditos_faltantes = max(0, creditos_necesarios - creditos_actuales)
            porcentaje = min(100, int((creditos_actuales / creditos_necesarios) * 100)) if creditos_necesarios > 0 else 0
            cumple = creditos_actuales >= creditos_necesarios
            
            logger.info(f"Créditos VU: {creditos_actuales}/{creditos_necesarios}")
            
            # Crear modelo Pydantic (con validación automática)
            creditos_info = CreditosVUInfo(
                creditos_actuales=creditos_actuales,
                creditos_necesarios=creditos_necesarios,
                creditos_faltantes=creditos_faltantes,
                porcentaje_completado=porcentaje,
                cumple_requisito=cumple
            )
            
            return CreditosVUResponse(creditos=creditos_info)
            
        except Exception as e:
            logger.error(f"Error obteniendo créditos VU: {e}", exc_info=True)
            raise SupabaseError(str(e), operation="get_creditos_vu")


# Instancia global del repositorio
academic_repository = AcademicRepository()
