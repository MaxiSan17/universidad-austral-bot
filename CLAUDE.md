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

### Filtrado de Contexto de Mensajes ⚡ NUEVO
**Problema solucionado**: Reducir consumo de tokens enviando solo contexto relevante

**Configuración** (`.env`):
```bash
MESSAGE_HISTORY_HOURS=24  # Solo mensajes de últimas N horas
```

**Cómo funciona**:
- `supervisor.py:_get_filtered_message_history()` filtra mensajes por timestamp
- Solo incluye mensajes de las últimas 24 horas (configurable)
- Reduce significativamente el consumo de tokens
- Mantiene contexto relevante sin información obsoleta

**Logs**:
```
📊 Historial filtrado para {session_id}:
   {N} mensajes únicos de {M}/{T} estados
   (últimas 24h desde {timestamp})
```

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

## 🤖 Sistema de Respuestas LLM (NUEVO - Octubre 2025)

### 🎯 Objetivo

Transformar el bot de respuestas basadas en templates rígidos a **respuestas generadas por LLM** que sean:
- Naturales y conversacionales
- Contextuales (usan historial de 24h)
- Selectivas (responden solo lo preguntado)
- Empáticas (adaptan tono según emoción/urgencia)
- Proactivas (sugieren información útil relacionada)

### 📊 Arquitectura

**Flujo anterior (templates)**:
```
Usuario → Agent → Tool (datos) → Template Formatter → Usuario
```

**Flujo nuevo (LLM)**:
```
Usuario → Agent → Tool (datos) → LLM Response Generator → Usuario
                                         ↑
                                 Context Enhancer
                                 (historial 24h + emociones + proactividad)
```

### 📁 Nuevos Módulos

#### 1. `app/models/context.py`
Modelos Pydantic para contexto conversacional enriquecido:
- `EmotionalState` - Estado emocional (tono, urgencia, empatía)
- `QueryEntity` - Entidades extraídas (aula, horario, profesor)
- `ConversationContext` - Contexto completo (historial, emociones, sugerencias)
- `ResponseStrategy` - Estrategia de respuesta (longitud, tono, formato)

#### 2. `app/prompts/system_prompts.py`
System prompts estructurados para el LLM:
- Prompts base por agent (academic, calendar)
- Instrucciones de tono emocional (urgente, celebración, empatía, ánimo)
- Instrucciones de longitud (short, medium, detailed, auto)
- **Instrucciones de selectividad** (CRÍTICO: responder solo lo preguntado)
- Instrucciones de proactividad y referencias históricas

#### 3. `app/utils/llm_response_generator.py`
Generador principal de respuestas con LLM:
- `LLMResponseGenerator` class - Generador principal
- `generate_natural_response()` - Helper function para uso fácil
- `should_use_llm_generation()` - Determina si usar LLM vs templates
- `determine_data_complexity()` - Analiza complejidad de datos

#### 4. `app/utils/response_strategy.py`
Analiza queries y determina estrategia de respuesta:
- `QueryEntityExtractor` - Extrae entidades (aula, horario, profesor)
- `ResponseStrategyBuilder` - Construye estrategia completa
- `build_response_strategy()` - Helper function

#### 5. `app/utils/context_enhancer.py`
Enriquece contexto conversacional:
- `ContextEnhancer` class - Enriquecedor principal
- Extrae historial relevante (últimas 24h)
- Detecta estado emocional
- Genera sugerencias proactivas
- `enhance_conversation_context()` - Helper function

### ⚙️ Configuración (.env)

```bash
# LLM Response Generation
RESPONSE_GENERATION_MODE=llm  # "llm", "template", "hybrid"
LLM_RESPONSE_MODEL=gpt-4o-mini  # Opcional, usa LLM_MODEL si no se especifica
LLM_RESPONSE_TEMPERATURE=0.5  # Balance creatividad/precisión
MAX_RESPONSE_TOKENS=500

# Context Enhancement
ENABLE_CONTEXT_ENHANCEMENT=true
CONTEXT_LOOKBACK_HOURS=24  # Historial conversacional
ENABLE_PROACTIVE_SUGGESTIONS=true

# Response Strategy
ENABLE_SMART_FILTERING=true  # LLM filtra datos relevantes
DEFAULT_RESPONSE_LENGTH=auto  # "short", "medium", "detailed", "auto"
```

### 🔄 Integración en Agents

**Ejemplo en `academic_agent.py`** (método `_handle_schedules`):

