# coding=utf-8

from plugins.web.api_errors import invalid_key_error, permissions_error

__author__ = 'Gareth Coles'


def check_xsrf(func):
    def inner(self, *args, **kwargs):
        self.check_xsrf_cookie()

        return func(self, *args, **kwargs)
    return inner


def check_api(permission=None, required_key=False):
    def wrap(func):
        def inner(self, api_key, *args, **kwargs):
            username = self.plugin.api_keys.get_username(api_key)

            if username is None and required_key:
                # Invalid API key
                return finish_invalid_key(self)

            if permission is not None and not self.plugin.check_permission(
                permission, username
            ):
                return finish_permissions_error(self, permission)

            return func(self, username, *args, **kwargs)
        return inner
    return wrap


def finish_invalid_key(self):
    def inner():
        self.finish_json(invalid_key_error())

    return inner


def finish_permissions_error(self, permission):
    def inner():
        self.finish_json(permissions_error(permission))

    return inner
