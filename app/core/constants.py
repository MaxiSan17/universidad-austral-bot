"""
Constantes del sistema
"""
from typing import Dict, List

# =====================================================
# MENSAJES DEL SISTEMA
# =====================================================

MENSAJE_BIENVENIDA = """¡Hola! 👋 Soy el asistente virtual de la Universidad Austral.

Para poder ayudarte necesito que me pases tu DNI (solo números, sin puntos ni espacios).

Por ejemplo: 12345678"""

MENSAJE_ERROR_GENERICO = """¡Ups! 😅 Hubo un problemita técnico y no pude procesar tu consulta.

Por favor intentá de nuevo en unos minutos, o si es urgente podés contactar directamente a la secretaría.

¿Te puedo ayudar con algo más mientras tanto?"""

MENSAJE_DNI_INVALIDO = """❌ Lo siento, no reconozco ese DNI en nuestra base de datos.

Por favor, verificá el número o contactá a administración para resolver este problema.

También podés intentar ingresar tu DNI nuevamente (solo números, sin puntos ni espacios)."""

# =====================================================
# HORARIOS Y TIEMPOS
# =====================================================

# Días de la semana en español
DIAS_SEMANA_ES: Dict[int, str] = {
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
    7: "Domingo"
}

# Meses en español
MESES_ES: Dict[int, str] = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}

# Horarios de atención
HORARIO_ATENCION = {
    "inicio": "09:00",
    "fin": "17:00",
    "dias": [1, 2, 3, 4, 5]  # Lunes a Viernes
}

# =====================================================
# TIPOS DE EXAMEN
# =====================================================

TIPOS_EXAMEN: Dict[str, str] = {
    "parcial": "Parcial",
    "recuperatorio": "Recuperatorio",
    "final": "Final",
    "trabajo_practico": "Trabajo Práctico"
}

# =====================================================
# EMOJIS POR CONTEXTO
# =====================================================

EMOJIS = {
    # Académico
    "horario": "📚",
    "clase": "📅",
    "profesor": "👨‍🏫",
    "aula": "📍",
    "materia": "📖",
    "inscripcion": "📝",

    # Calendario
    "examen": "📝",
    "parcial": "📝",
    "final": "🎯",
    "recuperatorio": "🔄",
    "trabajo_practico": "💻",
    "evento": "📅",
    "feriado": "🏖️",
    "calendario": "📋",

    # Financiero
    "pago": "💰",
    "deuda": "💳",
    "factura": "📄",
    "descuento": "🎁",

    # Vida Universitaria
    "creditos_vu": "🎓",
    "actividad": "🎯",

    # Estados
    "exito": "✅",
    "error": "❌",
    "advertencia": "⚠️",
    "info": "ℹ️",
    "pregunta": "❓",
    "cargando": "⏳",

    # Generales
    "saludo": "👋",
    "despedida": "👋",
    "ayuda": "🤝",

    # NUEVO: Modalidades (más visual)
    "presencial": "🏫",
    "virtual": "💻",
    "hibrida": "🔄",

    # NUEVO: Urgencia/Temporalidad
    "hoy": "🔴",
    "mañana": "🟡",
    "proximo": "🟢",
    "pasado": "⚫",

    # NUEVO: Estados de progreso
    "activo": "🟢",
    "pendiente": "🟡",
    "vencido": "🔴",
    "completado": "✅",

    # NUEVO: Hora del día
    "mañana_tiempo": "☀️",
    "tarde": "👋",
    "noche": "🌙",

    # NUEVO: Emocionales
    "celebracion": "🎉",
    "animo": "💪",
    "tranquilo": "😊",
    "preocupacion": "😓"
}

# =====================================================
# VARIACIONES DE TONO CONVERSACIONAL
# =====================================================

GREETING_VARIATIONS = [
    "¡Hola {nombre}!",
    "¡Listo, {nombre}!",
    "Acá va, {nombre}",
    "Ya lo tengo, {nombre}",
    "¡Dale, {nombre}!",
    "{nombre}, acá está"
]

