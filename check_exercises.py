import sqlite3

conn = sqlite3.connect('train.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== УПРАЖНЕНИЯ В БИБЛИОТЕКЕ ===\n")
cursor.execute('SELECT id, name FROM exercises ORDER BY id')
exercises = cursor.fetchall()

for ex in exercises:
    print(f"ID: {ex['id']} - {ex['name']}")

print(f"\nВсего упражнений: {len(exercises)}")

conn.close()
input("\nНажми Enter для выхода...")