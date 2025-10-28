
# Инструкция по развёртыванию сайта на виртуальной машине Linux

## Требования

- Ubuntu 20.04/22.04 или аналогичный дистрибутив Linux
- Права sudo
- Доступ к интернету

---

## Шаг 1: Обновление системы и установка зависимостей

```bash
# Обновление списка пакетов
sudo apt update && sudo apt upgrade -y

# Установка Python и необходимых инструментов
sudo apt install -y python3 python3-pip python3-venv git

# Установка PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Установка библиотек для сборки psycopg2
sudo apt install -y libpq-dev python3-dev build-essential
```

---

## Шаг 2: Настройка PostgreSQL

### 2.1. Создание базы данных и пользователя

```bash
# Переключиться на пользователя postgres
sudo -u postgres psql
```

В PostgreSQL консоли выполните:

```sql
-- Создание пользователя БД
CREATE USER mineral_user WITH PASSWORD 'ваш_надёжный_пароль';

-- Создание базы данных
CREATE DATABASE mineral_licenses_db;

-- Выдача прав пользователю
GRANT ALL PRIVILEGES ON DATABASE mineral_licenses_db TO mineral_user;

-- Выход
\q
```

### 2.2. Настройка доступа к PostgreSQL

Отредактируйте файл `pg_hba.conf`:

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

Добавьте или измените строку для локального доступа:

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   mineral_licenses_db  mineral_user                        md5
```

Перезапустите PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 2.3. Проверка подключения

```bash
psql -U mineral_user -d mineral_licenses_db -h localhost
```

Введите пароль. Если подключение успешно, выйдите через `\q`.

---

## Шаг 3: Клонирование и настройка проекта

### 3.1. Создание директории проекта

```bash
# Создание директории для приложения
sudo mkdir -p /var/www/mineral_licenses
cd /var/www/mineral_licenses

# Клонирование кода (или загрузка архива)
# Вариант 1: Если есть git репозиторий
# git clone https://ваш-репозиторий.git .

# Вариант 2: Загрузка и распаковка архива проекта
# sudo tar -xzf mineral_licenses.tar.gz

# Установка прав
sudo chown -R $USER:$USER /var/www/mineral_licenses
```

### 3.2. Установка зависимостей Python

```bash
cd /var/www/mineral_licenses

# Установка uv (менеджер пакетов)
pip3 install uv

# Установка зависимостей из pyproject.toml
uv pip install --system django psycopg2-binary django-cors-headers pillow python-dotenv dj-database-url
```

---

## Шаг 4: Настройка переменных окружения

Создайте файл `.env`:

```bash
nano /var/www/mineral_licenses/.env
```

Добавьте следующие настройки:

```bash
# Django настройки
SECRET_KEY='ваш-секретный-ключ-здесь-создайте-случайную-строку'
DEBUG=False
ALLOWED_HOSTS=ваш-домен.com,ваш-ip-адрес

# База данных PostgreSQL
DATABASE_URL=postgresql://mineral_user:ваш_надёжный_пароль@localhost:5432/mineral_licenses_db

# Яндекс.Карты API ключ (опционально)
YANDEX_MAPS_API_KEY=ваш-api-ключ

# CSRF настройки
CSRF_TRUSTED_ORIGINS=https://ваш-домен.com,http://ваш-ip-адрес
```

**Генерация SECRET_KEY:**

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## Шаг 5: Настройка Django settings.py

Отредактируйте `mineral_licenses/settings.py`:

```bash
nano mineral_licenses/settings.py
```

Убедитесь, что следующие настройки корректны:

```python
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Загрузка переменных окружения
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# CSRF настройки
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')

# Static и Media файлы
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

---

## Шаг 6: Выполнение миграций и сбор статики

```bash
cd /var/www/mineral_licenses

# Выполнение миграций БД
python3 manage.py migrate

# Сбор статических файлов
python3 manage.py collectstatic --noinput

# Создание суперпользователя
python3 manage.py createsuperuser

# Создание директории для медиа файлов
mkdir -p media
chmod 755 media
```

---

## Шаг 7: Установка и настройка Gunicorn

### 7.1. Установка Gunicorn

```bash
pip3 install gunicorn
```

### 7.2. Тестовый запуск

```bash
cd /var/www/mineral_licenses
gunicorn --bind 0.0.0.0:8000 mineral_licenses.wsgi:application
```

Если всё работает, остановите сервер (Ctrl+C).

### 7.3. Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Добавьте:

```ini
[Unit]
Description=Gunicorn daemon for Mineral Licenses Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mineral_licenses
Environment="PATH=/usr/bin"
ExecStart=/usr/local/bin/gunicorn \
    --workers 3 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    mineral_licenses.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 7.4. Настройка прав и запуск

```bash
# Установка прав
sudo chown -R www-data:www-data /var/www/mineral_licenses

