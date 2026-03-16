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
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Таблица пользователей (с full_name)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
        
        print("База данных инициализирована")
        
        # Создаем тестового пользователя, если нет админа
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (username, password, full_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin123', 'Администратор', 1))
            
            cursor.execute('''
                INSERT INTO users (username, password, full_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('user1', 'user123', 'Тестовый пользователь', 0))
            print("Созданы тестовые пользователи")
#region Функции для работы с пользователями
def create_user(username, password, full_name):
    """Создать нового пользователя с ФИО"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, full_name)
                VALUES (?, ?, ?)
            ''', (username, password, full_name))
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
        cursor.execute('SELECT id, username, full_name, is_admin, created_at FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()
#endregion

#region АДМИН-ФУНКЦИИ
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

#endregion

#region Функции для работы с тренировками (обычные пользователи)
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
    """Получить всех пользователей с паролями и ФИО (для админа)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                id, 
                username, 
                full_name,
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
#endregion

#region ================ БИБЛИОТЕКА УПРАЖНЕНИЙ ================

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
                    ('Жим штанги лежа', None, 'Грудные')
                   
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
            exercise = cursor.fetchone()
            if exercise:
                # Преобразуем в dict для удобства
                result = dict(exercise)
                # Проверяем путь к картинке
                if result.get('image'):
                    # Убеждаемся, что путь начинается с 'uploads/'
                    if not result['image'].startswith('uploads/'):
                        result['image'] = f"uploads/{result['image']}"
                return result
            return None
    except Exception as e:
        print(f"Ошибка при получении упражнения: {e}")
        return None

def add_exercise(name, image, muscle_group, created_by):
    """Добавить новое упражнение"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже упражнение с таким названием
            cursor.execute('SELECT id FROM exercises WHERE name = ? COLLATE NOCASE', (name,))
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
#endregion

#region ================ ТРЕНИРОВКИ ================
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
                SELECT 
                    we.id,  -- это ID записи в workout_exercises
                    we.exercise_id,  -- а это ID упражнения из библиотеки
                    we.sets,
                    we.reps,
                    we.weight,
                    we.notes,
                    we.order_num,
                    e.name,
                    e.image,
                    e.muscle_group
                FROM workout_exercises we
                JOIN exercises e ON we.exercise_id = e.id
                WHERE we.workout_id = ?
                ORDER BY we.order_num
            ''', (workout_id,))
            
            results = []
            for row in cursor.fetchall():
                # Преобразуем в словарь, но добавляем оба поля
                result = dict(row)
                # Явно добавляем exercise_id из библиотеки
                result['exercise_lib_id'] = row['exercise_id']
                results.append(result)
            
            return results
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
            
            # Проверяем, что упражнение существует в библиотеке
            cursor.execute('SELECT id FROM exercises WHERE id = ?', (exercise_id,))
            if not cursor.fetchone():
                print(f"Ошибка: упражнение с ID {exercise_id} не существует в библиотеке")
                return False
            
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
            
            # Сначала удаляем все подходы этой тренировки из статистики
            cursor.execute('''
                DELETE FROM completed_sets 
                WHERE workout_id = ? AND user_id = ?
            ''', (workout_id, user_id))
            
            # Затем удаляем запись о завершённой тренировке
            cursor.execute('''
                DELETE FROM completed_workouts 
                WHERE workout_id = ? AND user_id = ?
            ''', (workout_id, user_id))
            
            # Затем удаляем все упражнения из тренировки
            cursor.execute('''
                DELETE FROM workout_exercises 
                WHERE workout_id = ?
            ''', (workout_id,))
            
            # И наконец удаляем саму тренировку
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

#endregion   

#region ================ СТАТИСТИКА ================

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
            
            # Таблица выполненных подходов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completed_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    workout_id INTEGER NOT NULL,
                    exercise_id INTEGER NOT NULL,
                    exercise_name TEXT NOT NULL,
                    workout_date TEXT NOT NULL,
                    weight REAL NOT NULL,
                    reps INTEGER NOT NULL,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (workout_id) REFERENCES workout_sessions (id) ON DELETE CASCADE,
                    FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
                )
            ''')
            
            print("Таблицы статистики инициализированы")
    except Exception as e:
        print(f"Ошибка при создании таблиц статистики: {e}")


def save_completed_workout(user_id, workout_id, workout_name, duration, sets_data):
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
            
            # Сохраняем каждый выполненный подход
            for set_data in sets_data:
                # Проверяем, что упражнение существует в библиотеке
                cursor.execute('SELECT id FROM exercises WHERE id = ?', (set_data['exercise_id'],))
                if cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO completed_sets 
                        (user_id, workout_id, exercise_id, exercise_name, workout_date, weight, reps)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        workout_id,
                        set_data['exercise_id'],
                        set_data['exercise_name'],
                        today,
                        set_data['weight'],
                        set_data['reps']
                    ))
                else:
                    print(f"Предупреждение: упражнение с ID {set_data['exercise_id']} не найдено, пропускаем")
            
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
                SELECT COUNT(DISTINCT workout_id) as count 
                FROM completed_workouts 
                WHERE user_id = ?
            ''', (user_id,))
            workouts_count = cursor.fetchone()['count']
            
            # Общее время тренировок (в минутах)
            cursor.execute('''
                SELECT SUM(duration) as total 
                FROM completed_workouts 
                WHERE user_id = ?
            ''', (user_id,))
            total_duration = cursor.fetchone()['total'] or 0
            total_minutes = total_duration // 60
            
            # Упражнения - группируем по ID (теперь они должны быть одинаковыми)
            cursor.execute('''
                SELECT exercise_id, exercise_name 
                FROM completed_sets 
                WHERE user_id = ?
                GROUP BY exercise_id
                ORDER BY exercise_name
            ''', (user_id,))
            exercises = cursor.fetchall()
            
            return {
                'workouts_count': workouts_count,
                'total_duration': total_minutes,
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
            
            # Получаем все подходы этого упражнения
            cursor.execute('''
                SELECT workout_date, weight, reps
                FROM completed_sets 
                WHERE user_id = ? AND exercise_id = ?
                ORDER BY completed_at
            ''', (user_id, exercise_id))
            
            results = []
            for row in cursor.fetchall():
                # Расчёт 1ПМ: если 1 повторение, то 1ПМ = вес
                if row['reps'] == 1:
                    one_rm = row['weight']
                else:
                    # Формула Эйпли для нескольких повторений
                    one_rm = row['weight'] * (1 + row['reps'] / 30)
                
                results.append({
                    'workout_date': row['workout_date'],
                    'weight': row['weight'],
                    'reps': row['reps'],
                    'one_rm': round(one_rm, 1)
                })
            
            return results
    except Exception as e:
        print(f"Ошибка при получении прогресса: {e}")
        return []

# Получить последние тренировки
def get_recent_workouts(user_id, limit=10):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM completed_workouts 
                WHERE user_id = ? 
                ORDER BY completed_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при получении последних тренировок: {e}")
        return []   

def get_admin_stats():
    """Получить расширенную статистику для админ-панели"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Общее количество пользователей
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            # Количество админов
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 1')
            total_admins = cursor.fetchone()['count']
            
            # Количество ЗАВЕРШЁННЫХ тренировок (исправлено!)
            cursor.execute('SELECT COUNT(*) as count FROM completed_workouts')
            total_workouts = cursor.fetchone()['count']
            
            # Общее количество упражнений в библиотеке
            cursor.execute('SELECT COUNT(*) as count FROM exercises')
            total_exercises = cursor.fetchone()['count']
            
            # Общее количество часов тренировок
            cursor.execute('SELECT SUM(duration) as total FROM completed_workouts')
            total_seconds = cursor.fetchone()['total'] or 0
            total_hours = round(total_seconds / 3600, 1)
            
            # Активные сегодня
            from datetime import datetime, timedelta
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as count 
                FROM completed_workouts 
                WHERE date = ? OR date = ?
            ''', (today, yesterday))
            active_today = cursor.fetchone()['count']
            
            # Процент роста пользователей за месяц
            month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                SELECT COUNT(*) as count FROM users 
                WHERE created_at >= ?
            ''', (month_ago,))
            new_users_month = cursor.fetchone()['count']
            user_growth = round((new_users_month / max(total_users, 1)) * 100) if total_users > 0 else 0
            
            # Процент роста тренировок за неделю
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) as count FROM completed_workouts 
                WHERE date >= ?
            ''', (week_ago,))
            new_workouts_week = cursor.fetchone()['count']
            workout_growth = round((new_workouts_week / max(total_workouts, 1)) * 100) if total_workouts > 0 else 0
            
            # Новые упражнения
            cursor.execute('''
                SELECT COUNT(*) as count FROM exercises 
                WHERE created_at >= ?
            ''', (week_ago,))
            new_exercises = cursor.fetchone()['count']
            
            return {
                'total_users': total_users,
                'total_admins': total_admins,
                'total_workouts': total_workouts,  # Теперь это завершённые тренировки
                'total_exercises': total_exercises,
                'total_hours': total_hours,
                'active_today': active_today,
                'user_growth': user_growth,
                'workout_growth': workout_growth,
                'new_exercises': new_exercises,
                'new_workouts_week': new_workouts_week
            }
    except Exception as e:
        print(f"Ошибка при получении админ-статистики: {e}")
        return {
            'total_users': 0,
            'total_admins': 0,
            'total_workouts': 0,
            'total_exercises': 0,
            'total_hours': 0,
            'active_today': 0,
            'user_growth': 0,
            'workout_growth': 0,
            'new_exercises': 0,
            'new_workouts_week': 0
        }

