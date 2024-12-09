from bs4 import BeautifulSoup
from datetime import datetime
from decorators import role_required, user_details
from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_file, make_response, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms import LoginForm, RegistrationForm
from io import BytesIO
from load_data_from_excel import load_data_from_excel
from models import db, Product, Location, Measurement, add_default_measurements, Supplier, User, Dish, UserProductLocation, DishProduct
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
import qrcode
import tempfile
from urllib.parse import quote
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))

with app.app_context():
    db.create_all()
    add_default_measurements()
    #file_path = 'inventory 3.xlsx'
    #load_data_from_excel(file_path)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Обработчик ошибки 404
@app.errorhandler(404)
@user_details
def page_not_found(e):
    # Можно отрендерить 404.html или вернуть текст
    return render_template('404.html', establishment_name=g.establishment_name, role=g.role, username=g.username), 404

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/user_list')
@login_required
@user_details
@role_required('admin')  # Только администраторы могут видеть этот список
def user_list():
    if request.method == 'POST':
        supplier_name = request.form.get('supplier')
        if supplier_name:
            supplier = Supplier(name=supplier_name)
            db.session.add(supplier)
            db.session.commit()
            return redirect(url_for('suppliers_page'))
    users = User.query.all()
    establishments = {1: 'Лукашевича', 2: 'Ленина'}  
    return render_template('user_list.html', users=users, establishments=establishments, establishment_name=g.establishment_name, role=g.role, username=g.username )

@app.route('/set_role/<int:user_id>', methods=['POST'])
@login_required
def set_role(user_id):
    # Проверяем, что текущий пользователь - администратор
    if current_user.role != 'admin':
        abort(403)

    # Находим пользователя, которому нужно изменить роль
    user = User.query.get_or_404(user_id)
    
    # Получаем новую роль из формы
    new_role = request.form.get('role')  # 'admin', 'user', etc.
    
    if new_role:
        user.role = new_role
        db.session.commit()
        flash(f'Роль пользователя {user.username} изменена на {new_role}', 'success')
    
    return redirect(url_for('user_list'))  # Перенаправляем на список пользователей или другую страницу

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    # Проверим, проходит ли форма валидацию
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        role = form.role.data  # Получаем выбранную роль
        establishment_id = form.establishment.data
        
        # Хешируем пароль
        password_hash = generate_password_hash(password)
        
        # Создаем нового пользователя
        new_user = User(username=username, password_hash=password_hash, role=role, establishment_id=establishment_id)
        
        try:
            # Пробуем добавить пользователя в базу данных
            db.session.add(new_user)
            db.session.commit()
            flash('Пользователь успешно зарегистрирован!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            # Если произошла ошибка — откатываем транзакцию и выводим сообщение об ошибке
            db.session.rollback()
            flash(f'Ошибка при создании пользователя: {str(e)}', 'danger')
    else:
        # Если валидация формы не прошла, выводим сообщение
        flash('Пожалуйста, проверьте данные формы.', 'danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('products_page'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Вы успешно вошли в систему!')
            return redirect(url_for('products_page'))
        else:
            flash('Неверное имя пользователя или пароль')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.')
    return redirect(url_for('login'))

@app.route('/home_page')
@login_required
def home_page():
    return f'Привет, {current_user.username}! Это домашняя страница.'

@app.route('/products', methods=['GET', 'POST'])
@login_required
@user_details
def products_page():
    locations = Location.query.filter_by(establishment_id=g.establishment_id).all()
    measurements = Measurement.query.all()
    if request.method == 'POST':
        product_name = request.form.get('product')
        location_id = request.form.get('location')
        measurement_id = request.form.get('measurement')
        

        if product_name and location_id and measurement_id:
            product = Product(name=product_name, location_id=location_id, measurement_id=measurement_id, establishment_id=g.establishment_id)
            db.session.add(product)
            db.session.commit()
            return redirect(url_for('products_page'))

    products = Product.query.all()
    return render_template('products.html', products=products, locations=locations, measurements=measurements, username=g.username, role=g.role, establishment_name=g.establishment_name)

@app.route('/locations', methods=['GET', 'POST'])
@login_required
@user_details
def locations_page():
    if request.method == 'POST':
        location_name = request.form.get('location')
        if location_name:
            location = Location(name=location_name, establishment_id=g.establishment_id)
            db.session.add(location)
            db.session.commit()
            return redirect(url_for('locations_page'))
    locations = Location.query.filter_by(establishment_id=g.establishment_id).all()
    return render_template('locations.html', locations=locations, username=g.username, role=g.role, establishment_name=g.establishment_name)

@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
@user_details
def suppliers_page():
    if request.method == 'POST':
        supplier_name = request.form.get('supplier')
        if supplier_name:
            supplier = Supplier(name=supplier_name)
            db.session.add(supplier)
            db.session.commit()
            return redirect(url_for('suppliers_page'))

    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers, establishment_name=g.establishment_name,  username=g.username, role=g.role)

