__author__ = 'Gareth Coles'


def check_xsrf(func):
    def inner(self, *args, **kwargs):
        self.check_xsrf_cookie()

        return func(self, *args, **kwargs)

    return inner
