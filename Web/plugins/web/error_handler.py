__author__ = 'Gareth Coles'

from cyclone.web import ErrorHandler as Handler


class ErrorHandler(Handler):
    def write_error(self, status_code, **kwargs):
        print kwargs
        try:
            self.render(
                "generic.html",
                show_breadcrumbs=False,
                content="HTTP %s - %s" % (status_code, kwargs),
                nav_items={}
            )
        except Exception as e:
            self.finish("Error: %s" % e)
