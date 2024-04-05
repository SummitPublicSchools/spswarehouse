import time

from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


### Click Elements

def click_element_by_css_selector(driver, css_selector: str, wait_time_in_seconds=30):
    """
    Waits for an element by CSS Selector and clicks it.
    """
    _wait_for_element_to_be_clickable_and_click_it(driver, By.CSS_SELECTOR, css_selector, wait_time_in_seconds)

def click_element_by_id(driver, element_id: str, wait_time_in_seconds=30):
    """
    Waits for an element by ID and clicks it.
    """
    _wait_for_element_to_be_clickable_and_click_it(driver, By.ID, element_id, wait_time_in_seconds)

def click_element_by_name(driver, element_name: str, wait_time_in_seconds=30):
    """
    Waits for an element by name and clicks it.
    """
    _wait_for_element_to_be_clickable_and_click_it(driver, By.NAME, element_name, wait_time_in_seconds)

def click_element_by_link_text(driver, link_text, wait_time_in_seconds=30):
    """
    Waits for an element by (full) link text and clicks it.
    """
    _wait_for_element_to_be_clickable_and_click_it(driver, By.LINK_TEXT, link_text, wait_time_in_seconds)

def click_element_by_partial_link_text(driver, partial_link_text: str, wait_time_in_seconds=30):
    """
    Waits for an element by partial link text and clicks it.
    """
    _wait_for_element_to_be_clickable_and_click_it(driver, By.PARTIAL_LINK_TEXT, partial_link_text, wait_time_in_seconds)

def click_element_by_xpath(driver, xpath: str, wait_time_in_seconds=30):
    """
    Waits for an element by XPATH and clicks it.
    """
    _wait_for_element_to_be_clickable_and_click_it(driver, By.XPATH, xpath, wait_time_in_seconds)


### Checkboxes

def ensure_checkbox_is_checked_by_name(driver, checkbox_name: str, wait_time_in_seconds=30):
    """
    Waits for a checkbox element by name and clicks it if it is not already selected.
    """
    checkbox = _wait_for_element_to_be_clickable_and_return_it(driver, By.XPATH, f"//input[@type='checkbox' and @name='{checkbox_name}']", 
        wait_time_in_seconds)
    
    if checkbox.is_selected() == False:
        checkbox.click()

def ensure_checkbox_is_unchecked_by_name(driver, checkbox_name: str, wait_time_in_seconds=30):
    """
    Waits for a checkbox element by name and clicks it if it is already selected, to make
    sure it is not checked.
    """
    checkbox = _wait_for_element_to_be_clickable_and_return_it(driver, By.XPATH, f"//input[@type='checkbox' and @name='{checkbox_name}']", 
        wait_time_in_seconds)
    
    if checkbox.is_selected():
        checkbox.click()


### Element Text Matches

def ensure_element_text_matches_expected_value_by_xpath(driver, element_xpath, expected_text, wait_time_in_seconds=30):
    """
    Waits for an element by XPATH and checks whether its text matches the expected text.
    """
    elem = _wait_for_element_to_be_clickable_and_return_it(driver, By.XPATH, element_xpath, wait_time_in_seconds)
    return elem.text == expected_text


### Get Element(s)

def get_element_by_css_selector(driver, css_selector: str, wait_time_in_seconds=30):
    """
    Waits for an element by CSS Selector and returns it.
    """
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.CSS_SELECTOR, css_selector, wait_time_in_seconds)
    return elem

def get_element_by_id(driver, element_id, wait_time_in_seconds=30):
    """
    Waits for an element by ID and returns it.
    """
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.ID, element_id, wait_time_in_seconds)
    return elem

def get_element_by_link_text(driver, link_text, wait_time_in_seconds=30):
    """
    Waits for an element by (full) link text and returns it.
    """
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.LINK_TEXT, link_text, wait_time_in_seconds)
    return elem