@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@user_details
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

    return render_template('edit_product.html', product=product, locations=locations, measurements=measurements, establishment_name=g.establishment_name,  username=g.username, role=g.role)

@app.route('/locations/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
@user_details
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    if request.method == 'POST':
        db.session.commit()
        return redirect(url_for('locations_page'))

    return render_template('edit_location.html', location=location,  establishment_name=g.establishment_name,  username=g.username, role=g.role)

@app.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@user_details
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    products = Product.query.all()
    if request.method == 'POST':
        product_ids = request.form.getlist('products')
        supplier.products = Product.query.filter(Product.id.in_(product_ids)).all()
        db.session.commit()
        return redirect(url_for('suppliers_page'))

    return render_template('edit_supplier.html', supplier=supplier, products=products, establishment_name=g.establishment_name, username=g.username, role=g.role )


@app.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('products_page'))

@app.route('/locations/<int:location_id>/delete', methods=['POST'])
@login_required
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

@app.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)

    products_using_supplier = Product.query.filter_by(supplier_id=supplier_id).all()
    
    if products_using_supplier:
        error_message = "Cannot delete this suppliar because it is used in one or more products."
        suppliers = Supplier.query.all()
        return render_template('suppliers.html', suppliers=suppliers, error_message=error_message)
    
    db.session.delete(supplier)
    db.session.commit()
    return redirect(url_for('suppliers_page'))

@app.route('/supplier/<int:supplier_id>/product/<int:product_id>/remove', methods=['POST'])
@login_required
def remove_product_from_supplier(supplier_id, product_id):
    supplier = Supplier.query.get(supplier_id)
    product = Product.query.get(product_id)

    if supplier and product:
        # Удаление связи между поставщиком и продуктом
        supplier.products.remove(product)
        db.session.commit()
        flash('Продукт успешно удален из списка поставщика.', 'success')
    else:
        flash('Не удалось найти поставщика или продукт.', 'error')

    # Возвращаемся на страницу поставщика
    return redirect(url_for('suppliers_page', supplier_id=supplier_id))

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
@user_details
def inventory_page():
    user_id = current_user.id
    assigned_locations = UserProductLocation.query.filter_by(user_id=user_id).all()
    
    # Фильтруем уникальные локации и продукты
    locations = {assignment.location for assignment in assigned_locations}
    current_date = datetime.now().strftime('%d.%m.%y')

    if request.method == 'POST':
        data = []
        for location in locations:
            for product in location.products:
                quantity = request.form.get(f'quantity_{product.id}')
                if quantity:
                    data.append({
                        'Название': product.name,
                        'Расположение': product.location.name,
                        'Ед. изм.': product.measurement.name,
                        'Колличество': float(quantity)
                    })

        df = pd.DataFrame(data)
        file_name = f'Инвентаризация_{g.establishment_name}_{current_date}_{user_id}.xlsx'
        file_path = os.path.join('static', file_name)
        df.to_excel(file_path, index=False)

        return redirect(url_for('download_file', file_name=file_name))

    return render_template('inventory.html', locations=locations, current_date=current_date, establishment_name=g.establishment_name,  username=g.username, role=g.role)

@app.route('/download/<file_name>')
@login_required
def download_file(file_name):
    # Путь к файлу для скачивания
    file_path = os.path.join('static', file_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('Файл не найден', 'error')
        return redirect(url_for('inventory_page'))

@app.route('/download_order', methods=['POST'])
@login_required
@user_details
def download_order():
    supplier_id = request.form.get('supplier_id')
    supplier = Supplier.query.get(supplier_id)
    
    # Получаем текущую дату в формате ДД.ММ
    current_date = datetime.now().strftime('%d.%m')

    data = []
    for product in supplier.products:
        quantity = request.form.get(f'quantity_{product.id}')
        if quantity:
            data.append({
                'Product Name': product.name,
                'Measurement': product.measurement.name,
                'Quantity': float(quantity)
            })

    if data:
        # Генерируем имя файла с датой
        file_name = f'Заявка_{supplier.name}_{g.establishment_name}_{current_date}.xlsx'
        file_path = os.path.join('static', file_name)

        # Записываем данные в Excel
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)

        # Отправляем файл для загрузки
        return send_file(file_path, as_attachment=True)

    # Если данные не заполнены, перенаправляем на страницу обратно
    return redirect(url_for('supplier_page'))

@app.route('/suppliers_orders', methods=['GET'])
@login_required
@user_details
def supplier_page():
    suppliers = Supplier.query.all()
    current_date = datetime.now().strftime('%d.%m')
    return render_template('suppliers_orders.html', suppliers=suppliers, current_date=current_date, establishment_name=g.establishment_name, username=g.username, role=g.role)

