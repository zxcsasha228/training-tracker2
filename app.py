import os
import sys
import threading
import webbrowser
import time
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
import database
from flask import jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'

# Добавляем фильтр float для Jinja2
@app.template_filter('float')
def float_filter(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

# Определяем базовую папку где лежит exe-файл
if getattr(sys, 'frozen', False):
    # Запущены из exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Запущены из скрипта
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"Базовая папка: {BASE_DIR}")

# 💡 ВАЖНО: Указываем Flask где искать статические файлы
app.static_folder = os.path.join(BASE_DIR, 'static')
app.static_url_path = '/static'

print(f"Static folder: {app.static_folder}")
print(f"Static URL path: {app.static_url_path}")

# Создаём нужные папки
# Явно указываем папки для статических файлов
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
# Создаём папки если их нет
try:
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)
        print(f"Создана папка: {STATIC_FOLDER}")
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f"Создана папка для загрузок: {UPLOAD_FOLDER}")
except Exception as e:
    print(f"Ошибка при создании папок: {e}")

# Настраиваем Flask
app.static_folder = STATIC_FOLDER
app.static_url_path = '/static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 💡 Добавляем маршрут для явной раздачи статических файлов (на всякий случай)
@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory(app.static_folder, filename)

# Важно! Явный маршрут для раздачи статических файлов
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

# Маршрут для загруженных файлов
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = database.check_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            
            # Админа отправляем в админку, обычных пользователей на главную
            if user['is_admin']:
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверное имя пользователя или пароль')
    
    return render_template('login.html')

# Страница регистрации (обычные пользователи)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        
        if password != confirm:
            return render_template('register.html', error='Пароли не совпадают')
        
        user_id = database.create_user(username, password, is_admin=0)  # Обычный пользователь
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            session['is_admin'] = 0
            return redirect(url_for('index'))
        else:
            return render_template('register.html', error='Пользователь с таким именем уже существует')
    
    return render_template('register.html')

# Выход из системы
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    stats = database.get_admin_stats()
    users = database.get_all_users_with_passwords()
    users_chart = database.get_users_chart_data()
    workouts_chart = database.get_workouts_chart_data()
    
    return render_template('admin_panel_enhanced.html', 
                         stats=stats, 
                         users=users,
                         users_chart=users_chart,
                         workouts_chart=workouts_chart,
                         is_admin=session.get('is_admin', 0))

# Просмотр данных пользователя (для админа)
@app.route('/admin/user/<int:user_id>')
def admin_user_details(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    user = database.get_user_with_password(user_id)
    if not user:
        return redirect(url_for('admin_panel'))
    
    return render_template('admin_user_details.html', 
                         user=user,
                         is_admin=session.get('is_admin', 0))



@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Получаем тренировки пользователя
    workouts = database.get_user_workout_sessions(session['user_id'])
    
    # Рендерим красивый шаблон для всех
    return render_template('workouts.html', 
                         workouts=workouts, 
                         username=session['username'],
                         is_admin=session.get('is_admin', 0))

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    
    date = request.form['date']
    exercise = request.form['exercise']
    sets = request.form['sets']
    reps = request.form['reps']
    weight = request.form['weight']
    
    database.add_workout(session['user_id'], date, exercise, sets, reps, weight)
    return redirect(url_for('index'))

@app.route('/edit/<int:workout_id>')
def edit(workout_id):
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    
    workout = database.get_workout(workout_id, session['user_id'])
    if not workout:
        return redirect(url_for('index'))
    
    return render_template('edit.html', workout=workout)

@app.route('/update/<int:workout_id>', methods=['POST'])
def update(workout_id):
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    
    date = request.form['date']
    exercise = request.form['exercise']
    sets = request.form['sets']
    reps = request.form['reps']
    weight = request.form['weight']
    
    database.update_workout(workout_id, session['user_id'], date, exercise, sets, reps, weight)
    return redirect(url_for('index'))

@app.route('/delete/<int:workout_id>', methods=['POST'])
def delete(workout_id):
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    
    database.delete_workout(workout_id, session['user_id'])
    return redirect(url_for('index'))

# Переключение прав администратора
@app.route('/admin/toggle_admin/<int:user_id>')
def toggle_admin(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Не даем админу изменить права самого себя
    if user_id == session['user_id']:
        return redirect(url_for('admin_panel'))
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        # Получаем текущие права
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            new_admin_status = 0 if user['is_admin'] else 1
            cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', 
                         (new_admin_status, user_id))
    
    return redirect(url_for('admin_panel'))

# Удаление пользователя (обновленная версия)
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):

    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Не даем админу удалить самого себя
    if user_id == session['user_id']:
        return redirect(url_for('admin_panel'))
    
    database.delete_user_admin(user_id)
    return redirect(url_for('admin_panel'))
   
