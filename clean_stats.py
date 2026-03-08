import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Очистка статистики от битых записей...\n")

# Находим все exercise_id в статистике, которых нет в библиотеке
cursor.execute('''
    SELECT DISTINCT cs.exercise_id, cs.exercise_name 
    FROM completed_sets cs
    LEFT JOIN exercises e ON cs.exercise_id = e.id
    WHERE e.id IS NULL
''')
broken = cursor.fetchall()

print(f"Найдено битых записей: {len(broken)}")
for ex_id, ex_name in broken:
    print(f"  exercise_id: {ex_id}, название: '{ex_name}'")
    
    # Удаляем эти записи
    cursor.execute('DELETE FROM completed_sets WHERE exercise_id = ?', (ex_id,))
    print(f"    Удалено записей: {cursor.rowcount}")

conn.commit()

print("\n" + "="*50)
print("Проверка результата:")

# Проверяем, что осталось
cursor.execute('''
    SELECT cs.exercise_id, cs.exercise_name, e.name as lib_name
    FROM completed_sets cs
    LEFT JOIN exercises e ON cs.exercise_id = e.id
    ORDER BY cs.id
''')
remaining = cursor.fetchall()
print(f"Осталось записей в статистике: {len(remaining)}")
for ex_id, ex_name, lib_name in remaining:
    if lib_name:
        print(f"  ✅ exercise_id: {ex_id}, название: '{ex_name}' (есть в библиотеке: '{lib_name}')")
    else:
        print(f"  ❌ exercise_id: {ex_id}, название: '{ex_name}' (НЕТ в библиотеке!)")

conn.close()
input("\nНажми Enter для выхода...")