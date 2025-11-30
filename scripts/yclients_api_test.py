import json
import sys
from typing import Any, Optional

import requests


URL = "https://platform.yclients.com/api/v1/b2c/booking/availability/search-timeslots"

LOCATION_ID = 967881  # MyProtennis.ru, тот же, что в payload из DevTools


def fetch_timeslots(date_str: str) -> Optional[Any]:
    """
    Простой тестовый запрос к YClients API.

    Сейчас YClients для прямых запросов с сервера отдаёт 404 и HTML-страницу,
    поэтому функция возвращает None, если статус не 200.
    """
    payload = {
        "context": {"location_id": LOCATION_ID},
        "filter": {
            "date": date_str,
            "records": [
                {
                    "staff_id": -1,
                    "attendance_service_items": [],
                }
            ],
        },
    }

    print(f"Отправляем запрос на {URL}")
    print("Payload:", json.dumps(payload, ensure_ascii=False))

    resp = requests.post(URL, json=payload, timeout=15)
    print("HTTP статус:", resp.status_code)

    if resp.status_code != 200:
        # Просто выводим первые ~400 символов ответа и возвращаем None
        print("Неверный статус, сырой ответ (обрезан):")
        print(resp.text[:400])
        return None

    try:
        return resp.json()
    except Exception:
        print("Не удалось распарсить JSON, сырой ответ:")
        print(resp.text[:400])
        return None


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else "2025-12-01"
    print(f"Запрашиваем слоты на дату: {date_str}")

    data = fetch_timeslots(date_str)
    if not data:
        print("JSON не получен (скорее всего защита API на стороне YClients).")
        return

    items = data.get("data", [])
    print(f"Найдено таймслотов: {len(items)}")

    for item in items:
        attrs = item.get("attributes", {})
        dt = attrs.get("datetime")
        time_str = attrs.get("time")
        is_bookable = attrs.get("is_bookable")
        print(f" - {dt} | {time_str} | bookable={is_bookable}")


if __name__ == "__main__":
    main()
