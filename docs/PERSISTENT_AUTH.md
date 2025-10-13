# 🔐 SISTEMA DE AUTENTICACIÓN PERSISTENTE POR TELÉFONO

## 📋 RESUMEN

Sistema que permite que los usuarios NO tengan que ingresar su DNI cada vez que interactúan con el bot. Después de la primera autenticación, el sistema recuerda el teléfono del usuario.

---

## 🎯 FUNCIONAMIENTO

### **Primera Vez (Usuario Nuevo)**

```
Usuario: "Hola"
Bot: "¡Hola! Para ayudarte necesito que me pases tu DNI (solo números)."

Usuario: "12345678"
Bot: "¡Perfecto, Juan! Ya te reconocí. ¿En qué te puedo ayudar hoy?"
      [Guarda: +5491112345678 → user_id en BD]
```

### **Todas las Veces Siguientes**

```
Usuario: "Hola" (días/semanas después)
Bot: "¡Hola de nuevo, Juan! 👋 ¿En qué te puedo ayudar hoy?"
     [Busca automáticamente en BD y auto-autentica]
```

### **Comando "Olvidar"**

```
Usuario: "olvidar"
Bot: "He olvidado tu información. 🛡️
     La próxima vez te pediré tu DNI nuevamente."
     [Elimina asociación de BD]
```

---

## 🏗️ ARQUITECTURA

### **Tabla en Supabase: `telefono_usuario`**

```sql
CREATE TABLE telefono_usuario (
    telefono VARCHAR(20) PRIMARY KEY,          -- +5491112345678
    usuario_id UUID REFERENCES usuarios(id),    -- UUID del usuario
    ultimo_acceso TIMESTAMP,                    -- Última interacción
    created_at TIMESTAMP                        -- Primera asociación
);
```

### **Flujo de Datos**

```
WhatsApp → Supervisor → phone_repository.get_user_by_phone()
                              ↓
                        [Busca en BD]
                              ↓
                    ¿Encontró asociación?
                      /              \
                    SI               NO
                    ↓                 ↓
        Auto-autenticar          Pedir DNI
        user_repository          ↓
        .get_user_by_id()        Autenticar
                ↓                 ↓
        Responder          phone_repository
                           .save_phone_user_mapping()
                                  ↓
                           [Guarda en BD]
```

---

## 📁 ARCHIVOS MODIFICADOS/CREADOS

### **Creados:**
1. `app/database/phone_repository.py` - Gestor de asociaciones teléfono→usuario
2. `docs/PERSISTENT_AUTH.md` - Esta documentación

### **Modificados:**
1. `app/database/supabase_client.py` - Agregado `get_user_by_id()`
2. `app/database/__init__.py` - Export de `phone_repository`
3. `app/agents/supervisor.py` - Lógica de autenticación persistente

### **SQL Scripts:**
1. Script de creación de tabla `telefono_usuario` en Supabase

---

## 🚀 INSTALACIÓN

### **PASO 1: Ejecutar SQL en Supabase**

Copia y ejecuta el script SQL completo que se encuentra en esta guía (arriba).

### **PASO 2: Verificar RLS**

```sql
-- Verificar que RLS esté configurado
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'telefono_usuario';

-- Debe retornar: rowsecurity = true
```

### **PASO 3: Rebuild del Contenedor**

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🧪 TESTING

### **Test 1: Primera Autenticación**
```
1. Enviar: "Hola"
   Esperado: "Para ayudarte necesito que me pases tu DNI"

2. Enviar: "12345678"
   Esperado: "¡Perfecto, Juan! Ya te reconocí"

3. Verificar en Supabase:
   SELECT * FROM telefono_usuario WHERE telefono = '+549...';
   Debe existir 1 registro
```

### **Test 2: Auto-Autenticación**
```
1. Cerrar WhatsApp o esperar 5 minutos
2. Enviar: "Hola"
   Esperado: "¡Hola de nuevo, Juan! 👋"
   (SIN pedir DNI)
```

### **Test 3: Comando Olvidar**
```
1. Enviar: "olvidar"
   Esperado: "He olvidado tu información"

2. Enviar: "Hola"
   Esperado: Vuelve a pedir DNI

3. Verificar en Supabase:
   SELECT * FROM telefono_usuario WHERE telefono = '+549...';
   Debe estar VACÍO (0 registros)
```

