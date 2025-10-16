
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mineral_licenses.settings')
django.setup()

from django.contrib.auth.models import User

# Данные суперпользователя
username = 'admin'
email = 'admin@example.com'
password = 'admin123'

# Проверяем, существует ли уже суперпользователь
if User.objects.filter(username=username).exists():
    print(f'Суперпользователь "{username}" уже существует!')
else:
    # Создаем суперпользователя
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Суперпользователь создан успешно!')
    print(f'Логин: {username}')
    print(f'Пароль: {password}')
    print(f'Теперь можете войти в /admin/')
