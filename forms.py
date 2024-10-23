from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo

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
    
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')
