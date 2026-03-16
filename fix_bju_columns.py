import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Добавление колонок в таблицу bju_settings...")

try:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN gender_id INTEGER DEFAULT 1")
    print("✅ Добавлена колонка gender_id")
except Exception as e:
    print(f"⏩ gender_id: {e}")

try:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN activity_id INTEGER DEFAULT 3")
    print("✅ Добавлена колонка activity_id")
except Exception as e:
    print(f"⏩ activity_id: {e}")

try:
    cursor.execute("ALTER TABLE bju_settings ADD COLUMN goal_id INTEGER DEFAULT 1")
    print("✅ Добавлена колонка goal_id")
except Exception as e:
    print(f"⏩ goal_id: {e}")

# Обновляем существующие записи
cursor.execute('''
    UPDATE bju_settings 
    SET gender_id = CASE gender 
        WHEN 'male' THEN 1 
        WHEN 'female' THEN 2 
        ELSE 1 
    END
''')
print(f"✅ Обновлены gender_id: {cursor.rowcount} записей")

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
print(f"✅ Обновлены activity_id: {cursor.rowcount} записей")

cursor.execute('''
    UPDATE bju_settings 
    SET goal_id = CASE goal 
        WHEN 'maintain' THEN 1 
        WHEN 'lose' THEN 2 
        WHEN 'gain' THEN 3 
        ELSE 1 
    END
''')
print(f"✅ Обновлены goal_id: {cursor.rowcount} записей")

conn.commit()
conn.close()
print("\n✅ Готово!")
input("Нажми Enter для выхода...")