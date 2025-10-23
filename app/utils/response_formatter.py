"""
Response Formatter Utilities para mejorar la UX del bot.

Este módulo provee funciones para:
- Variación de tono conversacional
- Saludos adaptativos por hora del día
- Selección aleatoria de aperturas/cierres
- Formateo progresivo (resumen → detalle)
"""

import random
from datetime import datetime
from typing import Optional
from app.core.constants import (
    GREETING_VARIATIONS,
    GREETING_TIME_BASED,
    CLOSING_VARIATIONS,
    EMOJIS
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_random_greeting(nombre: str, use_time_based: bool = False) -> str:
    """
    Retorna un saludo aleatorio o basado en la hora del día.

    Args:
        nombre: Nombre del usuario
        use_time_based: Si True, usa saludo según hora del día

    Returns:
        Saludo formateado

    Examples:
        >>> get_random_greeting("Juan")
        "¡Hola Juan!"
        >>> get_random_greeting("María", use_time_based=True)
        "¡Buenos días, María! ☀️"  # (si es de mañana)
    """
    if use_time_based:
        hora_actual = datetime.now().hour

        if 6 <= hora_actual < 12:
            time_period = "morning"
        elif 12 <= hora_actual < 18:
            time_period = "afternoon"
        elif 18 <= hora_actual < 22:
            time_period = "evening"
        else:
            time_period = "night"

        greeting_template = GREETING_TIME_BASED[time_period]
        return greeting_template.format(nombre=nombre)

    # Saludo aleatorio
    greeting_template = random.choice(GREETING_VARIATIONS)
    return greeting_template.format(nombre=nombre)


def get_random_closing() -> str:
    """
    Retorna un cierre conversacional aleatorio.

    Returns:
        Cierre de conversación (puede ser string vacío)

    Examples:
        >>> get_random_closing()
        "¿Algo más? 🤝"
    """
    return random.choice(CLOSING_VARIATIONS)


def format_progressive_response(
    summary: str,
    detail: Optional[str] = None,
    show_detail_prompt: bool = True
) -> str:
    """
    Formatea una respuesta progresiva: primero resumen, luego detalle opcional.

    Args:
        summary: Resumen ejecutivo (siempre se muestra)
        detail: Detalle completo (opcional)
        show_detail_prompt: Si True, muestra sugerencia de "escribí X para ver más"

    Returns:
        Respuesta formateada

    Examples:
        >>> format_progressive_response(
        ...     "Tenés 3 exámenes esta semana",
        ...     "Detalles...",
        ...     show_detail_prompt=True
        ... )
        "Tenés 3 exámenes esta semana\n\n💡 Escribí 'detalles' para ver la info completa"
    """
    output = summary

    if detail:
        output += f"\n\n{detail}"
    elif show_detail_prompt:
        output += f"\n\n💡 Escribí 'detalles' para ver la info completa"

    return output


def format_urgency_indicator(dias_hasta: int) -> tuple[str, str]:
    """
    Retorna emoji y texto según urgencia temporal.

    Args:
        dias_hasta: Días hasta el evento

    Returns:
        (emoji, texto_urgencia)

    Examples:
        >>> format_urgency_indicator(0)
        ('🔴', '¡HOY!')
        >>> format_urgency_indicator(1)
        ('🟡', '¡MAÑANA!')
        >>> format_urgency_indicator(5)
        ('🟢', 'En 5 días')
    """
    if dias_hasta == 0:
        return EMOJIS["hoy"], "¡HOY!"
    elif dias_hasta == 1:
        return EMOJIS["mañana"], "¡MAÑANA!"
    elif dias_hasta <= 3:
        return EMOJIS["mañana"], f"En {dias_hasta} días"
    elif dias_hasta <= 7:
        return EMOJIS["proximo"], f"En {dias_hasta} días"
    else:
        return EMOJIS["proximo"], f"En {dias_hasta} días"


def create_summary_line(
    total_items: int,
    item_type: str,
    context: Optional[str] = None
) -> str:
    """
    Crea una línea de resumen ejecutivo.

    Args:
        total_items: Cantidad de items
        item_type: Tipo de item (ej: "clases", "exámenes")
        context: Contexto temporal opcional (ej: "hoy", "esta semana")

    Returns:
        Línea de resumen

    Examples:
        >>> create_summary_line(3, "clases", "mañana")
        "Mañana tenés 3 clases"
        >>> create_summary_line(1, "examen")
        "Tenés 1 examen"
    """
    # Singular/plural
    if total_items == 1:
        item_text = item_type.rstrip('s')  # "clases" → "clase"
    else:
        item_text = item_type

    # Con o sin contexto
    if context:
        return f"{context.capitalize()} tenés {total_items} {item_text}"
    else:
        return f"Tenés {total_items} {item_text}"


def get_modalidad_emoji(modalidad: str) -> str:
    """
    Retorna emoji visual según modalidad.

    Args:
        modalidad: "presencial", "virtual", "hibrida"

    Returns:
        Emoji correspondiente

    Examples:
        >>> get_modalidad_emoji("presencial")
        "🏫"
    """
    modalidad_lower = modalidad.lower()

    if "presencial" in modalidad_lower:
        return EMOJIS["presencial"]
    elif "virtual" in modalidad_lower or "remoto" in modalidad_lower:
        return EMOJIS["virtual"]
    elif "hibrido" in modalidad_lower or "hibrida" in modalidad_lower:
        return EMOJIS["hibrida"]
    else:
        return "📍"  # Default


def truncate_if_long(text: str, max_length: int = 300) -> str:
    """
    Trunca texto si excede longitud máxima.

    Args:
        text: Texto a truncar
        max_length: Longitud máxima

    Returns:
        Texto truncado con "..." si fue necesario
    """
    if len(text) <= max_length:
        return text

    return text[:max_length].rsplit(' ', 1)[0] + "..."


def build_response(
    greeting: str,
    body: str,
    closing: str = "",
    emoji_start: str = ""
) -> str:
    """
    Construye una respuesta completa con estructura consistente.

    Args:
        greeting: Saludo inicial
        body: Cuerpo del mensaje
        closing: Cierre conversacional
        emoji_start: Emoji opcional al inicio

    Returns:
        Respuesta formateada

    Examples:
        >>> build_response("¡Hola Juan!", "Tenés clase mañana", "¿Algo más?", "📚")
        "📚 ¡Hola Juan!\n\nTenés clase mañana\n\n¿Algo más?"
    """
    parts = []

    # Emoji + greeting
    if emoji_start and greeting:
        parts.append(f"{emoji_start} {greeting}")
    elif greeting:
        parts.append(greeting)

    # Body
    if body:
        parts.append(body)

    # Closing
    if closing:
        parts.append(closing)

    return "\n\n".join(parts)
