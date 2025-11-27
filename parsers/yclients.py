from datetime import datetime, timedelta, date
import re
from typing import List, Optional

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from parsers.base import BaseParser, SlotData


MONTHS_RU = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


class YClientsMyProTennisCourt2Parser(BaseParser):
    """
    Парсер слотов для корта MyProtennis.ru на YClients.

    Логика:
    1. Открываем страницу выбора времени.
    2. Если видим текст "В этот день нет свободного времени" —
       жмём "Перейти к ближайшей дате" и пытаемся вытащить дату
       из текста "Ближайшая доступная дата: ...".
    3. Берём HTML всей страницы и вытаскиваем все подстроки формата HH:MM.
    4. Считаем каждое время отдельным слотом с фиксированной длительностью.
    """

    source_name = "yclients_myprotennis_court2"

    def __init__(self, headless: bool = False):
        # Пока оставляем headless=False, чтобы ты видел окно браузера.
        self.headless = headless
        self.url = (
            "https://b1044864.yclients.com/company/967881/"
            "personal/select-time?o=m-1"
        )
        self.club_name = "MyProtennis.ru"
        self.court_name = "Корт №2"
        self.slot_duration_minutes = 60

    def _parse_nearest_date_from_text(self, text: str) -> Optional[date]:
        """
        Пытаемся вытащить дату из строки вида:
        'Ближайшая доступная дата: пятница, 28 ноября'
        """
        text = " ".join(text.split())
        match = re.search(
            r"Ближайшая доступная дата:\s*[^,]*,\s*(\d{1,2})\s+([А-Яа-я]+)",
            text,
        )
        if not match:
            return None

        day = int(match.group(1))
        month_name = match.group(2).lower()
        month = MONTHS_RU.get(month_name)
        if not month:
            return None

        today = datetime.now().date()
        year = today.year
        if month < today.month:
            year += 1

        try:
            return date(year, month, day)
        except ValueError:
            return None

    def fetch_slots(self) -> List[SlotData]:
        print("[YClients] Старт парсера для MyProtennis Court 2")
        target_date: Optional[date] = None
        html: str = ""

        try:
            with sync_playwright() as p:
                print("[YClients] Запуск браузера…")
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context()
                page = context.new_page()

                print(f"[YClients] Открываем URL: {self.url}")
                page.goto(self.url, wait_until="networkidle", timeout=30_000)
                page.wait_for_timeout(2_000)

                # Проверяем сообщение про отсутствие слотов
                no_slots_locator = page.locator(
                    "text=В этот день нет свободного времени"
                )
                if no_slots_locator.count() > 0:
                    print("[YClients] На текущий день слотов нет.")

                    # Пытаемся прочитать текст с ближайшей датой
                    nearest_text_locator = page.locator(
                        "text=Ближайшая доступная дата"
                    )
                    if nearest_text_locator.count() > 0:
                        nearest_full_text = nearest_text_locator.nth(
                            0
                        ).evaluate("el => el.parentElement.textContent")
                        neat_text = " ".join(nearest_full_text.split())
                        print(
                            "[YClients] Текст про ближайшую дату:",
                            repr(neat_text),
                        )
                        parsed_date = self._parse_nearest_date_from_text(
                            nearest_full_text
                        )
                        if parsed_date:
                            target_date = parsed_date
                            print(
                                f"[YClients] Распарсили ближайшую дату: {target_date}"
                            )

                    # Жмём "Перейти к ближайшей дате"
                    goto_btn = page.locator("text=Перейти к ближайшей дате")
                    if goto_btn.count() > 0:
                        print("[YClients] Нажимаем кнопку 'Перейти к ближайшей дате'")
                        goto_btn.first.click()
                        page.wait_for_timeout(2_000)
                    else:
                        print(
                            "[YClients] Кнопка 'Перейти к ближайшей дате' не найдена"
                        )

                if target_date is None:
                    target_date = datetime.now().date()
                    print(
                        "[YClients] Используем сегодняшнюю дату "
                        f"как дату слотов: {target_date}"
                    )

                # Берём весь HTML и вытаскиваем времена по регулярке
                html = page.content()
                print(f"[YClients] Длина HTML: {len(html)} символов")

                # Ищем все вхождения HH:MM, окружённые границами слова/нецифрами
                time_strings = re.findall(r"\b(\d{1,2}:\d{2})\b", html)
                # Убираем дубликаты и сортируем
                unique_times = sorted(set(time_strings), key=lambda t: (
                    int(t.split(":")[0]),
                    int(t.split(":")[1]),
                ))

                print(
                    f"[YClients] Найдено временных вхождений: {len(time_strings)}, "
                    f"уникальных: {len(unique_times)}"
                )
                print("[YClients] Список уникальных времён:", unique_times)

                # Небольшая пауза, чтобы можно было посмотреть на окно браузера
                page.wait_for_timeout(2_000)

                context.close()
                browser.close()
                print("[YClients] Браузер закрыт")

        except PlaywrightTimeoutError:
            print("[YClients] Timeout при загрузке страницы")
            unique_times = []
            target_date = target_date or datetime.now().date()
        except Exception as exc:  # noqa: BLE001
            print(f"[YClients] Ошибка при парсинге: {exc}")
            unique_times = []
            target_date = target_date or datetime.now().date()

        slots: List[SlotData] = []

        if not unique_times:
            print("[YClients] Не найдено ни одного слота (по регулярке), возвращаем пустой список")
            return slots

        print(f"[YClients] Используем дату {target_date} для всех найденных времён")

        for t_str in unique_times:
            hours, minutes = map(int, t_str.split(":"))
            start_dt = datetime(
                year=target_date.year,
                month=target_date.month,
                day=target_date.day,
                hour=hours,
                minute=minutes,
            )
            end_dt = start_dt + timedelta(minutes=self.slot_duration_minutes)

            slot = SlotData(
                club=self.club_name,
                court=self.court_name,
                start=start_dt,
                end=end_dt,
                duration_minutes=self.slot_duration_minutes,
                status="free",
                source=self.source_name,
            )
            slots.append(slot)

        print(f"[YClients] Всего слотов подготовлено: {len(slots)}")
        return slots
