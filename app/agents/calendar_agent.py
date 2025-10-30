"""
Agente de calendario usando Pydantic Models para mejor tipado y formateo.
NUEVO: Integración con LLM Response Generator para respuestas naturales y contextuales.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from app.tools.calendar_tools import CalendarTools
from app.models import (
    ExamenesResponse,
    ExamenInfo,
    CalendarioAcademicoResponse,
    EventoCalendario,
    TipoExamen
)
from app.core import DIAS_SEMANA_ES, MESES_ES, EMOJIS
from app.core.llm_factory import llm_factory
from app.core.config import settings
from app.utils.logger import get_logger
from app.session.session_manager import session_manager

# NUEVO: Imports para LLM Response Generation
from app.utils.llm_response_generator import generate_natural_response, should_use_llm_generation
from app.utils.context_enhancer import enhance_conversation_context
from app.utils.response_strategy import build_response_strategy

logger = get_logger(__name__)


class CalendarAgent:
    """Agente de calendario modernizado con soporte Pydantic"""

    def __init__(self):
        self.tools = CalendarTools()

    def _fuzzy_match(self, word: str, keywords: list, threshold: float = 0.75) -> bool:
        """
        Verifica si una palabra coincide con alguna keyword usando fuzzy matching.

        Args:
            word: Palabra a verificar
            keywords: Lista de keywords a comparar
            threshold: Umbral de similitud (0.0 a 1.0, default 0.75)

        Returns:
            True si encuentra match con similitud >= threshold
        """
        word_clean = word.lower().strip()

        # Filtrar palabras muy cortas que pueden dar falsos positivos
        # Si la palabra tiene menos de 4 caracteres, requerir match exacto
        if len(word_clean) < 4:
            return word_clean in [kw.lower() for kw in keywords]

        # Para palabras de 4-5 caracteres, usar threshold más estricto
        # para evitar falsos positivos como "hola" ≈ "hora"
        effective_threshold = threshold
        if len(word_clean) <= 5:
            effective_threshold = 0.85  # Más estricto para palabras cortas

        for keyword in keywords:
            # Calcular similitud usando SequenceMatcher
            similarity = SequenceMatcher(None, word_clean, keyword.lower()).ratio()

            if similarity >= effective_threshold:
                logger.debug(f"  Fuzzy match: '{word}' ≈ '{keyword}' (sim: {similarity:.2f})")
                return True

        return False

    def _check_keywords_fuzzy(self, query: str, keywords: list, threshold: float = 0.75) -> bool:
        """
        Verifica si alguna palabra del query coincide con las keywords usando fuzzy matching.

        Args:
            query: Query del usuario
            keywords: Lista de keywords a buscar
            threshold: Umbral de similitud

        Returns:
            True si encuentra al menos un match
        """
        words = query.split()

        for word in words:
            if self._fuzzy_match(word, keywords, threshold):
                return True

        return False

    async def _classify_with_llm(self, query: str) -> str:
        """
        Usa LLM para clasificar la consulta cuando fuzzy matching no funciona.

        Args:
            query: Query del usuario

        Returns:
            Tipo de consulta: "examenes", "eventos", "feriados", "general"
        """
        try:
            llm = llm_factory.create(temperature=0.0)

            prompt = f"""Eres un clasificador de consultas sobre calendario académico.

Analiza la siguiente consulta y determina de qué tipo es.

CONSULTA DEL USUARIO:
"{query}"

TIPOS POSIBLES:
- examenes: Consultas sobre fechas de exámenes (parciales, finales, recuperatorios)
- eventos: Consultas sobre eventos del calendario académico
- feriados: Consultas sobre feriados o días sin clases
- general: Consulta ambigua o que no encaja en las anteriores

INSTRUCCIONES:
1. Ignora errores ortográficos
2. Considera sinónimos (ej: "prueba" = "examen", "descanso" = "feriado")
3. Responde con UNA SOLA PALABRA (el tipo)
4. Si no estás seguro, responde "general"

