import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Исправление таблицы weight_tracking...")

# Проверяем текущую структуру
cursor.execute("PRAGMA table_info(weight_tracking)")
columns = cursor.fetchall()
print("Текущая структура:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

# Создаём временную таблицу без UNIQUE
cursor.execute('''
    CREATE TABLE weight_tracking_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        weight REAL NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
''')

# Копируем данные
cursor.execute('''
    INSERT INTO weight_tracking_new (id, user_id, date, weight, notes, created_at)
    SELECT id, user_id, date, weight, notes, created_at FROM weight_tracking
''')

# Удаляем старую таблицу
cursor.execute('DROP TABLE weight_tracking')

# Переименовываем новую
cursor.execute('ALTER TABLE weight_tracking_new RENAME TO weight_tracking')

# Создаём индекс для быстрого поиска (опционально)
cursor.execute('CREATE INDEX idx_weight_date ON weight_tracking(user_id, date)')

conn.commit()
conn.close()

print("Готово! Таблица обновлена.")