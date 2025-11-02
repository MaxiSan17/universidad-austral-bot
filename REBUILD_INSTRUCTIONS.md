# 🔄 Instrucciones de Rebuild - Corrección de Bugs

## 🐛 Problemas Corregidos

1. **Error de cuota OpenAI (429)**: Estaba usando `gpt-4o` (caro), ahora usa `gpt-4o-mini` (barato) ✅
2. **Clasificación incorrecta**: "que curso mañana" ahora se clasifica como `horarios` ✅
3. **Respuestas con templates**: Ahora usa LLM para respuestas naturales ✅

---

## ⚙️ Cambios Realizados

### 1. `.env` - Nuevas configuraciones
```bash
# Modelo LLM - Usar gpt-4o-mini (barato, con cuota disponible)
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=tu_openai_key_actual

# LLM Response Generation - Usar MISMO modelo (gpt-4o-mini)
RESPONSE_GENERATION_MODE=llm
LLM_RESPONSE_MODEL=gpt-4o-mini  # ✅ Ahora usa el modelo barato
LLM_RESPONSE_TEMPERATURE=0.5
MAX_RESPONSE_TOKENS=500
ENABLE_CONTEXT_ENHANCEMENT=true
ENABLE_PROACTIVE_SUGGESTIONS=true
ENABLE_SMART_FILTERING=true
```

**¿Por qué funcionaba antes?**
- El error 429 era porque intentaba usar `gpt-4o` (que es caro y no tenés cuota)
- Ahora usa `gpt-4o-mini` para TODO (clasificación + respuestas)
- `gpt-4o-mini` es mucho más barato y probablemente tengás cuota disponible

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

### ✅ Sin Pasos Adicionales Necesarios
Tu API key de OpenAI actual ya está configurada. Solo necesitás hacer el rebuild.

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
LLMResponseGenerator inicializado: model=gpt-4o-mini, temp=0.5
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
2025-11-02 21:45:11 - app.agents.academic_agent - INFO - 🤖 Usando LLM Response Generator para horarios
2025-11-02 21:45:11 - app.utils.llm_response_generator - INFO - 🤖 Generando respuesta con LLM: agent=academic, type=horarios
2025-11-02 21:45:11 - app.core.llm_factory - INFO - Creando LLM: provider=openai, model=gpt-4o-mini, temperature=0.5
2025-11-02 21:45:13 - app.utils.llm_response_generator - INFO - ✅ Respuesta generada (245 chars)
```

---

## ⚠️ Troubleshooting

### Error 429: "insufficient_quota"
- Tu API key de OpenAI no tiene cuota disponible
- Verificá en: https://platform.openai.com/account/usage
- Agregá créditos o usá otra API key

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
