# Actualizaciones del Bot Universidad Austral

## Resumen de Cambios

### 1. Integración con n8n (Reemplaza Chatwoot directo)

**Cambio principal**: El bot ahora se integra con Chatwoot y otras plataformas mediante n8n como intermediario, permitiendo mayor flexibilidad y control del flujo de mensajes.

#### Nuevo Endpoint: `/webhook/n8n`

- **Ruta**: `POST /webhook/n8n`
- **Autenticación**: Header `X-N8N-API-KEY`
- **Soporta múltiples plataformas**: Chatwoot, WhatsApp, Telegram (futuro)

#### Estructura de Mensaje desde n8n

**Formato Simplificado** (recomendado para desarrollo):
```json
{
  "source": "chatwoot",
  "session_id": "chatwoot_12345",
  "message": "Hola, quiero saber mi horario"
}
```

**Formato Completo**:
```json
{
  "event_type": "message.created",
  "source": "chatwoot",
  "timestamp": "2024-09-29T10:30:00Z",
  "session": {
    "session_id": "chatwoot_12345",
    "platform": "chatwoot"
  },
  "user": {
    "name": "Juan Pérez",
    "email": "juan.perez@example.com"
  },
  "message": {
    "content": "Hola, quiero saber mi horario",
    "message_id": "msg_abc123"
  }
}
```

**Ver documentación completa**: [N8N_MESSAGE_STRUCTURE.md](./N8N_MESSAGE_STRUCTURE.md)

#### Respuesta del Bot a n8n

```json
{
  "status": "success",
  "session_id": "chatwoot_12345",
  "response": {
    "content": "¡Hola Juan! 📚 Te muestro tu horario...",
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

---

### 2. Migración a LangChain/LangGraph v1

#### Nueva Abstracción: `LLMFactory`

Se creó una capa de abstracción completa para el manejo de LLMs:

**Ubicación**: `app/core/llm_factory.py`

**Características**:
- ✅ Abstracción completa de proveedores (OpenAI, Anthropic, Google)
- ✅ Configuración por tipo de agente
- ✅ Fallback automático a OpenAI
- ✅ Registro de proveedores customizados
- ✅ Compatible con LangChain v1

**Uso Básico**:
```python
from app.core.llm_factory import llm_factory

# Crear LLM genérico
llm = llm_factory.create()

# Crear LLM para agente específico
llm = llm_factory.create_for_agent("supervisor")
llm = llm_factory.create_for_agent("financial")
```

**Uso Avanzado**:
```python
# Especificar proveedor y modelo
llm = llm_factory.create(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    temperature=0.2
)

# Registrar proveedor customizado
class CustomProvider(LLMProvider):
    def create_llm(self, **kwargs):
        # Tu implementación
        pass

llm_factory.register_provider("custom", CustomProvider())
```

#### Actualización del Supervisor

**Antes**:
```python
def _get_llm(self):
    if "gpt" in model:
        return ChatOpenAI(...)
    elif "claude" in model:
        return ChatAnthropic(...)
    # ... más código duplicado
```

**Después**:
```python
def __init__(self):
    self.llm = llm_factory.create_for_agent("supervisor")
