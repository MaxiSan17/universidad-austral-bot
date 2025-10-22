"""
Agente académico usando Pydantic Models para mejor tipado y formateo
"""
from typing import Dict, Any, Optional
from datetime import date
from difflib import SequenceMatcher
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
from app.core.llm_factory import llm_factory
from app.utils.logger import get_logger
from app.utils.temporal_parser import temporal_parser

logger = get_logger(__name__)


class AcademicAgent:
    """Agente académico modernizado con soporte Pydantic"""

    def __init__(self):
        self.tools = AcademicTools()
        self.system_prompt = self._get_system_prompt()

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
            Tipo de consulta: "horarios", "inscripciones", "profesores", "aulas", "creditos_vu", "general"
        """
        try:
            llm = llm_factory.create(temperature=0.0)

            prompt = f"""Eres un clasificador de consultas académicas universitarias.

Analiza la siguiente consulta y determina de qué tipo es.

CONSULTA DEL USUARIO:
"{query}"

TIPOS POSIBLES:
- horarios: Consultas sobre horarios de clase, cuándo tiene clase, a qué hora es una materia
- inscripciones: Consultas sobre materias inscriptas, en qué está cursando
- profesores: Consultas sobre quién es el profesor de una materia
- aulas: Consultas sobre dónde es una clase, ubicación de aulas
- creditos_vu: Consultas sobre créditos de Vida Universitaria
- general: Consulta ambigua o que no encaja en las anteriores

INSTRUCCIONES:
1. Ignora errores ortográficos
2. Considera sinónimos (ej: "docente" = "profesor", "clase" = "cursada")
3. Responde con UNA SOLA PALABRA (el tipo)
4. Si no estás seguro, responde "general"

