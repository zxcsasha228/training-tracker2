import sqlite3

conn = sqlite3.connect('train.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== ПРОВЕРКА ID УПРАЖНЕНИЙ В ТРЕНИРОВКАХ ===\n")

# Смотрим все упражнения в тренировках
cursor.execute('''
    SELECT DISTINCT we.exercise_id, e.id as lib_id, e.name as lib_name
    FROM workout_exercises we
    LEFT JOIN exercises e ON we.exercise_id = e.id
    ORDER BY we.exercise_id
''')
exercises = cursor.fetchall()

print("Упражнения, используемые в тренировках:")
for ex in exercises:
    if ex['lib_id']:
        print(f"  ✅ ID {ex['exercise_id']} -> есть в библиотеке: {ex['lib_name']} (ID {ex['lib_id']})")
    else:
        print(f"  ❌ ID {ex['exercise_id']} -> НЕТ в библиотеке!")

print("\n" + "="*50)

# Проверим конкретно ID 99
cursor.execute('''
    SELECT we.*, ws.name as workout_name
    FROM workout_exercises we
    JOIN workout_sessions ws ON we.workout_id = ws.id
    WHERE we.exercise_id = 99
''')
bad_exercises = cursor.fetchall()

if bad_exercises:
    print(f"\nНайдены записи с ID 99 в тренировках:")
    for ex in bad_exercises:
        print(f"  Тренировка: '{ex['workout_name']}' (ID {ex['workout_id']})")
        print(f"    подходы: {ex['sets']}x{ex['reps']}, вес: {ex['weight']}")
else:
    print(f"\nЗаписей с ID 99 в тренировках не найдено")

conn.close()
input("\nНажми Enter для выхода...")