import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Исправление таблицы пасхалки...")

# Удаляем старую таблицу
cursor.execute('DROP TABLE IF EXISTS easter_egg_settings')
print("Старая таблица удалена")

# Создаём новую с правильной структурой
cursor.execute('''
    CREATE TABLE easter_egg_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        media_path TEXT,
        media_type TEXT DEFAULT 'image',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
print("Новая таблица создана")

# Добавляем запись по умолчанию
cursor.execute('''
    INSERT INTO easter_egg_settings (media_path, media_type)
    VALUES (?, ?)
''', ('uploads/easter_default.jpg', 'image'))
print("Запись по умолчанию добавлена")

conn.commit()
conn.close()

print("Готово!")