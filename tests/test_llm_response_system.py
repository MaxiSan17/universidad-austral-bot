"""
Script de testing simple para el sistema de respuestas LLM.

Este script valida que todos los módulos nuevos se importen correctamente
y que la funcionalidad básica funcione.
"""

import asyncio
from datetime import datetime
import sys

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Test imports
print("=" * 60)
print("TEST 1: Validando imports de modulos nuevos...")
print("=" * 60)

try:
    from app.models.context import (
        EmotionalState,
        QueryEntity,
        PreviousQuery,
        ProactiveSuggestion,
        ConversationContext,
        ResponseStrategy
    )
    print("[OK] app.models.context - OK")
except Exception as e:
    print(f"[ERROR] app.models.context - ERROR: {e}")
    exit(1)

try:
    from app.prompts.system_prompts import (
        build_system_prompt,
        build_user_prompt,
        get_tone_emoji,
        get_suggested_length
    )
    print("[OK] app.prompts.system_prompts - OK")
except Exception as e:
    print(f"[ERROR] app.prompts.system_prompts - ERROR: {e}")
    exit(1)

try:
    from app.utils.llm_response_generator import (
        LLMResponseGenerator,
        generate_natural_response,
        should_use_llm_generation,
        determine_data_complexity
    )
    print("[OK] app.utils.llm_response_generator - OK")
except Exception as e:
    print(f"[ERROR] app.utils.llm_response_generator - ERROR: {e}")
    exit(1)

try:
    from app.utils.response_strategy import (
        QueryEntityExtractor,
        ResponseStrategyBuilder,
        build_response_strategy
    )
    print("[OK] app.utils.response_strategy - OK")
except Exception as e:
    print(f"[ERROR] app.utils.response_strategy - ERROR: {e}")
    exit(1)

try:
    from app.utils.context_enhancer import (
        ContextEnhancer,
        enhance_conversation_context
    )
    print("[OK] app.utils.context_enhancer - OK")
except Exception as e:
    print(f"[ERROR] app.utils.context_enhancer - ERROR: {e}")
    exit(1)

print("\n" + "=" * 60)
print("TEST 2: Validando configuraciones...")
print("=" * 60)

try:
    from app.core.config import settings

    # Validar que las nuevas configuraciones existen
    assert hasattr(settings, "response_generation_mode"), "Falta response_generation_mode"
    assert hasattr(settings, "llm_response_temperature"), "Falta llm_response_temperature"
    assert hasattr(settings, "max_response_tokens"), "Falta max_response_tokens"
    assert hasattr(settings, "enable_context_enhancement"), "Falta enable_context_enhancement"
    assert hasattr(settings, "enable_proactive_suggestions"), "Falta enable_proactive_suggestions"

    print(f"[OK] Configuraciones cargadas correctamente")
    print(f"   - Response mode: {settings.response_generation_mode}")
    print(f"   - LLM temperature: {settings.llm_response_temperature}")
    print(f"   - Max tokens: {settings.max_response_tokens}")
    print(f"   - Context enhancement: {settings.enable_context_enhancement}")
    print(f"   - Proactive suggestions: {settings.enable_proactive_suggestions}")

except Exception as e:
    print(f"[ERROR] Error en configuraciones: {e}")
    exit(1)

print("\n" + "=" * 60)
print("TEST 3: Validando modelos Pydantic...")
print("=" * 60)

