import sqlite3

# Подключаемся к обеим базам данных
conn1 = sqlite3.connect('dublicat.db')  # Первая база данных
conn2 = sqlite3.connect('site.db')     # Вторая база данных

# Создаем курсоры
cursor1 = conn1.cursor()
cursor2 = conn2.cursor()

# Считываем все данные из таблицы `users` из первой базы
cursor1.execute("SELECT * FROM users")
users = cursor1.fetchall()

# Проверяем структуру таблицы
cursor1.execute("PRAGMA table_info(users)")
columns_info = cursor1.fetchall()
columns = [col[1] for col in columns_info]  # Список колонок
placeholders = ', '.join(['?'] * len(columns))  # Генерируем плейсхолдеры для вставки

# Вставляем данные во вторую базу
for user in users:
    try:
        cursor2.execute(f"INSERT INTO users ({', '.join(columns)}) VALUES ({placeholders})", user)
    except sqlite3.IntegrityError as e:
        print(f"Ошибка вставки для пользователя {user}: {e}")

# Сохраняем изменения
conn2.commit()

# Закрываем подключения
conn1.close()
conn2.close()

print("Данные успешно перенесены.")

