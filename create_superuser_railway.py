import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
email = 'admin@example.com'
password = 'Admin123456'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Суперпользователь '{username}' создан!")
    print(f"   Пароль: {password}")
else:
    print(f"⚠️ Суперпользователь '{username}' уже существует")
    
# Вывести всех пользователей
print(f"\n📊 Всего пользователей в БД: {User.objects.count()}")
