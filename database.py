import sqlite3
import os

DB_NAME = 'train.db'

def get_db():
    """Создает соединение с БД."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создает таблицу, если её нет."""
    if not os.path.exists(DB_NAME):
        print("База данных не найдена. Создаю новую...")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                exercise TEXT NOT NULL,
                sets INTEGER,
                reps INTEGER,
                weight REAL
            )
        ''')
        # Добавим демо-записи для примера
        workouts_data = [
            ('2026-03-01', 'Жим лежа', 3, 10, 50.5),
            ('2026-03-03', 'Приседания', 4, 8, 80.0),
            ('2026-03-05', 'Тяга штанги', 3, 12, 60.0)
        ]
        cursor.executemany('''
            INSERT INTO workouts (date, exercise, sets, reps, weight)
            VALUES (?, ?, ?, ?, ?)
        ''', workouts_data)
        conn.commit()
        conn.close()
        print("База данных инициализирована.")
    else:
        print("База данных найдена.")

def add_workout(date, exercise, sets, reps, weight):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO workouts (date, exercise, sets, reps, weight)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, exercise, sets, reps, weight))
    conn.commit()
    conn.close()

def get_all_workouts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workouts ORDER BY date DESC')
    workouts = cursor.fetchall()
    conn.close()
    return workouts

# НОВЫЕ ФУНКЦИИ:

def get_workout(workout_id):
    """Получить одну тренировку по ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workouts WHERE id = ?', (workout_id,))
    workout = cursor.fetchone()
    conn.close()
    return workout

def update_workout(workout_id, date, exercise, sets, reps, weight):
    """Обновить существующую тренировку"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE workouts 
        SET date = ?, exercise = ?, sets = ?, reps = ?, weight = ?
        WHERE id = ?
    ''', (date, exercise, sets, reps, weight, workout_id))
    conn.commit()
    conn.close()

def delete_workout(workout_id):
    """Удалить тренировку"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM workouts WHERE id = ?', (workout_id,))
    conn.commit()
    conn.close()