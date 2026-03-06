import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"Текущая папка: {BASE_DIR}")

# Проверяем папки
static_folder = os.path.join(BASE_DIR, 'static')
uploads_folder = os.path.join(BASE_DIR, 'static', 'uploads')

print(f"\nПроверка папок:")
print(f"static существует: {os.path.exists(static_folder)}")
print(f"uploads существует: {os.path.exists(uploads_folder)}")

if not os.path.exists(static_folder):
    print("Создаю static...")
    os.makedirs(static_folder)
    
if not os.path.exists(uploads_folder):
    print("Создаю uploads...")
    os.makedirs(uploads_folder)

print(f"\nПосле создания:")
print(f"static существует: {os.path.exists(static_folder)}")
print(f"uploads существует: {os.path.exists(uploads_folder)}")

input("\nНажми Enter для выхода...")