def get_element_by_xpath(driver, xpath: str, wait_time_in_seconds=30):
    """
    Waits for an element by XPATH and returns it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.XPATH, xpath)))
    return elem

def get_element_by_class_name(driver, class_name: str, wait_time_in_seconds=30):
    """
    Waits for an element by class_name and returns it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))

    return elem

def get_multiple_elements_by_class_name(driver, class_name: str, wait_time_in_seconds=30):
    """
    Waits for an element by class name, then retrieves the full list of elements with that class name.
    """
    _wait_for_element_to_be_present_and_return_it(driver, By.CLASS_NAME, class_name, wait_time_in_seconds)

    # Pause to give all elements with that class_name time to load
    time.sleep(5)

    elements_list = driver.find_elements(By.CLASS_NAME, class_name)

    return elements_list


### Select Text in Element

def select_visible_text_in_element_by_id(driver, element_id: str, text_to_select: str, wait_time_in_seconds=30):
    """
    Waits for an element by ID and selects it by specified text.
    """
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.ID, element_id, wait_time_in_seconds)
    select = Select(elem)
    select.select_by_visible_text(text_to_select)

def select_visible_text_in_element_by_name(driver, element_name: str, text_to_select: str, wait_time_in_seconds=30):
    """
    Waits for an element by name and selects it by specified text.
    """
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.NAME, element_name, wait_time_in_seconds)
    select = Select(elem)
    select.select_by_visible_text(text_to_select)


### Type in Element

def type_in_element_by_id(driver, element_id: str, input_to_type: str, wait_time_in_seconds=30):
    """
    Waits for an element by ID, clears it, and types in the input.
    """
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.ID, element_id, wait_time_in_seconds)
    elem.clear()
    elem.send_keys(input_to_type)

def type_in_element_by_name(driver, element_name: str, input_to_type: str, wait_time_in_seconds=30):
    """
    Waits for an element by name, clears it, and types in the input.
    """
    elem =  _wait_for_element_to_be_present_and_return_it(driver, By.NAME, element_name, wait_time_in_seconds)
    elem.clear()
    elem.send_keys(input_to_type)

def type_in_element_by_xpath(driver, element_xpath: str, input_to_type: str, wait_time_in_seconds=30):
    """
    Waits for an element by XPATH, clears it, and types in the input.
    """
    elem =  _wait_for_element_to_be_present_and_return_it(driver, By.XPATH, element_xpath, wait_time_in_seconds)
    elem.clear()
    elem.send_keys(input_to_type)


### Wait for Element
    
def wait_for_element_containing_specific_text(driver, expected_element_text, wait_time_in_seconds=30):
    """
    Waits for an element containing the specific text. Will crash if it does not 
    appear in the time allotted (default = 30 seconds).
    """
    xpath_text = f"//*[contains(text(), '{expected_element_text}')]"
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.XPATH, xpath_text, wait_time_in_seconds)
    return elem
    

### Internal Functions

def _wait_for_element_to_be_clickable_and_return_it(driver, by_object, target_identifier, wait_time_in_seconds=30):
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((by_object, target_identifier)))
    return elem

def _wait_for_element_to_be_clickable_and_click_it(driver, by_object, target_identifier, wait_time_in_seconds=30):
    elem = _wait_for_element_to_be_clickable_and_return_it(driver, by_object, target_identifier, wait_time_in_seconds)
    elem.click()

def _wait_for_element_to_be_present_and_return_it(driver, by_object, target_identifier, wait_time_in_seconds=30):
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((by_object, target_identifier)))
    return elem


