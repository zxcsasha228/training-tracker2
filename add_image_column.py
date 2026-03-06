import sqlite3

# Подключаемся к базе
conn = sqlite3.connect('train.db')
cursor = conn.cursor()

# Проверяем текущую структуру
cursor.execute("PRAGMA table_info(exercises)")
columns = cursor.fetchall()
print("Текущая структура таблицы exercises:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

# Добавляем колонку image, если её нет
try:
    cursor.execute("ALTER TABLE exercises ADD COLUMN image TEXT")
    print("Колонка image успешно добавлена")
except Exception as e:
    print(f"Колонка image уже существует или ошибка: {e}")

# Проверяем обновлённую структуру
cursor.execute("PRAGMA table_info(exercises)")
columns = cursor.fetchall()
print("\nОбновлённая структура таблицы exercises:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

conn.close()
print("\nГотово!")