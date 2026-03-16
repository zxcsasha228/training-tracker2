from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import sys
import threading
import webbrowser
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import database

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

# Маршрут для статических файлов
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

# Маршрут для загруженных файлов
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



















# ========== ОСНОВНЫЕ СТРАНИЦЫ ==========



@app.route('/profile/<int:user_id>')
def profile_view(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    user = database.get_user_by_id(user_id)
    if not user:
        return redirect(url_for('admin_panel'))
    
    stats = database.get_user_stats(user_id)
    

    return render_template('profile.html', 
                         user=user, 
                         stats=stats,
                         is_admin=session.get('is_admin', 0),
                         view_as_admin=True)
                        

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Перенаправляем на страницу с тренировками
    return redirect(url_for('my_workouts'))

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
            
            if user['is_admin']:
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверное имя пользователя или пароль')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        password = request.form['password']
        confirm = request.form['confirm_password']
        
        if password != confirm:
            return render_template('register.html', error='Пароли не совпадают')
        
        if not full_name:
            return render_template('register.html', error='Введите ФИО')
        
        user_id = database.create_user(username, password, full_name)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            session['full_name'] = full_name
            session['is_admin'] = 0
            return redirect(url_for('index'))
        else:
            return render_template('register.html', error='Пользователь с таким именем уже существует')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/my_workouts')
def my_workouts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workouts = database.get_user_workout_sessions(session['user_id'])
    
    # 👇 ПОЛУЧАЕМ СТАТУС ПАСХАЛКИ
    
    return render_template('my_workouts.html', 
                         workouts=workouts, 
                         username=session['username'],
                         is_admin=session.get('is_admin', 0))

@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stats_data = database.get_user_stats(session['user_id'])
    recent_workouts = database.get_recent_workouts(session['user_id'])
    
    easter_egg_enabled = database.get_easter_egg_enabled()  # 👈 ПОЛУЧАЕМ
    
    return render_template('stats.html', 
                         stats=stats_data,
                         recent_workouts=recent_workouts,
                         is_admin=session.get('is_admin', 0),
                         easter_egg_enabled=easter_egg_enabled)  # 👈 ПЕРЕДАЁМ

@app.route('/about')
def about():
    stats = database.get_admin_stats()
    about_content = database.get_about_content()
    return render_template('about.html',
                         about_content=about_content,
                         total_users=stats.get('total_users', 0),
                         total_exercises=stats.get('total_exercises', 0),
                         total_hours=stats.get('total_hours', 0),
                         is_admin=session.get('is_admin', 0))


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

# ========== ТРЕНИРОВКИ ==========

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
        
        today = datetime.now().strftime('%Y-%m-%d')
        
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

@app.route('/workout/<int:workout_id>')
def view_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    if not workout:
        return redirect(url_for('my_workouts'))
    
    exercises = database.get_workout_exercises(workout_id)
    all_exercises = database.get_all_exercises()
    return render_template('view_workout.html', 
                         workout=workout,
                         exercises=exercises,
                         all_exercises=all_exercises,
                         username=session['username'],
                         is_admin=session.get('is_admin', 0))

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
                         is_admin=session.get('is_admin', 0))

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
                         is_admin=session.get('is_admin', 0))

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

@app.route('/workout/delete_single', methods=['POST'])
def delete_single_workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout_id = request.form.get('workout_id')
    database.delete_workout_session(workout_id, session['user_id'])
    
    return redirect(url_for('my_workouts'))

@app.route('/workout/delete_multiple', methods=['POST'])
def delete_multiple_workouts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout_ids = request.form.getlist('workout_ids[]')
    
    for workout_id in workout_ids:
        database.delete_workout_session(workout_id, session['user_id'])
    
    return redirect(url_for('my_workouts'))

@app.route('/api/check_workout/<int:workout_id>')
def check_workout_exists(workout_id):
    if 'user_id' not in session:
        return jsonify({'exists': False})
    
    workout = database.get_workout_session(workout_id, session['user_id'])
    return jsonify({'exists': workout is not None})
# ========== УПРАЖНЕНИЯ ==========

