import ldap
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class MultiDomainLDAPBackend:
    """
    Кастомный LDAP backend для поддержки нескольких доменов.
    
    Поддерживает два режима работы:
    1. Автоопределение домена - пробует авторизацию на всех доменах последовательно
    2. Конкретный домен - авторизация только на выбранном домене
    """
    
    def authenticate(self, request, username=None, password=None, domain=None):
        """
        Аутентификация пользователя с поддержкой мультидоменной среды.
        
        Args:
            request: HTTP запрос
            username: Имя пользователя
            password: Пароль
            domain: Код домена (domain1, domain2, domain3) или None для автоопределения
        
        Returns:
            User объект при успешной аутентификации или None
        """
        if not username or not password:
            return None
        
        # Получаем список доменов из настроек
        ldap_domains = getattr(settings, 'LDAP_DOMAINS', {})
        
        if not ldap_domains:
            logger.warning("LDAP_DOMAINS не настроен в settings.py")
            return None
        
        # Если домен указан - пробуем только его
        if domain and domain in ldap_domains:
            logger.info(f"Попытка авторизации пользователя '{username}' на домене '{domain}'")
            return self._authenticate_on_domain(username, password, domain, ldap_domains[domain])
        
        # Если домен не указан - пробуем все домены по очереди
        logger.info(f"Автоопределение домена для пользователя '{username}'")
        for domain_code, domain_config in ldap_domains.items():
            logger.info(f"Попытка авторизации на домене '{domain_code}'")
            user = self._authenticate_on_domain(username, password, domain_code, domain_config)
            if user:
                logger.info(f"Успешная авторизация пользователя '{username}' на домене '{domain_code}'")
                return user
        
        logger.warning(f"Не удалось авторизовать пользователя '{username}' ни на одном из доменов")
        return None
    
    def _authenticate_on_domain(self, username, password, domain_code, domain_config):
        """
        Попытка авторизации на конкретном домене.
        
        Args:
            username: Имя пользователя
            password: Пароль
            domain_code: Код домена (domain1, domain2, и т.д.)
            domain_config: Конфигурация домена из settings.LDAP_DOMAINS
        
        Returns:
            User объект при успешной аутентификации или None
        """
        try:
            # Извлекаем конфигурацию домена
            server_uri = domain_config.get('SERVER_URI')
            bind_dn = domain_config.get('BIND_DN')
            bind_password = domain_config.get('BIND_PASSWORD')
            user_search_base = domain_config.get('USER_SEARCH_BASE')
            user_search_filter = domain_config.get('USER_SEARCH_FILTER', '(sAMAccountName=%(user)s)')
            
            if not all([server_uri, user_search_base]):
                logger.error(f"Неполная конфигурация для домена '{domain_code}'")
                return None
            
            # Подключаемся к LDAP серверу
            conn = ldap.initialize(server_uri)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
            
            # Авторизуемся под служебной учеткой (bind user)
            if bind_dn and bind_password:
                conn.simple_bind_s(bind_dn, bind_password)
            
            # Ищем пользователя в LDAP
            search_filter = user_search_filter % {'user': username}
            result = conn.search_s(
                user_search_base,
                ldap.SCOPE_SUBTREE,
                search_filter,
                ['sAMAccountName', 'mail', 'givenName', 'sn', 'displayName']
            )
            
            if not result:
                logger.info(f"Пользователь '{username}' не найден на домене '{domain_code}'")
                conn.unbind_s()
                return None
            
            # Получаем DN пользователя
            user_dn, user_attrs = result[0]
            
            # Пробуем авторизоваться под учеткой пользователя
            try:
                user_conn = ldap.initialize(server_uri)
                user_conn.set_option(ldap.OPT_REFERRALS, 0)
                user_conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
                user_conn.simple_bind_s(user_dn, password)
                user_conn.unbind_s()
            except ldap.INVALID_CREDENTIALS:
                logger.info(f"Неверный пароль для пользователя '{username}' на домене '{domain_code}'")
                conn.unbind_s()
                return None
            
            # Авторизация успешна - получаем или создаем пользователя Django
            conn.unbind_s()
            
            # Извлекаем атрибуты пользователя
            email = user_attrs.get('mail', [b''])[0].decode('utf-8') if 'mail' in user_attrs else ''
            first_name = user_attrs.get('givenName', [b''])[0].decode('utf-8') if 'givenName' in user_attrs else ''
            last_name = user_attrs.get('sn', [b''])[0].decode('utf-8') if 'sn' in user_attrs else ''
            display_name = user_attrs.get('displayName', [b''])[0].decode('utf-8') if 'displayName' in user_attrs else ''
            
            # Создаем или обновляем пользователя в Django
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name or display_name.split()[0] if display_name else '',
                    'last_name': last_name or ' '.join(display_name.split()[1:]) if display_name else '',
                }
            )
            
            if not created:
                user.email = email
                user.first_name = first_name or display_name.split()[0] if display_name else user.first_name
                user.last_name = last_name or ' '.join(display_name.split()[1:]) if display_name else user.last_name
                user.save()
            
            logger.info(f"Пользователь '{username}' успешно авторизован на домене '{domain_code}'")
            return user
            
        except ldap.LDAPError as e:
            logger.error(f"Ошибка LDAP при авторизации на домене '{domain_code}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при авторизации на домене '{domain_code}': {str(e)}")
            return None
    
    def get_user(self, user_id):
        """
        Получение пользователя по ID (требуется Django).
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
