"""
Webhook handlers actualizados para el nuevo formato de Chatwoot
Incluye integración bidireccional completa con Chatwoot API
"""

from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.agents.supervisor import supervisor_agent
from app.session.session_manager import session_manager
from app.config import settings
from app.utils.logger import get_logger
import httpx
import json
from datetime import datetime

logger = get_logger(__name__)

webhook_router = APIRouter()


# ============================================================================
# MODELOS PYDANTIC PARA NUEVO FORMATO CHATWOOT
# ============================================================================

class ChatwootIncomingMessage(BaseModel):
    """Mensaje entrante desde Chatwoot en el nuevo formato"""
    mensaje: str = Field(..., description="Contenido del mensaje")
    account_id: int = Field(..., description="ID de cuenta de Chatwoot")
    conversation_id: int = Field(..., description="ID de conversación")
    telefono: str = Field(..., description="Número de teléfono del usuario")
    message_type: Optional[str] = Field(default="incoming")
    sender_id: Optional[int] = None


class ChatwootClient:
    """Cliente para interactuar con la API de Chatwoot"""
    
    def __init__(self):
        self.base_url = settings.CHATWOOT_URL or "https://app.chatwoot.com"
        self.api_token = settings.CHATWOOT_API_TOKEN
        
    async def send_message(
        self,
        account_id: int,
        conversation_id: int,
        content: str,
        message_type: str = "outgoing",
        private: bool = False
    ) -> Dict[str, Any]:
        """
        Envía un mensaje a través de la API de Chatwoot
        
        Documentación: https://developers.chatwoot.com/api-reference/messages/create-new-message
        """
        url = f"{self.base_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        
        headers = {
            "api_access_token": self.api_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": content,
            "private": private,
            "message_type": message_type,
            "sender": {"type": "bot"}
        }
        
        logger.info(f"📤 Enviando mensaje a Chatwoot - Conv: {conversation_id}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ Mensaje enviado exitosamente a Chatwoot")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Error HTTP enviando mensaje a Chatwoot: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje a Chatwoot: {e}", exc_info=True)
            raise


