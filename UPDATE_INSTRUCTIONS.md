# Инструкция по обновлению сайта на VM

## Описание
Эта инструкция описывает процесс обновления работающего Django-сайта "База лицензий на недропользование" на Ubuntu Server VM. Процесс включает обновление кода из GitHub репозитория, обновление зависимостей, применение миграций и перезапуск сервисов.

## Предварительные требования
- Доступ к серверу по SSH
- Работающий сайт на `/var/www/mineral_licenses`
- PostgreSQL база данных `mineral_licenses`
- Git репозиторий настроен и подключен к GitHub
- Права sudo для перезапуска Apache

---

## Шаг 1: Подготовка и создание бэкапа

### 1.1. Подключение к серверу

```bash
# Подключиться к серверу через SSH (PuTTY или терминал)
ssh username@IP_АДРЕС_СЕРВЕРА
# или
ssh username@домен.ru
```

### 1.2. Проверка статуса сервисов

Перед обновлением убедитесь, что все сервисы работают корректно:

```bash
# Проверить статус Apache
sudo systemctl status apache2

# Проверить статус PostgreSQL
sudo systemctl status postgresql

# Если сервисы не работают, запустить их:
sudo systemctl start apache2
sudo systemctl start postgresql
```

### 1.3. Сохранение текущей версии кода

```bash
# Перейти в директорию проекта
cd /var/www/mineral_licenses

# Проверить текущий коммит (сохранить для отката при необходимости)
git log -1 --oneline > /tmp/current_version.txt
cat /tmp/current_version.txt

# Или создать тег текущей версии
git tag backup-$(date +%Y%m%d-%H%M%S)
git log -1
```

### 1.4. Создание бэкапа базы данных

**ВАЖНО:** Всегда создавайте бэкап базы данных перед обновлением!

```bash
# Если у вас есть скрипт бэкапа (из DEPLOYMENT_UBUNTU_SERVER.md)
sudo /usr/local/bin/backup_mineral_db.sh

# Или создать бэкап вручную:
BACKUP_DIR="/mnt/media_storage/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/mineral_licenses_$DATE.sql.gz"

# Создать директорию для бэкапов, если её нет
sudo mkdir -p $BACKUP_DIR

# Создать бэкап (замените пароль на ваш)
PGPASSWORD="ВАШ_ПАРОЛЬ_БД" pg_dump -U mineral_user -h localhost mineral_licenses | gzip > $BACKUP_FILE

# Проверить, что бэкап создан
ls -lh $BACKUP_FILE

# Сохранить путь к бэкапу
echo "Backup created: $BACKUP_FILE" > /tmp/backup_info.txt
cat /tmp/backup_info.txt
```

**Примечание:** Если база данных называется `mineral_licenses_db` (а не `mineral_licenses`), замените имя в команде выше.

---

## Шаг 2: Обновление кода из GitHub

### 2.1. Настройка безопасного доступа к репозиторию

Если при выполнении Git команд вы получили ошибку:
```
fatal: detected dubious ownership in repository at '/var/www/mineral_licenses'
```

Это защита Git от выполнения команд в репозиториях, принадлежащих другому пользователю. Решение:

```bash
# Добавить директорию в список безопасных (выполнить один раз)
git config --global --add safe.directory /var/www/mineral_licenses

# Или для всех директорий (менее безопасно, но удобно):
# git config --global --add safe.directory '*'

# Проверить, что настройка применена
git config --global --get-all safe.directory
```

**Примечание:** Эта настройка безопасна, так как вы доверяете этой директории. Она сохраняется в `~/.gitconfig` и применяется ко всем Git операциям.

**Важно:** Если после добавления в `safe.directory` вы все еще получаете ошибку `Permission denied` при выполнении `git fetch` или `git pull`, это означает, что у вас нет прав на запись в директорию `.git`. См. решение ниже в разделе "Проблема: Permission denied при git fetch/pull".

### 2.2. Проверка текущего состояния репозитория

```bash
cd /var/www/mineral_licenses

# Проверить текущую ветку
git branch

# Проверить статус (не должно быть незакоммиченных изменений)
git status
```

