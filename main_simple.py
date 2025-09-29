"""
Universidad Austral Bot - Punto de entrada simplificado
"""

from fastapi import FastAPI, Request
import uvicorn
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Universidad Austral Bot",
    description="Sistema de agentes para atención universitaria",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Universidad Austral Bot funcionando"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Universidad Austral Bot"}

@app.post("/webhook/chatwoot")
async def chatwoot_webhook(request: Request):
    """
    Webhook para recibir mensajes de Chatwoot
    """
    try:
        # Obtener el cuerpo del request
        body = await request.body()
        
        # Intentar parsear como JSON
        try:
            data = await request.json()
            logger.info(f"Webhook recibido desde Chatwoot: {data}")
            
            # Extraer información básica si existe
            event = data.get("event", "unknown")
            content = data.get("content", "")
            message_type = data.get("message_type", "")
            
            logger.info(f"Evento: {event}, Tipo: {message_type}, Contenido: {content}")
            
            return {
                "status": "success",
                "message": "Webhook recibido correctamente",
                "received": {
                    "event": event,
                    "message_type": message_type
                }
            }
        except Exception as json_error:
            logger.warning(f"No se pudo parsear JSON: {json_error}")
            logger.info(f"Body raw: {body}")
            
            return {
                "status": "success",
                "message": "Webhook recibido (sin parsear JSON)"
            }
            
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    logger.info("Universidad Austral Bot - Iniciando servidor...")
    logger.info("API disponible en: http://0.0.0.0:8000")
    logger.info("Webhook: http://0.0.0.0:8000/webhook/chatwoot")
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
