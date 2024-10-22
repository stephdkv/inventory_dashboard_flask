from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user

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
