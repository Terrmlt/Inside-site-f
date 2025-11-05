"""
Настройки LDAP аутентификации для Django
==========================================

Этот файл содержит шаблоны настроек для интеграции Django с LDAP сервером.
По умолчанию LDAP выключен. Для активации установите переменную окружения:
    USE_LDAP=true

ВАЖНО: Этот файл импортируется в settings.py ТОЛЬКО если USE_LDAP=true
"""

import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

# =============================================================================
# ОСНОВНЫЕ НАСТРОЙКИ LDAP
# =============================================================================

# URL вашего LDAP сервера
# Примеры:
#   - Active Directory: ldap://dc.example.com:389 или ldaps://dc.example.com:636 (SSL)
#   - OpenLDAP: ldap://ldap.example.com:389
AUTH_LDAP_SERVER_URI = "ldap://your-ldap-server.example.com:389"

# Учетные данные для подключения к LDAP (bind credentials)
# Можно оставить пустым для анонимного доступа (если ваш LDAP это разрешает)
AUTH_LDAP_BIND_DN = "cn=admin,dc=example,dc=com"
AUTH_LDAP_BIND_PASSWORD = "your_bind_password"

# =============================================================================
# ПОИСК ПОЛЬЗОВАТЕЛЕЙ
# =============================================================================

# Базовый DN для поиска пользователей
# Примеры:
#   - Active Directory: "ou=Users,dc=company,dc=com"
#   - OpenLDAP: "ou=people,dc=example,dc=com"
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=users,dc=example,dc=com",  # Базовый DN
    ldap.SCOPE_SUBTREE,  # Глубина поиска (SCOPE_SUBTREE = включая подразделы)
    "(uid=%(user)s)"  # Фильтр поиска. Для AD используйте: "(sAMAccountName=%(user)s)"
)

# =============================================================================
# МАППИНГ АТРИБУТОВ ПОЛЬЗОВАТЕЛЯ
# =============================================================================

# Соответствие между атрибутами Django User и LDAP
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",      # Имя
    "last_name": "sn",              # Фамилия
    "email": "mail"                 # Email
}

# Для Active Directory также популярны:
# AUTH_LDAP_USER_ATTR_MAP = {
#     "first_name": "givenName",
#     "last_name": "sn",
#     "email": "mail",
#     "username": "sAMAccountName"
# }

# =============================================================================
# ГРУППЫ И ПРАВА ДОСТУПА
# =============================================================================

# Базовый DN для поиска групп
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "ou=groups,dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(objectClass=groupOfNames)"  # Для AD используйте: "(objectClass=group)"
)

# Тип групп
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()

# Автоматическое назначение прав на основе LDAP групп
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    # Пользователи из группы "admins" получают статус superuser
    "is_superuser": "cn=admins,ou=groups,dc=example,dc=com",
    
    # Пользователи из группы "staff" получают доступ в админ-панель
    "is_staff": "cn=staff,ou=groups,dc=example,dc=com",
}

# Можно также назначать права Django на основе LDAP групп
# AUTH_LDAP_FIND_GROUP_PERMS = True

# =============================================================================
# СОЗДАНИЕ И ОБНОВЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ
# =============================================================================

# Автоматически создавать пользователя при первом входе
AUTH_LDAP_ALWAYS_UPDATE_USER = True

# Если пользователь не найден в LDAP, не удалять его из Django
# (полезно для сохранения локальных аккаунтов)
AUTH_LDAP_MIRROR_GROUPS = False

# =============================================================================
# ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
# =============================================================================

# Настройки подключения к LDAP
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_DEBUG_LEVEL: 0,  # Уровень отладки (0 = выключено)
    ldap.OPT_REFERRALS: 0,  # Отключить referrals (нужно для некоторых AD)
}

# Таймаут подключения (в секундах)
# AUTH_LDAP_CONNECTION_OPTIONS[ldap.OPT_NETWORK_TIMEOUT] = 10

# Для SSL/TLS подключений раскомментируйте:
# import ldap
# AUTH_LDAP_CONNECTION_OPTIONS[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_NEVER
# AUTH_LDAP_START_TLS = True

# =============================================================================
# КЭШИРОВАНИЕ
# =============================================================================

# Кэширование групп пользователя (в секундах)
# AUTH_LDAP_CACHE_TIMEOUT = 3600  # 1 час

# =============================================================================
# ОТЛАДКА
# =============================================================================

# Для отладки LDAP раскомментируйте:
# import logging
# logger = logging.getLogger('django_auth_ldap')
# logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.DEBUG)


# =============================================================================
# ПРИМЕРЫ КОНФИГУРАЦИЙ
# =============================================================================

"""
ПРИМЕР 1: Active Directory (Windows Server)
--------------------------------------------

AUTH_LDAP_SERVER_URI = "ldap://dc.company.local:389"
AUTH_LDAP_BIND_DN = "CN=django_bind,OU=Service Accounts,DC=company,DC=local"
AUTH_LDAP_BIND_PASSWORD = "SecurePassword123"

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "OU=Employees,DC=company,DC=local",
    ldap.SCOPE_SUBTREE,
    "(sAMAccountName=%(user)s)"
)

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "OU=Groups,DC=company,DC=local",
    ldap.SCOPE_SUBTREE,
    "(objectClass=group)"
)

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_superuser": "CN=IT Admins,OU=Groups,DC=company,DC=local",
    "is_staff": "CN=Managers,OU=Groups,DC=company,DC=local",
}

AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,
}
"""

"""
ПРИМЕР 2: OpenLDAP
------------------

AUTH_LDAP_SERVER_URI = "ldap://ldap.example.org:389"
AUTH_LDAP_BIND_DN = "cn=admin,dc=example,dc=org"
AUTH_LDAP_BIND_PASSWORD = "admin_password"

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=people,dc=example,dc=org",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"
)

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "ou=groups,dc=example,dc=org",
    ldap.SCOPE_SUBTREE,
    "(objectClass=posixGroup)"
)

from django_auth_ldap.config import PosixGroupType
AUTH_LDAP_GROUP_TYPE = PosixGroupType(name_attr="cn")
"""
