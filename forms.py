from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    
    # Поле для выбора роли с вариантами (админ не доступен)
    role = SelectField('Роль', choices=[
        ('повар лб', 'Повар ЛБ'),
        ('пицца лб', 'Пицца ЛБ'),
        ('сушист лб', 'Сушист ЛБ'),
        ('старший лб', 'Старший ЛБ'),
        ('повар пб', 'Повар ПБ'),
        ('сушист пб', 'Сушист ПБ'),
        ('старший пб', 'Старший ПБ'),
        ('пицца пб', 'Пицца ПБ')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')
