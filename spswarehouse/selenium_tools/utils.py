import os

from selenium.webdriver import Chrome
from selenium.webdriver.chrome import webdriver as chrome_webdriver

# Borrowed from ducttape.utils
class DriverBuilder:
    """A set of function used to instantiate a Chrome Selenium Webdriver"""
    def get_driver(self, download_location=None, headless=False, window_size=(1400, 900),
                   chrome_option_prefs=None):
        """
        Convenience function for creating a chrome driver.
        :param download_location: A path to where files should be downloaded. Can be absolute or relative.
        :param headless: A boolean for whether the chromedriver should run without GUI.
        :param window_size: A tuple of l x w for the browser window
        :param chrome_option_prefs: A dict() of any options for to apply to the driver using
        the chrome options class. See http://chromedriver.chromium.org/capabilities and
        https://chromium.googlesource.com/chromium/src/+/master/chrome/common/pref_names.cc
        :return: A selenium web driver.
        """

        driver = self._get_chrome_driver(download_location, headless, chrome_option_prefs)

        driver.set_window_size(*window_size)

        return driver

    def _get_chrome_driver(self, download_location, headless, chrome_option_prefs):
        chrome_options = chrome_webdriver.Options()
        prefs = {}
        if download_location:
            dl_prefs = {'download.default_directory': os.path.abspath(download_location),
                        'download.prompt_for_download': False,
                        'download.directory_upgrade': True,
                        'safebrowsing.enabled': False,
                        'safebrowsing.disable_download_protection': True}

            prefs.update(dl_prefs)

        if chrome_option_prefs:
            prefs.update(chrome_option_prefs)
        chrome_options.add_experimental_option('prefs', prefs)
        
        # when run from a Docker container
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        if headless:
            chrome_options.add_argument("--headless")

        driver = Chrome(options=chrome_options)

        return driver