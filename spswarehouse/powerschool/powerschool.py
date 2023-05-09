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

ADMIN_LOGIN_PAGE_PATH = 'admin/pw.html'
ADMIN_HOME_PAGE_PATH = 'admin/home.html'
ADMIN_URL_SCHEME = 'https://'
STATE_REPORTS_PAGE_PATH = 'admin/reports/statereports.html?repType=state'
REPORT_QUEUE_REPORTWORKS_PAGE_PATH = 'admin/reportqueue/prhome.html'
REPORT_QUEUE_SYSTEM_PAGE_PATH = 'admin/reportqueue/home.html'

class PowerSchool:
    """
    This class is an abstraction for interacting with the PowerSchool Admin user 
    interface via Selenium.
    """

    def __init__(self, username: str=None, password: str=None, host: str=None, headless: bool=True, 
        download_location: str='.'):
        
        if username is None: 
            username = powerschool_config['username']
        else:
            username = username

        if password is None:
            password = powerschool_config['password']
        else:
            password = password

        if host is None:
            self.host = powerschool_config['host']
        else:
            self.host = host

        self.driver = DriverBuilder().get_driver(headless=headless, download_location=download_location)
        
        self._log_into_powerschool_admin(username, password)

    def quit(self):
        self.driver.quit()

    def ensure_on_desired_path(self, desired_path: str):
        """
        Checks whether the WebDriver is on the desired path. If not, navigates there.
        When using this function, consider a WebDriverWait afterwards to confirm the
        desired page has loaded.

        Parameters:
        self
        desired_path: The path to be checked against

        Returns:
        n/a
        """

        current_path = self._get_current_path()

        logging.info(f"The current path is: {current_path}")

        if(current_path == desired_path):
            logging.info("The current path is the desired path. No action taken.")
        else:
            logging.info(f"This does not match {desired_path}, so going to that path")
            self.driver.get('https://' + self._get_current_domain(self.driver) + "/" + desired_path)
            time.sleep(3) # Give new page time to load
            logging.info(f"Moved to {desired_path}.")

    def check_whether_desired_school_selected(self, school_name: str) -> bool:
        """
        Checks whether the specified school is currently selected in PowerSchool but
        takes no action either way.

        Parameters:
        self
        school_name: The school name for selecting from the drop-down in the upper-right of the user 
        interface. Should be the complete school name to avoid incorrect partial matches.

        Returns:
        bool: True indicates the desired school is selected, and False indicates it is not.
        """

        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 
            'school_picker_adminSchoolPicker_toggle_btn')))

        elem.click()
        time.sleep(1)

        selected_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '.list-item.selectable.selected')))

        school_element_text = selected_element.find_element(By.XPATH, ".//div").text

        result_message = f"Found the {school_name} in the school element text. Match!"
        outcome = True

        if(school_name not in school_element_text):
            result_message = f"Did not find {school_name} in the school element text. No match."
            outcome = False

        logging.info(result_message)

        logging.info(f"Pressing escape to leave dropdown selection.")
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.ESCAPE).perform()
        
        return outcome

    def switch_to_school(self, school_name: str):
        """
        Switches to a specified school in PowerSchool.

        Parameters:
        self
        school_name: The school name for selecting from the drop-down in the upper-right of the user 
            interface. Should be the complete school name to avoid incorrect partial matches.

        Returns:
        n/a
        """

        if self.check_whether_desired_school_selected(school_name) == False:
            logging.info(f"{school_name} is not already selected. Selecting now.")

            self.ensure_on_desired_path(ADMIN_HOME_PAGE_PATH)

            logging.info("Waiting for School Picker")
            elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 
                'school_picker_adminSchoolPicker_toggle_btn')))
            logging.info("School Picker found. Click it.")

            elem.click()

            time.sleep(1)

            logging.info("Waiting for School Search Field")
            elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 
                'schoolSearchField_value')))
            logging.info("Found School Search Field. Typing in school name.")

            elem.send_keys(school_name)

            time.sleep(1)

            logging.info("Looking for first school in list")
            elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, 
                "//ul[@id='school_choices']/li[1]")))

            logging.info("Found first school in results list. Clicking.")
            elem.click()
            logging.info("Click. Waiting for page to refresh.")
            time.sleep(1)
            
            assert self.check_whether_desired_school_selected(school_name), "Failed to select \
                desired school."
        else:
            logging.info(f"{school_name} is already selected. No action taken.")
    
    def navigate_to_state_reports_page(self):
        """
        Navigates to the state reports page in PowerSchool.

        Parameters:
        self
        
        Returns:
        n/a
        """

        self.driver.get(ADMIN_URL_SCHEME + self._get_current_domain() + '/' + STATE_REPORTS_PAGE_PATH)

        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 
            'ul li.selected')))
        assert elem.text == 'State', "'State' tab is not selected"

    def navigate_to_specific_state_report(self, report_link_text: str):
        """
        Navigates to the state reports page in PowerSchool and clicks on the report containing
        the report_link_text string.

        Parameters:
        self
        report_link_text: The string to uniquely identify the report. Can be partial text.

        Returns:
        n/a
        """
        self.navigate_to_state_reports_page()

        self.helper_click_element_by_partial_link_text(report_link_text)

    def helper_type_in_element_by_id(self, element_id: str, input_to_type: str):
        """
        Waits for an element by ID, clears it, and types in the input.
        """
        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
        elem.clear()
        elem.send_keys(input_to_type)

    def helper_type_in_element_by_name(self, element_name: str, input_to_type: str):
        """
        Waits for an element by name, clears it, and types in the input.
        """
        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.NAME, 
            element_name)))
        elem.clear()
        elem.send_keys(input_to_type)

    def helper_select_visible_text_in_element_by_id(self, element_id: str, 
        text_to_select: str):
        """
        Waits for an element by ID and selects it by specified text.
        """
        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
        select = Select(elem)
        select.select_by_visible_text(text_to_select)

    def helper_select_visible_text_in_element_by_name(self, element_name: str, 
        text_to_select: str):
        """
        Waits for an element by name and selects it by specified text.
        """
        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.NAME, 
            element_name)))
        select = Select(elem)
        select.select_by_visible_text(text_to_select)

    def helper_click_element_by_id(self, element_id: str):
        """
        Waits for an element by ID and clicks it.
        """
        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
        elem.click()

    def helper_click_element_by_partial_link_text(self, partial_link_text: str):
        """
        Waits for an element by partial link text and clicks it.
        """
        elem = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 
            f"{partial_link_text}")))
        elem.click()

    def download_latest_report_from_report_queue_reportworks(self, destination_directory_path: str = '', 
        file_postfix: str = ''):
        """
        Navigates to the PowerSchool Report Queue (ReportWorks), confirms the most recent report is 
        done generating, and downloads it.

        Parameters:
        self
        destination_directory_path: Where to download the PowerSchool report to.
        file_postfix: Optional postfix to attach to the end of the downloaded file's filename.

        Returns:
        bool: True once successfully downloads the report. Otherwise, function keeps looping.
        """

        # Pause briefly to give a just-submitted report time to get into the queue
        time.sleep(1)

        self.ensure_on_desired_path(REPORT_QUEUE_REPORTWORKS_PAGE_PATH)
        
        while True:
            # TODO: Add a counter so this function can't get stuck in an infinte loop.
            try:
                # Confirm no reports are running
                self.driver.find_element(By.XPATH, "//p[contains(text(), 'No reports running or pending!')]")
                
                # There is occasional flakiness where the "No reports running or pending!" message 
                #    shows up but the latest report is not in the list for downloading yet, so refresh 
                #    the page one more time.
                time.sleep(1)
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, 'prReloadButton')))
                self.driver.find_element(By.ID, 'prReloadButton').click()
                time.sleep(1)
            except NoSuchElementException: # Because reports ARE running
                time.sleep(5)
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, 'prReloadButton')))
                self.driver.find_element(By.ID, 'prReloadButton').click()
                logging.info('PowerSchool report is not ready, refreshing and waiting.')
                time.sleep(3)
            else:
                # Download the first report in table
                queued_reports = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((
                    By.XPATH, '//*[@id="queuecontent"]/table/tbody/tr[2]/td[7]/a')))
                download_link = queued_reports.get_attribute('href')
                original_files_list = os.listdir(destination_directory_path)
                self.driver.get(download_link) #downloads the file
                logging.info('PowerSchool report downloaded.')
                break

        self._wait_for_new_file_in_folder(destination_directory_path, original_files_list)
        self._rename_recent_file_in_dir(destination_directory_path, file_postfix)
        logging.info('Successfully renamed the downloaded file.')

        return True

    def download_latest_report_from_report_queue_system(self, destination_directory_path: str = '', 
        file_postfix: str = ''):
        """
        Navigates to the PowerSchool Report Queue (System), confirms the most recent report is done 
        generating, and downloads it.

        Parameters:
        driver: A Selenium WebDriver
        destination_directory_path: Where to download the PowerSchool report to.
        file_postfix: Optional postfix to attach to the end of the downloaded file's filename.

        Returns:
        bool: True if successfully downloads a report, or False if it cannot, either because the 
            report generated no results from the previously-submitted parameters or the report
            download page is in a format this function does not handle.
        """
        # Pause briefly to give a just-submitted report time to get into the queue
        time.sleep(1)

        self.ensure_on_desired_path(REPORT_QUEUE_SYSTEM_PAGE_PATH)

        while True:
            try:
                # Try to find a running report
                self.driver.find_element(By.XPATH, "//td[text()='Running']")

                # If yes, keep going here
                time.sleep(5)
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, 'prReloadButton')))
                self.driver.find_element(By.ID, 'prReloadButton').click()
                logging.info('PowerSchool report is not ready, refreshing and waiting.')
                time.sleep(3)
            except NoSuchElementException: # Because all reports are done running
                break

        top_completed_report_view_link = self.driver.find_element(By.XPATH, 
            '//*[@id="content-main"]/div[3]/table/tbody/tr[1]/td[5]/a')
        top_completed_report_view_link.click()

        try:
            # Look for a result file link
            download_link = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((
                By.LINK_TEXT, 'Click to Download Result File')))
            download_link.click()
            logging.info('Downloading PowerSchool report.')

            original_files_list = os.listdir(destination_directory_path)

            self._wait_for_new_file_in_folder(destination_directory_path, original_files_list)
            self._rename_recent_file_in_dir(destination_directory_path, file_postfix)
            logging.info('Successfully renamed the downloaded file.')

            return True
        except:
            try:
                # If no result file link is found, look for a confirmation that no file was generated
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, 
                    "//h1[text()='No records found']")))
                logging.info('PowerSchool reports "No records found"')
                return False
            except:
                # TODO: Check for the SCSC validation errors page and download it appropriately
                logging.info(f"Unable to confirm results. Please check manually for postfix \
                    {file_postfix}.")
                self.driver.back()
                return False
    
    def _log_into_powerschool_admin(self, username, password):
        """
        Log into PowerSchool Admin and confirm the login was successful.
        
        Parameters:
        n/a
            
        Returns:
        n/a
        """
        
        logging.info("Create webpage URL for PowerSchool Admin")
        host_full = self.host + "/" + ADMIN_LOGIN_PAGE_PATH
        logging.info(f"The webpage url is: {host_full}")
        
        logging.info("Go to webpage URL for PowerSchool Admin")
        self.driver.get(host_full)
        
        logging.info("Find the username field within the login page")
        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 
            'fieldUsername')))
        
        logging.info("Clear any pre-filled values within the username field")
        elem.clear()
        
        logging.info("Type your PowerSchool username")
        elem.send_keys(username)
        
        logging.info("Find the password field within the HTML page")
        elem = self.driver.find_element(By.ID, 'fieldPassword')
        
        logging.info("Type your PowerSchool password")
        elem.send_keys(password)
        
        logging.info("Press enter to submit your credentials and complete your login.")
        elem.send_keys(Keys.RETURN)

        try:
            logging.info("Waiting for 'Start Page' element to be visible to confirm successful login")
            elem = WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.XPATH, 
                "//h1[text()='Start Page']")))

            logging.info("Successful login confirmed!")
        except:
            raise Exception("Unable to confirm successful login to PowerSchool. Please check your \
                credentials.")

    def _get_current_domain(self):
        """
        Retrieves the current domain.
        
        Parameters:
        self

        Returns:
        str: The current domain
        """

        return self.driver.current_url[8:].split("/",1)[:1][0]

    def _get_current_path(self):
        """
        Retrieves the current path, minus the 'https://'.
        
        Parameters:
        self

        Returns:
        str: The current path
        """

        return self.driver.current_url[8:].split("/",1)[1:][0]

    def _wait_for_new_file_in_folder(self, folder_path, original_files, max_attempts=20000):
        """
        Waits until a new file shows up in a folder. Loops until that is true or max_attempts is 
        reached.

        Parameters:
        self
        folder_path: The folder being monitored.
        original_files: The list of files originally in the folder, before the new one is added.
        max_attmepts: Optional parameter that sets how many loops the function will do.

        Returns:
        n/a
        """
        file_added = False
        attempts = 0
        while True and attempts < max_attempts:
            for root, folders, files in os.walk(folder_path):
                # break 'for' loop if files found
                if len(files) > len(original_files):
                    file_added = True
                    break
                else:
                    continue
            # break 'while' loop if files found
            if file_added:
                # wait for download to complete fully after it's been added - hopefully 3 seconds 
                #    is enough.
                time.sleep(3)
                break
            attempts +=1

    def _rename_recent_file_in_dir(self, folder, append_text):
        """
        Gets the most recent file in a folder and appends text to its filename.

        Parameters:
        self
        folder: The path of the folder
        append_text: The text to appended to the filename before the extension.

        Returns:
        n/a
        """

        recent_file = get_most_recent_file_in_dir(folder)
        recent_file = recent_file.replace('\\', '/')
        new_file, file_ext = os.path.splitext(recent_file)
        new_file += append_text
        new_file += file_ext
        os.rename(recent_file, new_file)