```python
# Obtener datos del tool
result_dict = await self.tools.consultar_horarios(params)
response = HorariosResponse(**result_dict)

# Verificar si usar LLM generation
if should_use_llm_generation():
    # Obtener sesión
    session = session_manager.get_session(session_id)

    # Enriquecer contexto
    context = await enhance_conversation_context(
        current_query=query,
        query_type="horarios",
        user_name=user_info["nombre"],
        session=session,
        data=response
    )

    # Construir estrategia
    strategy, entities = build_response_strategy(
        query=query,
        data=response,
        context=context
    )

    # Generar respuesta natural
    natural_response = await generate_natural_response(
        data=response,
        original_query=query,
        user_name=user_info["nombre"],
        query_type="horarios",
        agent_type="academic",
        context=context,
        strategy=strategy
    )

    # Actualizar contexto en sesión
    session.update_query_context(
        query=query,
        query_type="horarios",
        query_data={"materia": materia, "temporal": contexto_temporal},
        response_summary=natural_response[:100]
    )

    return natural_response
else:
    # Fallback a templates
    return self._format_schedule_response(response, nombre, contexto_temporal)
```

### 📊 Comparación de Respuestas

**Pregunta**: "¿En qué aula tengo ética?"

**Antes (template rígido)**:
```
📚 Horarios de Juan

• Ética y Deontología (14:00 - 16:00)
  📍 Aula R3 🏫
  👨‍🏫 Prof. García Martínez
  ⏱️ Duración: 120 minutos

¿Algo más? 🤝
```

**Después (LLM selectivo)**:
```
Tu clase de Ética es en el aula R3 📍

(Es los viernes a las 14hs con García Martínez)
```

**Pregunta**: "¿Cuándo tengo clases mañana?"

**Después (LLM con proactividad)**:
```
Mañana tenés un día bastante cargado con 3 materias 💪

14:00 - Ética (R3)
16:00 - Programación I (L2)
18:30 - Matemática Discreta (R1)

Ah, y acordate que tenés el parcial de Nativa Digital el lunes 🟡
¿Querés que te recuerde el aula?
```

### ✅ Testing

Ejecutar test de validación:
```bash
python test_llm_response_system.py
```

El test valida:
1. ✅ Imports de módulos nuevos
2. ✅ Configuraciones cargadas correctamente
3. ✅ Modelos Pydantic funcionando
4. ✅ Extractores de entidades
5. ✅ Generación de prompts
6. ✅ Determinación de complejidad

### 🎯 Características Clave

1. **Selectividad Inteligente**: El LLM analiza la pregunta y responde SOLO lo solicitado
2. **Contexto Conversacional**: Usa historial de 24h para hacer referencias ("como te dije antes...")
3. **Adaptación Emocional**: Ajusta tono según urgencia (examen mañana) o celebración (día libre)
4. **Proactividad Contextual**: Sugiere información útil relacionada automáticamente
5. **Variación de Longitud**: Respuestas cortas para preguntas simples, detalladas para complejas
6. **Fallback Seguro**: Si LLM falla, usa templates legacy como backup

### ⚠️ Implicaciones

**Ventajas**:
- Naturalidad máxima en respuestas
- Mejor experiencia de usuario
- Flexibilidad total ante queries complejas
- Contexto conversacional rico

**Trade-offs**:
- Latencia: +1-2s por respuesta (total: 2-4s)
- Costo: ~$0.001-0.003 por respuesta
- Tokens: 500-1500 tokens/respuesta (vs ~50 con templates)
- Variabilidad: Menos predecible (requiere prompt engineering)

### ✅ Estado de Integración

**Agents con LLM Response Generator integrado**:
- ✅ **Academic Agent** - Consultas de horarios (`_handle_schedules`)
- ✅ **Calendar Agent** - Consultas de exámenes (`_handle_exams`)

**Agents pendientes** (usando templates legacy):
- ⏳ Academic Agent - Inscripciones, profesores, aulas, créditos VU
- ⏳ Calendar Agent - Eventos, feriados
- ⏳ Financial Agent - Pagos, deudas
- ⏳ Policies Agent - Reglamentos, syllabi

### 🚀 Próximos Pasos

1. ✅ ~~Migración completa: Integrar LLM generator en calendar_agent.py~~ **COMPLETADO**
2. **Migración incremental**: Integrar en resto de métodos de academic y calendar agents
3. **Optimización de prompts**: Ajustar system prompts basado en feedback de usuarios reales
4. **A/B Testing**: Comparar satisfacción usuario con templates vs LLM
5. **Memoria de largo plazo**: Integrar Memory MCP para recordar preferencias del usuario
6. **Streaming**: Implementar streaming de tokens para mejor UX

---

**Última actualización**: Sistema de Respuestas LLM implementado (Octubre 2025)
