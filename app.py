from flask import Flask, render_template, request, redirect, url_for
import database
import threading
import webbrowser
import time

app = Flask(__name__)

# Главная страница - показывает таблицу с тренировками
@app.route('/')
def index():
    workouts = database.get_all_workouts()
    return render_template('index.html', workouts=workouts)

# Страница для добавления новой тренировки
@app.route('/add', methods=['POST'])
def add():
    date = request.form['date']
    exercise = request.form['exercise']
    sets = request.form['sets']
    reps = request.form['reps']
    weight = request.form['weight']
    
    database.add_workout(date, exercise, sets, reps, weight)
    return redirect(url_for('index'))

def open_browser():
    """Функция для открытия браузера через 1 секунду после запуска сервера."""
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    # Инициализируем базу данных при запуске
    database.init_db()
    
    # Запускаем браузер в отдельном потоке, чтобы не блокировать сервер
    threading.Thread(target=open_browser).start()
    
    # Запускаем сервер
    # host='127.0.0.1' - чтобы сайт был только на локальном компьютере
    # debug=False - важно для exe, чтобы не было ошибок
    app.run(host='127.0.0.1', port=5000, debug=False)