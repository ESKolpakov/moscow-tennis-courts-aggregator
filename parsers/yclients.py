from dataclasses import dataclass
from datetime import datetime, timedelta, date
import re
from typing import List, Optional

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from parsers.base import BaseParser, SlotData


# --- Вспомогательные данные ---

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


@dataclass
class CourtConfig:
    """
    Настройки для одного корта / услуги на YClients.
    """
    club_name: str
    court_name: str
    url: str
    duration_minutes: int
    service_label: str  # например, "Аренда 1 час", "1.5 часа"

    # пока просто храним, позже начнём использовать для честного разделения кортов
    staff_id: int       # уникальный ID корта (staff) в YClients
    service_id: int     # ID услуги ("Аренда 1 час" и т.п.)


class YClientsMyProTennisCourtParser(BaseParser):
    """
    Парсер слотов для MyProtennis.ru на YClients.
    """

    source_name = "yclients_myprotennis"

    def __init__(self, headless: bool = True, days_ahead: int = 2):
        """
        :param headless: True на проде, False — чтобы видеть браузер при отладке.
        :param days_ahead: сколько дней вперёд от сегодняшнего обходить
                           (0 = только сегодня, 2 = сегодня + 2 дня и т.д.).
        """
        self.headless = headless
        self.days_ahead = days_ahead

        common_url = (
            "https://b1044864.yclients.com/company/967881/"
            "personal/select-time?o=m-1"
        )

        self.courts: List[CourtConfig] = [
            CourtConfig(
                club_name="MyProtennis.ru",
                court_name="Корт №1",
                url=common_url,
                duration_minutes=60,
                service_label="Аренда 1 час",
                staff_id=2909330,
                service_id=14378490,
            ),
            CourtConfig(
                club_name="MyProtennis.ru",
                court_name="Корт №2",
                url=common_url,
                duration_minutes=60,
                service_label="Аренда 1 час",
                staff_id=2909345,
                service_id=14378490,
            ),
            CourtConfig(
                club_name="MyProtennis.ru",
                court_name="Корт №3",
                url=common_url,
                duration_minutes=60,
                service_label="Аренда 1 час",
                staff_id=2909347,
                service_id=14378490,
            ),
            CourtConfig(
                club_name="MyProtennis.ru",
                court_name="Корт №4",
                url=common_url,
                duration_minutes=60,
                service_label="Аренда 1 час",
                staff_id=2909348,
                service_id=14378490,
            ),
        ]

    # ---------- Публичный метод парсера ---------- #

    def fetch_slots(self) -> List[SlotData]:
        print("[YClients] Старт YClientsMyProTennisCourtParser")

        all_slots: List[SlotData] = []

        for cfg in self.courts:
            try:
                slots = self._collect_slots_for_court(cfg)
                all_slots.extend(slots)
                print(
                    f"[YClients] Для {cfg.court_name} подготовлено слотов: "
                    f"{len(slots)}"
                )
            except Exception as e:
                print(
                    f"[YClients] Ошибка при обработке {cfg.court_name}: {e}"
                )

        print(f"[YClients] Итого слотов по всем кортам: {len(all_slots)}")
        return all_slots

    # ---------- Вспомогательные методы ---------- #

    def _parse_nearest_date_from_text(self, text: str) -> Optional[date]:
        """
        Пытаемся вытащить дату из строки вида:
        'Ближайшая доступная дата: пятница, 28 ноября'
        (используется только если на сегодня слотов нет).
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

    def _extract_unique_times(self, html: str) -> List[str]:
        """
        Достаём из HTML все вхождения времён вида H:MM или HH:MM и
        возвращаем отсортированный список уникальных строк.
        """
        time_pattern = r"\b\d{1,2}:\d{2}\b"
        all_times = re.findall(time_pattern, html)
        unique_times = sorted(set(all_times), key=lambda t: (
            int(t.split(":")[0]),
            int(t.split(":")[1]),
        ))
        return unique_times

    def _click_month_arrow(self, page, direction: str) -> None:
        """
        Кликает по стрелке переключения месяца.

        direction: "next" (вперёд, вправо) или "prev" (назад, влево).

        Здесь мы:
        - ищем ВСЕ возможные кандидаты: y-core-icon-button и
          y-core-simple-button.y-core-icon-button;
        - логируем их в Python (tag, class, data-locator),
        - пытаемся кликнуть по нужному host напрямую (host.click()).
        """

        js = """
        (direction) => {
            const debug = [];

            const iconHosts  = Array.from(
                document.querySelectorAll('y-core-icon-button')
            );
            const simpleHosts = Array.from(
                document.querySelectorAll('y-core-simple-button.y-core-icon-button')
            );

            const hosts = [...iconHosts, ...simpleHosts];

            debug.push(
                `found y-core-icon-button: ${iconHosts.length}, `
                + `y-core-simple-button.y-core-icon-button: ${simpleHosts.length}, `
                + `total hosts: ${hosts.length}`
            );

            hosts.forEach((host, idx) => {
                const tag = host.tagName;
                const classes = host.getAttribute('class') || '';
                const dl = host.getAttribute('data-locator') || '';
                debug.push(
                    `host[${idx}]: tag=${tag}, class="${classes}", `
                    + `data-locator="${dl}"`
                );

                // Если есть shadowRoot — тоже немного посмотрим внутрь
                const sr = host.shadowRoot;
                if (sr) {
                    const innerButtons = Array.from(sr.querySelectorAll('button'));
                    debug.push(
                        `host[${idx}]: shadowRoot buttons=${innerButtons.length}`
                    );
                    innerButtons.forEach((b, bi) => {
                        debug.push(
                            `host[${idx}] button[${bi}] class="${b.className}"`
                        );
                    });
                } else {
                    debug.push(`host[${idx}]: shadowRoot = null`);
                }
            });

            let host = null;
            if (hosts.length === 0) {
                debug.push("no hosts at all for month arrows");
                return { ok: false, reason: "no-hosts", debug };
            }

            // по договорённости: [0] — левая стрелка, [1] — правая
            if (direction === "next") {
                host = hosts[1] || hosts[0];
                debug.push(
                    `direction=next, picked host index=${hosts[1] ? 1 : 0}`
                );
            } else {
                host = hosts[0];
                debug.push("direction=prev, picked host index=0");
            }

            if (!host) {
                debug.push("host is null after selection");
                return { ok: false, reason: "no-host-for-direction", debug };
            }

            try {
                host.click();
                debug.push("clicked host directly with host.click()");
                return { ok: true, reason: "clicked-host", debug };
            } catch (e) {
                debug.push("error on host.click(): " + e);
            }

            // fallback: если есть shadowRoot и button внутри — пробуем его
            const sr = host.shadowRoot;
            if (sr) {
                const btn = sr.querySelector("button");
                if (btn) {
                    try {
                        btn.click();
                        debug.push("clicked inner button inside shadowRoot");
                        return { ok: true, reason: "clicked-inner-button", debug };
                    } catch (e2) {
                        debug.push("error on inner button click: " + e2);
                    }
                } else {
                    debug.push("no <button> inside shadowRoot in fallback");
                }
            } else {
                debug.push("no shadowRoot in fallback");
            }

            return { ok: false, reason: "click-failed", debug };
        }
        """

        result = page.evaluate(js, direction)

        # Аккуратно выводим все debug-строки
        if isinstance(result, dict):
            for line in result.get("debug", []):
                print(f"[YClients][ARROW_DEBUG] {line}")

            if not result.get("ok"):
                print(
                    f"[YClients] Не удалось кликнуть стрелку месяца ({direction}). "
                    f"Причина: {result.get('reason')}"
                )
            else:
                print(
                    f"[YClients] Успешно кликнули стрелку месяца ({direction}). "
                    f"Режим: {result.get('reason')}"
                )
                page.wait_for_timeout(1_000)
        else:
            print(
                f"[YClients] Непонятный результат из JS для стрелки ({direction}): "
                f"{result}"
            )

    def _select_date_on_calendar(self, page, target_date: date, base_date: date) -> None:
        """
        Переключаем календарь на нужный месяц стрелками и выбираем день.

        base_date — дата, которую считаем текущей при открытии виджета.
        """
        month_diff = (target_date.year - base_date.year) * 12 + (
            target_date.month - base_date.month
        )
        print(
            f"[YClients] Переключение календаря: base={base_date}, "
            f"target={target_date}, month_diff={month_diff}"
        )

        if month_diff > 0:
            print(f"[YClients] Листаем календарь вперёд на {month_diff} мес.")
            for _ in range(month_diff):
                self._click_month_arrow(page, "next")
        elif month_diff < 0:
            print(f"[YClients] Листаем календарь назад на {-month_diff} мес.")
            for _ in range(-month_diff):
                self._click_month_arrow(page, "prev")

        day_str = str(target_date.day)

        try:
            print(f"[YClients] Пытаемся выбрать дату {target_date} (день {day_str})")

            js = """
            (day) => {
                const nodes = Array.from(
                    document.querySelectorAll('[data-locator="working_day_number"]')
                );
                console.log("YClients parser: found day nodes =", nodes.length);

                const target = nodes.find(
                    (n) => n.textContent && n.textContent.trim() === String(day)
                );
                if (!target) {
                    console.warn("YClients parser: day element not found for", day);
                    return false;
                }

                const btn = target.closest('button');
                if (btn) {
                    btn.click();
                    return true;
                }

                target.dispatchEvent(
                    new MouseEvent('click', { bubbles: true, cancelable: true })
                );
                return true;
            }
            """

            ok = page.evaluate(js, day_str)
            if not ok:
                print(
                    f"[YClients] Не нашли день {day_str} в календаре после переключения месяца."
                )
            else:
                page.wait_for_timeout(1_000)

        except Exception as e:
            print(
                f"[YClients] Не удалось кликнуть дату {target_date} "
                f"(день {day_str}) — ошибка: {e}"
            )

    def _collect_slots_for_court(self, cfg: CourtConfig) -> List[SlotData]:
        """
        Собирает слоты для одного корта/услуги по его URL.
        Обходит несколько дат подряд (сегодня + self.days_ahead).
        """

        print(
            f"[YClients] Старт парсера для {cfg.club_name} / "
            f"{cfg.court_name} / {cfg.service_label}"
        )

        all_slots: List[SlotData] = []

        base_date = datetime.now().date()
        target_dates = [base_date + timedelta(days=i) for i in range(self.days_ahead + 1)]
        target_dates_str = ", ".join(d.isoformat() for d in target_dates)
        print(f"[YClients] Даты для запроса: {target_dates_str}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()

            try:
                # ВАЖНО: на КАЖДУЮ дату заново открываем виджет.
                # Так мы всегда стартуем из одного и того же месяца (base_date)
                # и не накапливаем смещение.
                page = context.new_page()

                for target_date in target_dates:
                    print(
                        f"[YClients] === Обработка даты {target_date} "
                        f"для {cfg.court_name} ==="
                    )

                    print(f"[YClients] Открываем URL виджета: {cfg.url}")
                    page.goto(cfg.url, timeout=30_000)
                    page.wait_for_timeout(3_000)

                    self._select_date_on_calendar(page, target_date, base_date)

                    html = page.content()
                    print(
                        f"[YClients] Длина HTML для {cfg.court_name} / "
                        f"{target_date}: {len(html)} символов"
                    )

                    unique_times = self._extract_unique_times(html)
                    print(
                        f"[YClients] Временных вхождений (уникальных) на "
                        f"{target_date}: {unique_times}"
                    )

                    if not unique_times:
                        print(
                            f"[YClients] На дату {target_date} времён не найдено — "
                            f"пропускаем."
                        )
                        continue

                    for time_str in unique_times:
                        try:
                            hour, minute = map(int, time_str.split(":"))
                        except ValueError:
                            print(
                                f"[YClients] Не удалось распарсить время '{time_str}' "
                                f"на дату {target_date}"
                            )
                            continue

                        start_dt = datetime(
                            year=target_date.year,
                            month=target_date.month,
                            day=target_date.day,
                            hour=hour,
                            minute=minute,
                        )
                        end_dt = start_dt + timedelta(
                            minutes=cfg.duration_minutes
                        )

                        slot = SlotData(
                            club=cfg.club_name,
                            court=cfg.court_name,
                            start=start_dt,
                            end=end_dt,
                            duration_minutes=cfg.duration_minutes,
                            status="free",
                            source=self.source_name,
                        )
                        all_slots.append(slot)

            finally:
                browser.close()

        return all_slots
