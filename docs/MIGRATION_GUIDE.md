# 📋 Guía de Migración - Universidad Austral Bot v2.0

## 🎯 Resumen de Cambios

Esta migración moderniza completamente la arquitectura del bot utilizando las últimas versiones de LangChain, LangGraph y LangSmith (2024-2025).

### Cambios Principales

1. **Arquitectura LangGraph**: Nuevo sistema de supervisor con agentes especializados
2. **Estructura modular**: Organización según mejores prácticas
3. **Tools n8n**: Preparación completa para integración con webhooks
4. **Observabilidad**: Integración con LangSmith para monitoreo
5. **Configuración moderna**: Uso de Pydantic v2 settings

## 🏗️ Nueva Estructura

```
universidad-austral-bot/
├── app/                          # Código principal modernizado
│   ├── main.py                   # FastAPI con nueva estructura
│   ├── config.py                 # Configuración con Pydantic v2
│   │
│   ├── agents/                   # Agentes LangGraph
│   │   ├── supervisor.py         # Supervisor LangGraph principal
│   │   ├── academic_agent.py     # Agente académico modernizado
│   │   ├── financial_agent.py    # Agente financiero modernizado
│   │   ├── policies_agent.py     # Agente de políticas modernizado
│   │   └── calendar_agent.py     # Agente de calendario modernizado
│   │
│   ├── tools/                    # Herramientas n8n
│   │   ├── n8n_manager.py        # Gestor central de webhooks
│   │   ├── academic_tools.py     # Tools académicas
│   │   ├── financial_tools.py    # Tools financieras
│   │   ├── policies_tools.py     # Tools de políticas
│   │   └── calendar_tools.py     # Tools de calendario
│   │
│   ├── integrations/             # Integraciones externas
│   │   └── webhook_handlers.py   # Manejadores de webhooks
│   │
│   ├── session/                  # Gestión de sesiones
│   │   └── session_manager.py    # Gestor de sesiones modernizado
│   │
│   └── utils/                    # Utilidades
│       └── logger.py             # Sistema de logging
│
├── n8n_workflows/                # Workflows de n8n listos
│   ├── academic_tools.json       # Workflow académico
│   └── financial_tools.json      # Workflow financiero
│
└── requirements.txt              # Dependencias actualizadas
```

## 🔧 Pasos de Migración

### 1. Backup del Proyecto Actual

```bash
# Crear backup
cp -r universidad-austral-bot universidad-austral-bot-backup
```

### 2. Actualizar Dependencias

```bash
# Instalar nuevas dependencias
pip install -r requirements.txt
```

### 3. Migrar Variables de Entorno

Actualizar `.env` con las nuevas variables:

```bash
# LangSmith para observabilidad
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=universidad-austral-bot

# n8n Webhooks
N8N_WEBHOOK_BASE_URL=https://n8n.tucbbs.com.ar/webhook
N8N_API_KEY=your_n8n_api_key

# Configuración mejorada
SESSION_TTL_MINUTES=60
LOG_LEVEL=INFO
```

### 4. Configurar n8n Workflows

1. Importar workflows desde `n8n_workflows/`
2. Configurar credenciales de base de datos
3. Activar webhooks

### 5. Actualizar Punto de Entrada

El nuevo punto de entrada es `app/main.py`:

```bash
# Desarrollo
uvicorn app.main:app --reload

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🆕 Nuevas Características

### LangGraph Supervisor

- **Orquestación inteligente**: El supervisor decide qué agente usar
- **Estado compartido**: Información persiste entre agentes
- **Checkpointing**: Capacidad de resume desde fallos
- **Escalación automática**: Derivación a humanos cuando es necesario

### Tools n8n Mejoradas

- **Webhooks preparados**: Estructura lista para copy-paste
- **Documentación completa**: Cada tool tiene specs detalladas
- **Mock responses**: Desarrollo sin n8n
- **Error handling**: Manejo robusto de errores

### Observabilidad con LangSmith

- **Tracing completo**: Visibilidad de cada step del agente
- **Métricas automáticas**: Latencia, costos, success rate
- **Debug facilitado**: Logs estructurados y detallados

## 🔄 Cambios en la API

### Endpoints Actualizados

| Anterior | Nuevo | Descripción |
|----------|--------|-------------|
| `/webhook/test` | `/webhook/test` | Mantenido, estructura mejorada |
| N/A | `/webhook/sessions` | Nuevo: estadísticas de sesiones |
| N/A | `/webhook/sessions/{id}` | Nuevo: limpiar sesión específica |

### Estructura de Respuesta

Las respuestas ahora incluyen más metadata:

```json
{
  "status": "success",
  "session_id": "test_session",
  "user_message": "Hola",
  "bot_response": "¡Hola! Para ayudarte...",
  "session_stats": {
    "active_sessions": 5,
    "authenticated_sessions": 3
  }
}
```

## 🧪 Testing de la Migración

### 1. Test Básico

```bash
curl -X POST http://localhost:8000/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "Hola"}'
```

### 2. Test de Autenticación

```bash
curl -X POST http://localhost:8000/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_auth", "message": "12345678"}'
```

### 3. Test de Consultas

```bash
# Consulta académica
curl -X POST http://localhost:8000/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_auth", "message": "¿Cuándo tengo clases?"}'
```

### 4. Verificar n8n

```bash
# Test de webhook académico
curl -X POST https://n8n.tucbbs.com.ar/webhook/consultas-horarios \
  -H "Content-Type: application/json" \
  -d '{"data": {"alumno_id": 1}}'
```

## 📊 Monitoreo y Observabilidad

### LangSmith Dashboard

1. Ir a [LangSmith](https://smith.langchain.com)
2. Crear proyecto "universidad-austral-bot"
3. Configurar API key en `.env`
4. Ver traces en tiempo real

### Logs Locales

```bash
# Ver logs en tiempo real
tail -f app.log

# Logs por nivel
grep "ERROR" app.log
grep "INFO" app.log
```

### Métricas de Sesiones

```bash
# Estadísticas actuales
curl http://localhost:8000/webhook/sessions
```

## 🚨 Troubleshooting

### Error: ModuleNotFoundError

```bash
# Reinstalar dependencias
pip install --force-reinstall -r requirements.txt
```

### Error: n8n webhooks no responden

```bash
# Verificar n8n está corriendo
curl http://localhost:5678/healthz

# Verificar workflows activos
curl http://localhost:5678/api/v1/workflows
```

### Error: LangSmith no está trackeando

```bash
# Verificar variables de entorno
echo $LANGCHAIN_TRACING_V2
echo $LANGCHAIN_API_KEY
```

## 🔮 Próximos Pasos

1. **Configurar n8n en producción**: Importar workflows reales
2. **Integrar base de datos real**: Conectar PostgreSQL/Supabase
3. **Deploy con Docker**: Usar docker-compose actualizado
4. **Configurar alertas**: Monitoring en producción
5. **Tests automatizados**: Suite de tests con pytest

## 📞 Soporte

- **Documentación**: `/docs` folder
- **Issues**: GitHub Issues
- **Logs**: `app.log` file

La migración está completa. El sistema ahora utiliza la arquitectura más moderna de LangChain/LangGraph con preparación completa para n8n webhooks.