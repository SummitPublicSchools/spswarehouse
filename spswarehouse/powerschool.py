import logging

# from selenium.webdriver.support.ui import Select
# from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def log_into_powerschool_admin(driver: WebDriver, 
                               username: str, 
                               password: str, 
                               host: str):
    """
    Using the supplied Selenium webdriver, log into PowerSchool Admin
    with the given username, password, and host.
    
    Arguments:
        driver (webdriver.Chrome()): a Selenium-powered Chrome Window
        username (str): the PowerSchool Admin username
        password (str): the PowerSchool Admin password
        host (str): the PowerSchool Admin login-page
        
    Returns:
        None: Selenium will log you into PowerSchool Admin
    """
    logging.info("Create webpage URL for PowerSchool Admin")
    host_file_page_type = '/admin/pw.html'
    host_full = host + host_file_page_type
    logging.info(f"The webpage url is: {host_full}")
    
    logging.info("Go to webpage URL for PowerSchool Admin")
    driver.get(host_full)
    
    logging.info("Find the username field within the login page")
    elem = (
        WebDriverWait(driver, 30)
        .until(EC.presence_of_element_located((By.ID, 'fieldUsername')))
    )
    
    logging.info("Clear any pre-filled values within the username field")
    elem.clear()
    
    logging.info("Type your PowerSchool username")
    elem.send_keys(username)
    
    logging.info("Find the password field within the HTML page")
    elem = driver.find_element_by_id('fieldPassword')
    
    logging.info("Type your PowerSchool CA password")
    elem.send_keys(password)
    
    logging.info("Press enter to submit your credentials and complete your login.")
    elem.send_keys(Keys.RETURN)