**Если есть незакоммиченные изменения:**

**Вариант 1: Изменения не нужны (все важное на GitHub) - отменить их:**

```bash
# Посмотреть, какие файлы изменены
git status

# Посмотреть, что именно изменилось (опционально, для проверки)
git diff

# Отменить ВСЕ незакоммиченные изменения (ОСТОРОЖНО: это удалит изменения!)
git checkout -- .

# Или отменить изменения в конкретном файле:
# git checkout -- путь/к/файлу

# Проверить, что изменения отменены
git status
```

**Вариант 2: Изменения могут понадобиться - сохранить их в stash:**

```bash
# Сохранить изменения в stash (можно восстановить позже)
git stash save "backup before update $(date +%Y%m%d-%H%M%S)"

# Посмотреть список сохраненных изменений
git stash list

# Если нужно восстановить позже:
# git stash pop
```

**Если при stash возникает ошибка "Permission denied":**

Это происходит, когда файлы принадлежат другому пользователю (например, `www-data`). Решения:

**Решение A: Изменить владельца файлов перед stash**

```bash
# Проверить текущего пользователя
whoami

# Временно изменить владельца измененных файлов
sudo chown -R $USER:$USER .

# Теперь выполнить stash
git stash save "backup before update $(date +%Y%m%d-%H%M%S)"

# После stash можно вернуть права (опционально)
sudo chown -R www-data:www-data .
```

**Решение B: Если изменения не нужны, просто отменить их (проще)**

```bash
# Отменить все изменения без stash
git checkout -- .

# Проверить статус
git status
```

**Решение C: Сохранить изменения в отдельный файл вручную**

```bash
# Посмотреть, что изменилось
git diff > /tmp/local_changes_backup.patch

# Отменить изменения
git checkout -- .

# Если нужно восстановить позже:
# git apply /tmp/local_changes_backup.patch
```

**Вариант 3: Изменения нужно закоммитить (если это важные настройки сервера):**

```bash
# Посмотреть, что изменилось
git status
git diff

# Добавить измененные файлы в staging
git add mineral_licenses/settings.py
# или добавить все измененные файлы:
# git add .

# Создать коммит с описанием
git commit -m "Local server configuration changes before update"

# Проверить, что коммит создан
git log -1 --oneline

# Теперь можно обновляться (но могут быть конфликты при merge)
git pull origin main
```

**Важно:** Если вы закоммитите изменения, а затем сделаете `git pull`, Git попытается автоматически объединить изменения. Если возникнут конфликты, их нужно будет разрешить вручную (см. раздел "Проблема: Git pull выдает ошибку 'Your local changes would be overwritten'").

**Рекомендация для продакшн-сервера:** Обычно на сервере не коммитят изменения напрямую. Лучше:
- Использовать `git stash` для временного сохранения
- Или сохранить важные настройки в `.env` файл (который не в Git)
- Или создать отдельную ветку для серверных настроек

### 2.3. Получение обновлений из GitHub

```bash
# Получить информацию об изменениях (не применяя их)
git fetch origin

# Посмотреть, какие изменения будут применены
git log HEAD..origin/main --oneline
# или для ветки master:
# git log HEAD..origin/master --oneline

# Применить обновления
# Для ветки main:
git pull origin main

# Или для ветки master:
# git pull origin master

# Если возникли конфликты, разрешить их вручную
# git status покажет файлы с конфликтами
```

**Если при `git pull` возникает ошибка "Permission denied":**

Это происходит, когда файлы принадлежат другому пользователю (например, `www-data`). Решение:

```bash
cd /var/www/mineral_licenses

# Проверить текущего пользователя
whoami

# Временно изменить владельца всех файлов на текущего пользователя
sudo chown -R $USER:$USER .

# Теперь выполнить pull
git pull origin main

# После успешного обновления вернуть права для Apache (ВАЖНО!)
sudo chown -R www-data:www-data /var/www/mineral_licenses/staticfiles
sudo chown -R www-data:www-data /mnt/media_storage
sudo chown -R www-data:www-data /var/www/mineral_licenses/media

# Для остальных файлов можно оставить вашего пользователя или вернуть www-data
# (в зависимости от вашей политики безопасности)
```