try:
    # Test EmotionalState
    emotional_state = EmotionalState(
        tone="animo",
        urgency_level=3,
        celebration_worthy=False,
        empathy_needed=True
    )
    print(f"[OK] EmotionalState: {emotional_state.tone}, urgency={emotional_state.urgency_level}")

    # Test QueryEntity
    entity = QueryEntity(
        entity_type="aula",
        entity_value="R3",
        confidence=0.9
    )
    print(f"[OK] QueryEntity: {entity.entity_type}={entity.entity_value} (conf={entity.confidence})")

    # Test ConversationContext
    context = ConversationContext(
        current_query="¿En qué aula tengo ética?",
        query_type="horarios",
        user_name="Juan",
        emotional_state=emotional_state,
        extracted_entities=[entity]
    )
    print(f"[OK] ConversationContext: query_type={context.query_type}, user={context.user_name}")
    print(f"   - Has urgent context: {context.has_urgent_context}")
    print(f"   - Should celebrate: {context.should_celebrate}")
    print(f"   - Needs empathy: {context.needs_empathy}")

    # Test ResponseStrategy
    strategy = ResponseStrategy(
        focus_entities=["aula"],
        length="short",
        tone="neutral",
        include_proactive=True,
        reference_history=False
    )
    print(f"[OK] ResponseStrategy: length={strategy.length}, focus={strategy.focus_entities}")

except Exception as e:
    print(f"[ERROR] Error en modelos: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("TEST 4: Validando extractores...")
print("=" * 60)

try:
    # Test QueryEntityExtractor
    extractor = QueryEntityExtractor()

    test_queries = [
        "¿En qué aula tengo ética?",
        "¿A qué hora es mi clase de programación?",
        "¿Quién es el profesor de matemática?",
        "¿Cuándo tengo clases mañana?"
    ]

    for query in test_queries:
        entities = extractor.extract_entities(query)
        print(f"[OK] Query: '{query}'")
        print(f"   Entidades: {[f'{e.entity_type}={e.entity_value}' for e in entities]}")

except Exception as e:
    print(f"[ERROR] Error en extractores: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("TEST 5: Validando prompts...")
print("=" * 60)

try:
    # Test prompt building
    test_context = ConversationContext(
        current_query="¿En qué aula tengo ética?",
        query_type="horarios",
        user_name="María",
        emotional_state=EmotionalState(tone="neutral")
    )

    test_strategy = ResponseStrategy(
        focus_entities=["aula"],
        length="short",
        tone="neutral"
    )

    system_prompt = build_system_prompt(
        agent_type="academic",
        response_type="horarios",
        context=test_context,
        strategy=test_strategy
    )

    print(f"[OK] System prompt generado ({len(system_prompt)} caracteres)")
    print(f"   Preview: {system_prompt[:150]}...")

    user_prompt = build_user_prompt(
        original_query="¿En qué aula tengo ética?",
        data_available={"aula": "R3", "materia": "Ética"},
        context=test_context,
        strategy=test_strategy
    )

    print(f"[OK] User prompt generado ({len(user_prompt)} caracteres)")
    print(f"   Preview: {user_prompt[:150]}...")

except Exception as e:
    print(f"[ERROR] Error en prompts: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("TEST 6: Validando complexity determination...")
print("=" * 60)

try:
    # Test data complexity
    simple_data = {"aula": "R3"}
    moderate_data = {"horarios": [1, 2, 3, 4]}
    complex_data = {"horarios": [i for i in range(20)]}

    complexity_simple = determine_data_complexity(simple_data)
    complexity_moderate = determine_data_complexity(moderate_data)
    complexity_complex = determine_data_complexity(complex_data)

    print(f"[OK] Simple data → {complexity_simple}")
    print(f"[OK] Moderate data → {complexity_moderate}")
    print(f"[OK] Complex data → {complexity_complex}")

except Exception as e:
    print(f"[ERROR] Error en complexity determination: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("[SUCCESS] TODOS LOS TESTS PASARON [SUCCESS]")
print("=" * 60)
print("\nEl sistema de respuestas LLM está correctamente configurado.")
print("Para probarlo en producción, asegúrate de:")
print("  1. Configurar las variables de entorno en .env")
print("  2. Tener una API key válida de OpenAI o Anthropic")
print("  3. Configurar RESPONSE_GENERATION_MODE=llm en .env")
print("\nPara testing con datos reales, ejecuta el bot y prueba con queries como:")
print("  - '¿En qué aula tengo ética?'")
print("  - '¿Cuándo tengo clases mañana?'")
print("  - '¿Quién es mi profesor de programación?'")
print("\n¡Listo para usar! ")
