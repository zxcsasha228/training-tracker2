from flask import Flask, render_template, request, redirect, url_for, session
import database
import threading
import webbrowser
import time
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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


# Страница тренировок для админа
@app.route('/my_workouts')
def my_workouts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workouts = database.get_user_workouts(session['user_id'])
    return render_template('index.html', workouts=workouts, username=session['username'], is_admin=session.get('is_admin', 0))
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Показываем тренировки текущего пользователя (даже если он админ)
    workouts = database.get_user_workouts(session['user_id'])
    return render_template('index.html', workouts=workouts, username=session['username'])

# Главная страница (для обычных пользователей)
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workouts = database.get_user_workouts(session['user_id'])
    return render_template('index.html', workouts=workouts, username=session['username'], is_admin=session.get('is_admin', 0))
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Если админ - показываем его тренировки, а не админку
    workouts = database.get_user_workouts(session['user_id'])
    return render_template('index.html', workouts=workouts, username=session['username'])

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

def open_browser():
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')


    
# ================ БИБЛИОТЕКА УПРАЖНЕНИЙ ================

# Страница библиотеки упражнений (доступна всем)
@app.route('/exercises')
def exercises_library():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Проверяем, есть ли таблица exercises, если нет - создаём
    try:
        exercises = database.get_all_exercises()
        muscle_groups = database.get_muscle_groups()
    except:
        # Если таблицы нет, инициализируем её
        database.init_exercises_table()
        exercises = database.get_all_exercises()
        muscle_groups = database.get_muscle_groups()
    
    return render_template('exercises_library.html', 
                         exercises=exercises, 
                         muscle_groups=muscle_groups,
                         is_admin=session.get('is_admin', 0))

# Добавление упражнения (только админ)
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
                # Создаём безопасное имя файла
                filename = secure_filename(file.filename)
                # Добавляем уникальный суффикс чтобы файлы не перезаписывались
                import time
                filename = f"{int(time.time())}_{filename}"
                # Сохраняем файл
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Сохраняем путь для базы данных
                image_path = f"uploads/{filename}"
        
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
                # Создаём безопасное имя файла
                filename = secure_filename(file.filename)
                import time
                filename = f"{int(time.time())}_{filename}"
                # Сохраняем файл
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Обновляем путь
                image_path = f"uploads/{filename}"
        
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

if __name__ == '__main__':
    database.init_db()                 # инициализация пользователей
    database.init_exercises_table()     # <-- ДОБАВЬ ЭТУ СТРОКУ
    threading.Thread(target=open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)