def get_users_chart_data():
    """Получить данные для графика новых пользователей за последние 7 дней"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            from datetime import datetime, timedelta
            dates = []
            users_data = []
            
            for i in range(6, -1, -1):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                next_date = (datetime.now() - timedelta(days=i-1)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM users 
                    WHERE date(created_at) >= ? AND date(created_at) < ?
                ''', (date, next_date))
                
                count = cursor.fetchone()['count']
                dates.append(date[-5:])  # Берем только день-месяц
                users_data.append(count)
            
            return {
                'labels': dates,
                'data': users_data
            }
    except Exception as e:
        print(f"Ошибка при получении данных графика пользователей: {e}")
        return {'labels': [], 'data': []}

def get_workouts_chart_data():
    """Получить данные для графика тренировок за последние 7 дней"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            from datetime import datetime, timedelta
            dates = []
            workouts_data = []
            
            for i in range(6, -1, -1):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM completed_workouts 
                    WHERE date = ?
                ''', (date,))
                
                count = cursor.fetchone()['count']
                dates.append(date[-5:])  # Берем только день-месяц
                workouts_data.append(count)
            
            return {
                'labels': dates,
                'data': workouts_data
            }
    except Exception as e:
        print(f"Ошибка при получении данных графика тренировок: {e}")
        return {'labels': [], 'data': []}
    """Получить данные для графика тренировок за последние 7 дней"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            from datetime import datetime, timedelta
            dates = []
            workouts_data = []
            
            for i in range(6, -1, -1):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM completed_workouts 
                    WHERE date = ?
                ''', (date,))
                
                count = cursor.fetchone()['count']
                dates.append(date[-5:])  # Берем только день-месяц
                workouts_data.append(count)
            
            return {
                'labels': dates,
                'data': workouts_data
            }
    except Exception as e:
        print(f"Ошибка при получении данных графика тренировок: {e}")
        return {'labels': [], 'data': []}
    
