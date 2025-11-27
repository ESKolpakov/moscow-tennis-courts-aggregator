from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class SlotData:
    """
    Универсальное представление слота, которое возвращают парсеры.

    Важно: это НЕ SQLAlchemy-модель, а обычный dataclass.
    Так мы не привязываем парсеры к конкретной БД.
    """
    club: str
    court: str
    start: datetime
    end: datetime
    duration_minutes: int
    status: str  # 'free' или 'busy'
    source: str  # идентификатор источника, например 'mock', 'yclients', 'findsport'


class BaseParser:
    """
    Базовый класс для всех парсеров.
    Конкретные реализации должны переопределить метод fetch_slots().
    """

    source_name: str = "base"

    def fetch_slots(self) -> List[SlotData]:
        """
        Должен вернуть список слотов в унифицированном формате SlotData.
        """
        raise NotImplementedError("fetch_slots() must be implemented in subclasses")
