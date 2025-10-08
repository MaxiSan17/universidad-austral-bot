# Estructura de Mensajes n8n

Este documento define la estructura de mensajes que n8n debe enviar al bot de la Universidad Austral.

## Webhook desde n8n (POST /webhook/n8n)

### Mensaje Entrante desde Chatwoot vía n8n

```json
{
  "event_type": "message.created",
  "source": "chatwoot",
  "timestamp": "2024-09-29T10:30:00Z",
  "session": {
    "session_id": "chatwoot_12345",
    "conversation_id": "67890",
    "platform": "chatwoot",
    "inbox_id": "1"
  },
  "user": {
    "contact_id": "54321",
    "name": "Juan Pérez",
    "email": "juan.perez@example.com",
    "phone": "+5491123456789",
    "custom_attributes": {}
  },
  "message": {
    "content": "Hola, quiero saber mi horario",
    "message_id": "msg_abc123",
    "message_type": "incoming",
    "content_type": "text",
    "attachments": []
  },
  "context": {
    "conversation_status": "open",
    "agent_assigned": null,
    "tags": [],
    "priority": "medium"
  }
}
```

### Estructura Simplificada (Mínimo Requerido)

```json
{
  "source": "chatwoot",
  "session_id": "chatwoot_12345",
  "message": "Hola, quiero saber mi horario",
  "user": {
    "name": "Juan Pérez"
  }
}
```

### Mensaje de WhatsApp vía n8n

```json
{
  "event_type": "message.received",
  "source": "whatsapp",
  "timestamp": "2024-09-29T10:30:00Z",
  "session": {
    "session_id": "whatsapp_5491123456789",
    "platform": "whatsapp",
    "phone_number": "+5491123456789"
  },
  "user": {
    "phone": "+5491123456789",
    "name": "María González",
    "profile_name": "María"
  },
  "message": {
    "content": "Cuánto debo?",
    "message_id": "wamid.xyz123",
    "content_type": "text",
    "attachments": []
  }
}
```

## Respuesta del Bot hacia n8n (para reenvío a Chatwoot/WhatsApp)

```json
{
  "status": "success",
  "session_id": "chatwoot_12345",
  "response": {
    "content": "¡Hola Juan! 📚 Te muestro tu horario para esta semana...",
    "message_type": "text",
    "metadata": {
      "confidence_score": 0.9,
      "agent_used": "academic",
      "escalation_required": false
    }
  },
  "timestamp": "2024-09-29T10:30:05Z"
}
```

## Integración con n8n Workflows

### Flujo Típico

1. **Chatwoot → n8n**: Chatwoot envía webhook a n8n cuando llega un mensaje
2. **n8n → Bot**: n8n transforma y envía mensaje con estructura estandarizada
3. **Bot → n8n**: Bot procesa y devuelve respuesta
4. **n8n → Chatwoot**: n8n reenvía respuesta a Chatwoot usando su API

### Configuración en n8n

El workflow de n8n debe:

1. **Webhook Trigger**: Recibir eventos de Chatwoot
2. **Function Node**: Transformar a estructura estandarizada
3. **HTTP Request**: Enviar a `POST https://tu-bot.com/webhook/n8n`
4. **Function Node**: Procesar respuesta del bot
5. **Chatwoot Node**: Enviar respuesta al usuario

### Ejemplo de Transformación en n8n (Function Node)

```javascript
// Transformar mensaje de Chatwoot a estructura del bot
const chatwootData = $input.item.json;

return {
  source: "chatwoot",
  session_id: `chatwoot_${chatwootData.conversation.id}`,
  message: chatwootData.content,
  user: {
    name: chatwootData.sender?.name || "Usuario",
    email: chatwootData.conversation?.contact_inbox?.source_id
  },
  timestamp: new Date().toISOString()
};
```

## Tipos de Eventos

### event_type posibles:

- `message.created` - Nuevo mensaje del usuario
- `conversation.opened` - Nueva conversación
- `conversation.resolved` - Conversación resuelta
- `agent.assigned` - Agente humano asignado

### source posibles:

- `chatwoot` - Desde Chatwoot
- `whatsapp` - Desde WhatsApp Business
- `telegram` - Desde Telegram (futuro)
- `webchat` - Desde chat web directo

## Validación de Mensajes

El bot validará:

1. Campo `source` presente
2. Campo `session_id` presente y único
3. Campo `message` con contenido no vacío
4. Timestamp en formato ISO 8601

## Manejo de Errores

Respuesta de error del bot:

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_MESSAGE_FORMAT",
    "message": "Missing required field: session_id",
    "details": {}
  },
  "timestamp": "2024-09-29T10:30:05Z"
}
```

## Seguridad

- El endpoint `/webhook/n8n` debe validar el origin de n8n
- Usar API key en headers: `X-N8N-API-KEY`
- Validar firma de webhook si está configurada
- Rate limiting por IP/session

## Variables de Entorno Requeridas

```bash
N8N_WEBHOOK_URL=https://n8n.tucbbs.com.ar/webhook
N8N_API_KEY=your-n8n-api-key
N8N_WEBHOOK_SECRET=your-webhook-secret
```