"""
Script de prueba para verificar el webhook de políticas

Uso:
    python test_policies_webhook.py

Este script prueba:
1. Conexión al webhook de n8n
2. Búsqueda vectorial con consulta de ejemplo
3. Formato de respuesta
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.policies_tools import PoliciesTools
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def test_webhook_connection():
    """Prueba la conexión básica al webhook"""
    print("\n" + "="*60)
    print("TEST 1: Conexión al webhook")
    print("="*60)

    tools = PoliciesTools()

    params = {
        'consulta': '¿Cuál es la asistencia mínima requerida?'
    }

    try:
        result = await tools.consultar_politicas(params)

        if result:
            print("✅ Webhook respondió correctamente")
            print(f"\nRespuesta recibida:")
            print(f"- Tiene 'respuesta': {bool(result.get('respuesta'))}")
            print(f"- Tiene 'fuentes': {bool(result.get('fuentes'))}")
            print(f"- Tiene 'error': {bool(result.get('error'))}")

            if result.get('respuesta'):
                print(f"\nRespuesta (primeros 200 chars):")
                print(result['respuesta'][:200] + "...")

            if result.get('fuentes'):
                print(f"\nFuentes encontradas: {len(result['fuentes'])}")

            return True
        else:
            print("❌ Webhook no respondió")
            return False

    except Exception as e:
        print(f"❌ Error en conexión: {e}")
        return False


async def test_syllabus_query():
    """Prueba una consulta sobre syllabus"""
    print("\n" + "="*60)
    print("TEST 2: Consulta sobre Syllabus")
    print("="*60)

    tools = PoliciesTools()

    params = {
        'consulta': '¿Qué temas se ven en el syllabus de Nativa Digital?',
        'materia': 'Nativa Digital',
        'tipo': 'syllabus'
    }

    try:
        result = await tools.consultar_politicas(params)

        if result and result.get('respuesta'):
            print("✅ Consulta de syllabus exitosa")
            print(f"\nRespuesta:")
            print(result['respuesta'][:300] + "...")
            return True
        else:
            print("❌ No se pudo obtener respuesta sobre syllabus")
            if result and result.get('error'):
                print(f"Error: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ Error en consulta: {e}")
        return False


async def test_reglamento_query():
    """Prueba una consulta sobre reglamentos"""
    print("\n" + "="*60)
    print("TEST 3: Consulta sobre Reglamento")
    print("="*60)

    tools = PoliciesTools()

    params = {
        'consulta': '¿Cuál es el porcentaje de asistencia mínimo para aprobar?',
        'tipo': 'reglamento'
    }

    try:
        result = await tools.consultar_politicas(params)

        if result and result.get('respuesta'):
            print("✅ Consulta de reglamento exitosa")
            print(f"\nRespuesta:")
            print(result['respuesta'][:300] + "...")
            return True
        else:
            print("❌ No se pudo obtener respuesta sobre reglamento")
            if result and result.get('error'):
                print(f"Error: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ Error en consulta: {e}")
        return False


async def test_legacy_methods():
    """Prueba los métodos legacy"""
    print("\n" + "="*60)
    print("TEST 4: Métodos Legacy (buscar_syllabus)")
    print("="*60)

    tools = PoliciesTools()

    params = {
        'materia': 'Programación I',
        'consulta_especifica': 'Criterios de evaluación'
    }

    try:
        result = await tools.buscar_syllabus(params)

        if result and result.get('respuesta'):
            print("✅ Método legacy funciona correctamente")
            print(f"\nRespuesta:")
            print(result['respuesta'][:300] + "...")
            return True
        else:
            print("⚠️ Método legacy no retornó respuesta esperada")
            return False

    except Exception as e:
        print(f"❌ Error en método legacy: {e}")
        return False


async def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*60)
    print("🧪 TEST DE WEBHOOK DE POLÍTICAS")
    print("="*60)
    print(f"\nWebhook URL: https://n8n.tucbbs.com.ar/webhook/a4c5728a-9853-424d-bb8d-44d2ec68d87e")
    print(f"Timeout: 60s")

    results = []

    # Test 1: Conexión
    results.append(await test_webhook_connection())

    # Test 2: Syllabus
    results.append(await test_syllabus_query())

    # Test 3: Reglamento
    results.append(await test_reglamento_query())

    # Test 4: Legacy
    results.append(await test_legacy_methods())

    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"\nTests pasados: {passed}/{total}")

    test_names = [
        "Conexión al webhook",
        "Consulta de syllabus",
        "Consulta de reglamento",
        "Método legacy"
    ]

    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")

    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron!")
    else:
        print(f"\n⚠️ {total - passed} test(s) fallaron")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
