"""
Database package - Exporta todos los repositorios
"""
from app.database.supabase_client import SupabaseClient, user_repository
from app.database.academic_repository import academic_repository
from app.database.calendar_repository import calendar_repository

__all__ = [
    'SupabaseClient',
    'user_repository',
    'academic_repository',
    'calendar_repository'
]