#endregion

#region ================ НАСТРОЙКИ ПАСХАЛКИ ================

def init_easter_egg_table():
    """Создать таблицу для настроек пасхалки"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS easter_egg_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_path TEXT,
                    media_type TEXT DEFAULT 'image',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Добавляем запись по умолчанию, если её нет
            cursor.execute('SELECT COUNT(*) as count FROM easter_egg_settings')
            if cursor.fetchone()['count'] == 0:
                cursor.execute('''
                    INSERT INTO easter_egg_settings (media_path, media_type)
                    VALUES (?, ?)
                ''', ('uploads/easter_default.jpg', 'image'))
            
            conn.commit()
            print("Таблица пасхалки инициализирована")
    except Exception as e:
        print(f"Ошибка при создании таблицы пасхалки: {e}")

def get_easter_egg_media():
    """Получить текущий медиафайл пасхалки"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT media_path, media_type, enabled FROM easter_egg_settings ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if row:
                return {'path': row['media_path'], 'type': row['media_type'], 'enabled': row['enabled']}
            return {'path': 'uploads/easter_default.jpg', 'type': 'image', 'enabled': True}
    except Exception as e:
        print(f"Ошибка при получении медиа пасхалки: {e}")
        return {'path': 'uploads/easter_default.jpg', 'type': 'image', 'enabled': True}

