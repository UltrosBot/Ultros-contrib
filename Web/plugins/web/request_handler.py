__author__ = 'Gareth Coles'

import traceback

from cyclone.web import RequestHandler as Handler
from cyclone import escape

import json

from twisted.python.failure import Failure


class RequestHandler(Handler):

    #: :type: str
    name = None

    #: :type: list
    css = None

    #: :type: list
    js = None

    def __init__(self, *args, **kwargs):
        self.css = ["/static/custom.css"]
        self.js = []

        super(RequestHandler, self).__init__(*args, **kwargs)

    @property
    def plugin(self):
        return self.create_template_loader().plugin

    @property
    def sessions(self):
        return self.plugin.sessions

    def add_css(self, path):
        if path not in self.css:
            self.css.append(path)

    def add_js(self, path):
        if path not in self.js:
            self.js.append(path)

    def clear_session(self):
        self.set_secure_cookie("auth", "")

    def create_template_loader(self, _=None):  # No alternate template paths
        return self.application.settings["template_loader"]

    def finish_json(self, _dict):
        self.set_header("Content-Type", "application/json")
        return self.finish(json.dumps(_dict, sort_keys=True))

    def get_session_key(self):
        return self.get_secure_cookie("session", max_age_days=9999999) or None

    def get_session_object(self):
        cookie = self.get_session_key()

        if cookie is not None:
            return self.sessions.get_session(cookie)
        return None

    def prepare(self):
        self.plugin.logger.trace("XSRF token: %s" % self.xsrf_token)

        s = self.get_session_object()
        key = self.get_session_key()

        if s:
            self.set_session(key, s["remember"])
            self.sessions.update_session_time(key)

    def redirect(self, url, permanent=False, status=None,
                 message=None, message_colour="green",
                 redirect=None):

        if message is not None or redirect is not None:
            url += "?"

            if message is not None:
                msg = escape.url_escape(message)
                col = escape.url_escape(message_colour)

                url += "msg=%s&col=%s" % (msg, col)

                if redirect is not None:
                    url += "&"

            if redirect is not None:
                url += "redirect=%s" % escape.url_escape(redirect)

        super(RequestHandler, self).redirect(url, permanent, status)

    def render(self, template_name, **kwargs):
        self.finish(self.render_string(template_name, **kwargs))

    def render_string(self, template_name, **kwargs):
        loader = self.create_template_loader()

        namespace = self.get_template_namespace()
        namespace.update(loader.namespace)
        namespace.update(kwargs)
        namespace.update(loader.plugin.namespace)

        namespace["extra_css"] = self.css
        namespace["extra_js"] = self.js
        namespace["headers"] = kwargs.get("headers", [])
        namespace["nav_items"] = self.plugin.navbar_items
        namespace["nav_name"] = self.name
        namespace["session"] = self.get_session_object()
        namespace["sessions"] = self.sessions
        namespace["xsrf"] = self.xsrf_form_html

        namespace["_message"] = self.get_argument("msg", None)
        namespace["_message_type"] = self.get_argument("col", "green")

        template = loader.load(template_name)
        return template.render(**namespace)

    def set_session(self, key, remember=False):
        self.set_secure_cookie("session", key, 30 if not remember else 9999999)

    def write_error(self, status_code, **kwargs):
        tb = ""
        ex = kwargs

        if "exception" in kwargs:
            #: :type: Exception
            ex = kwargs["exception"]
            if isinstance(ex, Failure):
                tb = traceback.format_tb(
                    kwargs["exception"].getTracebackObject()
                )

                kwargs["exception"].printTraceback()
            else:
                self.plugin.logger.error("%s" % ex)
                tb = ex.message
        try:
            self.render(
                "generic.html",
                _title="HTTP %s" % self.get_status(),
                show_breadcrumbs=False,
                content="""
<div class="ui red segment">
    HTTP %s - %s
    <br /> <pre class="ui segment">%s</pre>
</div>
                """ % (self.get_status(), escape.xhtml_escape(str(ex)),
                       escape.xhtml_escape("\n".join(tb))),
                nav_items={}
            )
        except Exception as e:
            self.set_status(status_code)
            self.finish("Error: %s" % e)
