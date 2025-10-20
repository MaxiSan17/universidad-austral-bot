from typing import Dict, Any, Optional
from app.tools.policies_tools import PoliciesTools
from app.utils.logger import get_logger

logger = get_logger(__name__)

class PoliciesAgent:
    """Agente de políticas y reglamentos modernizado"""

    def __init__(self):
        self.tools = PoliciesTools()

    async def process_query(self, query: str, user_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Procesa una consulta sobre políticas y reglamentos usando búsqueda vectorial

        Este método ahora usa el nuevo sistema de búsqueda semántica que:
        1. Vectoriza la consulta del usuario
        2. Busca documentos similares en Supabase
        3. Genera respuesta contextual con LLM
        """
        try:
            # Normalizar query
            query_normalized = query.lower().strip()

            query_type = self._classify_policies_query(query_normalized)
            logger.info(f"Consulta de políticas clasificada como: {query_type}")

            # Usar búsqueda vectorial como método principal
            params = {
                'consulta': query,
                'alumno_id': user_info.get('id'),
                'tipo': query_type if query_type != 'general' else None
            }

            # Extraer materia si está en la consulta
            materia = self._extract_subject_from_query(query)
            if materia:
                params['materia'] = materia

            logger.info(f"Llamando búsqueda vectorial con params: {params}")

            # Llamar a búsqueda vectorial
            result = await self.tools.consultar_politicas(params)

            if result and result.get('respuesta'):
                # Si hay error pero también respuesta, usar la respuesta
                if result.get('error'):
                    logger.warning(f"⚠️ Búsqueda vectorial retornó error Y respuesta: {result['error']}")

                return self._format_vector_search_response(result, user_info['nombre'])

            elif result and result.get('error'):
                # Solo error, sin respuesta válida
                logger.error(f"❌ Error en búsqueda vectorial: {result['error']}")

                # NO hacer fallback para evitar loops - retornar error amigable
                return f"""¡Hola {user_info['nombre']}! 😅

Hubo un problema al buscar esa información en nuestra base de conocimientos.

{result.get('respuesta', 'Por favor, intentá reformular tu pregunta o contactá a la secretaría académica.')}

¿Te puedo ayudar con algo más? 😊"""

            else:
                # Sin resultado válido
                logger.error("❌ Búsqueda vectorial sin resultado válido")
                return self._get_error_response(user_info)

        except Exception as e:
            logger.error(f"Error en agente de políticas: {e}", exc_info=True)
            return self._get_error_response(user_info)

    async def _fallback_to_legacy(self, query: str, query_type: str, user_info: Dict[str, Any]) -> str:
        """Fallback a métodos legacy si falla la búsqueda vectorial"""
        logger.info(f"Usando fallback legacy para query_type: {query_type}")

        if query_type == "syllabus":
            return await self._handle_syllabus(query, user_info)
        elif query_type == "reglamentos":
            return await self._handle_regulations(query, user_info)
        elif query_type == "procedimientos":
            return await self._handle_procedures(query, user_info)
        elif query_type == "becas":
            return await self._handle_scholarships(user_info)
        else:
            return await self._handle_general_policies(user_info)

    def _classify_policies_query(self, query: str) -> str:
        """Clasifica el tipo de consulta de políticas"""
        if any(word in query for word in ["syllabus", "programa", "materia", "contenido", "temas", "bibliografia"]):
            return "syllabus"
        elif any(word in query for word in ["reglamento", "regla", "norma", "evaluacion", "asistencia"]):
            return "reglamentos"
        elif any(word in query for word in ["procedimiento", "tramite", "solicitar", "certificado", "inscripcion"]):
            return "procedimientos"
        elif any(word in query for word in ["beca", "descuento", "ayuda economica"]):
            return "becas"
        else:
            return "general"

    async def _handle_syllabus(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre syllabus"""
        try:
            materia = self._extract_subject_from_query(query)

            if not materia:
                return f"""¡Hola {user_info['nombre']}! 📖

Para ayudarte con información del syllabus, necesito saber de qué materia.

Por ejemplo:
• "Syllabus de Nativa Digital"
• "Programa de Programación I"
• "Contenidos de Matemática"

¿De qué materia necesitás información? 😊"""

            params = {"materia": materia}

            # Agregar consulta específica si está presente
            consulta_especifica = self._extract_specific_query(query)
            if consulta_especifica:
                params["consulta_especifica"] = consulta_especifica

            result = await self.tools.buscar_syllabus(params)

            if result:
                return self._format_syllabus_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return self._get_mock_syllabus_response(materia, user_info["nombre"])

        except Exception as e:
            logger.error(f"Error consultando syllabus: {e}")
            return self._get_error_response(user_info)

    async def _handle_regulations(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre reglamentos"""
        try:
            tipo_reglamento = self._extract_regulation_type(query)
            params = {"tipo_reglamento": tipo_reglamento}

            consulta_especifica = self._extract_specific_query(query)
            if consulta_especifica:
                params["consulta_especifica"] = consulta_especifica

            result = await self.tools.consultar_reglamento(params)

            if result:
                return self._format_regulation_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return self._get_mock_regulation_response(tipo_reglamento, user_info["nombre"])

        except Exception as e:
            logger.error(f"Error consultando reglamentos: {e}")
            return self._get_error_response(user_info)

    async def _handle_procedures(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre procedimientos"""
        try:
            tipo_procedimiento = self._extract_procedure_type(query)
            params = {"tipo_procedimiento": tipo_procedimiento}

            result = await self.tools.buscar_procedimiento(params)

            if result:
                return self._format_procedure_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return self._get_mock_procedure_response(tipo_procedimiento, user_info["nombre"])

        except Exception as e:
            logger.error(f"Error consultando procedimientos: {e}")
            return self._get_error_response(user_info)

    async def _handle_scholarships(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre becas"""
        try:
            params = {"alumno_id": user_info["id"], "tipo_beca": "todas"}
            result = await self.tools.consultar_becas(params)

            if result:
                return self._format_scholarships_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return f"""¡Hola {user_info['nombre']}! 🎓

📋 **Becas disponibles:**

🏆 **Beca por Mérito Académico**
• Descuento: 50%
• Requisito: Promedio mínimo 8.5
• Fecha límite: 1 de Diciembre 2024

⚽ **Beca Deportiva**
• Descuento: 30%
• Requisito: Participar en equipos universitarios
• Estado: Siempre abierta

🤝 **Beca por Necesidad Económica**
• Descuento: Variable (20-70%)
• Requisito: Evaluación socioeconómica
• Fecha límite: 15 de Noviembre 2024

¿Querés información específica sobre alguna beca? 😊"""

        except Exception as e:
            logger.error(f"Error consultando becas: {e}")
            return self._get_error_response(user_info)

    async def _handle_general_policies(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas generales sobre políticas"""
        return f"""¡Hola {user_info['nombre']}! 📋

¿En qué te puedo ayudar con políticas y reglamentos?

Puedo ayudarte con:
• 📖 **Syllabus y programas** de materias
• 📜 **Reglamentos académicos** y de evaluación
• 📋 **Procedimientos administrativos**
• 🎓 **Becas y ayudas económicas**

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

    def _extract_regulation_type(self, query: str) -> str:
        """Extrae el tipo de reglamento de la consulta"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["evaluacion", "examen", "nota", "parcial"]):
            return "evaluacion"
        elif any(word in query_lower for word in ["asistencia", "falta", "presente"]):
            return "asistencia"
        elif any(word in query_lower for word in ["academico", "materia", "cursada"]):
            return "academico"
        else:
            return "general"

    def _extract_procedure_type(self, query: str) -> str:
        """Extrae el tipo de procedimiento de la consulta"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["certificado", "constancia"]):
            return "certificados"
        elif any(word in query_lower for word in ["inscripcion", "inscribir", "materia"]):
            return "inscripcion"
        elif any(word in query_lower for word in ["cambio", "cambiar"]):
            return "cambio_materia"
        elif any(word in query_lower for word in ["baja", "abandonar"]):
            return "baja"
        else:
            return "general"

    def _extract_specific_query(self, query: str) -> Optional[str]:
        """Extrae la consulta específica del texto"""
        # Palabras clave que indican consultas específicas
        specific_words = ["como", "cuando", "donde", "que", "cuanto", "cual", "requisito", "procedimiento"]

        for word in specific_words:
            if word in query.lower():
                return query  # Retorna la consulta completa para análisis por n8n

        return None

    def _format_syllabus_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de syllabus"""
        response = f"¡Hola {nombre}! 📖\n\n"
        response += f"📚 **{data['materia']}**\n\n"

        contenido = data.get("contenido", {})

        if contenido.get("objetivos"):
            response += f"🎯 **Objetivos:**\n{contenido['objetivos']}\n\n"

        if contenido.get("evaluacion"):
            response += f"📊 **Evaluación:**\n{contenido['evaluacion']}\n\n"

        if contenido.get("temas"):
            response += "📋 **Temas principales:**\n"
            for tema in contenido["temas"]:
                response += f"• {tema}\n"
            response += "\n"

        if contenido.get("bibliografia"):
            response += "📚 **Bibliografía:**\n"
            for libro in contenido["bibliografia"]:
                response += f"• {libro}\n"
            response += "\n"

        if data.get("url_completo"):
            response += f"🔗 **Syllabus completo:** {data['url_completo']}\n\n"

        response += "¿Necesitás información específica sobre algún tema? 😊"
        return response

    def _format_regulation_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de reglamentos"""
        response = f"¡Hola {nombre}! 📜\n\n"
        response += f"📋 **Reglamento {data['tipo'].title()}**\n\n"

        if data.get("contenido"):
            response += f"{data['contenido']}\n\n"

        if data.get("articulos"):
            response += "📖 **Artículos relevantes:**\n"
            for articulo in data["articulos"]:
                response += f"• **{articulo['numero']}:** {articulo['texto']}\n"
            response += "\n"

        if data.get("url_completo"):
            response += f"🔗 **Reglamento completo:** {data['url_completo']}\n\n"

        response += "¿Necesitás aclaración sobre algún punto específico? 😊"
        return response

    def _format_procedure_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de procedimientos"""
        response = f"¡Hola {nombre}! 📋\n\n"
        response += f"📝 **{data['procedimiento']}**\n\n"

        if data.get("pasos"):
            response += "👣 **Pasos a seguir:**\n"
            for paso in data["pasos"]:
                response += f"{paso}\n"
            response += "\n"

        if data.get("requisitos"):
            response += "✅ **Requisitos:**\n"
            for requisito in data["requisitos"]:
                response += f"• {requisito}\n"
            response += "\n"

        if data.get("tiempo_estimado"):
            response += f"⏰ **Tiempo estimado:** {data['tiempo_estimado']}\n"

        if data.get("costo"):
            response += f"💰 **Costo:** {data['costo']}\n"

        if data.get("formulario_url"):
            response += f"🔗 **Formulario:** {data['formulario_url']}\n"

        response += "\n¿Necesitás ayuda con algún paso específico? 😊"
        return response

    def _format_scholarships_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de becas"""
        response = f"¡Hola {nombre}! 🎓\n\n"

        if data.get("becas_disponibles"):
            response += "📋 **Becas disponibles:**\n\n"
            for beca in data["becas_disponibles"]:
                response += f"🏆 **{beca['nombre']}**\n"
                response += f"• Descuento: {beca['porcentaje_descuento']}%\n"
                response += f"• Requisitos: {', '.join(beca['requisitos'])}\n"
                response += f"• Fecha límite: {beca['fecha_limite']}\n\n"

        if data.get("becas_del_alumno"):
            response += "✅ **Tus becas activas:**\n\n"
            for beca in data["becas_del_alumno"]:
                response += f"🎯 **{beca['nombre']}**\n"
                response += f"• Descuento: {beca['descuento']}%\n"
                response += f"• Vigencia: {beca['vigencia']}\n\n"

        response += "¿Querés información específica sobre alguna beca? 😊"
        return response

    def _format_vector_search_response(self, data: Dict[str, Any], nombre: str) -> str:
        """
        Formatea la respuesta de búsqueda vectorial

        La respuesta ya viene procesada por el LLM de n8n, solo agregamos contexto
        """
        response = f"¡Hola {nombre}! 📚\n\n"

        # La respuesta principal ya está formateada por el LLM
        response += data['respuesta']

        # Agregar fuentes si están disponibles (para transparencia)
        if data.get('fuentes') and len(data['fuentes']) > 0:
            response += "\n\n📖 **Fuentes consultadas:**\n"
            for fuente in data['fuentes'][:3]:  # Máximo 3 fuentes
                doc_nombre = fuente.get('documento', 'Documento')
                if fuente.get('seccion'):
                    response += f"• {doc_nombre} - {fuente['seccion']}\n"
                else:
                    response += f"• {doc_nombre}\n"

                # Agregar URL si está disponible
                if fuente.get('url'):
                    response += f"  🔗 {fuente['url']}\n"

        # Agregar confidence score si es bajo (para transparencia)
        confidence = data.get('confidence', 1.0)
        if confidence < 0.7:
            response += f"\n\n⚠️ *Nota: Esta información tiene una confianza del {int(confidence * 100)}%. Si necesitás confirmación, consultá con la secretaría académica.*"

        response += "\n\n¿Necesitás más información? 😊"
        return response

    def _get_mock_syllabus_response(self, materia: str, nombre: str) -> str:
        """Respuesta mock para syllabus"""
        return f"""¡Hola {nombre}! 📖

📚 **{materia}**

🎯 **Objetivos:**
Desarrollar competencias en tecnologías web modernas y metodologías ágiles de desarrollo.

📊 **Evaluación:**
• 2 Parciales (70%)
• Trabajos Prácticos (30%)
• Nota mínima: 6

📋 **Temas principales:**
• Introducción a React
• Estado y Props
• Hooks y Context
• Routing y Navigation

📚 **Bibliografía:**
• JavaScript: The Good Parts - Douglas Crockford
• React Documentation

¿Necesitás información específica sobre algún tema? 😊"""

    def _get_mock_regulation_response(self, tipo: str, nombre: str) -> str:
        """Respuesta mock para reglamentos"""
        return f"""¡Hola {nombre}! 📜

📋 **Reglamento de {tipo.title()}**

📖 **Puntos importantes:**
• **Art. 15:** La asistencia mínima requerida es del 75%
• **Art. 20:** Los exámenes parciales son obligatorios
• **Art. 25:** Se permite un recuperatorio por parcial

¿Necesitás aclaración sobre algún punto específico? 😊"""

    def _get_mock_procedure_response(self, tipo: str, nombre: str) -> str:
        """Respuesta mock para procedimientos"""
        return f"""¡Hola {nombre}! 📋

📝 **Procedimiento: {tipo.replace('_', ' ').title()}**

👣 **Pasos a seguir:**
1. Completar formulario online
2. Adjuntar documentación requerida
3. Pagar arancel correspondiente
4. Esperar confirmación por email

⏰ **Tiempo estimado:** 5-7 días hábiles
💰 **Costo:** $25.000

¿Necesitás ayuda con algún paso específico? 😊"""

    def _get_error_response(self, user_info: Dict[str, Any]) -> str:
        """Respuesta de error personalizada"""
        return f"""¡Hola {user_info['nombre']}! 😅

Hubo un problemita técnico y no pude procesar tu consulta sobre políticas y reglamentos.

Por favor intentá de nuevo en unos minutos, o si es urgente podés contactar directamente a la secretaría académica.

¿Te puedo ayudar con algo más mientras tanto? 😊"""