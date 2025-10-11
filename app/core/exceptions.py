"""
Excepciones custom del sistema
"""
from typing import Optional, Dict, Any


class UniversidadAustralException(Exception):
    """Excepción base para todas las excepciones del sistema"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a diccionario"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


# =====================================================
# EXCEPCIONES DE VALIDACIÓN
# =====================================================

class ValidationError(UniversidadAustralException):
    """Error de validación de datos"""
    pass


class InvalidDNIError(ValidationError):
    """DNI inválido"""
    
    def __init__(self, dni: str):
        super().__init__(
            message=f"DNI '{dni}' no es válido",
            error_code="INVALID_DNI",
            details={"dni": dni}
        )


class InvalidUUIDError(ValidationError):
    """UUID inválido"""
    
    def __init__(self, uuid_str: str):
        super().__init__(
            message=f"UUID '{uuid_str}' no es válido",
            error_code="INVALID_UUID",
            details={"uuid": uuid_str}
        )


class InvalidDateRangeError(ValidationError):
    """Rango de fechas inválido"""
    
    def __init__(self, fecha_desde: str, fecha_hasta: str):
        super().__init__(
            message=f"Rango de fechas inválido: {fecha_desde} a {fecha_hasta}",
            error_code="INVALID_DATE_RANGE",
            details={"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta}
        )


# =====================================================
# EXCEPCIONES DE BASE DE DATOS
# =====================================================

class DatabaseError(UniversidadAustralException):
    """Error genérico de base de datos"""
    pass


class SupabaseError(DatabaseError):
    """Error de Supabase"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=f"Error en Supabase: {message}",
            error_code="SUPABASE_ERROR",
            details={"operation": operation}
        )


class RecordNotFoundError(DatabaseError):
    """Registro no encontrado"""
    
    def __init__(self, table: str, identifier: str):
        super().__init__(
            message=f"No se encontró registro en '{table}' con identificador '{identifier}'",
            error_code="RECORD_NOT_FOUND",
            details={"table": table, "identifier": identifier}
        )


class DuplicateRecordError(DatabaseError):
    """Registro duplicado"""
    
    def __init__(self, table: str, field: str, value: str):
        super().__init__(
            message=f"Ya existe un registro en '{table}' con {field}='{value}'",
            error_code="DUPLICATE_RECORD",
            details={"table": table, "field": field, "value": value}
        )


# =====================================================
# EXCEPCIONES DE AUTENTICACIÓN
# =====================================================

class AuthenticationError(UniversidadAustralException):
    """Error de autenticación"""
    pass


class UserNotFoundError(AuthenticationError):
    """Usuario no encontrado"""
    
    def __init__(self, dni: str):
        super().__init__(
            message=f"Usuario con DNI '{dni}' no encontrado",
            error_code="USER_NOT_FOUND",
            details={"dni": dni}
        )


class SessionExpiredError(AuthenticationError):
    """Sesión expirada"""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Sesión '{session_id}' expirada",
            error_code="SESSION_EXPIRED",
            details={"session_id": session_id}
        )


# =====================================================
# EXCEPCIONES DE HERRAMIENTAS
# =====================================================

class ToolError(UniversidadAustralException):
    """Error en herramienta"""
    pass


class ToolNotAvailableError(ToolError):
    """Herramienta no disponible"""
    
    def __init__(self, tool_name: str):
        super().__init__(
            message=f"Herramienta '{tool_name}' no está disponible",
            error_code="TOOL_NOT_AVAILABLE",
            details={"tool_name": tool_name}
        )


class ToolTimeoutError(ToolError):
    """Timeout en herramienta"""
    
    def __init__(self, tool_name: str, timeout: int):
        super().__init__(
            message=f"Timeout en herramienta '{tool_name}' después de {timeout} segundos",
            error_code="TOOL_TIMEOUT",
            details={"tool_name": tool_name, "timeout": timeout}
        )


# =====================================================
# EXCEPCIONES DE INTEGRACIÓN
# =====================================================

class IntegrationError(UniversidadAustralException):
    """Error de integración con servicios externos"""
    pass


class ChatwootError(IntegrationError):
    """Error de Chatwoot"""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Error en Chatwoot: {message}",
            error_code="CHATWOOT_ERROR"
        )


class N8NError(IntegrationError):
    """Error de n8n"""
    
    def __init__(self, message: str, webhook_name: Optional[str] = None):
        super().__init__(
            message=f"Error en n8n: {message}",
            error_code="N8N_ERROR",
            details={"webhook_name": webhook_name}
        )


class LLMError(IntegrationError):
    """Error del modelo de lenguaje"""
    
    def __init__(self, message: str, model: Optional[str] = None):
        super().__init__(
            message=f"Error en LLM: {message}",
            error_code="LLM_ERROR",
            details={"model": model}
        )


# =====================================================
# EXCEPCIONES DE NEGOCIO
# =====================================================

class BusinessLogicError(UniversidadAustralException):
    """Error de lógica de negocio"""
    pass


class InscripcionNoEncontradaError(BusinessLogicError):
    """Alumno no inscripto en materia"""
    
    def __init__(self, alumno_id: str, materia: Optional[str] = None):
        message = f"Alumno '{alumno_id}' no tiene inscripciones"
        if materia:
            message += f" en '{materia}'"
        
        super().__init__(
            message=message,
            error_code="NO_INSCRIPCION",
            details={"alumno_id": alumno_id, "materia": materia}
        )


class CreditosVUInsuficientesError(BusinessLogicError):
    """Créditos VU insuficientes"""
    
    def __init__(self, creditos_actuales: int, creditos_requeridos: int):
        super().__init__(
            message=f"Créditos VU insuficientes: {creditos_actuales}/{creditos_requeridos}",
            error_code="CREDITOS_VU_INSUFICIENTES",
            details={
                "creditos_actuales": creditos_actuales,
                "creditos_requeridos": creditos_requeridos,
                "creditos_faltantes": creditos_requeridos - creditos_actuales
            }
        )


# =====================================================
# EXCEPCIONES DE RATE LIMITING
# =====================================================

class RateLimitError(UniversidadAustralException):
    """Límite de tasa excedido"""
    
    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Límite de {limit} requests por {window} excedido",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window}
        )
