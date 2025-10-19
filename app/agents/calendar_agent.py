"""
Agente de calendario usando Pydantic Models para mejor tipado y formateo
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.tools.calendar_tools import CalendarTools
from app.models import (
    ExamenesResponse,
    ExamenInfo,
    CalendarioAcademicoResponse,
    EventoCalendario,
    TipoExamen
)
from app.core import DIAS_SEMANA_ES, MESES_ES, EMOJIS
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CalendarAgent:
    """Agente de calendario modernizado con soporte Pydantic"""

    def __init__(self):
        self.tools = CalendarTools()

    async def process_query(self, query: str, user_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Procesa una consulta sobre calendario y fechas"""
        try:
            # Normalizar query
            query_normalized = query.lower().strip()

            query_type = self._classify_calendar_query(query_normalized)
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
        """Clasifica el tipo de consulta de calendario"""
        query_norm = self._normalize_text(query)

        # Verificar exámenes PRIMERO
        if any(word in query_norm for word in ["examen", "examenes", "parcial", "final", "recuperatorio", "prueba"]):
            return "examenes"
        elif any(word in query_norm for word in ["feriado", "feriados", "no hay clases"]):
            return "feriados"
        elif any(word in query_norm for word in ["evento", "calendario", "fecha"]):
            return "eventos"
        else:
            return "general"

    async def _handle_exams(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre exámenes usando ExamenesResponse"""
        try:
            params = {"alumno_id": user_info["id"]}

            # Detectar materia específica
            materia = self._extract_subject_from_query(query)
            if materia:
                params["materia_nombre"] = materia

            # Detectar mes específico
            fecha_desde, fecha_hasta = self._extract_month_from_query(query)
            if fecha_desde:
                params["fecha_desde"] = fecha_desde
            if fecha_hasta:
                params["fecha_hasta"] = fecha_hasta

            # Detectar tipo de examen
            tipo = self._extract_exam_type(query)
            if tipo:
                params["tipo_examen"] = tipo

            result_dict = await self.tools.consultar_examenes(params)

            if result_dict and result_dict.get("examenes"):
                # Convertir a modelo Pydantic
                response = ExamenesResponse(**result_dict)
                return self._format_exams_response(response, user_info["nombre"])
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

    def _format_exams_response(self, response: ExamenesResponse, nombre: str) -> str:
        """Formatea la respuesta de exámenes usando ExamenesResponse"""
        if not response.tiene_examenes:
            return f"{EMOJIS['examen']} ¡Hola {nombre}!\n\n{EMOJIS['info']} No tenés exámenes programados en los próximos días.\n\n¿Necesitás información sobre alguna fecha específica? {EMOJIS['ayuda']}"

        output = f"{EMOJIS['examen']} ¡Hola {nombre}!\n\n"
        output += f"{EMOJIS['calendario']} **Tus próximos exámenes:** ({response.total} en total)\n\n"

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

        # Mostrar resumen por tipo usando property examenes_por_tipo
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
