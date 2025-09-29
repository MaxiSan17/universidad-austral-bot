"""
Universidad Austral Bot - Con agente básico (Testing Mode)
"""

from fastapi import FastAPI, Request
import uvicorn
import logging
import httpx
import os
from anthropic import Anthropic

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Universidad Austral Bot",
    description="Sistema de agentes para atención universitaria",
    version="1.0.0"
)

# Cliente de Anthropic
anthropic_client = None
if os.getenv("ANTHROPIC_API_KEY"):
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Cliente HTTP para Chatwoot
http_client = httpx.AsyncClient(timeout=30.0)

async def send_message_to_chatwoot(conversation_id: int, content: str):
    """Enviar mensaje de vuelta a Chatwoot"""
    try:
        chatwoot_url = os.getenv("CHATWOOT_URL", "https://app.chatwoot.com")
        account_id = os.getenv("CHATWOOT_ACCOUNT_ID")
        api_token = os.getenv("CHATWOOT_API_TOKEN")
        
        if not all([account_id, api_token]):
            logger.warning("Faltan credenciales de Chatwoot - modo testing")
            return False
        
        url = f"{chatwoot_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        
        response = await http_client.post(
            url,
            headers={"api_access_token": api_token},
            json={
                "content": content,
                "message_type": "outgoing",
                "private": False
            }
        )
        
        if response.status_code == 200:
            logger.info(f"Mensaje enviado a Chatwoot: {content[:50]}...")
            return True
        else:
            logger.error(f"Error enviando a Chatwoot: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error en send_message_to_chatwoot: {e}")
        return False

async def process_with_agent(user_message: str) -> str:
    """Procesar mensaje con Claude"""
    try:
        if not anthropic_client:
            return "Bot configurado incorrectamente. Falta ANTHROPIC_API_KEY."
        
        # Prompt del sistema
        system_prompt = """Sos un asistente virtual de la Universidad Austral en Argentina.

Tu trabajo es ayudar a estudiantes y profesores con consultas sobre:
- Horarios de clases
- Inscripciones
- Información general de la universidad
- Calendario académico

Respondé de forma amigable, usando el voseo argentino (vos, tenés, podés).
Si no sabés algo, decilo claramente y sugerí contactar a la secretaría.
Mantené las respuestas breves y claras."""

        # Llamar a Claude
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        response_text = message.content[0].text
        logger.info(f"Respuesta de Claude: {response_text[:100]}...")
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error procesando con agente: {e}")
        return f"Disculpá, tuve un problema técnico: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Universidad Austral Bot funcionando"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Universidad Austral Bot",
        "agent": "claude" if anthropic_client else "not_configured"
    }

@app.post("/webhook/chatwoot")
async def chatwoot_webhook(request: Request):
    """Webhook para recibir mensajes de Chatwoot"""
    try:
        data = await request.json()
        logger.info(f"Webhook recibido: {data}")
        
        # Extraer información del mensaje
        event = data.get("event")
        message_type = data.get("message_type")
        content = data.get("content", "")
        conversation = data.get("conversation", {})
        conversation_id = conversation.get("id")
        
        # Solo procesar mensajes entrantes
        if event == "message_created" and message_type == "incoming" and content:
            logger.info(f"Procesando mensaje: {content}")
            
            # Procesar con el agente
            response = await process_with_agent(content)
            
            # Intentar enviar respuesta a Chatwoot
            chatwoot_sent = False
            if conversation_id:
                chatwoot_sent = await send_message_to_chatwoot(conversation_id, response)
            
            # Retornar respuesta completa (útil para testing con Postman)
            return {
                "status": "success",
                "message": "Mensaje procesado",
                "user_message": content,
                "bot_response": response,
                "sent_to_chatwoot": chatwoot_sent
            }
        else:
            logger.info(f"Mensaje ignorado - Event: {event}, Type: {message_type}")
            return {
                "status": "ignored",
                "reason": "Not an incoming message"
            }
            
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    logger.info("Universidad Austral Bot - Iniciando servidor con agente...")
    logger.info("API disponible en: http://0.0.0.0:8000")
    logger.info("Webhook: http://0.0.0.0:8000/webhook/chatwoot")
    
    uvicorn.run(
        "main_with_agent:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
