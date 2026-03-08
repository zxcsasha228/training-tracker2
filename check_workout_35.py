import sqlite3

conn = sqlite3.connect('train.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== ПРОВЕРКА ТРЕНИРОВКИ ID 35 ===\n")

# Проверяем саму тренировку
cursor.execute('SELECT * FROM workout_sessions WHERE id = 35')
workout = cursor.fetchone()
if workout:
    print(f"Тренировка: {workout['name']}")
    print(f"Дата: {workout['date']}")
    print(f"User ID: {workout['user_id']}")
else:
    print("Тренировка 35 не найдена")

print("\n=== УПРАЖНЕНИЯ В ТРЕНИРОВКЕ 35 ===")
cursor.execute('''
    SELECT we.*, e.id as lib_id, e.name as lib_name
    FROM workout_exercises we
    LEFT JOIN exercises e ON we.exercise_id = e.id
    WHERE we.workout_id = 35
''')
exercises = cursor.fetchall()

for ex in exercises:
    print(f"\nЗапись в тренировке:")
    print(f"  exercise_id в тренировке: {ex['exercise_id']}")
    print(f"  В библиотеке: ID {ex['lib_id']}, название '{ex['lib_name']}'")
    print(f"  подходы: {ex['sets']}x{ex['reps']}, вес: {ex['weight']}")

conn.close()
input("\nНажми Enter для выхода...")