# Профиль пользователя
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = database.get_user_by_id(session['user_id'])
    stats = database.get_user_stats(session['user_id'])
    
    return render_template('profile.html', 
                         user=user, 
                         stats=stats,
                         is_admin=session.get('is_admin', 0))


#region---------------------БИБЛИОТЕКА УПРАЖНЕНИЙ---------------------
# ================ БИБЛИОТЕКА УПРАЖНЕНИЙ ================

# Страница библиотеки упражнений (доступна всем)
@app.route('/exercises')
def exercises_library():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        exercises = database.get_all_exercises()
        muscle_groups = database.get_muscle_groups()
        
        # ВРЕМЕННО: выводим в консоль для проверки
        for ex in exercises:
            print(f"Упражнение {ex['id']}: {ex['name']} - image: {ex['image']}")
            
    except Exception as e:
        print(f"Ошибка при загрузке упражнений: {e}")
        exercises = []
        muscle_groups = []
    
    return render_template('exercises_library.html', 
                         exercises=exercises, 
                         muscle_groups=muscle_groups,
                         is_admin=session.get('is_admin', 0))  # ДОБАВЬ ЭТО
    
    return render_template('exercises_library.html', 
                         exercises=exercises, 
                         muscle_groups=muscle_groups,
                         is_admin=session.get('is_admin', 0))

# Добавление упражнения (только админ)
@app.route('/exercises/add', methods=['GET', 'POST'])
def add_exercise():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        muscle_group = request.form.get('muscle_group', '').strip()
        
        if not name or not muscle_group:
            return render_template('add_exercise.html', 
                                 error='Заполните все обязательные поля',
                                 is_admin=session.get('is_admin', 0))
        
        # Обработка загруженного изображения
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Создаём безопасное имя файла
                    filename = secure_filename(file.filename)
                    # Добавляем временную метку для уникальности
                    import time
                    filename = f"{int(time.time())}_{filename}"
                    # Полный путь для сохранения
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    # Сохраняем файл
                    file.save(full_path)
                    print(f"Файл сохранён: {full_path}")
                    
                    # Сохраняем ОТНОСИТЕЛЬНЫЙ путь для базы данных
                    # Важно! Используем прямой путь без url_for
                    image_path = f"uploads/{filename}"
                    print(f"Сохранён путь в БД: {image_path}")
                    
                except Exception as e:
                    print(f"Ошибка при сохранении файла: {e}")
        
        success = database.add_exercise(name, image_path, muscle_group, session['user_id'])
        if success:
            return redirect(url_for('exercises_library'))
        else:
            return render_template('add_exercise.html', 
                                 error='Упражнение с таким названием уже существует',
                                 is_admin=session.get('is_admin', 0))
    
    return render_template('add_exercise.html',
                         is_admin=session.get('is_admin', 0))

