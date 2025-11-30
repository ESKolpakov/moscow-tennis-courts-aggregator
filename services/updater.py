"""
Сервис обновления слотов из всех источников.

Здесь мы:
- вызываем парсеры (mock, YClients, потом добавим другие сайты);
- очищаем таблицу Slot;
- записываем новые слоты в БД.
"""

from typing import List

from app import db
from app.models import Slot
from parsers.base import SlotData
from parsers.mock_parser import MockTennisParser
from parsers.yclients import YClientsMyProTennisCourtParser


def _save_slots(slots_data: List[SlotData]) -> None:
    """
    Сохраняет список SlotData в БД.
    """
    for s in slots_data:
        slot = Slot(
            club=s.club,
            court=s.court,
            start_datetime=s.start,
            end_datetime=s.end,
            duration_minutes=s.duration_minutes,
            status=s.status,
            source=s.source,
        )
        db.session.add(slot)


def update_slots_from_all_sources() -> int:
    """
    Основная функция, которую дергает API /api/update_slots.

    Возвращает количество добавленных слотов.
    """

    # Здесь будут все наши парсеры.
    parsers = [
        MockTennisParser(),
        YClientsMyProTennisCourtParser(),
    ]

    # Пока не заморачиваемся по источникам — просто очищаем таблицу Slot.
    Slot.query.delete()
    db.session.commit()

    total_slots = 0

    for parser in parsers:
        print(f"[Updater] Запускаем парсер: {parser.__class__.__name__}")
        try:
            slots_data = parser.fetch_slots()
        except Exception as exc:  # noqa: BLE001
            # Чтобы падение одного парсера не ломало остальные
            print(f"[Updater] Ошибка в парсере {parser.__class__.__name__}: {exc}")
            continue

        _save_slots(slots_data)
        total_slots += len(slots_data)

    db.session.commit()
    print(f"[Updater] Обновление завершено, всего слотов: {total_slots}")
    return total_slots
