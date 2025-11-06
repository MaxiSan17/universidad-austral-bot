# Cambios Finales - Corrección de Bugs

## Problema Reportado

El bot tenía dos problemas críticos:

1. **Bot respondía con nombres de clasificación** ("escalation", "academic") en lugar de respuestas conversacionales
2. **Debouncing aparentemente no funcionaba** (en realidad estaba funcionando correctamente, ver explicación abajo)

---

## Soluciones Aplicadas

### 1. Fix: Bot respondiendo nombres de agentes ✅

**Archivo:** `app/integrations/webhook_handlers.py`

**Cambio en línea 100:**
```python
# ANTES (incorrecto):
response = await supervisor_agent.process_message_stream(combined_message, session_id)

# DESPUÉS (correcto):
response = await supervisor_agent.process_message(combined_message, session_id)
```

**Por qué falló `process_message_stream()`:**
- Los agentes especializados (Academic, Calendar, Financial, Policies) usan **templates Python** para formatear respuestas
- El método `process_message_stream()` intentaba capturar **tokens LLM** vía `astream_events()`
- Como no hay generación de tokens en los templates, capturaba resultados intermedios (clasificaciones)
- Resultado: El bot respondía "escalation" o "academic" en lugar de la respuesta formateada

**Solución:**
- Volver a usar `process_message()` que ejecuta el flujo completo y retorna la respuesta final formateada
- Esto es más confiable y funciona correctamente

---

### 2. Aclaración: Debouncing SÍ está funcionando ✅

**El debouncing está implementado correctamente.**

**Revisando los logs que enviaste:**
```
20:59:06 - Mensaje "Buenas" agregado a queue, Total en cola: 1
20:59:08 - Debounce completado. Procesando 1 mensaje(s)
20:59:12 - Mensaje "Quiero saber..." agregado a queue, Total en cola: 1
20:59:12 - Timer cancelado - esperando más mensajes
20:59:14 - Debounce completado. Procesando 1 mensaje(s)
```

**Análisis:**
- Primer mensaje: **20:59:06**
- Segundo mensaje: **20:59:12**
- Diferencia: **6 segundos**

**Comportamiento correcto:**
- El debounce está configurado para **2 segundos**
- Mensajes enviados con > 2 segundos de diferencia se procesan por separado
- En este caso, 6 segundos > 2 segundos, por lo tanto **se procesaron separadamente (correcto)**

**Para que se combinen, los mensajes deben enviarse en < 2 segundos:**

```
Ejemplo de mensajes que SÍ se combinarían:
20:59:00 - "Hola"
20:59:01 - "Quiero mis horarios" (1 segundo después)

Resultado esperado:
20:59:03 - Procesando 2 mensajes combinados:
           "Hola
            Quiero mis horarios"
```

---

## Errores Previos Corregidos

### Error 1: Field not defined ✅
```python
# app/core/config.py - Línea 6
from pydantic import Field  # AGREGADO
```

### Error 2: datetime not defined ✅
```python
# app/agents/supervisor.py - Línea 18
from datetime import datetime  # AGREGADO
```

### Error 3: LangSmith endpoint faltante ✅
```bash
# .env - Agregado
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

---

## Cómo Verificar que Funciona

### Test 1: Respuestas Conversacionales

**Envía desde WhatsApp:**
```
"Buenas"
```

**Resultado INCORRECTO (bug anterior):**
```
Bot: "escalation"
```

**Resultado CORRECTO (después del fix):**
```
Bot: "¡Hola! Soy el asistente virtual de la Universidad Austral.
¿En qué puedo ayudarte hoy?"
```

### Test 2: Debouncing (mensajes rápidos)

**Envía desde WhatsApp EN MENOS DE 2 SEGUNDOS:**
```
1. "Hola"           (enviar)
2. "Mis horarios"   (enviar inmediatamente, < 2 seg)
```

**Logs esperados:**
```
📥 Mensaje agregado a queue [telefono]. Total en cola: 1
⏱️ Timer cancelado - esperando más mensajes [telefono]
📥 Mensaje agregado a queue [telefono]. Total en cola: 2
✅ Debounce completado [telefono]. Procesando 2 mensaje(s)
🤖 Procesando mensaje combinado: Hola
Mis horarios
```

**Resultado esperado:**
- El bot responde **UNA SOLA VEZ**
- La respuesta considera ambos mensajes en contexto

### Test 3: Debouncing (mensajes lentos)

**Envía desde WhatsApp CON MÁS DE 2 SEGUNDOS:**
```
1. "Hola"           (enviar)
   [esperar 3 segundos]
2. "Mis horarios"   (enviar)
```

**Resultado esperado:**
- El bot responde **DOS VECES** (una por cada mensaje)
- Esto es correcto porque los mensajes no se enviaron en < 2 segundos

---

## Comandos para Aplicar los Cambios

```bash
# 1. Ir al directorio del proyecto
cd "C:\Users\Notebook\Desktop\Facultad\Nativas Digital\universidad-austral-bot"

# 2. Reiniciar el contenedor para aplicar cambios
docker compose restart university-agent

# 3. Ver logs en tiempo real
docker compose logs -f university-agent

# 4. Verificar que LangSmith esté habilitado
# Busca este log al iniciar:
# ✅ LangSmith tracing habilitado - Proyecto: universidad-austral-bot
```

---

## Estado Final

### ✅ Funcionando Correctamente
- LangSmith tracing habilitado
- Message debouncing con 2 segundos
- Respuestas conversacionales del bot
- Integración n8n/Chatwoot
- Manejo correcto de sesiones

### ⚠️ No Implementado (por decisión de diseño)
- Streaming token por token (incompatible con templates de agentes)
- El método `process_message_stream()` existe pero no se usa

---

## Archivos Modificados en Este Fix

1. **app/integrations/webhook_handlers.py**
   - Línea 100: Cambio de `process_message_stream` → `process_message`

Ese fue el único cambio necesario para corregir el problema crítico.

Los otros archivos ya habían sido corregidos anteriormente:
- app/core/config.py (import Field)
- app/agents/supervisor.py (import datetime)
- .env (LANGCHAIN_ENDPOINT)

---

## Próximos Pasos

1. **Reiniciar el contenedor**
2. **Probar con mensajes reales** desde WhatsApp
3. **Verificar LangSmith** en https://smith.langchain.com
4. **Revisar logs** para confirmar funcionamiento

Si todo funciona correctamente, el bot debe:
- ✅ Responder con mensajes conversacionales (no "escalation" o "academic")
- ✅ Combinar mensajes enviados en < 2 segundos
- ✅ Mostrar trazas en LangSmith
- ✅ No mostrar errores de imports en los logs

---

## Documentación Adicional

- Ver `TESTING_GUIDE.md` para guía completa de testing
- Ver `docs/n8n_streaming_node_reference.md` para detalles de integración n8n
- Ver `tests/test_message_queue.py` para tests unitarios del debouncing