@app.route('/suppliers/<int:supplier_id>/add_product', methods=['GET', 'POST'])
@login_required
@user_details
def add_product_to_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    products = Product.query.group_by(Product.name).all()
    measurements = Measurement.query.all()
    if request.method == 'POST':
        product_id = request.form.get('product')
        measurement_id = request.form.get('measurement')

        if product_id and measurement_id:
            product = Product.query.get_or_404(product_id)
            supplier.products.append(product)  # Добавляем продукт к поставщику
            db.session.commit()
            return redirect(url_for('suppliers_page'))  # Перенаправляем на страницу поставщиков

    return render_template('add_product_to_supplier.html', supplier=supplier, products=products, measurements=measurements, establishment_name=g.establishment_name, username=g.username, role=g.role)

@app.route('/suppliers/<int:supplier_id>/edit_product', methods=['GET', 'POST'])
@login_required
@user_details
def edit_product_to_supplier(supplier_id):
    product = Product.query.get_or_404(supplier_id)
    supplier = Supplier.query.get_or_404(supplier_id)
    products = Product.query.group_by(Product.name).all()
    measurements = Measurement.query.all()
    product_ids = request.form.getlist('products')
    supplier.products = Product.query.filter(Product.id.in_(product_ids)).all()

    if request.method == 'POST':
        product_id = request.form.get('product')
        measurement_id = request.form.get('measurement')
        

        if product_id and measurement_id:
            product = Product.query.get_or_404(product_id)
            supplier.products.append(product)  # Добавляем продукт к поставщику
            db.session.commit()
            return redirect(url_for('suppliers_page'))  # Перенаправляем на страницу поставщиков

    return render_template('edit_product_to_supplier.html',product=product, supplier=supplier, products=products, measurements=measurements, establishment_name=g.establishment_name, username=g.username, role=g.role)


# Главная страница со списком блюд
@app.route('/dishes', methods=['GET'])
@login_required
def dishes():
    dishes = Dish.query.all()
    return render_template('dishes.html', dishes=dishes)

@app.route('/dishes/<int:dish_id>', methods=['GET'])
@login_required
def dish_detail(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    return render_template('dish_detail.html', dish=dish)

@app.route('/dishes/<int:dish_id>/download', methods=['GET'])
@login_required
def download_dish_pdf(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    
    page_width, page_height = A4
    left_margin = 50
    right_margin = 50
    line_height = 15  # Высота строки

    # Создаем временный буфер для PDF
    pdf_buffer = BytesIO()
    x_margin = 50
    # Создаем PDF с использованием ReportLab
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
    pdf.setTitle(f"Рецепт: {dish.name}")

    # Заголовок
    pdf.setFont("DejaVuSans", 16)
    pdf.drawString(50, page_height - 70, f"{dish.name}")

    # Если изображение есть, добавим его
    if dish.image_url:
        try:
            img_path = os.path.join(app.root_path, 'static', dish.image_url)
            pdf.drawImage(img_path, 50, page_height - 330, width=250, height=250, preserveAspectRatio=True)
        except Exception as e:
            pdf.setFont("DejaVuSans", 10)
            pdf.drawString(50, 770, f"[Ошибка загрузки изображения: {str(e)}]")

 

    # Парсинг HTML
    soup = BeautifulSoup(dish.preparation_steps, "html.parser")
    ol_items = soup.find_all('li')

    y_position = 480
    pdf.setFont("DejaVuSans", 10)

    for idx, li in enumerate(ol_items, start=1):
        line = f"{idx}. {li.get_text(strip=True)}"
        
        # Разбиваем текст на строки, чтобы он не выходил за правую границу
        wrapped_lines = simpleSplit(line, "DejaVuSans", 10, page_width - left_margin - right_margin)
    
        for wrapped_line in wrapped_lines:
            # Рисуем строку
            pdf.drawString(left_margin, y_position, wrapped_line)
            y_position -= line_height

            # Если достигли нижней границы страницы
            if y_position < 50:
                pdf.showPage()  # Создаем новую страницу
                pdf.setFont("DejaVuSans", 10)  # Устанавливаем шрифт для новой страницы
                y_position = page_height - 50  # Сбрасываем y_position

    # Ингредиенты
    y_position = 500
   
    pdf.setFont("DejaVuSans", 12)
    pdf.drawString(50, y_position, "Способ приготовления:")
    

    data = [["Название продукта", "Ед. изм.", "Вес"]]  # Заголовки
    pdf.setFont("DejaVuSans", 12)
    # Добавляем данные о продуктах
    for dish_product in dish.dish_products:
        product = dish_product.product
        data.append([
            product.name,
            product.measurement.name,
            f"{dish_product.quantity:.2f}"
        ])
    pdf.setFont("DejaVuSans", 12)
    # Настраиваем стиль таблицы
    table = Table(data, colWidths=[170, 60, 40])  # ширина колонок
    table.setStyle(TableStyle([
    # Стиль заголовков
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Фон заголовка
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Цвет текста заголовка
    ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),  # Жирный шрифт для заголовка
    ('FONTSIZE', (0, 0), (-1, 0), 10),  # Размер шрифта для заголовка
    
    # Стиль данных
    ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),  # Обычный шрифт для данных
    ('FONTSIZE', (0, 1), (-1, -1), 10),  # Размер шрифта для данных
    ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Фон данных
    ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Сетка таблицы
]))

    # Рисуем таблицу в PDF
    table.wrapOn(pdf, 320, page_height)
    table.drawOn(pdf, 320, page_height - 265)

    # Генерация QR-кода
    qr_url = f"{request.host_url}dishes/{dish_id}"
    qr = qrcode.make(qr_url)  # Создаем QR-код
    
    y_position = 705
    # Сохраняем QR-код в временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_qr_file:
        qr.save(temp_qr_file, format="PNG")
        temp_qr_file.close()  # Закрываем файл, чтобы можно было использовать его путь
        
        # Добавляем QR-код в PDF
        pdf.drawImage(temp_qr_file.name, x_margin + 505, y_position + 95, width=40, height=40)
        
        # Удаляем временный файл после использования
        os.remove(temp_qr_file.name)       

    # Завершаем PDF
    pdf.save()

    # Перемещаем курсор в начало буфера
    pdf_buffer.seek(0)

   # Кодируем имя файла для Content-Disposition
    filename = f"{dish.name}.pdf"
    filename_encoded = quote(filename)

    # Возвращаем PDF в виде HTTP-ответа
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename_encoded}"

    return response

