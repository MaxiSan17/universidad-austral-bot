# Nodo n8n para Manejo de Streaming (Referencia)

## Descripción
Este documento describe la configuración del nodo n8n que recibe mensajes del backend FastAPI y los envía a Chatwoot con delay para simular escritura progresiva.

## Flujo de Datos
```
WhatsApp → n8n (recibir) → FastAPI (webhook) → n8n (callback) → Chatwoot → WhatsApp
                                    ↓
                            Message Queue + Debouncing (2 seg)
                                    ↓
                            LLM Streaming (1-3 seg)
                                    ↓
                            Respuesta completa
```

## Implementación Actual: Backend Maneja Todo

Con la implementación de **debouncing** y **streaming**, el backend FastAPI se encarga de:

1. **Recibir el mensaje** desde n8n
2. **Agregarlo a la message queue** con debouncing de 2 segundos
3. **Responder inmediatamente** a n8n con status "queued"
4. **Esperar 2 segundos** sin nuevos mensajes
5. **Procesar con streaming** usando LangGraph
6. **Enviar respuesta directamente a Chatwoot**

### Respuesta Inmediata del Backend

Cuando n8n envía un mensaje al webhook `/n8n`, recibe esta respuesta inmediata:

```json
{
  "status": "queued",
  "session_id": "+549...",
  "message": "Mensaje agregado a cola de procesamiento",
  "timestamp": "2025-10-17T..."
}
```

### Nodo n8n Simplificado

El workflow de n8n queda así:

1. **Nodo 1: Webhook Trigger (WhatsApp)**
   - Recibe mensaje desde WhatsApp/Chatwoot
   - Extrae: teléfono, mensaje, conversation_id

2. **Nodo 2: HTTP Request - Enviar a FastAPI**
   - URL: `http://university-agent:8000/webhooks/n8n`
   - Method: POST
   - Body:
     ```json
     {
       "session_id": "{{ $json.telefono }}",
       "message": "{{ $json.mensaje }}",
       "conversation_id": "{{ $json.conversation_id }}",
       "source": "chatwoot"
     }
     ```

3. **Nodo 3: FIN**
   - n8n termina aquí
   - El backend maneja el resto (debouncing + streaming + envío a Chatwoot)

## Ventajas de Esta Arquitectura

### 1. Debouncing Automático
- **Problema resuelto**: Múltiples mensajes rápidos ("Hola" + "Quiero mis horarios")
- **Solución**: Se juntan en uno solo y se procesan con contexto completo
- **Configuración**: 2 segundos de espera (configurable en `MESSAGE_DEBOUNCE_SECONDS`)

### 2. Streaming Transparente
- **El usuario ve "escribiendo..."** desde los primeros tokens
- **Backend usa `astream_events()`** para capturar tokens en tiempo real
- **LangSmith registra todo** el flujo de tokens para debugging

### 3. Sin Polling/Webhooks Adicionales
- **n8n no necesita esperar** la respuesta procesada
- **Backend envía directamente a Chatwoot** usando la API
- **Menos complejidad** en el workflow de n8n

## Configuración del Backend

### Variables de Entorno Necesarias

```bash
# Message Debouncing
MESSAGE_DEBOUNCE_SECONDS=2.0

# LLM Streaming
LLM_STREAMING_ENABLED=true

# LangSmith (Opcional - para debugging)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=universidad-austral-bot

# Chatwoot (Para envío de respuestas)
CHATWOOT_URL=https://app.chatwoot.com
CHATWOOT_API_TOKEN=tu-token-aqui
CHATWOOT_ACCOUNT_ID=tu-account-id
```

## Logs para Monitoreo

El backend genera logs detallados para seguimiento:

### 1. Llegada de Mensaje
```
📥 Mensaje agregado a queue [+549...]. Total en cola: 1
```

### 2. Debouncing en Acción
Si llega otro mensaje rápido:
```
⏱️ Timer cancelado - esperando más mensajes [+549...]
📥 Mensaje agregado a queue [+549...]. Total en cola: 2
```

### 3. Procesamiento
Después de 2 segundos sin mensajes nuevos:
```
✅ Debounce completado [+549...]. Procesando 2 mensaje(s)
🤖 Procesando mensaje combinado para [+549...]: Hola
Quiero mis horarios
```

