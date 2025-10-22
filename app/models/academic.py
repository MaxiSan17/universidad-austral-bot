"""
Modelos Pydantic para Academic Tools (Herramientas Académicas)
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date
from app.models.common import (
    BaseModelConfig,
    UUIDMixin,
    MateriaBase,
    ComisionBase,
    Modalidad,
    DiaSemana,
    EstadoInscripcion,
    validate_horario
)


# =====================================================
# REQUEST MODELS
# =====================================================

class HorariosRequest(BaseModelConfig):
    """Request para consultar horarios del alumno"""
    alumno_id: str = Field(..., description="UUID del alumno")
    materia_nombre: Optional[str] = Field(None, description="Filtrar por materia específica")
    dia_semana: Optional[int] = Field(None, ge=1, le=7, description="Día de la semana (1=Lunes, 7=Domingo)")
    fecha_desde: Optional[date] = Field(None, description="Fecha de inicio del rango (para filtros temporales)")
    fecha_hasta: Optional[date] = Field(None, description="Fecha de fin del rango (para filtros temporales)")

    @validator('alumno_id')
    def validate_id(cls, v):
        return UUIDMixin.validate_uuid(v)

    @validator('materia_nombre')
    def normalize_materia(cls, v):
        """Normaliza el nombre de la materia"""
        if v:
            return v.strip()
        return v


class InscripcionesRequest(BaseModelConfig):
    """Request para consultar inscripciones del alumno"""
    alumno_id: str = Field(..., description="UUID del alumno")
    estado: Optional[EstadoInscripcion] = Field(None, description="Filtrar por estado")
    
    @validator('alumno_id')
    def validate_id(cls, v):
        return UUIDMixin.validate_uuid(v)


class ProfesorRequest(BaseModelConfig):
    """Request para buscar información de profesor"""
    profesor_nombre: Optional[str] = Field(None, description="Nombre del profesor")
    materia_nombre: Optional[str] = Field(None, description="Materia que dicta")
    
    @validator('profesor_nombre', 'materia_nombre')
    def at_least_one(cls, v, values):
        """Al menos uno de los dos debe estar presente"""
        if not v and not values.get('profesor_nombre') and not values.get('materia_nombre'):
            raise ValueError('Debe especificar profesor_nombre o materia_nombre')
        return v


class AulaRequest(BaseModelConfig):
    """Request para consultar información de aula"""
    aula: Optional[str] = Field(None, description="Código del aula")
    materia_nombre: Optional[str] = Field(None, description="Materia que se dicta en el aula")


class CreditosVURequest(BaseModelConfig):
    """Request para consultar créditos de Vida Universitaria"""
    alumno_id: str = Field(..., description="UUID del alumno")
    
    @validator('alumno_id')
    def validate_id(cls, v):
        return UUIDMixin.validate_uuid(v)


# =====================================================
# RESPONSE MODELS
# =====================================================

class HorarioInfo(BaseModelConfig):
    """Información de un horario específico"""
    dia_semana: int = Field(..., ge=1, le=7, description="1=Lunes, 7=Domingo")
    materia_nombre: str = Field(..., description="Nombre de la materia")
    materia_codigo: str = Field(..., description="Código de la materia")
    comision: str = Field(..., description="Código de comisión")
    hora_inicio: str = Field(..., description="Hora de inicio (HH:MM)")
    hora_fin: str = Field(..., description="Hora de fin (HH:MM)")
    aula: str = Field(..., description="Aula donde se dicta")
    edificio: str = Field(default="Campus Principal", description="Edificio")
    modalidad: Modalidad = Field(default=Modalidad.PRESENCIAL, description="Modalidad de cursada")
    profesor_nombre: Optional[str] = Field(None, description="Nombre del profesor")
    
    @validator('hora_inicio', 'hora_fin')
    def validate_horario_format(cls, v):
        """Valida formato de horario"""
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError(f'Horario "{v}" debe tener formato HH:MM')
        return v
    
    @property
    def dia_nombre(self) -> str:
        """Retorna el nombre del día en español"""
        from app.core import DIAS_SEMANA_ES
        return DIAS_SEMANA_ES.get(self.dia_semana, "Desconocido")
    
    @property
    def duracion_minutos(self) -> int:
        """Calcula la duración en minutos"""
        h_i, m_i = map(int, self.hora_inicio.split(':'))
        h_f, m_f = map(int, self.hora_fin.split(':'))
        return (h_f * 60 + m_f) - (h_i * 60 + m_i)


class HorariosResponse(BaseModelConfig):
    """Response con horarios del alumno"""
    horarios: List[HorarioInfo] = Field(default_factory=list)
    total: int = Field(..., ge=0, description="Total de horarios")
    
    @validator('total')
    def total_matches_list(cls, v, values):
        """Valida que total coincida con la cantidad de horarios"""
        if 'horarios' in values and v != len(values['horarios']):
            raise ValueError('total no coincide con cantidad de horarios')
        return v
    
    @property
    def tiene_horarios(self) -> bool:
        """Verifica si hay horarios"""
        return self.total > 0
    
    @property
    def dias_con_clases(self) -> List[int]:
        """Retorna lista de días en los que hay clases"""
        return sorted(list(set(h.dia_semana for h in self.horarios)))


class InscripcionInfo(BaseModelConfig):
    """Información de una inscripción"""
    materia_id: str
    materia_nombre: str = Field(..., description="Nombre de la materia")
    materia_codigo: str = Field(..., description="Código de la materia")
    comision_id: str
    comision_codigo: str = Field(..., description="Código de comisión")
    estado: EstadoInscripcion = Field(default=EstadoInscripcion.CURSANDO)
    fecha_inscripcion: Optional[date] = None
    
    @validator('materia_id', 'comision_id')
    def validate_ids(cls, v):
        return UUIDMixin.validate_uuid(v)
    
    @property
    def esta_cursando(self) -> bool:
        """Verifica si está cursando actualmente"""
        return self.estado == EstadoInscripcion.CURSANDO


class InscripcionesResponse(BaseModelConfig):
    """Response con inscripciones del alumno"""
    materias: List[InscripcionInfo] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    
    @validator('total')
    def total_matches_list(cls, v, values):
        if 'materias' in values and v != len(values['materias']):
            raise ValueError('total no coincide con cantidad de materias')
        return v
    
    @property
    def materias_cursando(self) -> List[InscripcionInfo]:
        """Retorna solo las materias que está cursando"""
        return [m for m in self.materias if m.esta_cursando]


class ProfesorInfo(BaseModelConfig):
    """Información de un profesor"""
    id: Optional[str] = None
    nombre: str = Field(..., description="Nombre completo del profesor")
    email: Optional[str] = None
    departamento: Optional[str] = None
    materias: List[str] = Field(default_factory=list, description="Materias que dicta")
    
    @validator('id')
    def validate_id(cls, v):
        if v:
            return UUIDMixin.validate_uuid(v)
        return v


class ProfesorResponse(BaseModelConfig):
    """Response con información de profesor"""
    profesor: Optional[ProfesorInfo] = None
    encontrado: bool = Field(default=False)
    
    @property
    def tiene_profesor(self) -> bool:
        return self.profesor is not None


class AulaInfo(BaseModelConfig):
    """Información de un aula"""
    codigo_aula: str = Field(..., description="Código del aula")
    edificio: str = Field(default="Campus Principal")
    capacidad: Optional[int] = Field(None, ge=1)
    tipo: Optional[str] = Field(None, description="Ej: Laboratorio, Teórico, etc.")
    materias: List[str] = Field(default_factory=list, description="Materias que se dictan")


class AulaResponse(BaseModelConfig):
    """Response con información de aula"""
    aula: Optional[AulaInfo] = None
    encontrada: bool = Field(default=False)


class CreditosVUInfo(BaseModelConfig):
    """Información de créditos de Vida Universitaria"""
    creditos_actuales: int = Field(..., ge=0, description="Créditos VU acumulados")
    creditos_necesarios: int = Field(..., ge=0, description="Créditos VU requeridos")
    creditos_faltantes: int = Field(..., ge=0, description="Créditos VU que faltan")
    porcentaje_completado: int = Field(..., ge=0, le=100, description="Porcentaje de avance")
    cumple_requisito: bool = Field(..., description="Si cumple con el mínimo requerido")
    
    @validator('creditos_faltantes')
    def validate_faltantes(cls, v, values):
        """Valida que los créditos faltantes sean coherentes"""
        if 'creditos_actuales' in values and 'creditos_necesarios' in values:
            expected = max(0, values['creditos_necesarios'] - values['creditos_actuales'])
            if v != expected:
                raise ValueError('creditos_faltantes no coincide con el cálculo')
        return v
    
    @validator('cumple_requisito')
    def validate_cumple(cls, v, values):
        """Valida que cumple_requisito sea coherente"""
        if 'creditos_actuales' in values and 'creditos_necesarios' in values:
            expected = values['creditos_actuales'] >= values['creditos_necesarios']
            if v != expected:
                raise ValueError('cumple_requisito no coincide con los créditos')
        return v
    
    @property
    def nivel_progreso(self) -> str:
        """Retorna nivel de progreso en texto"""
        if self.cumple_requisito:
            return "Completado"
        elif self.porcentaje_completado >= 75:
            return "Casi completo"
        elif self.porcentaje_completado >= 50:
            return "En progreso"
        else:
            return "Inicial"


class CreditosVUResponse(BaseModelConfig):
    """Response con créditos de Vida Universitaria"""
    creditos: CreditosVUInfo
    
    @property
    def necesita_creditos(self) -> bool:
        """Verifica si necesita más créditos"""
        return not self.creditos.cumple_requisito
