import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Добавление колонки enabled в таблицу easter_egg_settings...")

try:
    cursor.execute("ALTER TABLE easter_egg_settings ADD COLUMN enabled INTEGER DEFAULT 1")
    print("✅ Колонка enabled добавлена")
    
    # Обновляем существующие записи
    cursor.execute("UPDATE easter_egg_settings SET enabled = 1 WHERE enabled IS NULL")
    print("✅ Значения обновлены")
    
except Exception as e:
    print(f"⏩ {e}")

conn.commit()
conn.close()
print("Готово!")