### 4. Streaming
Durante el procesamiento:
```
🔤 Token: ¡Hola
🔤 Token:  Juan
🔤 Token: !
...
✅ Nodo completado: authentication
✅ Nodo completado: supervisor
✅ Nodo completado: academic
```

### 5. Envío a Chatwoot
```
✅ Respuesta enviada a Chatwoot (conversation 12345)
```

## Alternativa: Streaming Progresivo a WhatsApp (Futura)

Si en el futuro se quiere enviar texto progresivamente a WhatsApp (como ChatGPT), se puede:

1. **Modificar `_process_message_callback`** para enviar chunks a n8n
2. **Agregar endpoint SSE** en FastAPI para eventos en tiempo real
3. **n8n escucha SSE** y envía cada chunk a Chatwoot

### Ejemplo de Implementación Futura

```python
# En webhook_handlers.py
async def _process_message_callback(session_id: str, combined_message: str):
    # Streaming progresivo
    async for event in supervisor_agent.app.astream_events(...):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content

            # Enviar chunk a n8n/Chatwoot
            await send_chunk_to_chatwoot(
                conversation_id=session.conversation_id,
                chunk=chunk,
                is_final=False
            )

    # Marcar como final
    await send_chunk_to_chatwoot(
        conversation_id=session.conversation_id,
        chunk="",
        is_final=True
    )
```

## Testing Manual

### Test 1: Debouncing
```bash
# Enviar 2 mensajes rápidos desde WhatsApp:
1. "Hola"
2. "Quiero mis horarios" (enviar inmediatamente)

# Resultado esperado:
- Backend junta ambos mensajes
- Responde UNA sola vez con contexto completo
- Logs muestran: "Procesando 2 mensaje(s)"
```

### Test 2: Streaming
```bash
# Enviar mensaje desde WhatsApp:
"¿Cuándo tengo clase?"

# Resultado esperado:
- WhatsApp muestra "escribiendo..." inmediatamente
- Respuesta aparece progresivamente (streaming)
- LangSmith muestra trace completo del flujo
```

### Test 3: LangSmith Tracing
```bash
# 1. Configurar LANGCHAIN_TRACING_V2=true
# 2. Enviar mensaje de prueba
# 3. Ir a https://smith.langchain.com
# 4. Buscar trace con tag "session:+549..."

# Debe mostrar:
- authentication node
- supervisor node
- academic/calendar/financial node
- Todos los tokens streameados
```

## Troubleshooting

### Problema: Mensajes duplicados
**Causa**: Debouncing no está funcionando
**Solución**: Verificar logs - debe aparecer "Timer cancelado"
**Verificar**: `MESSAGE_DEBOUNCE_SECONDS` en .env

### Problema: No aparece "escribiendo..."
**Causa**: Streaming deshabilitado
**Solución**: Verificar `LLM_STREAMING_ENABLED=true`
**Verificar**: Logs deben mostrar "🔤 Token: ..."

### Problema: No hay traces en LangSmith
**Causa**: Variables de entorno mal configuradas
**Solución**: Verificar `LANGCHAIN_TRACING_V2=true` y API key válida
**Verificar**: Logs deben mostrar "✅ LangSmith tracing habilitado"

### Problema: Respuesta no llega a Chatwoot
**Causa**: Token de Chatwoot inválido
**Solución**: Verificar `CHATWOOT_API_TOKEN` y `CHATWOOT_ACCOUNT_ID`
**Verificar**: Logs deben mostrar "✅ Respuesta enviada a Chatwoot"

## Métricas de Performance

### Antes de Implementación
- **Tiempo de respuesta**: 3-5 segundos sin feedback
- **Mensajes múltiples**: Respuestas duplicadas
- **Debugging**: Solo logs de consola

### Después de Implementación
- **Debouncing**: 2 segundos de espera (configurable)
- **Streaming visible**: Usuario ve actividad desde segundo 1
- **Respuesta única**: Contexto completo
- **Observabilidad**: Traces completos en LangSmith

## Referencias

- **FastAPI Webhook**: `app/integrations/webhook_handlers.py`
- **Message Queue**: `app/session/session_manager.py` (clase `MessageQueue`)
- **Supervisor Streaming**: `app/agents/supervisor.py` (método `process_message_stream`)
- **Configuración**: `app/core/config.py` + `.env`
