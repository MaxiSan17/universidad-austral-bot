"""
Test del flujo completo de saludos
"""
import asyncio
from app.agents.query_classifier import query_classifier
from app.utils.greeting_detector import greeting_detector

async def test_greeting_classification():
    """Prueba la clasificación de diferentes tipos de mensajes"""

    test_cases = [
        # Saludos puros (deben clasificarse como 'greeting')
        ("Hola", "greeting"),
        ("Buenas tardes", "greeting"),
        ("Que tal?", "greeting"),
        ("Buenos dias", "greeting"),

        # Saludo + consulta (NO deben clasificarse como greeting)
        ("Hola, quiero saber mi horario", "academic"),
        ("Buenas, tengo un parcial?", "calendar"),
        ("Hola, cuanto debo?", "financial"),
        ("Que tal, quiero ver el programa de la materia", "policies"),

        # Consultas sin saludo
        ("Cual es mi horario de manana?", "academic"),
        ("Cuando es el final de matematica?", "calendar"),
        ("Tengo deudas?", "financial"),
    ]

    print("=" * 80)
    print("TEST DE CLASIFICACIÓN DE QUERIES CON SALUDOS")
    print("=" * 80)

    passed = 0
    failed = 0

    for query, expected_agent in test_cases:
        # Clasificar
        agent, confidence, method = query_classifier.classify(query)

        # Verificar
        success = agent == expected_agent
        status = "[PASS]" if success else "[FAIL]"

        if success:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}")
        print(f"  Query:    '{query}'")
        print(f"  Expected: {expected_agent}")
        print(f"  Got:      {agent} (confidence: {confidence:.2f}, method: {method})")

        # Detalles de detección
        is_greeting = greeting_detector.is_greeting(query)
        has_content = greeting_detector.has_content_beyond_greeting(query)
        if has_content:
            cleaned = greeting_detector.remove_greeting_from_message(query)
            print(f"  Greeting?: {is_greeting}, Has content beyond?: {has_content}")
            print(f"  Cleaned query: '{cleaned}'")
        else:
            print(f"  Greeting?: {is_greeting}, Has content beyond?: {has_content}")

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_greeting_classification())
