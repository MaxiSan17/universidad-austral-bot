"""
Modelos Pydantic comunes compartidos entre todos los módulos
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Literal
from datetime import date, datetime
from enum import Enum
import uuid


# =====================================================
# ENUMS
# =====================================================

class TipoUsuario(str, Enum):
    """Tipos de usuario en el sistema"""
    ALUMNO = "Alumno"
    PROFESOR = "Profesor"
    ADMIN = "Administrador"


class EstadoInscripcion(str, Enum):
    """Estados de inscripción a materias"""
    CURSANDO = "cursando"
    APROBADA = "aprobada"
    DESAPROBADA = "desaprobada"
    ABANDONO = "abandono"


class Modalidad(str, Enum):
    """Modalidades de cursada"""
    PRESENCIAL = "presencial"
    VIRTUAL = "virtual"
    HIBRIDA = "hibrida"


class DiaSemana(int, Enum):
    """Días de la semana"""
    LUNES = 1
    MARTES = 2
    MIERCOLES = 3
    JUEVES = 4
    VIERNES = 5
    SABADO = 6
    DOMINGO = 7


# =====================================================
# MODELOS BASE
# =====================================================

class BaseModelConfig(BaseModel):
    """Configuración base para todos los modelos"""
    
    class Config:
        # Permitir validación por nombre de campo
        validate_assignment = True
        # Usar enum values en lugar de enum names
        use_enum_values = True
        # Permitir población por nombre de campo o alias
        populate_by_name = True
        # Configuración de JSON
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class UUIDMixin(BaseModel):
    """Mixin para validación de UUIDs"""
    
    @staticmethod
    def validate_uuid(value: str) -> str:
        """Valida que un string sea un UUID válido"""
        try:
            uuid.UUID(str(value))
            return value
        except (ValueError, AttributeError, TypeError):
            raise ValueError(f"'{value}' no es un UUID válido")


# =====================================================
# MODELOS DE USUARIO
# =====================================================

class UsuarioBase(BaseModelConfig):
    """Información básica de usuario"""
    id: str
    dni: str = Field(..., min_length=7, max_length=10)
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    tipo: TipoUsuario
    nombre_preferido: Optional[str] = None
    
    @validator('id')
    def validate_id(cls, v):
        return UUIDMixin.validate_uuid(v)
    
    @validator('dni')
    def validate_dni(cls, v):
        """Valida que el DNI sea solo números"""
        if not v.isdigit():
            raise ValueError('DNI debe contener solo números')
        return v
    
    @property
    def nombre_completo(self) -> str:
        """Retorna nombre completo"""
        return f"{self.nombre} {self.apellido}"
    
    @property
    def nombre_display(self) -> str:
        """Retorna el nombre preferido o nombre real"""
        return self.nombre_preferido or self.nombre


class Alumno(UsuarioBase):
    """Modelo de alumno"""
    tipo: Literal[TipoUsuario.ALUMNO] = TipoUsuario.ALUMNO
    legajo: str = Field(..., min_length=1, max_length=20)
    carrera: Optional[str] = None
    telefono_whatsapp: Optional[str] = None


class Profesor(UsuarioBase):
    """Modelo de profesor"""
    tipo: Literal[TipoUsuario.PROFESOR] = TipoUsuario.PROFESOR
    departamento: Optional[str] = None
    email: Optional[EmailStr] = None


# =====================================================
# MODELOS ACADÉMICOS COMUNES
# =====================================================

class MateriaBase(BaseModelConfig):
    """Información básica de una materia"""
    id: Optional[str] = None
    nombre: str = Field(..., min_length=1, max_length=200)
    codigo: str = Field(..., min_length=1, max_length=20)
    
    @validator('id')
    def validate_id(cls, v):
        if v:
            return UUIDMixin.validate_uuid(v)
        return v


class ComisionBase(BaseModelConfig):
    """Información básica de una comisión"""
    id: Optional[str] = None
    codigo_comision: str = Field(..., min_length=1, max_length=20)
    materia_id: str
    
    @validator('id', 'materia_id')
    def validate_ids(cls, v):
        if v:
            return UUIDMixin.validate_uuid(v)
        return v


# =====================================================
# MODELOS DE RESPUESTA BASE
# =====================================================

class PaginatedResponse(BaseModelConfig):
    """Response paginado genérico"""
    total: int = Field(..., ge=0, description="Total de items")
    page: int = Field(default=1, ge=1, description="Página actual")
    page_size: int = Field(default=20, ge=1, le=100, description="Items por página")
    
    @property
    def total_pages(self) -> int:
        """Calcula el total de páginas"""
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        """Verifica si hay siguiente página"""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Verifica si hay página anterior"""
        return self.page > 1


class ErrorResponse(BaseModelConfig):
    """Response de error estándar"""
    error: str = Field(..., description="Mensaje de error")
    error_code: Optional[str] = Field(None, description="Código de error")
    details: Optional[dict] = Field(None, description="Detalles adicionales del error")
    timestamp: datetime = Field(default_factory=datetime.now)


# =====================================================
# VALIDADORES COMUNES
# =====================================================

def validate_fecha_range(fecha_desde: Optional[date], fecha_hasta: Optional[date]) -> tuple:
    """
    Valida que el rango de fechas sea coherente
    
    Returns:
        tuple con (fecha_desde, fecha_hasta) validadas
    """
    if fecha_desde and fecha_hasta:
        if fecha_hasta < fecha_desde:
            raise ValueError('fecha_hasta debe ser posterior a fecha_desde')
    
    return fecha_desde, fecha_hasta


def validate_horario(hora_inicio: str, hora_fin: str) -> tuple:
    """
    Valida que los horarios sean coherentes (HH:MM formato)
    
    Returns:
        tuple con (hora_inicio, hora_fin) validadas
    """
    import re
    
    # Validar formato HH:MM
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    
    if not re.match(pattern, hora_inicio):
        raise ValueError(f'hora_inicio "{hora_inicio}" debe tener formato HH:MM')
    
    if not re.match(pattern, hora_fin):
        raise ValueError(f'hora_fin "{hora_fin}" debe tener formato HH:MM')
    
    # Validar que hora_fin sea posterior a hora_inicio
    h_i, m_i = map(int, hora_inicio.split(':'))
    h_f, m_f = map(int, hora_fin.split(':'))
    
    minutos_inicio = h_i * 60 + m_i
    minutos_fin = h_f * 60 + m_f
    
    if minutos_fin <= minutos_inicio:
        raise ValueError('hora_fin debe ser posterior a hora_inicio')
    
    return hora_inicio, hora_fin
