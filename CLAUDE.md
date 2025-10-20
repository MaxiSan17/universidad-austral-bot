# 🎓 Universidad Austral Bot - Guía de Proyecto

## 📋 Descripción General

Bot universitario con arquitectura LangGraph + FastAPI + Supabase para atención estudiantil vía WhatsApp.

**Stack Tecnológico:**
- **Backend**: Python 3.11, FastAPI, LangGraph
- **Database**: Supabase (PostgreSQL)
- **LLM**: OpenAI GPT-4o-mini, Claude Opus 4.1
- **Integration**: Chatwoot (WhatsApp), n8n (tools)
- **Deployment**: Docker Compose

## 🏗️ Arquitectura del Sistema

### Componentes Principales
1. **Supervisor Agent** (LangGraph): Orquesta 4 sub-agents especializados
2. **Academic Agent**: Horarios, inscripciones, profesores
3. **Calendar Agent**: Exámenes, fechas, calendario académico
4. **Financial Agent**: Pagos, deudas (futuro)
5. **Policies Agent**: Reglamentos, syllabi (futuro)

### Flujo de Datos
```
WhatsApp → Chatwoot Webhook → FastAPI → LangGraph Supervisor
    ↓
Clasificador de Query → Agent Especializado → n8n Tool → Supabase
    ↓
Response → FastAPI → Chatwoot → WhatsApp
```

## 📂 Estructura de Directorios

```
app/
├── core/              # Config, constants, exceptions
├── models/            # Pydantic models (CRÍTICO: usar properties)
├── agents/            # LangGraph agents
├── tools/             # n8n tool wrappers
├── database/          # Supabase repositories
├── integrations/      # Chatwoot, WhatsApp webhooks
└── utils/             # Logging, formatters
```

## 🛠️ Comandos Importantes

### Docker
```bash
# Rebuild completo
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Ver logs
docker-compose logs -f university-agent

# Restart solo el bot
docker-compose restart university-agent
```

### Testing
```bash
# Tests locales
pytest tests/ -v

# Test específico
pytest tests/unit/test_agents.py -v
```

### Git
```bash
# Branch naming: feature/nombre-funcionalidad
# Commits: usar conventional commits (feat:, fix:, refactor:)
```

## 📝 Convenciones de Código

### Python Style
- **Type hints**: SIEMPRE usar (mandatory)
- **Pydantic Models**: Preferir sobre dicts
- **Properties calculadas**: Usar @property en models
- **Docstrings**: Google style
- **Naming**:
  - Variables: snake_case
  - Classes: PascalCase
  - Constants: UPPER_CASE
  - Private: _leading_underscore

### Importaciones
```python
# Orden: stdlib → third-party → local
import os
from typing import Dict, Any

from fastapi import FastAPI
from langchain_core.messages import HumanMessage

from app.core import settings
from app.models import HorariosResponse
```

### Logs
```python
# Usar logger, no print
from app.utils.logger import get_logger
logger = get_logger(__name__)

logger.info(f"Query clasificada como: {query_type}")
logger.error(f"Error: {e}", exc_info=True)
```

## ⚠️ Reglas Críticas

### NUNCA:
- ❌ Usar `dict` genéricos - usar Pydantic Models
- ❌ Hacer cambios en `main.py` sin consultar (critical)
- ❌ Modificar `.env` en commits (usar .env.example)
- ❌ Hardcodear URLs o API keys
- ❌ Usar `print()` - usar `logger`

### SIEMPRE:
- ✅ Validar UUIDs antes de queries a DB
- ✅ Usar try/except en tool calls
- ✅ Retornar Pydantic models desde repositories
- ✅ Usar properties calculadas en models
- ✅ Formatear responses con emojis (1-2 por mensaje)

## 🔧 Configuración de Herramientas

### n8n Webhooks
Base URL: `https://n8n.tucbbs.com.ar/webhook`

Tools disponibles:
- `consultar_horarios`
- `ver_inscripciones`
- `buscar_profesor`
- `consultar_aula`
- `estado_cuenta`
- `consultar_creditos_vu`
- `calendario_academico`
- `consultar_examenes`
- `escalar_consulta`

### Supabase
```python
# Usar repositories, NUNCA queries directas
from app.database.academic_repository import AcademicRepository

repo = AcademicRepository()
response = await repo.get_horarios_alumno(request)
```

## 🎨 Terminología Universitaria Argentina

- "Cursada" (no "curso")
- "Materia" (no "asignatura")
- "Comisión" (para grupos)
- "Final" / "Parcial" (exámenes)
- "Cuatrimestre" (no "semestre")
- "Carrera" (programa)
- Usar "vos" en respuestas

## 🐛 Debugging

### Logs de LangSmith
- Project: `universidad-austral-bot`
- Ver traces en: https://smith.langchain.com

### Common Issues
1. **ValidationError en Pydantic**: Revisar types en Request
2. **Tool timeout**: n8n puede tardar >30s
3. **Context window full**: Usar properties en vez de full objects

## 📊 Performance

- **Max response time**: 5 segundos
- **Token budget**: Usar fuzzy matching antes de LLM
- **Cache**: Memory MCP mantiene contexto

## 🎯 Workflow Recomendado

1. **Plan**: Leer código existente, entender arquitectura
2. **Research**: Buscar patrones similares en el código
3. **Implement**: Crear/modificar código
4. **Test**: Verificar que funciona
5. **Review**: Check logs de LangSmith

## 📚 Recursos

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Supabase Docs**: https://supabase.com/docs

---

**Última actualización**: Proyecto en fase de migración completa a Pydantic Models (completado)
