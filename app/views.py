from flask import Blueprint, render_template, jsonify

from app.models import Slot

# Создаём Blueprint, чтобы структуру можно было легко расширять
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """
    Главная страница с поиском свободных слотов.
    Слоты берём из базы данных для первоначального отображения.
    """

    slots = Slot.query.order_by(Slot.start_datetime).all()
    return render_template("index.html", slots=slots)


@main_bp.route("/api/slots")
def api_slots():
    """
    API-эндпоинт, который возвращает список слотов в формате JSON.
    В дальнейшем сюда добавим фильтры по дате/времени/клубу и т.д.
    """

    slots = Slot.query.order_by(Slot.start_datetime).all()

    slots_data = []
    for slot in slots:
        slots_data.append(
            {
                "id": slot.id,
                "club": slot.club,
                "court": slot.court,
                "date": slot.start.strftime("%d.%m.%Y"),
                "time_range": f"{slot.start.strftime('%H:%M')}–{slot.end.strftime('%H:%M')}",
                "duration_minutes": slot.duration_minutes,
                "status": slot.status,
                "source": slot.source or "",
            }
        )

    return jsonify({"slots": slots_data})
