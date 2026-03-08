import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Исправление дубликатов упражнений...")

# Находим все уникальные названия упражнений
cursor.execute('''
    SELECT name, MIN(id) as main_id 
    FROM exercises 
    GROUP BY name 
    HAVING COUNT(*) > 1
''')
duplicates = cursor.fetchall()

for name, main_id in duplicates:
    print(f"\nУпражнение '{name}':")
    print(f"  Основной ID: {main_id}")
    
    # Находим все дублирующиеся ID
    cursor.execute('SELECT id FROM exercises WHERE name = ? AND id != ?', (name, main_id))
    duplicate_ids = [row[0] for row in cursor.fetchall()]
    print(f"  Дубликаты ID: {duplicate_ids}")
    
    # Обновляем все подходы в статистике
    for dup_id in duplicate_ids:
        cursor.execute('''
            UPDATE completed_sets 
            SET exercise_id = ?, exercise_name = ? 
            WHERE exercise_id = ?
        ''', (main_id, name, dup_id))
        print(f"  Обновлено подходов с ID {dup_id} -> {main_id}: {cursor.rowcount}")
    
    # Удаляем дубликаты из библиотеки
    cursor.execute('DELETE FROM exercises WHERE id IN ({})'.format(','.join('?' * len(duplicate_ids))), duplicate_ids)
    print(f"  Удалено дубликатов из библиотеки: {len(duplicate_ids)}")

conn.commit()

print("\nПроверка результата:")
cursor.execute('''
    SELECT exercise_id, exercise_name, COUNT(*) 
    FROM completed_sets 
    GROUP BY exercise_id, exercise_name
''')
for row in cursor.fetchall():
    print(f"  {row[1]} (ID: {row[0]}) - {row[2]} подходов")

conn.close()
print("\nГотово!")