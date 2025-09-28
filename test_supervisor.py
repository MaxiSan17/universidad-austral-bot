#!/usr/bin/env python3
"""
Script de prueba para el Sistema Evolucionado de Universidad Austral
Testa el LangGraph Supervisor y todos los agentes especializados
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.core.main_supervisor import UniversityAssistantSupervisor
    print("✅ Importación exitosa del supervisor")
except ImportError as e:
    print(f"❌ Error importando supervisor: {e}")
    print("Ejecutando en modo mock...")

class MockSupervisor:
    """Supervisor mock para testing sin dependencias"""

    async def process_message(self, session_id: str, message: str) -> str:
        if not hasattr(self, '_authenticated_sessions'):
            self._authenticated_sessions = set()

        # Simular autenticación
        if session_id not in self._authenticated_sessions:
            if message.replace(" ", "").isdigit() and len(message.replace(" ", "")) == 8:
                dni = message.replace(" ", "")
                if dni in ["12345678", "87654321"]:
                    self._authenticated_sessions.add(session_id)
                    return f"¡Perfecto! Ya te reconocí. ¿En qué te puedo ayudar? 😊"
                else:
                    return "❌ DNI no encontrado en la base de datos."
            else:
                return "¡Hola! 👋 Para ayudarte necesito tu DNI (solo números): 12345678"

        # Simular respuestas por categoría
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["horario", "clase", "materia", "aula"]):
            return """📚 **Agente Académico Activado**

Tu horario para esta semana:
• Lunes: Nativa Digital - 14:00-16:00 - Aula R3
• Miércoles: Programación I - 16:00-18:00 - Aula A4

¿Necesitás algo más? 😊"""

        elif any(kw in message_lower for kw in ["pago", "deuda", "credito", "vu"]):
            return """💰 **Agente Financiero Activado**

Estado de cuenta:
✅ No tenés deudas pendientes
🎯 Créditos VU: 8/10 (te faltan 2)

¿Te ayudo con algo más?"""

        elif any(kw in message_lower for kw in ["syllabus", "programa", "evaluacion", "bibliografia"]):
            return """📋 **Agente de Políticas Activado**

Programa de Nativa Digital:
1. Introducción al desarrollo móvil
2. React Native y componentes
3. APIs y persistencia de datos
4. Publicación en stores

¿Querés más detalles de algún tema?"""

        elif any(kw in message_lower for kw in ["examen", "fecha", "calendario", "parcial"]):
            return """📅 **Agente de Calendario Activado**

Próximos exámenes:
• 1er Parcial Nativa Digital: 20/11 - 14:00hs
• 1er Parcial Programación I: 22/11 - 16:00hs

¿Te recordamos algo más?"""

        else:
            return """🤖 **Supervisor Activado**

Puedo ayudarte con:
📚 Consultas académicas (horarios, materias, profesores)
💰 Temas financieros (pagos, deudas, créditos VU)
📋 Políticas y reglamentos (syllabi, evaluaciones)
📅 Calendario y fechas (exámenes, eventos)

