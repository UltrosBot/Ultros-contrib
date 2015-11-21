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
                return lambda *_, **__: self.finish_json(
                    invalid_key_error()
                )

            if permission is not None and not self.plugin.check_permission(
                permission, username
            ):
                return lambda *_, *__: self.finish_json(
                    permissions_error(permission)
                )

            return func(self, username, *args, **kwargs)
        return inner
    return wrap