# Страница добавления нового блюда
@app.route('/dishes/add', methods=['GET', 'POST'])
@login_required
def add_dish():
    products = Product.query.group_by(Product.name).all()
    measurements = Measurement.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        image_file = request.files.get('image')
        # Поле для изображения
        image_path = None
        if image_file:
            filename = secure_filename(image_file.filename)
            relative_image_path = f"uploads/{filename}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        # Обработка загруженного видео
        video_file = request.files.get('video')
        video_path = None
        if video_file:
            filename = secure_filename(video_file.filename)
            relative_video_path = f"uploads/{filename}"
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_path)

        preparation_steps = request.form.get('preparation_steps')
        
        # Создаем блюдо
        dish = Dish(
            name=name,
            image_url=relative_image_path,
            video_url=relative_video_path,
            preparation_steps=preparation_steps
        )
        db.session.add(dish)
        db.session.flush()  # Получаем ID блюда после вставки

        # Обработка продуктов и количества
        product_ids = request.form.getlist('product_id')
        quantities = request.form.getlist('quantity')
        
        for product_id, quantity in zip(product_ids, quantities):
            if product_id and quantity:  # Проверка, что оба значения не пустые
                try:
                    quantity_value = float(quantity)  # Преобразуем количество в число
                    product = Product.query.get(int(product_id))
                    if product:
                        # Добавляем продукт через модель DishProduct
                        dish_product = DishProduct(
                            dish_id=dish.id, 
                            product_id=product.id, 
                            quantity=quantity_value  # Передаем количество
                        )
                        db.session.add(dish_product)
                except ValueError:
                    # Игнорируем, если количество не удалось преобразовать в float
                    continue

        db.session.commit()  # Сохраняем все изменения в базе данных
        return redirect(url_for('dishes'))
    
    return render_template('add_dish.html', products=products, measurements=measurements)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@user_details
def profile_page():    
    return render_template('user_profile.html', username=g.username, role=g.role, establishment_name=g.establishment_name)

@app.route('/assign_inventory/<int:user_id>', methods=['GET', 'POST'])
@login_required
@user_details
def assign_inventory(user_id):
    user = User.query.get_or_404(user_id)
    
    # Получаем список локаций и продуктов для текущего заведения пользователя
    locations = Location.query.filter_by(establishment_id=g.establishment_id).all()
    
    
    if request.method == 'POST':
        # Получаем выбранные продукты и локации из формы
        
        selected_locations = request.form.getlist('locations')
        
        # Удаляем текущие назначения и добавляем новые
        UserProductLocation.query.filter_by(user_id=user.id).delete()
        for location_id in selected_locations:
            
            assignment = UserProductLocation(user_id=user.id, location_id=location_id)
            db.session.add(assignment)
        
        db.session.commit()
        flash('Назначения успешно обновлены', 'success')
        return redirect(url_for('products_page'))  # Перенаправляем на панель администратора

    return render_template('assign_inventory.html', user=user, locations=locations, username=g.username, role=g.role, establishment_name=g.establishment_name )

if __name__ == '__main__':
    app.run(debug=True)





