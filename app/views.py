from flask import Blueprint, render_template

from app.models import Slot

# Создаём Blueprint, чтобы структуру можно было легко расширять
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """
    Главная страница с поиском свободных слотов.
    Теперь слоты берём из базы данных.
    """

    # Получаем слоты из базы, отсортированные по времени начала
    slots = Slot.query.order_by(Slot.start_datetime).all()

    return render_template("index.html", slots=slots)
