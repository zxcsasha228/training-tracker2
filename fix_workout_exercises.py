import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Проверка упражнений в тренировках...\n")

# Находим все exercise_id в workout_exercises, которых нет в exercises
cursor.execute('''
    SELECT DISTINCT we.exercise_id 
    FROM workout_exercises we
    LEFT JOIN exercises e ON we.exercise_id = e.id
    WHERE e.id IS NULL
''')
missing = cursor.fetchall()

print(f"Найдено битых exercise_id в тренировках: {len(missing)}")
for (ex_id,) in missing:
    print(f"  exercise_id: {ex_id} - отсутствует в библиотеке")
    
    # Показываем, в каких тренировках используется этот ID
    cursor.execute('''
        SELECT ws.id, ws.name, ws.user_id 
        FROM workout_exercises we
        JOIN workout_sessions ws ON we.workout_id = ws.id
        WHERE we.exercise_id = ?
    ''', (ex_id,))
    workouts = cursor.fetchall()
    for w in workouts:
        print(f"    Тренировка ID {w[0]}: '{w[1]}' (user_id: {w[2]})")

print("\n" + "="*50)

# Если хотим удалить эти записи (чтобы они не мешали)
answer = input("\nУдалить битые записи из тренировок? (да/нет): ")
if answer.lower() == 'да':
    for (ex_id,) in missing:
        cursor.execute('DELETE FROM workout_exercises WHERE exercise_id = ?', (ex_id,))
        print(f"Удалено записей с exercise_id {ex_id}: {cursor.rowcount}")
    conn.commit()
    print("Готово!")

conn.close()