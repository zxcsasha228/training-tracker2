import sqlite3
import os
from contextlib import contextmanager

DB_NAME = 'train.db'

@contextmanager
def get_db():
    """Контекстный менеджер для безопасной работы с БД"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_user(user_id):
    """Получить данные пользователя по ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()

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
                    is_admin INTEGER DEFAULT 0,
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
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Создаем админа
            cursor.execute('''
                INSERT INTO users (username, password, is_admin)
                VALUES (?, ?, ?)
            ''', ('admin', 'admin123', 1))
            
            # Создаем тестового пользователя
            cursor.execute('''
                INSERT INTO users (username, password, is_admin)
                VALUES (?, ?, ?)
            ''', ('user1', 'user123', 0))
            
            # Получаем ID пользователей
            cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
            admin_id = cursor.fetchone()[0]
            
            cursor.execute('SELECT id FROM users WHERE username = ?', ('user1',))
            user1_id = cursor.fetchone()[0]
            
            # Добавляем демо-тренировки для админа
            admin_workouts = [
                (admin_id, '2026-03-01', 'Жим лежа', 3, 10, 50.5),
                (admin_id, '2026-03-03', 'Приседания', 4, 8, 80.0)
            ]
            cursor.executemany('''
                INSERT INTO workouts (user_id, date, exercise, sets, reps, weight)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', admin_workouts)
            
            # Добавляем демо-тренировки для обычного пользователя
            user_workouts = [
                (user1_id, '2026-03-02', 'Тяга штанги', 3, 12, 60.0),
                (user1_id, '2026-03-04', 'Жим гантелей', 3, 10, 20.5)
            ]
            cursor.executemany('''
                INSERT INTO workouts (user_id, date, exercise, sets, reps, weight)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', user_workouts)
            
        print("База данных инициализирована.")
        print("Админ: admin / admin123")
        print("Пользователь: user1 / user123")
    else:
        print("База данных найдена.")

# Функции для работы с пользователями
def create_user(username, password, is_admin=0):
    """Создать нового пользователя"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, is_admin)
                VALUES (?, ?, ?)
            ''', (username, password, is_admin))
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

# АДМИН-ФУНКЦИИ
def get_all_users():
    """Получить всех пользователей (для админа)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                u.*, 
                COUNT(w.id) as workouts_count 
            FROM users u
            LEFT JOIN workouts w ON u.id = w.user_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        ''')
        return cursor.fetchall()

def get_user_workouts_admin(user_id):
    """Получить тренировки любого пользователя (для админа)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM workouts 
            WHERE user_id = ? 
            ORDER BY date DESC
        ''', (user_id,))
        return cursor.fetchall()

def delete_user_admin(user_id):
    """Удалить пользователя и все его тренировки"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

def get_user_stats():
    """Получить общую статистику (для админа)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Общее количество пользователей
        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']
        
        # Общее количество тренировок
        cursor.execute('SELECT COUNT(*) as count FROM workouts')
        total_workouts = cursor.fetchone()['count']
        
        # Количество админов
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 1')
        total_admins = cursor.fetchone()['count']
        
        # Последние 5 тренировок
        cursor.execute('''
            SELECT w.*, u.username 
            FROM workouts w
            JOIN users u ON w.user_id = u.id
            ORDER BY w.date DESC
            LIMIT 5
        ''')
        recent_workouts = cursor.fetchall()
        
        return {
            'total_users': total_users,
            'total_workouts': total_workouts,
            'total_admins': total_admins,
            'recent_workouts': recent_workouts
        }

# Функции для работы с тренировками (обычные пользователи)
def add_workout(user_id, date, exercise, sets, reps, weight):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO workouts (user_id, date, exercise, sets, reps, weight)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, date, exercise, sets, reps, weight))

def get_user_with_password(user_id):
    """Получить данные пользователя включая пароль (только для админа)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password, is_admin, created_at 
            FROM users WHERE id = ?
        ''', (user_id,))
        return cursor.fetchone()

def get_all_users_with_passwords():
    """Получить всех пользователей с паролями (только для админа) - БЕЗ подсчета тренировок"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                id, 
                username, 
                password, 
                is_admin, 
                created_at
            FROM users
            ORDER BY created_at DESC
        ''')
        return cursor.fetchall()

def get_user_workouts(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM workouts 
            WHERE user_id = ? 
            ORDER BY date DESC
        ''', (user_id,))
        return cursor.fetchall()