```

#### Configuraciones por Agente

Cada agente tiene su configuración optimizada:

| Agente | Temperature | Razón |
|--------|-------------|-------|
| Supervisor | 0.0 | Routing determinista |
| Academic | 0.3 | Creatividad moderada |
| Financial | 0.0 | Precisión en datos numéricos |
| Policies | 0.2 | Precisión con flexibilidad |
| Calendar | 0.1 | Precisión en fechas |

---

### 3. Compatibilidad con LangChain v1

#### Actualizaciones de Dependencias

**requirements.txt actualizado**:
```txt
# LangGraph y LangChain - v1 compatible
langgraph==0.2.50
langgraph-checkpoint-sqlite==2.0.0
langchain==0.3.10
langchain-core==0.3.26
langchain-openai==0.3.33
langchain-anthropic==0.3.20
langchain-google-genai==2.0.8
```

#### Cambios en Imports

**Antes**:
```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
# Imports repetidos en múltiples archivos
```

**Después**:
```python
from app.core.llm_factory import llm_factory
from langchain_core.language_models import BaseChatModel
```

#### StateGraph (Compatible v1)

El uso de `StateGraph` se mantiene compatible con LangGraph 0.2.x y preparado para v1:

```python
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", self._supervisor_node)
workflow.add_edge(START, "authentication")
app = workflow.compile(checkpointer=memory)
```

---

### 4. Arquitectura de Archivos

#### Nuevos Archivos

```
app/
├── core/                          # NUEVO
│   ├── __init__.py               # Exports de abstracciones
│   └── llm_factory.py            # Factory de LLMs
├── integrations/
│   └── webhook_handlers.py       # Actualizado con /webhook/n8n
N8N_MESSAGE_STRUCTURE.md          # NUEVO - Documentación de n8n
ACTUALIZACIONES.md                # NUEVO - Este archivo
```

#### Estructura Completa

```
universidad-austral-bot/
├── app/
│   ├── agents/
│   │   ├── supervisor.py         # Actualizado: usa llm_factory
│   │   ├── academic_agent.py
│   │   ├── financial_agent.py
│   │   ├── policies_agent.py
│   │   └── calendar_agent.py
│   ├── core/                      # NUEVO
│   │   ├── __init__.py
│   │   └── llm_factory.py
│   ├── integrations/
│   │   └── webhook_handlers.py   # Actualizado: endpoint /webhook/n8n
│   ├── tools/
│   │   ├── academic_tools.py
│   │   ├── financial_tools.py
│   │   └── n8n_manager.py
│   ├── utils/
│   │   └── logger.py
│   ├── session/
│   │   └── session_manager.py
│   ├── config.py                  # Actualizado: N8N_API_KEY
│   └── main.py
├── N8N_MESSAGE_STRUCTURE.md       # NUEVO
├── ACTUALIZACIONES.md             # NUEVO
├── requirements.txt               # Actualizado para v1
└── .env                           # Agregar N8N_API_KEY
```

---

### 5. Variables de Entorno Necesarias

Agregar a `.env`:

```bash
# n8n Integration (NUEVO)
N8N_WEBHOOK_URL=http://localhost:5678/webhook
N8N_API_KEY=your-n8n-api-key
N8N_WEBHOOK_SECRET=your-webhook-secret

# Existentes
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

---

### 6. Flujo de Integración con n8n

```
┌─────────────┐      ┌──────────┐      ┌────────────┐      ┌──────────┐
│  Chatwoot   │─────▶│   n8n    │─────▶│    Bot     │─────▶│   n8n    │
│  (Usuario)  │      │ Transform│      │ /webhook/  │      │  Envía   │
│             │      │          │      │    n8n     │      │  Resp.   │
└─────────────┘      └──────────┘      └────────────┘      └──────────┘
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │  Supervisor  │
                                       │   LangGraph  │
                                       └──────────────┘
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
                  ┌──────────┐        ┌──────────┐         ┌──────────┐
                  │ Academic │        │Financial │         │ Calendar │
                  │  Agent   │        │  Agent   │         │  Agent   │
                  └──────────┘        └──────────┘         └──────────┘
```

---

### 7. Endpoints Disponibles

| Endpoint | Método | Propósito | Estado |
|----------|--------|-----------|--------|
| `/webhook/n8n` | POST | **Principal** - Mensajes desde n8n | ✅ Nuevo |
| `/webhook/chatwoot` | POST | Legacy - Directo desde Chatwoot | ⚠️ Deprecado |
| `/webhook/whatsapp` | POST | Legacy - Directo desde WhatsApp | ⚠️ Deprecado |
| `/webhook/test` | POST | Testing y desarrollo | ✅ Activo |
| `/health` | GET | Health check | ✅ Activo |
| `/webhook/sessions` | GET | Estadísticas de sesiones | ✅ Activo |

**Recomendación**: Usar `/webhook/n8n` para todas las integraciones nuevas.

---

### 8. Testing

#### Test del Endpoint n8n

```bash
# Formato simplificado
curl -X POST http://localhost:8000/webhook/n8n \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: your-api-key" \
  -d '{
    "source": "chatwoot",
    "session_id": "test_123",
    "message": "Hola, quiero saber mi horario"
  }'
```

```bash
# Formato completo
curl -X POST http://localhost:8000/webhook/n8n \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: your-api-key" \
  -d '{
    "event_type": "message.created",
    "source": "chatwoot",
    "session": {
      "session_id": "chatwoot_12345",
      "platform": "chatwoot"
    },
    "user": {
      "name": "Juan Pérez"
    },
    "message": {
      "content": "Cuánto debo?"
    }
  }'
```

