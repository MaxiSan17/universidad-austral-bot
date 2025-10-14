"""
DEPRECATED: Este archivo es legacy y redirige a app.core.config

Todos los nuevos imports deben usar:
    from app.core.config import settings

Este archivo se mantiene solo para compatibilidad con código existente.
"""
import warnings

# Importar todo desde app.core.config
from app.core.config import settings, get_settings, Settings

# Mostrar warning en desarrollo
if settings.is_development:
    warnings.warn(
        "app.config is deprecated. Use 'from app.core.config import settings' instead.",
        DeprecationWarning,
        stacklevel=2
    )

# Exportar para compatibilidad
__all__ = ['settings', 'get_settings', 'Settings']
