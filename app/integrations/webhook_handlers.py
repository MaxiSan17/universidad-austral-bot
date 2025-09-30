from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.agents.supervisor import supervisor_agent
from app.session.session_manager import session_manager
from app.config import settings
from app.utils.logger import get_logger
import json
from datetime import datetime

logger = get_logger(__name__)

webhook_router = APIRouter()


# Modelos Pydantic para validación de n8n
class N8NUser(BaseModel):
    """Usuario desde n8n"""
    name: str = "Usuario"
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_id: Optional[str] = None


class N8NMessage(BaseModel):
    """Mensaje desde n8n"""
    content: str
    message_id: Optional[str] = None
    content_type: str = "text"
    attachments: list = Field(default_factory=list)


class N8NSession(BaseModel):
    """Sesión desde n8n"""
    session_id: str
    platform: str = "chatwoot"
    conversation_id: Optional[str] = None


class N8NWebhookPayload(BaseModel):
    """Payload completo desde n8n"""
    source: str
    session_id: Optional[str] = None  # Para formato simplificado
    message: Optional[str] = None  # Para formato simplificado
    user: Optional[N8NUser] = None
    session: Optional[N8NSession] = None
    message_data: Optional[N8NMessage] = Field(None, alias="message")
    timestamp: Optional[str] = None
    event_type: Optional[str] = None

    class Config:
        populate_by_name = True

@webhook_router.post("/n8n")
async def n8n_webhook(
    request: Request,
    x_n8n_api_key: Optional[str] = Header(None)
):
    """
    Maneja webhooks desde n8n (Chatwoot, WhatsApp, etc.)

    Este endpoint es el punto de entrada para todos los mensajes que vienen
    desde n8n, independientemente de la plataforma origen.
    """
    try:
        # Validar API key si está configurada
        if settings.N8N_API_KEY and x_n8n_api_key != settings.N8N_API_KEY:
            logger.warning("Intento de acceso con API key inválida")
            raise HTTPException(status_code=401, detail="API key inválida")

        # Parsear payload
        raw_payload = await request.json()
        logger.debug(f"Payload recibido desde n8n: {json.dumps(raw_payload, indent=2)}")

        # Normalizar payload (soporta formato completo y simplificado)
        normalized = _normalize_n8n_payload(raw_payload)

        # Extraer datos normalizados
        session_id = normalized["session_id"]
        user_message = normalized["message"]
        source = normalized["source"]

        logger.info(f"Mensaje desde n8n - Source: {source}, Session: {session_id}")

        # Procesar mensaje con el supervisor
        response = await supervisor_agent.process_message(user_message, session_id)

        # Preparar respuesta estructurada para n8n
        response_payload = {
            "status": "success",
            "session_id": session_id,
            "response": {
                "content": response,
                "message_type": "text",
                "metadata": {
                    "source": source,
                    "confidence_score": 0.9,
                    "agent_used": "supervisor",
                    "escalation_required": False
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        logger.info(f"Respuesta enviada a n8n para sesión {session_id}")
        return JSONResponse(response_payload)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando webhook de n8n: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


def _normalize_n8n_payload(raw_payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Normaliza diferentes formatos de payload de n8n a un formato estándar.

    Soporta:
    - Formato completo con session, user, message_data
    - Formato simplificado con session_id, message directamente
    """
    # Formato simplificado
    if "message" in raw_payload and isinstance(raw_payload["message"], str):
        return {
            "session_id": raw_payload.get("session_id", "unknown"),
            "message": raw_payload["message"],
            "source": raw_payload.get("source", "unknown")
        }

    # Formato completo
    session_data = raw_payload.get("session", {})
    message_data = raw_payload.get("message", {})

    session_id = session_data.get("session_id") or raw_payload.get("session_id", "unknown")

    # Extraer contenido del mensaje
    if isinstance(message_data, dict):
        message_content = message_data.get("content", "")
    else:
        message_content = str(message_data) if message_data else ""

    return {
        "session_id": session_id,
        "message": message_content,
        "source": raw_payload.get("source", "unknown")
    }


@webhook_router.post("/chatwoot")
async def chatwoot_webhook(request: Request):
    """
    Maneja webhooks directos de Chatwoot (legacy).
    Se recomienda usar n8n como intermediario.
    """
    try:
        payload = await request.json()

        # Validar que es un mensaje nuevo
        if payload.get("event") != "message_created":
            return JSONResponse({"status": "ignored", "reason": "not_a_message"})

        # Extraer información del mensaje
        message_data = payload.get("data", {})
        conversation = message_data.get("conversation", {})
        message = message_data.get("message", {})

        # Verificar que es un mensaje del usuario (no del bot)
        if message.get("message_type") != "incoming":
            return JSONResponse({"status": "ignored", "reason": "outgoing_message"})

        # Extraer datos necesarios
        session_id = str(conversation.get("id", "unknown"))
        user_message = message.get("content", "")

        logger.info(f"Mensaje directo de Chatwoot - Sesión: {session_id}")
        logger.warning("Usando webhook directo de Chatwoot. Se recomienda usar n8n.")

        # Procesar mensaje con el supervisor
        response = await supervisor_agent.process_message(user_message, session_id)

        logger.info(f"Respuesta generada para sesión {session_id}: {response[:100]}...")

        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "response_sent": True,
            "response": response
        })

    except Exception as e:
        logger.error(f"Error procesando webhook de Chatwoot: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@webhook_router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """Maneja webhooks de WhatsApp Business API"""
    try:
        payload = await request.json()

        # Extraer mensajes de WhatsApp
        messages = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])

        for message in messages:
            # Extraer información del mensaje
            phone_number = message.get("from", "")
            message_text = message.get("text", {}).get("body", "")
            message_id = message.get("id", "")

            if not message_text:
                continue

            # Usar el número de teléfono como session_id
            session_id = f"whatsapp_{phone_number}"

            logger.info(f"Mensaje de WhatsApp - Teléfono: {phone_number}")

            # Procesar mensaje
            response = await supervisor_agent.process_message(message_text, session_id)

            # Aquí irían las llamadas a la API de WhatsApp para enviar la respuesta
            logger.info(f"Respuesta para WhatsApp {phone_number}: {response[:100]}...")

        return JSONResponse({"status": "success"})

    except Exception as e:
        logger.error(f"Error procesando webhook de WhatsApp: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@webhook_router.post("/test")
async def test_webhook(request: Request):
    """Endpoint de prueba para desarrollo"""
    try:
        payload = await request.json()

        session_id = payload.get("session_id", "test_session")
        message = payload.get("message", "Hola")

        logger.info(f"Mensaje de prueba - Sesión: {session_id}")

        # Procesar mensaje
        response = await supervisor_agent.process_message(message, session_id)

        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "user_message": message,
            "bot_response": response,
            "session_stats": session_manager.get_session_stats()
        })

    except Exception as e:
        logger.error(f"Error en webhook de prueba: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@webhook_router.get("/sessions")
async def get_sessions():
    """Endpoint para obtener estadísticas de sesiones"""
    try:
        # Limpiar sesiones expiradas
        cleaned = session_manager.cleanup_expired_sessions()

        stats = session_manager.get_session_stats()
        stats["cleaned_sessions"] = cleaned

        return JSONResponse(stats)

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@webhook_router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Endpoint para limpiar una sesión específica"""
    try:
        session_manager.clear_session(session_id)

        return JSONResponse({
            "status": "success",
            "message": f"Sesión {session_id} limpiada"
        })

    except Exception as e:
        logger.error(f"Error limpiando sesión: {e}")
        raise HTTPException(status_code=500, detail=str(e))