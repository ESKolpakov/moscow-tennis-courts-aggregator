from app import create_app

# Создаём экземпляр приложения
app = create_app()

if __name__ == "__main__":
    # debug=True удобно на этапе разработки:
    # автоматический перезапуск при изменениях + отладочная инфа
    app.run(debug=True)
