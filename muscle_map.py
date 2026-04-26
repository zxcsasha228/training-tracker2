import os
import sqlite3
from pathomap import BodyMap
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

DB_NAME = 'train.db'

def get_muscle_load(user_id):
    """Получить нагрузку на мышцы за последние 7 дней"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT 
            e.muscle_group,
            COUNT(cs.id) as sets_count
        FROM completed_sets cs
        JOIN exercises e ON cs.exercise_id = e.id
        WHERE cs.user_id = ? AND cs.workout_date >= ?
        GROUP BY e.muscle_group
    ''', (user_id, week_ago))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Базовые мышцы со значением 0
    muscles = {
        'Грудные': 0,
        'Спина': 0,
        'Ноги': 0,
        'Плечи': 0,
        'Бицепс': 0,
        'Трицепс': 0,
        'Пресс': 0,
        'Ягодицы': 0
    }
    
    for row in rows:
        if row[0] in muscles:
            muscles[row[0]] = row[1]
    
    return muscles

def create_muscle_heatmap(user_id, output_path='static/muscle_heatmap.png'):
    """Создаёт карту нагрузки мышц и сохраняет как изображение"""
    
    muscle_data = get_muscle_load(user_id)
    
    # Нормализуем значения (0-20+ подходов -> 0-1)
    max_load = max(muscle_data.values()) if max(muscle_data.values()) > 0 else 1
    
    # Создаём BodyMap
    bm = BodyMap()
    
    # Соответствие мышц в БД и в BodyMap
    muscle_mapping = {
        'Грудные': 'chest',
        'Спина': 'back',
        'Ноги': 'legs',
        'Плечи': 'shoulders',
        'Бицепс': 'biceps',
        'Трицепс': 'triceps',
        'Пресс': 'abs',
        'Ягодицы': 'glutes'
    }
    
    # Применяем цвета к мышцам
    for muscle_name, value in muscle_data.items():
        bodypart = muscle_mapping.get(muscle_name)
        if bodypart:
            # Нормализуем значение
            intensity = min(value / 20.0, 1.0)
            # Выбираем цвет: от синего (0) до красного (1)
            if intensity < 0.2:
                color = '#3b82f6'  # синий
            elif intensity < 0.4:
                color = '#22c55e'  # зелёный
            elif intensity < 0.6:
                color = '#eab308'  # жёлтый
            elif intensity < 0.8:
                color = '#f97316'  # оранжевый
            else:
                color = '#ef4444'  # красный
            
            bm.set_muscle_color(bodypart, color)
    
    # Визуализируем
    fig = bm.plot()
    fig.set_size_inches(10, 16)
    plt.tight_layout()
    
    # Создаём папку static если её нет
    os.makedirs('static', exist_ok=True)
    
    # Сохраняем
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Карта мышц сохранена: {output_path}")
    return output_path

if __name__ == '__main__':
    # Для теста возьмём первого пользователя
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    conn.close()
    
    if user:
        create_muscle_heatmap(user[0])
    else:
        print("❌ Пользователи не найдены")