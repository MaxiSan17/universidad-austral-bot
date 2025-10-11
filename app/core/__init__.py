"""
Core package - Configuración, constantes y excepciones
"""
from app.core.config import settings, get_settings, Settings
from app.core.constants import (
    DIAS_SEMANA_ES,
    MESES_ES,
    TIPOS_EXAMEN,
    EMOJIS,
    DEPARTAMENTOS,
    KEYWORDS,
    MENSAJE_BIENVENIDA,
    MENSAJE_ERROR_GENERICO,
    MENSAJE_DNI_INVALIDO
)
from app.core.exceptions import (
    UniversidadAustralException,
    ValidationError,
    InvalidDNIError,
    InvalidUUIDError,
    DatabaseError,
    SupabaseError,
    RecordNotFoundError,
    AuthenticationError,
    UserNotFoundError,
    ToolError,
    IntegrationError,
    BusinessLogicError
)

__all__ = [
    # Config
    'settings',
    'get_settings',
    'Settings',
    
    # Constants
    'DIAS_SEMANA_ES',
    'MESES_ES',
    'TIPOS_EXAMEN',
    'EMOJIS',
    'DEPARTAMENTOS',
    'KEYWORDS',
    'MENSAJE_BIENVENIDA',
    'MENSAJE_ERROR_GENERICO',
    'MENSAJE_DNI_INVALIDO',
    
    # Exceptions
    'UniversidadAustralException',
    'ValidationError',
    'InvalidDNIError',
    'InvalidUUIDError',
    'DatabaseError',
    'SupabaseError',
    'RecordNotFoundError',
    'AuthenticationError',
    'UserNotFoundError',
    'ToolError',
    'IntegrationError',
    'BusinessLogicError',
]