**Альтернативный способ (если не хотите менять владельца всех файлов):**

```bash
# Изменить владельца только для файлов, которые будут обновлены
# Сначала посмотреть, какие файлы изменятся
git diff --name-only HEAD origin/main

# Изменить владельца только этих файлов (пример)
sudo chown $USER:$USER licenses/templates/licenses/*.html licenses/views.py mineral_licenses/settings.py

# Выполнить pull
git pull origin main

# Вернуть права
sudo chown www-data:www-data licenses/templates/licenses/*.html licenses/views.py mineral_licenses/settings.py
```

### 2.3. Проверка изменений в requirements.txt

```bash
# Посмотреть, изменился ли requirements.txt
git diff HEAD~1 requirements.txt

# Или сравнить с удаленной версией
git diff HEAD origin/main requirements.txt
```

---

## Шаг 3: Обновление зависимостей Python

### 3.1. Активация виртуального окружения

```bash
cd /var/www/mineral_licenses

# Активировать виртуальное окружение
source venv/bin/activate

# Проверить, что окружение активировано (должен показать путь к venv)
which python
```

### 3.2. Обновление зависимостей

```bash
# Обновить pip до последней версии
pip install --upgrade pip

# Установить/обновить зависимости из requirements.txt
pip install -r requirements.txt

# Если используете uv (опционально):
# pip install uv
# uv pip install -r requirements.txt

# Проверить установленные пакеты
pip list
```

---

## Шаг 4: Применение миграций базы данных

### 4.1. Проверка наличия новых миграций

```bash
cd /var/www/mineral_licenses
source venv/bin/activate

# Проверить, какие миграции нужно применить
python manage.py showmigrations

# Или посмотреть только непримененные миграции
python manage.py showmigrations --plan | grep "\[ \]"
```

### 4.2. Применение миграций

```bash
# Применить все непримененные миграции
python manage.py migrate

# Если нужно применить миграции для конкретного приложения:
# python manage.py migrate licenses

# Проверить статус миграций после применения
python manage.py showmigrations
```

**Что означает "No migrations to apply":**

Если вы видите сообщение:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, licenses, sessions
Running migrations:
  No migrations to apply.
```

**Это нормально и хорошо!** Это означает:
- ✅ Все миграции уже применены
- ✅ База данных находится в актуальном состоянии
- ✅ В обновлении не было новых миграций (или они уже были применены ранее)

**Когда это может произойти:**
- Миграции уже были применены при предыдущем обновлении
- В новом коде нет изменений в моделях базы данных
- База данных уже синхронизирована с кодом

**Важно:** Если при применении миграций возникли ошибки, НЕ ПРОДОЛЖАЙТЕ! Откатите изменения (см. раздел "Откат изменений").

---

## Шаг 5: Обновление статических файлов

### 5.1. Сбор статических файлов

```bash
cd /var/www/mineral_licenses
source venv/bin/activate

# Собрать статические файлы
python manage.py collectstatic --noinput

# Проверить, что файлы собраны
ls -lh staticfiles/
```

### 5.2. Проверка прав доступа

```bash
# Убедиться, что Apache имеет доступ к статическим файлам
sudo chown -R www-data:www-data /var/www/mineral_licenses/staticfiles
sudo chmod -R 755 /var/www/mineral_licenses/staticfiles
```

---

## Шаг 6: Перезапуск сервисов

### 6.1. Проверка конфигурации Apache

```bash
# Проверить конфигурацию Apache на ошибки
sudo apache2ctl configtest

# Если есть ошибки, исправить их перед перезапуском
```

### 6.2. Перезапуск Apache

```bash
# Перезапустить Apache для применения изменений
sudo systemctl restart apache2

# Проверить статус после перезапуска
sudo systemctl status apache2

