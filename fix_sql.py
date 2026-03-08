import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Шаг 4: Очистка базы данных\n")

# Удаляем неправильные записи из тренировок
cursor.execute('''
    DELETE FROM workout_exercises 
    WHERE exercise_id NOT IN (SELECT id FROM exercises)
''')
print(f"Удалено записей из workout_exercises: {cursor.rowcount}")

# Удаляем неправильные записи из статистики
cursor.execute('''
    DELETE FROM completed_sets 
    WHERE exercise_id NOT IN (SELECT id FROM exercises)
''')
print(f"Удалено записей из completed_sets: {cursor.rowcount}")

# Сохраняем изменения
conn.commit()

# Проверяем результат
print("\nОставшиеся записи в workout_exercises:")
cursor.execute('''
    SELECT we.*, e.name 
    FROM workout_exercises we
    JOIN exercises e ON we.exercise_id = e.id
''')
rows = cursor.fetchall()
for row in rows:
    print(f"  Тренировка ID {row[1]}, упражнение: {row[5]} (ID {row[2]})")

print("\nОставшиеся записи в completed_sets:")
cursor.execute('''
    SELECT cs.*, e.name 
    FROM completed_sets cs
    JOIN exercises e ON cs.exercise_id = e.id
''')
rows = cursor.fetchall()
for row in rows:
    print(f"  Тренировка ID {row[2]}, упражнение: {row[4]} (ID {row[3]})")

conn.close()
input("\nНажми Enter для выхода...")