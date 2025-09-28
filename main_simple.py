"""
Universidad Austral Bot - Punto de entrada simplificado
"""

from fastapi import FastAPI
import uvicorn

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
async def chatwoot_webhook(request: dict):
    # Por ahora solo devolver confirmación
    return {"status": "received", "message": "Webhook funcionando"}

if __name__ == "__main__":
    print("Universidad Austral Bot - Iniciando servidor...")
    print("API disponible en: http://localhost:8000")
    print("Webhook: http://localhost:8000/webhook/chatwoot")
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
