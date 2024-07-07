from flask import Flask, render_template, request, redirect, url_for
from models import db, Product, Location, Measurement, add_default_measurements
import pandas as pd
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    add_default_measurements()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products', methods=['GET', 'POST'])
def products_page():
    locations = Location.query.all()
    measurements = Measurement.query.all()

    if request.method == 'POST':
        product_name = request.form.get('product')
        location_id = request.form.get('location')
        measurement_id = request.form.get('measurement')

        if product_name and location_id and measurement_id:
            product = Product(name=product_name, location_id=location_id, measurement_id=measurement_id)
            db.session.add(product)
            db.session.commit()
            return redirect(url_for('products_page'))

    products = Product.query.all()
    return render_template('products.html', products=products, locations=locations, measurements=measurements)

@app.route('/locations', methods=['GET', 'POST'])
def locations_page():
    if request.method == 'POST':
        location_name = request.form.get('location')
        if location_name:
            location = Location(name=location_name)
            db.session.add(location)
            db.session.commit()
            return redirect(url_for('locations_page'))
    locations = Location.query.all()
    return render_template('locations.html', locations=locations)

@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    locations = Location.query.all()
    measurements = Measurement.query.all()

    if request.method == 'POST':
        product.name = request.form.get('product')
        product.location_id = request.form.get('location')
        product.measurement_id = request.form.get('measurement')
        db.session.commit()
        return redirect(url_for('products_page'))

    return render_template('edit_product.html', product=product, locations=locations, measurements=measurements)

@app.route('/locations/<int:location_id>/edit', methods=['GET', 'POST'])
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)

    if request.method == 'POST':
        location.name = request.form.get('location')
        db.session.commit()
        return redirect(url_for('locations_page'))

    return render_template('edit_location.html', location=location)


@app.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('products_page'))

@app.route('/locations/<int:location_id>/delete', methods=['POST'])
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)

    # Проверяем, используется ли расположение в продуктах
    products_using_location = Product.query.filter_by(location_id=location_id).all()

    if products_using_location:
        error_message = "Cannot delete this location because it is used in one or more products."
        locations = Location.query.all()
        return render_template('locations.html', locations=locations, error_message=error_message)

    db.session.delete(location)
    db.session.commit()
    return redirect(url_for('locations_page'))

@app.route('/inventory', methods=['GET', 'POST'])
def inventory_page():
    locations = Location.query.all()

    if request.method == 'POST':
        data = []
        for location in locations:
            for product in location.products:
                quantity = request.form.get(f'quantity_{product.id}')
                if quantity:
                    data.append({
                        'Product Name': product.name,
                        'Location': product.location.name,
                        'Measurement': product.measurement.name,
                        'Quantity': float(quantity)
                    })

        df = pd.DataFrame(data)
        file_path = os.path.join('static', 'inventory.xlsx')
        df.to_excel(file_path, index=False)

        return redirect(url_for('inventory_page'))

    return render_template('inventory.html', locations=locations)


if __name__ == '__main__':
    app.run(debug=True)





