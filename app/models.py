from datetime import datetime

from app import db


class Slot(db.Model):
    """
    Универсальный слот времени на корте.
    В дальнейшем сюда можно добавить цену, покрытие и т.д.
    """
    id = db.Column(db.Integer, primary_key=True)

    club = db.Column(db.String(100), nullable=False)        # Название клуба
    court = db.Column(db.String(50), nullable=False)        # Название/номер корта

    start_datetime = db.Column(db.DateTime, nullable=False)  # Начало слота
    end_datetime = db.Column(db.DateTime, nullable=False)    # Конец слота

    duration_minutes = db.Column(db.Integer, nullable=False)  # Длительность в минутах

    status = db.Column(db.String(20), nullable=False, default="free")  # free/busy
    source = db.Column(db.String(50), nullable=True)                   # yclients, findsport, etc.

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    @property
    def start(self):
        """Удобное свойство для шаблонов: начало слота."""
        return self.start_datetime

    @property
    def end(self):
        """Удобное свойство для шаблонов: конец слота."""
        return self.end_datetime

    def __repr__(self):
        return (
            f"<Slot {self.club} {self.court} "
            f"{self.start_datetime}–{self.end_datetime} ({self.status})>"
        )
