import sqlite3
import os
from contextlib import contextmanager

DB_NAME = 'train.db'

@contextmanager
def get_db():
    """Контекстный менеджер для безопасной работы с БД"""
    conn = sqlite3.connect(DB_NAME, timeout=10)  # таймаут 10 секунд
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Создает таблицы, если их нет."""
    if not os.path.exists(DB_NAME):
        print("База данных не найдена. Создаю новую...")
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица тренировок
            cursor.execute('''
                CREATE TABLE workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    exercise TEXT NOT NULL,
                    sets INTEGER,
                    reps INTEGER,
                    weight REAL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Создаем тестового пользователя
            cursor.execute('''
                INSERT INTO users (username, password)
                VALUES (?, ?)
            ''', ('admin', 'admin123'))
            
            # Получаем ID созданного пользователя
            user_id = cursor.lastrowid
            
            # Добавляем демо-тренировки
            workouts_data = [
                (user_id, '2026-03-01', 'Жим лежа', 3, 10, 50.5),
                (user_id, '2026-03-03', 'Приседания', 4, 8, 80.0),
                (user_id, '2026-03-05', 'Тяга штанги', 3, 12, 60.0)
            ]
            cursor.executemany('''
                INSERT INTO workouts (user_id, date, exercise, sets, reps, weight)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', workouts_data)
            
        print("База данных инициализирована. Тестовый пользователь: admin / admin123")
    else:
        print("База данных найдена.")

# Функции для работы с пользователями
def create_user(username, password):
    """Создать нового пользователя"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password)
                VALUES (?, ?)
            ''', (username, password))
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def check_user(username, password):
    """Проверить логин и пароль"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            WHERE username = ? AND password = ?
        ''', (username, password))
        return cursor.fetchone()

def get_user_by_id(user_id):
    """Получить пользователя по ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()

# Функции для работы с тренировками
def add_workout(user_id, date, exercise, sets, reps, weight):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO workouts (user_id, date, exercise, sets, reps, weight)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, date, exercise, sets, reps, weight))

def get_user_workouts(user_id):
    """Получить тренировки конкретного пользователя"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM workouts 
            WHERE user_id = ? 
            ORDER BY date DESC
        ''', (user_id,))
        return cursor.fetchall()

def get_workout(workout_id, user_id):
    """Получить одну тренировку по ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM workouts 
            WHERE id = ? AND user_id = ?
        ''', (workout_id, user_id))
        return cursor.fetchone()

def update_workout(workout_id, user_id, date, exercise, sets, reps, weight):
    """Обновить тренировку"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE workouts 
            SET date = ?, exercise = ?, sets = ?, reps = ?, weight = ?
            WHERE id = ? AND user_id = ?
        ''', (date, exercise, sets, reps, weight, workout_id, user_id))

def delete_workout(workout_id, user_id):
    """Удалить тренировку"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM workouts 
            WHERE id = ? AND user_id = ?
        ''', (workout_id, user_id))