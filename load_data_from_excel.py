import pandas as pd


# Функция для загрузки данных из Excel
def load_data_from_excel(file_path):
    from app import db
    from models import Product, Location, Measurement
    # Установим establishment_id для всех продуктов
    establishment_id = 2
    
    # Чтение файла Excel
    data = pd.read_excel(file_path)
    
    for index, row in data.iterrows():
        # Извлекаем данные из строки
        product_name = row['Название']
        location_name = row['Расположение']
        measurement_name = row['Ед. изм.']
        
        
        # Находим или создаем локацию по имени и establishment_id
        location = Location.query.filter_by(name=location_name, establishment_id=establishment_id).first()
        if not location:
            print(f"Локация '{location_name}' не найдена в базе данных.")
            continue
        
        # Находим или создаем единицу измерения
        measurement = Measurement.query.filter_by(name=measurement_name).first()
        if not measurement:
            measurement = Measurement(name=measurement_name)
            db.session.add(measurement)
            db.session.commit()
        
        # Проверяем, существует ли продукт с таким именем в локации и заведении
        product = Product.query.filter_by(
            name=product_name,
            location_id=location.id,
            establishment_id=establishment_id
        ).first()
        
        # Если продукт не существует, создаем новый продукт
        if not product:
            product = Product(
                name=product_name,
                location_id=location.id,
                measurement_id=measurement.id,
                establishment_id=establishment_id
            )
            db.session.add(product)
        
        
    db.session.commit()
    print("Данные успешно загружены из Excel.")
