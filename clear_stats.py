import sqlite3

DB_NAME = 'train.db'

def clear_completed_stats():
    """Очищает таблицы завершённых тренировок"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Проверяем сколько записей было
        cursor.execute("SELECT COUNT(*) FROM completed_workouts")
        old_workouts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM completed_sets")
        old_sets = cursor.fetchone()[0]
        
        print(f"📊 До очистки:")
        print(f"   - completed_workouts: {old_workouts} записей")
        print(f"   - completed_sets: {old_sets} записей")
        
        # Очищаем таблицы
        cursor.execute("DELETE FROM completed_sets")
        cursor.execute("DELETE FROM completed_workouts")
        
        # Сбрасываем автоинкремент
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='completed_workouts'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='completed_sets'")
        
        conn.commit()
        
        print(f"\n✅ Очищено!")
        print(f"   - completed_workouts: 0 записей")
        print(f"   - completed_sets: 0 записей")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def reset_all_user_stats():
    """Сбросить статистику для всех пользователей (очистить завершённые тренировки)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Полная очистка
        cursor.execute("DELETE FROM completed_sets")
        cursor.execute("DELETE FROM completed_workouts")
        
        # Сброс автоинкремента
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='completed_workouts'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='completed_sets'")
        
        conn.commit()
        conn.close()
        
        print("✅ Статистика всех пользователей сброшена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🧹 Очистка завершённых тренировок")
    print("=" * 50)
    clear_completed_stats()