-- Crear esquema de base de datos para Universidad Austral

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dni VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    legajo VARCHAR(20) UNIQUE NOT NULL,
    tipo VARCHAR(20) CHECK (tipo IN ('Alumno', 'Profesor')),
    carrera VARCHAR(200),
    telefono_whatsapp VARCHAR(20),
    nombre_preferido VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de sesiones
CREATE TABLE IF NOT EXISTS sesiones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id UUID REFERENCES usuarios(id),
    user_authenticated BOOLEAN DEFAULT FALSE,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conversation_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de conversaciones
CREATE TABLE IF NOT EXISTS conversaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) REFERENCES sesiones(session_id),
    user_id UUID REFERENCES usuarios(id),
    message_type VARCHAR(20) CHECK (message_type IN ('incoming', 'outgoing')),
    content TEXT,
    agent_type VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de escalaciones
CREATE TABLE IF NOT EXISTS escalaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100),
    user_id UUID REFERENCES usuarios(id),
    razon TEXT,
    departamento VARCHAR(50),
    urgencia VARCHAR(20),
    estado VARCHAR(20) DEFAULT 'pendiente',
    resolucion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Índices para mejorar performance
CREATE INDEX idx_usuarios_dni ON usuarios(dni);
CREATE INDEX idx_sesiones_session_id ON sesiones(session_id);
CREATE INDEX idx_conversaciones_session_id ON conversaciones(session_id);
CREATE INDEX idx_conversaciones_created_at ON conversaciones(created_at);
CREATE INDEX idx_escalaciones_estado ON escalaciones(estado);

-- Datos de ejemplo
INSERT INTO usuarios (dni, nombre, apellido, legajo, tipo, carrera, telefono_whatsapp, nombre_preferido)
VALUES
    ('12345678', 'Juan', 'Pérez', 'UA001', 'Alumno', 'Ingeniería en Informática', '+5491112345678', 'Juan'),
    ('87654321', 'María', 'González', 'UA002', 'Alumno', 'Licenciatura en Administración', '+5491187654321', 'Mari'),
    ('11223344', 'Carlos', 'Rodríguez', 'UAP001', 'Profesor', NULL, '+5491111223344', 'Carlos');