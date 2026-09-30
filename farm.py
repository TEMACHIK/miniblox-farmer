import os
import time
import json
from datetime import datetime
import requests

# Читаем куки из переменных окружения
COOKIES = os.getenv("COOKIE_HEADER")

if not COOKIES:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Ошибка: Переменная COOKIE_HEADER не задана в GitHub Secrets!")
    exit(1)

# Создаем сессию и задаем базовые заголовки
session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "Cookie": COOKIES,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

def log(message: str, level: str = "INFO"):
    """Вспомогательная функция для красиво оформленных логов с временем."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅",
        "WARN": "⚠️ ",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "  ")
    print(f"[{timestamp}] {prefix} {message}")

def safe_post(url: str, json_data: dict, step_name: str):
    """Выполняет POST-запрос с подробным дебагом ошибок и формата ответа."""
    log(f"[{step_name}] POST -> {url}", "DEBUG")
    log(f"[{step_name}] Payload: {json.dumps(json_data)}", "DEBUG")
    
    try:
        response = session.post(url, json=json_data, timeout=15)
        log(f"[{step_name}] Response Status: {response.status_code}", "DEBUG")
        
        # Попытка распарсить JSON
        try:
            res_json = response.json()
            log(f"[{step_name}] Response Body (JSON): {json.dumps(res_json, ensure_ascii=False)}", "DEBUG")
            return response.status_code, res_json
        except json.JSONDecodeError:
            log(f"[{step_name}] Response Body (RAW Text): {response.text[:200]}...", "WARN")
            return response.status_code, None

    except requests.exceptions.RequestException as e:
        log(f"[{step_name}] Сетевая ошибка при запросе: {e}", "ERROR")
        return None, None

def run_ad_chain():
    start_time = time.time()
    
    # 1. Запрос на старт рекламы
    log("1. Отправка запроса на старт рекламы...", "INFO")
    status, start_data = safe_post(
        "https://miniblox.io/auth-api/rewarded_ad/start", 
        {}, 
        "START_AD"
    )
    
    if status != 200 or not start_data:
        log(f"Не удалось запустить рекламу. Status: {status}", "ERROR")
        return False

    ticket = start_data.get("ticket")
    if not ticket:
        log(f"В ответе отсутствует 'ticket'. Ответ: {start_data}", "ERROR")
        return False

    log(f"Ticket успешно получен: {ticket}", "SUCCESS")

    # 2. Отправка метрики: shown
    log("2. Отправка метрики: phase = shown...", "INFO")
    safe_post(
        "https://miniblox.io/auth-api/metrics/ad_event", 
        {"kind": "rewarded", "phase": "shown"}, 
        "METRIC_SHOWN"
    )

    # 3. Тайм-аут просмотра рекламы (35 секунд)
    log("3. Старт таймера просмотра рекламы (35 секунд)...", "INFO")
    for remaining in range(35, 0, -5):
        log(f"Ожидание просмотра: осталось {remaining} сек...", "DEBUG")
        time.sleep(5)
    log("Ожидание 35 секунд завершено.", "SUCCESS")

    # 4. Отправка метрики: completed
    log("4. Отправка метрики: phase = completed...", "INFO")
    safe_post(
        "https://miniblox.io/auth-api/metrics/ad_event", 
        {"kind": "rewarded", "phase": "completed"}, 
        "METRIC_COMPLETED"
    )

    # 5. Получение награды
    log("5. Забор награды по тикету...", "INFO")
    claim_status, claim_data = safe_post(
        "https://miniblox.io/auth-api/rewarded_ad", 
        {"ticket": ticket}, 
        "CLAIM_REWARD"
    )

    elapsed = round(time.time() - start_time, 2)
    if claim_status == 200:
        log(f"Итерация завершена успешно за {elapsed}s. Результат: {claim_data}", "SUCCESS")
        return True
    else:
        log(f"Ошибка получения награды за {elapsed}s. Status: {claim_status}", "ERROR")
        return False

if __name__ == "__main__":
    log("Скрипт запущен в цикле.", "INFO")
    count = 1
    
    while True:
        print("\n" + "="*60)
        log(f"НАЧАЛО ИТЕРАЦИИ #{count}", "INFO")
        print("="*60)
        
        success = run_ad_chain()
        
        log(f"Статус итерации #{count}: {'УСПЕХ' if success else 'СБОЙ'}", "INFO" if success else "WARN")
        
        count += 1
        pause_sec = 5
        log(f"Пауза {pause_sec} секунд перед следующей итерацией...", "INFO")
        time.sleep(pause_sec)
