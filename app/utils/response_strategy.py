"""
Response Strategy - Analiza queries y determina estrategia de respuesta.

Este módulo extrae entidades de la query del usuario y determina:
- Qué información específica pregunta (aula, horario, profesor, etc)
- Qué longitud de respuesta usar
- Qué tono aplicar
- Si usar referencias históricas
"""

from typing import List, Dict, Any, Tuple, Optional
import re
from difflib import SequenceMatcher

from app.models.context import (
    QueryEntity,
    ResponseStrategy,
    ConversationContext
)
from app.prompts.system_prompts import get_suggested_length
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# PATRONES DE ENTIDADES
# ============================================================

# Patrones para detectar qué información específica pregunta el usuario
ENTITY_PATTERNS = {
    "aula": {
        "keywords": ["aula", "salon", "salón", "donde", "dónde", "ubicación", "ubicacion", "lugar"],
        "patterns": [
            r"en qu[eé] aula",
            r"d[oó]nde (?:es|tengo|queda)",
            r"qu[eé] aula"
        ]
    },
    "horario": {
        "keywords": ["hora", "horario", "cuando", "cuándo", "qué hora"],
        "patterns": [
            r"a qu[eé] hora",
            r"qu[eé] horario",
            r"cu[aá]ndo (?:es|tengo)"
        ]
    },
    "profesor": {
        "keywords": ["profesor", "profesora", "profe", "docente", "quien", "quién", "dicta"],
        "patterns": [
            r"qui[eé]n (?:es|da|dicta)",
            r"qu[eé] profesor",
            r"profesor de"
        ]
    },
    "dia": {
        "keywords": ["día", "dia", "cuando", "cuándo", "qué día"],
        "patterns": [
            r"qu[eé] d[ií]a",
            r"cu[aá]ndo tengo"
        ]
    },
    "materia": {
        "keywords": ["materia", "cursada", "clase", "asignatura"],
        "patterns": [
            r"(?:de |para )?(\w+(?:\s+\w+)?)",  # Detectar nombre de materia
        ]
    }
}

# Materias conocidas (para extracción más precisa)
KNOWN_SUBJECTS = {
    "nativa": "Nativa Digital",
    "programación": "Programación I",
    "programacion": "Programación I",
    "matemática": "Matemática Discreta",
    "matematica": "Matemática Discreta",
    "ética": "Ética y Deontología",
    "etica": "Ética y Deontología",
    "fisica": "Física",
    "física": "Física",
}


# ============================================================
# EXTRACTOR DE ENTIDADES
# ============================================================

class QueryEntityExtractor:
    """Extrae entidades de la query del usuario"""

    def __init__(self):
        self.entity_patterns = ENTITY_PATTERNS
        self.known_subjects = KNOWN_SUBJECTS

    def extract_entities(self, query: str) -> List[QueryEntity]:
        """
        Extrae todas las entidades relevantes de la query.

        Args:
            query: Query del usuario

        Returns:
            Lista de QueryEntity detectadas
        """
        entities = []
        query_lower = query.lower().strip()

        # Extraer cada tipo de entidad
        for entity_type, config in self.entity_patterns.items():
            detected = self._detect_entity(query_lower, entity_type, config)
            if detected:
                entities.append(detected)

        logger.info(f"🔍 Entidades extraídas: {[f'{e.entity_type}={e.entity_value}' for e in entities]}")
        return entities

    def _detect_entity(
        self,
        query: str,
        entity_type: str,
        config: Dict[str, Any]
    ) -> Optional[QueryEntity]:
        """
        Detecta una entidad específica en la query.

        Args:
            query: Query en minúsculas
            entity_type: Tipo de entidad a detectar
            config: Configuración con keywords y patterns

        Returns:
            QueryEntity si se detecta, None si no
        """
        # Método 1: Buscar keywords
        for keyword in config["keywords"]:
            if keyword in query:
                logger.debug(f"  ✅ Detectado {entity_type} por keyword: {keyword}")
                return QueryEntity(
                    entity_type=entity_type,
                    entity_value=keyword,
                    confidence=0.9
                )

        # Método 2: Buscar patterns con regex
        for pattern in config.get("patterns", []):
            match = re.search(pattern, query)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                logger.debug(f"  ✅ Detectado {entity_type} por pattern: {pattern}")
                return QueryEntity(
                    entity_type=entity_type,
                    entity_value=value,
                    confidence=0.85
                )

        return None

    def extract_subject_name(self, query: str) -> Optional[str]:
        """
        Extrae el nombre de la materia de la query.

        Args:
            query: Query del usuario

        Returns:
            Nombre de la materia si se detecta, None si no
        """
        query_lower = query.lower()

        # Buscar en materias conocidas
        for keyword, full_name in self.known_subjects.items():
            if keyword in query_lower:
                logger.debug(f"  📚 Materia detectada: {full_name}")
                return full_name

        return None


# ============================================================
# STRATEGY BUILDER
# ============================================================

