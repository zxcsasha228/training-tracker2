import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("🔧 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ТАБЛИЦЫ bju_settings")
print("="*50)

# Проверяем текущую структуру таблицы
cursor.execute("PRAGMA table_info(bju_settings)")
columns = cursor.fetchall()
print("\nТекущая структура таблицы bju_settings:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

# Добавляем колонки, если их нет
column_names = [col[1] for col in columns]

print("\n📁 Добавление недостающих колонок:")

if 'gender_id' not in column_names:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN gender_id INTEGER DEFAULT 1")
    print("  ✅ Добавлена колонка gender_id")
else:
    print("  ⏩ gender_id уже существует")

if 'activity_id' not in column_names:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN activity_id INTEGER DEFAULT 3")
    print("  ✅ Добавлена колонка activity_id")
else:
    print("  ⏩ activity_id уже существует")

if 'goal_id' not in column_names:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN goal_id INTEGER DEFAULT 1")
    print("  ✅ Добавлена колонка goal_id")
else:
    print("  ⏩ goal_id уже существует")

# Обновляем существующие записи
print("\n📁 Обновление существующих записей:")

# Получаем все записи
cursor.execute("SELECT id, gender, activity_level, goal FROM bju_settings")
rows = cursor.fetchall()

for row in rows:
    row_id = row[0]
    gender = row[1]
    activity = row[2]
    goal = row[3]
    
    # Определяем gender_id
    gender_id = 1 if gender == 'male' else 2
    
    # Определяем activity_id
    if activity == 1.2:
        activity_id = 1
    elif activity == 1.375:
        activity_id = 2
    elif activity == 1.55:
        activity_id = 3
    elif activity == 1.725:
        activity_id = 4
    elif activity == 1.9:
        activity_id = 5
    else:
        activity_id = 3
    
    # Определяем goal_id
    if goal == 'maintain':
        goal_id = 1
    elif goal == 'lose':
        goal_id = 2
    elif goal == 'gain':
        goal_id = 3
    else:
        goal_id = 1
    
    cursor.execute('''
        UPDATE bju_settings 
        SET gender_id = ?, activity_id = ?, goal_id = ?
        WHERE id = ?
    ''', (gender_id, activity_id, goal_id, row_id))

print(f"  ✅ Обновлено {len(rows)} записей")

# Проверяем итоговую структуру
cursor.execute("PRAGMA table_info(bju_settings)")
columns = cursor.fetchall()
print("\n✅ Итоговая структура таблицы bju_settings:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

conn.commit()
conn.close()

print("\n" + "="*50)
print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
input("\nНажми Enter для выхода...")