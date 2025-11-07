# 🗄️ Шпаргалка по PostgreSQL для проекта

## 🚀 Быстрый старт

### Запуск PostgreSQL

**Windows:**
```cmd
# Проверка статуса службы
services.msc
# Найдите "postgresql-x64-16" → должен быть запущен

# Или через командную строку (от администратора)
net start postgresql-x64-16
```

**macOS:**
```bash
# Запуск
brew services start postgresql@16

# Остановка
brew services stop postgresql@16

# Статус
brew services list | grep postgresql
```

**Linux:**
```bash
# Запуск
sudo systemctl start postgresql

# Остановка
sudo systemctl stop postgresql

# Статус
sudo systemctl status postgresql

# Автозапуск при загрузке
sudo systemctl enable postgresql
```

---

## 🔌 Подключение к PostgreSQL

### Через командную строку (psql)

```bash
# Подключение как пользователь postgres к любой БД
psql -U postgres

# Подключение к конкретной базе данных
psql -U postgres -d mineral_licenses

# Подключение с указанием хоста и порта
psql -h localhost -p 5432 -U postgres -d mineral_licenses

# Подключение и выполнение команды
psql -U postgres -c "SELECT version();"
```

### Через pgAdmin 4 (графический интерфейс)

1. Запустите pgAdmin 4
2. Servers → PostgreSQL 16 → правый клик → Connect
3. Введите пароль пользователя postgres
4. Databases → mineral_licenses

---

## 📊 Основные команды в psql

### Команды просмотра

```sql
-- Список всех баз данных
\l
\list

-- Подключение к базе данных
\c mineral_licenses
\connect mineral_licenses

-- Список всех таблиц в текущей БД
\dt

-- Список таблиц с подробной информацией
\dt+

-- Описание структуры таблицы
\d licenses_license
\d+ licenses_license

-- Список всех схем
\dn

-- Список пользователей/ролей
\du

-- Текущая база данных и пользователь
\conninfo

-- Справка по SQL командам
\h SELECT
\h CREATE TABLE

-- Справка по командам psql
\?

-- Выход из psql
\q
```

---

## 🔧 Управление базами данных

### Создание и удаление

```sql
-- Создание базы данных
CREATE DATABASE mineral_licenses;

-- Создание с указанием владельца
CREATE DATABASE mineral_licenses OWNER postgres;

-- Создание с кодировкой UTF-8
CREATE DATABASE mineral_licenses 
    ENCODING 'UTF8' 
    LC_COLLATE 'ru_RU.UTF-8' 
    LC_CTYPE 'ru_RU.UTF-8';

-- Удаление базы данных (ОСТОРОЖНО!)
DROP DATABASE mineral_licenses;

-- Переименование базы данных
ALTER DATABASE mineral_licenses RENAME TO new_name;
```

---

## 👥 Управление пользователями

### Создание пользователей

```sql
-- Создание пользователя с паролем
CREATE USER licenses_user WITH PASSWORD 'secure_password123';

-- Создание пользователя с правами
CREATE USER admin_user WITH PASSWORD 'admin123' 
    CREATEDB CREATEROLE;

-- Дать все права на базу данных пользователю
GRANT ALL PRIVILEGES ON DATABASE mineral_licenses TO licenses_user;

-- Дать права на все таблицы в схеме public
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO licenses_user;

-- Сделать пользователя владельцем базы данных
ALTER DATABASE mineral_licenses OWNER TO licenses_user;

-- Изменить пароль пользователя
ALTER USER postgres WITH PASSWORD 'new_password';

-- Удалить пользователя
DROP USER licenses_user;
```

---

## 📋 Работа с данными (для проверки)

### Просмотр данных

```sql
-- Подключиться к БД
\c mineral_licenses

-- Посмотреть первые 10 лицензий
SELECT * FROM licenses_license LIMIT 10;

-- Посмотреть количество лицензий
SELECT COUNT(*) FROM licenses_license;

-- Посмотреть лицензии по статусу
SELECT license_number, status, region 
FROM licenses_license 
WHERE status = 'active';

-- Посмотреть все документы
SELECT * FROM licenses_document;

-- Посмотреть лицензии с документами (JOIN)
SELECT l.license_number, d.name, d.file_type
FROM licenses_license l
JOIN licenses_document d ON l.id = d.license_id;
```

### Очистка данных (ОСТОРОЖНО!)

```sql
-- Удалить все записи из таблицы
TRUNCATE TABLE licenses_license CASCADE;

-- Удалить все записи с условием
DELETE FROM licenses_license WHERE status = 'expired';

-- Сбросить автоинкремент ID
ALTER SEQUENCE licenses_license_id_seq RESTART WITH 1;
```

---

## 🔍 Диагностика и отладка

### Информация о подключениях

