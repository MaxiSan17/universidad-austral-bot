"""
Modelos Pydantic para Policies Tools

TODO: Implementar cuando se migren las tools de políticas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from app.models.common import BaseModelConfig


# =====================================================
# PLACEHOLDER - Para implementar después
# =====================================================

class SyllabusSearchRequest(BaseModelConfig):
    """
    Request para búsqueda en syllabus
    
    TODO: Implementar cuando se integre búsqueda vectorial
    """
    materia: str = Field(..., min_length=1, max_length=200)
    consulta: str = Field(..., min_length=3, description="Texto a buscar")
    match_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    max_resultados: int = Field(default=5, ge=1, le=20)
    
    @validator('consulta')
    def consulta_no_vacia(cls, v):
        if not v.strip():
            raise ValueError('consulta no puede estar vacía')
        return v.strip()


class SyllabusChunk(BaseModelConfig):
    """
    Un chunk del syllabus
    
    TODO: Implementar cuando se integre búsqueda vectorial
    """
    contenido: str
    seccion: str
    pagina: Optional[int] = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class SyllabusSearchResponse(BaseModelConfig):
    """
    Response de búsqueda en syllabus
    
    TODO: Implementar cuando se integre búsqueda vectorial
    """
    materia: str
    consulta_original: str
    chunks: List[SyllabusChunk] = []
    total: int = 0
