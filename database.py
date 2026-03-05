import sqlite3
import os

DB_NAME = 'train.db'

def get_db():
    """Создает соединение с БД."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Чтобы обращаться к колонкам по имени
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
        # Добавим демо-запись для примера
        cursor.execute('''
            INSERT INTO workouts (date, exercise, sets, reps, weight)
            VALUES (date('now'), 'Жим лежа', 3, 10, 50.5)
        ''')
        conn.commit()
        conn.close()
        print("База данных инициализирована.")
    else:
        print("База данных найдена.")

# Функции для работы с данными
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