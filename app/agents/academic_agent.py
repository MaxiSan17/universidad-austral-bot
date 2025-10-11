from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from app.tools.academic_tools import AcademicTools
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)

class AcademicAgent:
    """Agente académico modernizado con LangChain/LangGraph"""

    def __init__(self):
        self.tools = AcademicTools()
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """Define el prompt del sistema para el agente académico"""
        return """Eres el agente académico especializado de la Universidad Austral.

        Tu especialidad es ayudar con:
        - Horarios de clases y materias
        - Inscripciones y estados académicos
        - Información sobre profesores
        - Ubicación de aulas
        - Consultas generales académicas

        INSTRUCCIONES:
        1. Analiza la consulta del usuario cuidadosamente
        2. Determina qué herramientas necesitas usar
        3. Usa las herramientas disponibles para obtener información precisa
        4. Responde de manera amigable y clara
        5. Si no puedes resolver algo, sugiere escalación

        HERRAMIENTAS DISPONIBLES:
        - consultar_horarios: Para obtener horarios de un estudiante
        - ver_inscripciones: Para ver materias en las que está inscripto
        - buscar_profesor: Para encontrar información de profesores
        - consultar_aula: Para ubicación de aulas

        TONO: Amigable, informativo y profesional. Usa emojis apropiados.
        """

    async def process_query(self, query: str, user_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Procesa una consulta académica"""
        try:
            # Analizar el tipo de consulta
            query_type = self._classify_academic_query(query.lower())

            logger.info(f"Consulta académica clasificada como: {query_type}")

            # Procesar según el tipo
            if query_type == "horarios":
                return await self._handle_schedules(query, user_info)
            elif query_type == "inscripciones":
                return await self._handle_enrollments(user_info)
            elif query_type == "profesores":
                return await self._handle_professors(query)
            elif query_type == "aulas":
                return await self._handle_classrooms(query, user_info)
            elif query_type == "creditos_vu":
                return await self._handle_creditos_vu(user_info)
            else:
                return await self._handle_general_academic(user_info)

        except Exception as e:
            logger.error(f"Error en agente académico: {e}")
            return self._get_error_response(user_info)

    def _classify_academic_query(self, query: str) -> str:
        """Clasifica el tipo de consulta académica"""
        if any(word in query for word in ["horario", "clase", "cuándo tengo", "cuando tengo"]):
            return "horarios"
        elif any(word in query for word in ["inscripción", "inscripto", "materias", "cursando"]):
            return "inscripciones"
        elif any(word in query for word in ["profesor", "profesora", "docente", "quien da"]):
            return "profesores"
        elif any(word in query for word in ["aula", "dónde", "donde", "ubicación"]):
            return "aulas"
        elif any(word in query for word in ["credito", "creditos", "vu", "vida universitaria"]):
            return "creditos_vu"
        else:
            return "general"

    async def _handle_schedules(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre horarios"""
        try:
            # Parámetros para la herramienta
            params = {"alumno_id": user_info["id"]}

            # Detectar si pregunta por una materia específica
            if "nativa" in query.lower():
                params["materia_nombre"] = "Nativa Digital"
            elif "programación" in query.lower() or "programacion" in query.lower():
                params["materia_nombre"] = "Programación I"

            # Llamar a la herramienta n8n
            result = await self.tools.consultar_horarios(params)

            if result and "horarios" in result:
                return self._format_schedule_response(result["horarios"], user_info["nombre"])
            else:
                return f"¡Hola {user_info['nombre']}! 😅 No pude encontrar información sobre tus horarios en este momento."

        except Exception as e:
            logger.error(f"Error obteniendo horarios: {e}")
            return self._get_error_response(user_info)

    async def _handle_enrollments(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre inscripciones"""
        try:
            result = await self.tools.ver_inscripciones({"alumno_id": user_info["id"]})

            if result and "materias" in result:
                return self._format_enrollment_response(result["materias"], user_info["nombre"])
            else:
                # Respuesta mock para desarrollo
                return f"""¡Hola {user_info['nombre']}! 📝

Estás inscripto en las siguientes materias:

1. 📚 **Nativa Digital** - Comisión A
2. 💻 **Programación I** - Comisión B
3. 🔢 **Matemática Discreta** - Comisión A

¿Necesitás información específica sobre alguna de estas materias? 😊"""

        except Exception as e:
            logger.error(f"Error obteniendo inscripciones: {e}")
            return self._get_error_response(user_info)

    async def _handle_professors(self, query: str) -> str:
        """Maneja consultas sobre profesores"""
        try:
            # Extraer materia de la consulta
            materia = self._extract_subject_from_query(query)

            if materia:
                result = await self.tools.buscar_profesor({"materia": materia})

                if result and "profesor" in result:
                    return f"👨‍🏫 El profesor de **{materia}** es: **{result['profesor']}**"
                else:
                    # Mock response para desarrollo
                    mock_professors = {
                        "Nativa Digital": "Prof. García Martínez",
                        "Programación I": "Prof. Rodríguez",
                        "Matemática Discreta": "Prof. López"
                    }
                    profesor = mock_professors.get(materia, "Información no disponible")
                    return f"👨‍🏫 El profesor de **{materia}** es: **{profesor}**"
            else:
                return "🤔 ¿Podrías decirme de qué materia querés saber el profesor?"

        except Exception as e:
            logger.error(f"Error buscando profesor: {e}")
            return "😅 Hubo un problema buscando información del profesor."

    async def _handle_classrooms(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre aulas"""
        try:
            materia = self._extract_subject_from_query(query)

            if materia:
                result = await self.tools.consultar_aula({"materia": materia})

                if result and "aula" in result:
                    return f"📍 **{materia}** se cursa en el **{result['aula']}**"
                else:
                    # Mock response para desarrollo
                    mock_classrooms = {
                        "Nativa Digital": "Aula R3",
                        "Programación I": "Aula A4",
                        "Matemática Discreta": "Aula B2"
                    }
                    aula = mock_classrooms.get(materia, "Información no disponible")
                    return f"📍 **{materia}** se cursa en el **{aula}**"
            else:
                # Mostrar todas las aulas del estudiante
                return f"""📍 ¡Hola {user_info['nombre']}! Tus aulas para esta semana:

• **Nativa Digital**: Aula R3
• **Programación I**: Aula A4
• **Matemática Discreta**: Aula B2

¿Querés que te ayude con direcciones o algo más específico? 😊"""

        except Exception as e:
            logger.error(f"Error consultando aulas: {e}")
            return "😅 Hubo un problema consultando la información de aulas."

    async def _handle_creditos_vu(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre créditos VU"""
        try:
            result = await self.tools.consultar_creditos_vu({"alumno_id": user_info["id"]})

            if result:
                return self._format_creditos_vu_response(result, user_info["nombre"])
            else:
                return f"""¡Hola {user_info['nombre']}! 😅

No pude obtener información sobre tus créditos de Vida Universitaria en este momento.

Por favor intentá de nuevo o contactá a la secretaría académica."""

        except Exception as e:
            logger.error(f"Error obteniendo créditos VU: {e}")
            return self._get_error_response(user_info)

    async def _handle_general_academic(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas académicas generales"""
        return f"""¡Hola {user_info['nombre']}! 🎓

¿En qué te puedo ayudar con temas académicos?

Puedo contarte sobre:
• 📅 **Horarios de clases**
• 📝 **Materias en las que estás inscripto**
• 👨‍🏫 **Profesores de cada materia**
• 📍 **Ubicación de aulas**

¿Qué te interesa saber? 😊"""

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

    def _format_schedule_response(self, horarios: List[Dict], nombre: str) -> str:
        """Formatea la respuesta de horarios"""
        # Mapeo de días
        dias_semana = {
            1: 'Lunes',
            2: 'Martes',
            3: 'Miércoles',
            4: 'Jueves',
            5: 'Viernes',
            6: 'Sábado',
            7: 'Domingo'
        }
        
        response = f"¡Hola {nombre}! 📚 Te muestro tu horario para esta semana:\n\n"

        for horario in horarios:
            dia = dias_semana.get(horario.get('dia_semana'), 'Día desconocido')
            materia = horario.get('materia_nombre', 'N/A')
            hora_inicio = horario.get('hora_inicio', 'N/A')
            hora_fin = horario.get('hora_fin', 'N/A')
            aula = horario.get('aula', 'N/A')
            modalidad = horario.get('modalidad', 'N/A')
            profesor = horario.get('profesor_nombre', 'N/A')
            
            response += f"📅 **{dia}**:\n"
            response += f"• {materia} - {hora_inicio} a {hora_fin}\n"
            response += f"• Aula {aula} ({modalidad})\n"
            response += f"• Prof. {profesor}\n\n"

        response += "¿Necesitás que te ayude con algo más? 😊"
        return response

    def _format_enrollment_response(self, materias: List[Dict], nombre: str) -> str:
        """Formatea la respuesta de inscripciones"""
        if not materias:
            return f"¡Hola {nombre}! 😅 No encontré inscripciones registradas para vos en este momento."
        
        response = f"¡Hola {nombre}! 📝 Estás inscripto en las siguientes materias:\n\n"

        for i, materia in enumerate(materias, 1):
            nombre_materia = materia.get('nombre', 'Materia sin nombre')
            codigo = materia.get('codigo', '')
            comision = materia.get('comision', 'Sin comisión')
            estado = materia.get('estado', 'cursando')
            
            # Formato más completo
            response += f"{i}. 📚 **{nombre_materia}**"
            if codigo and codigo != 'N/A':
                response += f" ({codigo})"
            response += f"\n   • Comisión: {comision}\n"
            response += f"   • Estado: {estado}\n\n"

        response += "¿Necesitás información específica sobre alguna materia? 😊"
        return response

    def _format_creditos_vu_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de créditos VU"""
        creditos_actuales = data.get('creditos_actuales', 0)
        creditos_necesarios = data.get('creditos_necesarios', 10)
        creditos_faltantes = data.get('creditos_faltantes', 10)
        porcentaje = data.get('porcentaje_completado', 0)
        cumple = data.get('cumple_requisito', False)
        
        # Emoji según progreso
        if cumple:
            emoji_status = "✅"
            status_text = "**¡Felicitaciones! Ya cumplís con el requisito.**"
        elif porcentaje >= 75:
            emoji_status = "🔵"
            status_text = "Estás muy cerca de completar el requisito."
        elif porcentaje >= 50:
            emoji_status = "🟡"
            status_text = "Vas por buen camino."
        else:
            emoji_status = "🟠"
            status_text = "Aún te quedan varios créditos por completar."
        
        # Barra de progreso visual
        barra_llena = int(porcentaje / 10)  # 10 bloques
        barra_vacia = 10 - barra_llena
        barra = "█" * barra_llena + "░" * barra_vacia
        
        response = f"""¡Hola {nombre}! 🎓

**Créditos de Vida Universitaria (VU)**

{emoji_status} {status_text}

📊 **Progreso:**
{barra} {porcentaje}%

📝 **Detalle:**
• Créditos actuales: **{creditos_actuales}**
• Créditos necesarios: **{creditos_necesarios}**
• Créditos faltantes: **{creditos_faltantes}**

💡 **¿Qué son los créditos VU?**
Son actividades extracurriculares obligatorias para recibir tu título. Incluyen:
• Talleres deportivos
• Actividades culturales
• Voluntariado universitario
• Charlas y conferencias
"""
        
        if not cumple:
            response += "\n¿Querés saber más sobre actividades disponibles para sumar créditos? 😊"
        
        return response

    def _get_error_response(self, user_info: Dict[str, Any]) -> str:
        """Respuesta de error personalizada"""
        return f"""¡Hola {user_info['nombre']}! 😅

Hubo un problemita técnico y no pude procesar tu consulta académica.

Por favor intentá de nuevo en unos minutos, o si es urgente podés contactar directamente a la secretaría académica.

¿Te puedo ayudar con algo más mientras tanto? 😊"""