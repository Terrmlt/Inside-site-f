# Развертывание Django приложения на Ubuntu Server 22.04 LTS с Apache

## Содержание
1. [Введение и требования](#введение-и-требования)
2. [Подключение к серверу через PuTTY](#подключение-к-серверу-через-putty)
3. [Настройка двух дисков](#настройка-двух-дисков)
4. [Обновление системы и установка зависимостей](#обновление-системы-и-установка-зависимостей)
5. [Установка и настройка PostgreSQL](#установка-и-настройка-postgresql)
6. [Установка Python и виртуального окружения](#установка-python-и-виртуального-окружения)
7. [Клонирование репозитория и настройка приложения](#клонирование-репозитория-и-настройка-приложения)
8. [Установка и настройка Apache + mod_wsgi](#установка-и-настройка-apache--mod_wsgi)
9. [Настройка SSL (Let's Encrypt)](#настройка-ssl-lets-encrypt)
10. [Настройка Firewall (UFW)](#настройка-firewall-ufw)
11. [Автоматические бэкапы](#автоматические-бэкапы)
12. [Обслуживание и мониторинг](#обслуживание-и-мониторинг)
13. [Troubleshooting](#troubleshooting)

---

## Введение и требования

Эта методичка описывает развертывание Django-приложения "База лицензий на недропользование" на чистом сервере Ubuntu 22.04 LTS.

### Системные требования
- Ubuntu Server 22.04 LTS (GNU/Linux 5.15.0-160-generic x86_64)
- Минимум 2 GB RAM
- Два диска:
  - **Диск 1 (системный):** ОС, приложение, база данных
  - **Диск 2 (данные):** папка media/ для загруженных файлов
- Доступ по SSH (для PuTTY)
- Доменное имя (опционально, для SSL)

### Что будет установлено
- Apache 2.4 + mod_wsgi
- PostgreSQL 14
- Python 3.10+ с pip
- Git
- Certbot (для SSL сертификатов)

---

## Подключение к серверу через PuTTY

### 1. Запуск PuTTY

1. Откройте PuTTY
2. В поле **Host Name** введите IP-адрес вашего сервера
3. **Port:** 22
4. **Connection type:** SSH
5. Нажмите **Open**

### 2. Первый вход

```bash
# Вход под root (если есть доступ)
login as: root

# Или под обычным пользователем
login as: username
```

### 3. Создание пользователя для приложения (рекомендуется)

```bash
# Создать нового пользователя
sudo adduser appuser

# Добавить в группу sudo
sudo usermod -aG sudo appuser

# Переключиться на нового пользователя
su - appuser
```

---

## Настройка двух дисков

В вашей VM есть два диска. Нужно смонтировать второй диск для хранения media-файлов.

### 1. Проверка доступных дисков

```bash
# Посмотреть список дисков
lsblk

# Пример вывода:
# NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
# sda      8:0    0   50G  0 disk 
# ├─sda1   8:1    0   49G  0 part /
# └─sda2   8:2    0    1G  0 part [SWAP]
# sdb      8:16   0  100G  0 disk           <- Второй диск
```

### 2. Форматирование второго диска (если еще не отформатирован)

**ВНИМАНИЕ:** Эта операция удалит все данные на диске!

```bash
# Проверить, смонтирован ли диск
sudo fdisk -l /dev/sdb

# Если диск пустой, создать раздел
sudo fdisk /dev/sdb

# В интерактивном режиме fdisk:
# n (новый раздел)
# p (primary)
# 1 (номер раздела)
# Enter (начало по умолчанию)
# Enter (конец по умолчанию)
# w (записать изменения)

# Отформатировать раздел в ext4
sudo mkfs.ext4 /dev/sdb1
```

### 3. Создание точки монтирования

```bash
# Создать директорию для media-файлов
sudo mkdir -p /mnt/media_storage

# Смонтировать диск
sudo mount /dev/sdb1 /mnt/media_storage

# Проверить монтирование
df -h | grep media_storage
```

### 4. Автоматическое монтирование при загрузке

```bash
# Узнать UUID диска
sudo blkid /dev/sdb1

# Пример вывода:
# /dev/sdb1: UUID="a1b2c3d4-e5f6-7890-abcd-ef1234567890" TYPE="ext4"

# Добавить в fstab для автомонтирования
sudo nano /etc/fstab

# Добавить строку в конец файла (замените UUID на свой):
UUID=a1b2c3d4-e5f6-7890-abcd-ef1234567890  /mnt/media_storage  ext4  defaults  0  2

# Сохранить и выйти: Ctrl+O, Enter, Ctrl+X

# Проверить корректность fstab
sudo mount -a

# Если ошибок нет, перезагрузить для проверки
sudo reboot
```

### 5. После перезагрузки (подключиться снова через PuTTY)

```bash
# Проверить, что диск примонтирован
df -h | grep media_storage

# Настроить права доступа
sudo chown -R www-data:www-data /mnt/media_storage
sudo chmod -R 755 /mnt/media_storage
```

---

## Обновление системы и установка зависимостей

### 1. Обновление пакетов

```bash
# Обновить списки пакетов
sudo apt update

# Установить обновления
sudo apt upgrade -y

# Перезагрузить (если обновилось ядро)
sudo reboot
```

### 2. Установка базовых утилит

```bash
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    vim \
    htop \
    ufw \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    libpq-dev
```

---

## Установка и настройка PostgreSQL

### 1. Установка PostgreSQL

```bash
# Установить PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Проверить статус
sudo systemctl status postgresql

# Включить автозапуск
sudo systemctl enable postgresql
```

### 2. Создание базы данных и пользователя

```bash
# Переключиться на пользователя postgres
sudo -u postgres psql

# В консоли PostgreSQL выполнить:
CREATE DATABASE mineral_licenses_db;
CREATE USER mineral_user WITH PASSWORD 'ВАШ_СЛОЖНЫЙ_ПАРОЛЬ';
ALTER ROLE mineral_user SET client_encoding TO 'utf8';
ALTER ROLE mineral_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE mineral_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE mineral_licenses_db TO mineral_user;

# Выйти из psql
\q
```

### 3. Настройка доступа (опционально, для удаленного подключения)

```bash
# Редактировать pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Найти строку:
# local   all   all   peer

# Изменить на:
# local   all   all   md5

# Сохранить и перезапустить PostgreSQL
sudo systemctl restart postgresql
```

### 4. Проверка подключения

```bash
# Попробовать подключиться
psql -U mineral_user -d mineral_licenses_db -h localhost

# Ввести пароль
# Если подключение успешно, выйти:
\q
```

---

## Установка Python и виртуального окружения

### 1. Проверка версии Python

```bash
# Проверить версию (должна быть 3.10+)
python3 --version

# Если версия старше 3.10, установить:
sudo apt install -y python3.10 python3.10-venv python3.10-dev
```

### 2. Создание директории для приложения

```bash
# Создать директорию
sudo mkdir -p /var/www/mineral_licenses
cd /var/www/mineral_licenses

# Назначить владельца
sudo chown -R $USER:$USER /var/www/mineral_licenses
```

---

## Клонирование репозитория и настройка приложения

### 1. Клонирование кода

```bash
cd /var/www/mineral_licenses

# Если репозиторий на GitHub/GitLab
git clone https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ.git .

# Или скопировать файлы вручную через SCP/SFTP
```

### 2. Создание виртуального окружения

```bash
cd /var/www/mineral_licenses

# Создать виртуальное окружение
python3 -m venv venv

# Активировать
source venv/bin/activate

# Обновить pip
pip install --upgrade pip
```

### 3. Установка зависимостей Python

```bash
# Установить зависимости из requirements.txt
pip install -r requirements.txt

# Если используете uv (установить отдельно):
pip install uv
uv pip install -r requirements.txt
```

### 4. Создание файла .env с настройками

```bash
# Создать файл .env
nano /var/www/mineral_licenses/.env

# Добавить следующие переменные:
SECRET_KEY='ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_DJANGO_50_СИМВОЛОВ'
DEBUG=False
ALLOWED_HOSTS=ваш-домен.ru,www.ваш-домен.ru,IP_АДРЕС_СЕРВЕРА

# База данных
DATABASE_URL=postgresql://mineral_user:ВАШ_ПАРОЛЬ@localhost:5432/mineral_licenses_db

# LDAP (если используется)
USE_LDAP=False

# Сохранить и выйти: Ctrl+O, Enter, Ctrl+X
```

### 5. Сбор статики и миграции

```bash
# Активировать виртуальное окружение
source /var/www/mineral_licenses/venv/bin/activate

cd /var/www/mineral_licenses

# Применить миграции
python manage.py migrate

# Собрать статические файлы
python manage.py collectstatic --noinput

# Создать суперпользователя
python manage.py createsuperuser
```

### 6. Создание символической ссылки для media

```bash
# Создать символическую ссылку на второй диск
ln -s /mnt/media_storage /var/www/mineral_licenses/media

# Или переместить существующую папку media
sudo mv /var/www/mineral_licenses/media /mnt/media_storage/
ln -s /mnt/media_storage /var/www/mineral_licenses/media

# Установить права
sudo chown -R www-data:www-data /mnt/media_storage
sudo chmod -R 755 /mnt/media_storage
```

### 7. Проверка settings.py

```bash
nano /var/www/mineral_licenses/mineral_licenses/settings.py

# Убедиться, что настройки корректны:
# STATIC_ROOT = BASE_DIR / 'staticfiles'
# MEDIA_ROOT = BASE_DIR / 'media'  (будет указывать на /mnt/media_storage)
# MEDIA_URL = '/media/'
```

---

## Установка и настройка Apache + mod_wsgi

### 1. Установка Apache и mod_wsgi

```bash
# Установить Apache
sudo apt install -y apache2

# Установить mod_wsgi для Python 3
sudo apt install -y libapache2-mod-wsgi-py3

# Проверить статус Apache
sudo systemctl status apache2

# Включить автозапуск
sudo systemctl enable apache2
```

### 2. Создание конфигурационного файла VirtualHost

```bash
# Создать файл конфигурации
sudo nano /etc/apache2/sites-available/mineral_licenses.conf
```

**Содержимое файла `/etc/apache2/sites-available/mineral_licenses.conf`:**

```apache
<VirtualHost *:80>
    ServerName ваш-домен.ru
    ServerAlias www.ваш-домен.ru
    ServerAdmin admin@ваш-домен.ru

    # Путь к приложению
    DocumentRoot /var/www/mineral_licenses

    # Логи
    ErrorLog ${APACHE_LOG_DIR}/mineral_licenses_error.log
    CustomLog ${APACHE_LOG_DIR}/mineral_licenses_access.log combined

    # WSGI настройки
    WSGIDaemonProcess mineral_licenses python-home=/var/www/mineral_licenses/venv python-path=/var/www/mineral_licenses
    WSGIProcessGroup mineral_licenses
    WSGIScriptAlias / /var/www/mineral_licenses/mineral_licenses/wsgi.py

    # Доступ к wsgi.py
    <Directory /var/www/mineral_licenses/mineral_licenses>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    # Статические файлы
    Alias /static/ /var/www/mineral_licenses/staticfiles/
    <Directory /var/www/mineral_licenses/staticfiles>
        Require all granted
    </Directory>

    # Media файлы (на втором диске)
    Alias /media/ /mnt/media_storage/
    <Directory /mnt/media_storage>
        Require all granted
    </Directory>

    # Безопасность
    <Directory /var/www/mineral_licenses>
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
```

### 3. Активация сайта и перезапуск Apache

```bash
# Отключить дефолтный сайт
sudo a2dissite 000-default.conf

# Включить новый сайт
sudo a2ensite mineral_licenses.conf

# Проверить конфигурацию на ошибки
sudo apache2ctl configtest

# Если вывод: "Syntax OK", перезапустить Apache
sudo systemctl restart apache2
```

### 4. Установка прав доступа

```bash
# Назначить Apache владельцем приложения
sudo chown -R www-data:www-data /var/www/mineral_licenses

# Установить корректные права
sudo chmod -R 755 /var/www/mineral_licenses

# Права на media (второй диск)
sudo chown -R www-data:www-data /mnt/media_storage
sudo chmod -R 755 /mnt/media_storage
```

### 5. Проверка работы

```bash
# Открыть в браузере:
http://IP_АДРЕС_СЕРВЕРА

# Или:
http://ваш-домен.ru
```

---

## Настройка SSL (Let's Encrypt)

### 1. Установка Certbot

```bash
# Установить Certbot для Apache
sudo apt install -y certbot python3-certbot-apache
```

### 2. Получение SSL сертификата

```bash
# Убедиться, что домен указывает на IP сервера

# Получить сертификат (автоматическая настройка Apache)
sudo certbot --apache -d ваш-домен.ru -d www.ваш-домен.ru

# Следовать инструкциям:
# 1. Ввести email для уведомлений
# 2. Принять условия (A)
# 3. Выбрать опцию перенаправления HTTP на HTTPS (2)
```

### 3. Проверка автообновления

```bash
# Certbot автоматически добавляет задачу cron для обновления
# Проверить таймер
sudo systemctl status certbot.timer

# Тестовый запуск обновления
sudo certbot renew --dry-run
```

### 4. Настройка HTTPS VirtualHost (опционально, если Certbot не настроил автоматически)

```bash
# Certbot должен был автоматически создать файл:
# /etc/apache2/sites-available/mineral_licenses-le-ssl.conf

# Если нет, создать вручную:
sudo nano /etc/apache2/sites-available/mineral_licenses-le-ssl.conf
```

**Содержимое:**

```apache
<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName ваш-домен.ru
    ServerAlias www.ваш-домен.ru

    DocumentRoot /var/www/mineral_licenses

    ErrorLog ${APACHE_LOG_DIR}/mineral_licenses_error.log
    CustomLog ${APACHE_LOG_DIR}/mineral_licenses_access.log combined

    WSGIDaemonProcess mineral_licenses python-home=/var/www/mineral_licenses/venv python-path=/var/www/mineral_licenses
    WSGIProcessGroup mineral_licenses
    WSGIScriptAlias / /var/www/mineral_licenses/mineral_licenses/wsgi.py

    <Directory /var/www/mineral_licenses/mineral_licenses>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    Alias /static/ /var/www/mineral_licenses/staticfiles/
    <Directory /var/www/mineral_licenses/staticfiles>
        Require all granted
    </Directory>

    Alias /media/ /mnt/media_storage/
    <Directory /mnt/media_storage>
        Require all granted
    </Directory>

    SSLCertificateFile /etc/letsencrypt/live/ваш-домен.ru/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/ваш-домен.ru/privkey.pem
    Include /etc/letsencrypt/options-ssl-apache.conf
</VirtualHost>
</IfModule>
```

```bash
# Включить SSL модуль
sudo a2enmod ssl

# Активировать HTTPS сайт
sudo a2ensite mineral_licenses-le-ssl.conf

# Перезапустить Apache
sudo systemctl restart apache2
```

---

## Настройка Firewall (UFW)

### 1. Установка и настройка UFW

```bash
# Проверить статус UFW
sudo ufw status

# Разрешить SSH (ВАЖНО! Иначе потеряете доступ)
sudo ufw allow OpenSSH

# Разрешить HTTP и HTTPS
sudo ufw allow 'Apache Full'

# Или отдельно:
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включить firewall
sudo ufw enable

# Проверить правила
sudo ufw status verbose
```

### 2. Ограничение доступа к PostgreSQL (опционально)

```bash
# По умолчанию PostgreSQL слушает только localhost
# Если нужен удаленный доступ, добавить правило:
sudo ufw allow from ДОВЕРЕННЫЙ_IP to any port 5432
```

---

## Автоматические бэкапы

### 1. Скрипт резервного копирования базы данных

```bash
# Создать директорию для бэкапов на втором диске
sudo mkdir -p /mnt/media_storage/backups
sudo chown -R www-data:www-data /mnt/media_storage/backups

# Создать скрипт бэкапа
sudo nano /usr/local/bin/backup_mineral_db.sh
```

**Содержимое `/usr/local/bin/backup_mineral_db.sh`:**

```bash
#!/bin/bash

# Настройки
DB_NAME="mineral_licenses_db"
DB_USER="mineral_user"
BACKUP_DIR="/mnt/media_storage/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/mineral_db_$DATE.sql.gz"

# Создание бэкапа
PGPASSWORD="ВАШ_ПАРОЛЬ_БД" pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_FILE

# Удалить бэкапы старше 30 дней
find $BACKUP_DIR -name "mineral_db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

```bash
# Сделать скрипт исполняемым
sudo chmod +x /usr/local/bin/backup_mineral_db.sh

# Проверить работу
sudo /usr/local/bin/backup_mineral_db.sh
```

### 2. Настройка автоматического запуска через cron

```bash
# Открыть crontab
sudo crontab -e

# Добавить строку для ежедневного бэкапа в 2:00 ночи:
0 2 * * * /usr/local/bin/backup_mineral_db.sh >> /var/log/mineral_backup.log 2>&1

# Сохранить и выйти
```

### 3. Скрипт бэкапа media-файлов (опционально)

```bash
sudo nano /usr/local/bin/backup_mineral_media.sh
```

**Содержимое:**

```bash
#!/bin/bash

# Настройки
MEDIA_DIR="/mnt/media_storage"
BACKUP_DIR="/mnt/media_storage/backups/media"
DATE=$(date +"%Y%m%d")
BACKUP_FILE="$BACKUP_DIR/media_$DATE.tar.gz"

# Создать директорию для бэкапов
mkdir -p $BACKUP_DIR

# Создание архива (исключая папку backups)
tar -czf $BACKUP_FILE --exclude="$BACKUP_DIR" $MEDIA_DIR

# Удалить бэкапы старше 7 дней
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "Media backup completed: $BACKUP_FILE"
```

```bash
# Сделать исполняемым
sudo chmod +x /usr/local/bin/backup_mineral_media.sh

# Добавить в crontab (еженедельно, по воскресеньям в 3:00)
sudo crontab -e

# Добавить строку:
0 3 * * 0 /usr/local/bin/backup_mineral_media.sh >> /var/log/mineral_backup.log 2>&1
```

---

## Обслуживание и мониторинг

### 1. Просмотр логов Apache

```bash
# Логи ошибок
sudo tail -f /var/log/apache2/mineral_licenses_error.log

# Логи доступа
sudo tail -f /var/log/apache2/mineral_licenses_access.log

# Все логи Apache
sudo tail -f /var/log/apache2/*.log
```

### 2. Просмотр логов PostgreSQL

```bash
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### 3. Мониторинг использования диска

```bash
# Общее использование
df -h

# Использование второго диска (media)
df -h /mnt/media_storage

# Размер папок в media
du -sh /mnt/media_storage/*
```

### 4. Мониторинг памяти и процессов

```bash
# Использование памяти
free -h

# Процессы Apache
ps aux | grep apache2

# Процессы PostgreSQL
ps aux | grep postgres

# Интерактивный мониторинг
htop
```

### 5. Перезапуск служб

```bash
# Перезапуск Apache
sudo systemctl restart apache2

# Перезапуск PostgreSQL
sudo systemctl restart postgresql

# Проверка статуса
sudo systemctl status apache2
sudo systemctl status postgresql
```

### 6. Обновление кода приложения

```bash
cd /var/www/mineral_licenses

# Получить обновления из git
git pull origin main

# Активировать виртуальное окружение
source venv/bin/activate

# Установить новые зависимости (если есть)
pip install -r requirements.txt

# Применить миграции
python manage.py migrate

# Собрать статику
python manage.py collectstatic --noinput

# Перезапустить Apache
sudo systemctl restart apache2
```

---

## Troubleshooting

### Проблема: Apache не запускается

```bash
# Проверить конфигурацию
sudo apache2ctl configtest

# Проверить логи
sudo tail -50 /var/log/apache2/error.log

# Проверить статус
sudo systemctl status apache2

# Детальная информация об ошибке
sudo journalctl -xe -u apache2
```

### Проблема: Ошибка 500 Internal Server Error

```bash
# Проверить логи ошибок Django/Apache
sudo tail -100 /var/log/apache2/mineral_licenses_error.log

# Проверить права доступа
ls -la /var/www/mineral_licenses/

# Проверить владельца
sudo chown -R www-data:www-data /var/www/mineral_licenses
sudo chown -R www-data:www-data /mnt/media_storage

# Проверить wsgi.py
cat /var/www/mineral_licenses/mineral_licenses/wsgi.py
```

### Проблема: Статические файлы не загружаются

```bash
# Проверить сбор статики
cd /var/www/mineral_licenses
source venv/bin/activate
python manage.py collectstatic --noinput

# Проверить права
sudo chown -R www-data:www-data /var/www/mineral_licenses/staticfiles
sudo chmod -R 755 /var/www/mineral_licenses/staticfiles

# Проверить конфигурацию Apache (Alias /static/)
sudo nano /etc/apache2/sites-available/mineral_licenses.conf
```

### Проблема: База данных недоступна

```bash
# Проверить статус PostgreSQL
sudo systemctl status postgresql

# Попробовать подключиться вручную
psql -U mineral_user -d mineral_licenses_db -h localhost

# Проверить pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Проверить, слушает ли PostgreSQL
sudo netstat -plnt | grep postgres
```

### Проблема: Второй диск не монтируется

```bash
# Проверить fstab
cat /etc/fstab

# Проверить UUID диска
sudo blkid

# Попробовать смонтировать вручную
sudo mount /dev/sdb1 /mnt/media_storage

# Проверить ошибки монтирования
dmesg | grep sdb
```

### Проблема: Недостаточно прав на запись в media

```bash
# Проверить права
ls -la /mnt/media_storage

# Установить правильные права
sudo chown -R www-data:www-data /mnt/media_storage
sudo chmod -R 755 /mnt/media_storage

# Проверить SELinux (если включен)
sudo getenforce
```

### Проблема: Certbot не может получить сертификат

```bash
# Проверить, что домен резолвится на IP
nslookup ваш-домен.ru

# Проверить, открыт ли порт 80
sudo ufw status | grep 80

# Проверить логи Certbot
sudo tail -50 /var/log/letsencrypt/letsencrypt.log

# Попробовать получить сертификат заново
sudo certbot --apache -d ваш-домен.ru -d www.ваш-домен.ru --dry-run
```

### Проблема: Django показывает ошибку конфигурации

```bash
# Проверить .env файл
cat /var/www/mineral_licenses/.env

# Проверить SECRET_KEY
# Проверить DATABASE_URL
# Проверить ALLOWED_HOSTS

# Проверить settings.py
nano /var/www/mineral_licenses/mineral_licenses/settings.py

# Тестовый запуск Django (для диагностики)
cd /var/www/mineral_licenses
source venv/bin/activate
python manage.py check
python manage.py runserver 0.0.0.0:8000
```

---

## Полезные команды

```bash
# Перезапуск Apache
sudo systemctl restart apache2

# Проверка конфигурации Apache
sudo apache2ctl configtest

# Просмотр активных сайтов
ls -l /etc/apache2/sites-enabled/

# Просмотр логов в реальном времени
sudo tail -f /var/log/apache2/mineral_licenses_error.log

# Проверка использования диска
df -h

# Проверка свободной памяти
free -h

# Список процессов Apache
ps aux | grep apache2

# Проверка открытых портов
sudo netstat -tlnp

# Перезагрузка сервера
sudo reboot
```

---

## Контрольный список после установки

- [ ] Сервер доступен по SSH через PuTTY
- [ ] Второй диск смонтирован в `/mnt/media_storage` и автомонтируется при загрузке
- [ ] PostgreSQL установлен, база данных создана
- [ ] Python виртуальное окружение создано
- [ ] Код приложения клонирован в `/var/www/mineral_licenses`
- [ ] Зависимости установлены через pip
- [ ] Миграции базы данных применены
- [ ] Статические файлы собраны
- [ ] Суперпользователь Django создан
- [ ] Apache установлен и настроен
- [ ] VirtualHost настроен и активирован
- [ ] Сайт работает по HTTP
- [ ] SSL сертификат установлен (Let's Encrypt)
- [ ] Сайт работает по HTTPS с автоматическим редиректом
- [ ] Firewall настроен (UFW)
- [ ] Автоматические бэкапы настроены
- [ ] Логи доступны и читаемы
- [ ] Админ-панель Django доступна по адресу `https://домен/admin/`

---

## Дополнительные рекомендации

### Безопасность

1. **Регулярно обновляйте систему:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Измените стандартный порт SSH (опционально):**
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Изменить: Port 22 → Port 2222
   sudo systemctl restart sshd
   ```

3. **Используйте fail2ban для защиты от брутфорса:**
   ```bash
   sudo apt install -y fail2ban
   sudo systemctl enable fail2ban
   ```

4. **Никогда не храните пароли и SECRET_KEY в git:**
   - Добавьте `.env` в `.gitignore`
   - Используйте переменные окружения

### Производительность

1. **Настройте Apache MPM (Multi-Processing Module):**
   ```bash
   sudo a2dismod mpm_prefork
   sudo a2enmod mpm_event
   sudo systemctl restart apache2
   ```

2. **Включите кеширование в Django (Redis/Memcached):**
   - Установите Redis: `sudo apt install redis-server`
   - Настройте в `settings.py`

3. **Оптимизируйте PostgreSQL для вашей нагрузки:**
   ```bash
   sudo nano /etc/postgresql/14/main/postgresql.conf
   # Настроить shared_buffers, work_mem, effective_cache_size
   ```

### Мониторинг

Рассмотрите установку инструментов мониторинга:
- **Netdata** — веб-интерфейс для мониторинга системы в реальном времени
- **Prometheus + Grafana** — для продвинутого мониторинга и алертов

---

**Поздравляем! Ваше Django приложение развернуто на Ubuntu Server 22.04 LTS с Apache.**

Если возникнут проблемы, обратитесь к разделу Troubleshooting или к логам Apache/PostgreSQL.
