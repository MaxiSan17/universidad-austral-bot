# 🎓 Universidad Austral Bot - Sistema Evolucionado

Sistema de agentes jerárquicos con LangGraph Supervisor para atención estudiantil de la Universidad Austral.

## 🚀 Arquitectura Avanzada

```
WhatsApp → Chatwoot → FastAPI → LangGraph Supervisor
                                      ↓
                            [4 Agentes Especializados]
                                      ↓
                                n8n Tools → DB Universidad
```

## ⭐ Características Principales

- **LangGraph Supervisor**: Orquestación inteligente de agentes especializados
- **Integración Chatwoot**: WhatsApp Business API completa
- **Herramientas n8n**: Automatización de procesos universitarios
- **Base de datos PostgreSQL**: Persistencia completa de conversaciones
- **Docker Compose**: Infraestructura lista para producción
- **Autenticación por DNI**: Sistema seguro con base de datos real

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.11 + FastAPI
- **Agentes**: LangGraph + LangChain
- **LLM**: OpenAI GPT-4o / Anthropic Claude / Google Gemini
- **Base de datos**: PostgreSQL 16
- **Cache**: Redis 7
- **Automatización**: n8n
- **Chat**: Chatwoot + WhatsApp Business API
- **Contenedores**: Docker + Docker Compose

## 🚀 Inicio Rápido

### Prerequisitos
- Docker y Docker Compose
- API Key de OpenAI/Anthropic/Google
- Cuenta de Chatwoot configurada
- n8n para herramientas universitarias

### 1. Clonar y configurar
```bash
git clone <repo>
cd universidad-austral-bot
cp .env.example .env
```

### 2. Configurar variables de entorno
Editar `.env` con tus credenciales:
```bash
# Modelo LLM
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Chatwoot
CHATWOOT_URL=https://app.chatwoot.com
CHATWOOT_API_TOKEN=your_token
CHATWOOT_ACCOUNT_ID=your_account_id

# n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook
N8N_API_KEY=your_n8n_key
```

### 3. Levantar servicios
```bash
# Con Docker (recomendado)
make docker-up

# O localmente
make install
make run
```

## 📚 Servicios Disponibles

- **API Principal**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **n8n Interface**: http://localhost:5678 (admin/admin)

## 🤖 Agentes Especializados

### 1. Agente Académico
**Herramientas n8n**:
- `consultar_horarios(alumno_id, materia?, dia?)`
- `ver_inscripciones(alumno_id)`
- `buscar_profesor(nombre?, materia?)`
- `consultar_aula(aula?, materia?)`

**Casos de uso**:
- "¿Cuándo tengo clases?"
- "¿En qué aula es Nativa Digital?"
- "¿Quién es el profesor de Programación?"

### 2. Agente Financiero
**Herramientas n8n**:
- `estado_cuenta(alumno_id)`
- `consultar_creditos_vu(alumno_id)`

**Casos de uso**:
- "¿Tengo deudas?"
- "¿Cuántos créditos VU tengo?"
- "¿Cuándo vence mi próximo pago?"

### 3. Agente de Políticas
**Herramientas n8n**:
- `buscar_syllabus(materia, consulta_especifica)`

**Casos de uso**:
- "¿Qué temas vemos en la materia?"
- "¿Cómo se evalúa en Nativa Digital?"
- "¿Qué bibliografía necesito?"

### 4. Agente de Calendario
**Herramientas n8n**:
- `calendario_academico(tipo_evento?, fecha_inicio?, fecha_fin?)`
- `consultar_examenes(alumno_id, materia?)`

**Casos de uso**:
- "¿Cuándo es el parcial?"
- "¿Hay feriados próximos?"
- "¿Cuándo empiezan las clases?"

## 🔗 Integración con Chatwoot

### Configurar Webhook
1. Ir a Chatwoot Settings > Integrations > Webhooks
2. Agregar webhook:
   - URL: `https://tu-dominio.com/webhook/chatwoot`
   - Eventos: `message_created`
   - Método: POST

### Flujo de conversación
```
Usuario WhatsApp → Chatwoot → Webhook → LangGraph → n8n → Respuesta
```

## 🔧 Testing y Development

### Tests básicos
```bash
# Test directo
curl -X POST http://localhost:8000/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "Hola"}'

# Health check
curl http://localhost:8000/health
```

### Usuarios de prueba
- **DNI: 12345678** - Juan Pérez (Alumno)
- **DNI: 87654321** - María González (Alumno)
- **DNI: 11223344** - Carlos Rodríguez (Profesor)

### Logs y monitoreo
```bash
# Ver logs en tiempo real
make logs

# Estado de servicios
docker-compose ps

# Logs específicos
docker-compose logs university-agent
```

## 📋 Comandos Make

```bash
make help          # Ver todos los comandos
make install       # Instalar dependencias
make run           # Ejecutar localmente
make docker-up     # Levantar con Docker
make docker-down   # Bajar servicios
make logs          # Ver logs
make clean         # Limpiar archivos temp
```

## 🗄️ Base de Datos

### Esquema Principal
- `usuarios`: Datos de alumnos y profesores
- `sesiones`: Manejo de sesiones y autenticación
- `conversaciones`: Historial completo de chats
- `escalaciones`: Derivaciones a humanos

### Conexión
```sql
-- Conectar a PostgreSQL
psql postgresql://postgres:password@localhost:5432/universidad_austral
```

## 🔐 Seguridad

- Autenticación por DNI con base de datos
- Sesiones con TTL configurable
- Validación de webhooks
- Headers de seguridad en Nginx
- Datos sensibles en variables de entorno

## 📊 Escalación a Humanos

El sistema incluye escalación automática cuando:
- Usuario solicita hablar con persona
- Consultas complejas no resueltas
- Problemas técnicos persistentes
- Temas sensibles detectados

```python
# Escalación programática
await escalar_consulta(
    razon="consulta_compleja",
    departamento="administracion",
    urgencia="normal"
)
```

## 🌐 Deployment en Producción

### Con Docker Compose
```bash
# Producción
docker-compose -f docker-compose.prod.yml up -d
```

### Variables de entorno críticas
```bash
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-prod-...
DATABASE_URL=postgresql://prod-user:password@db:5432/universidad_austral
CHATWOOT_URL=https://chat.universidad.edu.ar
WHATSAPP_VERIFY_TOKEN=secure-production-token
```

## 📈 Monitoreo y Métricas

- Health checks automáticos
- Logs estructurados con timestamp
- Métricas de uso por agente
- Tracking de escalaciones
- Performance de herramientas n8n

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Agregar nueva funcionalidad'`
4. Push branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📄 Licencia

MIT License - Ver LICENSE para más detalles.

## 📞 Soporte

- Issues: GitHub Issues
- Documentación: `/docs`
- Email: soporte@universidad.edu.ar