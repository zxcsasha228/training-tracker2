import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = 'train.db'

def add_test_data():
    """Добавляет тестовые данные для статистики"""
    
    # Получаем ID пользователя (обычно 1 для admin, 2 для user1)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Выбираем пользователя (можно изменить)
    cursor.execute("SELECT id FROM users WHERE username = 'user1'")
    user = cursor.fetchone()
    if not user:
        cursor.execute("SELECT id FROM users LIMIT 1")
        user = cursor.fetchone()
    
    user_id = user[0]
    print(f"Добавляем данные для пользователя ID: {user_id}")
    
    # Получаем ID упражнений
    cursor.execute("SELECT id, name FROM exercises")
    exercises = cursor.fetchall()
    
    if not exercises:
        print("❌ Нет упражнений в базе! Сначала добавьте упражнения.")
        conn.close()
        return
    
    print(f"Найдено упражнений: {len(exercises)}")
    
    # Очищаем старые тестовые данные (опционально)
    cursor.execute("DELETE FROM completed_sets WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM completed_workouts WHERE user_id = ?", (user_id,))
    print("✅ Старые тестовые данные удалены")
    
    # Генерируем данные за последние 30 дней
    start_date = datetime.now() - timedelta(days=30)
    workout_counter = 1
    
    for exercise in exercises:
        exercise_id = exercise[0]
        exercise_name = exercise[1]
        
        # Для каждого упражнения генерируем 8-15 тренировок
        num_workouts = random.randint(8, 15)
        
        # Базовый вес (разный для разных упражнений)
        base_weight = random.choice([40, 50, 60, 70, 80, 100, 120])
        
        for i in range(num_workouts):
            # Дата тренировки (разброс по 30 дням)
            days_ago = random.randint(0, 30)
            workout_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            # Прогрессия веса (чем ближе к сегодня, тем больше вес)
            progress_factor = 1 + (30 - days_ago) / 60  # от 0.5 до 1.5
            weight = round(base_weight * progress_factor, 1)
            weight = min(weight, 250)  # ограничиваем 250 кг
            
            # Количество повторений
            reps = random.choice([5, 6, 8, 10, 12])
            
            # 1ПМ по формуле
            if reps == 1:
                one_rm = weight
            else:
                one_rm = round(weight * (1 + reps / 30), 1)
            
            # Добавляем подход
            cursor.execute('''
                INSERT INTO completed_sets 
                (user_id, workout_id, exercise_id, exercise_name, workout_date, weight, reps, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                workout_counter,
                exercise_id,
                exercise_name,
                workout_date,
                weight,
                reps,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            workout_counter += 1
    
    # Добавляем записи в completed_workouts
    # Получаем уникальные даты тренировок
    cursor.execute('''
        SELECT DISTINCT workout_date, COUNT(*) as sets_count 
        FROM completed_sets 
        WHERE user_id = ? 
        GROUP BY workout_date
    ''', (user_id,))
    
    workouts = cursor.fetchall()
    
    for workout in workouts:
        workout_date = workout[0]
        sets_count = workout[1]
        duration = random.randint(1800, 5400)  # 30-90 минут в секундах
        
        cursor.execute('''
            INSERT INTO completed_workouts 
            (user_id, workout_id, workout_name, date, duration, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            random.randint(1, 1000),
            f"Тренировка {workout_date}",
            workout_date,
            duration,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    conn.commit()
    
    # Подсчитываем результат
    cursor.execute("SELECT COUNT(*) FROM completed_sets WHERE user_id = ?", (user_id,))
    sets_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM completed_workouts WHERE user_id = ?", (user_id,))
    workouts_count = cursor.fetchone()[0]
    
    print(f"\n✅ Добавлено тестовых данных:")
    print(f"   - Выполненных подходов: {sets_count}")
    print(f"   - Завершённых тренировок: {workouts_count}")
    
    conn.close()

def add_single_exercise_data():
    """Добавить данные для конкретного упражнения с прогрессией"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Выбираем пользователя
    cursor.execute("SELECT id FROM users WHERE username = 'user1'")
    user = cursor.fetchone()
    if not user:
        cursor.execute("SELECT id FROM users LIMIT 1")
        user = cursor.fetchone()
    user_id = user[0]
    
    # Выбираем упражнение "Жим штанги лежа" или первое попавшееся
    cursor.execute("SELECT id, name FROM exercises WHERE name LIKE '%жим%' OR name LIKE '%Жим%'")
    exercise = cursor.fetchone()
    if not exercise:
        cursor.execute("SELECT id, name FROM exercises LIMIT 1")
        exercise = cursor.fetchone()
    
    exercise_id = exercise[0]
    exercise_name = exercise[1]
    
    print(f"Добавляем данные для упражнения: {exercise_name}")
    
    # Удаляем старые данные для этого упражнения (опционально)
    cursor.execute("DELETE FROM completed_sets WHERE user_id = ? AND exercise_id = ?", (user_id, exercise_id))
    
    # Генерируем прогрессию от 40 кг до 120 кг за 20 тренировок
    for i in range(1, 21):
        days_ago = 30 - i
        workout_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # Линейная прогрессия
        weight = 40 + (i * 4)  # 40, 44, 48... до 120
        weight = min(weight, 120)
        
        reps = random.choice([5, 6, 8, 10])
        
        if reps == 1:
            one_rm = weight
        else:
            one_rm = round(weight * (1 + reps / 30), 1)
        
        cursor.execute('''
            INSERT INTO completed_sets 
            (user_id, workout_id, exercise_id, exercise_name, workout_date, weight, reps, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            i,
            exercise_id,
            exercise_name,
            workout_date,
            weight,
            reps,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM completed_sets WHERE user_id = ? AND exercise_id = ?", (user_id, exercise_id))
    count = cursor.fetchone()[0]
    print(f"✅ Добавлено {count} подходов для упражнения {exercise_name}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("📊 Генератор тестовых данных для статистики")
    print("=" * 50)
    
    print("\n1. Добавляем полные данные для всех упражнений...")
    add_test_data()
    
    print("\n2. Добавляем прогрессивные данные для основного упражнения...")
    add_single_exercise_data()
    
    print("\n✅ Готово! Зайдите на страницу статистики и выберите упражнение.")