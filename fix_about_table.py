import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("🔧 СОЗДАНИЕ ТАБЛИЦЫ about_content")

cursor.execute('''
    CREATE TABLE IF NOT EXISTS about_content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_key TEXT UNIQUE NOT NULL,
        section_title TEXT,
        section_content TEXT,
        icon TEXT,
        sort_order INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
print("✅ Таблица about_content создана")

# Добавляем контент по умолчанию
default_content = [
    ('mission', 'Наша миссия', 'Мы создали этот трекер тренировок, чтобы помочь вам достигать своих фитнес-целей, отслеживать прогресс и оставаться мотивированными.', 'fa-rocket', 1),
    ('team_developer', 'Громов Александр Сергеевич', 'Разработчик', 'fa-user-tie', 2),
    ('team_designer', 'Виртуальный помощник', 'Дизайнер', 'fa-paint-brush', 3),
    ('team_curator', 'Родионов Виктор Валерьевич', 'Куратор', 'fa-crown', 4),
]

for key, title, content, icon, sort in default_content:
    cursor.execute('''
        INSERT OR IGNORE INTO about_content (section_key, section_title, section_content, icon, sort_order)
        VALUES (?, ?, ?, ?, ?)
    ''', (key, title, content, icon, sort))

print("✅ Контент по умолчанию добавлен")

conn.commit()
conn.close()

print("\n✅ ГОТОВО!")
input("Нажми Enter для выхода...")
