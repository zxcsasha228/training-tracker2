from flask import Flask, render_template, request, redirect, url_for, jsonify
import database
import threading
import webbrowser
import time

app = Flask(__name__)

@app.route('/')
def index():
    workouts = database.get_all_workouts()
    return render_template('index.html', workouts=workouts)

@app.route('/add', methods=['POST'])
def add():
    date = request.form['date']
    exercise = request.form['exercise']
    sets = request.form['sets']
    reps = request.form['reps']
    weight = request.form['weight']
    
    database.add_workout(date, exercise, sets, reps, weight)
    return redirect(url_for('index'))

# НОВЫЙ МАРШРУТ: Страница редактирования
@app.route('/edit/<int:workout_id>')
def edit(workout_id):
    workout = database.get_workout(workout_id)
    return render_template('edit.html', workout=workout)

# НОВЫЙ МАРШРУТ: Сохранение изменений
@app.route('/update/<int:workout_id>', methods=['POST'])
def update(workout_id):
    date = request.form['date']
    exercise = request.form['exercise']
    sets = request.form['sets']
    reps = request.form['reps']
    weight = request.form['weight']
    
    database.update_workout(workout_id, date, exercise, sets, reps, weight)
    return redirect(url_for('index'))

# НОВЫЙ МАРШРУТ: Удаление
@app.route('/delete/<int:workout_id>', methods=['POST'])
def delete(workout_id):
    database.delete_workout(workout_id)
    return redirect(url_for('index'))

def open_browser():
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    database.init_db()
    threading.Thread(target=open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)