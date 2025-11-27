from datetime import datetime, timedelta
from typing import List

from parsers.base import BaseParser, SlotData


class MockTennisParser(BaseParser):
    """
    Тестовый парсер, который возвращает несколько заранее
    подготовленных слотов. Позже мы заменим/дополним его
    реальными парсерами (YClients, FindSport, Tsaritsyno).
    """

    source_name = "mock"

    def fetch_slots(self) -> List[SlotData]:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)

        slots: List[SlotData] = [
            SlotData(
                club="Tsaritsyno Tennis",
                court="Корт 1",
                start=now.replace(hour=18),
                end=now.replace(hour=19),
                duration_minutes=60,
                status="free",
                source=self.source_name,
            ),
            SlotData(
                club="MosTennis Club",
                court="Корт 3",
                start=now.replace(hour=19, minute=30),
                end=now.replace(hour=21),
                duration_minutes=90,
                status="busy",
                source=self.source_name,
            ),
            SlotData(
                club="YClients Arena",
                court="Корт 2",
                start=now + timedelta(days=1, hours=2),
                end=now + timedelta(days=1, hours=3),
                duration_minutes=60,
                status="free",
                source=self.source_name,
            ),
        ]

        return slots