def update_easter_egg_media(media_path, media_type):
    """Обновить медиафайл пасхалки"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Очищаем старые записи
            cursor.execute('DELETE FROM easter_egg_settings')
            # Добавляем новую
            cursor.execute('''
                INSERT INTO easter_egg_settings (media_path, media_type)
                VALUES (?, ?)
            ''', (media_path, media_type))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при обновлении медиа пасхалки: {e}")
        return False

def get_easter_egg_settings():
    """Получить все настройки пасхалки"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, setting_value FROM easter_egg_settings')
            settings = cursor.fetchall()
            return {row['setting_key']: row['setting_value'] for row in settings}
    except Exception as e:
        print(f"Ошибка при получении настроек пасхалки: {e}")
        return {}

def update_easter_egg_setting(key, value):
    """Обновить настройку пасхалки"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE easter_egg_settings 
                SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE setting_key = ?
            ''', (value, key))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при обновлении настройки пасхалки: {e}")
        return False

def get_easter_egg_enabled():
    """Проверить, включена ли пасхалка"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT enabled FROM easter_egg_settings ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            return row['enabled'] if row else True
    except:
        return True

def set_easter_egg_enabled(enabled):
    """Включить/выключить пасхалку"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE easter_egg_settings SET enabled = ?', (1 if enabled else 0,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при изменении статуса пасхалки: {e}")
        return False
#endregion


#region================ ПИТАНИЕ ================

def init_nutrition_tables():
    """Создать таблицы для питания"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица для отслеживания веса
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weight_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    weight REAL NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    UNIQUE(user_id, date)
                )
            ''')
            
            print("Таблицы питания инициализированы")
    except Exception as e:
        print(f"Ошибка при создании таблиц питания: {e}")


def init_bju_settings_table():
    """Создать таблицу настроек БЖУ"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bju_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    age INTEGER DEFAULT 30,
                    height INTEGER DEFAULT 175,
                    gender TEXT DEFAULT 'female',
                    activity_level REAL DEFAULT 1.55,
                    goal TEXT DEFAULT 'maintain',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Добавляем настройки для существующих пользователей
            cursor.execute('SELECT id FROM users')
            users = cursor.fetchall()
            for user in users:
                cursor.execute('''
                    INSERT OR IGNORE INTO bju_settings (user_id)
                    VALUES (?)
                ''', (user['id'],))
            
            conn.commit()
            print("Таблица настроек БЖУ инициализирована")
    except Exception as e:
        print(f"Ошибка при создании таблицы настроек БЖУ: {e}")

# Добавить запись веса
def add_weight_entry(user_id, date, weight, notes=""):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже запись на эту дату
            cursor.execute('SELECT id FROM weight_tracking WHERE user_id = ? AND date = ?', 
                         (user_id, date))
            existing = cursor.fetchone()
            
            if existing:
                # Если есть - обновляем
                cursor.execute('''
                    UPDATE weight_tracking 
                    SET weight = ?, notes = ?
                    WHERE user_id = ? AND date = ?
                ''', (weight, notes, user_id, date))
                print(f"Обновлена запись за {date}")
            else:
                # Если нет - добавляем новую
                cursor.execute('''
                    INSERT INTO weight_tracking (user_id, date, weight, notes)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, date, weight, notes))
                print(f"Добавлена новая запись за {date}")
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при добавлении веса: {e}")
        return False
