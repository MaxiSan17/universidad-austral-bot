"""
Sistema de prompts para generación de respuestas naturales con LLM.
"""

from app.prompts.system_prompts import (
    build_system_prompt,
    build_user_prompt,
    get_tone_emoji,
    get_suggested_length
)

__all__ = [
    "build_system_prompt",
    "build_user_prompt",
    "get_tone_emoji",
    "get_suggested_length"
]
