import sqlite3

DB_NAME = 'train.db'

def clear_duplicates():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Проверяем сколько записей было
    cursor.execute("SELECT COUNT(*) FROM completed_sets")
    old_count = cursor.fetchone()[0]
    print(f"Было записей в completed_sets: {old_count}")
    
    # Удаляем дубликаты
    cursor.execute('''
        DELETE FROM completed_sets 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM completed_sets 
            GROUP BY workout_id, exercise_id, weight, reps
        )
    ''')
    
    conn.commit()
    
    # Проверяем сколько осталось
    cursor.execute("SELECT COUNT(*) FROM completed_sets")
    new_count = cursor.fetchone()[0]
    print(f"Осталось записей: {new_count}")
    print(f"Удалено дублей: {old_count - new_count}")
    
    conn.close()

def clear_all_stats():
    """Полностью очистить статистику"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM completed_sets")
    cursor.execute("DELETE FROM completed_workouts")
    
    conn.commit()
    conn.close()
    print("Статистика полностью очищена!")

if __name__ == "__main__":
    print("1. Очистить дубликаты (оставить уникальные)")
    print("2. Полностью очистить всю статистику")
    choice = input("Выберите действие (1 или 2): ")
    
    if choice == '1':
        clear_duplicates()
    elif choice == '2':
        confirm = input("Точно очистить ВСЮ статистику? (да/нет): ")
        if confirm.lower() == 'да':
            clear_all_stats()
        else:
            print("Отменено")
    else:
        print("Неверный выбор")