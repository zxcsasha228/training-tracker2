import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Добавление колонки full_name в таблицу users...")

# Добавляем колонку full_name
try:
    cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    print("Колонка full_name добавлена")
except Exception as e:
    print(f"Колонка уже существует или ошибка: {e}")

# Заполняем full_name для существующих пользователей (если пусто)
cursor.execute("UPDATE users SET full_name = username WHERE full_name IS NULL OR full_name = ''")
print("Заполнены пустые значения")

conn.commit()
conn.close()

print("Готово!")