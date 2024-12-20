from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FileField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo,  Optional
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Product

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    
    # Поле для выбора роли с вариантами (админ не доступен)
    role = SelectField('Роль', choices=[
        ('повар', 'Повар'),
        ('пицца', 'Пицца'),
        ('сушист', 'Сушист'),
        ('старший', 'Старший'),
    ], validators=[DataRequired()])

    establishment = SelectField('Заведение', choices=[('1', 'Лукашевича'), ('2', 'Ленина')], validators=[DataRequired()])
    
    submit = SubmitField('Регистрация')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class DishForm(FlaskForm):
    name = StringField('Название блюда', validators=[DataRequired()])
    image = FileField('Фото блюда', validators=[Optional()])
    preparation_steps = TextAreaField('Технология приготовления', validators=[Optional()])
    video_url = StringField('Ссылка на видео', validators=[Optional()])
    
class ProductQuantityForm(FlaskForm):
    product = QuerySelectField(
        'Продукт',
        query_factory=lambda: Product.query.group_by(Product.name).all(),
        allow_blank=True,
        get_label='name'
    )
    quantity = FloatField('Количество', validators=[Optional()])