from typing import Dict, Any, List, Optional
from app.tools.financial_tools import FinancialTools
from app.utils.logger import get_logger

logger = get_logger(__name__)

class FinancialAgent:
    """Agente financiero modernizado con LangChain/LangGraph"""

    def __init__(self):
        self.tools = FinancialTools()

    async def process_query(self, query: str, user_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Procesa una consulta financiera"""
        try:
            query_type = self._classify_financial_query(query.lower())
            logger.info(f"Consulta financiera clasificada como: {query_type}")

            if query_type == "estado_cuenta":
                return await self._handle_account_status(user_info)
            elif query_type == "creditos_vu":
                return await self._handle_vu_credits(user_info)
            elif query_type == "pagos":
                return await self._handle_payments(user_info)
            elif query_type == "facturas":
                return await self._handle_invoices(query, user_info)
            else:
                return await self._handle_general_financial(user_info)

        except Exception as e:
            logger.error(f"Error en agente financiero: {e}")
            return self._get_error_response(user_info)

    def _classify_financial_query(self, query: str) -> str:
        """Clasifica el tipo de consulta financiera"""
        if any(word in query for word in ["deuda", "debo", "estado", "cuenta", "pagar", "vencimiento"]):
            return "estado_cuenta"
        elif any(word in query for word in ["credito", "crédito", "vu", "vida universitaria", "actividades"]):
            return "creditos_vu"
        elif any(word in query for word in ["pago", "pagué", "transferencia", "historial"]):
            return "pagos"
        elif any(word in query for word in ["factura", "comprobante", "recibo"]):
            return "facturas"
        else:
            return "general"

    async def _handle_account_status(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre estado de cuenta"""
        try:
            result = await self.tools.estado_cuenta({"alumno_id": user_info["id"]})

            if result:
                return self._format_account_status_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return f"""¡Hola {user_info['nombre']}! 💰

📊 **Estado de tu cuenta:**

✅ **¡Estás al día!** No tenés deudas pendientes.

📅 **Próximo vencimiento:** 15 de Diciembre 2024
💵 **Monto:** $150.000

¿Necesitás ayuda con algo más relacionado a pagos? 😊"""

        except Exception as e:
            logger.error(f"Error obteniendo estado de cuenta: {e}")
            return self._get_error_response(user_info)

    async def _handle_vu_credits(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre créditos VU"""
        try:
            result = await self.tools.consultar_creditos_vu({"alumno_id": user_info["id"]})

            if result:
                return self._format_vu_credits_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return f"""¡Hola {user_info['nombre']}! 🎯

📈 **Tus créditos de Vida Universitaria:**

✅ **Créditos actuales:** 8/10
🎯 **Te faltan:** 2 créditos para completar

📋 **Actividades completadas:**
• ✅ Taller de Teatro (3 créditos)
• ✅ Voluntariado (5 créditos)

💡 **¿Sabías que...?** Podés completar los créditos faltantes con deportes, talleres o actividades de extensión.

¿Querés información sobre actividades disponibles? 😊"""

        except Exception as e:
            logger.error(f"Error obteniendo créditos VU: {e}")
            return self._get_error_response(user_info)

    async def _handle_payments(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre historial de pagos"""
        try:
            result = await self.tools.historial_pagos({"alumno_id": user_info["id"]})

            if result:
                return self._format_payments_response(result, user_info["nombre"])
            else:
                # Mock response para desarrollo
                return f"""¡Hola {user_info['nombre']}! 💳

📋 **Historial de pagos recientes:**

• ✅ **Septiembre 2024** - $150.000 - Pagado el 10/09
• ✅ **Agosto 2024** - $150.000 - Pagado el 08/08
• ✅ **Julio 2024** - $150.000 - Pagado el 05/07

💰 **Total pagado este año:** $1.350.000

¿Necesitás algún comprobante específico? 😊"""

        except Exception as e:
            logger.error(f"Error obteniendo historial de pagos: {e}")
            return self._get_error_response(user_info)

    async def _handle_invoices(self, query: str, user_info: Dict[str, Any]) -> str:
        """Maneja consultas sobre facturas"""
        try:
            # Detectar período específico
            periodo = self._extract_period_from_query(query)
            params = {"alumno_id": user_info["id"], "tipo": "cuota"}

            if periodo:
                params["periodo"] = periodo

            result = await self.tools.generar_factura(params)

            if result:
                return self._format_invoice_response(result, user_info["nombre"])
            else:
                return f"""¡Hola {user_info['nombre']}! 📄

Para generar tu factura, necesito saber de qué período la necesitás.

Por ejemplo:
• "Factura de octubre 2024"
• "Comprobante de inscripción"
• "Recibo del último pago"

¿De qué período necesitás la factura? 😊"""

        except Exception as e:
            logger.error(f"Error generando factura: {e}")
            return self._get_error_response(user_info)

    async def _handle_general_financial(self, user_info: Dict[str, Any]) -> str:
        """Maneja consultas financieras generales"""
        return f"""¡Hola {user_info['nombre']}! 💰

¿En qué te puedo ayudar con temas financieros?

Puedo ayudarte con:
• 📊 **Estado de cuenta** y deudas
• 💳 **Historial de pagos**
• 📄 **Facturas y comprobantes**
• 🎯 **Créditos de Vida Universitaria**

¿Qué necesitás saber? 😊"""

    def _extract_period_from_query(self, query: str) -> Optional[str]:
        """Extrae el período de la consulta"""
        import re

        # Buscar patrones como "octubre 2024", "10/2024", etc.
        month_pattern = r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})'
        date_pattern = r'(\d{1,2})/(\d{4})'

        month_match = re.search(month_pattern, query.lower())
        if month_match:
            month_name = month_match.group(1)
            year = month_match.group(2)
            month_mapping = {
                'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
            }
            month_num = month_mapping.get(month_name, '01')
            return f"{year}-{month_num}"

        date_match = re.search(date_pattern, query)
        if date_match:
            month = date_match.group(1).zfill(2)
            year = date_match.group(2)
            return f"{year}-{month}"

        return None

    def _format_account_status_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de estado de cuenta"""
        response = f"¡Hola {nombre}! 💰\n\n📊 **Estado de tu cuenta:**\n\n"

        if data.get("deudas"):
            response += "⚠️ **Tenés deudas pendientes:**\n\n"
            for deuda in data["deudas"]:
                response += f"• **{deuda['concepto']}**: ${deuda['monto']:,}\n"
                response += f"  📅 Vence: {deuda['vencimiento']}\n\n"
        else:
            response += "✅ **¡Estás al día!** No tenés deudas pendientes.\n\n"

        if data.get("proximo_vencimiento"):
            response += f"📅 **Próximo vencimiento:** {data['proximo_vencimiento']}\n"

        if data.get("monto_pendiente", 0) > 0:
            response += f"💵 **Monto:** ${data['monto_pendiente']:,}\n"

        response += "\n¿Necesitás ayuda con algo más? 😊"
        return response

    def _format_vu_credits_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de créditos VU"""
        response = f"¡Hola {nombre}! 🎯\n\n📈 **Tus créditos de Vida Universitaria:**\n\n"
        response += f"✅ **Créditos actuales:** {data['creditos_actuales']}/{data['creditos_necesarios']}\n"

        faltantes = data['creditos_necesarios'] - data['creditos_actuales']
        if faltantes > 0:
            response += f"🎯 **Te faltan:** {faltantes} créditos para completar\n\n"
        else:
            response += "🎉 **¡Completaste todos los créditos!**\n\n"

        if data.get("actividades"):
            response += "📋 **Actividades completadas:**\n"
            for actividad in data["actividades"]:
                estado_emoji = "✅" if actividad["estado"] == "Completado" else "⏳"
                response += f"• {estado_emoji} {actividad['nombre']} ({actividad['creditos']} créditos)\n"

        response += "\n¿Necesitás información sobre actividades disponibles? 😊"
        return response

    def _format_payments_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de historial de pagos"""
        response = f"¡Hola {nombre}! 💳\n\n📋 **Historial de pagos recientes:**\n\n"

        for pago in data.get("pagos", []):
            response += f"• ✅ **{pago['concepto']}** - ${pago['monto']:,}\n"
            response += f"  📅 Pagado el {pago['fecha']} via {pago['metodo']}\n\n"

        if data.get("total_pagado"):
            response += f"💰 **Total pagado:** ${data['total_pagado']:,}\n"

        response += "\n¿Necesitás algún comprobante específico? 😊"
        return response

    def _format_invoice_response(self, data: Dict[str, Any], nombre: str) -> str:
        """Formatea la respuesta de factura"""
        response = f"¡Hola {nombre}! 📄\n\n✅ **Factura generada exitosamente:**\n\n"
        response += f"📋 **Número:** {data['numero_factura']}\n"
        response += f"📅 **Fecha:** {data['fecha_emision']}\n"
        response += f"💵 **Monto:** ${data['monto']:,}\n"

        if data.get("vencimiento"):
            response += f"⏰ **Vencimiento:** {data['vencimiento']}\n"

        if data.get("factura_url"):
            response += f"\n🔗 **Descargar:** {data['factura_url']}\n"

        response += "\n¿Necesitás algo más? 😊"
        return response

    def _get_error_response(self, user_info: Dict[str, Any]) -> str:
        """Respuesta de error personalizada"""
        return f"""¡Hola {user_info['nombre']}! 😅

Hubo un problemita técnico y no pude procesar tu consulta financiera.

Por favor intentá de nuevo en unos minutos, o si es urgente podés contactar directamente a administración.

¿Te puedo ayudar con algo más mientras tanto? 😊"""