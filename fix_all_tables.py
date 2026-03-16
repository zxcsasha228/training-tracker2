import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("🔄 НАЧИНАЕМ ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ")
print("="*50)

# ========== ТАБЛИЦА USERS ==========
print("\n📁 Таблица users:")
try:
    cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    print("  ✅ Добавлена колонка full_name")
    
    # Заполняем full_name для существующих пользователей
    cursor.execute("UPDATE users SET full_name = username WHERE full_name IS NULL")
    print(f"  ✅ Обновлено {cursor.rowcount} записей")
except Exception as e:
    print(f"  ⏩ {e}")

# ========== ТАБЛИЦА BJU_SETTINGS ==========
print("\n📁 Таблица bju_settings:")

# Добавляем колонки
try:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN gender_id INTEGER DEFAULT 1")
    print("  ✅ Добавлена колонка gender_id")
except Exception as e:
    print(f"  ⏩ gender_id: {e}")

try:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN activity_id INTEGER DEFAULT 3")
    print("  ✅ Добавлена колонка activity_id")
except Exception as e:
    print(f"  ⏩ activity_id: {e}")

try:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN goal_id INTEGER DEFAULT 1")
    print("  ✅ Добавлена колонка goal_id")
except Exception as e:
    print(f"  ⏩ goal_id: {e}")

# Обновляем существующие записи
cursor.execute('''
    UPDATE bju_settings 
    SET gender_id = CASE gender 
        WHEN 'male' THEN 1 
        WHEN 'female' THEN 2 
        ELSE 1 
    END
''')
print(f"  ✅ Обновлены gender_id: {cursor.rowcount} записей")

cursor.execute('''
    UPDATE bju_settings 
    SET activity_id = CASE 
        WHEN activity_level = 1.2 THEN 1
        WHEN activity_level = 1.375 THEN 2
        WHEN activity_level = 1.55 THEN 3
        WHEN activity_level = 1.725 THEN 4
        WHEN activity_level = 1.9 THEN 5
        ELSE 3
    END
''')
print(f"  ✅ Обновлены activity_id: {cursor.rowcount} записей")

cursor.execute('''
    UPDATE bju_settings 
    SET goal_id = CASE goal 
        WHEN 'maintain' THEN 1 
        WHEN 'lose' THEN 2 
        WHEN 'gain' THEN 3 
        ELSE 1 
    END
''')
print(f"  ✅ Обновлены goal_id: {cursor.rowcount} записей")

# ========== СОЗДАЁМ ТАБЛИЦЫ СПРАВОЧНИКОВ ==========
print("\n📁 Создание справочных таблиц:")

# Таблица gender_types
cursor.execute('''
    CREATE TABLE IF NOT EXISTS gender_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        icon TEXT,
        sort_order INTEGER DEFAULT 0
    )
''')
print("  ✅ Таблица gender_types создана")

# Таблица activity_levels
cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        value REAL NOT NULL,
        icon TEXT,
        description TEXT,
        sort_order INTEGER DEFAULT 0
    )
''')
print("  ✅ Таблица activity_levels создана")

# Таблица goal_types
cursor.execute('''
    CREATE TABLE IF NOT EXISTS goal_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        icon TEXT,
        description TEXT,
        sort_order INTEGER DEFAULT 0
    )
''')
print("  ✅ Таблица goal_types создана")

# Таблица about_content
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
print("  ✅ Таблица about_content создана")

# ========== ЗАПОЛНЯЕМ СПРАВОЧНИКИ ==========
print("\n📁 Заполнение справочников:")

# Типы пола
genders = [
    ('male', '👨 Мужской', 'fa-mars', 1),
    ('female', '👩 Женский', 'fa-venus', 2)
]
for name, display_name, icon, sort in genders:
    cursor.execute('''
        INSERT OR IGNORE INTO gender_types (name, display_name, icon, sort_order)
        VALUES (?, ?, ?, ?)
    ''', (name, display_name, icon, sort))
print("  ✅ Типы пола добавлены")

# Уровни активности
activities = [
    ('minimal', '🪑 Минимальная', 1.2, 'fa-chair', 'Сидячая работа, нет тренировок', 1),
    ('light', '🚶 Лёгкая', 1.375, 'fa-walking', '1-3 тренировки в неделю', 2),
    ('moderate', '🏃 Средняя', 1.55, 'fa-running', '3-5 тренировок в неделю', 3),
    ('high', '💪 Высокая', 1.725, 'fa-dumbbell', '6-7 тренировок в неделю', 4),
    ('extreme', '🏆 Очень высокая', 1.9, 'fa-trophy', 'Спортсмены, физическая работа', 5)
]
for name, display_name, value, icon, desc, sort in activities:
    cursor.execute('''
        INSERT OR IGNORE INTO activity_levels (name, display_name, value, icon, description, sort_order)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, display_name, value, icon, desc, sort))
print("  ✅ Уровни активности добавлены")

# Цели
goals = [
    ('maintain', '🏋️ Поддержание', 'fa-balance-scale', 'Сохранить текущий вес', 1),
    ('lose', '📉 Похудение', 'fa-arrow-down', 'Снизить вес', 2),
    ('gain', '📈 Набор массы', 'fa-arrow-up', 'Увеличить мышечную массу', 3)
]
for name, display_name, icon, desc, sort in goals:
    cursor.execute('''
        INSERT OR IGNORE INTO goal_types (name, display_name, icon, description, sort_order)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, display_name, icon, desc, sort))
print("  ✅ Цели добавлены")

# ========== СОЗДАЁМ АДМИНА ==========
print("\n📁 Проверка администратора:")

cursor.execute("SELECT * FROM users WHERE username = 'admin'")
admin = cursor.fetchone()
if not admin:
    cursor.execute('''
        INSERT INTO users (username, password, full_name, is_admin)
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin123', 'Администратор', 1))
    print("  ✅ Создан администратор: admin / admin123")
else:
    print("  ⏩ Администратор уже существует")

conn.commit()
conn.close()

print("\n" + "="*50)
print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
input("\nНажми Enter для выхода...")