#### Test del LLMFactory

```python
# test_llm_factory.py
from app.core.llm_factory import llm_factory

# Test creación básica
llm = llm_factory.create()
response = llm.invoke("Hola, ¿cómo estás?")
print(response.content)

# Test por agente
supervisor_llm = llm_factory.create_for_agent("supervisor")
financial_llm = llm_factory.create_for_agent("financial")

# Test proveedor específico
anthropic_llm = llm_factory.create(provider="anthropic")
```

---

### 9. Mejoras de Abstracción

#### Antes (Código Duplicado)

Cada archivo tenía su propia lógica de selección de LLM:

```python
# En supervisor.py
if "gpt" in model:
    return ChatOpenAI(...)
elif "claude" in model:
    return ChatAnthropic(...)

# En academic_agent.py
if "gpt" in model:
    return ChatOpenAI(...)
elif "claude" in model:
    return ChatAnthropic(...)
```

#### Después (DRY - Don't Repeat Yourself)

```python
# En todos los archivos
from app.core.llm_factory import llm_factory

llm = llm_factory.create_for_agent("agent_type")
```

**Beneficios**:
- ✅ Código centralizado
- ✅ Fácil de mantener
- ✅ Agregar nuevos proveedores sin tocar agentes
- ✅ Testing más simple
- ✅ Configuración consistente

---

### 10. Migración Paso a Paso

Para proyectos existentes que quieran adoptar estas actualizaciones:

#### Paso 1: Actualizar Dependencias
```bash
pip install -r requirements.txt
```

#### Paso 2: Agregar Variables de Entorno
```bash
# Agregar a .env
N8N_API_KEY=your-api-key
N8N_WEBHOOK_URL=http://localhost:5678/webhook
```

#### Paso 3: Actualizar Imports en Agentes
```python
# Reemplazar
from langchain_openai import ChatOpenAI

# Con
from app.core.llm_factory import llm_factory
```

#### Paso 4: Actualizar Inicialización de LLM
```python
# Reemplazar
self.llm = ChatOpenAI(model="gpt-4o-mini", ...)

# Con
self.llm = llm_factory.create_for_agent("agent_name")
```

#### Paso 5: Configurar n8n Workflow
1. Crear webhook trigger en n8n
2. Agregar Function Node para transformar mensaje
3. HTTP Request a `/webhook/n8n`
4. Procesar respuesta
5. Enviar a Chatwoot/WhatsApp

---

### 11. Próximos Pasos (Roadmap)

- [ ] Implementar rate limiting por session en n8n webhook
- [ ] Agregar métricas de performance por proveedor de LLM
- [ ] Crear tests unitarios para LLMFactory
- [ ] Implementar circuit breaker para LLMs
- [ ] Agregar soporte para streaming responses
- [ ] Documentar workflows de n8n específicos

---

### 12. Recursos Adicionales

- [Documentación LangChain v1](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [Documentación LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)
- [N8N Documentation](https://docs.n8n.io/)
- [Estructura de Mensajes n8n](./N8N_MESSAGE_STRUCTURE.md)

---

## Preguntas Frecuentes

### ¿Por qué usar n8n en lugar de conectar directo a Chatwoot?

n8n actúa como capa de orquestación que permite:
- Transformar mensajes de diferentes plataformas a un formato estándar
- Agregar lógica de negocio sin modificar el bot
- Routing condicional
- Logging y monitoring centralizado
- Facilitar testing con webhooks simulados

### ¿Puedo seguir usando el endpoint `/webhook/chatwoot`?

Sí, pero está deprecado. Se recomienda migrar a `/webhook/n8n` para aprovechar las nuevas funcionalidades.

### ¿Cómo agrego un nuevo proveedor de LLM?

```python
from app.core.llm_factory import LLMProvider, llm_factory

class MyCustomProvider(LLMProvider):
    def get_default_model(self) -> str:
        return "my-model"

    def create_llm(self, **kwargs):
        # Tu implementación
        return MyCustomLLM(**kwargs)

# Registrar
llm_factory.register_provider("custom", MyCustomProvider())

# Usar
llm = llm_factory.create(provider="custom")
```

---

## Contacto y Soporte

Para reportar issues o sugerencias sobre estas actualizaciones, contactar al equipo de desarrollo.