RESPUESTA (una palabra):"""

            response = await llm.ainvoke(prompt)
            classification = response.content.strip().lower()

            # Validar que la respuesta sea válida
            valid_types = ["examenes", "eventos", "feriados", "general"]
            if classification in valid_types:
                logger.info(f"🤖 LLM clasificó como: {classification}")
                return classification
            else:
                logger.warning(f"⚠️ LLM retornó tipo inválido: {classification}, usando 'general'")
                return "general"

        except Exception as e:
            logger.error(f"Error en clasificación con LLM: {e}")
            return "general"

    async def process_query(self, query: str, user_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Procesa una consulta sobre calendario y fechas"""
        try:
            # Normalizar query
            query_normalized = query.lower().strip()

            query_type = self._classify_calendar_query(query_normalized)

            # Si es "general", intentar con LLM antes de mostrar menú
            if query_type == "general":
                logger.info("🤖 Usando LLM fallback para clasificación...")
                query_type = await self._classify_with_llm(query)

                # Si el LLM también dice "general", entonces realmente es ambiguo
                if query_type == "general":
                    logger.info("✅ Confirmado como consulta general (ambigua)")
                else:
                    logger.info(f"✅ LLM reclasificó como: {query_type}")

            logger.info(f"Consulta de calendario clasificada como: {query_type}")

            if query_type == "examenes":
                return await self._handle_exams(query, user_info)
            elif query_type == "eventos":
                return await self._handle_events(query, user_info)
            elif query_type == "feriados":
                return await self._handle_holidays(user_info)
            else:
                return await self._handle_general_calendar(user_info)

        except Exception as e:
            logger.error(f"Error en agente de calendario: {e}", exc_info=True)
            return self._get_error_response(user_info)

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto quitando acentos y convirtiendo a minúsculas"""
        import unicodedata
        nfkd = unicodedata.normalize('NFD', text)
        without_accents = ''.join([c for c in nfkd if not unicodedata.combining(c)])
        return without_accents.lower()

    def _classify_calendar_query(self, query: str) -> str:
        """
        Clasifica el tipo de consulta de calendario con tolerancia a typos.

        Estrategia de tres niveles:
        1. Match exacto con keywords (más rápido)
        2. Fuzzy matching para typos (tolerante)
        3. LLM fallback en process_query si es "general"

        Args:
            query: Query normalizado (lowercase)

        Returns:
            Tipo de consulta
        """
        # Definir keywords por categoría
        examenes_kw = [
            "examen", "examenes", "parcial", "parciales",
            "final", "finales", "recuperatorio", "evaluacion", "prueba"
        ]

        feriados_kw = [
            "feriado", "feriados", "no hay clases", "descanso", "receso"
        ]

        eventos_kw = [
            "evento", "calendario", "fecha", "cuando", "cuándo"
        ]

        # NIVEL 1: Match exacto (más rápido)
        if any(kw in query for kw in examenes_kw):
            logger.debug("✅ Match exacto: examenes")
            return "examenes"

        if any(kw in query for kw in feriados_kw):
            logger.debug("✅ Match exacto: feriados")
            return "feriados"

        if any(kw in query for kw in eventos_kw):
            logger.debug("✅ Match exacto: eventos")
            return "eventos"

        # NIVEL 2: Fuzzy matching (tolerante a typos)
        logger.debug("🔍 No hubo match exacto, intentando fuzzy matching...")

        if self._check_keywords_fuzzy(query, examenes_kw, threshold=0.75):
            logger.debug("✅ Fuzzy match: examenes")
            return "examenes"

        if self._check_keywords_fuzzy(query, feriados_kw, threshold=0.75):
            logger.debug("✅ Fuzzy match: feriados")
            return "feriados"

        if self._check_keywords_fuzzy(query, eventos_kw, threshold=0.75):
            logger.debug("✅ Fuzzy match: eventos")
            return "eventos"

        # NIVEL 3: Retornar "general" (se usará LLM en process_query)
        logger.debug("❓ No hubo fuzzy match, marcando como 'general' para LLM fallback")
        return "general"

    async def _handle_exams(self, query: str, user_info: Dict[str, Any]) -> str:
        """
        Maneja consultas sobre exámenes usando ExamenesResponse.

        NUEVO: Integra LLM Response Generator para respuestas naturales y contextuales.
        """
        try:
            params = {
                "alumno_id": user_info["id"],
                "query": query  # NUEVO: pasar query original para parseo temporal
            }

            # Detectar materia específica
            materia = self._extract_subject_from_query(query)
            if materia:
                params["materia_nombre"] = materia

            # Detectar tipo de examen
            tipo = self._extract_exam_type(query)
            if tipo:
                params["tipo_examen"] = tipo

            # NOTA: Las fechas ahora se parsean automáticamente en CalendarTools
            # usando temporal_parser, pero mantenemos el método legacy como fallback
            if not any(kw in query.lower() for kw in ['hoy', 'mañana', 'semana', 'mes', 'día', 'próximo']):
                # Solo usar método legacy si no hay expresiones temporales
                fecha_desde, fecha_hasta = self._extract_month_from_query(query)
                if fecha_desde:
                    params["fecha_desde"] = fecha_desde
                if fecha_hasta:
                    params["fecha_hasta"] = fecha_hasta

            result_dict = await self.tools.consultar_examenes(params)

            if result_dict and result_dict.get("examenes"):
                # Convertir a modelo Pydantic
                response = ExamenesResponse(**result_dict)

                # ===== NUEVO: LLM RESPONSE GENERATION =====
                # Verificar si usar LLM generation
                if should_use_llm_generation():
                    logger.info("🤖 Usando LLM Response Generator para exámenes")

                    # Obtener sesión actual
                    session_id = user_info.get("session_id", "unknown")
                    session = session_manager.get_session(session_id)

                    # Detectar contexto temporal
                    solo_proximo = len(response.examenes) == 1 and 'próximo' in query.lower()
                    contexto_temporal = "próximo examen" if solo_proximo else None

                    # Enriquecer contexto conversacional
                    context = await enhance_conversation_context(
                        current_query=query,
                        query_type="examenes",
                        user_name=user_info["nombre"],
                        session=session,
                        data=response,
                        temporal_context=contexto_temporal
                    )

                    # Construir estrategia de respuesta
                    strategy, entities = build_response_strategy(
                        query=query,
                        data=response,
                        context=context
                    )

                    # Generar respuesta natural con LLM
                    natural_response = await generate_natural_response(
                        data=response,
                        original_query=query,
                        user_name=user_info["nombre"],
                        query_type="examenes",
                        agent_type="calendar",
                        context=context,
                        strategy=strategy
                    )

                    # Actualizar contexto en sesión para referencias futuras
                    session.update_query_context(
                        query=query,
                        query_type="examenes",
                        query_data={"materia": materia, "tipo": tipo},
                        response_summary=natural_response[:100]  # Guardar primeras 100 chars
                    )

                    return natural_response

                # ===== LEGACY: Template-based response (fallback) =====
                else:
                    logger.info("📋 Usando template-based response (legacy mode)")
                    solo_proximo = len(response.examenes) == 1 and 'próximo' in query.lower()
                    return self._format_exams_response(response, user_info["nombre"], solo_proximo=solo_proximo)

            else:
                materia_text = f" de {materia}" if materia else ""
                return f"{EMOJIS['examen']} ¡Hola {user_info['nombre']}!\n\n{EMOJIS['info']} No encontré exámenes{materia_text} para las fechas solicitadas.\n\n¿Necesitás información sobre otra fecha o materia? {EMOJIS['ayuda']}"

        except Exception as e:
            logger.error(f"Error consultando exámenes: {e}", exc_info=True)
            return self._get_error_response(user_info)

    async def _handle_events(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre eventos usando CalendarioAcademicoResponse"""
        try:
            params = {}

            # Detectar tipo de evento
            tipo_evento = self._extract_event_type(query)
            if tipo_evento:
                params["tipo_evento"] = tipo_evento

            # Detectar mes específico
            fecha_desde, fecha_hasta = self._extract_month_from_query(query)
            if fecha_desde:
                params["fecha_desde"] = fecha_desde
            if fecha_hasta:
                params["fecha_hasta"] = fecha_hasta

            result_dict = await self.tools.calendario_academico(params)

            if result_dict and result_dict.get("eventos"):
                # Convertir a modelo Pydantic
                response = CalendarioAcademicoResponse(**result_dict)
                return self._format_events_response(response, user_info["nombre"])
            else:
                return f"{EMOJIS['calendario']} ¡Hola {user_info['nombre']}!\n\n{EMOJIS['info']} No encontré eventos para las fechas solicitadas.\n\n¿Querés ver el calendario completo? {EMOJIS['ayuda']}"

        except Exception as e:
            logger.error(f"Error consultando eventos: {e}", exc_info=True)
            return self._get_error_response(user_info)

    async def _handle_holidays(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre feriados"""
        try:
            # Buscar eventos tipo feriado
            params = {"tipo_evento": "feriado"}

            result_dict = await self.tools.calendario_academico(params)

            if result_dict and result_dict.get("eventos"):
                response = CalendarioAcademicoResponse(**result_dict)
                return self._format_holidays_response(response, user_info["nombre"])
            else:
                return f"{EMOJIS['feriado']} ¡Hola {user_info['nombre']}!\n\n{EMOJIS['info']} No encontré información de feriados disponible.\n\n¿Te puedo ayudar con algo más? {EMOJIS['ayuda']}"

        except Exception as e:
            logger.error(f"Error consultando feriados: {e}", exc_info=True)
            return self._get_error_response(user_info)

    async def _handle_general_calendar(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas generales sobre calendario"""
        return f"""{EMOJIS['calendario']} ¡Hola {user_info['nombre']}!

¿En qué te puedo ayudar con fechas y calendario?

Puedo ayudarte con:
{EMOJIS['examen']} **Fechas de exámenes** (parciales y finales)
{EMOJIS['calendario']} **Calendario académico** y eventos importantes
{EMOJIS['feriado']} **Feriados** y días sin clases
{EMOJIS['evento']} **Eventos institucionales**

¿Qué necesitás saber? {EMOJIS['ayuda']}"""

    # =====================================================
    # HELPERS
    # =====================================================

    def _extract_subject_from_query(self, query: str) -> Optional[str]:
        """Extrae el nombre de la materia de la consulta"""
        query_norm = self._normalize_text(query)

        materias = {
            "nativa": "Nativa Digital",
            "programacion": "Programación I",
            "matematica": "Matemática Discreta",
        }

        for keyword, materia_nombre in materias.items():
            if keyword in query_norm:
                return materia_nombre

        return None

    def _extract_exam_type(self, query: str) -> Optional[str]:
        """Extrae el tipo de examen de la consulta"""
        query_norm = self._normalize_text(query)

        if "final" in query_norm:
            return "final"
        elif "parcial" in query_norm:
            return "parcial"
        elif "recuperatorio" in query_norm:
            return "recuperatorio"

        return None

    def _extract_event_type(self, query: str) -> Optional[str]:
        """Extrae el tipo de evento de la consulta"""
        query_norm = self._normalize_text(query)

        if any(word in query_norm for word in ["inicio", "empiezan", "comienzan"]):
            return "inicio_clases"
        elif any(word in query_norm for word in ["inscripcion", "inscripciones"]):
            return "inscripciones"

        return None

    def _extract_month_from_query(self, query: str) -> tuple:
        """Extrae mes de la consulta y devuelve rango de fechas"""
        query_norm = self._normalize_text(query)

        meses = {
            'enero': ('2025-01-01', '2025-01-31'),
            'febrero': ('2025-02-01', '2025-02-28'),
            'marzo': ('2025-03-01', '2025-03-31'),
            'abril': ('2025-04-01', '2025-04-30'),
            'mayo': ('2025-05-01', '2025-05-31'),
            'junio': ('2025-06-01', '2025-06-30'),
            'julio': ('2025-07-01', '2025-07-31'),
            'agosto': ('2025-08-01', '2025-08-31'),
            'septiembre': ('2025-09-01', '2025-09-30'),
            'setiembre': ('2025-09-01', '2025-09-30'),
            'octubre': ('2025-10-01', '2025-10-31'),
            'noviembre': ('2025-11-01', '2025-11-30'),
            'diciembre': ('2025-12-01', '2025-12-31'),
        }

        for mes, (inicio, fin) in meses.items():
            if mes in query_norm:
                return inicio, fin

        return None, None

    # =====================================================
    # FORMATTERS CON PYDANTIC
    # =====================================================

    def _format_exams_response(self, response: ExamenesResponse, nombre: str, solo_proximo: bool = False) -> str:
        """Formatea la respuesta de exámenes usando ExamenesResponse"""
        if not response.tiene_examenes:
            return f"{EMOJIS['examen']} ¡Hola {nombre}!\n\n{EMOJIS['info']} No tenés exámenes programados en los próximos días.\n\n¿Necesitás información sobre alguna fecha específica? {EMOJIS['ayuda']}"

        output = f"{EMOJIS['examen']} ¡Hola {nombre}!\n\n"

        # Personalizar título según contexto
        if solo_proximo:
            output += f"{EMOJIS['calendario']} **Tu próximo examen:**\n\n"
        else:
            output += f"{EMOJIS['calendario']} **Tus próximos exámenes:** ({response.total} en total)\n\n"

        # Si es solo próximo, mostrar directamente sin secciones
        if solo_proximo:
            for examen in response.examenes:
                output += self._format_single_exam(examen)
                output += "\n"
        else:
            # Resaltar exámenes próximos si hay
            proximos = response.examenes_proximos
            if proximos:
                output += f"{EMOJIS['advertencia']} **¡Exámenes próximos! (7 días)**\n\n"
                for examen in proximos:
                    output += self._format_single_exam(examen)
                    output += "\n"

            # Mostrar resto de exámenes
            otros = [e for e in response.examenes if not e.es_proximo]
            if otros:
                output += f"{EMOJIS['calendario']} **Otros exámenes:**\n\n"
                for examen in otros:
                    output += self._format_single_exam(examen)
                    output += "\n"

        # Mostrar resumen por tipo solo si NO es "solo próximo"
        if not solo_proximo:
            tipos_count = {tipo: len(exams) for tipo, exams in response.examenes_por_tipo.items()}
            if len(tipos_count) > 1:
                output += "\n📊 **Resumen:**\n"
                for tipo, count in tipos_count.items():
                    # tipo ya es string por use_enum_values=True
                    tipo_name = tipo.capitalize() if isinstance(tipo, str) else tipo.value.capitalize()
                    output += f"• {count} {tipo_name}(es)\n"

        output += f"\n¿Necesitás información sobre algún examen específico? {EMOJIS['ayuda']}"
        return output

    def _format_single_exam(self, examen: ExamenInfo) -> str:
        """Formatea un solo examen usando ExamenInfo y sus properties"""
        # Usar property emoji del modelo
        output = f"{examen.emoji} **{examen.materia}** - {examen.nombre}\n"
        output += f"   {EMOJIS['calendario']} Fecha: {examen.fecha.strftime('%d/%m/%Y')}\n"
        output += f"   ⏰ Horario: {examen.hora_inicio} a {examen.hora_fin}\n"
        output += f"   {EMOJIS['aula']} Aula: {examen.aula}\n"
        # modalidad ya es string por use_enum_values=True
        modalidad_text = examen.modalidad.capitalize() if isinstance(examen.modalidad, str) else examen.modalidad.value.capitalize()
        output += f"   🔵 Modalidad: {modalidad_text}\n"

        # Usar property dias_hasta_examen
        if examen.dias_hasta_examen >= 0:
            if examen.dias_hasta_examen == 0:
                output += f"   {EMOJIS['advertencia']} **¡HOY!**\n"
            elif examen.dias_hasta_examen == 1:
                output += f"   {EMOJIS['advertencia']} **¡MAÑANA!**\n"
            else:
                output += f"   ⏳ En {examen.dias_hasta_examen} días\n"

        if examen.observaciones:
            output += f"   📌 {examen.observaciones}\n"

        return output

    def _format_events_response(self, response: CalendarioAcademicoResponse, nombre: str) -> str:
        """Formatea la respuesta de eventos usando CalendarioAcademicoResponse"""
        if not response.tiene_eventos:
            return f"{EMOJIS['calendario']} ¡Hola {nombre}!\n\n{EMOJIS['info']} No encontré eventos en el calendario.\n\n¿Querés buscar por fechas específicas? {EMOJIS['ayuda']}"

        output = f"{EMOJIS['calendario']} ¡Hola {nombre}!\n\n"

        # Usar property eventos_proximos
        proximos = response.eventos_proximos
        if proximos:
            output += f"{EMOJIS['advertencia']} **Próximos eventos importantes:**\n\n"
            for evento in proximos:
                output += self._format_single_event(evento)
                output += "\n"

        # Resto de eventos
        otros = [e for e in response.eventos if not e.es_proximo]
        if otros:
            output += f"{EMOJIS['calendario']} **Calendario general:**\n\n"
            for evento in otros:
                output += self._format_single_event(evento)
                output += "\n"

        output += f"¿Necesitás información sobre algún evento específico? {EMOJIS['ayuda']}"
        return output

    def _format_single_event(self, evento: EventoCalendario) -> str:
        """Formatea un solo evento usando EventoCalendario"""
        output = f"{EMOJIS['evento']} **{evento.titulo}**\n"

        if evento.fecha:
            output += f"   {EMOJIS['calendario']} Fecha: {evento.fecha.strftime('%d/%m/%Y')}\n"

            # Usar property dias_hasta_evento
            dias = evento.dias_hasta_evento
            if dias is not None:
                if dias == 0:
                    output += f"   {EMOJIS['advertencia']} **¡HOY!**\n"
                elif dias == 1:
                    output += f"   {EMOJIS['advertencia']} **¡MAÑANA!**\n"
                elif dias > 0 and dias <= 14:
                    output += f"   ⏳ En {dias} días\n"

        if evento.descripcion:
            # Truncar si es muy largo
            desc = evento.descripcion[:100] + "..." if len(evento.descripcion) > 100 else evento.descripcion
            output += f"   📝 {desc}\n"

        return output

    def _format_holidays_response(self, response: CalendarioAcademicoResponse, nombre: str) -> str:
        """Formatea la respuesta de feriados"""
        if not response.tiene_eventos:
            return f"{EMOJIS['feriado']} ¡Hola {nombre}!\n\n{EMOJIS['info']} No encontré información de feriados.\n\n¿Te puedo ayudar con algo más? {EMOJIS['ayuda']}"

        output = f"{EMOJIS['feriado']} ¡Hola {nombre}!\n\n"
        output += f"{EMOJIS['calendario']} **Feriados y días sin clases:**\n\n"

        # Usar eventos_proximos para resaltar próximos feriados
        proximos = response.eventos_proximos
        if proximos:
            output += f"{EMOJIS['advertencia']} **Próximos feriados:**\n\n"
            for feriado in proximos:
                output += f"{EMOJIS['feriado']} **{feriado.titulo}**\n"
                if feriado.fecha:
                    output += f"   📅 {feriado.fecha.strftime('%d/%m/%Y')}\n"
                    dias = feriado.dias_hasta_evento
                    if dias is not None and dias >= 0:
                        output += f"   ⏳ En {dias} días\n"
                output += "\n"

        # Resto de feriados
        otros = [e for e in response.eventos if not e.es_proximo]
        if otros:
            output += f"{EMOJIS['calendario']} **Otros feriados:**\n\n"
            for feriado in otros:
                output += f"{EMOJIS['feriado']} **{feriado.titulo}**"
                if feriado.fecha:
                    output += f" - {feriado.fecha.strftime('%d/%m/%Y')}"
                output += "\n"

        output += f"\n¿Necesitás información sobre alguna fecha específica? {EMOJIS['ayuda']}"
        return output

    def _get_error_response(self, user_info: Dict[str, Any]) -> str:
        """Respuesta de error personalizada"""
        return f"""{EMOJIS['error']} ¡Hola {user_info['nombre']}!

Hubo un problemita técnico y no pude procesar tu consulta sobre fechas y calendario.

Por favor intentá de nuevo en unos minutos, o si es urgente podés contactar directamente a la secretaría académica.

¿Te puedo ayudar con algo más mientras tanto? {EMOJIS['ayuda']}"""
