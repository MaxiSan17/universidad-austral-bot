# 🔄 Instrucciones de Rebuild - Migración a Claude (Anthropic)

## 🐛 Problemas Corregidos

1. **Error de cuota OpenAI (429)**: Migrado a Claude 3.5 Sonnet con créditos disponibles ✅
2. **Clasificación incorrecta**: "que curso mañana" ahora se clasifica como `horarios` ✅
3. **Respuestas con templates**: Ahora usa Claude para respuestas naturales de alta calidad ✅

---

## ⚙️ Cambios Realizados

### 1. `.env` - Configuración de Anthropic
```bash
# Modelo LLM - Claude 3.5 Sonnet (con créditos disponibles en Anthropic)
LLM_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=tu_api_key_de_anthropic_aqui

# LLM Response Generation - Usar Claude 3.5 Sonnet
RESPONSE_GENERATION_MODE=llm
LLM_RESPONSE_MODEL=claude-3-5-sonnet-20241022
LLM_RESPONSE_TEMPERATURE=0.5
MAX_RESPONSE_TOKENS=500
ENABLE_CONTEXT_ENHANCEMENT=true
ENABLE_PROACTIVE_SUGGESTIONS=true
ENABLE_SMART_FILTERING=true
```

**⚠️ IMPORTANTE**: La API key real está configurada en tu archivo `.env` (que NO se commitea a git por seguridad).

**¿Por qué Claude?**
- ✅ Tenés créditos cargados en Anthropic (no más error 429)
- ✅ Claude 3.5 Sonnet es excelente para respuestas naturales en español
- ✅ Mejor comprensión de contexto que GPT-4o-mini
- ✅ Menos alucinaciones y respuestas más precisas

### 2. `query_classifier.py` - Nuevos patrones temporales
- Agregados 9 patrones para detectar "curso" + contexto temporal
- Ahora detecta correctamente "que curso mañana" → `academic` (horarios)

### 3. `supervisor.py` - Prompts mejorados
- Instrucciones más claras sobre contexto temporal
- Diferencia explícita entre horarios vs exámenes

### 4. `academic_agent.py` - Clasificación interna corregida
- **NIVEL 0** (MÁXIMA PRIORIDAD): Temporal + curso/clase → horarios
- Movida palabra "curso" de `inscripciones_kw` a `horarios_kw`
- Agregadas keywords temporales (hoy, mañana, etc.)

---

## 🚀 Pasos para Aplicar Cambios

### ✅ API Key de Anthropic Configurada
La API key de Claude ya está configurada en el `.env`. Solo necesitás hacer el rebuild.

---

### Opción 1: Rebuild Completo (Recomendado)

```bash
# 1. Detener containers actuales
docker-compose down

# 2. Rebuild sin cache (asegura cambios frescos)
docker-compose build --no-cache

# 3. Levantar de nuevo
docker-compose up -d

# 4. Ver logs para confirmar
docker-compose logs -f university-agent
```

---

### Opción 2: Rebuild Rápido (Solo si no hay cambios en requirements)

```bash
# 1. Detener y rebuild
docker-compose down && docker-compose up -d --build

# 2. Ver logs
docker-compose logs -f university-agent
```

---

## ✅ Verificación de Cambios

### 1. Verificar configuración LLM
Buscá en los logs estas líneas al iniciar:
```
LLMResponseGenerator inicializado: model=claude-3-5-sonnet-20241022, temp=0.5
```

### 2. Probar clasificación con "que curso mañana"
Envía el mensaje por WhatsApp y buscá en logs:
```
🎯 Contexto temporal + curso/clase detectado → horarios (PRIORIDAD)
🤖 Usando LLM Response Generator para horarios
```

### 3. Verificar respuesta natural (no template)
La respuesta debería ser conversacional, no con bullets rígidos:
- ❌ Antes: "📚 Horarios de Juan\n\n• Ética y Deontología..."
- ✅ Ahora: "Mañana tenés Ética a las 14hs en el aula R3 📍"

---

## 📊 Logs Esperados

### Clasificación correcta:
```
2025-11-02 21:45:10 - app.agents.query_classifier - INFO - 🎯 Clasificación por patrón: academic (conf: 0.95)
2025-11-02 21:45:10 - app.agents.supervisor - INFO - 🎯 Supervisor → ACADEMIC [pattern] (confianza: 0.95)
2025-11-02 21:45:10 - app.agents.academic_agent - INFO - 🎯 Contexto temporal + curso/clase detectado → horarios (PRIORIDAD)
2025-11-02 21:45:10 - app.agents.academic_agent - INFO - Consulta académica clasificada como: horarios ✅
```

### LLM Response Generation:
```
2025-11-02 22:00:11 - app.agents.academic_agent - INFO - 🤖 Usando LLM Response Generator para horarios
2025-11-02 22:00:11 - app.utils.llm_response_generator - INFO - 🤖 Generando respuesta con LLM: agent=academic, type=horarios
2025-11-02 22:00:11 - app.core.llm_factory - INFO - Creando LLM: provider=anthropic, model=claude-3-5-sonnet-20241022, temperature=0.5
2025-11-02 22:00:13 - app.utils.llm_response_generator - INFO - ✅ Respuesta generada (245 chars)
```

---

## ⚠️ Troubleshooting

### Error 429: "insufficient_quota" (Anthropic)
- Tu API key de Anthropic no tiene créditos disponibles
- Verificá en: https://console.anthropic.com/settings/billing
- Agregá créditos a tu cuenta de Anthropic

### Sigue usando templates
- No hiciste rebuild con `--no-cache`
- El `.env` no se reloadó correctamente
- Verificá logs: debería decir "Usando LLM Response Generator"

### Sigue clasificando mal
- No hiciste rebuild
- Verificá logs de clasificación
- Debería decir "Contexto temporal + curso/clase detectado"

---

## 📞 Siguiente Paso

Después del rebuild, probá con estos mensajes:
1. "que curso mañana" → Debe responder horarios del día siguiente
2. "que clases tengo hoy" → Debe responder horarios de hoy
3. "en que estoy inscripto" → Debe responder lista de materias

---

**Última actualización**: 2025-11-02 21:45
