import sqlite3

conn = sqlite3.connect('train.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== ПРОВЕРКА СТАТИСТИКИ ===\n")

# Смотрим все завершённые тренировки
cursor.execute('''
    SELECT * FROM completed_workouts
''')
workouts = cursor.fetchall()
print(f"Завершённых тренировок: {len(workouts)}")
for w in workouts:
    print(f"  ID: {w['id']}, Тренировка: {w['workout_name']}, Дата: {w['date']}")

print("\n=== ВСЕ ПОДХОДЫ ===")
cursor.execute('''
    SELECT cs.*, cw.workout_name 
    FROM completed_sets cs
    JOIN completed_workouts cw ON cs.workout_id = cw.workout_id AND cs.user_id = cw.user_id
''')
sets = cursor.fetchall()
print(f"Всего подходов: {len(sets)}")
for s in sets:
    print(f"  Упражнение: {s['exercise_name']} (ID: {s['exercise_id']}), Вес: {s['weight']}x{s['reps']}, Тренировка: {s['workout_name']}")

print("\n=== УНИКАЛЬНЫЕ УПРАЖНЕНИЯ ===")
cursor.execute('''
    SELECT exercise_id, exercise_name, COUNT(*) as count
    FROM completed_sets
    GROUP BY exercise_id, exercise_name
''')
unique = cursor.fetchall()
print(f"Уникальных упражнений: {len(unique)}")
for u in unique:
    print(f"  {u['exercise_name']} (ID: {u['exercise_id']}) - {u['count']} подходов")

conn.close()