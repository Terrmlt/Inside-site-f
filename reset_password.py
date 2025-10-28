
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mineral_licenses.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    user = User.objects.get(username='runner')
    user.set_password('admin123')
    user.save()
    print('Пароль успешно изменен!')
    print('Логин: runner')
    print('Новый пароль: admin123')
except User.DoesNotExist:
    print('Пользователь runner не найден')
