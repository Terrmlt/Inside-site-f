# Руководство по подключению LDAP аутентификации

Это подробное руководство по настройке LDAP аутентификации для системы управления лицензиями на недропользование.

## Содержание

1. [Введение](#введение)
2. [Предварительные требования](#предварительные-требования)
3. [Быстрый старт](#быстрый-старт)
4. [Подробная настройка](#подробная-настройка)
5. [Примеры конфигурации](#примеры-конфигурации)
6. [Тестирование](#тестирование)
7. [Устранение неполадок](#устранение-неполадок)
8. [FAQ](#faq)

---

## Введение

LDAP (Lightweight Directory Access Protocol) аутентификация позволяет пользователям входить в систему используя свои корпоративные учётные данные из Active Directory, OpenLDAP или других LDAP-серверов.

### Преимущества LDAP аутентификации:
- ✅ Единый вход (Single Sign-On) - пользователи используют свои корпоративные учётные данные
- ✅ Централизованное управление доступом
- ✅ Автоматическая синхронизация данных пользователей
- ✅ Управление правами на основе групп LDAP
- ✅ Повышенная безопасность

---

## Предварительные требования

Перед началом убедитесь, что у вас есть:

1. **Доступ к LDAP серверу** (Active Directory, OpenLDAP и т.д.)
2. **Учетные данные для подключения** (bind DN и пароль)
3. **Информация о структуре LDAP**:
   - Базовый DN (Distinguished Name)
   - DN для поиска пользователей
   - DN для поиска групп
   - Атрибут для идентификации пользователей (uid, sAMAccountName и т.д.)

4. **Необходимые пакеты уже установлены**:
   ```bash
   # Пакеты уже установлены в проекте:
   # - django-auth-ldap (5.2.0)
   # - python-ldap (3.4.5)
   ```

---

## Быстрый старт

### Шаг 1: Получите информацию о вашем LDAP сервере

Свяжитесь с вашим системным администратором и получите:

```
LDAP Server URL: ldap://ldap.example.com:389
Bind DN: cn=admin,dc=example,dc=com
Bind Password: ********
Base DN для пользователей: ou=users,dc=example,dc=com
Base DN для групп: ou=groups,dc=example,dc=com
Атрибут пользователя: uid  (или sAMAccountName для AD)
```

### Шаг 2: Настройте файл конфигурации

Откройте файл `mineral_licenses/settings_ldap.py` и измените следующие параметры:

```python
# ОСНОВНЫЕ НАСТРОЙКИ
AUTH_LDAP_SERVER_URI = "ldap://your-ldap-server.example.com:389"
AUTH_LDAP_BIND_DN = "cn=admin,dc=example,dc=com"
AUTH_LDAP_BIND_PASSWORD = "your_bind_password"

# ПОИСК ПОЛЬЗОВАТЕЛЕЙ
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=users,dc=example,dc=com",  # Ваш базовый DN
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"  # Для AD: "(sAMAccountName=%(user)s)"
)
```

### Шаг 3: Активируйте LDAP

В Replit Secrets или в файле `.env` добавьте:

```bash
USE_LDAP=true
```

### Шаг 4: Перезапустите приложение

Перезапустите Django сервер. В консоли должно появиться:
```
✓ LDAP authentication enabled
```

### Шаг 5: Проверьте работу

Попробуйте войти используя LDAP учётные данные на странице `/admin/`

---

## Подробная настройка

### Структура конфигурации

Настройки LDAP разделены на несколько секций:

#### 1. Основные настройки подключения

```python
# URL вашего LDAP сервера
AUTH_LDAP_SERVER_URI = "ldap://ldap.example.com:389"

# Учетные данные для подключения
AUTH_LDAP_BIND_DN = "cn=admin,dc=example,dc=com"
AUTH_LDAP_BIND_PASSWORD = "password"

# Опции подключения
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_DEBUG_LEVEL: 0,  # Уровень отладки
    ldap.OPT_REFERRALS: 0,    # Отключить referrals (для AD)
}
```

**Порты:**
- `389` - стандартный LDAP (незащищенный)
- `636` - LDAPS (SSL/TLS)
- `3268` - Global Catalog в AD (незащищенный)
- `3269` - Global Catalog в AD (SSL/TLS)

#### 2. Поиск пользователей

```python
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=users,dc=example,dc=com",  # Базовый DN для поиска
    ldap.SCOPE_SUBTREE,             # Глубина поиска
    "(uid=%(user)s)"                # Фильтр поиска
)
```

**Параметры глубины поиска:**
- `ldap.SCOPE_BASE` - только базовый объект
- `ldap.SCOPE_ONELEVEL` - только прямые потомки
- `ldap.SCOPE_SUBTREE` - рекурсивно все потомки (рекомендуется)

**Популярные фильтры:**
- OpenLDAP: `(uid=%(user)s)`
- Active Directory: `(sAMAccountName=%(user)s)`
- Email: `(mail=%(user)s)`

#### 3. Маппинг атрибутов

```python
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",   # Имя из LDAP → first_name в Django
    "last_name": "sn",           # Фамилия
    "email": "mail"              # Email
}
```

**Стандартные LDAP атрибуты:**
- `givenName` - имя
- `sn` (surname) - фамилия
- `mail` - email
- `telephoneNumber` - телефон
- `title` - должность
- `department` - отдел

#### 4. Работа с группами

```python
# Поиск групп
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "ou=groups,dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(objectClass=groupOfNames)"  # Для AD: "(objectClass=group)"
)

# Тип групп
from django_auth_ldap.config import GroupOfNamesType
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()

# Назначение прав на основе групп
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_superuser": "cn=admins,ou=groups,dc=example,dc=com",
    "is_staff": "cn=staff,ou=groups,dc=example,dc=com",
}
```

**Типы групп:**
- `GroupOfNamesType()` - стандартные LDAP группы
- `PosixGroupType()` - POSIX группы
- `ActiveDirectoryGroupType()` - группы Active Directory
- `NestedGroupOfNamesType()` - вложенные группы

#### 5. SSL/TLS подключение

Для безопасного подключения:

```python
AUTH_LDAP_SERVER_URI = "ldaps://ldap.example.com:636"

AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,  # Не проверять сертификат
}

# Или для StartTLS:
AUTH_LDAP_START_TLS = True
```

---

## Примеры конфигурации

### Пример 1: Active Directory (Microsoft)

```python
import ldap
from django_auth_ldap.config import LDAPSearch

# Подключение к AD
AUTH_LDAP_SERVER_URI = "ldap://dc.company.local:389"
AUTH_LDAP_BIND_DN = "CN=django_service,OU=Service Accounts,DC=company,DC=local"
AUTH_LDAP_BIND_PASSWORD = "SecurePassword123!"

# Поиск пользователей
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "OU=Employees,DC=company,DC=local",
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)"  # AD использует sAMAccountName
)

# Маппинг атрибутов
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

# Поиск групп
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "OU=Security Groups,DC=company,DC=local",
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)"
)

# Права на основе групп
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_superuser": "CN=Domain Admins,OU=Security Groups,DC=company,DC=local",
    "is_staff": "CN=IT Department,OU=Security Groups,DC=company,DC=local",
}

# Важно для AD - отключить referrals
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,
}
```

### Пример 2: OpenLDAP

```python
import ldap
from django_auth_ldap.config import LDAPSearch, PosixGroupType

# Подключение к OpenLDAP
AUTH_LDAP_SERVER_URI = "ldap://ldap.example.org:389"
AUTH_LDAP_BIND_DN = "cn=readonly,dc=example,dc=org"
AUTH_LDAP_BIND_PASSWORD = "readonly_password"

# Поиск пользователей
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=people,dc=example,dc=org",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"  # OpenLDAP обычно использует uid
)

# Маппинг атрибутов
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

# POSIX группы
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "ou=groups,dc=example,dc=org",
    ldap.SCOPE_SUBTREE,
    "(objectClass=posixGroup)"
)

AUTH_LDAP_GROUP_TYPE = PosixGroupType(name_attr="cn")

# Права на основе групп
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_superuser": "cn=admins,ou=groups,dc=example,dc=org",
    "is_staff": "cn=staff,ou=groups,dc=example,dc=org",
}
```

### Пример 3: FreeIPA

```python
import ldap
from django_auth_ldap.config import LDAPSearch

AUTH_LDAP_SERVER_URI = "ldap://ipa.example.org:389"
AUTH_LDAP_BIND_DN = "uid=bind_user,cn=users,cn=accounts,dc=example,dc=org"
AUTH_LDAP_BIND_PASSWORD = "bind_password"

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "cn=users,cn=accounts,dc=example,dc=org",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"
)

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}
```

---

## Тестирование

### Метод 1: Через Django shell

```bash
# Запустите Django shell
python manage.py shell
```

```python
# В shell выполните:
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import User

backend = LDAPBackend()

# Попробуйте аутентифицировать пользователя
user = backend.authenticate(request=None, username='testuser', password='testpassword')

if user:
    print(f"✓ Успешная аутентификация: {user.username}")
    print(f"  Имя: {user.first_name} {user.last_name}")
    print(f"  Email: {user.email}")
    print(f"  Staff: {user.is_staff}")
    print(f"  Superuser: {user.is_superuser}")
else:
    print("✗ Аутентификация не удалась")
```

### Метод 2: Через командную строку

Создайте тестовый скрипт `test_ldap.py`:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mineral_licenses.settings')
django.setup()

from django_auth_ldap.backend import LDAPBackend

def test_ldap_auth(username, password):
    backend = LDAPBackend()
    user = backend.authenticate(request=None, username=username, password=password)
    
    if user:
        print(f"✓ Успешная аутентификация")
        print(f"  Username: {user.username}")
        print(f"  Name: {user.first_name} {user.last_name}")
        print(f"  Email: {user.email}")
        return True
    else:
        print("✗ Аутентификация не удалась")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python test_ldap.py <username> <password>")
        sys.exit(1)
    
    test_ldap_auth(sys.argv[1], sys.argv[2])
```

Запустите:
```bash
python test_ldap.py your_username your_password
```

### Метод 3: Через веб-интерфейс

1. Откройте `/admin/`
2. Введите LDAP логин и пароль
3. Если вход успешен - LDAP настроен правильно

---

## Устранение неполадок

### Включение отладки LDAP

Добавьте в `settings_ldap.py`:

```python
import logging

logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)
```

Теперь в консоли будут выводиться подробные логи LDAP операций.

### Распространённые ошибки

#### 1. "Server not found" или "Connection refused"

**Причина:** Неверный URL сервера или сервер недоступен

**Решение:**
```bash
# Проверьте доступность сервера
ping ldap.example.com

# Проверьте порт
telnet ldap.example.com 389
```

#### 2. "Invalid credentials" для bind DN

**Причина:** Неверные учётные данные для подключения

**Решение:**
- Проверьте bind DN и пароль
- Убедитесь, что пользователь имеет права на поиск

#### 3. "No such object"

**Причина:** Неверный базовый DN

**Решение:**
```bash
# Используйте ldapsearch для проверки
ldapsearch -x -H ldap://ldap.example.com -D "cn=admin,dc=example,dc=com" -W -b "dc=example,dc=com"
```

#### 4. Пользователь не может войти, хотя LDAP работает

**Причина:** Неверный фильтр поиска

**Решение:**
- Для AD используйте `(sAMAccountName=%(user)s)`
- Для OpenLDAP используйте `(uid=%(user)s)`
- Проверьте атрибуты: `ldapsearch ... "(uid=username)"`

#### 5. "Referral" ошибки в Active Directory

**Причина:** AD возвращает referrals

**Решение:**
```python
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,  # Отключить referrals
}
```

#### 6. SSL/TLS ошибки

**Причина:** Проблемы с сертификатом

**Решение:**
```python
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
}
```

---

## FAQ

### Можно ли использовать LDAP и локальные аккаунты одновременно?

**Да!** По умолчанию система сначала проверяет LDAP, затем локальную БД Django:

```python
AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',       # Сначала LDAP
    'django.contrib.auth.backends.ModelBackend',  # Затем Django
]
```

### Что если LDAP сервер недоступен?

Если LDAP сервер недоступен, пользователи с локальными аккаунтами смогут войти через второй backend (ModelBackend).

### Как создать локального суперпользователя на случай проблем с LDAP?

```bash
python manage.py createsuperuser
```

Этот пользователь сможет войти даже если LDAP не работает.

### Синхронизируются ли пароли в Django БД?

**Нет.** Пароли не сохраняются в Django. Аутентификация всегда происходит через LDAP.

### Как отключить LDAP временно?

В Replit Secrets или `.env` измените:
```bash
USE_LDAP=false
```

Или удалите переменную `USE_LDAP` полностью.

### Можно ли использовать несколько LDAP серверов?

Да, но потребуется создать custom backend. Базовая конфигурация поддерживает один сервер.

### Нужно ли создавать пользователей в Django вручную?

**Нет.** При первом входе через LDAP пользователь автоматически создаётся в Django.

---

## Дополнительные ресурсы

- [Официальная документация django-auth-ldap](https://django-auth-ldap.readthedocs.io/)
- [Python-LDAP документация](https://www.python-ldap.org/)
- [LDAP Wiki](https://ldapwiki.com/)
- [Active Directory LDAP](https://docs.microsoft.com/en-us/windows/win32/ad/active-directory-ldap)

---

## Поддержка

Если у вас возникли проблемы:

1. Включите отладку LDAP (см. раздел "Устранение неполадок")
2. Проверьте логи Django
3. Используйте `ldapsearch` для тестирования подключения напрямую
4. Обратитесь к системному администратору LDAP сервера

---

**Версия документа:** 1.0  
**Последнее обновление:** Ноябрь 2025