# Если Apache не запустился, проверить логи:
sudo tail -50 /var/log/apache2/error.log
sudo tail -50 /var/log/apache2/mineral_licenses_error.log
```

### 6.3. Проверка работы сайта

```bash
# Проверить, что сайт отвечает
curl -I http://localhost
# или
curl -I https://ваш-домен.ru

# Проверить логи доступа
sudo tail -20 /var/log/apache2/mineral_licenses_access.log
```

---

## Шаг 7: Проверка и тестирование

### 7.0. Проверка файла .env (ВАЖНО!)

После обновления убедитесь, что файл `.env` существует и содержит все необходимые настройки:

```bash
cd /var/www/mineral_licenses

# Проверить, существует ли файл .env
ls -la .env

# Посмотреть содержимое (БЕЗ показа паролей)
cat .env | grep -v PASSWORD
```

**Если файл .env отсутствует или поврежден:**

```bash
# Создать файл .env
nano /var/www/mineral_licenses/.env
```

**Минимально необходимые настройки в .env:**

```env
SECRET_KEY='ваш_секретный_ключ_50_символов'
DEBUG=False
ALLOWED_HOSTS=192.168.23.58,ваш-домен.ru,www.ваш-домен.ru

# База данных (ВАЖНО!)
DATABASE_URL=postgresql://mineral_user:ВАШ_ПАРОЛЬ@localhost:5432/mineral_licenses
```

**После создания/обновления .env файла:**

```bash
# Проверить, что Django может прочитать настройки
source venv/bin/activate
python manage.py check --deploy

# Если ошибка "DATABASES is improperly configured", проверьте:
# 1. Существует ли файл .env
# 2. Правильно ли указан DATABASE_URL
# 3. Загружается ли .env файл (проверить load_dotenv() в settings.py)
```

### 7.1. Проверка логов на ошибки

```bash
# Логи ошибок Apache
sudo tail -50 /var/log/apache2/mineral_licenses_error.log

# Логи Django (если настроены)
# Обычно ошибки Django попадают в логи Apache

# Логи PostgreSQL (если есть проблемы с БД)
sudo tail -50 /var/log/postgresql/postgresql-14-main.log
```

### 7.2. Функциональное тестирование

Проверьте в браузере:
- [ ] Главная страница загружается
- [ ] Карта отображается корректно
- [ ] Список лицензий работает
- [ ] Фильтры работают
- [ ] Поиск работает
- [ ] Админ-панель доступна (если используется)
- [ ] Статические файлы (CSS, JS) загружаются

### 7.3. Проверка базы данных

```bash
# Подключиться к базе данных и проверить данные
psql -U mineral_user -d mineral_licenses -h localhost

# В консоли PostgreSQL:
# Проверить количество записей в таблице licenses
SELECT COUNT(*) FROM licenses_license;

# Выйти из psql
\q
```

---

## Откат изменений (если что-то пошло не так)

### Откат кода

```bash
cd /var/www/mineral_licenses

# Посмотреть сохраненную версию
cat /tmp/current_version.txt

# Откатиться к предыдущему коммиту
git reset --hard HEAD~1

# Или к конкретному коммиту/тегу
# git reset --hard backup-20250101-120000

# Или восстановить из stash
# git stash list
# git stash pop
```

### Восстановление базы данных из бэкапа

```bash
# Найти файл бэкапа
cat /tmp/backup_info.txt
# или
ls -lh /mnt/media_storage/backups/

# Восстановить базу данных (ЗАМЕНИТЕ путь к файлу)
BACKUP_FILE="/mnt/media_storage/backups/mineral_licenses_20250101_120000.sql.gz"

# ОСТОРОЖНО: Это удалит все текущие данные!
# Сначала можно переименовать текущую БД:
sudo -u postgres psql -c "ALTER DATABASE mineral_licenses RENAME TO mineral_licenses_old_$(date +%Y%m%d);"

# Создать новую БД
sudo -u postgres psql -c "CREATE DATABASE mineral_licenses;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mineral_licenses TO mineral_user;"

