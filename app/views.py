from datetime import datetime, time

from flask import Blueprint, render_template, jsonify, request

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
    Поддерживает фильтры по дате, времени, длительности, клубу и статусу.
    """

    query = Slot.query

    # ----- Читаем параметры запроса -----
    date_str = request.args.get("date")          # из <input type="date"> приходит YYYY-MM-DD
    time_from_str = request.args.get("time_from")
    time_to_str = request.args.get("time_to")
    min_duration = request.args.get("min_duration", type=int)
    club = request.args.get("club")
    free_only = request.args.get("free_only")    # "true" или None

    # ----- Фильтр по дате и времени -----
    if date_str:
        try:
            # Преобразуем строку в объект date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            # По умолчанию берём весь день
            dt_start = datetime.combine(date_obj, time(0, 0))
            dt_end = datetime.combine(date_obj, time(23, 59, 59))

            # Если указано время "с"
            if time_from_str:
                hours, minutes = map(int, time_from_str.split(":"))
                dt_start = datetime.combine(date_obj, time(hours, minutes))

            # Если указано время "до"
            if time_to_str:
                hours, minutes = map(int, time_to_str.split(":"))
                dt_end = datetime.combine(date_obj, time(hours, minutes))

            query = query.filter(
                Slot.start_datetime >= dt_start,
                Slot.start_datetime <= dt_end,
            )
        except ValueError:
            # Если пришёл кривой формат даты/времени — просто игнорируем фильтр
            pass

    # ----- Минимальная длительность -----
    if min_duration:
        query = query.filter(Slot.duration_minutes >= min_duration)

    # ----- Фильтр по клубу -----
    if club:
        query = query.filter(Slot.club == club)

    # ----- Показывать только свободные -----
    if free_only == "true":
        query = query.filter(Slot.status == "free")

    # ----- Выполняем запрос -----
    slots = query.order_by(Slot.start_datetime).all()

    # Готовим данные для фронтенда
    slots_data = [
        {
            "id": slot.id,
            "club": slot.club,
            "court": slot.court,
            "date": slot.start.strftime("%d.%m.%Y"),
            "time_range": (
                f"{slot.start.strftime('%H:%M')}–"
                f"{slot.end.strftime('%H:%M')}"
            ),
            "duration_minutes": slot.duration_minutes,
            "status": slot.status,
            "source": slot.source or "",
        }
        for slot in slots
    ]

    return jsonify({"slots": slots_data})
