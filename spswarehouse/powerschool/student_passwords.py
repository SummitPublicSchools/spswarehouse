import logging
import time
import os

try:
    from spswarehouse.credentials import powerschool_config
except ModuleNotFoundError:
    print("No credentials file found in spswarehouse. This could cause issues.")

from ducttape.utils import (
    DriverBuilder,
    get_most_recent_file_in_dir,
)
    
from selenium.webdriver import Chrome
from selenium.webdriver.chrome import webdriver as chrome_webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

STUDENT_URL_PATH = 'public'

class PSStudentPassword:
    """
    A class for interacting with the Student UI for PowerSchool in order to reset
    passwords.
    """
    
    def __init__(self, host: str=None, headless: bool=True, wait_time: int=30,
        download_location: str='.'):
        
        if host is None:
            self.host = powerschool_config['host']
        else:
            self.host = host
        
        self.wait_time = wait_time

        self.student_url = self.host + '/' + STUDENT_URL_PATH
        self.driver = DriverBuilder().get_driver(headless=headless, download_location=download_location)
        
    def reset_student(self, username: str, old_password: str, new_password: str):
        self._login(username, old_password)
        
        try:
            self._wait_by_name("newCredential")
        except:
            logging.info(f"Username: {username} - password change screen did not load. Skipping.")
            try:
                self._logout()
            except:
                pass
            return False
        
        self._find_by_name_and_send("currentCredential", old_password)
        self._find_by_name_and_send("newCredential", new_password)
        new_pw_box2 = self._find_by_name_and_send("newCredential1", new_password)
        new_pw_box2.send_keys(Keys.RETURN)
        
        try:
            self._logout()
        except:
            reused_pw_message = self.driver.find_element(By.XPATH, '//*[@id="content"]/ul/li/span')
            if reused_pw_message.text == 'The password entered was previously used. Please enter a new password':
                logging.info(f"Username: {username} - repeated password. Skipping.")
                return False
            
        self._login(username, new_password)
        
        try:
            self._logout()
            return True
        except:
            logging.info(f"Username: {username} - new password failed to login.")
            return False
            
    def _login(self, username: str, password: str):
        self.driver.get(self.student_url)
        
        try:
            username_elem = self._wait_by_id("fieldAccount")
        except:
            self._logout()
            username_elem = self._wait_by_id("fieldAccount")
        
        username_elem.send_keys(username)
        pw_box = self._find_by_id_and_send("fieldPassword", password)
        pw_box.send_keys(Keys.RETURN)
            
    def _logout(self):
        logout_button = self._wait_by_id("btnLogout")
        logout_button.click()
    
    def _find_by_id_and_send(self, field_id, entry):
        elem = self.driver.find_element(By.ID, field_id)
        elem.send_keys(entry)
        return elem
    
    def _find_by_name_and_send(self, field_name, entry):
        elem = self.driver.find_element(By.NAME, field_name)
        elem.send_keys(entry)
        return elem
    
    def _wait_by_id(self, elem_id):
        return WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located((By.ID, elem_id))
        )
    
    def _wait_by_name(self, elem_name):
        return WebDriverWait(self.driver, self.wait_time).until(
            EC.presence_of_element_located((By.NAME, elem_name))
        )