# Восстановить данные
gunzip < $BACKUP_FILE | psql -U mineral_user -d mineral_licenses -h localhost
```

### Откат зависимостей

```bash
cd /var/www/mineral_licenses
source venv/bin/activate

# Если нужно откатить конкретный пакет:
# pip install package_name==старая_версия

# Или переустановить все зависимости из старого requirements.txt
# (если вы сохранили старую версию)
# pip install -r requirements.txt.old
```

---

## Быстрая команда для обновления (после проверки)

Если вы уверены в процессе, можно выполнить все шаги одной командой:

```bash
#!/bin/bash
# Сохраните это как update_site.sh и сделайте исполняемым: chmod +x update_site.sh

cd /var/www/mineral_licenses

# Бэкап БД
BACKUP_DIR="/mnt/media_storage/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/mineral_licenses_$DATE.sql.gz"
mkdir -p $BACKUP_DIR
PGPASSWORD="ВАШ_ПАРОЛЬ" pg_dump -U mineral_user -h localhost mineral_licenses | gzip > $BACKUP_FILE
echo "Backup created: $BACKUP_FILE"

# Сохранение версии
git log -1 --oneline > /tmp/current_version.txt

# Обновление кода
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Миграции
python manage.py migrate

# Статика
python manage.py collectstatic --noinput
sudo chown -R www-data:www-data staticfiles

# Перезапуск
sudo systemctl restart apache2

echo "Update completed!"
```

---

## Часто возникающие проблемы

### Проблема: Ошибка "fatal: detected dubious ownership in repository"

**Симптомы:**
```
fatal: detected dubious ownership in repository at '/var/www/mineral_licenses'
To add an exception for this directory, call:
    git config --global --add safe.directory /var/www/mineral_licenses
```

**Причина:** Git защищает от выполнения команд в репозиториях, принадлежащих другому пользователю (например, `www-data`). Это функция безопасности, добавленная в Git 2.35.2+.

**Решение:**
```bash
# Добавить директорию в список безопасных (выполнить один раз)
git config --global --add safe.directory /var/www/mineral_licenses

# Проверить настройку
git config --global --get-all safe.directory

# Теперь команды Git должны работать
git branch
git status
```

**Альтернативное решение (менее безопасно):**
```bash
# Разрешить все директории (не рекомендуется для продакшена)
git config --global --add safe.directory '*'
```

### Проблема: Ошибка "Permission denied" при git stash

**Симптомы:**
```
error: unable to unlink old 'manage.py': Permission denied
error: unable to unlink old 'mineral_licenses/settings.py': Permission denied
fatal: Could not reset index file to revision 'HEAD'.
```

**Причина:** Файлы принадлежат другому пользователю (обычно `www-data`), и Git не может их изменить при выполнении stash.

**Решение 1: Изменить владельца файлов перед stash**

```bash
cd /var/www/mineral_licenses

# Проверить текущего пользователя
whoami

# Временно изменить владельца всех файлов
sudo chown -R $USER:$USER .

# Выполнить stash
git stash save "backup before update $(date +%Y%m%d-%H%M%S)"

# После stash вернуть права для Apache (ВАЖНО!)
sudo chown -R www-data:www-data /var/www/mineral_licenses/staticfiles
sudo chown -R www-data:www-data /mnt/media_storage
sudo chown -R www-data:www-data /var/www/mineral_licenses/media
```

**Решение 2: Если изменения не нужны, просто отменить их**

```bash
# Отменить все изменения (проще, чем stash)
git checkout -- .

# Проверить статус
git status
```

**Решение 3: Сохранить изменения в отдельный файл**

```bash
# Сохранить diff в файл
git diff > /tmp/local_changes_backup_$(date +%Y%m%d-%H%M%S).patch

# Отменить изменения
git checkout -- .

