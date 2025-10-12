"""
Agente académico usando Pydantic Models para mejor tipado y formateo
"""
from typing import Dict, Any, Optional
from app.tools.academic_tools import AcademicTools
from app.models import (
    HorariosResponse,
    HorarioInfo,
    InscripcionesResponse,
    InscripcionInfo,
    CreditosVUResponse,
    Modalidad
)
from app.core import DIAS_SEMANA_ES, EMOJIS
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AcademicAgent:
    """Agente académico modernizado con soporte Pydantic"""

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
- Créditos de Vida Universitaria (VU)
- Consultas generales académicas

INSTRUCCIONES:
1. Analiza la consulta del usuario cuidadosamente
2. Determina qué herramientas necesitas usar
3. Usa las herramientas disponibles para obtener información precisa
4. Responde de manera amigable y clara usando los modelos Pydantic
5. Si no puedes resolver algo, sugiere escalación

HERRAMIENTAS DISPONIBLES:
- consultar_horarios: Para obtener horarios de un estudiante
- ver_inscripciones: Para ver materias en las que está inscripto
- buscar_profesor: Para encontrar información de profesores
- consultar_aula: Para ubicación de aulas
- consultar_creditos_vu: Para créditos de Vida Universitaria

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
            logger.error(f"Error en agente académico: {e}", exc_info=True)
            return self._get_error_response(user_info)

    def _classify_academic_query(self, query: str) -> str:
        """Clasifica el tipo de consulta académica"""
        if any(word in query for word in ["horario", "clase", "cuándo tengo", "cuando tengo", "hora"]):
            return "horarios"
        elif any(word in query for word in ["inscripción", "inscripto", "materias", "cursando"]):
            return "inscripciones"
        elif any(word in query for word in ["profesor", "profesora", "docente", "quien da"]):
            return "profesores"
        elif any(word in query for word in ["aula", "dónde", "donde", "ubicación", "salón"]):
            return "aulas"
        elif any(word in query for word in ["credito", "creditos", "vu", "vida universitaria"]):
            return "creditos_vu"
        else:
            return "general"

    async def _handle_schedules(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre horarios usando HorariosResponse"""
        try:
            # Parámetros para la herramienta
            params = {"alumno_id": user_info["id"]}

            # Detectar si pregunta por una materia específica
            materia_detectada = self._extract_subject_from_query(query)
            if materia_detectada:
                params["materia_nombre"] = materia_detectada

            # Detectar día específico
            dia = self._extract_day_from_query(query)
            if dia:
                params["dia_semana"] = dia

            # Llamar a la herramienta (retorna dict)
            result_dict = await self.tools.consultar_horarios(params)

            if result_dict and result_dict.get("horarios"):
                # Convertir dict a modelo Pydantic para aprovechar properties
                response = HorariosResponse(**result_dict)
                return self._format_schedule_response(response, user_info["nombre"])
            else:
                return f"¡Hola {user_info['nombre']}! 😅 No pude encontrar información sobre tus horarios en este momento."

        except Exception as e:
            logger.error(f"Error obteniendo horarios: {e}", exc_info=True)
            return self._get_error_response(user_info)

    async def _handle_enrollments(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre inscripciones usando InscripcionesResponse"""
        try:
            result_dict = await self.tools.ver_inscripciones({"alumno_id": user_info["id"]})

            if result_dict and result_dict.get("materias"):
                # Convertir a modelo Pydantic
                response = InscripcionesResponse(**result_dict)
                return self._format_enrollment_response(response, user_info["nombre"])
            else:
                return f"""¡Hola {user_info['nombre']}! {EMOJIS['info']}

No encontré inscripciones registradas para vos en este momento.

Si creés que esto es un error, por favor contactá a la secretaría académica."""

        except Exception as e:
            logger.error(f"Error obteniendo inscripciones: {e}", exc_info=True)
            return self._get_error_response(user_info)

    async def _handle_professors(self, query: str) -> str:
        """Maneja consultas sobre profesores"""
        try:
            # Extraer materia de la consulta
            materia = self._extract_subject_from_query(query)

            if materia:
                result = await self.tools.buscar_profesor({"materia_nombre": materia})

                if result and result.get("encontrado") and result.get("profesor"):
                    prof = result["profesor"]
                    return f"{EMOJIS['profesor']} El profesor de **{materia}** es: **{prof.get('nombre', 'N/A')}**"
                else:
                    return f"{EMOJIS['info']} No encontré información del profesor de **{materia}**. ¿Querés que te ayude con algo más?"
            else:
                return f"{EMOJIS['pregunta']} ¿Podrías decirme de qué materia querés saber el profesor?"

        except Exception as e:
            logger.error(f"Error buscando profesor: {e}", exc_info=True)
            return f"{EMOJIS['error']} Hubo un problema buscando información del profesor."

    async def _handle_classrooms(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre aulas"""
        try:
            materia = self._extract_subject_from_query(query)

            if materia:
                result = await self.tools.consultar_aula({"materia_nombre": materia})

                if result and result.get("encontrada") and result.get("aula"):
                    aula_info = result["aula"]
                    return f"{EMOJIS['aula']} **{materia}** se cursa en el **{aula_info.get('codigo_aula', 'N/A')}** ({aula_info.get('edificio', 'Campus Principal')})"
                else:
                    return f"{EMOJIS['info']} No encontré información sobre el aula de **{materia}**."
            else:
                # Mostrar mensaje general
                return f"""{EMOJIS['aula']} ¡Hola {user_info['nombre']}!

Para saber en qué aula tenés clase, decime de qué materia querés saber.

También puedo mostrarte tu horario completo con todas las aulas si me preguntás por tus horarios. {EMOJIS['ayuda']}"""

        except Exception as e:
            logger.error(f"Error consultando aulas: {e}", exc_info=True)
            return f"{EMOJIS['error']} Hubo un problema consultando la información de aulas."

    async def _handle_creditos_vu(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre créditos VU usando CreditosVUResponse"""
        try:
            result_dict = await self.tools.consultar_creditos_vu({"alumno_id": user_info["id"]})

            if result_dict and result_dict.get("creditos"):
                # Convertir a modelo Pydantic
                response = CreditosVUResponse(**result_dict)
                return self._format_creditos_vu_response(response, user_info["nombre"])
            else:
                return f"""¡Hola {user_info['nombre']}! {EMOJIS['error']}

No pude obtener información sobre tus créditos de Vida Universitaria en este momento.

Por favor intentá de nuevo o contactá a la secretaría académica."""

        except Exception as e:
            logger.error(f"Error obteniendo créditos VU: {e}", exc_info=True)
            return self._get_error_response(user_info)

    async def _handle_general_academic(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas académicas generales"""
        return f"""¡Hola {user_info['nombre']}! {EMOJIS['saludo']}

¿En qué te puedo ayudar con temas académicos?

Puedo contarte sobre:
{EMOJIS['horario']} **Horarios de clases**
{EMOJIS['inscripcion']} **Materias en las que estás inscripto**
{EMOJIS['profesor']} **Profesores de cada materia**
{EMOJIS['aula']} **Ubicación de aulas**
{EMOJIS['creditos_vu']} **Créditos de Vida Universitaria**

¿Qué te interesa saber? {EMOJIS['ayuda']}"""

    # =====================================================
    # HELPERS
    # =====================================================

    def _extract_subject_from_query(self, query: str) -> Optional[str]:
        """Extrae el nombre de la materia de la consulta"""
        query_lower = query.lower()

        # Diccionario de materias conocidas
        materias = {
            "nativa": "Nativa Digital",
            "programación": "Programación I",
            "programacion": "Programación I",
            "matemática": "Matemática Discreta",
            "matematica": "Matemática Discreta",
        }

        for keyword, materia_nombre in materias.items():
            if keyword in query_lower:
                return materia_nombre

        return None

    def _extract_day_from_query(self, query: str) -> Optional[int]:
        """Extrae el día de la semana de la consulta"""
        query_lower = query.lower()

        dias = {
            "lunes": 1,
            "martes": 2,
            "miércoles": 3,
            "miercoles": 3,
            "jueves": 4,
            "viernes": 5,
            "sábado": 6,
            "sabado": 6,
            "domingo": 7
        }

        for dia_nombre, dia_numero in dias.items():
            if dia_nombre in query_lower:
                return dia_numero

        return None

    # =====================================================
    # FORMATTERS CON PYDANTIC
    # =====================================================

    def _format_schedule_response(self, response: HorariosResponse, nombre: str) -> str:
        """Formatea la respuesta de horarios usando HorariosResponse"""
        if not response.tiene_horarios:
            return f"¡Hola {nombre}! {EMOJIS['info']} No encontré horarios registrados para vos."

        output = f"¡Hola {nombre}! {EMOJIS['horario']} Te muestro tu horario para esta semana:\n\n"

        # Agrupar por día usando la property dias_con_clases
        for dia_num in response.dias_con_clases:
            dia_nombre = DIAS_SEMANA_ES[dia_num]
            horarios_del_dia = [h for h in response.horarios if h.dia_semana == dia_num]

            output += f"{EMOJIS['clase']} **{dia_nombre}**:\n"

            for horario in horarios_del_dia:
                # Usar properties del modelo
                output += f"• {horario.materia_nombre} - {horario.hora_inicio} a {horario.hora_fin}\n"
                output += f"  {EMOJIS['aula']} Aula {horario.aula} ({horario.modalidad})\n"

                if horario.profesor_nombre:
                    output += f"  {EMOJIS['profesor']} Prof. {horario.profesor_nombre}\n"

                # Usar property calculada duracion_minutos
                output += f"  ⏱️ Duración: {horario.duracion_minutos} minutos\n"

            output += "\n"

        output += f"¿Necesitás que te ayude con algo más? {EMOJIS['ayuda']}"
        return output

    def _format_enrollment_response(self, response: InscripcionesResponse, nombre: str) -> str:
        """Formatea la respuesta de inscripciones usando InscripcionesResponse"""
        if response.total == 0:
            return f"¡Hola {nombre}! {EMOJIS['info']} No encontré inscripciones registradas para vos."

        output = f"¡Hola {nombre}! {EMOJIS['inscripcion']} Estás inscripto en las siguientes materias:\n\n"

        # Usar property materias_cursando para mostrar solo las activas
        materias_activas = response.materias_cursando

        for i, inscripcion in enumerate(materias_activas, 1):
            output += f"{i}. {EMOJIS['materia']} **{inscripcion.materia_nombre}**"

            if inscripcion.materia_codigo != 'N/A':
                output += f" ({inscripcion.materia_codigo})"

            output += f"\n   • Comisión: {inscripcion.comision_codigo}\n"
            # estado ya es string por use_enum_values=True
            output += f"   • Estado: {inscripcion.estado}\n"

            # Usar property esta_cursando
            if inscripcion.esta_cursando:
                output += f"   {EMOJIS['exito']} Cursando actualmente\n"

            output += "\n"

        # Mostrar total
        output += f"**Total**: {len(materias_activas)} materias activas\n\n"
        output += f"¿Necesitás información específica sobre alguna materia? {EMOJIS['ayuda']}"

        return output

    def _format_creditos_vu_response(self, response: CreditosVUResponse, nombre: str) -> str:
        """Formatea la respuesta de créditos VU usando CreditosVUResponse"""
        creditos = response.creditos

        # Emoji según property nivel_progreso
        emoji_map = {
            "Completado": EMOJIS["exito"],
            "Casi completo": "🔵",
            "En progreso": "🟡",
            "Inicial": "🟠"
        }

        emoji_status = emoji_map.get(creditos.nivel_progreso, EMOJIS["info"])

        # Texto de status
        status_messages = {
            "Completado": "**¡Felicitaciones! Ya cumplís con el requisito.**",
            "Casi completo": "Estás muy cerca de completar el requisito.",
            "En progreso": "Vas por buen camino.",
            "Inicial": "Aún te quedan varios créditos por completar."
        }

        status_text = status_messages.get(creditos.nivel_progreso, "Seguí adelante.")

        # Barra de progreso visual
        barra_llena = int(creditos.porcentaje_completado / 10)
        barra_vacia = 10 - barra_llena
        barra = "█" * barra_llena + "░" * barra_vacia

        output = f"""¡Hola {nombre}! {EMOJIS['creditos_vu']}

**Créditos de Vida Universitaria (VU)**

{emoji_status} {status_text}

📊 **Progreso:**
{barra} {creditos.porcentaje_completado}%

📝 **Detalle:**
• Créditos actuales: **{creditos.creditos_actuales}**
• Créditos necesarios: **{creditos.creditos_necesarios}**
• Créditos faltantes: **{creditos.creditos_faltantes}**

💡 **¿Qué son los créditos VU?**
Son actividades extracurriculares obligatorias para recibir tu título. Incluyen:
• Talleres deportivos
• Actividades culturales
• Voluntariado universitario
• Charlas y conferencias
"""

        # Usar property necesita_creditos
        if response.necesita_creditos:
            output += f"\n¿Querés saber más sobre actividades disponibles para sumar créditos? {EMOJIS['ayuda']}"

        return output

    def _get_error_response(self, user_info: Dict[str, Any]) -> str:
        """Respuesta de error personalizada"""
        return f"""{EMOJIS['error']} ¡Hola {user_info['nombre']}!

Hubo un problemita técnico y no pude procesar tu consulta académica.

Por favor intentá de nuevo en unos minutos, o si es urgente podés contactar directamente a la secretaría académica.

¿Te puedo ayudar con algo más mientras tanto? {EMOJIS['ayuda']}"""
