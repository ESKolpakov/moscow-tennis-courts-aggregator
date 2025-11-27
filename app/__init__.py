from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Инициализируем объект базы данных, но не привязываем к приложению сразу
db = SQLAlchemy()


def create_app(config_class=Config):
    """
    Фабрика приложения.
    Такой подход позволяет легче тестировать и масштабировать проект.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Подключаем базу данных к приложению
    db.init_app(app)

    # Регистрируем маршруты (роуты) из отдельного модуля
    from app.views import main_bp
    app.register_blueprint(main_bp)

    # Создаём таблицы в базе данных (пока у нас модели простые/заготовки)
    with app.app_context():
        db.create_all()

    return app
