import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Обновление таблицы bju_settings...")

# Проверяем, есть ли уже колонки с внешними ключами
cursor.execute("PRAGMA table_info(bju_settings)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

if 'gender_id' not in column_names:
    # Добавляем колонки для внешних ключей
    cursor.execute('ALTER TABLE bju_settings ADD COLUMN gender_id INTEGER DEFAULT 1')
    cursor.execute('ALTER TABLE bju_settings ADD COLUMN activity_id INTEGER DEFAULT 3')
    cursor.execute('ALTER TABLE bju_settings ADD COLUMN goal_id INTEGER DEFAULT 1')
    
    # Обновляем существующие записи
    cursor.execute('''
        UPDATE bju_settings 
        SET gender_id = CASE gender 
            WHEN 'male' THEN 1 
            WHEN 'female' THEN 2 
            ELSE 1 
        END
    ''')
    
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
    
    cursor.execute('''
        UPDATE bju_settings 
        SET goal_id = CASE goal 
            WHEN 'maintain' THEN 1 
            WHEN 'lose' THEN 2 
            WHEN 'gain' THEN 3 
            ELSE 1 
        END
    ''')
    
    print("Колонки добавлены и данные обновлены")

conn.commit()
conn.close()
print("Готово!")