def get_workout(workout_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM workouts 
            WHERE id = ? AND user_id = ?
        ''', (workout_id, user_id))
        return cursor.fetchone()

def update_workout(workout_id, user_id, date, exercise, sets, reps, weight):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE workouts 
            SET date = ?, exercise = ?, sets = ?, reps = ?, weight = ?
            WHERE id = ? AND user_id = ?
        ''', (date, exercise, sets, reps, weight, workout_id, user_id))

def delete_workout(workout_id, user_id):



    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM workouts 
            WHERE id = ? AND user_id = ?
        ''', (workout_id, user_id))

        # ================ БИБЛИОТЕКА УПРАЖНЕНИЙ ================
# ================ БИБЛИОТЕКА УПРАЖНЕНИЙ ================

def init_exercises_table():
    """Создать таблицу упражнений, если её нет"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    image TEXT,
                    muscle_group TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # Проверяем, есть ли уже упражнения
            cursor.execute('SELECT COUNT(*) as count FROM exercises')
            count = cursor.fetchone()['count']
            
            if count == 0:
                # Добавляем базовые упражнения
                base_exercises = [
                    ('Жим штанги лежа', None, 'Грудные'),
                    ('Приседания со штангой', None, 'Ноги'),
                    ('Становая тяга', None, 'Спина'),
                    ('Подтягивания', None, 'Спина'),
                    ('Отжимания на брусьях', None, 'Грудные'),
                    ('Жим гантелей сидя', None, 'Плечи'),
                    ('Тяга штанги в наклоне', None, 'Спина'),
                    ('Сгибание рук со штангой', None, 'Бицепс'),
                    ('Французский жим', None, 'Трицепс'),
                    ('Выпады с гантелями', None, 'Ноги'),
                    ('Скручивания', None, 'Пресс'),
                    ('Молотки с гантелями', None, 'Бицепс'),
                    ('Разгибание рук на блоке', None, 'Трицепс'),
                    ('Махи гантелями в стороны', None, 'Плечи'),
                    ('Тяга верхнего блока', None, 'Спина')
                ]
                
                for ex in base_exercises:
                    try:
                        cursor.execute('''
                            INSERT INTO exercises (name, image, muscle_group)
                            VALUES (?, ?, ?)
                        ''', ex)
                    except:
                        pass
    except Exception as e:
        print(f"Ошибка при создании таблицы exercises: {e}")

def get_all_exercises():
    """Получить все упражнения"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, image, muscle_group, created_by, created_at 
                FROM exercises 
                ORDER BY name
            ''')
            return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при получении упражнений: {e}")
        return []
def get_exercise(exercise_id):
    """Получить упражнение по ID"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exercises WHERE id = ?', (exercise_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Ошибка при получении упражнения: {e}")
        return None

def add_exercise(name, image, muscle_group, created_by):
    """Добавить новое упражнение"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже такое упражнение
            cursor.execute('SELECT id FROM exercises WHERE name = ?', (name,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"Упражнение '{name}' уже существует с ID {existing['id']}")
                return False
            
            cursor.execute('''
                INSERT INTO exercises (name, image, muscle_group, created_by)
                VALUES (?, ?, ?, ?)
            ''', (name, image, muscle_group, created_by))
            return True
    except Exception as e:
        print(f"Ошибка при добавлении упражнения: {e}")
        return False

def update_exercise(exercise_id, name, image, muscle_group):
    """Обновить упражнение"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Если передано новое изображение, обновляем его
            if image:
                cursor.execute('''
                    UPDATE exercises 
                    SET name = ?, image = ?, muscle_group = ?
                    WHERE id = ?
                ''', (name, image, muscle_group, exercise_id))
            else:
                cursor.execute('''
                    UPDATE exercises 
                    SET name = ?, muscle_group = ?
                    WHERE id = ?
                ''', (name, muscle_group, exercise_id))
            
            return True
    except Exception as e:
        print(f"Ошибка при обновлении упражнения: {e}")
        return False
    
def delete_exercise(exercise_id):
    """Удалить упражнение"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
            return True
    except Exception as e:
        print(f"Ошибка при удалении упражнения: {e}")
        return False

def get_muscle_groups():
    """Получить все группы мышц"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT muscle_group 
                FROM exercises 
                WHERE muscle_group IS NOT NULL
                ORDER BY muscle_group
            ''')
            return [row['muscle_group'] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Ошибка при получении групп мышц: {e}")
        return []
    """Получить все группы мышц"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT muscle_group 
            FROM exercises 
            WHERE muscle_group IS NOT NULL
            ORDER BY muscle_group
        ''')
        return [row['muscle_group'] for row in cursor.fetchall()]

# ================ ТРЕНИРОВКИ ================
def init_workouts_table():
    """Создать таблицы для тренировок"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица тренировок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workout_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Таблица упражнений в тренировке
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workout_exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id INTEGER NOT NULL,
                    exercise_id INTEGER NOT NULL,
                    sets INTEGER,
                    reps INTEGER,
                    weight REAL,
                    order_num INTEGER,
                    notes TEXT,
                    FOREIGN KEY (workout_id) REFERENCES workout_sessions (id) ON DELETE CASCADE,
                    FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
                )
            ''')
            print("Таблицы тренировок инициализированы")
    except Exception as e:
        print(f"Ошибка при создании таблиц тренировок: {e}")

