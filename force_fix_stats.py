import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Принудительное исправление статистики...\n")

# Находим все уникальные названия упражнений в статистике
cursor.execute('''
    SELECT DISTINCT exercise_name FROM completed_sets
''')
names = cursor.fetchall()

for (name,) in names:
    print(f"\nОбрабатываем упражнение: '{name}'")
    
    # Ищем это упражнение в библиотеке
    cursor.execute('SELECT id FROM exercises WHERE LOWER(name) = LOWER(?) LIMIT 1', (name,))
    lib_ex = cursor.fetchone()
    
    if lib_ex:
        correct_id = lib_ex[0]
        print(f"  Найдено в библиотеке с ID: {correct_id}")
        
        # Смотрим, какие ID сейчас в статистике для этого упражнения
        cursor.execute('''
            SELECT DISTINCT exercise_id FROM completed_sets 
            WHERE LOWER(exercise_name) = LOWER(?)
        ''', (name,))
        current_ids = cursor.fetchall()
        
        for (old_id,) in current_ids:
            if old_id != correct_id:
                print(f"  Обновляем ID {old_id} -> {correct_id}")
                cursor.execute('''
                    UPDATE completed_sets 
                    SET exercise_id = ? 
                    WHERE exercise_id = ? AND LOWER(exercise_name) = LOWER(?)
                ''', (correct_id, old_id, name))
                print(f"    Обновлено записей: {cursor.rowcount}")
    else:
        print(f"  ⚠️ Упражнение '{name}' не найдено в библиотеке!")

conn.commit()

print("\n" + "="*50)
print("Проверка результата:")
cursor.execute('''
    SELECT exercise_id, exercise_name, COUNT(*) 
    FROM completed_sets 
    GROUP BY exercise_id, exercise_name
    ORDER BY exercise_name
''')
for row in cursor.fetchall():
    print(f"  {row[1]} (ID: {row[0]}) - {row[2]} подходов")

conn.close()
print("\nГотово!")