RESPUESTA (una palabra):"""

            response = await llm.ainvoke(prompt)
            classification = response.content.strip().lower()

            # Validar que la respuesta sea válida
            valid_types = ["horarios", "inscripciones", "profesores", "aulas", "creditos_vu", "general"]
            if classification in valid_types:
                logger.info(f"🤖 LLM clasificó como: {classification}")
                return classification
            else:
                logger.warning(f"⚠️ LLM retornó tipo inválido: {classification}, usando 'general'")
                return "general"

        except Exception as e:
            logger.error(f"Error en clasificación con LLM: {e}")
            return "general"

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
            # Normalizar query
            query_normalized = query.lower().strip()

            # Analizar el tipo de consulta
            query_type = self._classify_academic_query(query_normalized)

            # Si es "general", intentar con LLM antes de mostrar menú
            if query_type == "general":
                logger.info("🤖 Usando LLM fallback para clasificación...")
                query_type = await self._classify_with_llm(query)

                # Si el LLM también dice "general", entonces realmente es ambiguo
                if query_type == "general":
                    logger.info("✅ Confirmado como consulta general (ambigua)")
                else:
                    logger.info(f"✅ LLM reclasificó como: {query_type}")

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
        """
        Clasifica el tipo de consulta académica con tolerancia a typos.

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
        horarios_kw = [
            "horario", "horarios", "clase", "clases",
            "cuando", "cuándo", "hora", "tengo"
        ]

        inscripciones_kw = [
            "inscripción", "inscripcion", "inscripto", "inscripta",
            "materias", "materia", "cursando", "curso"
        ]

        profesores_kw = [
            "profesor", "profesora", "profe", "docente",
            "quien", "quién", "dicta"
        ]

        aulas_kw = [
            "aula", "salon", "salón", "donde", "dónde",
            "ubicación", "ubicacion"
        ]

        creditos_kw = [
            "credito", "creditos", "crédito", "créditos",
            "vu", "vida universitaria", "actividades"
        ]

        # NIVEL 1: Match exacto (más rápido)
        if any(kw in query for kw in horarios_kw):
            logger.debug("✅ Match exacto: horarios")
            return "horarios"

        if any(kw in query for kw in inscripciones_kw):
            logger.debug("✅ Match exacto: inscripciones")
            return "inscripciones"

        if any(kw in query for kw in profesores_kw):
            logger.debug("✅ Match exacto: profesores")
            return "profesores"

        if any(kw in query for kw in aulas_kw):
            logger.debug("✅ Match exacto: aulas")
            return "aulas"

        if any(kw in query for kw in creditos_kw):
            logger.debug("✅ Match exacto: creditos_vu")
            return "creditos_vu"

        # NIVEL 2: Fuzzy matching (tolerante a typos)
        logger.debug("🔍 No hubo match exacto, intentando fuzzy matching...")

        if self._check_keywords_fuzzy(query, horarios_kw, threshold=0.75):
            logger.debug("✅ Fuzzy match: horarios")
            return "horarios"

        if self._check_keywords_fuzzy(query, inscripciones_kw, threshold=0.75):
            logger.debug("✅ Fuzzy match: inscripciones")
            return "inscripciones"

        if self._check_keywords_fuzzy(query, profesores_kw, threshold=0.75):
            logger.debug("✅ Fuzzy match: profesores")
            return "profesores"

        if self._check_keywords_fuzzy(query, aulas_kw, threshold=0.75):
            logger.debug("✅ Fuzzy match: aulas")
            return "aulas"

        if self._check_keywords_fuzzy(query, creditos_kw, threshold=0.75):
            logger.debug("✅ Fuzzy match: creditos_vu")
            return "creditos_vu"

        # NIVEL 3: Retornar "general" (se usará LLM en process_query)
        logger.debug("❓ No hubo fuzzy match, marcando como 'general' para LLM fallback")
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

            # NUEVO: Parsear expresiones temporales usando TemporalParser
            fecha_desde, fecha_hasta, solo_proximo = temporal_parser.parse(query.lower())

            # Variable para guardar el contexto temporal (para el formatter)
            contexto_temporal = None

            if fecha_desde or fecha_hasta:
                # Se detectó expresión temporal
                params["fecha_desde"] = fecha_desde
                params["fecha_hasta"] = fecha_hasta
                contexto_temporal = self._get_temporal_context(query.lower(), fecha_desde, fecha_hasta)
                logger.info(f"📅 Expresión temporal detectada: {contexto_temporal} ({fecha_desde} a {fecha_hasta})")
            else:
                # Fallback: Detectar día específico con el método legacy
                dia = self._extract_day_from_query(query)
                if dia:
                    params["dia_semana"] = dia
                    contexto_temporal = DIAS_SEMANA_ES.get(dia, "")

            # Llamar a la herramienta (retorna dict)
            result_dict = await self.tools.consultar_horarios(params)

            if result_dict and result_dict.get("horarios"):
                # Convertir dict a modelo Pydantic para aprovechar properties
                response = HorariosResponse(**result_dict)
                return self._format_schedule_response(response, user_info["nombre"], contexto_temporal)
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

    def _get_temporal_context(self, query: str, fecha_desde: Optional[date], fecha_hasta: Optional[date]) -> str:
        """
        Determina el contexto temporal para usar en el mensaje de respuesta.

        Args:
            query: Query del usuario en minúsculas
            fecha_desde: Fecha de inicio del rango
            fecha_hasta: Fecha de fin del rango

        Returns:
            String con el contexto temporal (ej: "mañana", "esta semana", "la semana que viene")
        """
        if not fecha_desde:
            return "esta semana"

        # Detectar expresiones comunes en el query
        if "mañana" in query or "mañana" in query:
            return "mañana"
        elif "hoy" in query:
            return "hoy"
        elif "pasado mañana" in query or "pasado manana" in query:
            return "pasado mañana"
        elif "esta semana" in query:
            return "esta semana"
        elif "semana que viene" in query or "próxima semana" in query or "siguiente semana" in query:
            return "la semana que viene"
        elif "este mes" in query:
            return "este mes"
        elif "mes que viene" in query or "próximo mes" in query or "siguiente mes" in query:
            return "el mes que viene"
        elif fecha_desde == fecha_hasta:
            # Rango de un solo día
            dia_nombre = temporal_parser.get_nombre_dia(fecha_desde)
            return f"el {dia_nombre.lower()}"
        else:
            # Rango de múltiples días
            return f"entre {fecha_desde.strftime('%d/%m')} y {fecha_hasta.strftime('%d/%m')}"

    # =====================================================
    # FORMATTERS CON PYDANTIC
    # =====================================================

    def _format_schedule_response(self, response: HorariosResponse, nombre: str, contexto_temporal: Optional[str] = None) -> str:
        """
        Formatea la respuesta de horarios usando HorariosResponse

        Args:
            response: Respuesta con horarios del alumno
            nombre: Nombre del alumno
            contexto_temporal: Contexto temporal detectado (ej: "mañana", "esta semana")
        """
        if not response.tiene_horarios:
            if contexto_temporal:
                return f"¡Hola {nombre}! {EMOJIS['info']} No tenés clases {contexto_temporal}."
            return f"¡Hola {nombre}! {EMOJIS['info']} No encontré horarios registrados para vos."

        # Mensaje de encabezado adaptativo según el contexto temporal
        if contexto_temporal:
            output = f"¡Hola {nombre}! {EMOJIS['horario']} Te muestro tu horario para {contexto_temporal}:\n\n"
        else:
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
