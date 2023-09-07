from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


### Click Elements

def helper_click_element_by_css_selector(driver, css_selector: str, wait_time_in_seconds=30):
    """
    Waits for an element by CSS Selector and clicks it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
    elem.click()

def helper_click_element_by_id(driver, element_id: str, wait_time_in_seconds=30):
    """
    Waits for an element by ID and clicks it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((By.ID, element_id)))
    elem.click()

def helper_click_element_by_name(driver, element_name: str, wait_time_in_seconds=30):
    """
    Waits for an element by name and clicks it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((By.NAME, element_name)))
    elem.click()

def helper_click_element_by_link_text(driver, link_text, wait_time_in_seconds=30):
    """
    Waits for an element by (full) link text and clicks it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((By.LINK_TEXT, link_text)))
    elem.click()

def helper_click_element_by_partial_link_text(driver, partial_link_text: str):
    """
    Waits for an element by partial link text and clicks it.
    """
    elem = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, partial_link_text)))
    elem.click()

def helper_click_element_by_xpath(driver, xpath: str, wait_time_in_seconds=30):
    """
    Waits for an element by XPATH and clicks it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elem.click()


### Checkboxes

def helper_ensure_checkbox_is_checked_by_name(driver, checkbox_name: str, wait_time_in_seconds=30):
    """
    Waits for a checkbox element by name and clicks it if it is not already selected.
    """
    checkbox = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((By.XPATH, 
        f"//input[@type='checkbox' and @name='{checkbox_name}']")))
    
    if checkbox.is_selected() == False:
        checkbox.click()

def helper_ensure_checkbox_is_unchecked_by_name(driver, checkbox_name: str, wait_time_in_seconds=30):
    """
    Waits for a checkbox element by name and clicks it if it is already selected, to make
    sure it is not checked.
    """
    checkbox = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((By.XPATH, 
        f"//input[@type='checkbox' and @name='{checkbox_name}']")))
    
    if checkbox.is_selected():
        checkbox.click()


### Element Text Matches

def helper_ensure_element_text_matches_expected_value_by_xpath(driver, element_xpath, expected_text, wait_time_in_seconds=30):
    """
    Waits for an element by XPATH and checks whether its text matches the expected text.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.element_to_be_clickable((By.XPATH, 
        element_xpath)))
    
    return elem.text == expected_text


### Get Element(s)

def helper_get_element_by_css_selector(driver, css_selector: str, wait_time_in_seconds=30):
    """
    Waits for an element by CSS Selector and returns it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
    return elem

def helper_get_element_by_id(driver, element_id, wait_time_in_seconds=30):
    """
    Waits for an element by ID and returns it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.ID, element_id)))
    return elem

def helper_get_element_by_link_text(driver, link_text, wait_time_in_seconds=30):
    """
    Waits for an element by (full) link text and returns it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.LINK_TEXT, link_text)))
    return elem

def helper_get_element_by_xpath(driver, xpath: str, wait_time_in_seconds=30):
    """
    Waits for an element by XPATH and returns it.
    """
    elem = WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.XPATH, xpath)))
    return elem

def helper_get_multiple_elements_by_class_name(driver, class_name: str, wait_time_in_seconds=30):
    """
    Waits for an element by class name, then retrieves the full list of elements with that class name.
    """
    WebDriverWait(driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))

    # Pause to give all elements with that class_name time to load
    time.sleep(5)

    elements_list = driver.find_elements(By.CLASS_NAME, class_name)

    return elements_list


### Select Text in Element

def helper_select_visible_text_in_element_by_id(driver, element_id: str, text_to_select: str, wait_time_in_second=30):
    """
    Waits for an element by ID and selects it by specified text.
    """
    elem = WebDriverWait(driver, wait_time_in_second).until(EC.presence_of_element_located((By.ID, element_id)))
    select = Select(elem)
    select.select_by_visible_text(text_to_select)

def helper_select_visible_text_in_element_by_name(driver, element_name: str, text_to_select: str, wait_time_in_second=30):
    """
    Waits for an element by name and selects it by specified text.
    """
    elem = WebDriverWait(driver, wait_time_in_second).until(EC.presence_of_element_located((By.NAME, element_name)))
    select = Select(elem)
    select.select_by_visible_text(text_to_select)


### Type in Element

def helper_type_in_element_by_id(driver, element_id: str, input_to_type: str, wait_time_in_second=30):
    """
    Waits for an element by ID, clears it, and types in the input.
    """
    elem = WebDriverWait(driver, wait_time_in_second).until(EC.presence_of_element_located((By.ID, element_id)))
    elem.clear()
    elem.send_keys(input_to_type)

def helper_type_in_element_by_name(driver, element_name: str, input_to_type: str, wait_time_in_second=30):
    """
    Waits for an element by name, clears it, and types in the input.
    """
    elem = WebDriverWait(driver, wait_time_in_second).until(EC.presence_of_element_located((By.NAME, 
        element_name)))
    elem.clear()
    elem.send_keys(input_to_type)


### Wait for Element

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