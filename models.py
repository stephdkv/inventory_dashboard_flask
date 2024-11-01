from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Establishment(db.Model):
    __tablename__ = 'establishments'  # таблица для заведений
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    # Связь с пользователями
    users = db.relationship('User', backref='establishment', lazy=True)

    locations = db.relationship('Location', backref='establishment', lazy=True)

    # Связь с продуктами
    products = db.relationship('Product', backref='establishment', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    
    # Внешний ключ для связи с заведением
    establishment_id = db.Column(db.Integer, db.ForeignKey('establishments.id'), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    measurement_id = db.Column(db.Integer, db.ForeignKey('measurement.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)

    # Внешний ключ для связи с заведением
    establishment_id = db.Column(db.Integer, db.ForeignKey('establishments.id'), nullable=False)

    location = db.relationship('Location', backref=db.backref('products', lazy=True))
    measurement = db.relationship('Measurement', backref=db.backref('products', lazy=True))
    supplier = db.relationship('Supplier', back_populates='products')



class Measurement(db.Model):
    __tablename__ = 'measurement'  # таблица для единиц измерения
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

class Location(db.Model):
    __tablename__ = 'location'  # таблица для местоположений
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    establishment_id = db.Column(db.Integer, db.ForeignKey('establishments.id'), nullable=False)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Supplier(db.Model):
    __tablename__ = 'suppliers'  # таблица для поставщиков
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    
    # Связь с продуктами
    products = db.relationship('Product', back_populates='supplier')

    def delete(self):
        db.session.delete(self)
        db.session.commit()

# Обратите внимание на названия таблиц в связывающей таблице
supplier_product = db.Table('supplier_product',
    db.Column('supplier_id', db.Integer, db.ForeignKey('suppliers.id'), primary_key=True),  # исправлено на 'suppliers.id'
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)  # исправлено на 'products.id'
)

class Dish(db.Model):
    __tablename__ = 'dishes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)  # URL изображения
    preparation_steps = db.Column(db.Text, nullable=True)  # Шаги приготовления
    video_url = db.Column(db.String(200), nullable=True)  # Опциональное видео
    
    # Дата создания блюда
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с продуктами
    ingredients = db.relationship('DishProduct', back_populates='dish')
    
class DishProduct(db.Model):
    __tablename__ = 'dish_products'
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # Количество продукта в рецепте
    
    # Связи
    dish = db.relationship('Dish', back_populates='ingredients')
    product = db.relationship('Product', backref=db.backref('dish_products', lazy=True))

# Добавляем захардкоженные единицы измерения при первом запуске
def add_default_measurements():
    if Measurement.query.count() == 0:
        measurements = ['шт', 'л', 'кг']
        for measurement in measurements:
            db.session.add(Measurement(name=measurement))
        db.session.commit()



