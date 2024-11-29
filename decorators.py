from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user
from flask import g

def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)  # Пользователь не аутентифицирован
            # Добавим отладочный вывод
            print(f"Current user: {current_user.username}, Role: {current_user.role}")
            
            if current_user.role != role:
                abort(403)  # Запрещён доступ
            return func(*args, **kwargs)
        return wrapper
    return decorator

def user_details(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Предполагается, что current_user доступен
        g.establishment_id = current_user.establishment_id
        g.username = current_user.username
        g.role = current_user.role.capitalize()
        g.establishment_name = "Лукашевича" if g.establishment_id == 1 else "Ленина"
        return f(*args, **kwargs)
    return decorated_function