# Если нужно восстановить позже:
# git apply /tmp/local_changes_backup_*.patch
```

**Рекомендация:** Если изменения не критичны, используйте Решение 2 - просто отмените их командой `git checkout -- .`

### Проблема: Ошибка "Permission denied" при git pull

**Симптомы:**
```
error: unable to unlink old 'licenses/templates/licenses/map.html': Permission denied
error: unable to unlink old 'licenses/views.py': Permission denied
error: unable to unlink old 'mineral_licenses/settings.py': Permission denied
```

**Причина:** Файлы принадлежат другому пользователю (обычно `www-data`), и Git не может их обновить при выполнении pull.

**Решение 1: Изменить владельца файлов перед pull (рекомендуется)**

```bash
cd /var/www/mineral_licenses

# Проверить текущего пользователя
whoami

# Временно изменить владельца всех файлов
sudo chown -R $USER:$USER .

# Выполнить pull
git pull origin main

# После успешного обновления вернуть права для Apache (ВАЖНО!)
sudo chown -R www-data:www-data /var/www/mineral_licenses/staticfiles
sudo chown -R www-data:www-data /mnt/media_storage
sudo chown -R www-data:www-data /var/www/mineral_licenses/media

# Для остальных файлов можно оставить вашего пользователя или вернуть www-data
```

**Решение 2: Изменить владельца только обновляемых файлов**

```bash
# Сначала посмотреть, какие файлы будут обновлены
git fetch origin
git diff --name-only HEAD origin/main

