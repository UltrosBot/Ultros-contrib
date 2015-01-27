"""
Slightly-edited WebDriver implementations.

I've done this because Selenium hardcodes keep_alive in browser-specific
drivers for some reason, but doing so causes things to break. This is mostly
because we're doing things selenium wasn't at all designed for, but even so,
it seems like something that should be possible to set manually.
"""

__author__ = 'Gareth Coles'

from selenium import webdriver

from selenium.webdriver import DesiredCapabilities

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

from selenium.webdriver.firefox.extension_connection import ExtensionConnection
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver


class Firefox(webdriver.Firefox):
    def __init__(self, firefox_profile=None, firefox_binary=None, timeout=30,
                 capabilities=None, proxy=None, keep_alive=False):

        self.binary = firefox_binary
        self.profile = firefox_profile

        if self.profile is None:
            self.profile = FirefoxProfile()

        self.profile.native_events_enabled = (
            self.NATIVE_EVENTS_ALLOWED and self.profile.native_events_enabled)

        if self.binary is None:
            self.binary = FirefoxBinary()

        if capabilities is None:
            capabilities = DesiredCapabilities.FIREFOX

        if proxy is not None:
            proxy.add_to_capabilities(capabilities)

        RemoteWebDriver.__init__(
            self,
            command_executor=ExtensionConnection(
                "127.0.0.1", self.profile,
                self.binary, timeout
            ),
            desired_capabilities=capabilities,
            keep_alive=keep_alive
        )
        self._is_remote = False


class Chrome(webdriver.Chrome):
    def __init__(self, executable_path="chromedriver", port=0,
                 chrome_options=None, service_args=None,
                 desired_capabilities=None, service_log_path=None,
                 keep_alive=False):
        if chrome_options is None:
            # desired_capabilities stays as passed in
            if desired_capabilities is None:
                desired_capabilities = ChromeOptions().to_capabilities()
        else:
            if desired_capabilities is None:
                desired_capabilities = chrome_options.to_capabilities()
            else:
                desired_capabilities.update(chrome_options.to_capabilities())

        self.service = ChromeService(
            executable_path, port=port,
            service_args=service_args, log_path=service_log_path
        )

        self.service.start()

        try:
            RemoteWebDriver.__init__(
                self,
                command_executor=self.service.service_url,
                desired_capabilities=desired_capabilities,
                keep_alive=keep_alive
            )
        except:
            self.quit()
            raise
        self._is_remote = False


class Ie(webdriver.Ie):
    # Should never use keep_alive
    pass


class Opera(webdriver.Opera):
    # Should never use keep_alive
    pass


class Safari(webdriver.Safari):
    # Should never use keep_alive
    pass


class PhantomJS(webdriver.PhantomJS):
    # Should never use keep_alive
    pass


class Android(webdriver.Android):
    # Should never use keep_alive
    pass


class Remote(webdriver.Remote):
    # Already supports specifying keep_alive
    pass
