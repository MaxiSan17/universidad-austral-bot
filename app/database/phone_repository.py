"""
Repositorio para gestionar el mapeo teléfono → usuario
Implementa persistencia de autenticación por número de teléfono
"""
from typing import Optional
from datetime import datetime, timedelta
from app.database.supabase_client import SupabaseClient
from app.utils.logger import get_logger
from app.core import SupabaseError

logger = get_logger(__name__)


class PhoneRepository:
    """Repositorio para tabla telefono_usuario"""
    
    def __init__(self):
        self.client = SupabaseClient.get_client()
    
    async def get_user_by_phone(self, telefono: str, max_days: int = 30) -> Optional[str]:
        """
        Busca el usuario_id asociado a un teléfono
        
        Args:
            telefono: Número de teléfono en formato internacional
            max_days: Días máximos desde último acceso para considerar válido (default 30)
            
        Returns:
            usuario_id si existe y es reciente, None si no existe o expiró
        """
        try:
            logger.info(f"Buscando usuario asociado al teléfono {telefono}")
            
            response = self.client.table('telefono_usuario') \
                .select('usuario_id, ultimo_acceso') \
                .eq('telefono', telefono) \
                .execute()
            
            if not response.data or len(response.data) == 0:
                logger.info(f"❌ No se encontró asociación para teléfono {telefono}")
                return None
            
            record = response.data[0]
            usuario_id = record['usuario_id']
            ultimo_acceso_str = record['ultimo_acceso']
            
            # Verificar si la asociación no está expirada
            if ultimo_acceso_str:
                # Parsear fecha (Supabase devuelve ISO format)
                ultimo_acceso_dt = datetime.fromisoformat(ultimo_acceso_str.replace('Z', '+00:00'))
                dias_inactivo = (datetime.now(ultimo_acceso_dt.tzinfo) - ultimo_acceso_dt).days
                
                if dias_inactivo > max_days:
                    logger.warning(f"⏰ Asociación de {telefono} expirada ({dias_inactivo} días de inactividad)")
                    return None
                
                logger.info(f"✅ Asociación válida (último acceso hace {dias_inactivo} días)")
            
            # Actualizar ultimo_acceso
            await self.update_last_access(telefono)
            
            logger.info(f"✅ Usuario {usuario_id} encontrado para teléfono {telefono}")
            return usuario_id
            
        except Exception as e:
            logger.error(f"Error buscando usuario por teléfono: {e}", exc_info=True)
            return None
    
    async def save_phone_user_mapping(self, telefono: str, usuario_id: str) -> bool:
        """
        Guarda o actualiza la asociación teléfono → usuario
        
        Args:
            telefono: Número de teléfono
            usuario_id: UUID del usuario
            
        Returns:
            True si fue exitoso, False si hubo error
        """
        try:
            logger.info(f"Guardando asociación: {telefono} → {usuario_id}")
            
            # Upsert: insertar o actualizar si existe
            response = self.client.table('telefono_usuario') \
                .upsert({
                    'telefono': telefono,
                    'usuario_id': usuario_id,
                    'ultimo_acceso': datetime.now().isoformat()
                }, on_conflict='telefono') \
                .execute()
            
            logger.info(f"✅ Asociación guardada exitosamente: {telefono} → {usuario_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando asociación teléfono-usuario: {e}", exc_info=True)
            return False
    
    async def update_last_access(self, telefono: str) -> bool:
        """
        Actualiza la fecha de último acceso
        
        Args:
            telefono: Número de teléfono
            
        Returns:
            True si fue exitoso
        """
        try:
            self.client.table('telefono_usuario') \
                .update({'ultimo_acceso': datetime.now().isoformat()}) \
                .eq('telefono', telefono) \
                .execute()
            
            logger.debug(f"Último acceso actualizado para {telefono}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando último acceso: {e}", exc_info=True)
            return False
    
    async def delete_phone_mapping(self, telefono: str) -> bool:
        """
        Elimina la asociación de un teléfono (logout/olvidar)
        
        Args:
            telefono: Número de teléfono
            
        Returns:
            True si fue exitoso
        """
        try:
            logger.info(f"Eliminando asociación para teléfono {telefono}")
            
            self.client.table('telefono_usuario') \
                .delete() \
                .eq('telefono', telefono) \
                .execute()
            
            logger.info(f"✅ Asociación eliminada para teléfono {telefono}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando asociación: {e}", exc_info=True)
            return False
    
    async def get_all_phone_mappings(self) -> list:
        """
        Obtiene todas las asociaciones (para admin/debugging)
        
        Returns:
            Lista de diccionarios con las asociaciones
        """
        try:
            response = self.client.table('telefono_usuario') \
                .select('*') \
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error obteniendo todas las asociaciones: {e}")
            return []


# Instancia global del repositorio
phone_repository = PhoneRepository()
