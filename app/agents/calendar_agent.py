from typing import Dict, Any, Optional
from app.tools.calendar_tools import CalendarTools
from app.utils.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

class CalendarAgent:
    """Agente de calendario modernizado"""

    def __init__(self):
        self.tools = CalendarTools()

    async def process_query(self, query: str, user_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Procesa una consulta sobre calendario y fechas"""
        try:
            query_type = self._classify_calendar_query(query.lower())
            logger.info(f"Consulta de calendario clasificada como: {query_type}")

            if query_type == "examenes":
                return await self._handle_exams(query, user_info)
            elif query_type == "eventos":
                return await self._handle_events(query, user_info)
            elif query_type == "feriados":
                return await self._handle_holidays(user_info)
            elif query_type == "inscripciones":
                return await self._handle_enrollments(user_info)
            else:
                return await self._handle_general_calendar(user_info)

        except Exception as e:
            logger.error(f"Error en agente de calendario: {e}")
            return self._get_error_response(user_info)

    def _classify_calendar_query(self, query: str) -> str:
        """Clasifica el tipo de consulta de calendario"""
        # IMPORTANTE: Verificar exámenes PRIMERO antes de palabras genéricas
        if any(word in query for word in ["examen", "parcial", "final", "recuperatorio", "prueba"]):
            return "examenes"
        elif any(word in query for word in ["feriado", "feriados", "no hay clases"]):
            return "feriados"
        elif any(word in query for word in ["inscripcion", "inscripciones", "cuando inscribir"]):
            return "inscripciones"
        # Palabras genéricas al final para no interferir con lo anterior
        elif any(word in query for word in ["evento", "calendario", "fecha"]):
            return "eventos"
        else:
            return "general"

    async def _handle_exams(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre exámenes"""
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

            result = await self.tools.consultar_examenes(params)

            if result and result.get("examenes"):
                return self._format_exams_response(result, user_info["nombre"])
            else:
                return f"¡Hola {user_info['nombre']}! 📝\n\n📅 No encontré exámenes{' de ' + materia if materia else ''} para las fechas solicitadas.\n\n¿Necesitás información sobre otra fecha o materia? 😊"

        except Exception as e:
            logger.error(f"Error consultando exámenes: {e}")
            return self._get_error_response(user_info)

    async def _handle_events(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre eventos del calendario académico"""
        try:
            params = {}

            # Detectar tipo de evento
            tipo_evento = self._extract_event_type(query)
            if tipo_evento:
                params["tipo_evento"] = tipo_evento

            # Detectar rango de fechas
            fecha_inicio, fecha_fin = self._extract_date_range(query)
            if fecha_inicio:
                params["fecha_inicio"] = fecha_inicio
            if fecha_fin:
                params["fecha_fin"] = fecha_fin

            result = await self.tools.calendario_academico(params)

            if result:
                return self._format_events_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return self._get_mock_events_response(user_info["nombre"])

        except Exception as e:
            logger.error(f"Error consultando eventos: {e}")
            return self._get_error_response(user_info)

    async def _handle_holidays(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre feriados"""
        try:
            current_year = datetime.now().year
            params = {"año": current_year}

            result = await self.tools.consultar_feriados(params)

            if result:
                return self._format_holidays_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return self._get_mock_holidays_response(user_info["nombre"])

        except Exception as e:
            logger.error(f"Error consultando feriados: {e}")
            return self._get_error_response(user_info)

    async def _handle_enrollments(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre fechas de inscripciones"""
        try:
            params = {}
            result = await self.tools.inscripciones_fechas(params)

            if result:
                return self._format_enrollments_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return self._get_mock_enrollments_response(user_info["nombre"])

        except Exception as e:
            logger.error(f"Error consultando inscripciones: {e}")
            return self._get_error_response(user_info)

    async def _handle_general_calendar(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas generales sobre calendario"""
        return f"""¡Hola {user_info['nombre']}! 📅

¿En qué te puedo ayudar con fechas y calendario?

Puedo ayudarte con:
• 📝 **Fechas de exámenes** (parciales y finales)
• 📋 **Calendario académico** y eventos importantes
• 🏖️ **Feriados** y días sin clases
• 📊 **Fechas de inscripciones** a materias y exámenes

¿Qué necesitás saber? 😊"""

    def _extract_subject_from_query(self, query: str) -> Optional[str]:
        """Extrae el nombre de la materia de la consulta"""
        query_lower = query.lower()

        if "nativa" in query_lower:
            return "Nativa Digital"
        elif "programación" in query_lower or "programacion" in query_lower:
            return "Programación I"
        elif "matemática" in query_lower or "matematica" in query_lower:
            return "Matemática Discreta"

        return None

    def _extract_exam_type(self, query: str) -> Optional[str]:
        """Extrae el tipo de examen de la consulta"""
        query_lower = query.lower()

        if "final" in query_lower:
            return "final"
        elif "parcial" in query_lower:
            return "parcial"
        elif "recuperatorio" in query_lower:
            return "recuperatorio"

        return None

    def _extract_event_type(self, query: str) -> Optional[str]:
        """Extrae el tipo de evento de la consulta"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["inicio", "empiezan", "comienzan"]):
            return "inicio_clases"
        elif any(word in query_lower for word in ["final", "finales"]):
            return "finales"
        elif any(word in query_lower for word in ["inscripcion", "inscripciones"]):
            return "inscripciones"

        return None

    def _extract_date_range(self, query: str) -> tuple:
        """Extrae rango de fechas de la consulta"""
        # Por simplicidad, retornamos None por ahora
        # En una implementación completa, usaríamos NLP para extraer fechas
        return None, None

    def _extract_month_from_query(self, query: str) -> tuple:
        """Extrae mes de la consulta y devuelve rango de fechas"""
        query_lower = query.lower()
        
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
            # También año siguiente
            'enero 2026': ('2026-01-01', '2026-01-31'),
            'febrero 2026': ('2026-02-01', '2026-02-28'),
        }
        
        for mes, (inicio, fin) in meses.items():
            if mes in query_lower:
                return inicio, fin
        
        # Si dice "este mes"
        if 'este mes' in query_lower:
            from datetime import datetime
            hoy = datetime.now()
            inicio = hoy.replace(day=1).strftime('%Y-%m-%d')
            # Último día del mes
            if hoy.month == 12:
                fin = hoy.replace(day=31).strftime('%Y-%m-%d')
            else:
                fin = (hoy.replace(day=1, month=hoy.month+1) - timedelta(days=1)).strftime('%Y-%m-%d')
            return inicio, fin
        
        return None, None

    def _format_exams_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de exámenes"""
        if not data or not data.get("examenes"):
            return f"¡Hola {nombre}! 📝\n\n📅 No tenés exámenes programados en los próximos días.\n\n¿Necesitás información sobre alguna fecha específica? 😊"
        
        response = f"¡Hola {nombre}! 📝\n\n"
        response += f"📅 **Tus próximos exámenes:** ({data['total']} en total)\n\n"
        
        for examen in data["examenes"]:
            # Emoji según tipo
            tipo_emoji = {
                'parcial': '📝',
                'final': '🎯',
                'recuperatorio': '🔄',
                'trabajo_practico': '💻'
            }.get(examen['tipo'], '📝')
            
            response += f"{tipo_emoji} **{examen['materia']}** - {examen['nombre']}\n"
            response += f"   • 📆 Fecha: {examen['fecha']}\n"
            response += f"   • ⏰ Horario: {examen['hora_inicio']} a {examen['hora_fin']}\n"
            response += f"   • 📍 Aula: {examen['aula']} ({examen.get('edificio', 'Campus Principal')})\n"
            response += f"   • 🔵 Modalidad: {examen['modalidad'].capitalize()}\n"
            
            if examen.get('observaciones'):
                response += f"   • 📌 {examen['observaciones']}\n"
            
            response += "\n"
        
        response += "¿Necesitás información sobre algún examen específico? 😊"
        return response

    def _format_events_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de eventos"""
        response = f"¡Hola {nombre}! 📋\n\n"

        if data.get("eventos"):
            response += "📅 **Eventos del calendario académico:**\n\n"
            for evento in data["eventos"]:
                response += f"📌 **{evento['nombre']}**\n"
                response += f"• Fecha: {evento['fecha']}\n"
                if evento.get("descripcion"):
                    response += f"• {evento['descripcion']}\n"
                response += "\n"

        if data.get("proximos_eventos"):
            response += "🔜 **Próximos eventos importantes:**\n\n"
            for evento in data["proximos_eventos"]:
                response += f"⏰ **{evento['nombre']}** - {evento['fecha']}\n"
                response += f"   (En {evento['dias_restantes']} días)\n\n"

        response += "¿Necesitás información sobre algún evento específico? 😊"
        return response

    def _format_holidays_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de feriados"""
        response = f"¡Hola {nombre}! 🏖️\n\n"

        if data.get("feriados"):
            response += "📅 **Feriados y días sin clases:**\n\n"
            for feriado in data["feriados"]:
                emoji = "🏖️" if not feriado.get("hay_clases", True) else "📚"
                response += f"{emoji} **{feriado['nombre']}** - {feriado['fecha']}\n"
                if not feriado.get("hay_clases", True):
                    response += "   (No hay clases)\n"
                response += "\n"

        if data.get("proximo_feriado"):
            prox = data["proximo_feriado"]
            response += f"🔜 **Próximo feriado:** {prox['nombre']} ({prox['fecha']})\n"
            response += f"   En {prox['dias_restantes']} días\n\n"

        response += "¿Necesitás información sobre alguna fecha específica? 😊"
        return response

    def _format_enrollments_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de inscripciones"""
        response = f"¡Hola {nombre}! 📊\n\n"

        if data.get("inscripciones"):
            response += "📝 **Períodos de inscripción:**\n\n"
            for inscripcion in data["inscripciones"]:
                estado_emoji = "✅" if inscripcion["estado"] == "abierta" else "⏰"
                response += f"{estado_emoji} **{inscripcion['tipo']}**\n"
                response += f"• Período: {inscripcion['fecha_inicio']} al {inscripcion['fecha_fin']}\n"
                response += f"• Estado: {inscripcion['estado'].title()}\n"
                if inscripcion.get("url_inscripcion"):
                    response += f"• Link: {inscripcion['url_inscripcion']}\n"
                response += "\n"

        if data.get("proximas_inscripciones"):
            response += "🔜 **Próximas aperturas:**\n\n"
            for inscripcion in data["proximas_inscripciones"]:
                response += f"⏰ **{inscripcion['tipo']}**\n"
                response += f"   Abre el {inscripcion['fecha_apertura']} (en {inscripcion['dias_restantes']} días)\n\n"

        response += "¿Necesitás ayuda con alguna inscripción específica? 😊"
        return response

    def _get_mock_exams_response(self, materia: Optional[str], nombre: str) -> str:
        """Respuesta mock para exámenes"""
        if materia:
            return f"""¡Hola {nombre}! 📝

📅 **Exámenes de {materia}:**

📚 **Parcial 1**
• Fecha: 15 de Noviembre 2024 a las 14:00
• Aula: R3
• Duración: 2 horas

¿Necesitás información sobre algún otro examen? 😊"""
        else:
            return f"""¡Hola {nombre}! 📝

📅 **Tus próximos exámenes:**

📚 **Nativa Digital - Parcial 1**
• Fecha: 15 de Noviembre 2024 a las 14:00
• Aula: R3

📚 **Programación I - Parcial 2**
• Fecha: 20 de Noviembre 2024 a las 16:00
• Aula: A4

¿Necesitás información específica sobre algún examen? 😊"""

    def _get_mock_events_response(self, nombre: str) -> str:
        """Respuesta mock para eventos"""
        return f"""¡Hola {nombre}! 📋

📅 **Próximos eventos del calendario académico:**

📌 **Exámenes Finales**
• Fecha: 2 de Diciembre 2024
• Inicio del período de finales

📌 **Fin de Clases**
• Fecha: 25 de Noviembre 2024
• Última semana de cursada

¿Necesitás información sobre algún evento específico? 😊"""

    def _get_mock_holidays_response(self, nombre: str) -> str:
        """Respuesta mock para feriados"""
        return f"""¡Hola {nombre}! 🏖️

📅 **Próximos feriados:**

🎄 **Navidad** - 25 de Diciembre 2024
   (No hay clases)

🎊 **Año Nuevo** - 1 de Enero 2025
   (No hay clases)

🔜 **Próximo feriado:** Navidad (en 35 días)

¿Necesitás información sobre alguna fecha específica? 😊"""

    def _get_mock_enrollments_response(self, nombre: str) -> str:
        """Respuesta mock para inscripciones"""
        return f"""¡Hola {nombre}! 📊

📝 **Períodos de inscripción:**

✅ **Inscripción a Exámenes Finales**
• Período: 1 al 15 de Noviembre 2024
• Estado: Abierta
• Link: https://inscripciones.austral.edu.ar

⏰ **Inscripción a Materias 2025**
• Período: 15 al 30 de Noviembre 2024
• Estado: Próximamente

¿Necesitás ayuda con alguna inscripción específica? 😊"""

    def _get_error_response(self, user_info: Dict[str, Any]) -> str:
        """Respuesta de error personalizada"""
        return f"""¡Hola {user_info['nombre']}! 😅

Hubo un problemita técnico y no pude procesar tu consulta sobre fechas y calendario.

Por favor intentá de nuevo en unos minutos, o si es urgente podés contactar directamente a la secretaría académica.

¿Te puedo ayudar con algo más mientras tanto? 😊"""