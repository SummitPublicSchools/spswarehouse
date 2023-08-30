from selenium.webdriver import Chrome
from selenium.webdriver.chrome import webdriver as chrome_webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException


def helper_type_in_element_by_id(driver, element_id: str, input_to_type: str):
        """
        Waits for an element by ID, clears it, and types in the input.
        """
        elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
        elem.clear()
        elem.send_keys(input_to_type)

def helper_type_in_element_by_name(driver, element_name: str, input_to_type: str):
    """
    Waits for an element by name, clears it, and types in the input.
    """
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 
        element_name)))
    elem.clear()
    elem.send_keys(input_to_type)

def helper_select_visible_text_in_element_by_id(driver, element_id: str, 
    text_to_select: str):
    """
    Waits for an element by ID and selects it by specified text.
    """
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
    select = Select(elem)
    select.select_by_visible_text(text_to_select)

def helper_select_visible_text_in_element_by_name(driver, element_name: str, 
    text_to_select: str):
    """
    Waits for an element by name and selects it by specified text.
    """
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 
        element_name)))
    select = Select(elem)
    select.select_by_visible_text(text_to_select)

def helper_click_element_by_id(driver, element_id: str):
    """
    Waits for an element by ID and clicks it.
    """
    elem = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, element_id)))
    elem.click()

def helper_click_element_by_name(driver, element_name: str):
    """
    Waits for an element by name and clicks it.
    """
    elem = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.NAME, element_name)))
    elem.click()

def helper_click_element_by_partial_link_text(driver, partial_link_text: str):
    """
    Waits for an element by partial link text and clicks it.
    """
    elem = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 
        f"{partial_link_text}")))
    elem.click()

def helper_ensure_checkbox_is_checked_by_name(driver, checkbox_name: str):
    """
    Waits for a checkbox element by name and clicks it if it is not already selected.
    """
    checkbox = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, 
        f"//input[@type='checkbox' and @name='{checkbox_name}']")))
    
    if checkbox.is_selected() == False:
        checkbox.click()

def helper_ensure_checkbox_is_unchecked_by_name(driver, checkbox_name: str):
    """
    Waits for a checkbox element by name and clicks it if it is already selected, to make
    sure it is not checked.
    """
    checkbox = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, 
        f"//input[@type='checkbox' and @name='{checkbox_name}']")))
    
    if checkbox.is_selected():
        checkbox.click()

def helper_ensure_element_text_matches_expected_value_by_xpath(driver, element_xpath, expected_text):
    """
    Waits for an element by XPATH and checks whether its text matches the expected text.
    """
    elem = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, 
        element_xpath)))
    
    return elem.text == expected_text

def helper_wait_for_element_containing_specific_text(driver, expected_element_text, wait_time_in_second=30):
    """
    Waits for an element containing specific text and returns True if it appears in the time allotted
    (default = 30 seconds) or False if it does not appear.
    """
    try:
        WebDriverWait(driver, wait_time_in_second).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{expected_element_text}')]")))
        return True
    except:
        return False