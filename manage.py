#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()


# git status
# git add .
# git commit -m ""
# git push origin main
# python manage.py makemigrations
# python manage.py migrate
# pip list - проверить что установено


#Локальная подготовка (выполнить перед пушем)
# 1. Установить зависимости
#pip install -r requirements.txt

# 2. Создайте .env файл для локальной разработки
# (скопируйте из .env.example)

# 3. Проверьте настройки
#python manage.py check --deploy

# 4. Создайте локальную БД
#python manage.py migrate

# 5. Соберите статику
#python manage.py collectstatic --noinput

# 6. Запустите сервер для теста
#python manage.py runserver

# 7. Если всё работает - остановить сервер (Ctrl+C)


# Пуш на GitHub

# 1. Убедитесь, что .env НЕ в git
#git status

# 2. Добавьте все файлы
# git add .

# или изменения только из определенной папки
# git add shop/templates/shop/

# 3. Создайте коммит
#git commit -m "Ready for Railway deployment with PostgreSQL"

# 4. Пуш
#git push origin main

# Проверьте структуру
# tree shop\static

# # Поиск модели в файле
# findstr "class Preorder" shop\models.py

# 1. Проверьте существующие миграции
# python manage.py showmigrations shop

# Поверяет галичие определенных строк/слов в определенном файле
# type shop\urls.py | findstr "add_to_cart"
# type shop\views.py | findstr "def add_to_cart"       определенных функций
