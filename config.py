import os


class Config:
    """Базовая конфигурация приложения."""

    # Секретный ключ используется Flask'ом для сессий, флеш-сообщений и т.п.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # SQLite база на этапе разработки
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
