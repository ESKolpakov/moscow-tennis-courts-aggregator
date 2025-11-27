from datetime import datetime, timedelta

from app import create_app, db
from app.models import Slot


def seed_slots():
    """Создаём несколько тестовых слотов в базе данных."""
    app = create_app()

    with app.app_context():
        # На всякий случай создаём таблицы (если их ещё нет)
        db.create_all()

        # Очищаем таблицу слотов
        Slot.query.delete()

        now = datetime.now().replace(minute=0, second=0, microsecond=0)

        slots = [
            Slot(
                club="Tsaritsyno Tennis",
                court="Корт 1",
                start_datetime=now.replace(hour=18),
                end_datetime=now.replace(hour=19),
                duration_minutes=60,
                status="free",
                source="seed",
            ),
            Slot(
                club="MosTennis Club",
                court="Корт 3",
                start_datetime=now.replace(hour=19, minute=30),
                end_datetime=now.replace(hour=21),
                duration_minutes=90,
                status="free",
                source="seed",
            ),
            Slot(
                club="YClients Arena",
                court="Корт 2",
                start_datetime=now + timedelta(days=1, hours=2),
                end_datetime=now + timedelta(days=1, hours=3),
                duration_minutes=60,
                status="busy",
                source="seed",
            ),
        ]

        db.session.add_all(slots)
        db.session.commit()

        print(f"Создано слотов: {len(slots)}")


if __name__ == "__main__":
    seed_slots()