GREETING_TIME_BASED = {
    "morning": "¡Buenos días, {nombre}! ☀️",
    "afternoon": "¡Hola, {nombre}! 👋",
    "evening": "¡Buenas tardes, {nombre}!",
    "night": "¡Buenas noches, {nombre}! 🌙"
}

CLOSING_VARIATIONS = [
    "¿Algo más? 🤝",
    "Si necesitás algo, avisame 👍",
    "Cualquier cosa, preguntame de nuevo",
    "¿Te ayudo con algo más?",
    ""  # Sin cierre (para respuestas muy claras)
]

# =====================================================
# DEPARTAMENTOS PARA ESCALACIÓN
# =====================================================

DEPARTAMENTOS = {
    "secretaria": {
        "nombre": "Secretaría Académica",
        "descripcion": "Trámites académicos, certificados, inscripciones",
        "horario": "Lunes a Viernes 9:00 a 17:00"
    },
    "administracion": {
        "nombre": "Administración",
        "descripcion": "Pagos, facturación, deudas",
        "horario": "Lunes a Viernes 9:00 a 17:00"
    },
    "sistemas": {
        "nombre": "Sistemas",
        "descripcion": "Problemas técnicos, accesos, contraseñas",
        "horario": "Lunes a Viernes 9:00 a 18:00"
    },
    "vida_universitaria": {
        "nombre": "Vida Universitaria",
        "descripcion": "Actividades extracurriculares, créditos VU",
        "horario": "Lunes a Viernes 10:00 a 16:00"
    }
}

# =====================================================
# LÍMITES Y VALIDACIONES
# =====================================================

# Límites de texto
MAX_QUERY_LENGTH = 500
MAX_RESPONSE_LENGTH = 4000
MAX_CONVERSATION_HISTORY = 50

# Límites de paginación
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Límites de búsqueda
MAX_SEARCH_RESULTS = 20
MIN_SEARCH_QUERY_LENGTH = 3

# Timeouts (en segundos)
TIMEOUT_LLM = 60
TIMEOUT_DATABASE = 10
TIMEOUT_HTTP = 30

# =====================================================
# FORMATOS
# =====================================================

# Formatos de fecha
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_DISPLAY = "%d/%m/%Y"
TIME_FORMAT = "%H:%M"

# =====================================================
# CRÉDITOS VU
# =====================================================

CREDITOS_VU_INFO = {
    "minimo_requerido": 10,
    "descripcion": """Los **Créditos de Vida Universitaria (VU)** son actividades extracurriculares obligatorias para recibir tu título. Incluyen:
• Talleres deportivos
• Actividades culturales
• Voluntariado universitario
• Charlas y conferencias

Cada actividad dura un cuatrimestre y puede darte entre 1 y 3 créditos según la intensidad.""",
    "categorias": [
        "Deportes",
        "Cultura",
        "Voluntariado",
        "Conferencias",
        "Talleres"
    ]
}

# =====================================================
# KEYWORDS PARA CLASIFICACIÓN
# =====================================================

KEYWORDS = {
    "academico": [
        "horario", "clases", "inscripción", "inscripcion", "materia", 
        "profesor", "aula", "comisión", "comision", "cursada", 
        "inscripto", "curso", "carrera"
    ],
    "calendario": [
        "examen", "examenes", "parcial", "final", "recuperatorio", 
        "fecha", "calendario", "feriado", "evento", "cuando"
    ],
    "financiero": [
        "pago", "deuda", "cuota", "factura", "arancelario", 
        "debo", "cuenta", "cobro", "vencimiento", "dinero"
    ],
    "vida_universitaria": [
        "credito", "creditos", "vu", "vida universitaria", 
        "actividad", "taller", "voluntariado"
    ]
}

# =====================================================
# REGEX PATTERNS
# =====================================================

PATTERNS = {
    "dni": r"^\d{7,10}$",
    "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "telefono": r"^\+?[0-9]{10,15}$",
    "horario": r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
    "fecha": r"^\d{4}-\d{2}-\d{2}$"
}
