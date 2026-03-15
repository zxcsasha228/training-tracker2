import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

# Проверяем структуру таблицы
cursor.execute("PRAGMA table_info(bju_settings)")
columns = cursor.fetchall()
print("Структура таблицы bju_settings:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

# Проверяем несколько записей
cursor.execute("SELECT * FROM bju_settings LIMIT 11")
rows = cursor.fetchall()
print("\nПервые 11 записи:")
for row in rows:
    print(row)

conn.close()