import logging
import time

# from selenium.webdriver.support.ui import Select
# from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

ADMIN_LOGIN_PAGE_PATH = 'admin/pw.html'
ADMIN_HOME_PAGE_PATH = 'admin/home.html'
ADMIN_URL_SCHEME = 'https://'
STATE_REPORTS_PAGE_PATH = 'admin/reports/statereports.html?repType=state'

"""
TODO: Should this be a class that creates its own WebDriver? Might make it 
harder for the end user to access it for doing their own custom code in PowerSchool,
but it would eliminate the need to pass the user's WebDriver to all these functions.
How would this work with Airflow?
"""

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
    host_full = host + "/" + ADMIN_LOGIN_PAGE_PATH
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
    
    logging.info("Type your PowerSchool password")
    elem.send_keys(password)
    
    logging.info("Press enter to submit your credentials and complete your login.")
    elem.send_keys(Keys.RETURN)

def get_current_domain(driver: WebDriver):
    return driver.current_url[8:].split("/",1)[:1][0]

def get_current_path(driver: WebDriver):
    return driver.current_url[8:].split("/",1)[1:][0]

def ensure_on_desired_path(driver: WebDriver, desired_path: str):
    current_path = get_current_path(driver)

    logging.info(f"The current path is: {current_path}")

    if(current_path == desired_path):
        logging.info("The current path is the desired path. No action taken.")
    else:
        logging.info(f"This does not match {desired_path}, so going to that path")
        driver.get('https://' + get_current_domain(driver) + "/" + desired_path)
        logging.info(f"Moved to {desired_path}")

def switch_to_school(driver: WebDriver, 
                    school_name: str):
    ensure_on_desired_path(driver, ADMIN_HOME_PAGE_PATH)

    logging.info("Waiting for School Picker")
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'school_picker_adminSchoolPicker_toggle_btn')))
    logging.info("School Picker found. Click it.")

    elem.click()

    time.sleep(1)

    logging.info("Waiting for School Search Field")
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'schoolSearchField_value')))
    logging.info("Found School Search Field. Typing in school name.")

    elem.send_keys(school_name)

    time.sleep(1)

    logging.info("Looking for first school in list")
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//ul[@id='school_choices']/li[1]")))

    logging.info("Found first school in results list. Clicking.")
    elem.click()
    logging.info("Click. Waiting for page to refresh.")
    time.sleep(1)

    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'school_picker_adminSchoolPicker_toggle_btn')))

    elem.click()
    time.sleep(1)

    selected_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.list-item.selectable.selected')))

    school_element_text = selected_element.find_element(By.XPATH, ".//div").text

    actions = ActionChains(driver)

    if(school_name in school_element_text):
        logging.info(f"Found the {school_name} in the school element text. Success!")

        logging.info(f"Pressing escape to leave dropdown selection.")
        actions.send_keys(Keys.ESCAPE).perform()
    else:
        raise Exception(f"Did not find {school_name} in the school element text.")
    
def navigate_to_state_reports_page(driver: WebDriver):
    driver.get(ADMIN_URL_SCHEME + get_current_domain(driver) + '/' + STATE_REPORTS_PAGE_PATH)

    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul li.selected')))
    assert elem.text == 'State', "'State' tab is not selected"