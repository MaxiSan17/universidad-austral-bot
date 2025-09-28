"""
Script simple para testear el bot de Universidad Austral
"""

import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import asyncio
from src.agents.orchestrator import orchestrator

async def test_conversation():
    """Simula una conversación completa con el bot"""

    print("🎓 Testeando Universidad Austral Bot")
    print("=" * 40)

    session_id = "test_session_123"

    # Test 1: Saludo sin autenticación
    print("\n1️⃣ Test: Saludo inicial")
    response = await orchestrator.process_message("Hola", session_id)
    print(f"Bot: {response}")

    # Test 2: Autenticación con DNI válido
    print("\n2️⃣ Test: Autenticación")
    response = await orchestrator.process_message("12345678", session_id)
    print(f"Bot: {response}")

    # Test 3: Consulta académica
    print("\n3️⃣ Test: Consulta académica")
    response = await orchestrator.process_message("¿Cuándo tengo clases?", session_id)
    print(f"Bot: {response}")

    # Test 4: Consulta financiera
    print("\n4️⃣ Test: Consulta financiera")
    response = await orchestrator.process_message("¿Tengo deudas?", session_id)
    print(f"Bot: {response}")

    # Test 5: Consulta de políticas
    print("\n5️⃣ Test: Consulta de políticas")
    response = await orchestrator.process_message("¿Qué temas vemos en Nativa Digital?", session_id)
    print(f"Bot: {response}")

    # Test 6: Consulta de calendario
    print("\n6️⃣ Test: Consulta de calendario")
    response = await orchestrator.process_message("¿Cuándo es el parcial?", session_id)
    print(f"Bot: {response}")

    print("\n✅ Tests completados!")

async def test_authentication_flow():
    """Testa el flujo de autenticación"""
    print("\n🔐 Testeando flujo de autenticación")
    print("=" * 40)

    session_id = "auth_test_456"

    # DNI inválido
    print("\n❌ Test: DNI inválido")
    response = await orchestrator.process_message("99999999", session_id)
    print(f"Bot: {response}")

    # DNI válido
    print("\n✅ Test: DNI válido")
    response = await orchestrator.process_message("87654321", session_id)
    print(f"Bot: {response}")

if __name__ == "__main__":
    print("🚀 Iniciando tests del bot...")

    # Ejecutar tests
    asyncio.run(test_conversation())
    asyncio.run(test_authentication_flow())

    print("\n🎉 ¡Todos los tests completados!")
    print("Para probar la API completa, ejecuta: python main.py")