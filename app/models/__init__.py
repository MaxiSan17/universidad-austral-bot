"""
Models package - Modelos Pydantic para requests y responses
"""
from app.models.common import (
    # Enums
    TipoUsuario,
    EstadoInscripcion,
    Modalidad,
    DiaSemana,
    
    # Base models
    BaseModelConfig,
    UUIDMixin,
    
    # Usuario models
    UsuarioBase,
    Alumno,
    Profesor,
    
    # Academic models
    MateriaBase,
    ComisionBase,
    
    # Response models
    PaginatedResponse,
    ErrorResponse,
    
    # Validators
    validate_fecha_range,
    validate_horario,
)

__all__ = [
    # Enums
    'TipoUsuario',
    'EstadoInscripcion',
    'Modalidad',
    'DiaSemana',
    
    # Base
    'BaseModelConfig',
    'UUIDMixin',
    
    # Usuario
    'UsuarioBase',
    'Alumno',
    'Profesor',
    
    # Academic
    'MateriaBase',
    'ComisionBase',
    
    # Response
    'PaginatedResponse',
    'ErrorResponse',
    
    # Validators
    'validate_fecha_range',
    'validate_horario',
]
