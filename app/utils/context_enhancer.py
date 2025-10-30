"""
Context Enhancer - Enriquece el contexto conversacional.

Este módulo toma el contexto básico y lo enriquece con:
- Historial conversacional relevante (últimas 24h)
- Estado emocional detectado
- Sugerencias proactivas
- Referencias temporales
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.context import (
    ConversationContext,
    EmotionalState,
    PreviousQuery,
    ProactiveSuggestion,
    QueryEntity
)
from app.session.session_manager import Session
from app.utils.emotional_tone import (
    detect_schedule_context,
    detect_exam_urgency,
    detect_credits_context,
    EmotionalContext as LegacyEmotionalContext
)
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


# ============================================================
# CONTEXT ENHANCER
# ============================================================

class ContextEnhancer:
    """Enriquece el contexto conversacional con información relevante"""

    def __init__(self):
        self.lookback_hours = getattr(settings, "CONTEXT_LOOKBACK_HOURS", 24)
        self.enable_proactive = getattr(settings, "ENABLE_PROACTIVE_SUGGESTIONS", True)
        logger.info(f"ContextEnhancer inicializado: lookback={self.lookback_hours}h, proactive={self.enable_proactive}")

    async def enhance_context(
        self,
        current_query: str,
        query_type: str,
        user_name: str,
        session: Session,
        data: Optional[Any] = None,
        temporal_context: Optional[str] = None,
        extracted_entities: Optional[List[QueryEntity]] = None
    ) -> ConversationContext:
        """
        Enriquece el contexto conversacional completo.

        Args:
            current_query: Query actual del usuario
            query_type: Tipo de query (horarios, examenes, etc)
            user_name: Nombre del usuario
            session: Sesión actual del usuario
            data: Datos disponibles para responder (opcional)
            temporal_context: Contexto temporal detectado (opcional)
            extracted_entities: Entidades extraídas de la query (opcional)

        Returns:
            ConversationContext completo y enriquecido
        """
        logger.info(f"🔄 Enriqueciendo contexto para query: '{current_query}'")

        # Extraer historial relevante
        recent_queries = self._extract_recent_queries(session)

        # Detectar estado emocional
        emotional_state = self._detect_emotional_state(
            query_type=query_type,
            data=data,
            session=session
        )

        # Generar sugerencias proactivas
        proactive_suggestions = []
        if self.enable_proactive:
            proactive_suggestions = self._generate_proactive_suggestions(
                query_type=query_type,
                data=data,
                session=session
            )

        # Crear contexto completo
        context = ConversationContext(
            current_query=current_query,
            query_type=query_type,
            extracted_entities=extracted_entities or [],
            emotional_state=emotional_state,
            recent_queries=recent_queries,
            has_conversation_history=len(recent_queries) > 0,
            proactive_suggestions=proactive_suggestions,
            user_name=user_name,
            temporal_context=temporal_context,
            enable_proactivity=self.enable_proactive
        )

        logger.info(f"✅ Contexto enriquecido: {len(recent_queries)} queries previas, {len(proactive_suggestions)} sugerencias")

        return context

    def _extract_recent_queries(self, session: Session) -> List[PreviousQuery]:
        """
        Extrae consultas recientes relevantes del historial.

        Args:
            session: Sesión del usuario

        Returns:
            Lista de PreviousQuery
        """
        recent_queries = []

        # Obtener timestamp límite (últimas X horas)
        cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)

        # Filtrar historial conversacional
        for msg in session.conversation_history:
            # Verificar si tiene timestamp
            if "timestamp" not in msg:
                continue

            msg_time = msg["timestamp"]
            if isinstance(msg_time, str):
                try:
                    msg_time = datetime.fromisoformat(msg_time)
                except:
                    continue

            # Filtrar por tiempo
            if msg_time < cutoff_time:
                continue

            # Solo mensajes del usuario
            if msg.get("role") != "user":
                continue

            # Crear PreviousQuery
            query_obj = PreviousQuery(
                query=msg.get("content", ""),
                query_type=msg.get("query_type", "unknown"),
                timestamp=msg_time,
                summary=msg.get("response_summary")
            )
            recent_queries.append(query_obj)

        logger.debug(f"  📊 Extraídas {len(recent_queries)} consultas recientes")
        return recent_queries

    def _detect_emotional_state(
        self,
        query_type: str,
        data: Optional[Any],
        session: Session
    ) -> EmotionalState:
        """
        Detecta el estado emocional del contexto.

        Args:
            query_type: Tipo de query
            data: Datos disponibles
            session: Sesión del usuario

        Returns:
            EmotionalState detectado
        """
        logger.debug(f"  🎭 Detectando estado emocional para {query_type}...")

        # Detectar contexto emocional según tipo de query
        legacy_context: Optional[LegacyEmotionalContext] = None

        if query_type == "horarios" and data:
            # Detectar contexto de horarios
            try:
                tiene_clases = getattr(data, "tiene_horarios", True)
                total_clases = len(getattr(data, "horarios", []))
                legacy_context = detect_schedule_context(tiene_clases, total_clases)
            except Exception as e:
                logger.warning(f"Error detectando contexto de horarios: {e}")

        elif query_type == "examenes" and data:
            # Detectar urgencia de exámenes
            try:
                # Buscar examen más cercano
                examenes = getattr(data, "examenes", [])
                if examenes:
                    # Calcular días hasta el primer examen
                    hoy = datetime.now().date()
                    primer_examen = examenes[0]
                    fecha_examen = getattr(primer_examen, "fecha", None)

                    if fecha_examen:
                        dias_hasta = (fecha_examen - hoy).days
                        legacy_context = detect_exam_urgency(dias_hasta)
            except Exception as e:
                logger.warning(f"Error detectando urgencia de exámenes: {e}")

        elif query_type == "creditos_vu" and data:
            # Detectar contexto de créditos
            try:
                creditos_obj = getattr(data, "creditos", None)
                if creditos_obj:
                    actuales = getattr(creditos_obj, "creditos_actuales", 0)
                    necesarios = getattr(creditos_obj, "creditos_necesarios", 10)
                    legacy_context = detect_credits_context(actuales, necesarios)
            except Exception as e:
                logger.warning(f"Error detectando contexto de créditos: {e}")

        # Convertir legacy context a EmotionalState
        if legacy_context:
            return self._convert_legacy_context(legacy_context)

        # Por defecto: estado neutral
        return EmotionalState(
            tone="neutral",
            urgency_level=0,
            celebration_worthy=False,
            empathy_needed=False
        )

    def _convert_legacy_context(
        self,
        legacy: LegacyEmotionalContext
    ) -> EmotionalState:
        """
        Convierte EmotionalContext legacy a EmotionalState nuevo.

        Args:
            legacy: Contexto emocional legacy

        Returns:
            EmotionalState nuevo
        """
        # Mapear tono
        tone = legacy.tone

        # Mapear urgencia
        urgency_map = {
            "urgente": 5,
            "animo": 3,
            "empatia": 2,
            "celebracion": 0,
            "tranquilo": 0,
            "neutral": 0
        }
        urgency_level = urgency_map.get(tone, 0)

        # Determinar celebration
        celebration_worthy = tone == "celebracion"

        # Determinar empathy
        empathy_needed = tone in ["empatia", "animo"]

        return EmotionalState(
            tone=tone,
            urgency_level=urgency_level,
            celebration_worthy=celebration_worthy,
            empathy_needed=empathy_needed,
            context_description=legacy.prefix or legacy.suffix
        )

    def _generate_proactive_suggestions(
        self,
        query_type: str,
        data: Optional[Any],
        session: Session
    ) -> List[ProactiveSuggestion]:
        """
        Genera sugerencias proactivas relevantes.

        Args:
            query_type: Tipo de query
            data: Datos disponibles
            session: Sesión del usuario

        Returns:
            Lista de ProactiveSuggestion
        """
        suggestions = []

        logger.debug(f"  💡 Generando sugerencias proactivas para {query_type}...")

        # Sugerencias por tipo de query
        if query_type == "horarios":
            # Sugerir exámenes cercanos si consulta horarios
            suggestions.extend(self._suggest_upcoming_exams(session, data))

        elif query_type == "examenes":
            # Sugerir ver ubicación de aula
            suggestions.extend(self._suggest_exam_location(data))

        elif query_type == "creditos_vu":
            # Sugerir actividades disponibles si está cerca del requisito
            suggestions.extend(self._suggest_vu_activities(data))

        logger.debug(f"  ✅ Generadas {len(suggestions)} sugerencias proactivas")
        return suggestions

    def _suggest_upcoming_exams(
        self,
        session: Session,
        horarios_data: Optional[Any]
    ) -> List[ProactiveSuggestion]:
        """Sugiere exámenes próximos cuando consulta horarios"""
        # TODO: Implementar cuando tengamos acceso a datos de exámenes
        # Por ahora retornar lista vacía
        return []

    def _suggest_exam_location(self, examenes_data: Optional[Any]) -> List[ProactiveSuggestion]:
        """Sugiere ver ubicación de aula cuando consulta examen"""
        suggestions = []

        try:
            if not examenes_data:
                return suggestions

            examenes = getattr(examenes_data, "examenes", [])
            if not examenes:
                return suggestions

            # Si hay examen próximo (en 3 días o menos)
            primer_examen = examenes[0]
            fecha_examen = getattr(primer_examen, "fecha", None)

            if fecha_examen:
                dias_hasta = (fecha_examen - datetime.now().date()).days

                if 0 <= dias_hasta <= 3:
                    # Sugerir ver aula
                    aula = getattr(primer_examen, "aula", None)
                    if aula:
                        suggestions.append(ProactiveSuggestion(
                            suggestion_type="reminder",
                            content=f"Tu examen es en el aula {aula}",
                            priority=3,
                            reason="Examen muy próximo"
                        ))
        except Exception as e:
            logger.warning(f"Error sugiriendo ubicación de examen: {e}")

        return suggestions

    def _suggest_vu_activities(self, creditos_data: Optional[Any]) -> List[ProactiveSuggestion]:
        """Sugiere actividades VU cuando está cerca del requisito"""
        suggestions = []

        try:
            if not creditos_data:
                return suggestions

            creditos_obj = getattr(creditos_data, "creditos", None)
            if not creditos_obj:
                return suggestions

            actuales = getattr(creditos_obj, "creditos_actuales", 0)
            necesarios = getattr(creditos_obj, "creditos_necesarios", 10)
            porcentaje = (actuales / necesarios) * 100

            # Si está entre 50% y 90%, sugerir actividades
            if 50 <= porcentaje < 90:
                faltantes = necesarios - actuales
                suggestions.append(ProactiveSuggestion(
                    suggestion_type="follow_up",
                    content=f"Te faltan {faltantes} créditos. ¿Querés ver actividades disponibles?",
                    priority=2,
                    reason="Progreso moderado en créditos VU"
                ))

        except Exception as e:
            logger.warning(f"Error sugiriendo actividades VU: {e}")

        return suggestions


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

# Crear instancia global
context_enhancer = ContextEnhancer()


# ============================================================
# HELPER FUNCTION
# ============================================================

async def enhance_conversation_context(
    current_query: str,
    query_type: str,
    user_name: str,
    session: Session,
    data: Optional[Any] = None,
    temporal_context: Optional[str] = None,
    extracted_entities: Optional[List[QueryEntity]] = None
) -> ConversationContext:
    """
    Función helper para enriquecer contexto fácilmente.

    Args:
        current_query: Query actual
        query_type: Tipo de query
        user_name: Nombre del usuario
        session: Sesión del usuario
        data: Datos disponibles (opcional)
        temporal_context: Contexto temporal (opcional)
        extracted_entities: Entidades extraídas (opcional)

    Returns:
        ConversationContext enriquecido

    Example:
        ```python
        context = await enhance_conversation_context(
            current_query="¿En qué aula tengo ética?",
            query_type="horarios",
            user_name="Juan",
            session=session,
            data=horarios_response
        )
        ```
    """
    return await context_enhancer.enhance_context(
        current_query=current_query,
        query_type=query_type,
        user_name=user_name,
        session=session,
        data=data,
        temporal_context=temporal_context,
        extracted_entities=extracted_entities
    )
