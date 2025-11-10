# 🔐 Настройка мультидоменной LDAP аутентификации

## 🎯 Введение

Система поддерживает **авторизацию через несколько доменов LDAP** одновременно с двумя режимами работы:

- **Автоопределение домена** - система пробует все настроенные домены по очереди
- **Выбор домена пользователем** - пользователь выбирает свой домен на странице входа

---

## ⚙️ Быстрая настройка

### Шаг 1: Активируйте LDAP

В файле `.env` добавьте:
```env
USE_LDAP=true
```

### Шаг 2: Настройте домены

Добавьте параметры для каждого домена в `.env`:

```env
# Домен 1
LDAP_DOMAIN1_SERVER_URI=ldap://dc01.company.local:389
LDAP_DOMAIN1_BIND_DN=CN=ldap-reader,OU=Service,DC=company,DC=local
LDAP_DOMAIN1_BIND_PASSWORD=Password123
LDAP_DOMAIN1_USER_SEARCH_BASE=OU=Users,DC=company,DC=local
LDAP_DOMAIN1_USER_SEARCH_FILTER=(sAMAccountName=%(user)s)

# Домен 2 (опционально)
LDAP_DOMAIN2_SERVER_URI=ldap://dc-spb.holding.ru:389
LDAP_DOMAIN2_BIND_DN=CN=svc-ldap,OU=Service,DC=holding,DC=ru
LDAP_DOMAIN2_BIND_PASSWORD=SecurePass456
LDAP_DOMAIN2_USER_SEARCH_BASE=OU=Users,DC=holding,DC=ru
LDAP_DOMAIN2_USER_SEARCH_FILTER=(sAMAccountName=%(user)s)

# Домен 3 (опционально)
LDAP_DOMAIN3_SERVER_URI=ldap://ldap.subsidiary.com:389
LDAP_DOMAIN3_BIND_DN=cn=admin,dc=subsidiary,dc=com
LDAP_DOMAIN3_BIND_PASSWORD=OpenLDAP789
LDAP_DOMAIN3_USER_SEARCH_BASE=ou=people,dc=subsidiary,dc=com
LDAP_DOMAIN3_USER_SEARCH_FILTER=(uid=%(user)s)
```

### Шаг 3: Измените названия доменов в форме

Откройте `licenses/templates/licenses/login.html` и обновите названия доменов:

```html
<select class="form-control form-select-icon" id="domain" name="domain">
    <option value="">Автоопределение</option>
    <option value="domain1">Головной офис (Москва)</option>
    <option value="domain2">Холдинг (Санкт-Петербург)</option>
    <option value="domain3">Филиал (Казань)</option>
</select>
```

**Важно:** Не меняйте `value="domain1"`, `value="domain2"` и т.д. - меняйте только текст между тегами!

### Шаг 4: Перезапустите сервер

```bash
uv run python manage.py runserver
```

Вы увидите:
```
✓ LDAP authentication enabled - 3 domain(s) configured
```

---

## 📋 Получение параметров LDAP

Обратитесь к системному администратору за следующими данными:

| Параметр | Описание | Пример |
|----------|----------|---------|
| **SERVER_URI** | Адрес LDAP сервера | `ldap://dc.company.local:389` |
| **BIND_DN** | Служебная учетная запись | `CN=ldap-reader,OU=Service,DC=company,DC=local` |
| **BIND_PASSWORD** | Пароль служебной УЗ | `SecurePassword123` |
| **USER_SEARCH_BASE** | База поиска пользователей | `OU=Users,DC=company,DC=local` |
| **USER_SEARCH_FILTER** | Фильтр поиска | `(sAMAccountName=%(user)s)` для AD<br>`(uid=%(user)s)` для OpenLDAP |

---

## 🧪 Тестирование

### Через веб-интерфейс:

1. Откройте `http://127.0.0.1:8000/login/`
2. Введите логин и пароль
3. Выберите домен или оставьте "Автоопределение"
4. Нажмите "Войти"

### Через Python скрипт:

Создайте файл `test_ldap_multi.py`:

```python
import ldap
import os
from dotenv import load_dotenv

load_dotenv()

# Тест домена 1
server = os.getenv('LDAP_DOMAIN1_SERVER_URI')
bind_dn = os.getenv('LDAP_DOMAIN1_BIND_DN')
bind_pw = os.getenv('LDAP_DOMAIN1_BIND_PASSWORD')
search_base = os.getenv('LDAP_DOMAIN1_USER_SEARCH_BASE')

try:
    conn = ldap.initialize(server)
    conn.set_option(ldap.OPT_REFERRALS, 0)
    conn.simple_bind_s(bind_dn, bind_pw)
    print(f"✅ Домен 1: подключение успешно к {server}")
    conn.unbind_s()
except Exception as e:
    print(f"❌ Домен 1: ошибка - {e}")
```

