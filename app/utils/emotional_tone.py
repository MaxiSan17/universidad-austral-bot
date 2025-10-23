"""
Emotional Tone Detection para adaptar el tono de las respuestas.

Este módulo detecta contextos emocionales y sugiere tonos apropiados:
- Urgencia (examen mañana)
- Celebración (sin deudas, día libre)
- Empatía (deuda grande, muchos exámenes)
- Ánimo (examen próximo)
"""

from typing import Literal, Optional
from datetime import date
from app.core.constants import EMOJIS
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Type hints
ToneType = Literal["neutral", "urgente", "celebracion", "empatia", "animo", "tranquilo"]


class EmotionalContext:
    """Contexto emocional detectado con sugerencias de tono"""

    def __init__(
        self,
        tone: ToneType,
        emoji: str,
        prefix: str = "",
        suffix: str = ""
    ):
        self.tone = tone
        self.emoji = emoji
        self.prefix = prefix  # Texto a agregar al inicio
        self.suffix = suffix  # Texto a agregar al final


def detect_exam_urgency(dias_hasta_examen: int) -> Optional[EmotionalContext]:
    """
    Detecta urgencia de examen y sugiere tono.

    Args:
        dias_hasta_examen: Días hasta el examen más próximo

    Returns:
        EmotionalContext si hay urgencia, None si es normal
    """
    if dias_hasta_examen == 0:
        return EmotionalContext(
            tone="urgente",
            emoji=EMOJIS["hoy"],
            prefix="⚠️ ",
            suffix=""
        )
    elif dias_hasta_examen == 1:
        return EmotionalContext(
            tone="animo",
            emoji=EMOJIS["animo"],
            prefix="",
            suffix="\n\n¡Mucha suerte! 💪"
        )
    elif dias_hasta_examen <= 3:
        return EmotionalContext(
            tone="animo",
            emoji=EMOJIS["mañana"],
            prefix="",
            suffix=""
        )
    else:
        return None  # Tono neutral


def detect_financial_context(
    tiene_deuda: bool,
    monto_deuda: Optional[float] = None
) -> Optional[EmotionalContext]:
    """
    Detecta contexto financiero y sugiere tono.

    Args:
        tiene_deuda: Si tiene deuda pendiente
        monto_deuda: Monto de la deuda (opcional)

    Returns:
        EmotionalContext apropiado
    """
    if not tiene_deuda:
        return EmotionalContext(
            tone="celebracion",
            emoji=EMOJIS["exito"],
            prefix="✅ ",
            suffix=""
        )

    # Tiene deuda
    if monto_deuda and monto_deuda > 300000:
        # Deuda grande - empatía
        return EmotionalContext(
            tone="empatia",
            emoji=EMOJIS["preocupacion"],
            prefix="",
            suffix="\n\n¿Querés que te ayude a consultar opciones de pago?"
        )
    else:
        # Deuda normal - neutral
        return EmotionalContext(
            tone="neutral",
            emoji=EMOJIS["info"],
            prefix="",
            suffix=""
        )


def detect_schedule_context(
    tiene_clases: bool,
    total_clases: int = 0
) -> Optional[EmotionalContext]:
    """
    Detecta contexto de horarios y sugiere tono.

    Args:
        tiene_clases: Si tiene clases en el período consultado
        total_clases: Total de clases

    Returns:
        EmotionalContext apropiado
    """
    if not tiene_clases:
        return EmotionalContext(
            tone="celebracion",
            emoji=EMOJIS["celebracion"],
            prefix="¡Día libre! 🎉 ",
            suffix=""
        )

    if total_clases >= 5:
        # Muchas clases - empatía
        return EmotionalContext(
            tone="empatia",
            emoji=EMOJIS["clase"],
            prefix="",
            suffix="\n\n¡Día intenso! 💪"
        )

    return None  # Tono neutral


def detect_credits_context(
    creditos_actuales: int,
    creditos_necesarios: int
) -> Optional[EmotionalContext]:
    """
    Detecta contexto de créditos VU y sugiere tono.

    Args:
        creditos_actuales: Créditos completados
        creditos_necesarios: Créditos requeridos

    Returns:
        EmotionalContext apropiado
    """
    porcentaje = (creditos_actuales / creditos_necesarios) * 100

    if creditos_actuales >= creditos_necesarios:
        # Completó el requisito
        return EmotionalContext(
            tone="celebracion",
            emoji=EMOJIS["celebracion"],
            prefix="¡Felicitaciones! 🎉 ",
            suffix=""
        )
    elif porcentaje >= 75:
        # Muy cerca
        return EmotionalContext(
            tone="animo",
            emoji=EMOJIS["animo"],
            prefix="",
            suffix="\n\n¡Casi llegás! 💪"
        )
    elif porcentaje < 30:
        # Muy lejos
        return EmotionalContext(
            tone="neutral",
            emoji=EMOJIS["info"],
            prefix="",
            suffix="\n\n💡 Recordá que necesitás completar estos créditos para graduarte"
        )

    return None  # Tono neutral


def apply_emotional_tone(
    base_response: str,
    context: Optional[EmotionalContext]
) -> str:
    """
    Aplica el tono emocional a una respuesta base.

    Args:
        base_response: Respuesta sin tono emocional
        context: Contexto emocional detectado

    Returns:
        Respuesta con tono aplicado

    Examples:
        >>> context = EmotionalContext("animo", "💪", "", "¡Mucha suerte!")
        >>> apply_emotional_tone("Tu examen es mañana", context)
        "Tu examen es mañana\n\n¡Mucha suerte! 💪"
    """
    if not context:
        return base_response

    response = base_response

    # Aplicar prefix
    if context.prefix:
        response = context.prefix + response

    # Aplicar suffix
    if context.suffix:
        response = response + context.suffix

    logger.debug(f"Aplicado tono emocional: {context.tone}")
    return response


def get_no_results_message(
    item_type: str,
    context: Optional[str] = None,
    emotional: bool = True
) -> str:
    """
    Genera mensaje cuando no hay resultados, con tono apropiado.

    Args:
        item_type: Tipo de item buscado ("clases", "exámenes", etc)
        context: Contexto temporal ("hoy", "esta semana")
        emotional: Si aplicar tono emocional

    Returns:
        Mensaje formateado

    Examples:
        >>> get_no_results_message("clases", "hoy", emotional=True)
        "¡Día libre! 🎉 No tenés clases hoy"
    """
    # Casos especiales con celebración
    if item_type == "clases" and emotional:
        if context:
            return f"¡Día libre! {EMOJIS['celebracion']} No tenés {item_type} {context}"
        return f"{EMOJIS['info']} No tenés {item_type} registradas"

    if item_type == "exámenes" and emotional:
        if context:
            return f"{EMOJIS['info']} No tenés {item_type} {context}\n\n¡Podés relajarte! {EMOJIS['tranquilo']}"
        return f"{EMOJIS['info']} No tenés {item_type} programados en los próximos días"

    if item_type == "deuda" and emotional:
        return f"{EMOJIS['exito']} ¡Estás al día! No tenés deudas pendientes {EMOJIS['celebracion']}"

    # Mensaje genérico
    if context:
        return f"{EMOJIS['info']} No encontré {item_type} {context}"
    return f"{EMOJIS['info']} No encontré {item_type}"
