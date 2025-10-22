"""
Sistema híbrido de clasificación de queries
Combina keywords determinísticas con LLM para casos ambiguos
"""
from typing import Optional, Tuple, Dict, List
from app.utils.logger import get_logger
from app.utils.greeting_detector import greeting_detector
import re

logger = get_logger(__name__)


class QueryClassifier:
    """
    Clasificador híbrido de queries universitarias.
    
    Estrategia de dos niveles:
    1. Pre-filtro con keywords (rápido, determinista)
    2. LLM para casos ambiguos (lento, inteligente)
    """
    
    def __init__(self):
        # Definir keywords por agente con pesos
        self.keywords = {
            "calendar": {
                # Keywords de alta prioridad (peso 3)
                "high": [
                    "parcial", "final", "examen", "recuperatorio", "parciales", "finales", "examenes",
                    "fecha de examen", "cuando es el", "calendario de examenes",
                    "proximo parcial", "proximo final", "siguiente examen", "tengo un parcial",
                    "tengo un final", "tengo examen"
                ],
                # Keywords de media prioridad (peso 2)
                "medium": [
                    "calendario", "evento", "feriado", "inscripcion",
                    "inicio de clases", "fin de cuatrimestre",
                    "esta semana", "semana que viene", "este mes", "mes que viene"
                ],
                # Keywords de baja prioridad (peso 1)
                "low": [
                    "cuando", "fecha", "dia", "hoy", "mañana", "manana",
                    "pasado mañana", "pasado manana", "proximo", "siguiente"
                ]
            },
            "academic": {
                "high": [
                    "horario", "clase", "aula", "salon", "profesor",
                    "docente", "comision", "cursada", "inscripto",
                    "creditos vu", "credito", "materia", "materias"
                ],
                "medium": [
                    "curso", "catedra", "dictado", "turno",
                    "presencial", "virtual", "zoom", "quiero saber",
                    "ver mi", "mi horario"
                ],
                "low": [
                    "tengo", "estoy", "voy", "ir", "asistir", "saber"
                ]
            },
            "financial": {
                "high": [
                    "pago", "deuda", "debo", "cuota", "vencimiento",
                    "factura", "arancel", "cobro", "cuenta", "cuanto debo",
                    "tengo deudas", "tengo deuda"
                ],
                "medium": [
                    "precio", "costo", "monto", "saldo", "adeudo"
                ],
                "low": [
                    "dinero", "plata", "pagar", "dolar", "peso", "cuanto"
                ]
            },
            "policies": {
                "high": [
                    "reglamento", "normativa", "politica", "syllabus",
                    "programa", "bibliografia", "contenido", "temas"
                ],
                "medium": [
                    "requisito", "condicion", "regla", "criterio",
                    "evaluacion", "aprobacion", "regularidad"
                ],
                "low": [
                    "como se", "que pide", "necesito", "debo cumplir"
                ]
            }
        }
        
        # Patrones de contexto temporal para disambiguación
        self.temporal_patterns = {
            "calendar": [
                r"cuando (es|sera|tengo|hay).*(parcial|final|examen)",
                r"(fecha|dia).*(parcial|final|examen|evaluacion)",
                r"(calendario|cronograma).*(examen|evaluacion)",
                r"(proximo|siguiente|esta semana|mes que viene).*(parcial|final)",
                r"(hoy|ma[ñn]ana|pasado ma[ñn]ana).*(parcial|final|examen)",
                r"(esta|la) semana.*(parcial|final|examen)",
                r"(este|el) mes.*(parcial|final|examen)",
                r"en \d+ d[ií]as?.*(parcial|final|examen)",
                r"(cual|cuál) es (mi|el) (proximo|próximo|siguiente).*(parcial|final|examen)"
            ],
            "academic": [
                r"cuando (tengo|es|hay).*(clase|cursada)",
                r"(horario|hora).*(clase|materia|cursada)",
                r"(donde|que aula|salon).*(clase|cursada)",
                r"(hoy|ma[ñn]ana|pasado ma[ñn]ana).*(clase|cursada)",
                r"(esta|la) semana.*(clase|cursada)"
            ]
        }
    
    def classify(self, query: str) -> Tuple[Optional[str], float, str]:
        """
        Clasifica una query en un agente.

        Args:
            query: Texto de la consulta del usuario

        Returns:
            Tuple de (agente, confianza, método)
            - agente: "academic", "calendar", "financial", "policies", "greeting", None
            - confianza: 0.0 a 1.0
            - método: "keywords", "pattern", "greeting", "ambiguous"
        """
        query_lower = query.lower().strip()

        # PASO 0: Detectar saludos puros (sin consulta adicional)
        if greeting_detector.is_greeting(query) and not greeting_detector.has_content_beyond_greeting(query):
            logger.info(f"👋 Clasificación: greeting puro (sin consulta adicional)")
            return "greeting", 0.98, "greeting"

        # PASO 0.5: Si hay saludo + contenido, remover el saludo y clasificar el contenido
        if greeting_detector.is_greeting(query) and greeting_detector.has_content_beyond_greeting(query):
            # Remover el saludo para clasificar solo el contenido real
            query_without_greeting = greeting_detector.remove_greeting_from_message(query)
            query_lower = query_without_greeting.lower().strip()
            logger.info(f"🔄 Saludo removido. Clasificando contenido: '{query_lower[:50]}...'")

        # PASO 1: Buscar patrones temporales específicos
        pattern_result = self._match_temporal_patterns(query_lower)
        if pattern_result:
            agent, confidence = pattern_result
            logger.info(f"🎯 Clasificación por patrón: {agent} (conf: {confidence})")
            return agent, confidence, "pattern"
        
        # PASO 2: Calcular scores por keywords
        scores = self._calculate_keyword_scores(query_lower)
        
        # PASO 3: Determinar si hay un ganador claro
        if scores:
            max_agent = max(scores, key=scores.get)
            max_score = scores[max_agent]
            
            # Normalizar score (máximo teórico es ~10)
            confidence = min(max_score / 10.0, 1.0)
            
            # Si la confianza es alta (>0.6), usar keywords
            if confidence > 0.6:
                logger.info(f"✅ Clasificación por keywords: {max_agent} (conf: {confidence:.2f})")
                return max_agent, confidence, "keywords"
            
            # Si hay un segundo lugar muy cercano, es ambiguo
            sorted_scores = sorted(scores.values(), reverse=True)
            if len(sorted_scores) >= 2:
                diff = sorted_scores[0] - sorted_scores[1]
                if diff < 2:  # Muy cercanos
                    logger.info(f"⚠️ Query ambigua: {max_agent} vs otros (diff: {diff})")
                    return None, confidence, "ambiguous"
            
            # Confianza media-baja pero hay un ganador
            if confidence > 0.3:
                logger.info(f"⚡ Clasificación tentativa: {max_agent} (conf: {confidence:.2f})")
                return max_agent, confidence, "keywords"
        
        # PASO 4: No se pudo clasificar con keywords
        logger.info("❓ Query requiere LLM para clasificación")
        return None, 0.0, "ambiguous"
    
    def _match_temporal_patterns(self, query: str) -> Optional[Tuple[str, float]]:
        """Busca patrones temporales específicos"""
        for agent, patterns in self.temporal_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return agent, 0.95  # Alta confianza
        return None
    
    def _calculate_keyword_scores(self, query: str) -> Dict[str, float]:
        """Calcula scores de keywords por agente"""
        scores = {}
        
        for agent, priority_keywords in self.keywords.items():
            score = 0.0
            
            # High priority keywords (peso 3)
            for kw in priority_keywords["high"]:
                if kw in query:
                    score += 3.0
                    logger.debug(f"  +3.0 para {agent}: '{kw}'")
            
            # Medium priority keywords (peso 2)
            for kw in priority_keywords["medium"]:
                if kw in query:
                    score += 2.0
                    logger.debug(f"  +2.0 para {agent}: '{kw}'")
            
            # Low priority keywords (peso 1)
            for kw in priority_keywords["low"]:
                if kw in query:
                    score += 1.0
                    logger.debug(f"  +1.0 para {agent}: '{kw}'")
            
            if score > 0:
                scores[agent] = score
        
        return scores
    
    def get_classification_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de clasificación (para monitoring)"""
        # Placeholder para futuras métricas
        return {
            "keywords_total": 0,
            "pattern_total": 0,
            "llm_total": 0,
            "ambiguous_total": 0
        }


# Instancia global del clasificador
query_classifier = QueryClassifier()