Запуск:
```bash
uv run python test_ldap_multi.py
```

---

## ⚠️ Решение частых проблем

### Проблема: "LDAP server is unavailable"
**Решение:**
```bash
# Проверьте доступность сервера
ping dc.company.local
telnet dc.company.local 389
```

### Проблема: "Invalid credentials"
**Решение:** Проверьте правильность `BIND_DN` и `BIND_PASSWORD` в `.env`

### Проблема: "User not found"
**Решение:** Убедитесь, что `USER_SEARCH_BASE` включает OU где находятся пользователи

### Проблема: Медленная авторизация при автоопределении
**Решение:** Попросите пользователей выбирать свой домен вручную из списка

---

## 📚 Примеры конфигурации

### Один домен Active Directory:
```env
USE_LDAP=true
LDAP_DOMAIN1_SERVER_URI=ldap://dc.company.local:389
LDAP_DOMAIN1_BIND_DN=CN=svc-ldap,OU=Service,DC=company,DC=local
LDAP_DOMAIN1_BIND_PASSWORD=Password123
LDAP_DOMAIN1_USER_SEARCH_BASE=OU=Users,DC=company,DC=local
LDAP_DOMAIN1_USER_SEARCH_FILTER=(sAMAccountName=%(user)s)
```

### Три домена (смешанная среда):
```env
USE_LDAP=true

# AD Домен 1
LDAP_DOMAIN1_SERVER_URI=ldap://dc-msk.company.ru:389
LDAP_DOMAIN1_BIND_DN=CN=ldap-reader,DC=company,DC=ru
LDAP_DOMAIN1_BIND_PASSWORD=MskPass123
LDAP_DOMAIN1_USER_SEARCH_BASE=OU=Moscow,DC=company,DC=ru
LDAP_DOMAIN1_USER_SEARCH_FILTER=(sAMAccountName=%(user)s)

# AD Домен 2
LDAP_DOMAIN2_SERVER_URI=ldap://dc-spb.company.ru:389
LDAP_DOMAIN2_BIND_DN=CN=ldap-reader,DC=spb,DC=company,DC=ru
LDAP_DOMAIN2_BIND_PASSWORD=SpbPass456
LDAP_DOMAIN2_USER_SEARCH_BASE=OU=Users,DC=spb,DC=company,DC=ru
LDAP_DOMAIN2_USER_SEARCH_FILTER=(sAMAccountName=%(user)s)

# OpenLDAP Домен 3
LDAP_DOMAIN3_SERVER_URI=ldap://ldap.subsidiary.com:389
LDAP_DOMAIN3_BIND_DN=cn=admin,dc=subsidiary,dc=com
LDAP_DOMAIN3_BIND_PASSWORD=LdapPass789
LDAP_DOMAIN3_USER_SEARCH_BASE=ou=people,dc=subsidiary,dc=com
LDAP_DOMAIN3_USER_SEARCH_FILTER=(uid=%(user)s)
```

### LDAPS (защищенное подключение):
```env
USE_LDAP=true
LDAP_DOMAIN1_SERVER_URI=ldaps://dc.company.local:636
LDAP_DOMAIN1_BIND_DN=CN=svc-ldap,OU=Service,DC=company,DC=local
LDAP_DOMAIN1_BIND_PASSWORD=SecurePassword
LDAP_DOMAIN1_USER_SEARCH_BASE=OU=Users,DC=company,DC=local
LDAP_DOMAIN1_USER_SEARCH_FILTER=(sAMAccountName=%(user)s)
```

---

## ✅ Проверочный чеклист

Перед запуском убедитесь:

- [ ] `USE_LDAP=true` установлено в `.env`
- [ ] Настроены параметры хотя бы одного домена
- [ ] Служебная учетка имеет права на чтение LDAP каталога
- [ ] LDAP сервер доступен по сети
- [ ] Обновлены названия доменов в `login.html`
- [ ] Сервер Django перезапущен
- [ ] Проверен вход с реальными учетными данными

---

## 📖 Дополнительные ресурсы

- **Полная документация LDAP:** `LDAP_SETUP.md`
- **Развертывание на ПК:** `DEPLOYMENT_LOCAL.md`
- **Проектная документация:** `replit.md`

**Версия:** 2.0 (Мультидоменная поддержка)  
**Дата:** Январь 2025
