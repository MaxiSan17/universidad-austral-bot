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

    def has_content_beyond_greeting(self, message: str) -> bool:
        """
        Detecta si hay contenido significativo además del saludo.

        Args:
            message: Mensaje del usuario

        Returns:
            True si hay una petición/consulta además del saludo
            False si es solo un saludo cordial
        """
        if not message:
            return False

        message_lower = message.lower().strip()

        # Remover saludos conocidos
        cleaned = message_lower

        # Remover todas las variantes de saludos (con y sin tildes)
        greeting_words = [
            'hola', 'buenas', 'buenos días', 'buenos dias', 'buen día', 'buen dia',
            'buenas tardes', 'buenas noches', 'que tal', 'qué tal',
            'como andas', 'cómo andás', 'como andás', 'cómo andas',
            'como estas', 'cómo estás', 'como estás', 'cómo estas',
            'todo bien', 'che', 'holi', 'hey', 'hi', 'saludos'
        ]

        for greeting in greeting_words:
            # Remover con variaciones de repetición (holaaa, buenaaas)
            pattern = greeting[0] + greeting[1:-1] + greeting[-1] + '+'
            cleaned = re.sub(r'\b' + pattern + r'\b', '', cleaned, flags=re.IGNORECASE)
            # Remover normal
            cleaned = cleaned.replace(greeting, '')

        # Remover emojis de saludo
        for emoji in self.greeting_emojis:
            cleaned = cleaned.replace(emoji, '')

        # Remover puntuación, espacios, saltos de línea
        cleaned = re.sub(r'[!?¿¡,.\n\s]+', ' ', cleaned).strip()

        # Si queda contenido significativo (>10 caracteres), hay una petición real
        has_content = len(cleaned) > 10

        if has_content:
            logger.debug(f"💬 Contenido más allá del saludo: '{cleaned[:50]}...'")
        else:
            logger.debug(f"👋 Solo saludo, sin contenido adicional")

        return has_content

    def remove_greeting_from_message(self, message: str) -> str:
        """
        Remueve el saludo del mensaje y retorna solo el contenido restante.

        Args:
            message: Mensaje completo

        Returns:
            Mensaje sin el saludo (útil para procesar la consulta real)
        """
        if not self.is_greeting(message):
            return message

        cleaned = message.lower()

        # Remover patrones de saludo específicos
        for pattern in self.greeting_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Remover emojis de saludo
        for emoji in self.greeting_emojis:
            cleaned = cleaned.replace(emoji, '')

        # Remover puntuación extra al inicio (comas, signos de exclamación/interrogación)
        cleaned = re.sub(r'^[,¡!¿?\s]+', '', cleaned)
        cleaned = cleaned.strip()

        # Si quedó vacío, retornar el mensaje original
        if not cleaned:
            return message

        return cleaned


# Instancia global
greeting_detector = GreetingDetector()