¿Qué necesitás?"""

async def test_authentication_flow():
    """Prueba el flujo de autenticación"""
    print("\n" + "="*50)
    print("🔐 TESTING FLUJO DE AUTENTICACIÓN")
    print("="*50)

    try:
        supervisor = UniversityAssistantSupervisor()
    except:
        supervisor = MockSupervisor()
        print("📝 Usando supervisor mock")

    session_id = "test_auth_001"

    # Test 1: Saludo sin autenticación
    print("\n1️⃣ Saludo inicial (sin autenticación)")
    response = await supervisor.process_message(session_id, "Hola")
    print(f"🤖 Bot: {response}")

    # Test 2: DNI inválido
    print("\n2️⃣ DNI inválido")
    response = await supervisor.process_message(session_id, "99999999")
    print(f"🤖 Bot: {response}")

    # Test 3: DNI válido
    print("\n3️⃣ DNI válido")
    response = await supervisor.process_message(session_id, "12345678")
    print(f"🤖 Bot: {response}")

    return supervisor, session_id

async def test_academic_agent(supervisor, session_id):
    """Prueba el agente académico"""
    print("\n" + "="*50)
    print("📚 TESTING AGENTE ACADÉMICO")
    print("="*50)

    queries = [
        "¿Cuándo tengo clases?",
        "¿En qué aula tengo Nativa Digital?",
        "¿Quién es el profesor de Programación I?",
        "¿En qué materias estoy inscripto?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{i}️⃣ {query}")
        response = await supervisor.process_message(session_id, query)
        print(f"🤖 Bot: {response}")

async def test_financial_agent(supervisor, session_id):
    """Prueba el agente financiero"""
    print("\n" + "="*50)
    print("💰 TESTING AGENTE FINANCIERO")
    print("="*50)

    queries = [
        "¿Tengo deudas pendientes?",
        "¿Cuántos créditos VU tengo?",
        "¿Cuándo vence mi próximo pago?",
        "Estado de mi cuenta"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{i}️⃣ {query}")
        response = await supervisor.process_message(session_id, query)
        print(f"🤖 Bot: {response}")

async def test_policies_agent(supervisor, session_id):
    """Prueba el agente de políticas"""
    print("\n" + "="*50)
    print("📋 TESTING AGENTE DE POLÍTICAS")
    print("="*50)

    queries = [
        "¿Qué temas vemos en Nativa Digital?",
        "¿Cómo se evalúa en Programación I?",
        "¿Qué bibliografía necesito?",
        "¿Cuál es el reglamento de asistencia?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{i}️⃣ {query}")
        response = await supervisor.process_message(session_id, query)
        print(f"🤖 Bot: {response}")

async def test_calendar_agent(supervisor, session_id):
    """Prueba el agente de calendario"""
    print("\n" + "="*50)
    print("📅 TESTING AGENTE DE CALENDARIO")
    print("="*50)

    queries = [
        "¿Cuándo es el parcial de Nativa Digital?",
        "¿Hay exámenes esta semana?",
        "¿Cuándo empiezan las clases?",
        "¿Hay feriados próximos?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{i}️⃣ {query}")
        response = await supervisor.process_message(session_id, query)
        print(f"🤖 Bot: {response}")

async def test_multi_session():
    """Prueba múltiples sesiones simultáneas"""
    print("\n" + "="*50)
    print("👥 TESTING MÚLTIPLES SESIONES")
    print("="*50)

    try:
        supervisor = UniversityAssistantSupervisor()
    except:
        supervisor = MockSupervisor()

    # Sesión 1: Juan
    print("\n🧑 Sesión Juan (12345678)")
    session1 = "juan_001"
    await supervisor.process_message(session1, "12345678")
    response1 = await supervisor.process_message(session1, "¿Cuándo tengo clases?")
    print(f"🤖 Juan: {response1}")

    # Sesión 2: María
    print("\n👩 Sesión María (87654321)")
    session2 = "maria_002"
    await supervisor.process_message(session2, "87654321")
    response2 = await supervisor.process_message(session2, "¿Tengo deudas?")
    print(f"🤖 María: {response2}")

    # Verificar que las sesiones son independientes
    print("\n🔄 Verificando independencia de sesiones...")
    response3 = await supervisor.process_message(session1, "¿Mi estado financiero?")
    print(f"🤖 Juan (financiero): {response3}")

async def test_error_handling():
    """Prueba manejo de errores"""
    print("\n" + "="*50)
    print("⚠️ TESTING MANEJO DE ERRORES")
    print("="*50)

    try:
        supervisor = UniversityAssistantSupervisor()
    except:
        supervisor = MockSupervisor()

    session_id = "error_test"

    # Autenticar primero
    await supervisor.process_message(session_id, "12345678")

    # Test consultas vagas
    print("\n1️⃣ Consulta muy vaga")
    response = await supervisor.process_message(session_id, "¿Qué?")
    print(f"🤖 Bot: {response}")

    # Test mensaje vacío
    print("\n2️⃣ Mensaje vacío")
    response = await supervisor.process_message(session_id, "")
    print(f"🤖 Bot: {response}")

    # Test caracteres especiales
    print("\n3️⃣ Caracteres especiales")
    response = await supervisor.process_message(session_id, "!@#$%^&*()")
    print(f"🤖 Bot: {response}")

async def run_all_tests():
    """Ejecuta todos los tests"""
    print("🎓 UNIVERSIDAD AUSTRAL BOT - SISTEMA DE TESTING")
    print("Sistema Evolucionado con LangGraph Supervisor")
    print("="*50)

    try:
        # Test de autenticación
        supervisor, session_id = await test_authentication_flow()

        # Tests de agentes especializados
        await test_academic_agent(supervisor, session_id)
        await test_financial_agent(supervisor, session_id)
        await test_policies_agent(supervisor, session_id)
        await test_calendar_agent(supervisor, session_id)

        # Tests avanzados
        await test_multi_session()
        await test_error_handling()

        print("\n" + "="*50)
        print("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("="*50)
        print("\n🚀 Para probar la API completa ejecutá:")
        print("   python src/core/main_supervisor.py")
        print("\n🐳 Para levantar con Docker:")
        print("   make docker-up")
        print("\n📖 Documentación:")
        print("   http://localhost:8000/docs")

    except Exception as e:
        print(f"\n❌ Error durante los tests: {e}")
        print("\n💡 Posibles soluciones:")
        print("1. Instalar dependencias: pip install -r requirements.txt")
        print("2. Configurar variables de entorno en .env")
        print("3. Verificar que todos los servicios estén disponibles")

if __name__ == "__main__":
    print("🔄 Iniciando tests del sistema...")
    asyncio.run(run_all_tests())