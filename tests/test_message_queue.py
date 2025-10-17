import pytest
import asyncio
from app.session.session_manager import MessageQueue


@pytest.mark.asyncio
async def test_message_queue_debouncing():
    """Test que verifica que el debouncing junta mensajes correctos"""

    processed_messages = []

    async def mock_callback(session_id: str, message: str):
        processed_messages.append(message)

    queue = MessageQueue(debounce_seconds=0.5)  # 0.5 seg para test rápido

    # Simular 3 mensajes rápidos
    await queue.add_message("test_session", "Mensaje 1", mock_callback)
    await asyncio.sleep(0.1)
    await queue.add_message("test_session", "Mensaje 2", mock_callback)
    await asyncio.sleep(0.1)
    await queue.add_message("test_session", "Mensaje 3", mock_callback)

    # Esperar a que se procese
    await asyncio.sleep(1.0)

    # Verificar que se procesó 1 solo mensaje combinado
    assert len(processed_messages) == 1
    assert "Mensaje 1" in processed_messages[0]
    assert "Mensaje 2" in processed_messages[0]
    assert "Mensaje 3" in processed_messages[0]


@pytest.mark.asyncio
async def test_message_queue_separate_sessions():
    """Test que verifica que sesiones diferentes no se mezclan"""

    processed_messages = {}

    async def mock_callback(session_id: str, message: str):
        processed_messages[session_id] = message

    queue = MessageQueue(debounce_seconds=0.5)

    # Mensajes de 2 sesiones diferentes
    await queue.add_message("session_1", "Mensaje A", mock_callback)
    await queue.add_message("session_2", "Mensaje B", mock_callback)

    await asyncio.sleep(1.0)

    # Verificar que cada sesión procesó su mensaje
    assert len(processed_messages) == 2
    assert processed_messages["session_1"] == "Mensaje A"
    assert processed_messages["session_2"] == "Mensaje B"


@pytest.mark.asyncio
async def test_message_queue_timer_reset():
    """Test que verifica que el timer se resetea con cada mensaje nuevo"""

    processed_messages = []
    processing_times = []

    async def mock_callback(session_id: str, message: str):
        import time
        processing_times.append(time.time())
        processed_messages.append(message)

    queue = MessageQueue(debounce_seconds=0.5)

    # Enviar 3 mensajes con intervalos de 0.3 segundos
    # Cada mensaje nuevo debe resetear el timer
    start_time = asyncio.get_event_loop().time()

    await queue.add_message("test_session", "Mensaje 1", mock_callback)
    await asyncio.sleep(0.3)
    await queue.add_message("test_session", "Mensaje 2", mock_callback)
    await asyncio.sleep(0.3)
    await queue.add_message("test_session", "Mensaje 3", mock_callback)

    # Esperar a que se procese (0.5s después del último mensaje)
    await asyncio.sleep(1.0)

    # Verificar que se procesó 1 solo mensaje combinado
    assert len(processed_messages) == 1
    assert "Mensaje 1" in processed_messages[0]
    assert "Mensaje 2" in processed_messages[0]
    assert "Mensaje 3" in processed_messages[0]

    # El tiempo total debe ser aproximadamente 0.3 + 0.3 + 0.5 = 1.1 segundos
    elapsed = asyncio.get_event_loop().time() - start_time
    assert 1.0 < elapsed < 1.5  # Margen de error


@pytest.mark.asyncio
async def test_message_queue_error_handling():
    """Test que verifica el manejo de errores en el callback"""

    processed_messages = []
    error_count = [0]  # Usar lista para poder modificar en nested function

    async def failing_callback(session_id: str, message: str):
        error_count[0] += 1
        if error_count[0] == 1:
            raise Exception("Simulated error")
        else:
            processed_messages.append(message)

    queue = MessageQueue(debounce_seconds=0.3)

    # Primer mensaje debería fallar
    await queue.add_message("test_session", "Mensaje con error", failing_callback)
    await asyncio.sleep(0.5)

    # Verificar que NO se procesó debido al error
    assert len(processed_messages) == 0
    assert error_count[0] == 1

    # Segundo mensaje debería funcionar
    await queue.add_message("test_session", "Mensaje exitoso", failing_callback)
    await asyncio.sleep(0.5)

    # Verificar que el segundo mensaje se procesó correctamente
    assert len(processed_messages) == 1
    assert processed_messages[0] == "Mensaje exitoso"


@pytest.mark.asyncio
async def test_message_queue_concurrent_sessions():
    """Test que verifica el manejo concurrente de múltiples sesiones"""

    processed_messages = {}

    async def mock_callback(session_id: str, message: str):
        processed_messages[session_id] = message

    queue = MessageQueue(debounce_seconds=0.3)

    # Simular 3 sesiones enviando mensajes simultáneamente
    await asyncio.gather(
        queue.add_message("session_1", "Mensaje A1", mock_callback),
        queue.add_message("session_2", "Mensaje B1", mock_callback),
        queue.add_message("session_3", "Mensaje C1", mock_callback),
    )

    await asyncio.sleep(0.1)

    # Agregar segundos mensajes a cada sesión
    await asyncio.gather(
        queue.add_message("session_1", "Mensaje A2", mock_callback),
        queue.add_message("session_2", "Mensaje B2", mock_callback),
        queue.add_message("session_3", "Mensaje C2", mock_callback),
    )

    # Esperar a que se procesen todas
    await asyncio.sleep(0.6)

    # Verificar que cada sesión recibió sus mensajes combinados
    assert len(processed_messages) == 3
    assert "Mensaje A1" in processed_messages["session_1"]
    assert "Mensaje A2" in processed_messages["session_1"]
    assert "Mensaje B1" in processed_messages["session_2"]
    assert "Mensaje B2" in processed_messages["session_2"]
    assert "Mensaje C1" in processed_messages["session_3"]
    assert "Mensaje C2" in processed_messages["session_3"]
