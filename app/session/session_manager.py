from typing import Dict, Any, Optional, List, Deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import asyncio
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Session:
    """Clase para representar una sesión de usuario"""
    session_id: str
    user_id: Optional[str] = None
    is_authenticated: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_agent: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    conversation_id: Optional[str] = None  # ID de conversación de Chatwoot/n8n

    def is_expired(self) -> bool:
        """Verifica si la sesión ha expirado"""
        ttl = timedelta(minutes=settings.SESSION_TTL_MINUTES)
        return datetime.now() - self.last_activity > ttl

    def update_activity(self):
        """Actualiza la última actividad"""
        self.last_activity = datetime.now()


class MessageQueue:
    """
    Cola de mensajes con debouncing para manejar múltiples mensajes rápidos.

    Cuando un usuario envía varios mensajes seguidos (ej: "Hola" + "Quiero mis horarios"),
    esta clase los junta y los procesa como uno solo después de un tiempo de espera.
    """

    def __init__(self, debounce_seconds: float = 2.0):
        self.debounce_seconds = debounce_seconds
        self.queues: Dict[str, Deque[str]] = {}  # session_id -> deque de mensajes
        self.timers: Dict[str, asyncio.Task] = {}  # session_id -> timer task
        self.locks: Dict[str, asyncio.Lock] = {}  # session_id -> lock
        self.processing: Dict[str, bool] = {}  # session_id -> is_processing

    async def add_message(self, session_id: str, message: str, process_callback) -> None:
        """
        Agrega un mensaje a la cola y resetea el timer de debouncing.

        Args:
            session_id: ID de la sesión del usuario
            message: Contenido del mensaje
            process_callback: Función async que procesa los mensajes acumulados
        """
        # Inicializar estructuras si no existen
        if session_id not in self.locks:
            self.locks[session_id] = asyncio.Lock()
            self.queues[session_id] = deque()
            self.processing[session_id] = False

        async with self.locks[session_id]:
            # Agregar mensaje a la cola
            self.queues[session_id].append(message)
            logger.info(f"📥 Mensaje agregado a queue [{session_id}]. Total en cola: {len(self.queues[session_id])}")

            # Cancelar timer anterior si existe
            if session_id in self.timers and not self.timers[session_id].done():
                self.timers[session_id].cancel()
                logger.info(f"⏱️ Timer cancelado - esperando más mensajes [{session_id}]")

            # Crear nuevo timer
            self.timers[session_id] = asyncio.create_task(
                self._debounce_timer(session_id, process_callback)
            )

    async def _debounce_timer(self, session_id: str, process_callback) -> None:
        """
        Timer de debouncing. Espera N segundos sin nuevos mensajes antes de procesar.
        """
        try:
            await asyncio.sleep(self.debounce_seconds)

            async with self.locks[session_id]:
                if self.processing[session_id]:
                    logger.warning(f"⚠️ Ya hay procesamiento en curso para [{session_id}]")
                    return

                # Marcar como procesando
                self.processing[session_id] = True

                # Obtener todos los mensajes acumulados
                messages = list(self.queues[session_id])
                self.queues[session_id].clear()

                if not messages:
                    self.processing[session_id] = False
                    return

                logger.info(f"✅ Debounce completado [{session_id}]. Procesando {len(messages)} mensaje(s)")

            # Unir mensajes con saltos de línea
            combined_message = "\n".join(messages)

            # Procesar mensaje combinado (fuera del lock para no bloquear)
            try:
                await process_callback(session_id, combined_message)
            except Exception as e:
                logger.error(f"❌ Error procesando mensajes [{session_id}]: {e}", exc_info=True)
            finally:
                # Liberar lock de procesamiento
                async with self.locks[session_id]:
                    self.processing[session_id] = False

        except asyncio.CancelledError:
            logger.info(f"🔄 Timer cancelado por nuevo mensaje [{session_id}]")
            # No hacer nada, es normal cuando llega un nuevo mensaje
        except Exception as e:
            logger.error(f"❌ Error en debounce timer [{session_id}]: {e}", exc_info=True)
            async with self.locks.get(session_id, asyncio.Lock()):
                self.processing[session_id] = False


class SessionManager:
    """Gestor de sesiones en memoria (para desarrollo)"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.users: Dict[str, Any] = {}  # Mock users storage

        # Agregar message queue con debouncing
        self.message_queue = MessageQueue(debounce_seconds=2.0)
        logger.info("✅ SessionManager inicializado con MessageQueue (debounce: 2.0s)")

    def get_session(self, session_id: str) -> Session:
        """Obtiene o crea una sesión"""
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(session_id=session_id)
            logger.info(f"Nueva sesión creada: {session_id}")

        session = self.sessions[session_id]

        # Verificar expiración
        if session.is_expired():
            logger.info(f"Sesión expirada, renovando: {session_id}")
            self.sessions[session_id] = Session(session_id=session_id)
            session = self.sessions[session_id]

        session.update_activity()
        return session

    def is_authenticated(self, session_id: str) -> bool:
        """Verifica si la sesión está autenticada"""
        session = self.get_session(session_id)
        return session.is_authenticated and not session.is_expired()

    def authenticate_user(self, session_id: str, user: Any) -> None:
        """Autentica un usuario en la sesión"""
        session = self.get_session(session_id)
        session.user_id = str(user.id)
        session.is_authenticated = True
        self.users[session_id] = user
        logger.info(f"Usuario autenticado en sesión {session_id}: {user.nombre}")

    def get_user(self, session_id: str) -> Optional[Any]:
        """Obtiene el usuario de la sesión"""
        if session_id in self.users and self.is_authenticated(session_id):
            return self.users[session_id]
        return None

    def add_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Agrega un mensaje al historial de conversación"""
        session = self.get_session(session_id)
        session.conversation_history.append(message)

        # Limitar el historial a los últimos 50 mensajes
        if len(session.conversation_history) > 50:
            session.conversation_history = session.conversation_history[-50:]

    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene el historial de conversación"""
        session = self.get_session(session_id)
        return session.conversation_history[-limit:]

    def clear_session(self, session_id: str) -> None:
        """Limpia una sesión específica"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.users:
            del self.users[session_id]
        logger.info(f"Sesión limpiada: {session_id}")

    def cleanup_expired_sessions(self) -> int:
        """Limpia sesiones expiradas"""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]

        for session_id in expired_sessions:
            self.clear_session(session_id)

        if expired_sessions:
            logger.info(f"Limpiadas {len(expired_sessions)} sesiones expiradas")

        return len(expired_sessions)

    def get_active_sessions_count(self) -> int:
        """Obtiene el número de sesiones activas"""
        return len([s for s in self.sessions.values() if not s.is_expired()])

    def get_session_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de sesiones"""
        total_sessions = len(self.sessions)
        active_sessions = self.get_active_sessions_count()
        authenticated_sessions = len([
            s for s in self.sessions.values()
            if s.is_authenticated and not s.is_expired()
        ])

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "authenticated_sessions": authenticated_sessions,
            "expired_sessions": total_sessions - active_sessions
        }

# Instancia global del gestor de sesiones
session_manager = SessionManager()