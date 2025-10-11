"""
Modelos Pydantic para Financial Tools

TODO: Implementar cuando se migren las tools financieras
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date
from app.models.common import BaseModelConfig, UUIDMixin


# =====================================================
# PLACEHOLDER - Para implementar después
# =====================================================

class EstadoCuentaRequest(BaseModelConfig):
    """
    Request para consultar estado de cuenta
    
    TODO: Implementar cuando se integre con sistema financiero
    """
    alumno_id: str
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    
    @validator('alumno_id')
    def validate_id(cls, v):
        return UUIDMixin.validate_uuid(v)


class EstadoCuentaResponse(BaseModelConfig):
    """
    Response de estado de cuenta
    
    TODO: Implementar cuando se integre con sistema financiero
    """
    alumno_id: str
    total_deuda: float = Field(ge=0)
    proximos_vencimientos: List[dict] = []
