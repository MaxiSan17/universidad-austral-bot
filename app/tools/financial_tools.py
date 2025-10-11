from typing import Dict, Any, Optional
from app.tools.n8n_manager import N8NManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

class FinancialTools:
    """Herramientas financieras que se conectan con n8n webhooks"""

    def __init__(self):
        self.n8n_manager = N8NManager()

    async def estado_cuenta(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta el estado de cuenta del alumno

        Webhook n8n: {N8N_BASE_URL}/financial/estado-cuenta

        Parámetros esperados por n8n:
        - alumno_id: ID del alumno

        Respuesta esperada de n8n:
        {
            "deudas": [
                {
                    "concepto": "Cuota Octubre 2024",
                    "monto": 150000,
                    "vencimiento": "2024-10-15",
                    "estado": "Pendiente"
                }
            ],
            "proximo_vencimiento": "2024-11-15",
            "monto_pendiente": 150000,
            "estado": "Con deuda"
        }
        """
        try:
            webhook_path = "financial/estado-cuenta"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook estado_cuenta: {e}")
            return None

    async def historial_pagos(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Consulta historial de pagos

        Webhook n8n: {N8N_BASE_URL}/financial/pagos

        Parámetros esperados por n8n:
        - alumno_id: ID del alumno
        - fecha_desde: (opcional) Fecha desde en formato YYYY-MM-DD
        - fecha_hasta: (opcional) Fecha hasta en formato YYYY-MM-DD

        Respuesta esperada de n8n:
        {
            "pagos": [
                {
                    "fecha": "2024-09-15",
                    "concepto": "Cuota Septiembre 2024",
                    "monto": 150000,
                    "metodo": "Transferencia",
                    "comprobante": "TRF-20240915-001"
                }
            ],
            "total_pagado": 450000,
            "cantidad_pagos": 3
        }
        """
        try:
            webhook_path = "financial/pagos"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook historial_pagos: {e}")
            return None

    async def generar_factura(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Genera o descarga una factura

        Webhook n8n: {N8N_BASE_URL}/financial/facturas

        Parámetros esperados por n8n:
        - alumno_id: ID del alumno
        - periodo: Período de la factura (ej: "2024-10")
        - tipo: "cuota" | "inscripcion" | "certificado"

        Respuesta esperada de n8n:
        {
            "factura_url": "https://storage.austral.edu.ar/facturas/2024-10-alumno-123.pdf",
            "numero_factura": "001-0012345",
            "fecha_emision": "2024-10-01",
            "monto": 150000,
            "vencimiento": "2024-10-15"
        }
        """
        try:
            webhook_path = "financial/facturas"
            return await self.n8n_manager.call_webhook(webhook_path, params)
        except Exception as e:
            logger.error(f"Error llamando webhook generar_factura: {e}")
            return None