"""
Тест времени отклика эндпоинта /api/rainbow/cases-by-color
- Полностью автоматический
- Выполняет один запрос на каждый цвет
- Warm-up и отдельный ошибочный запрос виден в логах
"""

import sys
import os
import time
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.rainbow.routes.rainbow import COLOR_MAPPING

API_BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/api/rainbow/cases-by-color"

# Все цвета для теста: русские
TEST_COLORS = list(COLOR_MAPPING.values())

def warm_up():
    """Warm-up с несуществующим цветом"""
    url = f"{API_BASE_URL}{ENDPOINT}"
    params = {"color": "TEST_INVALID_COLOR"}
    try:
        response = requests.get(url, params=params, timeout=5)
        print(f"❌ Ответ сервера: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Ошибка при warm-up: {e}")

def measure_endpoint_time(color: str) -> float:
    """Выполняет HTTP-запрос к эндпоинту и замеряет время ответа"""
    url = f"{API_BASE_URL}{ENDPOINT}"
    params = {"color": color}

    start = time.time()
    response = requests.get(url, params=params)
    duration = time.time() - start

    if response.status_code != 200:
        print(f"❌ Ошибка для цвета {color}: {response.status_code} {response.text}")
        raise RuntimeError("Эндпоинт вернул ошибку")

    payload = response.json()
    print(f"🎨 Цвет: {color} | Найдено дел: {payload.get('count')} | ⏱️ Время: {duration:.3f} сек")
    return duration

def run() -> bool:
    print("\n" + "="*60)
    print("⚡ ТЕСТ ВРЕМЕНИ ОТКЛИКА /cases-by-color (все цвета)")
    print("="*60)

    # Warm-up с ошибкой
    warm_up()

    try:
        for color in TEST_COLORS:
            measure_endpoint_time(color)

        print("\n✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО")
        return True

    except Exception as e:
        print(f"\n❌ ТЕСТ ПРОВАЛЕН: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_console(**kwargs):
    return run()

if __name__ == "__main__":
    success = run()
    import sys
    sys.exit(0 if success else 1)