# Получить все записи веса пользователя
def get_weight_entries(user_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM weight_tracking 
                WHERE user_id = ? 
                ORDER BY date DESC
            ''', (user_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при получении записей веса: {e}")
        return []

# Получить статистику веса
def get_weight_stats(user_id):

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Последняя запись
            cursor.execute('''
                SELECT weight, date FROM weight_tracking 
                WHERE user_id = ? 
                ORDER BY date DESC LIMIT 1
            ''', (user_id,))
            last = cursor.fetchone()
            
            # Минимальный вес
            cursor.execute('''
                SELECT MIN(weight) as min_weight, date FROM weight_tracking 
                WHERE user_id = ?
            ''', (user_id,))
            min_data = cursor.fetchone()
            
            # Максимальный вес
            cursor.execute('''
                SELECT MAX(weight) as max_weight, date FROM weight_tracking 
                WHERE user_id = ?
            ''', (user_id,))
            max_data = cursor.fetchone()
            
            # Изменение за последние 30 дней
            from datetime import datetime, timedelta
            month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT weight FROM weight_tracking 
                WHERE user_id = ? AND date >= ?
                ORDER BY date ASC LIMIT 1
            ''', (user_id, month_ago))
            first_month = cursor.fetchone()
            
            change_30d = 0
            if first_month and last:
                change_30d = round(last['weight'] - first_month['weight'], 1)
            
            return {
                'last_weight': last['weight'] if last else None,
                'last_date': last['date'] if last else None,
                'min_weight': min_data['min_weight'] if min_data['min_weight'] else None,
                'min_date': min_data['date'] if min_data['date'] else None,
                'max_weight': max_data['max_weight'] if max_data['max_weight'] else None,
                'max_date': max_data['date'] if max_data['date'] else None,
                'change_30d': change_30d,
                'total_entries': len(get_weight_entries(user_id))
            }
    except Exception as e:
        print(f"Ошибка при получении статистики веса: {e}")
        return {}
    
