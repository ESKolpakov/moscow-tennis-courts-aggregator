from typing import List

from app import db
from app.models import Slot
from parsers.base import SlotData
from parsers.mock_parser import MockTennisParser
from parsers.yclients import YClientsMyProTennisCourt2Parser


def collect_slots_from_all_sources() -> List[SlotData]:
    """
    Вызывает все зарегистрированные парсеры и собирает слоты.
    Сейчас:
    - MockTennisParser (тестовые данные)
    - YClientsMyProTennisCourt2Parser (реальные данные с YClients)
    """
    slots: List[SlotData] = []

    parsers = [
        MockTennisParser(),
        YClientsMyProTennisCourt2Parser(),
        # сюда будем добавлять: FindSportParser(), TsaritsynoParser(), ...
    ]

    for parser in parsers:
        parser_slots = parser.fetch_slots()
        slots.extend(parser_slots)

    return slots


def replace_all_slots(slots_data: List[SlotData]) -> int:
    """
    Полностью заменяет содержимое таблицы Slot на новые данные.

    Для MVP это нормально. Позже можно сделать более умное обновление
    по ключу (клуб + корт + время начала).
    """
    # Удаляем все старые записи
    Slot.query.delete()

    # Создаём новые записи
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

    db.session.commit()

    return len(slots_data)


def update_slots_from_all_sources() -> int:
    """
    Главная функция обновления слотов.
    Её вызываем из Flask-обработчика и/или по расписанию (APScheduler).
    """
    slots = collect_slots_from_all_sources()
    count = replace_all_slots(slots)
    return count
