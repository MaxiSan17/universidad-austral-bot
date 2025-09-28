from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
from app.agents.supervisor import supervisor_agent
from app.session.session_manager import session_manager
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)

webhook_router = APIRouter()

@webhook_router.post("/chatwoot")
async def chatwoot_webhook(request: Request):
    """Maneja webhooks de Chatwoot"""
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
        contact = conversation.get("contact", {})

        logger.info(f"Mensaje recibido de Chatwoot - Sesión: {session_id}")

        # Procesar mensaje con el supervisor
        response = await supervisor_agent.process_message(user_message, session_id)

        # Enviar respuesta de vuelta a Chatwoot (aquí irían las llamadas a la API de Chatwoot)
        # Por ahora solo loggeamos la respuesta
        logger.info(f"Respuesta generada para sesión {session_id}: {response[:100]}...")

        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "response_sent": True
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