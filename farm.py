import os
import time
import requests

# Читаем и очищаем куки
raw_cookies = os.getenv("COOKIE_HEADER", "")
COOKIES = raw_cookies.strip().replace("\n", "").replace("\r", "")

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "Cookie": COOKIES,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

def run_task():
    try:
        print("Запуск итерации...")
        # 1. Старт
        res = session.post("https://miniblox.io/auth-api/rewarded_ad/start", json={})
        data = res.json()
        ticket = data.get("ticket")
        if not ticket:
            print("Билет не получен")
            return

        # 2. Метрика shown
        session.post("https://miniblox.io/auth-api/metrics/ad_event", json={"kind": "rewarded", "phase": "shown"})
        
        # 3. Ожидание показа (35 секунд)
        time.sleep(35)

        # 4. Метрика completed
        session.post("https://miniblox.io/auth-api/metrics/ad_event", json={"kind": "rewarded", "phase": "completed"})

        # 5. Получение награды
        claim = session.post("https://miniblox.io/auth-api/rewarded_ad", json={"ticket": ticket})
        print("Результат:", claim.json())

    except Exception as e:
        print(f"Ошибка во время выполнения: {e}")

def main_loop():
    # Интервал между запусками цикла в секундах (например, каждые 15 минут = 900 сек)
    INTERVAL_SECONDS = 900 

    print("Запуск циклического скрипта. Нажмите Ctrl+C для остановки.")
    
    while True:
        run_task()
        print(f"Следующий запуск через {INTERVAL_SECONDS // 60} минут...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nСкрипт остановлен пользователем.")
