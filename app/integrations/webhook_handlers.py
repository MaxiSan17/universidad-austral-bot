from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.agents.supervisor import supervisor_agent
from app.session.session_manager import session_manager
from app.config import settings
from app.utils.logger import get_logger
import json
import httpx
from datetime import datetime

logger = get_logger(__name__)

webhook_router = APIRouter()


# Función para enviar mensajes a Chatwoot
async def send_message_to_chatwoot(conversation_id: int, message: str):
    """
    Envía un mensaje a Chatwoot usando su API.
    
    Args:
        conversation_id: ID de la conversación en Chatwoot
        message: Contenido del mensaje a enviar
    """
    if not settings.CHATWOOT_API_TOKEN or not settings.CHATWOOT_URL:
        logger.warning("Chatwoot no configurado. No se puede enviar mensaje.")
        return
    
    url = f"{settings.CHATWOOT_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages"
    
    headers = {
        "api_access_token": settings.CHATWOOT_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": message,
        "message_type": "outgoing",
        "private": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
    logger.info(f"Mensaje enviado a Chatwoot exitosamente (conversation {conversation_id})")


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
    Maneja webhooks directos de Chatwoot.
    """
    try:
        payload = await request.json()
        
        # LOG: Payload completo recibido
        logger.info("=" * 80)
        logger.info("📨 WEBHOOK CHATWOOT RECIBIDO")
        logger.info(f"Payload completo: {json.dumps(payload, indent=2)}")
        logger.info("=" * 80)

        # Validar evento
        event_type = payload.get("event")
        logger.info(f"Event type: {event_type}")
        
        if event_type != "message_created":
            logger.warning(f"❌ Evento ignorado: '{event_type}'")
            return JSONResponse({"status": "ignored", "reason": "not_message_created"})

        # Extraer datos directamente del root (formato real de Chatwoot)
        message_type = payload.get("message_type")
        content = payload.get("content")
        conversation = payload.get("conversation", {})
        sender = payload.get("sender", {})
        
        # LOG: Datos extraídos
        logger.info(f"Message type: {message_type}")
        logger.info(f"Content: {content}")
        logger.info(f"Conversation ID: {conversation.get('id')}")
        
        # Validar que es incoming
        if message_type != "incoming":
            logger.warning(f"❌ Mensaje ignorado: tipo '{message_type}'")
            return JSONResponse({"status": "ignored", "reason": "not_incoming"})
        
        if not content:
            logger.warning("❌ Mensaje ignorado: sin contenido")
            return JSONResponse({"status": "ignored", "reason": "no_content"})

        # Extraer session_id y conversation_id
        conversation_id = conversation.get("id")
        session_id = str(conversation_id) if conversation_id else "unknown"
        phone_number = sender.get("phone_number", "")
        
        # Preferir usar el número de teléfono si está disponible
        if phone_number:
            session_id = phone_number
        
        logger.info(f"✅ Mensaje válido para procesar:")
        logger.info(f"   Conversation ID: {conversation_id}")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   User message: {content}")
        logger.info(f"   Sender: {sender.get('name', 'Unknown')}")

        # Procesar con el supervisor
        logger.info(f"🤖 Enviando mensaje al supervisor...")
        response = await supervisor_agent.process_message(content, session_id)
        
        logger.info(f"✅ Respuesta del supervisor recibida ({len(response)} chars)")
        logger.info(f"   First 150 chars: {response[:150]}...")

        # Enviar respuesta a Chatwoot
        if settings.CHATWOOT_API_TOKEN and conversation_id:
            try:
                await send_message_to_chatwoot(
                    conversation_id=conversation_id,
                    message=response
                )
                logger.info(f"✅ Respuesta enviada a Chatwoot (conversation {conversation_id})")
            except Exception as e:
                logger.error(f"❌ Error enviando mensaje a Chatwoot: {e}", exc_info=True)
        else:
            logger.warning("⚠️ No se envió respuesta a Chatwoot (falta token o conversation_id)")
        
        logger.info("=" * 80)

        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "response_sent": True,
            "response": response
        })

    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO en webhook Chatwoot: {e}", exc_info=True)
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