```sql
-- Текущие активные подключения
SELECT * FROM pg_stat_activity;

-- Подключения к конкретной БД
SELECT * FROM pg_stat_activity 
WHERE datname = 'mineral_licenses';

-- Количество подключений по базам
SELECT datname, count(*) 
FROM pg_stat_activity 
GROUP BY datname;

-- Завершить подключение (по PID)
SELECT pg_terminate_backend(12345);
```

### Размеры баз данных и таблиц

```sql
-- Размер базы данных
SELECT pg_size_pretty(pg_database_size('mineral_licenses'));

-- Размеры всех баз данных
SELECT datname, pg_size_pretty(pg_database_size(datname))
FROM pg_database
ORDER BY pg_database_size(datname) DESC;

-- Размер таблицы
SELECT pg_size_pretty(pg_total_relation_size('licenses_license'));

-- Размеры всех таблиц
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Проверка версии и расширений

```sql
-- Версия PostgreSQL
SELECT version();

-- Список установленных расширений
\dx

-- Установить расширение PostGIS (если нужно для геоданных)
CREATE EXTENSION postgis;
```

---

## 📤 Резервное копирование и восстановление

### Создание backup

**Вся база данных:**
```bash
# Windows (в командной строке)
pg_dump -U postgres -d mineral_licenses -f backup.sql

# С сжатием
pg_dump -U postgres -d mineral_licenses -F c -f backup.dump

# Только данные (без структуры)
pg_dump -U postgres -d mineral_licenses --data-only -f data.sql

# Только структура (без данных)
pg_dump -U postgres -d mineral_licenses --schema-only -f schema.sql
```

**Отдельная таблица:**
```bash
pg_dump -U postgres -d mineral_licenses -t licenses_license -f licenses_backup.sql
```

### Восстановление из backup

```bash
# Из SQL файла
psql -U postgres -d mineral_licenses -f backup.sql

# Из dump файла
pg_restore -U postgres -d mineral_licenses backup.dump

# Создать новую БД и восстановить
createdb -U postgres mineral_licenses_restore
pg_restore -U postgres -d mineral_licenses_restore backup.dump
```

---

## ⚙️ Конфигурация PostgreSQL для проекта Django

### Проверка настроек подключения

```sql
-- Показать максимум подключений
SHOW max_connections;

-- Показать текущий порт
SHOW port;

-- Показать директорию данных
SHOW data_directory;

-- Показать файл конфигурации
SHOW config_file;
```

### Рекомендуемые настройки в postgresql.conf

```ini
# Для локальной разработки:
max_connections = 100
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB

# Логирование (для отладки)
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = 'all'
```

**Где найти postgresql.conf:**
- Windows: `C:\Program Files\PostgreSQL\16\data\postgresql.conf`
- macOS: `/opt/homebrew/var/postgresql@16/postgresql.conf`
- Linux: `/etc/postgresql/16/main/postgresql.conf`

**После изменений перезапустите PostgreSQL!**

---

## 🆘 Решение частых проблем

### Проблема: "password authentication failed"

```bash
# Проверка текущего пароля
psql -U postgres

# Если не помните пароль - сбросьте через pg_hba.conf:
# 1. Откройте файл pg_hba.conf
# 2. Найдите строку: host all all 127.0.0.1/32 md5
# 3. Замените md5 на trust
# 4. Перезапустите PostgreSQL
# 5. Подключитесь без пароля и смените его:

psql -U postgres
ALTER USER postgres WITH PASSWORD 'новый_пароль';

# 6. Верните md5 обратно в pg_hba.conf
# 7. Перезапустите PostgreSQL
```

### Проблема: "could not connect to server"

```bash
# Проверка, запущен ли PostgreSQL
# Windows:
services.msc
# Найдите postgresql-x64-16

# macOS:
brew services list | grep postgresql

# Linux:
sudo systemctl status postgresql

# Проверка порта
netstat -an | grep 5432
# или
lsof -i :5432
```

### Проблема: "database does not exist"

```sql
-- Проверьте список баз данных
\l

-- Если нет mineral_licenses - создайте
CREATE DATABASE mineral_licenses;
```

### Проблема: "permission denied for schema public"

```sql
-- Дайте права пользователю
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
```

---

## 📚 Полезные ссылки

- Официальная документация: https://www.postgresql.org/docs/
- Скачать PostgreSQL: https://www.postgresql.org/download/
- pgAdmin 4: https://www.pgadmin.org/
- PostGIS (геоданные): https://postgis.net/

---

## ✅ Чеклист перед запуском Django проекта

- [ ] PostgreSQL установлен и запущен
- [ ] База данных `mineral_licenses` создана
- [ ] Пользователь имеет права на базу данных
- [ ] Порт 5432 доступен
- [ ] Файл `.env` содержит правильные данные подключения
- [ ] `psql -U postgres -d mineral_licenses` подключается успешно

**Команда для полной проверки:**
```bash
psql -U postgres -d mineral_licenses -c "SELECT 'PostgreSQL готов к работе!' as status;"
```

Если увидели "PostgreSQL готов к работе!" → всё настроено правильно! ✅