# Изменить владельца только этих файлов (пример)
sudo chown $USER:$USER licenses/templates/licenses/*.html licenses/views.py mineral_licenses/settings.py

# Выполнить pull
git pull origin main

# Вернуть права для Apache
sudo chown www-data:www-data licenses/templates/licenses/*.html licenses/views.py mineral_licenses/settings.py
```

**Решение 3: Добавить пользователя в группу www-data (для постоянного доступа)**

```bash
# Добавить текущего пользователя в группу www-data
sudo usermod -aG www-data $USER

# Выйти и войти снова, чтобы изменения вступили в силу
# Или выполнить:
newgrp www-data

# Изменить права на файлы для группы
sudo chmod -R g+w /var/www/mineral_licenses

# Теперь pull должен работать
git pull origin main
```

**Рекомендация:** Используйте Решение 1 для разовых обновлений. Если вы регулярно обновляете сайт, рассмотрите Решение 3 для постоянного доступа.

### Проблема: Ошибка "Permission denied" при git fetch

**Симптомы:**
```
error: cannot open .git/FETCH_HEAD: Permission denied
# или
error: cannot lock ref 'HEAD': Permission denied
```

**Причина:** Директория проекта принадлежит пользователю `www-data` (для Apache), а вы работаете под другим пользователем. Git не может записать метаданные в директорию `.git`.

**Решение 1: Временно изменить владельца .git директории (рекомендуется)**

```bash
cd /var/www/mineral_licenses

# Проверить текущего пользователя
whoami

# Временно изменить владельца только .git директории
sudo chown -R $USER:$USER .git

# Теперь выполнить Git команды
git fetch origin
git pull origin main

# После обновления вернуть права обратно (опционально, но рекомендуется)
sudo chown -R www-data:www-data .git
```

**Решение 2: Изменить владельца всей директории проекта**

```bash
cd /var/www/mineral_licenses

# Изменить владельца всей директории на текущего пользователя
sudo chown -R $USER:$USER /var/www/mineral_licenses

# Выполнить обновление
git fetch origin
git pull origin main

# После обновления вернуть права для Apache (ВАЖНО!)
# Оставить права на запись для статики и media
sudo chown -R www-data:www-data /var/www/mineral_licenses/staticfiles
sudo chown -R www-data:www-data /mnt/media_storage
sudo chown -R www-data:www-data /var/www/mineral_licenses/media

# Для остальных файлов можно оставить вашего пользователя или вернуть www-data
# (в зависимости от того, кто должен иметь доступ)
```

**Решение 3: Добавить текущего пользователя в группу www-data**

```bash
# Добавить текущего пользователя в группу www-data
sudo usermod -aG www-data $USER

# Выйти и войти снова, чтобы изменения вступили в силу
# Или выполнить:
newgrp www-data

# Изменить права на .git для группы
sudo chmod -R g+w /var/www/mineral_licenses/.git

# Теперь Git команды должны работать
git fetch origin
```

**Рекомендация:** Используйте Решение 1 для разовых обновлений. Если вы регулярно обновляете сайт, рассмотрите Решение 3 для постоянного доступа.

### Проблема: Git pull выдает ошибку "Your local changes would be overwritten"

**Симптомы:**
```
error: Your local changes to the following files would be overwritten by merge:
        mineral_licenses/settings.py
Please commit your changes or stash them before you merge.
Aborting
```

**Причина:** На сервере есть локальные изменения в файлах, которые также изменены в новой версии из GitHub. Git не может автоматически объединить изменения.

**Решение 1: Сохранить изменения в stash (если локальные изменения не важны)**

```bash
# Посмотреть, что именно изменилось
git diff mineral_licenses/settings.py

# Если изменения не критичны, сохранить их в stash
git stash save "local changes before update $(date +%Y%m%d-%H%M%S)"

# Применить обновления
git pull origin main

# Если нужно, посмотреть сохраненные изменения
git stash list

# Если нужно восстановить сохраненные изменения (после обновления)
git stash pop
```

**Решение 2: Сохранить локальные изменения в отдельный файл (рекомендуется для settings.py)**

```bash
# Посмотреть, что изменилось
git diff mineral_licenses/settings.py

# Сохранить локальные изменения в отдельный файл
git diff mineral_licenses/settings.py > /tmp/settings_local_changes.patch

# Или сохранить весь файл как бэкап
cp mineral_licenses/settings.py mineral_licenses/settings.py.local_backup

# Отменить локальные изменения
git checkout -- mineral_licenses/settings.py

# Применить обновления
git pull origin main

# После обновления проверить, нужно ли восстановить локальные настройки
# (например, SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS из .env файла)
cat mineral_licenses/settings.py.local_backup
```

**Решение 3: Вручную объединить изменения (для важных настроек)**

```bash
# Сохранить текущую версию
cp mineral_licenses/settings.py mineral_licenses/settings.py.backup

# Посмотреть изменения
git diff mineral_licenses/settings.py

# Сохранить изменения в stash
git stash save "local settings changes"

# Применить обновления
git pull origin main

# Восстановить локальные изменения
git stash pop

# Если возникли конфликты, разрешить их вручную
# Отредактировать файл, оставив нужные настройки
nano mineral_licenses/settings.py

# После разрешения конфликтов
git add mineral_licenses/settings.py
git commit -m "Merge local settings with updates"
```

**Важно для settings.py:** Обычно на сервере в `settings.py` не должно быть локальных изменений, так как все настройки должны браться из `.env` файла. Если вы видите изменения в `settings.py`, проверьте:

1. Не хранятся ли секретные данные (SECRET_KEY, пароли) прямо в файле
2. Все ли настройки вынесены в `.env` файл
3. Можно ли эти изменения безопасно отменить

**Рекомендация:** Используйте Решение 2 - сохраните бэкап, отмените изменения, обновите код, затем проверьте, что все настройки из `.env` применяются корректно.

### Проблема: Миграции не применяются

**Симптомы:**
- Команда `python manage.py migrate` не применяет миграции
- Ошибки при применении миграций

**Решение:**
```bash
# Проверить, какие миграции есть и их статус
python manage.py showmigrations

# Посмотреть план применения миграций
python manage.py migrate --plan

# Попробовать применить конкретную миграцию
python manage.py migrate licenses 0002_license_polygon_data

# Если проблема с зависимостями миграций, применить все приложения:
python manage.py migrate --run-syncdb
```

**Важно:** Если вы видите "No migrations to apply" - это нормально! Это означает, что все миграции уже применены и база данных актуальна.

### Проблема: Ошибка "DATABASES is improperly configured"

**Симптомы:**
```
ImproperlyConfigured at /
settings.DATABASES is improperly configured. Please supply the ENGINE value.
```

**Причина:** Django не может найти настройки базы данных. Обычно это означает, что:
- Файл `.env` отсутствует или не загружается
- Переменная `DATABASE_URL` не установлена в `.env`
- Файл `.env` находится не в корне проекта

**Решение:**

```bash
cd /var/www/mineral_licenses

# 1. Проверить, существует ли файл .env
ls -la .env

# 2. Если файла нет, создать его
nano .env
```

**Содержимое файла .env (минимально необходимое):**

```env
SECRET_KEY='ваш_секретный_ключ_50_символов'
DEBUG=False
ALLOWED_HOSTS=192.168.23.58,ваш-домен.ru

# База данных (ОБЯЗАТЕЛЬНО!)
DATABASE_URL=postgresql://mineral_user:ВАШ_ПАРОЛЬ@localhost:5432/mineral_licenses
```

**Проверка:**

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Проверить конфигурацию Django
python manage.py check

# Если ошибка все еще есть, проверить, загружается ли .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DATABASE_URL:', os.getenv('DATABASE_URL'))"
```

**Если DATABASE_URL не выводится:**

1. Проверьте путь к файлу `.env` - он должен быть в `/var/www/mineral_licenses/.env`
2. Проверьте права доступа: `chmod 600 .env`
3. Проверьте, что в `settings.py` есть `load_dotenv()` в начале файла

**Важно:** После создания/обновления `.env` файла перезапустите Apache:
```bash
sudo systemctl restart apache2
```

### Проблема: Статические файлы не обновляются

**Решение:**
```bash
# Очистить старые статические файлы
rm -rf staticfiles/*

# Собрать заново
python manage.py collectstatic --noinput --clear

# Проверить права
sudo chown -R www-data:www-data staticfiles
sudo chmod -R 755 staticfiles
```

### Проблема: Apache не перезапускается

**Решение:**
```bash
# Проверить конфигурацию
sudo apache2ctl configtest

# Проверить логи
sudo tail -100 /var/log/apache2/error.log

# Попробовать перезагрузить вместо restart
sudo systemctl reload apache2

# Если не помогает, проверить процессы
ps aux | grep apache2
sudo killall apache2
sudo systemctl start apache2
```

### Проблема: Ошибка "ModuleNotFoundError" после обновления

**Решение:**
```bash
# Убедиться, что виртуальное окружение активировано
source venv/bin/activate

# Переустановить зависимости
pip install -r requirements.txt --force-reinstall

# Проверить установленные пакеты
pip list | grep название_модуля
```

---

## Контрольный список обновления

Перед началом:
- [ ] Создан бэкап базы данных
- [ ] Сохранена текущая версия кода (commit hash)
- [ ] Проверен статус сервисов (Apache, PostgreSQL)

Во время обновления:
- [ ] Код обновлен из GitHub (git pull)
- [ ] Зависимости обновлены (pip install -r requirements.txt)
- [ ] Миграции применены (python manage.py migrate)
- [ ] Статические файлы собраны (collectstatic)
- [ ] Apache перезапущен

После обновления:
- [ ] Сайт доступен и работает
- [ ] Логи не содержат критических ошибок
- [ ] Функциональность проверена в браузере
- [ ] База данных содержит актуальные данные

---

## Дополнительные рекомендации

1. **Обновляйте в нерабочее время** - чтобы минимизировать влияние на пользователей
2. **Тестируйте на тестовом сервере** - если есть возможность, сначала обновите тестовый сервер
3. **Читайте changelog** - перед обновлением проверьте, какие изменения были внесены
4. **Мониторьте логи** - после обновления следите за логами в течение нескольких часов
5. **Держите бэкапы** - храните несколько последних бэкапов базы данных

---

## Полезные команды для мониторинга

```bash
# Мониторинг логов в реальном времени
sudo tail -f /var/log/apache2/mineral_licenses_error.log
sudo tail -f /var/log/apache2/mineral_licenses_access.log

# Проверка использования ресурсов
htop
free -h
df -h

# Проверка процессов Apache
ps aux | grep apache2

# Проверка открытых портов
sudo netstat -tlnp | grep apache
```

---

**Успешного обновления!**

Если возникли проблемы, обратитесь к разделу "Откат изменений" или проверьте логи сервисов.

