"""
Modelos Pydantic para Calendar Tools (Herramientas de Calendario)
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import date, datetime
from app.models.common import (
    BaseModelConfig,
    UUIDMixin,
    Modalidad,
    validate_fecha_range
)
from enum import Enum


# =====================================================
# ENUMS
# =====================================================

class TipoExamen(str, Enum):
    """Tipos de examen"""
    PARCIAL = "parcial"
    RECUPERATORIO = "recuperatorio"
    FINAL = "final"
    TRABAJO_PRACTICO = "trabajo_practico"


class TipoEvento(str, Enum):
    """Tipos de evento del calendario académico"""
    INICIO_CLASES = "inicio_clases"
    FIN_CLASES = "fin_clases"
    FERIADO = "feriado"
    INSCRIPCIONES = "inscripciones"
    EXAMENES = "examenes"
    EVENTO_INSTITUCIONAL = "evento_institucional"


# =====================================================
# REQUEST MODELS
# =====================================================

class ExamenesRequest(BaseModelConfig):
    """Request para consultar exámenes del alumno"""
    alumno_id: str = Field(..., description="UUID del alumno")
    materia_nombre: Optional[str] = Field(None, description="Filtrar por materia específica")
    fecha_desde: Optional[date] = Field(None, description="Fecha inicio (YYYY-MM-DD)")
    fecha_hasta: Optional[date] = Field(None, description="Fecha fin (YYYY-MM-DD)")
    tipo_examen: Optional[TipoExamen] = Field(None, description="Filtrar por tipo de examen")
    
    @validator('alumno_id')
    def validate_id(cls, v):
        return UUIDMixin.validate_uuid(v)
    
    @validator('fecha_hasta')
    def validate_fecha_range(cls, v, values):
        """Valida que el rango de fechas sea coherente"""
        fecha_desde = values.get('fecha_desde')
        if fecha_desde and v:
            if v < fecha_desde:
                raise ValueError('fecha_hasta debe ser posterior a fecha_desde')
        return v
    
    @validator('materia_nombre')
    def normalize_materia(cls, v):
        if v:
            return v.strip()
        return v


class CalendarioAcademicoRequest(BaseModelConfig):
    """Request para consultar calendario académico"""
    tipo_evento: Optional[str] = Field(None, description="Tipo de evento a buscar")
    fecha_desde: Optional[date] = Field(None, description="Fecha inicio")
    fecha_hasta: Optional[date] = Field(None, description="Fecha fin")
    
    @validator('fecha_hasta')
    def validate_fecha_range(cls, v, values):
        fecha_desde = values.get('fecha_desde')
        if fecha_desde and v:
            if v < fecha_desde:
                raise ValueError('fecha_hasta debe ser posterior a fecha_desde')
        return v


class ProximosExamenesRequest(BaseModelConfig):
    """Request para consultar próximos exámenes"""
    alumno_id: str = Field(..., description="UUID del alumno")
    dias: int = Field(default=7, ge=1, le=90, description="Cantidad de días a futuro")
    
    @validator('alumno_id')
    def validate_id(cls, v):
        return UUIDMixin.validate_uuid(v)


# =====================================================
# RESPONSE MODELS
# =====================================================

class ExamenInfo(BaseModelConfig):
    """Información de un examen"""
    materia: str = Field(..., description="Nombre de la materia")
    materia_codigo: str = Field(..., description="Código de la materia")
    comision: str = Field(..., description="Código de comisión")
    tipo: TipoExamen = Field(..., description="Tipo de examen")
    numero: Optional[int] = Field(None, ge=1, description="Número de parcial/recuperatorio")
    nombre: str = Field(..., description="Nombre formateado del examen")
    fecha: date = Field(..., description="Fecha del examen")
    hora_inicio: str = Field(..., description="Hora de inicio (HH:MM)")
    hora_fin: str = Field(..., description="Hora de fin (HH:MM)")
    aula: str = Field(..., description="Aula del examen")
    edificio: str = Field(default="Campus Principal", description="Edificio")
    modalidad: Modalidad = Field(default=Modalidad.PRESENCIAL, description="Modalidad del examen")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")
    
    @validator('hora_inicio', 'hora_fin')
    def validate_horario_format(cls, v):
        """Valida formato de horario"""
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError(f'Horario "{v}" debe tener formato HH:MM')
        return v
    
    @property
    def es_parcial(self) -> bool:
        """Verifica si es un parcial"""
        return self.tipo == TipoExamen.PARCIAL
    
    @property
    def es_final(self) -> bool:
        """Verifica si es un final"""
        return self.tipo == TipoExamen.FINAL
    
    @property
    def es_recuperatorio(self) -> bool:
        """Verifica si es un recuperatorio"""
        return self.tipo == TipoExamen.RECUPERATORIO
    
    @property
    def dias_hasta_examen(self) -> int:
        """Calcula días hasta el examen"""
        hoy = date.today()
        return (self.fecha - hoy).days
    
    @property
    def es_proximo(self) -> bool:
        """Verifica si es en los próximos 7 días"""
        return 0 <= self.dias_hasta_examen <= 7
    
    @property
    def emoji(self) -> str:
        """Retorna emoji según tipo de examen"""
        from app.core import EMOJIS
        emoji_map = {
            TipoExamen.PARCIAL: EMOJIS["parcial"],
            TipoExamen.FINAL: EMOJIS["final"],
            TipoExamen.RECUPERATORIO: EMOJIS["recuperatorio"],
            TipoExamen.TRABAJO_PRACTICO: EMOJIS["trabajo_practico"]
        }
        return emoji_map.get(self.tipo, EMOJIS["examen"])


class ExamenesResponse(BaseModelConfig):
    """Response con exámenes del alumno"""
    examenes: List[ExamenInfo] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    
    @validator('total')
    def total_matches_list(cls, v, values):
        if 'examenes' in values and v != len(values['examenes']):
            raise ValueError('total no coincide con cantidad de exámenes')
        return v
    
    @property
    def tiene_examenes(self) -> bool:
        """Verifica si hay exámenes"""
        return self.total > 0
    
    @property
    def examenes_proximos(self) -> List[ExamenInfo]:
        """Retorna solo exámenes próximos (7 días)"""
        return [e for e in self.examenes if e.es_proximo]
    
    @property
    def examenes_por_tipo(self) -> dict:
        """Agrupa exámenes por tipo"""
        from collections import defaultdict
        grouped = defaultdict(list)
        for examen in self.examenes:
            grouped[examen.tipo].append(examen)
        return dict(grouped)


class EventoCalendario(BaseModelConfig):
    """Evento del calendario académico"""
    tipo: str = Field(..., description="Tipo de evento")
    titulo: str = Field(..., description="Título del evento")
    descripcion: str = Field(..., description="Descripción del evento")
    fecha: Optional[date] = Field(None, description="Fecha del evento")
    metadata: dict = Field(default_factory=dict, description="Metadata adicional")
    
    @property
    def dias_hasta_evento(self) -> Optional[int]:
        """Calcula días hasta el evento"""
        if self.fecha:
            hoy = date.today()
            return (self.fecha - hoy).days
        return None
    
    @property
    def es_proximo(self) -> bool:
        """Verifica si es en los próximos 14 días"""
        dias = self.dias_hasta_evento
        return dias is not None and 0 <= dias <= 14


class CalendarioAcademicoResponse(BaseModelConfig):
    """Response con eventos del calendario académico"""
    eventos: List[EventoCalendario] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    
    @validator('total')
    def total_matches_list(cls, v, values):
        if 'eventos' in values and v != len(values['eventos']):
            raise ValueError('total no coincide con cantidad de eventos')
        return v
    
    @property
    def tiene_eventos(self) -> bool:
        """Verifica si hay eventos"""
        return self.total > 0
    
    @property
    def eventos_proximos(self) -> List[EventoCalendario]:
        """Retorna solo eventos próximos (14 días)"""
        return [e for e in self.eventos if e.es_proximo]


# =====================================================
# HELPER MODELS
# =====================================================

class ResumenExamenes(BaseModelConfig):
    """Resumen de exámenes del alumno"""
    total_examenes: int = Field(..., ge=0)
    proximos_7_dias: int = Field(..., ge=0)
    por_materia: dict = Field(default_factory=dict)
    
    @property
    def tiene_examenes_proximos(self) -> bool:
        """Verifica si hay exámenes próximos"""
        return self.proximos_7_dias > 0