# Запуск и включение автозагрузки
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Проверка статуса
sudo systemctl status gunicorn
```

---

## Шаг 8: Установка и настройка Nginx

### 8.1. Установка Nginx

```bash
sudo apt install -y nginx
```

### 8.2. Настройка конфигурации

```bash
sudo nano /etc/nginx/sites-available/mineral_licenses
```

Добавьте:

```nginx
server {
    listen 80;
    server_name ваш-домен.com ваш-ip-адрес;

    client_max_body_size 100M;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        alias /var/www/mineral_licenses/staticfiles/;
    }

    location /media/ {
        alias /var/www/mineral_licenses/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

### 8.3. Активация конфигурации

```bash
# Создание символической ссылки
sudo ln -s /etc/nginx/sites-available/mineral_licenses /etc/nginx/sites-enabled/

# Удаление дефолтной конфигурации (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## Шаг 9: Настройка SSL (HTTPS) с Let's Encrypt

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d ваш-домен.com

# Автообновление сертификата
sudo systemctl enable certbot.timer
```

---

## Шаг 10: Настройка Firewall

```bash
# Установка UFW (если не установлен)
sudo apt install -y ufw

# Разрешение SSH, HTTP и HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'

# Включение firewall
sudo ufw enable

# Проверка статуса
sudo ufw status
```

---

## Полезные команды для управления

### Перезапуск сервисов

```bash
# Перезапуск Gunicorn
sudo systemctl restart gunicorn

# Перезапуск Nginx
sudo systemctl restart nginx

# Перезапуск PostgreSQL
sudo systemctl restart postgresql
```

### Просмотр логов

```bash
# Логи Gunicorn
sudo journalctl -u gunicorn -f

# Логи Nginx (ошибки)
sudo tail -f /var/log/nginx/error.log

# Логи Nginx (доступ)
sudo tail -f /var/log/nginx/access.log

# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### Обновление кода

```bash
cd /var/www/mineral_licenses

# Обновление кода (git pull или загрузка новых файлов)
# git pull origin main

# Выполнение миграций (если есть новые)
python3 manage.py migrate

# Сбор статики
python3 manage.py collectstatic --noinput

# Перезапуск Gunicorn
sudo systemctl restart gunicorn
```

---

## Резервное копирование базы данных

### Создание бэкапа

```bash
# Полный бэкап БД
sudo -u postgres pg_dump mineral_licenses_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Бэкап через Django
python3 manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
```

### Восстановление из бэкапа

```bash
# Восстановление PostgreSQL дампа
sudo -u postgres psql mineral_licenses_db < backup_20251028_120000.sql

# Восстановление Django дампа
python3 manage.py loaddata backup_20251028_120000.json
```

---

## Мониторинг и оптимизация PostgreSQL

### Настройка пула соединений (опционально)

Для высоконагруженных приложений рекомендуется использовать PgBouncer:

```bash
# Установка PgBouncer
sudo apt install -y pgbouncer

# Редактирование конфигурации
sudo nano /etc/pgbouncer/pgbouncer.ini
```

Пример конфигурации:

```ini
[databases]
mineral_licenses_db = host=localhost port=5432 dbname=mineral_licenses_db

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
```

Обновите DATABASE_URL в `.env`:

```bash
DATABASE_URL=postgresql://mineral_user:пароль@localhost:6432/mineral_licenses_db
```

---

## Проверка работоспособности

1. Откройте браузер и перейдите по адресу: `http://ваш-ip-адрес` или `https://ваш-домен.com`
2. Проверьте доступ к админ-панели: `/admin/`
3. Проверьте API: `/api/licenses/`
4. Загрузите тестовый GeoJSON файл через `/upload-geojson/`

---

## Troubleshooting

### Проблема: 502 Bad Gateway

```bash
# Проверьте статус Gunicorn
sudo systemctl status gunicorn

# Проверьте логи
sudo journalctl -u gunicorn -n 50
```

### Проблема: Статические файлы не загружаются

```bash
# Убедитесь, что права правильные
sudo chown -R www-data:www-data /var/www/mineral_licenses/staticfiles
sudo chmod -R 755 /var/www/mineral_licenses/staticfiles

# Пересоберите статику
python3 manage.py collectstatic --noinput
```

### Проблема: Ошибка подключения к БД

```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Проверьте подключение вручную
psql -U mineral_user -d mineral_licenses_db -h localhost

# Проверьте DATABASE_URL в .env
cat /var/www/mineral_licenses/.env | grep DATABASE_URL
```

---

## Дополнительная безопасность

### 1. Ограничение доступа к PostgreSQL

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

Оставьте только локальный доступ:

```
local   all             postgres                                peer
local   mineral_licenses_db  mineral_user                        md5
```

### 2. Регулярные обновления

```bash
# Настройка автоматических обновлений безопасности
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

**Готово!** Ваш сайт развёрнут на виртуальной машине Linux с PostgreSQL базой данных.
