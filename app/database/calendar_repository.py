"""
Repositorio de calendario y exámenes - Consultas a Supabase con Pydantic Models
"""
from typing import Optional, List
from datetime import datetime, date, timedelta
from app.database.supabase_client import SupabaseClient
from app.utils.logger import get_logger
from app.models import (
    ExamenesRequest,
    ExamenesResponse,
    ExamenInfo,
    CalendarioAcademicoRequest,
    CalendarioAcademicoResponse,
    EventoCalendario,
    ProximosExamenesRequest,
    TipoExamen,
    Modalidad
)
from app.core import (
    ValidationError,
    InvalidUUIDError,
    SupabaseError,
    TIPOS_EXAMEN
)

logger = get_logger(__name__)


class CalendarRepository:
    """Repositorio para consultas de calendario y exámenes usando Pydantic"""

    def __init__(self):
        self.client = SupabaseClient.get_client()

    # =====================================================
    # TOOL 1: GET EXÁMENES ALUMNO
    # =====================================================

    async def get_examenes_alumno(self, request: ExamenesRequest) -> ExamenesResponse:
        """
        Obtiene los exámenes del alumno
        
        Args:
            request: ExamenesRequest validado con Pydantic
            
        Returns:
            ExamenesResponse con exámenes del alumno
            
        Raises:
            InvalidUUIDError: Si alumno_id es inválido
            SupabaseError: Si hay error en la consulta
        """
        try:
            logger.info(f"Consultando exámenes para alumno {request.alumno_id}")
            
            # Obtener inscripciones del alumno
            inscripciones = self.client.table('inscripciones') \
                .select('comision_id') \
                .eq('alumno_id', request.alumno_id) \
                .execute()
            
            if not inscripciones.data:
                logger.info(f"Alumno {request.alumno_id} no tiene inscripciones")
                return ExamenesResponse(examenes=[], total=0)
            
            comision_ids = [insc['comision_id'] for insc in inscripciones.data]
            logger.info(f"Alumno tiene {len(comision_ids)} comisiones")
            
            # Obtener exámenes de esas comisiones
            query = self.client.table('examenes') \
                .select('id, tipo, numero, fecha, hora_inicio, hora_fin, aula, modalidad, observaciones, comision_id') \
                .in_('comision_id', comision_ids) \
                .order('fecha', desc=False)
            
            # Filtrar por tipo si se especificó
            if request.tipo_examen:
                # Manejar tanto string como enum
                tipo_value = request.tipo_examen.value if hasattr(request.tipo_examen, 'value') else request.tipo_examen
                query = query.eq('tipo', tipo_value)
            
            # Filtrar por fechas si se especificaron
            if request.fecha_desde:
                query = query.gte('fecha', request.fecha_desde.isoformat())
            if request.fecha_hasta:
                query = query.lte('fecha', request.fecha_hasta.isoformat())
            
            examenes_response = query.execute()
            
            if not examenes_response.data:
                logger.info(f"No se encontraron exámenes para alumno {request.alumno_id}")
                return ExamenesResponse(examenes=[], total=0)
            
            logger.info(f"Se encontraron {len(examenes_response.data)} exámenes")

            # Enriquecer con datos de materia
            examenes = []
            for examen in examenes_response.data:
                try:
                    # Obtener comisión
                    comision_response = self.client.table('comisiones') \
                        .select('codigo_comision, materia_id') \
                        .eq('id', examen['comision_id']) \
                        .execute()
                    
                    if not comision_response.data or len(comision_response.data) == 0:
                        logger.warning(f"No se encontró comisión {examen['comision_id']}")
                        continue
                    
                    comision = comision_response.data[0]
                    
                    # Obtener materia
                    materia_response = self.client.table('materias') \
                        .select('nombre, codigo') \
                        .eq('id', comision['materia_id']) \
                        .execute()
                    
                    if not materia_response.data or len(materia_response.data) == 0:
                        logger.warning(f"No se encontró materia {comision['materia_id']}")
                        continue
                    
                    materia = materia_response.data[0]
                    materia_nombre_db = materia.get('nombre', 'N/A')
                    
                    # Filtrar por materia si se especificó
                    if request.materia_nombre and request.materia_nombre.lower() not in materia_nombre_db.lower():
                        continue
                    
                    # Formatear nombre del examen
                    tipo_examen = TipoExamen(examen['tipo'])
                    nombre_examen = self._format_exam_name(tipo_examen, examen.get('numero'))
                    
                    # Parsear fecha
                    fecha_examen = examen['fecha']
                    if isinstance(fecha_examen, str):
                        fecha_examen = datetime.strptime(fecha_examen, '%Y-%m-%d').date()
                    
                    # Formatear horarios a HH:MM (eliminar segundos si vienen)
                    hora_inicio = str(examen['hora_inicio'])[:5] if examen.get('hora_inicio') else '00:00'
                    hora_fin = str(examen['hora_fin'])[:5] if examen.get('hora_fin') else '00:00'
                    
                    # Crear modelo Pydantic
                    examen_info = ExamenInfo(
                        materia=materia_nombre_db,
                        materia_codigo=materia.get('codigo', 'N/A'),
                        comision=comision.get('codigo_comision', 'N/A'),
                        tipo=tipo_examen,
                        numero=examen.get('numero'),
                        nombre=nombre_examen,
                        fecha=fecha_examen,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        aula=examen.get('aula', 'A confirmar'),
                        modalidad=Modalidad(examen.get('modalidad', 'presencial')),
                        observaciones=examen.get('observaciones')
                    )
                    
                    examenes.append(examen_info)
                
                except Exception as e:
                    logger.error(f"Error procesando examen {examen.get('id')}: {e}")
                    continue

            logger.info(f"Se formatearon {len(examenes)} exámenes exitosamente")

            # NUEVO: Si solo_proximo=True, retornar solo el primer examen
            if request.solo_proximo and examenes:
                logger.info(f"🎯 Solo próximo activado: retornando solo el examen más cercano")
                examenes = [examenes[0]]

            return ExamenesResponse(examenes=examenes, total=len(examenes))
            
        except Exception as e:
            logger.error(f"Error obteniendo exámenes: {e}", exc_info=True)
            raise SupabaseError(str(e), operation="get_examenes_alumno")

    def _format_exam_name(self, tipo: TipoExamen, numero: Optional[int]) -> str:
        """Formatea el nombre del examen"""
        nombre_base = TIPOS_EXAMEN.get(tipo.value, tipo.value.capitalize())
        
        if numero:
            return f"{nombre_base} {numero}"
        return nombre_base

    # =====================================================
    # TOOL 2: GET CALENDARIO ACADÉMICO
    # =====================================================

    async def get_calendario_academico(self, request: CalendarioAcademicoRequest) -> CalendarioAcademicoResponse:
        """
        Obtiene eventos del calendario académico usando la tabla vectorizada
        
        Args:
            request: CalendarioAcademicoRequest validado
            
        Returns:
            CalendarioAcademicoResponse con eventos
        """
        try:
            logger.info(f"Consultando calendario académico: tipo={request.tipo_evento}, desde={request.fecha_desde}, hasta={request.fecha_hasta}")
            
            # Query base
            query = self.client.table('calendario_vectorizado') \
                .select('id, tipo_evento, contenido_original, metadata')
            
            # Filtrar por tipo de evento si se especificó
            if request.tipo_evento:
                query = query.ilike('tipo_evento', f'%{request.tipo_evento}%')
            
            response = query.execute()
            
            if not response.data:
                logger.info("No se encontraron eventos en el calendario")
                return CalendarioAcademicoResponse(eventos=[], total=0)
            
            # Procesar y filtrar eventos
            eventos = []
            for item in response.data:
                try:
                    metadata = item.get('metadata', {})
                    
                    # Extraer fecha del metadata
                    fecha_evento_str = metadata.get('fecha')
                    fecha_evento = None
                    
                    if fecha_evento_str:
                        try:
                            fecha_evento = datetime.strptime(fecha_evento_str, '%Y-%m-%d').date()
                        except ValueError:
                            logger.warning(f"Fecha inválida en metadata: {fecha_evento_str}")
                    
                    # Filtrar por rango de fechas si se especificó
                    if request.fecha_desde or request.fecha_hasta:
                        if not fecha_evento:
                            continue
                        
                        if request.fecha_desde and fecha_evento < request.fecha_desde:
                            continue
                        
                        if request.fecha_hasta and fecha_evento > request.fecha_hasta:
                            continue
                    
                    # Crear modelo Pydantic
                    evento = EventoCalendario(
                        tipo=item.get('tipo_evento', 'N/A'),
                        titulo=metadata.get('titulo', item.get('contenido_original', 'Evento')[:50]),
                        descripcion=item.get('contenido_original', ''),
                        fecha=fecha_evento,
                        metadata=metadata
                    )
                    
                    eventos.append(evento)
                
                except Exception as e:
                    logger.error(f"Error procesando evento {item.get('id')}: {e}")
                    continue
            
            # Ordenar por fecha (eventos sin fecha al final)
            eventos.sort(key=lambda x: x.fecha if x.fecha else date(9999, 12, 31))
            
            logger.info(f"Se encontraron {len(eventos)} eventos del calendario")
            
            return CalendarioAcademicoResponse(eventos=eventos, total=len(eventos))
            
        except Exception as e:
            logger.error(f"Error obteniendo calendario académico: {e}", exc_info=True)
            raise SupabaseError(str(e), operation="get_calendario_academico")

    # =====================================================
    # HELPER: GET PRÓXIMOS EXÁMENES
    # =====================================================

    async def get_proximos_examenes(self, request: ProximosExamenesRequest) -> ExamenesResponse:
        """
        Obtiene los próximos exámenes del alumno en los próximos N días
        
        Args:
            request: ProximosExamenesRequest validado
            
        Returns:
            ExamenesResponse con exámenes próximos
        """
        try:
            fecha_hoy = date.today()
            fecha_limite = fecha_hoy + timedelta(days=request.dias)
            
            # Crear request para get_examenes_alumno
            examenes_request = ExamenesRequest(
                alumno_id=request.alumno_id,
                fecha_desde=fecha_hoy,
                fecha_hasta=fecha_limite
            )
            
            return await self.get_examenes_alumno(examenes_request)
            
        except Exception as e:
            logger.error(f"Error obteniendo próximos exámenes: {e}")
            raise SupabaseError(str(e), operation="get_proximos_examenes")


# Instancia global del repositorio
calendar_repository = CalendarRepository()