### Deprecated old functions, do not delete until v1.0.0
def helper_click_element_by_css_selector(driver, css_selector: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    _wait_for_element_to_be_clickable_and_click_it(driver, By.CSS_SELECTOR, css_selector, wait_time_in_seconds)

def helper_click_element_by_id(driver, element_id: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    _wait_for_element_to_be_clickable_and_click_it(driver, By.ID, element_id, wait_time_in_seconds)

def helper_click_element_by_name(driver, element_name: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    _wait_for_element_to_be_clickable_and_click_it(driver, By.NAME, element_name, wait_time_in_seconds)

def helper_click_element_by_link_text(driver, link_text, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    _wait_for_element_to_be_clickable_and_click_it(driver, By.LINK_TEXT, link_text, wait_time_in_seconds)

def helper_click_element_by_partial_link_text(driver, partial_link_text: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    _wait_for_element_to_be_clickable_and_click_it(driver, By.PARTIAL_LINK_TEXT, partial_link_text, wait_time_in_seconds)

def helper_click_element_by_xpath(driver, xpath: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    _wait_for_element_to_be_clickable_and_click_it(driver, By.XPATH, xpath, wait_time_in_seconds)
    
def helper_ensure_checkbox_is_checked_by_name(driver, checkbox_name: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    checkbox = _wait_for_element_to_be_clickable_and_return_it(driver, By.XPATH, f"//input[@type='checkbox' and @name='{checkbox_name}']", 
        wait_time_in_seconds)
    
    if checkbox.is_selected() == False:
        checkbox.click()

def helper_ensure_checkbox_is_unchecked_by_name(driver, checkbox_name: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    checkbox = _wait_for_element_to_be_clickable_and_return_it(driver, By.XPATH, f"//input[@type='checkbox' and @name='{checkbox_name}']", 
        wait_time_in_seconds)
    
    if checkbox.is_selected():
        checkbox.click()

def helper_ensure_element_text_matches_expected_value_by_xpath(driver, element_xpath, expected_text, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem = _wait_for_element_to_be_clickable_and_return_it(driver, By.XPATH, element_xpath, wait_time_in_seconds)
    return elem.text == expected_text

def helper_get_element_by_css_selector(driver, css_selector: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.CSS_SELECTOR, css_selector, wait_time_in_seconds)
    return elem

def helper_get_element_by_id(driver, element_id, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.ID, element_id, wait_time_in_seconds)
    return elem

def helper_get_element_by_link_text(driver, link_text, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.LINK_TEXT, link_text, wait_time_in_seconds)
    return elem

def helper_get_element_by_xpath(driver, xpath: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.XPATH, xpath)))
    return elem

def helper_get_multiple_elements_by_class_name(driver, class_name: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    _wait_for_element_to_be_present_and_return_it(driver, By.CLASS_NAME, class_name, wait_time_in_seconds)

    # Pause to give all elements with that class_name time to load
    time.sleep(5)

    elements_list = driver.find_elements(By.CLASS_NAME, class_name)

    return elements_list

def helper_select_visible_text_in_element_by_id(driver, element_id: str, text_to_select: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.ID, element_id, wait_time_in_seconds)
    select = Select(elem)
    select.select_by_visible_text(text_to_select)

def helper_select_visible_text_in_element_by_name(driver, element_name: str, text_to_select: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.NAME, element_name, wait_time_in_seconds)
    select = Select(elem)
    select.select_by_visible_text(text_to_select)

def helper_type_in_element_by_id(driver, element_id: str, input_to_type: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.ID, element_id, wait_time_in_seconds)
    elem.clear()
    elem.send_keys(input_to_type)

def helper_type_in_element_by_name(driver, element_name: str, input_to_type: str, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    elem =  _wait_for_element_to_be_present_and_return_it(driver, By.NAME, element_name, wait_time_in_seconds)
    elem.clear()
    elem.send_keys(input_to_type)
    
def helper_wait_for_element_containing_specific_text(driver, expected_element_text, wait_time_in_seconds=30):
    print("Deprecated. Please remove helper_ prefix from function name")
    xpath_text = f"//*[contains(text(), '{expected_element_text}')]"
    elem = _wait_for_element_to_be_present_and_return_it(driver, By.XPATH, xpath_text, wait_time_in_seconds)
    return elem