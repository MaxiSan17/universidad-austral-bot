"""
Detector de saludos en mensajes del usuario
"""
import re
from typing import List
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GreetingDetector:
    """
    Detecta si un mensaje contiene un saludo.

    Tolerante a variaciones, typos y emojis.
    """

    def __init__(self):
        # Saludos comunes en español argentino
        self.greeting_patterns = [
            # Saludos generales
            r'\bhola+\b',
            r'\bbuenas+\b',
            r'\bbuen\s+d[ií]a+\b',
            r'\bbuenos+\s+d[ií]as+\b',
            r'\bbuenas+\s+tardes+\b',
            r'\bbuenas+\s+noches+\b',
            r'\bbuen\s+d[ií]a+\b',

            # Variaciones informales
            r'\bque+\s+tal+\b',
            r'\bqu[eé]\s+tal+\b',
            r'\bc[oó]mo\s+(and[aá]s|est[aá]s|va)\b',
            r'\btodo\s+bien\b',
            r'\bche\b',

            # Saludos con typos comunes
            r'\bholaaa+\b',
            r'\bbuenaa+s+\b',
            r'\bholi+\b',
            r'\bhey+\b',
            r'\bhi+\b',

            # Saludos formales
            r'\bbuen\s+d[ií]a+\b',
            r'\bsaludos+\b',
        ]

        # Emojis de saludo
        self.greeting_emojis = ['👋', '🙋', '✋', '🖐️', '👏', '🙌']

    def is_greeting(self, message: str) -> bool:
        """
        Detecta si el mensaje contiene un saludo.

        Args:
            message: Mensaje del usuario (puede ser multilínea)

        Returns:
            True si contiene un saludo, False en caso contrario
        """
        if not message:
            return False

        message_lower = message.lower().strip()

        # Buscar patrones de saludo
        for pattern in self.greeting_patterns:
            if re.search(pattern, message_lower):
                logger.debug(f"✋ Saludo detectado con patrón: {pattern}")
                return True

        # Buscar emojis de saludo
        for emoji in self.greeting_emojis:
            if emoji in message:
                logger.debug(f"✋ Saludo detectado con emoji: {emoji}")
                return True

        return False

    def extract_greeting_from_message(self, message: str) -> str:
        """
        Extrae solo la parte de saludo del mensaje.

        Args:
            message: Mensaje completo

        Returns:
            La parte del mensaje que es saludo (primera línea si es multilínea)
        """
        if not self.is_greeting(message):
            return ""

        # Si es multilínea, tomar solo la primera línea si contiene el saludo
        lines = message.split('\n')
        for line in lines:
            if self.is_greeting(line):
                return line.strip()

        return message.strip()


# Instancia global
greeting_detector = GreetingDetector()