def get_user_bju_settings(user_id):
    """Получить настройки БЖУ пользователя с расшифровкой"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                bs.*,
                g.display_name as gender_display,
                g.icon as gender_icon,
                a.display_name as activity_display,
                a.icon as activity_icon,
                a.value as activity_value,
                go.display_name as goal_display,
                go.icon as goal_icon
            FROM bju_settings bs
            LEFT JOIN gender_types g ON bs.gender_id = g.id
            LEFT JOIN activity_levels a ON bs.activity_id = a.id
            LEFT JOIN goal_types go ON bs.goal_id = go.id
            WHERE bs.user_id = ?
        ''', (user_id,))
        return cursor.fetchone()
    
#endregion


#region================О НАС ================
def init_about_table():
    """Создать таблицу для контента страницы О нас и заполнить базовыми данными"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS about_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_key TEXT UNIQUE NOT NULL,
                    section_title TEXT,
                    section_content TEXT,
                    icon TEXT,
                    sort_order INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Проверяем, есть ли уже записи
            cursor.execute('SELECT COUNT(*) as count FROM about_content')
            count = cursor.fetchone()['count']
            
            if count == 0:
                print("Добавление базового контента для страницы О нас...")
                
                # Базовая миссия
                cursor.execute('''
                    INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('mission', 'Наша миссия', 
                      'Мы создали этот трекер тренировок, чтобы помочь вам достигать своих фитнес-целей, отслеживать прогресс и оставаться мотивированными. Наша платформа объединяет удобный интерфейс, мощную аналитику и гибкие настройки под любые задачи.',
                      'fa-rocket', 1))
                
                # Команда - разработчик
                cursor.execute('''
                    INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('team_developer', 'Громов Александр Сергеевич', 'Разработчик', 'fa-user-tie', 2))
                
                # Команда - дизайнер
                cursor.execute('''
                    INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('team_designer', 'Виртуальный помощник', 'Дизайнер', 'fa-paint-brush', 3))
                
                # Команда - куратор
                cursor.execute('''
                    INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('team_curator', 'Родионов Виктор Валерьевич', 'Куратор', 'fa-crown', 4))
                
                print("✅ Базовый контент для страницы О нас добавлен")
            else:
                print("⏩ Контент для страницы О нас уже существует")
            
            conn.commit()
            print("✅ Таблица контента О нас инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при создании таблицы about_content: {e}")

def get_about_content():
    """Получить весь контент для страницы О нас"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM about_content ORDER BY sort_order')
            return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка при получении контента О нас: {e}")
        return []

def update_about_content(content_id, section_title, section_content, icon, sort_order):
    """Обновить контент страницы О нас"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE about_content 
                SET section_title = ?, section_content = ?, icon = ?, sort_order = ?
                WHERE id = ?
            ''', (section_title, section_content, icon, sort_order, content_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при обновлении контента О нас: {e}")
        return False

def delete_about_content(content_id):
    """Удалить контент страницы О нас"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM about_content WHERE id = ?', (content_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при удалении контента О нас: {e}")
        return False

def add_about_content(section_key, section_title, section_content, icon, sort_order):
    """Добавить новый контент на страницу О нас"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', (section_key, section_title, section_content, icon, sort_order))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при добавлении контента О нас: {e}")
        return False
    
#endregion


def init_lookup_tables():
    """Создать справочные таблицы для пола, активности и цели"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица для пола
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gender_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    icon TEXT,
                    sort_order INTEGER DEFAULT 0
                )
            ''')
            
            # Таблица для уровней активности
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    icon TEXT,
                    description TEXT,
                    sort_order INTEGER DEFAULT 0
                )
            ''')
            
            # Таблица для целей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goal_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    icon TEXT,
                    description TEXT,
                    sort_order INTEGER DEFAULT 0
                )
            ''')
            
            # Заполняем таблицы начальными данными
            # Пол
            genders = [
                ('male', '👨 Мужской', 'fa-mars', 1),
                ('female', '👩 Женский', 'fa-venus', 2)
            ]
            for name, display_name, icon, sort in genders:
                cursor.execute('''
                    INSERT OR IGNORE INTO gender_types (name, display_name, icon, sort_order)
                    VALUES (?, ?, ?, ?)
                ''', (name, display_name, icon, sort))
            
            # Активность
            activities = [
                ('minimal', '🪑 Минимальная', 1.2, 'fa-chair', 'Сидячая работа, нет тренировок', 1),
                ('light', '🚶 Лёгкая', 1.375, 'fa-walking', '1-3 тренировки в неделю', 2),
                ('moderate', '🏃 Средняя', 1.55, 'fa-running', '3-5 тренировок в неделю', 3),
                ('high', '💪 Высокая', 1.725, 'fa-dumbbell', '6-7 тренировок в неделю', 4),
                ('extreme', '🏆 Очень высокая', 1.9, 'fa-trophy', 'Спортсмены, физическая работа', 5)
            ]
            for name, display_name, value, icon, desc, sort in activities:
                cursor.execute('''
                    INSERT OR IGNORE INTO activity_levels (name, display_name, value, icon, description, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, display_name, value, icon, desc, sort))
            
            # Цели
            goals = [
                ('maintain', '🏋️ Поддержание', 'fa-balance-scale', 'Сохранить текущий вес', 1),
                ('lose', '📉 Похудение', 'fa-arrow-down', 'Снизить вес', 2),
                ('gain', '📈 Набор массы', 'fa-arrow-up', 'Увеличить мышечную массу', 3)
            ]
            for name, display_name, icon, desc, sort in goals:
                cursor.execute('''
                    INSERT OR IGNORE INTO goal_types (name, display_name, icon, description, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, display_name, icon, desc, sort))
            
            conn.commit()
            print("Справочные таблицы инициализированы")
    except Exception as e:
        print(f"Ошибка при создании справочных таблиц: {e}")


