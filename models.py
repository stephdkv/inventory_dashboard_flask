from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    measurement_id = db.Column(db.Integer, db.ForeignKey('measurement.id'), nullable=False)

    location = db.relationship('Location', backref=db.backref('products', lazy=True))
    measurement = db.relationship('Measurement', backref=db.backref('products', lazy=True))

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()

# Добавляем захардкоженные единицы измерения при первом запуске
def add_default_measurements():
    if Measurement.query.count() == 0:
        measurements = ['шт', 'л', 'кг']
        for measurement in measurements:
            db.session.add(Measurement(name=measurement))
        db.session.commit()