# Instancia global del cliente
chatwoot_client = ChatwootClient()


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@webhook_router.post("/chatwoot/new")
async def chatwoot_webhook_new_format(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook para el NUEVO formato de Chatwoot que viene desde n8n
    
    Formato esperado:
    {
        "mensaje": "texto del mensaje",
        "account_id": 6,
        "conversation_id": 1,
        "telefono": "5493815339805"
    }
    """
    try:
        raw_payload = await request.json()
        
        logger.info("=" * 80)
        logger.info("📨 WEBHOOK CHATWOOT - NUEVO FORMATO")
        logger.info(f"Payload recibido: {json.dumps(raw_payload, indent=2)}")
        logger.info("=" * 80)
        
        # Validar y parsear payload
        try:
            message_data = ChatwootIncomingMessage(**raw_payload)
        except Exception as e:
            logger.error(f"❌ Error validando payload: {e}")
            raise HTTPException(status_code=400, detail=f"Payload inválido: {str(e)}")
        
        # Extraer datos
        user_message = message_data.mensaje
        account_id = message_data.account_id
        conversation_id = message_data.conversation_id
        phone = message_data.telefono
        
        # Usar teléfono como session_id
        session_id = phone
        
        logger.info(f"✅ Mensaje válido:")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   Account: {account_id}")
        logger.info(f"   Conversation: {conversation_id}")
        logger.info(f"   Message: {user_message}")
        
        # Validar que no sea vacío
        if not user_message or not user_message.strip():
            logger.warning("❌ Mensaje vacío, ignorando")
            return JSONResponse({
                "status": "ignored",
                "reason": "empty_message"
            })
        
        # Procesar mensaje con el supervisor
        logger.info(f"🤖 Procesando con supervisor...")
        bot_response = await supervisor_agent.process_message(
            message=user_message,
            session_id=session_id
        )
        
        logger.info(f"✅ Respuesta del bot generada ({len(bot_response)} chars)")
        logger.info(f"   Primera línea: {bot_response.split(chr(10))[0][:100]}")
        
        # Enviar respuesta a Chatwoot en background
        background_tasks.add_task(
            send_chatwoot_response,
            account_id=account_id,
            conversation_id=conversation_id,
            content=bot_response
        )
        
        logger.info("=" * 80)
        
        # Responder al webhook inmediatamente
        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "account_id": account_id,
            "conversation_id": conversation_id,
            "response_queued": True,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO en webhook Chatwoot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": str(e)
            }
        )


async def send_chatwoot_response(
    account_id: int,
    conversation_id: int,
    content: str
):
    """
    Función auxiliar para enviar respuesta a Chatwoot
    Se ejecuta en background para no bloquear el webhook
    """
    try:
        await chatwoot_client.send_message(
            account_id=account_id,
            conversation_id=conversation_id,
            content=content,
            message_type="outgoing",
            private=False
        )
        logger.info(f"✅ Respuesta enviada a Chatwoot exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error enviando respuesta a Chatwoot: {e}", exc_info=True)
        # No lanzar excepción aquí porque es background task


@webhook_router.post("/chatwoot")
async def chatwoot_webhook_legacy(request: Request):
    """
    Webhook para el formato LEGACY de Chatwoot (directo sin n8n)
    Mantener por compatibilidad
    """
    try:
        payload = await request.json()
        
        logger.info("📨 WEBHOOK CHATWOOT - FORMATO LEGACY")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        event_type = payload.get("event")
        
        if event_type != "message_created":
            return JSONResponse({"status": "ignored", "reason": "not_message_created"})
        
        message_type = payload.get("message_type")
        content = payload.get("content")
        conversation = payload.get("conversation", {})
        
        if message_type != "incoming":
            return JSONResponse({"status": "ignored", "reason": "not_incoming"})
        
        if not content:
            return JSONResponse({"status": "ignored", "reason": "no_content"})
        
        session_id = str(conversation.get("id", "unknown"))
        
        # Procesar mensaje
        response = await supervisor_agent.process_message(content, session_id)
        
        logger.info(f"✅ Respuesta generada para formato legacy")
        
        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "response": response
        })
        
    except Exception as e:
        logger.error(f"Error en webhook Chatwoot legacy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@webhook_router.post("/test")
async def test_webhook(request: Request):
    """Endpoint de prueba para desarrollo"""
    try:
        payload = await request.json()
        
        session_id = payload.get("session_id", "test_session")
        message = payload.get("message", "Hola")
        
        logger.info(f"🧪 TEST - Sesión: {session_id}, Mensaje: {message}")
        
        # Procesar mensaje
        response = await supervisor_agent.process_message(message, session_id)
        
        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "user_message": message,
            "bot_response": response,
            "session_stats": session_manager.get_session_stats(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        logger.error(f"Error en test webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@webhook_router.get("/health")
async def webhook_health():
    """Health check para webhooks"""
    return {
        "status": "healthy",
        "chatwoot_configured": bool(settings.CHATWOOT_API_TOKEN),
        "chatwoot_url": settings.CHATWOOT_URL,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@webhook_router.get("/sessions")
async def get_sessions():
    """Obtener estadísticas de sesiones"""
    try:
        cleaned = session_manager.cleanup_expired_sessions()
        stats = session_manager.get_session_stats()
        stats["cleaned_sessions"] = cleaned
        
        return JSONResponse(stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@webhook_router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Limpiar una sesión específica"""
    try:
        session_manager.clear_session(session_id)
        
        return JSONResponse({
            "status": "success",
            "message": f"Sesión {session_id} limpiada",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        logger.error(f"Error limpiando sesión: {e}")
        raise HTTPException(status_code=500, detail=str(e))