@app.route('/exercises')
def exercises_library():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercises = database.get_all_exercises()
    muscle_groups = database.get_muscle_groups()
    
    return render_template('exercises_library.html', 
                         exercises=exercises, 
                         muscle_groups=muscle_groups,
                         is_admin=session.get('is_admin', 0))

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
        
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = f"uploads/{filename}"
        
        success = database.add_exercise(name, image, muscle_group, session['user_id'])
        if success:
            return redirect(url_for('exercises_library'))
        else:
            return render_template('add_exercise.html', 
                                 error='Упражнение с таким названием уже существует',
                                 is_admin=session.get('is_admin', 0))
    
    return render_template('add_exercise.html',
                         is_admin=session.get('is_admin', 0))

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
        
        image = exercise['image']
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = f"uploads/{filename}"
                
                if exercise['image']:
                    old_path = os.path.join(BASE_DIR, 'static', exercise['image'])
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
        
        database.update_exercise(exercise_id, name, image, muscle_group)
        return redirect(url_for('exercises_library'))
    
    return render_template('edit_exercise.html', 
                         exercise=exercise,
                         is_admin=session.get('is_admin', 0))

@app.route('/exercises/delete/<int:exercise_id>', methods=['POST'])
def delete_exercise(exercise_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    database.delete_exercise(exercise_id)
    return redirect(url_for('exercises_library'))

# ========== АДМИН-ПАНЕЛЬ ==========

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

@app.route('/admin/tables')
def table_manager():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    stats = database.get_admin_stats()
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, full_name, is_admin FROM users ORDER BY id DESC LIMIT 5')
        users = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT id, name, date FROM workout_sessions ORDER BY id DESC LIMIT 3')
        recent_workouts = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT id, name, muscle_group FROM exercises ORDER BY id DESC LIMIT 3')
        recent_exercises = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT id, display_name FROM gender_types ORDER BY sort_order')
        genders = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT id, display_name, value FROM activity_levels ORDER BY sort_order')
        activities = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT id, display_name FROM goal_types ORDER BY sort_order')
        goals = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT cw.id, cw.workout_name, cw.date 
            FROM completed_workouts cw 
            ORDER BY cw.id DESC LIMIT 3
        ''')
        recent_stats = [dict(row) for row in cursor.fetchall()]
    
    return render_template('table_manager.html',
                         stats=stats,
                         users=users,
                         recent_workouts=recent_workouts,
                         recent_exercises=recent_exercises,
                         recent_stats=recent_stats,
                         genders=genders,
                         activities=activities,
                         goals=goals,
                         is_admin=session.get('is_admin', 0))

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

@app.route('/admin/toggle_admin/<int:user_id>')
def toggle_admin(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if user_id == session['user_id']:
        return redirect(url_for('admin_panel'))
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            new_admin_status = 0 if user['is_admin'] else 1
            cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', 
                         (new_admin_status, user_id))
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if user_id == session['user_id']:
        return redirect(url_for('admin_panel'))
    
    database.delete_user_admin(user_id)
    return redirect(url_for('admin_panel'))

@app.route('/admin/nutrition-data')
def admin_nutrition_data():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    tab = request.args.get('tab', 'weight')
    
    weight_entries = database.admin_get_all_weight_entries()
    bju_settings = database.admin_get_all_bju_settings()
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, full_name FROM users ORDER BY username')
        users = [dict(row) for row in cursor.fetchall()]
    
    return render_template('admin_nutrition_data.html',
                         active_tab=tab,
                         weight_entries=weight_entries,
                         bju_settings=bju_settings,
                         users=users,
                         is_admin=session.get('is_admin', 0))

@app.route('/admin/lookups')
def lookup_tables():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM gender_types')
        gender_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM activity_levels')
        activity_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM goal_types')
        goal_count = cursor.fetchone()['count']
    
    return render_template('lookup_tables.html',
                         gender_count=gender_count,
                         activity_count=activity_count,
                         goal_count=goal_count,
                         is_admin=session.get('is_admin', 0))

@app.route('/admin/easter-egg')
def easter_egg_admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    media = database.get_easter_egg_media()
    return render_template('easter_egg_admin.html', 
                         media=media,
                         is_admin=session.get('is_admin', 0))

# ========== ПИТАНИЕ ==========

@app.route('/nutrition')
def nutrition():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    entries = database.get_weight_entries(session['user_id'])
    stats = database.get_weight_stats(session['user_id'])
    today = datetime.now().strftime('%Y-%m-%d')
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, display_name FROM gender_types ORDER BY sort_order')
        genders = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT id, display_name, value FROM activity_levels ORDER BY sort_order')
        activities = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT id, display_name FROM goal_types ORDER BY sort_order')
        goals = [dict(row) for row in cursor.fetchall()]
    
    return render_template('nutrition.html',
                         entries=entries,
                         stats=stats,
                         today=today,
                         genders=genders,
                         activities=activities,
                         goals=goals,
                         is_admin=session.get('is_admin', 0))

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

@app.route('/delete_weight/<int:entry_id>', methods=['POST'])
def delete_weight(entry_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM weight_tracking WHERE id = ? AND user_id = ?', 
                         (entry_id, session['user_id']))
            conn.commit()
    except Exception as e:
        print(f"Ошибка при удалении: {e}")
    
    return redirect(url_for('nutrition'))

# ========== API ДЛЯ ТАБЛИЦ ==========

@app.route('/api/table_data/<table_name>')
def get_table_data(table_name):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'gender_types', 'activity_levels', 'goal_types', 'about_content', 'easter_egg_settings', 'completed_workouts', 'completed_sets']
    if table_name not in allowed_tables:
        return jsonify({'error': 'Invalid table'}), 400
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            if table_name == 'workout_sessions':
                cursor.execute('''
                    SELECT 
                        ws.*,
                        u.full_name,
                        u.username
                    FROM workout_sessions ws
                    JOIN users u ON ws.user_id = u.id
                    ORDER BY ws.id DESC
                ''')
            elif table_name == 'weight_tracking':
                cursor.execute('''
                    SELECT 
                        wt.*,
                        u.full_name,
                        u.username
                    FROM weight_tracking wt
                    JOIN users u ON wt.user_id = u.id
                    ORDER BY wt.date DESC
                ''')
            elif table_name == 'bju_settings':
                cursor.execute('''
                    SELECT 
                        bs.*,
                        u.full_name,
                        u.username
                    FROM bju_settings bs
                    JOIN users u ON bs.user_id = u.id
                    ORDER BY u.username
                ''')
            elif table_name == 'completed_workouts':
                cursor.execute('''
                    SELECT 
                        cw.id,
                        cw.user_id,
                        cw.workout_name,
                        cw.date,
                        cw.duration,
                        cw.completed_at,
                        u.full_name,
                        u.username
                    FROM completed_workouts cw
                    JOIN users u ON cw.user_id = u.id
                    ORDER BY cw.completed_at DESC
                ''')
            elif table_name == 'completed_sets':
                cursor.execute('''
                    SELECT 
                        cs.*,
                        u.full_name,
                        u.username
                    FROM completed_sets cs
                    JOIN users u ON cs.user_id = u.id
                    ORDER BY cs.completed_at DESC
                ''')
            elif table_name == 'easter_egg_settings':
                cursor.execute('SELECT * FROM easter_egg_settings ORDER BY id DESC')
            else:
                cursor.execute(f'SELECT * FROM {table_name} ORDER BY id DESC')
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            
            return jsonify(result)
    except Exception as e:
        print(f"Ошибка при получении данных таблицы {table_name}: {e}")
        return jsonify([])

@app.route('/api/update_cell/<table_name>/<int:row_id>', methods=['POST'])
def update_cell(table_name, row_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    column = data.get('column')
    value = data.get('value')
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'gender_types', 'activity_levels', 'goal_types', 'about_content', 'easter_egg_settings', 'completed_workouts', 'completed_sets']
    if table_name not in allowed_tables:
        return jsonify({'success': False, 'error': 'Invalid table'}), 400
    
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            if column in ['gender_id', 'activity_id', 'goal_id', 'age', 'height', 'is_admin', 'sort_order']:
                try:
                    value = int(value)
                except:
                    pass
            elif column in ['weight', 'value', 'activity_level']:
                try:
                    value = float(value)
                except:
                    pass
            
            cursor.execute(f'UPDATE {table_name} SET {column} = ? WHERE id = ?', (value, row_id))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Ошибка при обновлении ячейки: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_row/<table_name>/<int:row_id>', methods=['POST'])
def delete_row(table_name, row_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'gender_types', 'activity_levels', 'goal_types', 'about_content', 'easter_egg_settings', 'completed_workouts', 'completed_sets']
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

@app.route('/api/bulk_delete/<table_name>', methods=['POST'])
def bulk_delete(table_name):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    ids = data.get('ids', [])
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'gender_types', 'activity_levels', 'goal_types', 'about_content', 'easter_egg_settings', 'completed_workouts', 'completed_sets']
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

@app.route('/api/add_row/<table_name>', methods=['POST'])
def add_row(table_name):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'gender_types', 'activity_levels', 'goal_types', 'about_content', 'easter_egg_settings', 'completed_workouts', 'completed_sets']
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

@app.route('/api/update_row/<table_name>/<int:row_id>', methods=['POST'])
def update_row(table_name, row_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    allowed_tables = ['users', 'workout_sessions', 'exercises', 'weight_tracking', 'bju_settings', 'gender_types', 'activity_levels', 'goal_types', 'about_content', 'easter_egg_settings', 'completed_workouts', 'completed_sets']
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

# ========== API ДЛЯ УПРАВЛЕНИЯ УПРАЖНЕНИЯМИ ТРЕНИРОВКИ ==========

@app.route('/api/workout_exercises/<int:workout_id>')
def get_workout_exercises_api(workout_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify([])
    
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
        return jsonify([dict(row) for row in rows])

@app.route('/api/all_exercises')
def get_all_exercises_api():
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, muscle_group FROM exercises ORDER BY name')
        rows = cursor.fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/api/add_exercise_to_workout/<int:workout_id>/<int:exercise_id>', methods=['POST'])
def add_exercise_to_workout_api(workout_id, exercise_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False})
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(order_num) as max FROM workout_exercises WHERE workout_id = ?', (workout_id,))
        max_order = cursor.fetchone()['max'] or 0
        order_num = max_order + 1
        
        cursor.execute('''
            INSERT INTO workout_exercises (workout_id, exercise_id, sets, reps, weight, order_num, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (workout_id, exercise_id, 3, 10, 0, order_num, ''))
        
        conn.commit()
        return jsonify({'success': True})

@app.route('/api/remove_exercise_from_workout/<int:workout_exercise_id>', methods=['POST'])
def remove_exercise_from_workout_api(workout_exercise_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False})
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM workout_exercises WHERE id = ?', (workout_exercise_id,))
        conn.commit()
        return jsonify({'success': True})

