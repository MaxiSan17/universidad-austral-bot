"""
Cliente de Supabase para gestión de usuarios
"""
from supabase import create_client, Client, ClientOptions
from app.core.config import settings
from app.utils.logger import get_logger
from typing import Optional, Dict, Any
from types import SimpleNamespace

logger = get_logger(__name__)

class SupabaseClient:
    """Cliente singleton para Supabase"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Obtiene o crea la instancia del cliente de Supabase"""
        if cls._instance is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
                raise ValueError("SUPABASE_URL y SUPABASE_ANON_KEY deben estar configurados")
            
            # IMPORTANTE: Para bypass RLS, configurar Authorization header
            # con la SERVICE_ROLE_KEY
            client_options = ClientOptions(
                headers={
                    "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"
                }
            )
            
            cls._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY,  # Esta es la SERVICE_ROLE_KEY (mal nombrada en config)
                options=client_options
            )
            logger.info("✅ Cliente de Supabase inicializado con SERVICE_ROLE_KEY (bypass RLS)")
        
        return cls._instance

class UserRepository:
    """Repositorio para operaciones de usuarios en Supabase"""
    
    def __init__(self):
        self.client = SupabaseClient.get_client()
    
    async def get_user_by_dni(self, dni: str) -> Optional[SimpleNamespace]:
        """
        Busca un usuario por DNI en Supabase
        
        Args:
            dni: Número de DNI del usuario
            
        Returns:
            SimpleNamespace con datos del usuario o None si no existe
        """
        try:
            logger.info(f"🔍 Intentando buscar usuario con DNI: {dni}")
            logger.info(f"📡 Supabase URL: {settings.SUPABASE_URL}")
            logger.info(f"🔑 Supabase Key (primeros 20 chars): {settings.SUPABASE_ANON_KEY[:20]}...")
            
            response = self.client.table("usuarios").select("*").eq("dni", dni).execute()
            
            logger.info(f"📊 Response data: {response.data}")
            logger.info(f"📊 Response count: {response.count if hasattr(response, 'count') else 'N/A'}")
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(f"✅ Usuario encontrado en Supabase: {user_data.get('nombre')} {user_data.get('apellido')}")
                logger.info(f"📋 Datos completos del usuario: {user_data.keys()}")
                
                # Convertir a SimpleNamespace para compatibilidad con código existente
                return SimpleNamespace(
                    id=user_data.get("id"),
                    nombre=user_data.get("nombre"),
                    apellido=user_data.get("apellido"),
                    legajo=user_data.get("legajo"),
                    tipo=user_data.get("tipo"),
                    dni=user_data.get("dni"),
                    carrera=user_data.get("carrera"),
                    telefono=user_data.get("telefono"),
                    email=user_data.get("email")
                )
            else:
                logger.warning(f"⚠️ Usuario con DNI {dni} no encontrado en Supabase")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error buscando usuario en Supabase: {e}", exc_info=True)
            return None
    
    async def get_user_by_phone(self, phone: str) -> Optional[SimpleNamespace]:
        """
        Busca un usuario por teléfono en Supabase
        
        Args:
            phone: Número de teléfono del usuario
            
        Returns:
            SimpleNamespace con datos del usuario o None si no existe
        """
        try:
            response = self.client.table("usuarios").select("*").eq("telefono", phone).execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(f"Usuario encontrado por teléfono: {user_data.get('nombre')} {user_data.get('apellido')}")
                
                return SimpleNamespace(
                    id=user_data.get("id"),
                    nombre=user_data.get("nombre"),
                    apellido=user_data.get("apellido"),
                    legajo=user_data.get("legajo"),
                    tipo=user_data.get("tipo"),
                    dni=user_data.get("dni"),
                    carrera=user_data.get("carrera"),
                    telefono=user_data.get("telefono"),
                    email=user_data.get("email")
                )
            else:
                logger.warning(f"Usuario con teléfono {phone} no encontrado en Supabase")
                return None
                
        except Exception as e:
            logger.error(f"Error buscando usuario por teléfono en Supabase: {e}", exc_info=True)
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[SimpleNamespace]:
        """
        Busca un usuario por ID (UUID) en Supabase
        
        Args:
            user_id: UUID del usuario
            
        Returns:
            SimpleNamespace con datos del usuario o None si no existe
        """
        try:
            response = self.client.table("usuarios").select("*").eq("id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(f"Usuario encontrado por ID: {user_data.get('nombre')} {user_data.get('apellido')}")
                
                return SimpleNamespace(
                    id=user_data.get("id"),
                    nombre=user_data.get("nombre"),
                    apellido=user_data.get("apellido"),
                    legajo=user_data.get("legajo"),
                    tipo=user_data.get("tipo"),
                    dni=user_data.get("dni"),
                    carrera=user_data.get("carrera"),
                    telefono=user_data.get("telefono"),
                    email=user_data.get("email")
                )
            else:
                logger.warning(f"Usuario con ID {user_id} no encontrado en Supabase")
                return None
                
        except Exception as e:
            logger.error(f"Error buscando usuario por ID en Supabase: {e}", exc_info=True)
            return None

# Instancia global del repositorio
user_repository = UserRepository()
