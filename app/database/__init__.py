"""
Database package - Exporta todos los repositorios con Pydantic
"""
from app.database.supabase_client import SupabaseClient, user_repository
from app.database.academic_repository import academic_repository, AcademicRepository
from app.database.calendar_repository import calendar_repository, CalendarRepository

__all__ = [
    'SupabaseClient',
    'user_repository',
    'academic_repository',
    'AcademicRepository',
    'calendar_repository',
    'CalendarRepository'
]
