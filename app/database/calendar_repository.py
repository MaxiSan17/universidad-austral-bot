"""
Repositorio de calendario y exámenes - Consultas a Supabase
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.database.supabase_client import SupabaseClient
from app.utils.logger import get_logger
import uuid

logger = get_logger(__name__)


class CalendarRepository:
    """Repositorio para consultas de calendario y exámenes"""

    def __init__(self):
        self.client = SupabaseClient.get_client()

    # =====================================================
    # VALIDACIONES INTERNAS
    # =====================================================

    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Valida si un string es un UUID válido"""
        try:
            uuid.UUID(str(uuid_string))
            return True
        except (ValueError, AttributeError, TypeError):
            return False

    def _validate_alumno_id(self, alumno_id: str) -> None:
        """Valida que alumno_id sea un UUID válido"""
        if not alumno_id:
            raise ValueError("alumno_id no puede estar vacío")
        if not self._is_valid_uuid(alumno_id):
            raise ValueError(f"alumno_id '{alumno_id}' no es un UUID válido")

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parsea un string de fecha a objeto date"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.warning(f"Fecha inválida: {date_str}")
            return None

    # =====================================================
    # TOOL 1: GET EXÁMENES ALUMNO
    # =====================================================

    async def get_examenes_alumno(
        self,
        alumno_id: str,
        materia_nombre: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene los exámenes del alumno
        
        Args:
            alumno_id: UUID del alumno
            materia_nombre: (Opcional) Filtrar por materia específica
            fecha_desde: (Opcional) Fecha inicio (YYYY-MM-DD)
            fecha_hasta: (Opcional) Fecha fin (YYYY-MM-DD)
            
        Returns:
            Dict con 'examenes' (lista) y 'total' (int)
        """
        try:
            # Validación
            self._validate_alumno_id(alumno_id)
            
            logger.info(f"Consultando exámenes para alumno {alumno_id}")
            
            # Obtener inscripciones del alumno
            inscripciones = self.client.table('inscripciones') \
                .select('comision_id') \
                .eq('alumno_id', alumno_id) \
                .execute()
            
            if not inscripciones.data:
                logger.info(f"Alumno {alumno_id} no tiene inscripciones")
                return {"examenes": [], "total": 0}
            
            comision_ids = [insc['comision_id'] for insc in inscripciones.data]
            
            # Obtener exámenes de esas comisiones
            query = self.client.table('examenes') \
                .select('id, tipo, numero, fecha, hora_inicio, hora_fin, aula, edificio, modalidad, observaciones, comision_id') \
                .in_('comision_id', comision_ids) \
                .order('fecha', desc=False)
            
            # Filtrar por fechas si se especificaron
            if fecha_desde:
                query = query.gte('fecha', fecha_desde)
            if fecha_hasta:
                query = query.lte('fecha', fecha_hasta)
            
            examenes_response = query.execute()
            
            if not examenes_response.data:
                logger.info(f"No se encontraron exámenes para alumno {alumno_id}")
                return {"examenes": [], "total": 0}
            
            # Enriquecer con datos de materia
            examenes = []
            for examen in examenes_response.data:
                try:
                    # Obtener comisión y materia
                    comision = self.client.table('comisiones') \
                        .select('codigo_comision, materias!inner(nombre, codigo)') \
                        .eq('id', examen['comision_id']) \
                        .single() \
                        .execute()
                    
                    if not comision.data:
                        continue
                    
                    materia = comision.data.get('materias', {})
                    materia_nombre_db = materia.get('nombre', 'N/A')
                    
                    # Filtrar por materia si se especificó
                    if materia_nombre and materia_nombre.lower() not in materia_nombre_db.lower():
                        continue
                    
                    # Formatear nombre del examen
                    nombre_examen = self._format_exam_name(
                        examen['tipo'],
                        examen.get('numero')
                    )
                    
                    examenes.append({
                        "materia": materia_nombre_db,
                        "materia_codigo": materia.get('codigo', 'N/A'),
                        "comision": comision.data.get('codigo_comision', 'N/A'),
                        "tipo": examen['tipo'],
                        "numero": examen.get('numero'),
                        "nombre": nombre_examen,
                        "fecha": examen['fecha'],
                        "hora_inicio": str(examen['hora_inicio']),
                        "hora_fin": str(examen['hora_fin']),
                        "aula": examen.get('aula', 'A confirmar'),
                        "edificio": examen.get('edificio', 'Campus Principal'),
                        "modalidad": examen.get('modalidad', 'presencial'),
                        "observaciones": examen.get('observaciones')
                    })
                
                except Exception as e:
                    logger.error(f"Error procesando examen {examen.get('id')}: {e}")
                    continue
            
            logger.info(f"Se encontraron {len(examenes)} exámenes")
            
            return {
                "examenes": examenes,
                "total": len(examenes)
            }
            
        except ValueError as e:
            logger.error(f"Error de validación en get_examenes_alumno: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo exámenes: {e}", exc_info=True)
            return {
                "examenes": [],
                "total": 0,
                "error": str(e)
            }

    def _format_exam_name(self, tipo: str, numero: Optional[int]) -> str:
        """Formatea el nombre del examen"""
        tipo_map = {
            'parcial': 'Parcial',
            'recuperatorio': 'Recuperatorio',
            'final': 'Final',
            'trabajo_practico': 'Trabajo Práctico'
        }
        
        nombre_base = tipo_map.get(tipo, tipo.capitalize())
        
        if numero:
            return f"{nombre_base} {numero}"
        return nombre_base

    # =====================================================
    # TOOL 2: GET CALENDARIO ACADÉMICO
    # =====================================================

    async def get_calendario_academico(
        self,
        tipo_evento: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene eventos del calendario académico usando la tabla vectorizada
        
        Args:
            tipo_evento: (Opcional) Tipo de evento a buscar
            fecha_desde: (Opcional) Fecha inicio (YYYY-MM-DD)
            fecha_hasta: (Opcional) Fecha fin (YYYY-MM-DD)
            
        Returns:
            Dict con 'eventos' (lista) y 'total' (int)
        """
        try:
            logger.info(f"Consultando calendario académico: tipo={tipo_evento}, desde={fecha_desde}, hasta={fecha_hasta}")
            
            # Query base
            query = self.client.table('calendario_vectorizado') \
                .select('id, tipo_evento, contenido_original, metadata')
            
            # Filtrar por tipo de evento si se especificó
            if tipo_evento:
                query = query.ilike('tipo_evento', f'%{tipo_evento}%')
            
            response = query.execute()
            
            if not response.data:
                logger.info("No se encontraron eventos en el calendario")
                return {"eventos": [], "total": 0}
            
            # Procesar y filtrar eventos
            eventos = []
            for item in response.data:
                try:
                    metadata = item.get('metadata', {})
                    
                    # Extraer fecha del metadata
                    fecha_evento = metadata.get('fecha')
                    
                    # Filtrar por rango de fechas si se especificó
                    if fecha_desde or fecha_hasta:
                        if not fecha_evento:
                            continue
                        
                        fecha_obj = self._parse_date(fecha_evento)
                        if not fecha_obj:
                            continue
                        
                        if fecha_desde:
                            fecha_desde_obj = self._parse_date(fecha_desde)
                            if fecha_desde_obj and fecha_obj < fecha_desde_obj:
                                continue
                        
                        if fecha_hasta:
                            fecha_hasta_obj = self._parse_date(fecha_hasta)
                            if fecha_hasta_obj and fecha_obj > fecha_hasta_obj:
                                continue
                    
                    eventos.append({
                        "tipo": item.get('tipo_evento', 'N/A'),
                        "titulo": metadata.get('titulo', item.get('contenido_original', 'Evento')[:50]),
                        "descripcion": item.get('contenido_original'),
                        "fecha": fecha_evento,
                        "metadata": metadata
                    })
                
                except Exception as e:
                    logger.error(f"Error procesando evento {item.get('id')}: {e}")
                    continue
            
            # Ordenar por fecha
            eventos.sort(key=lambda x: x.get('fecha') or '9999-12-31')
            
            logger.info(f"Se encontraron {len(eventos)} eventos del calendario")
            
            return {
                "eventos": eventos,
                "total": len(eventos)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo calendario académico: {e}", exc_info=True)
            return {
                "eventos": [],
                "total": 0,
                "error": str(e)
            }

    # =====================================================
    # HELPER: GET PRÓXIMOS EXÁMENES
    # =====================================================

    async def get_proximos_examenes(
        self,
        alumno_id: str,
        dias: int = 7
    ) -> Dict[str, Any]:
        """
        Obtiene los próximos exámenes del alumno en los próximos N días
        
        Args:
            alumno_id: UUID del alumno
            dias: Cantidad de días a futuro (default: 7)
            
        Returns:
            Dict con 'examenes' próximos
        """
        try:
            fecha_hoy = datetime.now().date().isoformat()
            fecha_limite = (datetime.now().date()).isoformat()
            
            from datetime import timedelta
            fecha_limite = (datetime.now().date() + timedelta(days=dias)).isoformat()
            
            return await self.get_examenes_alumno(
                alumno_id=alumno_id,
                fecha_desde=fecha_hoy,
                fecha_hasta=fecha_limite
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo próximos exámenes: {e}")
            return {"examenes": [], "total": 0, "error": str(e)}


# Instancia global del repositorio
calendar_repository = CalendarRepository()
