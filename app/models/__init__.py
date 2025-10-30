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

# Academic models
from app.models.academic import (
    # Requests
    HorariosRequest,
    InscripcionesRequest,
    ProfesorRequest,
    AulaRequest,
    CreditosVURequest,
    
    # Responses
    HorarioInfo,
    HorariosResponse,
    InscripcionInfo,
    InscripcionesResponse,
    ProfesorInfo,
    ProfesorResponse,
    AulaInfo,
    AulaResponse,
    CreditosVUInfo,
    CreditosVUResponse,
)

# Calendar models
from app.models.calendar import (
    # Enums
    TipoExamen,
    TipoEvento,

    # Requests
    ExamenesRequest,
    CalendarioAcademicoRequest,
    ProximosExamenesRequest,

    # Responses
    ExamenInfo,
    ExamenesResponse,
    EventoCalendario,
    CalendarioAcademicoResponse,
    ResumenExamenes,
)

# Context models (NUEVO - para LLM Response Generation)
from app.models.context import (
    EmotionalState,
    QueryEntity,
    PreviousQuery,
    ProactiveSuggestion,
    ConversationContext,
    ResponseStrategy,
)

__all__ = [
    # Common - Enums
    'TipoUsuario',
    'EstadoInscripcion',
    'Modalidad',
    'DiaSemana',
    
    # Common - Base
    'BaseModelConfig',
    'UUIDMixin',
    
    # Common - Usuario
    'UsuarioBase',
    'Alumno',
    'Profesor',
    
    # Common - Academic
    'MateriaBase',
    'ComisionBase',
    
    # Common - Response
    'PaginatedResponse',
    'ErrorResponse',
    
    # Common - Validators
    'validate_fecha_range',
    'validate_horario',
    
    # Academic - Requests
    'HorariosRequest',
    'InscripcionesRequest',
    'ProfesorRequest',
    'AulaRequest',
    'CreditosVURequest',
    
    # Academic - Responses
    'HorarioInfo',
    'HorariosResponse',
    'InscripcionInfo',
    'InscripcionesResponse',
    'ProfesorInfo',
    'ProfesorResponse',
    'AulaInfo',
    'AulaResponse',
    'CreditosVUInfo',
    'CreditosVUResponse',
    
    # Calendar - Enums
    'TipoExamen',
    'TipoEvento',
    
    # Calendar - Requests
    'ExamenesRequest',
    'CalendarioAcademicoRequest',
    'ProximosExamenesRequest',
    
    # Calendar - Responses
    'ExamenInfo',
    'ExamenesResponse',
    'EventoCalendario',
    'CalendarioAcademicoResponse',
    'ResumenExamenes',

    # Context models (NUEVO - LLM Response Generation)
    'EmotionalState',
    'QueryEntity',
    'PreviousQuery',
    'ProactiveSuggestion',
    'ConversationContext',
    'ResponseStrategy',
]