# Редактирование упражнения (только админ)
@app.route('/exercises/edit/<int:exercise_id>', methods=['GET', 'POST'])
def edit_exercise(exercise_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    exercise = database.get_exercise(exercise_id)
    if not exercise:
        return redirect(url_for('exercises_library'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        muscle_group = request.form.get('muscle_group', '').strip()
        
        if not name or not muscle_group:
            return render_template('edit_exercise.html', 
                                 exercise=exercise,
                                 error='Заполните все обязательные поля',
                                 is_admin=session.get('is_admin', 0))
        
        # Обработка нового изображения
        image_path = exercise['image']  # оставляем старое по умолчанию
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Создаём безопасное имя файла
                    filename = secure_filename(file.filename)
                    import time
                    filename = f"{int(time.time())}_{filename}"
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(full_path)
                    print(f"Файл сохранён: {full_path}")
                    
                    # Сохраняем относительный путь
                    image_path = f"uploads/{filename}"
                    print(f"Сохранён путь в БД: {image_path}")
                    
                    # Удаляем старое изображение (опционально)
                    if exercise['image']:
                        old_path = os.path.join(BASE_DIR, 'static', exercise['image'])
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                                print(f"Старое изображение удалено: {old_path}")
                            except:
                                pass
                except Exception as e:
                    print(f"Ошибка при сохранении файла: {e}")
        
        database.update_exercise(exercise_id, name, image_path, muscle_group)
        return redirect(url_for('exercises_library'))
    
    return render_template('edit_exercise.html', 
                         exercise=exercise,
                         is_admin=session.get('is_admin', 0))

# Удаление упражнения (только админ)
@app.route('/exercises/delete/<int:exercise_id>', methods=['POST'])
def delete_exercise(exercise_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    database.delete_exercise(exercise_id)
    return redirect(url_for('exercises_library'))
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    database.delete_exercise(exercise_id)
    return redirect(url_for('exercises_library'))

#endregion


#region-----------------------------------ТРЕНИРОВКИ------------------------------------
# ================ ТРЕНИРОВКИ ================

# Главная страница со списком тренировок
@app.route('/my_workouts')
def my_workouts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workouts = database.get_user_workout_sessions(session['user_id'])
    return render_template('workouts.html', 
                         workouts=workouts, 
                         username=session['username'],
                         is_admin=session.get('is_admin', 0))

# Создание новой тренировки
@app.route('/workout/create', methods=['GET', 'POST'])
def create_workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            return render_template('create_workout.html', 
                                 error='Введите название тренировки',
                                 is_admin=session.get('is_admin', 0))
        
        from datetime import date
        today = date.today().isoformat()
        
        workout_id = database.create_workout_session(
            session['user_id'], name, today, ""
        )
        
        if workout_id:
            return redirect(url_for('my_workouts'))
        else:
            return render_template('create_workout.html', 
                                 error='Ошибка при создании тренировки',
                                 is_admin=session.get('is_admin', 0))
    
    return render_template('create_workout.html',
                         is_admin=session.get('is_admin', 0))
# Просмотр тренировки
@app.route('/workout/<int:workout_id>')
def view_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    if not workout:
        return redirect(url_for('my_workouts'))
    
    exercises = database.get_workout_exercises(workout_id)
    all_exercises = database.get_all_exercises()  # для добавления новых
    
    return render_template('view_workout.html', 
                         workout=workout,
                         exercises=exercises,
                         all_exercises=all_exercises,
                         username=session['username'],
                         is_admin=session.get('is_admin', 0))  # ДОБАВЬ ЭТО

# Массовое добавление упражнений в тренировку
@app.route('/workout/<int:workout_id>/add_exercises', methods=['POST'])
def add_workout_exercises(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise_ids = request.form.getlist('exercise_ids[]')
    sets = request.form.get('sets', '3')
    reps = request.form.get('reps', '10')
    weight = request.form.get('weight', '0')
    
    print(f"\n=== ДОБАВЛЕНИЕ УПРАЖНЕНИЙ В ТРЕНИРОВКУ {workout_id} ===")
    print(f"Полученные ID: {exercise_ids}")
    print(f"Параметры: {sets} подходов x {reps} повторений, вес {weight}")
    
    # Получаем следующий порядковый номер
    exercises = database.get_workout_exercises(workout_id)
    order_num = len(exercises) + 1
    
    added_count = 0
    for exercise_id in exercise_ids:
        # Проверяем, что упражнение существует в библиотеке
        exercise = database.get_exercise(exercise_id)
        if exercise:
            print(f"✅ Добавляем упражнение ID {exercise_id}: {exercise['name']}")
            database.add_exercise_to_workout(
                workout_id, exercise_id, sets, reps, weight, order_num, ""
            )
            order_num += 1
            added_count += 1
        else:
            print(f"❌ Упражнение с ID {exercise_id} не найдено в библиотеке!")
    
    print(f"Добавлено упражнений: {added_count}")
    print("="*50)
    return redirect(url_for('view_workout', workout_id=workout_id))


# Массовое удаление упражнений из тренировки
@app.route('/workout/<int:workout_id>/delete_multiple', methods=['POST'])
def delete_multiple_exercises(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise_ids = request.form.getlist('exercise_ids[]')
    
    for exercise_id in exercise_ids:
        database.delete_workout_exercise(exercise_id)
    
    return redirect(url_for('view_workout', workout_id=workout_id))
# Редактировать упражнение в тренировке
@app.route('/workout/exercise/<int:exercise_id>/edit', methods=['POST'])
def edit_workout_exercise(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    sets = request.form.get('sets')
    reps = request.form.get('reps')
    weight = request.form.get('weight')
    notes = request.form.get('notes', '')
    
    database.update_workout_exercise(exercise_id, sets, reps, weight, notes)
    
    # Возвращаемся на страницу тренировки
    workout_id = request.form.get('workout_id')
    return redirect(url_for('view_workout', workout_id=workout_id))

# Удалить упражнение из тренировки
@app.route('/workout/exercise/<int:exercise_id>/delete', methods=['POST'])
def delete_workout_exercise(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout_id = request.form.get('workout_id')
    database.delete_workout_exercise(exercise_id)
    
    return redirect(url_for('view_workout', workout_id=workout_id))

# Редактировать тренировку
@app.route('/workout/<int:workout_id>/edit', methods=['GET', 'POST'])
def edit_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    if not workout:
        return redirect(url_for('my_workouts'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            return render_template('edit_workout.html', 
                                 workout=workout,
                                 error='Введите название тренировки',
                                 is_admin=session.get('is_admin', 0))
        
        database.update_workout_session(
            workout_id, 
            session['user_id'], 
            name, 
            workout['date'],
            workout['notes'] if workout['notes'] else ""
        )
        return redirect(url_for('view_workout', workout_id=workout_id))
    
    return render_template('edit_workout.html', 
                         workout=workout,
                         is_admin=session.get('is_admin', 0))
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    if not workout:
        return redirect(url_for('my_workouts'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            return render_template('edit_workout.html', 
                                 workout=workout,
                                 error='Введите название тренировки')
        
        # Оставляем старую дату и заметки без изменений
        database.update_workout_session(
            workout_id, 
            session['user_id'], 
            name, 
            workout['date'],  # оставляем старую дату
            workout['notes'] if workout['notes'] else ""  # оставляем старые заметки
        )
        return redirect(url_for('view_workout', workout_id=workout_id))
    
    return render_template('edit_workout.html', workout=workout)

# Удалить тренировку
@app.route('/workout/<int:workout_id>/delete', methods=['POST'])
def delete_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    database.delete_workout_session(workout_id, session['user_id'])
    return redirect(url_for('my_workouts'))

# Удаление одной тренировки
@app.route('/workout/delete_single', methods=['POST'])
def delete_single_workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout_id = request.form.get('workout_id')
    
    # Удаляем данные из localStorage на сервере (по сути ничего не делаем, 
    # но клиент сам почистит при следующем обновлении)
    # Просто удаляем тренировку из БД
    database.delete_workout_session(workout_id, session['user_id'])
    
    return redirect(url_for('my_workouts'))

# Массовое удаление тренировок
@app.route('/workout/delete_multiple', methods=['POST'])
def delete_multiple_workouts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout_ids = request.form.getlist('workout_ids[]')
    
    for workout_id in workout_ids:
        database.delete_workout_session(workout_id, session['user_id'])
    
    return redirect(url_for('my_workouts'))

# Начать тренировку
@app.route('/workout/<int:workout_id>/start')
def start_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    if not workout:
        return redirect(url_for('my_workouts'))
    
    exercises = database.get_workout_exercises(workout_id)
    
    return render_template('active_workout.html',
                         workout=workout,
                         exercises=exercises,
                         is_continuing=False,
                         is_admin=session.get('is_admin', 0))  # ДОБАВЬ ЭТО

# Продолжить тренировку
@app.route('/workout/<int:workout_id>/continue')
def continue_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    if not workout:
        return redirect(url_for('my_workouts'))
    
    exercises = database.get_workout_exercises(workout_id)
    
    return render_template('active_workout.html',
                         workout=workout,
                         exercises=exercises,
                         is_continuing=True,
                         is_admin=session.get('is_admin', 0))  # ДОБАВЬ ЭТО

# Сохранение завершённой тренировки
@app.route('/api/save_completed_workout', methods=['POST'])
def save_completed_workout():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = request.get_json()
    
    print(f"\n=== СОХРАНЕНИЕ ТРЕНИРОВКИ ===")
    print(f"Тренировка: {data['workout_name']} (ID {data['workout_id']})")
    print(f"Количество подходов: {len(data['sets'])}")
    
    # Проверим каждый подход
    for i, s in enumerate(data['sets']):
        print(f"  Подход {i+1}: упражнение ID {s['exercise_id']} - {s['exercise_name']}, {s['weight']}x{s['reps']}")
    
    success = database.save_completed_workout(
        session['user_id'],
        data['workout_id'],
        data['workout_name'],
        data['duration'],
        data['sets']
    )
    
    print(f"Результат сохранения: {success}")
    print("="*50)
    return jsonify({'success': success})

# API для проверки существования тренировки
@app.route('/api/check_workout/<int:workout_id>')
def check_workout(workout_id):
    if 'user_id' not in session:
        return jsonify({'exists': False})
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    return jsonify({'exists': workout is not None})

## Страница статистики
@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stats_data = database.get_user_stats(session['user_id'])
    recent_workouts = database.get_recent_workouts(session['user_id'])
    
    return render_template('stats.html', 
                         stats=stats_data,
                         recent_workouts=recent_workouts,
                         is_admin=session.get('is_admin', 0))

# API для получения прогресса упражнения
@app.route('/api/exercise_progress/<int:exercise_id>')
def exercise_progress(exercise_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = database.get_exercise_progress(session['user_id'], exercise_id)
    
    # Преобразуем Row в dict
    result = []
    for row in data:
        result.append({
            'workout_date': row['workout_date'],
            'one_rm': row['one_rm'],
            'weight': row['weight'],
            'reps': row['reps']
        })
    
    return jsonify({'success': True, 'data': result})


# API для проверки существования тренировки
@app.route('/api/check_workout/<int:workout_id>')
def check_workout_exists(workout_id):
    if 'user_id' not in session:
        return jsonify({'exists': False})
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    return jsonify({'exists': workout is not None})

#endregion

    #region --------------------------------УПРАВЛЕНИЕ ТАБЛИЦАМИ АДМИН ПАНЕЛЬ-------------------------
@app.route('/admin/tables')
def table_manager():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    stats = database.get_admin_stats()
    
    # Получаем последние записи для предпросмотра
    with database.get_db() as conn:
        cursor = conn.cursor()
        
        # Получаем всех пользователей (для таблицы)
        cursor.execute('SELECT id, username, is_admin FROM users ORDER BY id DESC LIMIT 5')
        users = cursor.fetchall()
        
        # Получаем последние тренировки
        cursor.execute('SELECT id, name, date FROM workout_sessions ORDER BY id DESC LIMIT 3')
        recent_workouts = cursor.fetchall()
        
        # Получаем последние упражнения
        cursor.execute('SELECT id, name, muscle_group FROM exercises ORDER BY id DESC LIMIT 3')
        recent_exercises = cursor.fetchall()
        
        # Получаем последние записи статистики
        cursor.execute('''
            SELECT cw.id, cw.workout_name, cw.date 
            FROM completed_workouts cw 
            ORDER BY cw.id DESC LIMIT 3
        ''')
        recent_stats = cursor.fetchall()
    
    return render_template('table_manager.html',
                         stats=stats,
                         users=users,  # Добавили users
                         recent_workouts=recent_workouts,
                         recent_exercises=recent_exercises,
                         recent_stats=recent_stats,
                         is_admin=session.get('is_admin', 0))

# API для получения данных графиков (если нужно обновлять в реальном времени)
@app.route('/api/chart_data')
def chart_data():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'users': database.get_users_chart_data(),
        'workouts': database.get_workouts_chart_data()
    })




#region ========== API ДЛЯ УПРАВЛЕНИЯ ТАБЛИЦАМИ ==========
# Получить данные таблицы
@app.route('/api/table_data/<table_name>')
def get_table_data(table_name):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'completed_workouts', 'completed_sets']
    if table_name not in allowed_tables:
        return jsonify({'error': 'Invalid table'}), 400
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Для таблиц с внешними ключами добавим JOIN чтобы видеть имена пользователей
            if table_name == 'weight_tracking':
                cursor.execute('''
                    SELECT wt.*, u.username 
                    FROM weight_tracking wt
                    JOIN users u ON wt.user_id = u.id
                    ORDER BY wt.date DESC
                ''')
            elif table_name == 'bju_settings':
                cursor.execute('''
                    SELECT bs.*, u.username 
                    FROM bju_settings bs
                    JOIN users u ON bs.user_id = u.id
                    ORDER BY u.username
                ''')
            else:
                cursor.execute(f'SELECT * FROM {table_name} ORDER BY id DESC')
            
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(row))
            
            return jsonify(result)
    except Exception as e:
        print(f"Ошибка при получении данных таблицы {table_name}: {e}")
        return jsonify([])
# Обновить ячейку
@app.route('/api/update_cell/<table_name>/<int:row_id>', methods=['POST'])
def update_cell(table_name, row_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    column = data.get('column')
    value = data.get('value')
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'completed_workouts', 'completed_sets']
    if table_name not in allowed_tables:
        return jsonify({'success': False, 'error': 'Invalid table'}), 400
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE {table_name} SET {column} = ? WHERE id = ?', (value, row_id))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка при обновлении ячейки: {e}")
        return jsonify({'success': False, 'error': str(e)})
# Удалить строку
@app.route('/api/delete_row/<table_name>/<int:row_id>', methods=['POST'])
def delete_row(table_name, row_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'completed_workouts', 'completed_sets']
    if table_name not in allowed_tables:
        return jsonify({'success': False, 'error': 'Invalid table'}), 400
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM {table_name} WHERE id = ?', (row_id,))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка при удалении строки: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Массовое удаление
@app.route('/api/bulk_delete/<table_name>', methods=['POST'])
def bulk_delete(table_name):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    ids = data.get('ids', [])
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'completed_workouts', 'completed_sets']
    if table_name not in allowed_tables:
        return jsonify({'success': False, 'error': 'Invalid table'}), 400
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(ids))
            cursor.execute(f'DELETE FROM {table_name} WHERE id IN ({placeholders})', ids)
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка при массовом удалении: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Добавить строку
@app.route('/api/add_row/<table_name>', methods=['POST'])
def add_row(table_name):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'completed_workouts', 'completed_sets']
    if table_name not in allowed_tables:
        return jsonify({'success': False, 'error': 'Invalid table'}), 400
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            columns = ','.join(data.keys())
            placeholders = ','.join(['?'] * len(data))
            values = list(data.values())
            
            cursor.execute(f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})', values)
            conn.commit()
            return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        print(f"Ошибка при добавлении строки: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Обновить строку
@app.route('/api/update_row/<table_name>/<int:row_id>', methods=['POST'])
def update_row(table_name, row_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'completed_workouts', 'completed_sets']
    if table_name not in allowed_tables:
        return jsonify({'success': False, 'error': 'Invalid table'}), 400
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            set_clause = ','.join([f"{k} = ?" for k in data.keys() if k != 'id'])
            values = [v for k, v in data.items() if k != 'id']
            values.append(row_id)
            
            cursor.execute(f'UPDATE {table_name} SET {set_clause} WHERE id = ?', values)
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка при обновлении строки: {e}")
        return jsonify({'success': False, 'error': str(e)})
#endregion


#region========== API ДЛЯ УПРАВЛЕНИЯ УПРАЖНЕНИЯМИ ТРЕНИРОВКИ ==========

# Получить упражнения тренировки
@app.route('/api/workout_exercises/<int:workout_id>')
def get_workout_exercises_api(workout_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    we.id as workout_exercise_id,
                    we.exercise_id,
                    e.name,
                    e.muscle_group
                FROM workout_exercises we
                JOIN exercises e ON we.exercise_id = e.id
                WHERE we.workout_id = ?
                ORDER BY we.order_num
            ''', (workout_id,))
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            
            return jsonify(result)
    except Exception as e:
        print(f"Ошибка при получении упражнений тренировки: {e}")
        return jsonify([])

# Получить все упражнения из библиотеки
@app.route('/api/all_exercises')
def get_all_exercises_api():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, muscle_group FROM exercises ORDER BY name')
            rows = cursor.fetchall()
            return jsonify([dict(row) for row in rows])
    except Exception as e:
        print(f"Ошибка при получении списка упражнений: {e}")
        return jsonify([])

# Добавить упражнение в тренировку
@app.route('/api/add_exercise_to_workout/<int:workout_id>/<int:exercise_id>', methods=['POST'])
def add_exercise_to_workout_api(workout_id, exercise_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Получаем следующий порядковый номер
            cursor.execute('SELECT MAX(order_num) as max FROM workout_exercises WHERE workout_id = ?', (workout_id,))
            max_order = cursor.fetchone()['max'] or 0
            order_num = max_order + 1
            
            # Добавляем упражнение
            cursor.execute('''
                INSERT INTO workout_exercises (workout_id, exercise_id, sets, reps, weight, order_num, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (workout_id, exercise_id, 3, 10, 0, order_num, ''))
            
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка при добавлении упражнения в тренировку: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Удалить упражнение из тренировки
@app.route('/api/remove_exercise_from_workout/<int:workout_exercise_id>', methods=['POST'])
def remove_exercise_from_workout_api(workout_exercise_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM workout_exercises WHERE id = ?', (workout_exercise_id,))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка при удалении упражнения из тренировки: {e}")
        return jsonify({'success': False, 'error': str(e)})

#endregion


@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/easter-egg')
def easter_egg():
    media = database.get_easter_egg_media()
    return render_template('easter_egg.html', media=media)

@app.route('/admin/easter-egg')
def easter_egg_admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    media = database.get_easter_egg_media()
    return render_template('easter_egg_admin.html', 
                         media=media,
                         is_admin=session.get('is_admin', 0))

@app.route('/api/save_easter_egg', methods=['POST'])
def save_easter_egg():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False}), 401
    
    if 'media' not in request.files:
        return jsonify({'success': False}), 400
    
    file = request.files['media']
    if file.filename == '':
        return jsonify({'success': False}), 400
    
    # Определяем тип
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    media_type = 'video' if ext in ['mp4', 'webm', 'ogg', 'mov'] else 'image'
    
    # Сохраняем с уникальным именем
    filename = secure_filename(f"easter_{int(time.time())}.{ext}")
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    # Обновляем в БД
    database.update_easter_egg_media(f'uploads/{filename}', media_type)
    
    return jsonify({'success': True})
# API для проверки наличия видео
@app.route('/api/check_video')
def check_video():
    settings = database.get_easter_egg_settings()
    video_path = settings.get('video_path', '')
    full_path = os.path.join(UPLOAD_FOLDER, os.path.basename(video_path))
    return jsonify({'has_video': os.path.exists(full_path)})






#region================ УПРАВЛЕНИЕ ДАННЫМИ ПИТАНИЯ ДЛЯ АДМИНА ================

# Страница управления данными питания
@app.route('/admin/nutrition-data')
def admin_nutrition_data():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    tab = request.args.get('tab', 'weight')
    
    weight_entries = database.admin_get_all_weight_entries()
    bju_settings = database.admin_get_all_bju_settings()
    
    # Получаем список всех пользователей для выпадающих списков
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users ORDER BY username')
        users = cursor.fetchall()
    
    return render_template('admin_nutrition_data.html',
                         active_tab=tab,
                         weight_entries=weight_entries,
                         bju_settings=bju_settings,
                         users=users,
                         is_admin=session.get('is_admin', 0))

# API для обновления записи веса
@app.route('/api/admin/update_weight', methods=['POST'])
def admin_update_weight():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    success = database.admin_update_weight_entry(
        data['entry_id'],
        data['user_id'],
        data['date'],
        float(data['weight']),
        data['notes']
    )
    return jsonify({'success': success})

# API для удаления записи веса
@app.route('/api/admin/delete_weight', methods=['POST'])
def admin_delete_weight():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    success = database.admin_delete_weight_entry(data['entry_id'])
    return jsonify({'success': success})

# API для обновления настроек БЖУ
@app.route('/api/admin/update_bju', methods=['POST'])
def admin_update_bju():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    success = database.admin_update_bju_settings(
        data['settings_id'],
        data['user_id'],
        data['age'],
        data['height'],
        data['gender'],
        data['activity_level'],
        data['goal']
    )
    return jsonify({'success': success})

# API для сброса настроек БЖУ
@app.route('/api/admin/reset_bju', methods=['POST'])
def admin_reset_bju():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    success = database.admin_reset_bju_settings(data['settings_id'])
    return jsonify({'success': success})


# Страница питания
@app.route('/nutrition')
def nutrition():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    entries = database.get_weight_entries(session['user_id'])
    stats = database.get_weight_stats(session['user_id'])
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('nutrition.html', 
                         entries=entries, 
                         stats=stats, 
                         today=today,
                         is_admin=session.get('is_admin', 0))

# Добавление записи веса
@app.route('/add_weight', methods=['POST'])
def add_weight():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    date = request.form.get('date')
    weight = request.form.get('weight')
    notes = request.form.get('notes', '')
    
    if not date or not weight:
        return redirect(url_for('nutrition'))
    
    database.add_weight_entry(session['user_id'], date, float(weight), notes)
    return redirect(url_for('nutrition'))

# Удаление записи веса
@app.route('/delete_weight/<int:entry_id>', methods=['POST'])
def delete_weight(entry_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Здесь нужно добавить функцию удаления в database.py
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM weight_tracking WHERE id = ? AND user_id = ?', 
                         (entry_id, session['user_id']))
            conn.commit()
    except Exception as e:
        print(f"Ошибка при удалении: {e}")
    
    return redirect(url_for('nutrition'))

#endregion




























def open_browser():
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    database.init_db()
    try:
        database.init_exercises_table()
        print("Таблица упражнений инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации упражнений: {e}")
    
    try:
        database.init_workouts_table()
        print("Таблицы тренировок инициализированы")
    except Exception as e:
        print(f"Ошибка при инициализации тренировок: {e}")
    
    try:
        database.init_stats_table()
        print("Таблицы статистики инициализированы")
    except Exception as e:
        print(f"Ошибка при инициализации статистики: {e}")
    
    # НОВОЕ: инициализация таблиц питания
    try:
        database.init_nutrition_tables()
        print("Таблицы питания инициализированы")
    except Exception as e:
        print(f"Ошибка при инициализации питания: {e}")
    
    try:
        database.init_bju_settings_table()
        print("Таблица настроек БЖУ инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации БЖУ: {e}")


    threading.Thread(target=open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)