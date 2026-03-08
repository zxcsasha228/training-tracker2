import os
import sys
import threading
import webbrowser
import time
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
import database

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'

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
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')

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

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 💡 Добавляем маршрут для явной раздачи статических файлов (на всякий случай)
@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory(app.static_folder, filename)



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

# АДМИН-ПАНЕЛЬ
@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    stats = database.get_user_stats()
    users = database.get_all_users()
    return render_template('admin_panel.html', stats=stats, users=users)

# Просмотр данных пользователя (для админа)
@app.route('/admin/user/<int:user_id>')
def admin_user_details(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    user = database.get_user_with_password(user_id)
    workouts = database.get_user_workouts_admin(user_id)
    return render_template('admin_user_details.html', user=user, workouts=workouts)


# # Страница тренировок для админа
# @app.route('/my_workouts')
# def my_workouts():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     workouts = database.get_user_workouts(session['user_id'])
#     return render_template('index.html', workouts=workouts, username=session['username'], is_admin=session.get('is_admin', 0))
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     # Показываем тренировки текущего пользователя (даже если он админ)
#     workouts = database.get_user_workouts(session['user_id'])
#     return render_template('index.html', workouts=workouts, username=session['username'])

# Главная страница (для обычных пользователей)
# Главная страница для всех пользователей (и админов, и обычных)
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
                         is_admin=session.get('is_admin', 0))
    
    return render_template('exercises_library.html', 
                         exercises=exercises, 
                         muscle_groups=muscle_groups,
                         is_admin=session.get('is_admin', 0))

@app.route('/exercises/add', methods=['GET', 'POST'])
def add_exercise():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('add_exercise.html')
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        muscle_group = request.form.get('muscle_group', '').strip()
        
        if not name or not muscle_group:
            return render_template('add_exercise.html', 
                                 error='Заполните все обязательные поля')
        
        # Обработка загруженного изображения
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Создаём безопасное имя файла
                    filename = secure_filename(file.filename)
                    # Добавляем уникальный суффикс
                    filename = f"{int(time.time())}_{filename}"
                    # Полный путь для сохранения
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    # Сохраняем файл
                    file.save(full_path)
                    print(f"Файл сохранён: {full_path}")
                    
                    # 👇 ВОТ ЗДЕСЬ НУЖНО ДОБАВИТЬ ЭТИ СТРОКИ 👇
                    # Сохраняем относительный путь для базы данных
                    image_path = f"uploads/{filename}"
                    print(f"Сохранён путь в БД: {image_path}")
                    # 👆 КОНЕЦ ДОБАВЛЕНИЯ 👆
                    
                except Exception as e:
                    print(f"Ошибка при сохранении файла: {e}")
        
        success = database.add_exercise(name, image_path, muscle_group, session['user_id'])
        if success:
            return redirect(url_for('exercises_library'))
        else:
            return render_template('add_exercise.html', 
                                 error='Упражнение с таким названием уже существует')

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
                                 error='Заполните все обязательные поля')
        
        # Обработка нового изображения
        image_path = exercise['image']  # оставляем старое по умолчанию
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Создаём безопасное имя файла
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(full_path)
                    print(f"Файл сохранён: {full_path}")
                    image_path = f"uploads/{filename}"
                    
                    # Можно удалить старое изображение
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
    
    return render_template('edit_exercise.html', exercise=exercise)

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

# Создание новой тренировки (упрощённое)
@app.route('/workout/create', methods=['GET', 'POST'])
def create_workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            return render_template('create_workout.html', 
                                 error='Введите название тренировки')
        
        # Используем текущую дату автоматически
        from datetime import date
        today = date.today().isoformat()
        
        workout_id = database.create_workout_session(
            session['user_id'], name, today, ""  # пустые заметки
        )
        
        if workout_id:
            # ВОЗВРАЩАЕМСЯ К СПИСКУ ТРЕНИРОВОК, А НЕ В СОЗДАННУЮ
            return redirect(url_for('my_workouts'))
        else:
            return render_template('create_workout.html', 
                                 error='Ошибка при создании тренировки')
    
    return render_template('create_workout.html')

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
                         username=session['username'])

# # Добавить упражнение в тренировку
# @app.route('/workout/<int:workout_id>/add_exercise', methods=['POST'])
# def add_workout_exercise(workout_id):
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     exercise_id = request.form.get('exercise_id')
#     sets = request.form.get('sets')
#     reps = request.form.get('reps')
#     weight = request.form.get('weight')
    
#     # Получаем следующий порядковый номер
#     exercises = database.get_workout_exercises(workout_id)
#     order_num = len(exercises) + 1
    
#     database.add_exercise_to_workout(
#         workout_id, exercise_id, sets, reps, weight, order_num
#     )
    
#     return redirect(url_for('view_workout', workout_id=workout_id))

# Массовое добавление упражнений в тренировку
@app.route('/workout/<int:workout_id>/add_exercises', methods=['POST'])
def add_workout_exercises(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise_ids = request.form.getlist('exercise_ids[]')
    sets = request.form.get('sets', '3')
    reps = request.form.get('reps', '10')
    weight = request.form.get('weight', '0')
    
    # Получаем следующий порядковый номер
    exercises = database.get_workout_exercises(workout_id)
    order_num = len(exercises) + 1
    
    for exercise_id in exercise_ids:
        database.add_exercise_to_workout(
            workout_id, exercise_id, sets, reps, weight, order_num, ""
        )
        order_num += 1
    
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

# Редактировать тренировку (упрощённое)
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
        database.init_workouts_table()  # <-- ДОБАВЬ ЭТО
        print("Таблицы тренировок инициализированы")
    except Exception as e:
        print(f"Ошибка при инициализации тренировок: {e}")
    
    threading.Thread(target=open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)