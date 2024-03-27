import ldap
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User as Userfun
from django.core.exceptions import ObjectDoesNotExist

import hashlib

from django.db.models import Q


class SettingsBackend(BaseBackend):
    """
    Authenticate against the settings ADMIN_LOGIN and ADMIN_PASSWORD.

    Use the login name and a hash of the password. For example:

    ADMIN_LOGIN = 'admin'
    ADMIN_PASSWORD = 'pbkdf2_sha256$30000$Vo0VlMnkR4Bk$qEvtdyZRWTcOsCnI/oQ7fVOu1XAURIZYoOZ3iq8Dr4M='
    """
    _connection = None
    _connection_bound = False

    def authenticate(self, request, username=None, password=None):
        tpuser = Userfun.objects.filter(Q(groups__name__isnull=False)|Q(is_staff=True)
                                        ).values_list("username",flat=True)
        # Userfun.objects.filter(=)
        if username not in tpuser:
            return None

        if not username or not password:
            return None
        if self._authenticate_user_dn(username, password):
            self._load_user_attrs(username)
            user = self._get_or_create_user(username, password)

            return user
        else:
            return None

    def _bind_as(self, bind_dn, bind_password, sticky=False):
        self._get_connection().simple_bind_s(
            bind_dn, bind_password
        )
        self._connection_bound = sticky

    def _get_connection(self):
        if not self._connection:
            self._connection = ldap.initialize(settings.LDAP_CONFIG['HOST'])
        return self._connection

    def _authenticate_user_dn(self, username, passwd):
        bind_dn = '%s@%s' % (username, 'intra.hoao.com')
        try:
            self._bind_as(bind_dn, passwd, False)
            return True
        except ldap.INVALID_CREDENTIALS:
            return False

    def _get_or_create_user(self, username, passwd):
        # 获取或者新建User
        try:
            return_user = Userfun.objects.get(username=username)
        except ObjectDoesNotExist:
            (user_chinese_name, user_email) = self._load_user_attrs(username)
            return_user = Userfun.objects.create(username=username, first_name=user_chinese_name, email=user_email)
        return return_user


    def _calc_sec_passwd(self, passwd):
        return_sec = hashlib.md5(passwd.encode(encoding='UTF-8')).hexdigest()
        return return_sec


    def _load_user_attrs(self, username):
        search_result = self._get_connection().search_s("ou=enterprise,dc=intra,dc=hoao,dc=com",
                                        ldap.SCOPE_SUBTREE, F"(&(objectClass=user)(sAMAccountName={username}))")
        user_chinese_name = search_result[0][0].split(',')[0].split('=')[-1]
        user_email = F"{username}@intra.hoao.com"
        return(user_chinese_name, user_email)


    def get_user(self, user_id):
        try:
            return Userfun.objects.get(pk=user_id)
        except Userfun.DoesNotExist:
            return None
