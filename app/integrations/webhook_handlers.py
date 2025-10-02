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
    Maneja webhooks directos de Chatwoot.
    """
    try:
        payload = await request.json()
        
        # LOG: Payload completo recibido
        logger.info("=" * 80)
        logger.info("📨 WEBHOOK CHATWOOT RECIBIDO")
        logger.info(f"Payload completo: {json.dumps(payload, indent=2)}")
        logger.info("=" * 80)

        # 1) Normalización flexible: soportar formato nativo de Chatwoot
        #    y también un formato simplificado enviado desde n8n:
        #    { mensaje, account_id, conversation_id, telefono }

        is_simple = (
            "mensaje" in payload
            or "conversation_id" in payload
            or "telefono" in payload
            or "account_id" in payload
        )

        if is_simple:
            # Construir una vista "tipo Chatwoot" a partir del formato simple
            event_type = payload.get("event") or "message_created"
            message_type = payload.get("message_type") or "incoming"
            content = payload.get("mensaje") or payload.get("content")
            conversation = {"id": payload.get("conversation_id")}
            sender = {"phone_number": payload.get("telefono")}
            account_id = payload.get("account_id")
        else:
            # Formato nativo
            event_type = payload.get("event")
            message_type = payload.get("message_type")
            content = payload.get("content")
            conversation = payload.get("conversation", {})
            sender = payload.get("sender", {})
            account = payload.get("account", {})
            account_id = account.get("id") if isinstance(account, dict) else None

        logger.info(f"Event type: {event_type}")
        
        # Validar evento
        if event_type != "message_created":
            logger.warning(f"❌ Evento ignorado: '{event_type}'")
            return JSONResponse({"status": "ignored", "reason": "not_message_created"})
        
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

        # Extraer session_id (usar conversation_id o phone_number)
        session_id = str(conversation.get("id", "unknown"))
        phone_number = sender.get("phone_number", "")
        
        # Preferir usar el número de teléfono si está disponible
        if phone_number:
            session_id = phone_number
        
        logger.info(f"✅ Mensaje válido para procesar:")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   User message: {content}")
        logger.info(f"   Sender: {sender.get('name', 'Unknown')}")

        # Procesar con el supervisor
        logger.info(f"🤖 Enviando mensaje al supervisor...")
        response = await supervisor_agent.process_message(content, session_id)
        
        logger.info(f"✅ Respuesta del supervisor recibida ({len(response)} chars)")
        logger.info(f"   First 150 chars: {response[:150]}...")
        logger.info("=" * 80)

        # 4) Intentar enviar la respuesta automáticamente a Chatwoot si hay credenciales
        try:
            chatwoot_url = os.getenv("CHATWOOT_URL") or settings.CHATWOOT_URL
            api_token = os.getenv("CHATWOOT_API_TOKEN") or settings.CHATWOOT_API_TOKEN
            resolved_account_id = (
                account_id
                or os.getenv("CHATWOOT_ACCOUNT_ID")
                or settings.CHATWOOT_ACCOUNT_ID
            )

            if chatwoot_url and api_token and resolved_account_id and conversation.get("id"):
                endpoint = f"{chatwoot_url}/api/v1/accounts/{resolved_account_id}/conversations/{conversation.get('id')}/messages"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    cw_resp = await client.post(
                        endpoint,
                        headers={"api_access_token": api_token, "Content-Type": "application/json"},
                        json={
                            "content": response,
                            "message_type": "outgoing",
                            "private": False,
                            "sender": {"type": "bot"}
                        }
                    )
                if cw_resp.status_code >= 200 and cw_resp.status_code < 300:
                    logger.info("📤 Respuesta enviada a Chatwoot correctamente")
                else:
                    logger.warning(f"No se pudo enviar a Chatwoot: {cw_resp.status_code} - {cw_resp.text[:200]}")
            else:
                logger.info("Credenciales/IDs de Chatwoot no completas; usar n8n como reenvío")
        except Exception as send_err:
            logger.error(f"Error enviando a Chatwoot: {send_err}", exc_info=True)

        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "response_sent": True,
            "response": response,
            # Eco de IDs útiles para n8n → Chatwoot
            "account_id": account_id,
            "conversation_id": conversation.get("id")
        })

    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO en webhook Chatwoot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

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