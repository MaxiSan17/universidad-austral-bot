"""
Script de prueba para verificar el sistema de clasificación con fuzzy matching
"""
from app.agents.academic_agent import AcademicAgent
from app.agents.calendar_agent import CalendarAgent


def test_academic_classification():
    """Prueba la clasificación académica con typos"""
    agent = AcademicAgent()

    print("=" * 60)
    print("PRUEBAS DE CLASIFICACIÓN ACADÉMICA")
    print("=" * 60)

    test_cases = [
        # Match exacto
        ("horario de nativa", "horarios"),
        ("que materias estoy cursando", "inscripciones"),
        ("quien es el profesor de matematica", "profesores"),
        ("donde es la clase de nativa", "aulas"),
        ("cuantos creditos vu tengo", "creditos_vu"),

        # Typos comunes
        ("horaios de nativa", "horarios"),  # typo en "horarios"
        ("orario de clase", "horarios"),    # typo en "horario"
        ("clace de programacion", "horarios"),  # typo en "clase"
        ("inscripion a materias", "inscripciones"),  # typo en "inscripción"
        ("porfe de matematica", "profesores"),  # typo en "profe"
        ("doente de nativa", "profesores"),  # typo en "docente"

        # Consultas ambiguas (deberían ser "general")
        ("hola", "general"),
        ("ayuda", "general"),
    ]

    for query, expected in test_cases:
        result = agent._classify_academic_query(query.lower())
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} '{query}' -> {result} (esperado: {expected})")

    print()


def test_calendar_classification():
    """Prueba la clasificación de calendario con typos"""
    agent = CalendarAgent()

    print("=" * 60)
    print("PRUEBAS DE CLASIFICACIÓN DE CALENDARIO")
    print("=" * 60)

    test_cases = [
        # Match exacto
        ("cuando es el parcial de nativa", "examenes"),
        ("que eventos hay en marzo", "eventos"),
        ("cuando es feriado", "feriados"),

        # Typos comunes
        ("cuanddo es el examen", "examenes"),  # typo en "cuando"
        ("parical de matematica", "examenes"),  # typo en "parcial"
        ("fernado del lunes", "feriados"),  # typo en "feriado"
        ("evnto importante", "eventos"),  # typo en "evento"

        # Consultas ambiguas
        ("hola", "general"),
    ]

    for query, expected in test_cases:
        result = agent._classify_calendar_query(query.lower())
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} '{query}' -> {result} (esperado: {expected})")

    print()


def test_fuzzy_matching():
    """Prueba específica del algoritmo de fuzzy matching"""
    agent = AcademicAgent()

    print("=" * 60)
    print("PRUEBAS DE FUZZY MATCHING (SIMILITUD)")
    print("=" * 60)

    test_cases = [
        ("horario", ["horario", "horarios"], True),
        ("horaios", ["horario", "horarios"], True),  # typo
        ("orario", ["horario", "horarios"], True),   # typo
        ("profesor", ["profesor", "profesora"], True),
        ("porfe", ["profe", "profesor"], True),       # typo
        ("doente", ["docente"], True),                # typo
        ("xyz123", ["horario", "clase"], False),      # no match
    ]

    for word, keywords, should_match in test_cases:
        result = agent._check_keywords_fuzzy(word, keywords, threshold=0.75)
        status = "[OK]" if result == should_match else "[FAIL]"
        match_text = "MATCH" if result else "NO MATCH"
        print(f"{status} '{word}' vs {keywords} -> {match_text} (esperado: {'MATCH' if should_match else 'NO MATCH'})")

    print()


if __name__ == "__main__":
    test_academic_classification()
    test_calendar_classification()
    test_fuzzy_matching()

    print("=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)
    print()
    print("NOTAS:")
    print("- [OK] = Clasificacion correcta")
    print("- [FAIL] = Clasificacion incorrecta (puede necesitar ajuste de threshold)")
    print("- Threshold actual: 0.75 (75% de similitud)")
    print("- Para casos complejos, el LLM fallback se activara automaticamente")
