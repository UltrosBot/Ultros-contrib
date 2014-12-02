__author__ = 'Gareth Coles'


def check_xsrf(func):
    def inner(self, *args, **kwargs):
        self.check_xsrf_cookie()

        return func(self, *args, **kwargs)
    return inner


def check_api(func):
    def inner(self, api_key, *args, **kwargs):
        username = self.plugin.api_keys.get_username(api_key)

        return func(self, username, *args, **kwargs)
    return inner