class ResponseStrategyBuilder:
    """Construye la estrategia de respuesta basada en la query"""

    def __init__(self):
        self.entity_extractor = QueryEntityExtractor()

    def build_strategy(
        self,
        query: str,
        data: Any,
        context: Optional[ConversationContext] = None
    ) -> Tuple[ResponseStrategy, List[QueryEntity]]:
        """
        Construye la estrategia de respuesta completa.

        Args:
            query: Query del usuario
            data: Datos disponibles para responder
            context: Contexto conversacional (opcional)

        Returns:
            Tuple de (ResponseStrategy, List[QueryEntity])
        """
        logger.info(f"🎯 Construyendo estrategia para: '{query}'")

        # Extraer entidades
        entities = self.entity_extractor.extract_entities(query)

        # Determinar focus entities (qué información incluir)
        focus_entities = self._determine_focus_entities(entities, query)

        # Determinar longitud
        length = self._determine_length(entities, data, query)

        # Determinar tono
        tone = context.emotional_state.tone if context else "neutral"

        # Determinar si incluir proactividad
        include_proactive = self._should_include_proactive(query, context)

        # Determinar si referenciar historial
        reference_history = self._should_reference_history(context)

        # Determinar formato
        format_style = self._determine_format_style(entities, length)

        strategy = ResponseStrategy(
            focus_entities=focus_entities,
            length=length,
            tone=tone,
            include_proactive=include_proactive,
            reference_history=reference_history,
            format_style=format_style
        )

        logger.info(f"✅ Estrategia construida: focus={focus_entities}, length={length}, tone={tone}")

        return strategy, entities

    def _determine_focus_entities(
        self,
        entities: List[QueryEntity],
        query: str
    ) -> List[str]:
        """
        Determina en qué entidades enfocarse (qué información incluir).

        Args:
            entities: Entidades extraídas
            query: Query original

        Returns:
            Lista de nombres de entidades para focus
        """
        # Si se detectaron entidades específicas, enfocarse solo en ellas
        if entities:
            return [e.entity_type for e in entities if e.confidence >= 0.7]

        # Si no hay entidades específicas, verificar si es query general
        # Palabras que indican query general (dar toda la info)
        general_keywords = [
            "completo", "completa", "todo", "toda",
            "horarios", "información", "informacion",
            "dame", "mostrame", "ver"
        ]

        query_lower = query.lower()
        if any(kw in query_lower for kw in general_keywords):
            logger.debug("  📋 Query general detectada - incluir toda la información")
            return []  # Lista vacía = incluir todo

        # Por defecto, incluir todo si no hay focus específico
        return []

    def _determine_length(
        self,
        entities: List[QueryEntity],
        data: Any,
        query: str
    ) -> str:
        """
        Determina la longitud apropiada de la respuesta.

        Args:
            entities: Entidades extraídas
            data: Datos disponibles
            query: Query original

        Returns:
            "short", "medium", o "detailed"
        """
        # Si hay entidades muy específicas → respuesta corta
        specific_entities = ["aula", "profesor", "dia"]
        if entities and any(e.entity_type in specific_entities for e in entities):
            return "short"

        # Si pregunta por horarios completos → respuesta detallada
        if "horario" in query.lower() or "clases" in query.lower():
            # Determinar por complejidad de datos
            from app.utils.llm_response_generator import determine_data_complexity
            complexity = determine_data_complexity(data)
            return get_suggested_length(complexity)

        # Por defecto: auto (el LLM decide)
        return "auto"

    def _should_include_proactive(
        self,
        query: str,
        context: Optional[ConversationContext]
    ) -> bool:
        """
        Determina si incluir sugerencias proactivas.

        Args:
            query: Query del usuario
            context: Contexto conversacional

        Returns:
            True si se deben incluir sugerencias
        """
        if not context:
            return False

        # Solo incluir proactividad si:
        # 1. Está habilitada en el contexto
        # 2. Hay sugerencias de alta prioridad
        return (
            context.enable_proactivity and
            len(context.high_priority_suggestions) > 0
        )

    def _should_reference_history(
        self,
        context: Optional[ConversationContext]
    ) -> bool:
        """
        Determina si hacer referencias al historial conversacional.

        Args:
            context: Contexto conversacional

        Returns:
            True si se deben hacer referencias
        """
        if not context:
            return False

        # Referenciar historial si:
        # 1. Hay historial reciente (últimos 5 min)
        # 2. Hay al menos una consulta previa
        return context.has_recent_context

    def _determine_format_style(
        self,
        entities: List[QueryEntity],
        length: str
    ) -> str:
        """
        Determina el estilo de formato.

        Args:
            entities: Entidades extraídas
            length: Longitud determinada

        Returns:
            "conversational", "structured", o "minimal"
        """
        # Si la respuesta es corta → formato minimal
        if length == "short":
            return "minimal"

        # Si la respuesta es detallada → formato structured
        elif length == "detailed":
            return "structured"

        # Por defecto → conversational
        return "conversational"


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

# Crear instancia global del builder
response_strategy_builder = ResponseStrategyBuilder()


# ============================================================
# HELPER FUNCTION
# ============================================================

def build_response_strategy(
    query: str,
    data: Any,
    context: Optional[ConversationContext] = None
) -> Tuple[ResponseStrategy, List[QueryEntity]]:
    """
    Función helper para construir estrategia de respuesta fácilmente.

    Args:
        query: Query del usuario
        data: Datos disponibles
        context: Contexto conversacional (opcional)

    Returns:
        Tuple de (ResponseStrategy, List[QueryEntity])

    Example:
        ```python
        strategy, entities = build_response_strategy(
            query="¿En qué aula tengo ética?",
            data=horarios_response,
            context=conversation_context
        )
        ```
    """
    return response_strategy_builder.build_strategy(query, data, context)
