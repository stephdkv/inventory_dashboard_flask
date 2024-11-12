# load_excel_data.py

from app import db, create_app  # Импортируем приложение и базу данных
from models import Product, Location, Measurement  # Импортируем нужные модели
import load_data_from_excel  # Импортируем функцию загрузки данных (если поместили её в utils.py)

app = create_app()  # Создаем приложение Flask

with app.app_context():
    # Путь к вашему файлу Excel
    file_path = '../inventory 3.xlsx'
    load_data_from_excel(file_path)
