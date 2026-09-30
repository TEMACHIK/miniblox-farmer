import os
import time
import requests

# Читаем куки из переменных окружения
COOKIES = os.getenv("COOKIE_HEADER")

if not COOKIES:
    print("Ошибка: Переменная COOKIE_HEADER не задана в GitHub Secrets!")
    exit(1)

# Создаем сессию и задаем базовые заголовки
session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "Cookie": COOKIES,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

def run_ad_chain():
    try:
        # 1. Запрос на старт рекламы
        print("1. Запрос на старт рекламы...")
        start_res = session.post("https://miniblox.io/auth-api/rewarded_ad/start", json={})
        
        if start_res.status_code != 200:
            print(f"Ошибка HTTP {start_res.status_code}: {start_res.text}")
            return

        start_data = start_res.json()
        ticket = start_data.get("ticket")
        
        if not ticket:
            print(f"Ticket не получен. Ответ сервера: {start_data}")
            return

        print("Ticket успешно получен.")

        # 2. Отправка метрики: shown
        print("2. Отправка метрики: phase = shown...")
        session.post(
            "https://miniblox.io/auth-api/metrics/ad_event", 
            json={"kind": "rewarded", "phase": "shown"}
        )

        # 3. Тайм-аут просмотра рекламы (35 секунд)
        print("3. Ожидание окончания просмотра рекламы (5 секунд)...")
        time.sleep(5)

        # 4. Отправка метрики: completed
        print("4. Отправка метрики: phase = completed...")
        session.post(
            "https://miniblox.io/auth-api/metrics/ad_event", 
            json={"kind": "rewarded", "phase": "completed"}
        )

        # 5. Получение награды
        print("5. Отправка тикета на забор награды...")
        claim_res = session.post(
            "https://miniblox.io/auth-api/rewarded_ad", 
            json={"ticket": ticket}
        )
        
        print("Результат:", claim_res.json())

    except Exception as e:
        print(f"Произошла ошибка во время выполнения: {e}")

if __name__ == "__main__":
    count = 1
    while True:
        print(f"\n--- Итерация #{count} ---")
        run_ad_chain()
        count += 1
        print("Пауза 10 секунды перед следующим кругом...")
        time.sleep(10)
