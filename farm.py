import os
import time
import requests

COOKIES = os.getenv("COOKIE_HEADER")

if not COOKIES:
    print("Ошибка: Переменная COOKIE_HEADER не задана в GitHub Secrets!")
    exit(1)

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
        
        # Перехватываем слишком частые запросы (HTTP 429 Rate Limit)
        if start_res.status_code == 429:
            print("🛑 [ЛИМИТ ЧАСТОТЫ] Слишком много запросов (Rate Limit / Too Many Requests).")
            return "RATE_LIMIT"

        # Перехватываем сбои сервера или запрет (HTTP 400 / 403 / 500)
        if start_res.status_code != 200:
            print(f"⚠️ Ошибка HTTP {start_res.status_code}: {start_res.text}")
            return "ERROR"

        start_data = start_res.json()
        
        # Проверка текста ошибки внутри JSON (например, "Limit reached" или "Cooldown")
        error_msg = str(start_data.get("error", "")).lower()
        message = str(start_data.get("message", "")).lower()
        
        if "limit" in error_msg or "limit" in message or "cooldown" in error_msg or "cooldown" in message:
            print(f"🛑 [ЛИМИТ ПРОСМОТРОВ] Ответ сервера: {start_data}")
            return "LIMIT_REACHED"

        ticket = start_data.get("ticket")
        if not ticket:
            print(f"⚠️ Ticket не получен. Ответ сервера: {start_data}")
            return "ERROR"

        print("Ticket успешно получен.")

        # 2. Отправка метрики: shown
        print("2. Отправка метрики: phase = shown...")
        session.post(
            "https://miniblox.io/auth-api/metrics/ad_event", 
            json={"kind": "rewarded", "phase": "shown"}
        )

        # 3. Тайм-аут просмотра рекламы (35 секунд)
        print("3. Ожидание окончания просмотра рекламы (35 секунд)...")
        time.sleep(35)

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
        
        if claim_res.status_code == 200:
            claim_data = claim_res.json()
            print("🎉 Результат забора награды:", claim_data)
            
            claim_err = str(claim_data.get("error", "")).lower()
            if "limit" in claim_err or "cooldown" in claim_err:
                print("🛑 [ЛИМИТ ПРОСМОТРОВ] При заборе награды обнаружен лимит.")
                return "LIMIT_REACHED"
            
            return "SUCCESS"
        else:
            print(f"⚠️ Ошибка забора награды HTTP {claim_res.status_code}: {claim_res.text}")
            return "ERROR"

    except Exception as e:
        print(f"⚠️ Произошла ошибка во время выполнения: {e}")
        return "ERROR"

if __name__ == "__main__":
    count = 1
    
    while True:
        print(f"\n--- Итерация #{count} ---")
        status = run_ad_chain()

        if status == "LIMIT_REACHED":
            print("⚠️ [ЛИМИТ] Достигнут лимит просмотра рекламы. Ждем 60 секунд перед следующей попыткой...")
            time.sleep(60)

        elif status == "RATE_LIMIT":
            print("⏳ [СПАМ-ЛИМИТ] Сервер просит снизить частоту запросов. Пауза 60 секунд...")
            time.sleep(60)

        elif status == "SUCCESS":
            print("✅ Итерация прошла успешно. Пауза 5 секунд...")
            time.sleep(5)
            count += 1

        else:  # ERROR
            print("⚠️ Ошибка вызова API. Повторная попытка через 10 секунд...")
            time.sleep(10)