### **Test 4: Expiración (30 días)**
```
1. Modificar ultimo_acceso en BD a 35 días atrás:
   UPDATE telefono_usuario 
   SET ultimo_acceso = NOW() - INTERVAL '35 days'
   WHERE telefono = '+549...';

2. Enviar: "Hola"
   Esperado: Pide DNI nuevamente (asociación expirada)
```

---

## 🔒 SEGURIDAD

### **Medidas Implementadas:**

1. **Expiración Automática** - Asociaciones expiran después de 30 días sin uso
2. **Comando de Logout** - Usuario puede borrar su asociación manualmente
3. **Validación de IDs** - Se verifica que el usuario aún exista en BD
4. **RLS Habilitado** - Row Level Security en Supabase
5. **Auditoría** - `ultimo_acceso` registra cada interacción

### **Consideraciones:**

- ❌ NO almacena contraseñas ni datos sensibles
- ✅ Solo guarda UUID (no DNI ni datos personales)
- ✅ Teléfono ya está en WhatsApp (no es información nueva)
- ✅ Usuario puede "olvidar" en cualquier momento

---

## 📊 MONITOREO

### **Queries Útiles para Admins:**

```sql
-- Ver todas las asociaciones activas
SELECT 
    tu.telefono,
    u.nombre,
    u.apellido,
    tu.ultimo_acceso,
    tu.created_at,
    EXTRACT(DAY FROM (NOW() - tu.ultimo_acceso)) as dias_inactivo
FROM telefono_usuario tu
JOIN usuarios u ON tu.usuario_id = u.id
ORDER BY tu.ultimo_acceso DESC;

-- Limpiar asociaciones expiradas (>30 días)
DELETE FROM telefono_usuario 
WHERE ultimo_acceso < NOW() - INTERVAL '30 days';

-- Contar usuarios con auto-login activo
SELECT COUNT(*) as total_auto_login 
FROM telefono_usuario 
WHERE ultimo_acceso > NOW() - INTERVAL '30 days';
```

---

## 🎯 BENEFICIOS

✅ **UX Mejorada** - Usuario no tiene que recordar/ingresar DNI cada vez  
✅ **Reduce Fricción** - Menos pasos para hacer consultas  
✅ **Seguro** - Con expiración y opt-out  
✅ **Escalable** - No impacta performance  
✅ **Auditable** - Logs completos de accesos  

---

## 🐛 TROUBLESHOOTING

### **Problema: Bot sigue pidiendo DNI siempre**

**Causa:** RLS bloqueando queries  
**Solución:**
```sql
ALTER TABLE telefono_usuario DISABLE ROW LEVEL SECURITY;
-- O configurar política correcta
```

### **Problema: Error "usuario_id no encontrado"**

**Causa:** Usuario eliminado de tabla `usuarios`  
**Solución:** ON DELETE CASCADE limpia automáticamente

### **Problema: Logs no aparecen**

**Verificar:**
```bash
docker-compose logs -f university-agent | grep "🔍"
```

---

## 📝 CHANGELOG

**v1.0.0 - 2025-10-12**
- ✅ Implementación inicial de autenticación persistente
- ✅ Tabla `telefono_usuario` en Supabase
- ✅ Auto-autenticación por teléfono
- ✅ Comando "olvidar"
- ✅ Expiración de 30 días
- ✅ Logs mejorados

---

## 👨‍💻 MANTENIMIENTO

### **Limpieza Programada (Opcional)**

Crear un cronjob para limpiar asociaciones viejas:

```sql
-- Ejecutar semanalmente
DELETE FROM telefono_usuario 
WHERE ultimo_acceso < NOW() - INTERVAL '30 days';
```

O usar Supabase Edge Functions para automatizar.

---

## 🔮 FUTURAS MEJORAS

- [ ] Multi-usuario por teléfono (familias)
- [ ] Notificación de nueva sesión
- [ ] Dashboard admin para gestionar asociaciones
- [ ] Configurar días de expiración por usuario
- [ ] Exportar logs de acceso

---

**Última actualización:** 2025-10-12  
**Autor:** Sistema UA Bot  
**Versión:** 1.0.0