# Получить все тренировки пользователя
def get_user_workout_sessions(user_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ws.*, 
                       COUNT(we.id) as exercises_count 
                FROM workout_sessions ws
                LEFT JOIN workout_exercises we ON ws.id = we.workout_id
                WHERE ws.user_id = ?
                GROUP BY ws.id
                ORDER BY ws.date DESC
            ''', (user_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при получении тренировок: {e}")
        return []

# Получить конкретную тренировку
def get_workout_session(workout_id, user_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM workout_sessions 
                WHERE id = ? AND user_id = ?
            ''', (workout_id, user_id))
            return cursor.fetchone()
    except Exception as e:
        print(f"Ошибка при получении тренировки: {e}")
        return None

# Получить упражнения тренировки
def get_workout_exercises(workout_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT we.*, e.name, e.image, e.muscle_group
                FROM workout_exercises we
                JOIN exercises e ON we.exercise_id = e.id
                WHERE we.workout_id = ?
                ORDER BY we.order_num
            ''', (workout_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при получении упражнений тренировки: {e}")
        return []

# Создать тренировку
def create_workout_session(user_id, name, date, notes=""):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO workout_sessions (user_id, name, date, notes)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, date, notes))
            return cursor.lastrowid
    except Exception as e:
        print(f"Ошибка при создании тренировки: {e}")
        return None

# Добавить упражнение в тренировку
def add_exercise_to_workout(workout_id, exercise_id, sets, reps, weight, order_num, notes=""):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO workout_exercises 
                (workout_id, exercise_id, sets, reps, weight, order_num, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (workout_id, exercise_id, sets, reps, weight, order_num, notes))
            return True
    except Exception as e:
        print(f"Ошибка при добавлении упражнения в тренировку: {e}")
        return False

# Обновить упражнение в тренировке
def update_workout_exercise(exercise_id, sets, reps, weight, notes):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE workout_exercises 
                SET sets = ?, reps = ?, weight = ?, notes = ?
                WHERE id = ?
            ''', (sets, reps, weight, notes, exercise_id))
            return True
    except Exception as e:
        print(f"Ошибка при обновлении упражнения: {e}")
        return False

