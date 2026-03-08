import sqlite3

conn = sqlite3.connect('train.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== ПРОВЕРКА ПРОБЛЕМЫ ===\n")

# Смотрим все упражнения в библиотеке
print("Упражнения в библиотеке:")
cursor.execute('SELECT id, name FROM exercises ORDER BY name')
exercises = cursor.fetchall()
for ex in exercises:
    print(f"  ID: {ex['id']} - {ex['name']}")

print("\n" + "="*50 + "\n")

# Смотрим все записи в статистике
print("Записи в статистике (completed_sets):")
cursor.execute('''
    SELECT cs.id, cs.exercise_id, cs.exercise_name, cs.weight, cs.reps, cw.workout_name, cw.date
    FROM completed_sets cs
    JOIN completed_workouts cw ON cs.workout_id = cw.workout_id AND cs.user_id = cw.user_id
    ORDER BY cs.id
''')
sets = cursor.fetchall()
for s in sets:
    print(f"  ID записи: {s['id']}, exercise_id: {s['exercise_id']}, название: '{s['exercise_name']}', вес: {s['weight']}x{s['reps']}, тренировка: {s['workout_name']} ({s['date']})")

print("\n" + "="*50 + "\n")

# Группируем по exercise_id
print("Группировка по exercise_id:")
cursor.execute('''
    SELECT exercise_id, exercise_name, COUNT(*) as count
    FROM completed_sets
    GROUP BY exercise_id
    ORDER BY exercise_id
''')
groups = cursor.fetchall()
for g in groups:
    print(f"  exercise_id: {g['exercise_id']}, название: '{g['exercise_name']}', записей: {g['count']}")

print("\n" + "="*50 + "\n")

# Проверяем соответствие exercise_id в статистике и в библиотеке
print("Проверка соответствия:")
for s in sets:
    cursor.execute('SELECT id, name FROM exercises WHERE id = ?', (s['exercise_id'],))
    ex_in_lib = cursor.fetchone()
    if ex_in_lib:
        print(f"  Запись ID {s['id']}: exercise_id {s['exercise_id']} -> есть в библиотеке: {ex_in_lib['name']}")
    else:
        print(f"  ⚠️  Запись ID {s['id']}: exercise_id {s['exercise_id']} -> ОТСУТСТВУЕТ в библиотеке!")

conn.close()
input("\nНажми Enter для выхода...")