# Функции для получения данных из справочников
def get_gender_types():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM gender_types ORDER BY sort_order')
        return cursor.fetchall()

def get_activity_levels():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM activity_levels ORDER BY sort_order')
        return cursor.fetchall()

def get_goal_types():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM goal_types ORDER BY sort_order')
        return cursor.fetchall()
    

def migrate_database():
    """Обновляет структуру базы данных до актуальной версии"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("Проверка структуры базы данных...")
        
        # ========== ТАБЛИЦА USERS ==========
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'full_name' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
            print("✅ Добавлена колонка full_name в users")
            cursor.execute("UPDATE users SET full_name = username WHERE full_name IS NULL")
        
        # ========== ТАБЛИЦА BJU_SETTINGS ==========
        try:
            cursor.execute("PRAGMA table_info(bju_settings)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'gender_id' not in columns:
                cursor.execute("ALTER TABLE bju_settings ADD COLUMN gender_id INTEGER DEFAULT 1")
                print("✅ Добавлена колонка gender_id")
                
            if 'activity_id' not in columns:
                cursor.execute("ALTER TABLE bju_settings ADD COLUMN activity_id INTEGER DEFAULT 3")
                print("✅ Добавлена колонка activity_id")
                
            if 'goal_id' not in columns:
                cursor.execute("ALTER TABLE bju_settings ADD COLUMN goal_id INTEGER DEFAULT 1")
                print("✅ Добавлена колонка goal_id")
            
            # Обновляем значения
            cursor.execute('''
                UPDATE bju_settings 
                SET gender_id = CASE gender 
                    WHEN 'male' THEN 1 
                    WHEN 'female' THEN 2 
                    ELSE 1 
                END
                WHERE gender_id IS NULL
            ''')
            
            cursor.execute('''
                UPDATE bju_settings 
                SET activity_id = CASE 
                    WHEN activity_level = 1.2 THEN 1
                    WHEN activity_level = 1.375 THEN 2
                    WHEN activity_level = 1.55 THEN 3
                    WHEN activity_level = 1.725 THEN 4
                    WHEN activity_level = 1.9 THEN 5
                    ELSE 3
                END
                WHERE activity_id IS NULL
            ''')
            
            cursor.execute('''
                UPDATE bju_settings 
                SET goal_id = CASE goal 
                    WHEN 'maintain' THEN 1 
                    WHEN 'lose' THEN 2 
                    WHEN 'gain' THEN 3 
                    ELSE 1 
                END
                WHERE goal_id IS NULL
            ''')
            print("✅ Обновлены значения в bju_settings")
        except Exception as e:
            print(f"⚠️ Таблица bju_settings еще не создана: {e}")
        
        # ========== ТАБЛИЦЫ СПРАВОЧНИКОВ ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gender_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                icon TEXT,
                sort_order INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                value REAL NOT NULL,
                icon TEXT,
                description TEXT,
                sort_order INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                icon TEXT,
                description TEXT,
                sort_order INTEGER DEFAULT 0
            )
        ''')
        
        # ========== ТАБЛИЦА ABOUT_CONTENT ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS about_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_key TEXT UNIQUE NOT NULL,
                section_title TEXT,
                section_content TEXT,
                icon TEXT,
                sort_order INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Таблица about_content создана")
        
        # Проверяем, есть ли записи
        cursor.execute("SELECT COUNT(*) as count FROM about_content")
        row = cursor.fetchone()
        if row[0] == 0:
            print("Добавление базового контента в about_content...")
            
            cursor.execute('''
                INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', ('mission', 'Наша миссия', 
                  'Мы создали этот трекер тренировок, чтобы помочь вам достигать своих фитнес-целей, отслеживать прогресс и оставаться мотивированными.',
                  'fa-rocket', 1))
            
            cursor.execute('''
                INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', ('team_developer', 'Громов Александр Сергеевич', 'Разработчик', 'fa-user-tie', 2))
            
            cursor.execute('''
                INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', ('team_designer', 'Виртуальный помощник', 'Дизайнер', 'fa-paint-brush', 3))
            
            cursor.execute('''
                INSERT INTO about_content (section_key, section_title, section_content, icon, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', ('team_curator', 'Родионов Виктор Валерьевич', 'Куратор', 'fa-crown', 4))
            
            print("✅ Базовый контент добавлен")
        
        # ========== ЗАПОЛНЯЕМ СПРАВОЧНИКИ ==========
        cursor.execute("SELECT COUNT(*) as count FROM gender_types")
        row = cursor.fetchone()
        if row[0] == 0:
            genders = [
                ('male', '👨 Мужской', 'fa-mars', 1),
                ('female', '👩 Женский', 'fa-venus', 2)
            ]
            for name, display_name, icon, sort in genders:
                cursor.execute('''
                    INSERT INTO gender_types (name, display_name, icon, sort_order)
                    VALUES (?, ?, ?, ?)
                ''', (name, display_name, icon, sort))
            print("✅ Добавлены типы пола")
        
        cursor.execute("SELECT COUNT(*) as count FROM activity_levels")
        row = cursor.fetchone()
        if row[0] == 0:
            activities = [
                ('minimal', '🪑 Минимальная', 1.2, 'fa-chair', 'Сидячая работа, нет тренировок', 1),
                ('light', '🚶 Лёгкая', 1.375, 'fa-walking', '1-3 тренировки в неделю', 2),
                ('moderate', '🏃 Средняя', 1.55, 'fa-running', '3-5 тренировок в неделю', 3),
                ('high', '💪 Высокая', 1.725, 'fa-dumbbell', '6-7 тренировок в неделю', 4),
                ('extreme', '🏆 Очень высокая', 1.9, 'fa-trophy', 'Спортсмены, физическая работа', 5)
            ]
            for name, display_name, value, icon, desc, sort in activities:
                cursor.execute('''
                    INSERT INTO activity_levels (name, display_name, value, icon, description, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, display_name, value, icon, desc, sort))
            print("✅ Добавлены уровни активности")
        
        cursor.execute("SELECT COUNT(*) as count FROM goal_types")
        row = cursor.fetchone()
        if row[0] == 0:
            goals = [
                ('maintain', '🏋️ Поддержание', 'fa-balance-scale', 'Сохранить текущий вес', 1),
                ('lose', '📉 Похудение', 'fa-arrow-down', 'Снизить вес', 2),
                ('gain', '📈 Набор массы', 'fa-arrow-up', 'Увеличить мышечную массу', 3)
            ]
            for name, display_name, icon, desc, sort in goals:
                cursor.execute('''
                    INSERT INTO goal_types (name, display_name, icon, description, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, display_name, icon, desc, sort))
            print("✅ Добавлены цели")
        
        conn.commit()
        conn.close()
        print("✅ Проверка структуры БД завершена")
        
    except Exception as e:
        print(f"⚠️ Ошибка при миграции БД: {e}")     