"""
Repositorio de datos académicos - Consultas a Supabase sin n8n
"""
from typing import Optional, List, Dict, Any
from app.database.supabase_client import SupabaseClient
from app.utils.logger import get_logger
import uuid

logger = get_logger(__name__)


class AcademicRepository:
    """Repositorio para consultas académicas a Supabase"""

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

    # =====================================================
    # TOOL 1: GET HORARIOS ALUMNO
    # =====================================================

    async def get_horarios_alumno(
        self, 
        alumno_id: str,
        materia_nombre: Optional[str] = None,
        dia_semana: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtiene los horarios del alumno usando la función SQL de Supabase
        
        Args:
            alumno_id: UUID del alumno
            materia_nombre: (Opcional) Filtrar por materia específica
            dia_semana: (Opcional) Filtrar por día (1=Lunes, 7=Domingo)
            
        Returns:
            Dict con 'horarios' (lista) y 'total' (int)
            
        Raises:
            ValueError: Si alumno_id es inválido
            Exception: Si hay error en la consulta
        """
        try:
            # Validación
            self._validate_alumno_id(alumno_id)
            
            logger.info(f"Consultando horarios para alumno {alumno_id}")
            
            # Llamar a la función SQL de Supabase
            response = self.client.rpc(
                'get_horarios_alumno',
                {'p_alumno_id': alumno_id}
            ).execute()
            
            if not response.data:
                logger.info(f"No se encontraron horarios para alumno {alumno_id}")
                return {
                    "horarios": [],
                    "total": 0
                }
            
            horarios = response.data
            
            # Filtro por materia (si se especificó)
            if materia_nombre:
                horarios = [
                    h for h in horarios 
                    if materia_nombre.lower() in h.get('materia_nombre', '').lower()
                ]
            
            # Filtro por día (si se especificó)
            if dia_semana:
                horarios = [
                    h for h in horarios 
                    if h.get('dia_semana') == dia_semana
                ]
            
            logger.info(f"Se encontraron {len(horarios)} horarios")
            
            return {
                "horarios": horarios,
                "total": len(horarios)
            }
            
        except ValueError as e:
            logger.error(f"Error de validación en get_horarios_alumno: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo horarios: {e}", exc_info=True)
            return {
                "horarios": [],
                "total": 0,
                "error": str(e)
            }

    # =====================================================
    # TOOL 2: GET INSCRIPCIONES
    # =====================================================

    async def get_inscripciones(self, alumno_id: str) -> Dict[str, Any]:
        """
        Obtiene las materias en las que está inscripto el alumno
        
        Args:
            alumno_id: UUID del alumno
            
        Returns:
            Dict con 'materias' (lista) y 'total' (int)
        """
        try:
            # Validación
            self._validate_alumno_id(alumno_id)
            
            logger.info(f"Consultando inscripciones para alumno {alumno_id}")
            
            # Obtener inscripciones
            inscripciones = self.client.table('inscripciones') \
                .select('id, estado, comision_id, asistencia_porcentaje, nota_cursada') \
                .eq('alumno_id', alumno_id) \
                .execute()
            
            if not inscripciones.data:
                logger.info(f"No se encontraron inscripciones para alumno {alumno_id}")
                return {"materias": [], "total": 0}
            
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
                        .select('nombre, codigo, carrera') \
                        .eq('id', comision['materia_id']) \
                        .execute()
                    
                    if not materia_response.data or len(materia_response.data) == 0:
                        logger.warning(f"No se encontró materia {comision['materia_id']}")
                        continue
                    
                    materia = materia_response.data[0]
                    
                    materias.append({
                        "nombre": materia.get('nombre', 'N/A'),
                        "codigo": materia.get('codigo', 'N/A'),
                        "comision": comision.get('codigo_comision', 'N/A'),
                        "carrera": materia.get('carrera', 'N/A'),
                        "cuatrimestre": comision.get('cuatrimestre', 0),
                        "estado": insc.get('estado', 'cursando'),
                        "asistencia": insc.get('asistencia_porcentaje', 0),
                        "nota_cursada": insc.get('nota_cursada')
                    })
                    
                except Exception as e:
                    logger.error(f"Error procesando inscripción {insc.get('id')}: {e}")
                    continue
            
            logger.info(f"Se encontraron {len(materias)} materias válidas")
            return {"materias": materias, "total": len(materias)}
            
        except ValueError as e:
            logger.error(f"Error de validación en get_inscripciones: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo inscripciones: {e}", exc_info=True)
            return {
                "materias": [],
                "total": 0,
                "error": str(e)
            }

    # =====================================================
    # TOOL 3: GET PROFESOR INFO
    # =====================================================

    async def get_profesor_info(
        self, 
        profesor_nombre: Optional[str] = None,
        materia_nombre: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca información de profesores
        
        Args:
            profesor_nombre: (Opcional) Nombre del profesor
            materia_nombre: (Opcional) Materia que dicta
            
        Returns:
            Dict con 'profesores' (lista)
        """
        try:
            logger.info(f"Buscando profesor: nombre={profesor_nombre}, materia={materia_nombre}")
            
            # Estrategia 1: Si se busca por materia
            if materia_nombre:
                response = self.client.table('comisiones') \
                    .select('''
                        id,
                        codigo_comision,
                        materias!inner (
                            nombre
                        ),
                        usuarios!inner (
                            id,
                            nombre,
                            apellido,
                            email,
                            telefono
                        )
                    ''') \
                    .ilike('materias.nombre', f'%{materia_nombre}%') \
                    .eq('usuarios.tipo', 'profesor') \
                    .execute()
                
                if response.data:
                    profesores = []
                    for comision in response.data:
                        usuario = comision.get('usuarios', {})
                        materia = comision.get('materias', {})
                        
                        profesor = {
                            "nombre": usuario.get('nombre', 'N/A'),
                            "apellido": usuario.get('apellido', ''),
                            "nombre_completo": f"{usuario.get('nombre', '')} {usuario.get('apellido', '')}".strip(),
                            "email": usuario.get('email', 'N/A'),
                            "telefono": usuario.get('telefono'),
                            "materia": materia.get('nombre', 'N/A'),
                            "comision": comision.get('codigo_comision', 'N/A')
                        }
                        
                        # Evitar duplicados
                        if not any(p['email'] == profesor['email'] for p in profesores):
                            profesores.append(profesor)
                    
                    return {
                        "profesores": profesores,
                        "total": len(profesores)
                    }
            
            # Estrategia 2: Si se busca por nombre de profesor
            if profesor_nombre:
                response = self.client.table('usuarios') \
                    .select('id, nombre, apellido, email, telefono') \
                    .eq('tipo', 'profesor') \
                    .or_(f'nombre.ilike.%{profesor_nombre}%,apellido.ilike.%{profesor_nombre}%') \
                    .execute()
                
                if response.data:
                    profesores = [
                        {
                            "nombre": p.get('nombre', 'N/A'),
                            "apellido": p.get('apellido', ''),
                            "nombre_completo": f"{p.get('nombre', '')} {p.get('apellido', '')}".strip(),
                            "email": p.get('email', 'N/A'),
                            "telefono": p.get('telefono')
                        }
                        for p in response.data
                    ]
                    
                    return {
                        "profesores": profesores,
                        "total": len(profesores)
                    }
            
            # Si no se especificó ningún filtro
            logger.info("No se especificó nombre ni materia para buscar profesor")
            return {
                "profesores": [],
                "total": 0,
                "message": "Especificá el nombre del profesor o la materia"
            }
            
        except Exception as e:
            logger.error(f"Error buscando profesor: {e}", exc_info=True)
            return {
                "profesores": [],
                "total": 0,
                "error": str(e)
            }

    # =====================================================
    # TOOL 4: GET AULA INFO
    # =====================================================

    async def get_aula_info(
        self,
        aula: Optional[str] = None,
        materia_nombre: Optional[str] = None,
        alumno_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta información sobre aulas
        
        Args:
            aula: (Opcional) Código del aula (ej: 'R3', 'A4')
            materia_nombre: (Opcional) Materia para buscar su aula
            alumno_id: (Opcional) Alumno para buscar sus aulas
            
        Returns:
            Dict con 'aulas' (lista)
        """
        try:
            logger.info(f"Buscando aula: aula={aula}, materia={materia_nombre}, alumno={alumno_id}")
            
            # Estrategia 1: Buscar aulas de un alumno específico
            if alumno_id:
                if not self._is_valid_uuid(alumno_id):
                    return {
                        "aulas": [],
                        "total": 0,
                        "error": "alumno_id inválido"
                    }
                
                # Obtener horarios del alumno (que incluyen info de aulas)
                horarios_result = await self.get_horarios_alumno(alumno_id)
                horarios = horarios_result.get('horarios', [])
                
                # Extraer info única de aulas
                aulas_dict = {}
                for h in horarios:
                    aula_codigo = h.get('aula')
                    if aula_codigo and aula_codigo not in aulas_dict:
                        aulas_dict[aula_codigo] = {
                            "aula": aula_codigo,
                            "edificio": h.get('edificio', 'N/A'),
                            "materias": []
                        }
                    if aula_codigo:
                        materia = h.get('materia_nombre', 'N/A')
                        if materia not in aulas_dict[aula_codigo]['materias']:
                            aulas_dict[aula_codigo]['materias'].append(materia)
                
                return {
                    "aulas": list(aulas_dict.values()),
                    "total": len(aulas_dict)
                }
            
            # Estrategia 2: Buscar por materia
            if materia_nombre:
                response = self.client.table('horarios_comision') \
                    .select('''
                        aula,
                        edificio,
                        comisiones!inner (
                            materias!inner (
                                nombre
                            )
                        )
                    ''') \
                    .ilike('comisiones.materias.nombre', f'%{materia_nombre}%') \
                    .execute()
                
                if response.data:
                    aulas = []
                    aulas_vistas = set()
                    
                    for horario in response.data:
                        aula_codigo = horario.get('aula')
                        if aula_codigo and aula_codigo not in aulas_vistas:
                            aulas_vistas.add(aula_codigo)
                            aulas.append({
                                "aula": aula_codigo,
                                "edificio": horario.get('edificio', 'N/A'),
                                "materia": horario['comisiones']['materias'].get('nombre', 'N/A')
                            })
                    
                    return {
                        "aulas": aulas,
                        "total": len(aulas)
                    }
            
            # Estrategia 3: Buscar por código de aula
            if aula:
                response = self.client.table('horarios_comision') \
                    .select('aula, edificio, dia_semana, hora_inicio, hora_fin') \
                    .ilike('aula', f'%{aula}%') \
                    .limit(10) \
                    .execute()
                
                if response.data:
                    return {
                        "aulas": response.data,
                        "total": len(response.data)
                    }
            
            # Sin filtros
            return {
                "aulas": [],
                "total": 0,
                "message": "Especificá el aula, materia o alumno para buscar"
            }
            
        except Exception as e:
            logger.error(f"Error buscando aula: {e}", exc_info=True)
            return {
                "aulas": [],
                "total": 0,
                "error": str(e)
            }


# Instancia global del repositorio
academic_repository = AcademicRepository()
