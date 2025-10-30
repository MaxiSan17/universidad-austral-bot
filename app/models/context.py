"""
Modelos Pydantic para contexto conversacional enriquecido.

Estos modelos estructuran el contexto que se pasa al LLM Response Generator
para generar respuestas naturales y contextuales.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.utils.emotional_tone import ToneType


class EmotionalState(BaseModel):
    """Estado emocional detectado del contexto"""

    tone: ToneType = Field(
        default="neutral",
        description="Tono emocional detectado"
    )

    urgency_level: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Nivel de urgencia (0-5): 0=ninguna, 5=crítica"
    )

    celebration_worthy: bool = Field(
        default=False,
        description="Si el contexto merece celebración (ej: sin deuda, día libre)"
    )

    empathy_needed: bool = Field(
        default=False,
        description="Si se necesita empatía (ej: muchas clases, deuda grande)"
    )

    context_description: Optional[str] = Field(
        default=None,
        description="Descripción del contexto emocional detectado"
    )


class QueryEntity(BaseModel):
    """Entidad extraída de la query del usuario"""

    entity_type: str = Field(
        ...,
        description="Tipo de entidad: materia, aula, profesor, día, horario"
    )

    entity_value: str = Field(
        ...,
        description="Valor de la entidad extraída"
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confianza en la extracción (0.0-1.0)"
    )


class PreviousQuery(BaseModel):
    """Información sobre una consulta previa relevante"""

    query: str = Field(..., description="Query del usuario")
    query_type: str = Field(..., description="Tipo de query")
    timestamp: datetime = Field(default_factory=datetime.now)
    summary: Optional[str] = Field(None, description="Resumen de la respuesta dada")


class ProactiveSuggestion(BaseModel):
    """Sugerencia proactiva para incluir en la respuesta"""

    suggestion_type: str = Field(
        ...,
        description="Tipo de sugerencia: related_info, reminder, follow_up"
    )

    content: str = Field(
        ...,
        description="Contenido de la sugerencia"
    )

    priority: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Prioridad de la sugerencia (1=baja, 3=alta)"
    )

    reason: Optional[str] = Field(
        None,
        description="Razón por la que se sugiere esto"
    )


class ConversationContext(BaseModel):
    """
    Contexto conversacional completo para generar respuestas naturales.

    Este modelo agrupa toda la información relevante que el LLM necesita
    para generar una respuesta contextual y empática.
    """

    # Información de la query actual
    current_query: str = Field(..., description="Query actual del usuario")
    query_type: str = Field(..., description="Tipo de query clasificado")
    extracted_entities: List[QueryEntity] = Field(
        default_factory=list,
        description="Entidades extraídas de la query"
    )

    # Contexto emocional
    emotional_state: EmotionalState = Field(
        default_factory=EmotionalState,
        description="Estado emocional detectado"
    )

    # Historial conversacional (últimas 24h)
    recent_queries: List[PreviousQuery] = Field(
        default_factory=list,
        description="Consultas recientes relevantes (últimas 24h)"
    )

    has_conversation_history: bool = Field(
        default=False,
        description="Si hay historial previo disponible"
    )

    # Sugerencias proactivas
    proactive_suggestions: List[ProactiveSuggestion] = Field(
        default_factory=list,
        description="Sugerencias proactivas para incluir"
    )

    # Información del usuario
    user_name: str = Field(..., description="Nombre del usuario")
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Preferencias del usuario (longitud, formalidad, etc)"
    )

    # Metadata temporal
    current_time: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp actual para contexto temporal"
    )

    temporal_context: Optional[str] = Field(
        None,
        description="Contexto temporal detectado (hoy, mañana, esta semana)"
    )

    # Configuración de respuesta
    response_length_preference: str = Field(
        default="auto",
        description="Preferencia de longitud: short, medium, detailed, auto"
    )

    enable_proactivity: bool = Field(
        default=True,
        description="Si se permiten sugerencias proactivas"
    )

    @property
    def has_urgent_context(self) -> bool:
        """Si hay contexto urgente que requiere atención especial"""
        return self.emotional_state.urgency_level >= 4

    @property
    def should_celebrate(self) -> bool:
        """Si la respuesta debería tener tono celebratorio"""
        return self.emotional_state.celebration_worthy

    @property
    def needs_empathy(self) -> bool:
        """Si la respuesta necesita tono empático"""
        return self.emotional_state.empathy_needed

    @property
    def high_priority_suggestions(self) -> List[ProactiveSuggestion]:
        """Sugerencias de alta prioridad"""
        return [s for s in self.proactive_suggestions if s.priority >= 3]

    @property
    def has_recent_context(self) -> bool:
        """Si hay contexto conversacional reciente"""
        if not self.recent_queries:
            return False

        # Considerar reciente si fue en los últimos 5 minutos
        latest = max(self.recent_queries, key=lambda q: q.timestamp)
        minutes_ago = (self.current_time - latest.timestamp).total_seconds() / 60
        return minutes_ago <= 5


class ResponseStrategy(BaseModel):
    """
    Estrategia determinada para generar la respuesta.

    Define qué información incluir, qué longitud usar, y qué tono aplicar.
    """

    focus_entities: List[str] = Field(
        default_factory=list,
        description="Entidades en las que enfocarse (solo incluir estas)"
    )

    length: str = Field(
        default="medium",
        description="Longitud objetivo: short, medium, detailed"
    )

    tone: ToneType = Field(
        default="neutral",
        description="Tono a aplicar"
    )

    include_proactive: bool = Field(
        default=True,
        description="Si incluir sugerencias proactivas"
    )

    reference_history: bool = Field(
        default=False,
        description="Si hacer referencias al historial conversacional"
    )

    format_style: str = Field(
        default="conversational",
        description="Estilo de formato: conversational, structured, minimal"
    )