# Удалить упражнение из тренировки
def delete_workout_exercise(exercise_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM workout_exercises WHERE id = ?', (exercise_id,))
            return True
    except Exception as e:
        print(f"Ошибка при удалении упражнения: {e}")
        return False

# Удалить тренировку
def delete_workout_session(workout_id, user_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM workout_sessions WHERE id = ? AND user_id = ?', 
                         (workout_id, user_id))
            return True
    except Exception as e:
        print(f"Ошибка при удалении тренировки: {e}")
        return False

# Обновить тренировку
def update_workout_session(workout_id, user_id, name, date, notes):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE workout_sessions 
                SET name = ?, date = ?, notes = ?
                WHERE id = ? AND user_id = ?
            ''', (name, date, notes, workout_id, user_id))
            return True
    except Exception as e:
        print(f"Ошибка при обновлении тренировки: {e}")
        return False     

   
 # ================ СТАТИСТИКА ================
def init_stats_table():
    """Создать таблицу для статистики тренировок"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица завершённых тренировок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completed_workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    workout_id INTEGER NOT NULL,
                    workout_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    duration INTEGER NOT NULL,  -- в секундах
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (workout_id) REFERENCES workout_sessions (id) ON DELETE CASCADE
                )
            ''')
            
            # Таблица выполненных упражнений с 1ПМ
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completed_exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    exercise_id INTEGER NOT NULL,
                    exercise_name TEXT NOT NULL,
                    workout_date TEXT NOT NULL,
                    one_rm REAL NOT NULL,  -- 1ПМ
                    weight REAL NOT NULL,
                    reps INTEGER NOT NULL,
                    sets INTEGER NOT NULL,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
                )
            ''')
            
            print("Таблицы статистики инициализированы")
    except Exception as e:
        print(f"Ошибка при создании таблиц статистики: {e}")

# Сохранить завершённую тренировку
def save_completed_workout(user_id, workout_id, workout_name, duration, exercises_data):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Сохраняем тренировку
            cursor.execute('''
                INSERT INTO completed_workouts (user_id, workout_id, workout_name, date, duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, workout_id, workout_name, today, duration))
            
            # Сохраняем каждое упражнение с расчётом 1ПМ
            for ex in exercises_data:
                # Расчёт 1ПМ по формуле Бжицки: вес * (1 + повторения/30)
                one_rm = float(ex['weight']) * (1 + int(ex['reps']) / 30)
                
                cursor.execute('''
                    INSERT INTO completed_exercises 
                    (user_id, exercise_id, exercise_name, workout_date, one_rm, weight, reps, sets)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, 
                    ex['exercise_id'], 
                    ex['exercise_name'], 
                    today, 
                    round(one_rm, 1),
                    ex['weight'],
                    ex['reps'],
                    ex['sets']
                ))
            
            return True
    except Exception as e:
        print(f"Ошибка при сохранении тренировки: {e}")
        return False

# Получить статистику пользователя
def get_user_stats(user_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Количество завершённых тренировок
            cursor.execute('''
                SELECT COUNT(*) as count FROM completed_workouts WHERE user_id = ?
            ''', (user_id,))
            workouts_count = cursor.fetchone()['count']
            
            # Общее время тренировок
            cursor.execute('''
                SELECT SUM(duration) as total FROM completed_workouts WHERE user_id = ?
            ''', (user_id,))
            total_duration = cursor.fetchone()['total'] or 0
            
            # Список упражнений, которые выполнял пользователь
            cursor.execute('''
                SELECT DISTINCT exercise_id, exercise_name 
                FROM completed_exercises 
                WHERE user_id = ?
                ORDER BY exercise_name
            ''', (user_id,))
            exercises = cursor.fetchall()
            
            return {
                'workouts_count': workouts_count,
                'total_duration': total_duration,
                'exercises': exercises
            }
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        return {
            'workouts_count': 0,
            'total_duration': 0,
            'exercises': []
        }

# Получить данные для графика упражнения
def get_exercise_progress(user_id, exercise_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT workout_date, one_rm, weight, reps
                FROM completed_exercises 
                WHERE user_id = ? AND exercise_id = ?
                ORDER BY completed_at
            ''', (user_id, exercise_id))
            
            return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при получении прогресса: {e}")
        return []  
    
def get_admin_stats():
    """Получить общую статистику для админ-панели"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Общее количество пользователей
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            # Количество админов
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 1')
            total_admins = cursor.fetchone()['count']
            
            # Общее количество тренировок
            cursor.execute('SELECT COUNT(*) as count FROM workout_sessions')
            total_workouts = cursor.fetchone()['count']
            
            # Общее количество упражнений в библиотеке
            cursor.execute('SELECT COUNT(*) as count FROM exercises')
            total_exercises = cursor.fetchone()['count']
            
            return {
                'total_users': total_users,
                'total_admins': total_admins,
                'total_workouts': total_workouts,
                'total_exercises': total_exercises
            }
    except Exception as e:
        print(f"Ошибка при получении админ-статистики: {e}")
        return {
            'total_users': 0,
            'total_admins': 0,
            'total_workouts': 0,
            'total_exercises': 0
        }