# Массовое добавление упражнений в тренировку
@app.route('/workout/<int:workout_id>/add_exercises', methods=['POST'])
def add_workout_exercises(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise_ids = request.form.getlist('exercise_ids[]')
    sets = request.form.get('sets', '3')
    reps = request.form.get('reps', '10')
    weight = request.form.get('weight', '0')
    
    exercises = database.get_workout_exercises(workout_id)
    order_num = len(exercises) + 1
    
    for exercise_id in exercise_ids:
        exercise = database.get_exercise(exercise_id)
        if exercise:
            database.add_exercise_to_workout(
                workout_id, exercise_id, sets, reps, weight, order_num, ""
            )
            order_num += 1
    
    return redirect(url_for('view_workout', workout_id=workout_id))

# Удаление нескольких упражнений из тренировки
@app.route('/workout/<int:workout_id>/delete_multiple', methods=['POST'])
def delete_multiple_exercises(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise_ids = request.form.getlist('exercise_ids[]')
    
    for exercise_id in exercise_ids:
        database.delete_workout_exercise(exercise_id)
    
    return redirect(url_for('view_workout', workout_id=workout_id))

# ========== API ДЛЯ БЖУ ==========

@app.route('/api/get_user_bju_settings')
def get_user_bju_settings():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM bju_settings WHERE user_id = ?', (session['user_id'],))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO bju_settings (user_id, age, height, gender_id, activity_id, goal_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], 30, 175, 2, 3, 1))
            conn.commit()
        
        cursor.execute('''
            SELECT age, height, gender_id, activity_id, goal_id 
            FROM bju_settings 
            WHERE user_id = ?
        ''', (session['user_id'],))
        
        settings = cursor.fetchone()
        
        if settings:
            return jsonify({
                'success': True,
                'age': settings['age'],
                'height': settings['height'],
                'gender_id': settings['gender_id'],
                'activity_id': settings['activity_id'],
                'goal_id': settings['goal_id']
            })
    
    return jsonify({'success': False})

@app.route('/api/update_bju_settings', methods=['POST'])
def update_bju_settings():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    data = request.get_json()
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM bju_settings WHERE user_id = ?', (session['user_id'],))
        if cursor.fetchone():
            cursor.execute('''
                UPDATE bju_settings 
                SET age = ?, height = ?, gender_id = ?, activity_id = ?, goal_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                data['age'],
                data['height'],
                data['gender_id'],
                data['activity_id'],
                data['goal_id'],
                session['user_id']
            ))
        else:
            cursor.execute('''
                INSERT INTO bju_settings (user_id, age, height, gender_id, activity_id, goal_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'],
                data['age'],
                data['height'],
                data['gender_id'],
                data['activity_id'],
                data['goal_id']
            ))
        
        conn.commit()
    
    return jsonify({'success': True})

@app.route('/api/check_bju_updates')
def check_bju_updates():
    if 'user_id' not in session:
        return jsonify({'changed': False})
    
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT updated_at FROM bju_settings 
            WHERE user_id = ?
        ''', (session['user_id'],))
        row = cursor.fetchone()
        
        if row:
            last_check = session.get('last_bju_update', '')
            current = row['updated_at']
            
            if last_check != current:
                session['last_bju_update'] = current
                return jsonify({'changed': True})
    
    return jsonify({'changed': False})

# ========== API ДЛЯ СТАТИСТИКИ ==========

@app.route('/api/save_completed_workout', methods=['POST'])
def save_completed_workout():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = request.get_json()
    
    success = database.save_completed_workout(
        session['user_id'],
        data['workout_id'],
        data['workout_name'],
        data['duration'],
        data['sets']
    )
    
    return jsonify({'success': success})

@app.route('/api/exercise_progress/<int:exercise_id>')
def exercise_progress(exercise_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = database.get_exercise_progress(session['user_id'], exercise_id)
    
    result = []
    for row in data:
        result.append({
            'workout_date': row['workout_date'],
            'one_rm': row['one_rm'],
            'weight': row['weight'],
            'reps': row['reps']
        })
    
    return jsonify({'success': True, 'data': result})

# ========== API ДЛЯ АДМИНКИ (ПИТАНИЕ) ==========

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

@app.route('/api/admin/delete_weight', methods=['POST'])
def admin_delete_weight():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    success = database.admin_delete_weight_entry(data['entry_id'])
    return jsonify({'success': success})

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

@app.route('/api/admin/reset_bju', methods=['POST'])
def admin_reset_bju():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    success = database.admin_reset_bju_settings(data['settings_id'])
    return jsonify({'success': success})

# ========== ПАСХАЛКА ==========

@app.route('/easter-egg')
def easter_egg():
    media = database.get_easter_egg_media()
    
    # Если пасхалка выключена, показываем 404 или редирект
    if not media.get('enabled', True):
        return redirect(url_for('my_workouts'))
    
    return render_template('easter_egg.html', media=media)

@app.route('/api/save_easter_egg', methods=['POST'])
def save_easter_egg():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False}), 401
    
    if 'media' not in request.files:
        return jsonify({'success': False}), 400
    
    file = request.files['media']
    if file.filename == '':
        return jsonify({'success': False}), 400
    
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    media_type = 'video' if ext in ['mp4', 'webm', 'ogg', 'mov'] else 'image'
    
    filename = secure_filename(f"easter_{int(time.time())}.{ext}")
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    database.update_easter_egg_media(f'uploads/{filename}', media_type)
    
    return jsonify({'success': True})

@app.route('/api/check_video')
def check_video():
    settings = database.get_easter_egg_media()
    video_path = settings.get('path', '')
    full_path = os.path.join(UPLOAD_FOLDER, os.path.basename(video_path))
    return jsonify({'has_video': os.path.exists(full_path)})

# ========== ЗАПУСК ==========

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
    
    try:
        database.init_lookup_tables()
        print("Справочные таблицы инициализированы")
    except Exception as e:
        print(f"Ошибка при инициализации справочников: {e}")
    
    try:
        database.init_about_table()
        print("Таблица контента О нас инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации контента О нас: {e}")
    
    try:
        database.init_easter_egg_table()
        print("Таблица пасхалки инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации пасхалки: {e}")
    
    try:
        database.migrate_database()
        print("Миграция базы данных выполнена")
    except Exception as e:
        print(f"Ошибка при миграции БД: {e}")
    
    threading.Thread(target=open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)