import sqlite3

conn = sqlite3.connect('train.db')
cursor = conn.cursor()

print("Создание администратора...")

# Проверяем, есть ли уже админ
cursor.execute("SELECT * FROM users WHERE username = 'admin'")
admin = cursor.fetchone()

if not admin:
    # Создаём админа
    cursor.execute('''
        INSERT INTO users (username, password, full_name, is_admin)
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin123', 'Администратор', 1))
    print("✅ Админ создан: admin / admin123")
else:
    print("⏩ Админ уже существует")

conn.commit()
conn.close()

print("\nГотово!")
input("Нажми Enter для выхода...")