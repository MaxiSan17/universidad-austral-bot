"""
Parser de expresiones temporales en español
Detecta y convierte expresiones como "mañana", "la semana que viene", etc. a rangos de fechas
"""
from typing import Optional, Tuple
from datetime import date, datetime, timedelta
from app.utils.logger import get_logger
import re

logger = get_logger(__name__)


class TemporalParser:
    """
    Parser de expresiones temporales en español argentino.

    Detecta expresiones como:
    - "hoy", "mañana", "pasado mañana"
    - "esta semana", "la semana que viene"
    - "este mes", "el mes que viene"
    - "en X días"
    - "próximo", "siguiente"

    Retorna rangos de fechas exactos según la expresión.
    """

    def __init__(self):
        # Expresiones de día específico (orden importa: más específico primero)
        self.day_patterns = {
            r'\bpasado\s+ma[ñn]ana\b': self._get_pasado_manana,
            r'\bma[ñn]ana\b': self._get_manana,
            r'\bhoy\b': self._get_hoy,
        }

        # Expresiones de semana
        self.week_patterns = {
            r'\besta\s+semana\b': lambda: self._get_esta_semana(),
            r'\b(la\s+)?semana\s+que\s+viene\b': lambda: self._get_semana_siguiente(),
            r'\b(la\s+)?(pr[oó]xima|siguiente)\s+semana\b': lambda: self._get_semana_siguiente(),
        }

        # Expresiones de mes
        self.month_patterns = {
            r'\beste\s+mes\b': lambda: self._get_este_mes(),
            r'\b(el\s+)?mes\s+que\s+viene\b': lambda: self._get_mes_siguiente(),
            r'\b(el\s+)?(pr[oó]ximo|siguiente)\s+mes\b': lambda: self._get_mes_siguiente(),
        }

        # Patrón para "en X días"
        self.days_ahead_pattern = r'\ben\s+(\d+)\s+d[ií]as?\b'

        # Keywords que indican "solo el próximo"
        self.proximo_keywords = [
            r'\bpr[oó]ximo\b',
            r'\bsiguiente\b',
            r'\bcu[aá]l\s+es\s+(mi|el)\s+(pr[oó]ximo|siguiente)\b'
        ]

    def parse(self, query: str) -> Tuple[Optional[date], Optional[date], bool]:
        """
        Parsea una query y extrae información temporal.

        Args:
            query: Query del usuario (en minúsculas)

        Returns:
            Tuple de (fecha_desde, fecha_hasta, solo_proximo)
            - fecha_desde: Fecha de inicio del rango (None si no hay)
            - fecha_hasta: Fecha de fin del rango (None si no hay)
            - solo_proximo: True si debe retornar solo el próximo examen
        """
        query_lower = query.lower().strip()

        # Detectar si pide "solo el próximo"
        solo_proximo = self._detect_solo_proximo(query_lower)

        # NIVEL 1: Expresiones de día específico
        for pattern, func in self.day_patterns.items():
            if re.search(pattern, query_lower):
                fecha = func()
                logger.info(f"📅 Detectado día específico: {fecha} (patrón: {pattern})")
                return fecha, fecha, solo_proximo

        # NIVEL 2: Expresiones "en X días"
        days_match = re.search(self.days_ahead_pattern, query_lower)
        if days_match:
            dias = int(days_match.group(1))
            fecha = date.today() + timedelta(days=dias)
            logger.info(f"📅 Detectado 'en {dias} días': {fecha}")
            return fecha, fecha, solo_proximo

        # NIVEL 3: Expresiones de semana
        for pattern, func in self.week_patterns.items():
            if re.search(pattern, query_lower):
                fecha_desde, fecha_hasta = func()
                logger.info(f"📅 Detectado semana: {fecha_desde} a {fecha_hasta} (patrón: {pattern})")
                return fecha_desde, fecha_hasta, solo_proximo

        # NIVEL 4: Expresiones de mes
        for pattern, func in self.month_patterns.items():
            if re.search(pattern, query_lower):
                fecha_desde, fecha_hasta = func()
                logger.info(f"📅 Detectado mes: {fecha_desde} a {fecha_hasta} (patrón: {pattern})")
                return fecha_desde, fecha_hasta, solo_proximo

        # No se detectó expresión temporal
        logger.debug("No se detectó expresión temporal en la query")
        return None, None, solo_proximo

    def _detect_solo_proximo(self, query: str) -> bool:
        """Detecta si la query pide solo el próximo examen"""
        for pattern in self.proximo_keywords:
            if re.search(pattern, query):
                logger.info(f"🎯 Detectado 'solo próximo': patrón {pattern}")
                return True
        return False

    # =====================================================
    # HELPERS - DÍA ESPECÍFICO
    # =====================================================

    def _get_hoy(self) -> date:
        """Retorna la fecha de hoy"""
        return date.today()

    def _get_manana(self) -> date:
        """Retorna la fecha de mañana"""
        return date.today() + timedelta(days=1)

    def _get_pasado_manana(self) -> date:
        """Retorna la fecha de pasado mañana"""
        return date.today() + timedelta(days=2)

    # =====================================================
    # HELPERS - SEMANA
    # =====================================================

    def _get_esta_semana(self) -> Tuple[date, date]:
        """
        Retorna el rango de 'esta semana' desde HOY hasta el domingo.

        Nota: Se filtra desde hoy para no mostrar exámenes pasados de la semana.
        """
        hoy = date.today()

        # Calcular el domingo de esta semana
        # weekday(): 0=Lunes, 6=Domingo
        dias_hasta_domingo = 6 - hoy.weekday()
        domingo = hoy + timedelta(days=dias_hasta_domingo)

        logger.debug(f"Esta semana: desde {hoy} (hoy) hasta {domingo} (domingo)")
        return hoy, domingo

    def _get_semana_siguiente(self) -> Tuple[date, date]:
        """
        Retorna el rango de 'la semana que viene' (Lunes a Domingo).

        Lógica:
        - Si hoy es Lunes-Domingo → próximo Lunes
        - Retorna exactamente 7 días (Lunes-Domingo)
        """
        hoy = date.today()

        # Calcular días hasta el próximo lunes
        # weekday(): 0=Lunes, 6=Domingo
        dias_hasta_lunes = (7 - hoy.weekday()) % 7
        if dias_hasta_lunes == 0:
            dias_hasta_lunes = 7  # Si hoy es lunes, ir al próximo

        lunes = hoy + timedelta(days=dias_hasta_lunes)
        domingo = lunes + timedelta(days=6)

        logger.debug(f"Semana siguiente: {lunes} (lunes) a {domingo} (domingo)")
        return lunes, domingo

    # =====================================================
    # HELPERS - MES
    # =====================================================

    def _get_este_mes(self) -> Tuple[date, date]:
        """
        Retorna el rango de 'este mes' desde HOY hasta fin de mes.

        Nota: Se filtra desde hoy para no mostrar exámenes pasados del mes.
        """
        hoy = date.today()

        # Último día del mes actual
        if hoy.month == 12:
            siguiente_mes = date(hoy.year + 1, 1, 1)
        else:
            siguiente_mes = date(hoy.year, hoy.month + 1, 1)

        ultimo_dia = siguiente_mes - timedelta(days=1)

        logger.debug(f"Este mes: desde {hoy} (hoy) hasta {ultimo_dia}")
        return hoy, ultimo_dia

    def _get_mes_siguiente(self) -> Tuple[date, date]:
        """
        Retorna el rango del mes siguiente (1 a último día).
        """
        hoy = date.today()

        # Primer día del mes siguiente
        if hoy.month == 12:
            primer_dia = date(hoy.year + 1, 1, 1)
        else:
            primer_dia = date(hoy.year, hoy.month + 1, 1)

        # Último día del mes siguiente
        if primer_dia.month == 12:
            siguiente_mes = date(primer_dia.year + 1, 1, 1)
        else:
            siguiente_mes = date(primer_dia.year, primer_dia.month + 1, 1)

        ultimo_dia = siguiente_mes - timedelta(days=1)

        logger.debug(f"Mes siguiente: {primer_dia} a {ultimo_dia}")
        return primer_dia, ultimo_dia

    # =====================================================
    # HELPERS - UTILIDADES
    # =====================================================

    def get_nombre_dia(self, fecha: date) -> str:
        """Retorna el nombre del día en español"""
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return dias[fecha.weekday()]

    def get_nombre_mes(self, fecha: date) -> str:
        """Retorna el nombre del mes en español"""
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        return meses[fecha.month - 1]


# Instancia global del parser
temporal_parser = TemporalParser()
