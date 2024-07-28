import logging
import time
import os
import math
import pandas as pd

try:
    from spswarehouse.credentials import powerschool_config
except ModuleNotFoundError:
    powerschool_config = None
    print("No credentials file found in spswarehouse. This could cause issues.")

from ducttape.utils import (
    DriverBuilder,
    get_most_recent_file_in_dir,
)

from spswarehouse.general.selenium import (
    type_in_element_by_id,
    select_visible_text_in_element_by_id,
    click_element_by_id,
    click_element_by_name,
    click_element_by_partial_link_text,
    wait_for_element_containing_specific_text,
)
    
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
DATA_IMPORT_MANAGER_PATH = 'admin/datamgmt/importmanager.action'

DEPRECATION_WARNING_MESSAGE = "DEPRECATION_WARNING: This helper function in the PowerSchool class will be deprecated in a future release. Use the helper functions in general.selenium instead."

class PowerSchool:
    """
    This class is an abstraction for interacting with the PowerSchool Admin user 
    interface via Selenium.
    """

    def __init__(
        self,
        config: dict=None,
        username: str=None,
        password: str=None,
        host: str=None,
        headless: bool=True, 
        download_location: str='.',
        chrome_option_prefs: dict=None,
    ):
        
        if config is None:
            config = powerschool_config
        
        if username is None: 
            username = config['username']
        else:
            username = username

        if password is None:
            password = config['password']
        else:
            password = password

        if host is None:
            self.host = config['host']
        else:
            self.host = host

        self.driver = DriverBuilder().get_driver(
            headless=headless,
            download_location=download_location,
            chrome_option_prefs=chrome_option_prefs,
        )
        
        self._log_into_powerschool_admin(username, password)

    def quit(self):
        self.driver.quit()

    def refresh(self):
        self.driver.refresh()

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
            self.driver.get('https://' + self._get_current_domain() + "/" + desired_path)
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
    
    def check_whether_desired_school_year_selected(self, school_year_dropdown: str):
        """
        Checks whether the specified school year is currently selected in PowerSchool but
        takes no action either way.

        Parameters:
        self
        school_year_dropdown: The exact text of the school year that appears in the dropdown in 
            PowerSchool. Should be 'XX-YY 20XX-20YY' format.

        Returns:
        bool: True indicates the desired school year is selected, and False indicates it is not.
        """

        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 
            'term_picker_adminTermPicker_toggle_btn')))

        elem.click()
        time.sleep(1)

        selected_element = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '.list-item.selectable.selected')))

        school_year_element_text = selected_element.find_element(By.XPATH, ".//div").text

        result_message = f"Found '{school_year_dropdown}' in the school year element text. Match!"
        outcome = True

        if(school_year_dropdown not in school_year_element_text):
            result_message = f"Did not find '{school_year_dropdown}' in the school year element text. No match."
            outcome = False

        logging.info(result_message)

        logging.info(f"Pressing escape to leave dropdown selection.")
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.ESCAPE).perform()
        
        return outcome
    
    def switch_to_school_year(self, school_year_dropdown: str):
        """
        Switches to a specified school year in PowerSchool.

        Parameters:
        self
        school_year_dropdown: The exact text of the school year that appears in the dropdown in 
            PowerSchool. Should be 'XX-YY 20XX-20YY' format.

        Returns:
        n/a
        """
        if self.check_whether_desired_school_year_selected(school_year_dropdown) == False:
            logging.info(f"'{school_year_dropdown}' is not already selected. Selecting now.")

            self.ensure_on_desired_path(ADMIN_HOME_PAGE_PATH)

            logging.info("Waiting for School Year Picker")
            elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 
                'term_picker_adminTermPicker_toggle_btn')))
            logging.info("School Year Picker found. Click it.")

            elem.click()

            time.sleep(1)

            logging.info("Waiting for School Year Search Field")
            elem = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.ID, 
                'termText')))
            logging.info("Found School Year Search Field. Typing in school year text.")

            # Only send the XX-YY portion of the dropdown text
            elem.send_keys(school_year_dropdown[:5])

            time.sleep(1)

            logging.info("Looking for first school year in list")
            
            elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, 
                "//ul[@id='term_choices']/li[2]"))) # This is li[2] instead of li[1] because there is read-only school year item displayed

            logging.info("Found first school year in results list. Clicking.")
            elem.click()
            logging.info("Click. Waiting for page to refresh.")
            time.sleep(1)
            
            assert self.check_whether_desired_school_year_selected(school_year_dropdown), "Failed to select \
                desired school year."
        else:
            logging.info(f"'{school_year_dropdown}' is already selected. No action taken.")

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
            elem = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.ID, 
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

        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 
            '.stateDiv')))

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

        click_element_by_partial_link_text(self.driver, report_link_text)



### START TODO: These helper functions inside the PowerSchool class will be removed in a future release. ##############
###             The functions in general.selenium should be used instead. #############################################

    def helper_type_in_element_by_id(self, element_id: str, input_to_type: str):
        """
        Waits for an element by ID, clears it, and types in the input.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
        elem.clear()
        elem.send_keys(input_to_type)

    def helper_type_in_element_by_name(self, element_name: str, input_to_type: str):
        """
        Waits for an element by name, clears it, and types in the input.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.NAME, 
            element_name)))
        elem.clear()
        elem.send_keys(input_to_type)

    def helper_select_visible_text_in_element_by_id(self, element_id: str, 
        text_to_select: str):
        """
        Waits for an element by ID and selects it by specified text.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
        select = Select(elem)
        select.select_by_visible_text(text_to_select)

    def helper_select_visible_text_in_element_by_name(self, element_name: str, 
        text_to_select: str):
        """
        Waits for an element by name and selects it by specified text.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        elem = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.NAME, 
            element_name)))
        select = Select(elem)
        select.select_by_visible_text(text_to_select)

    def helper_click_element_by_id(self, element_id: str):
        """
        Waits for an element by ID and clicks it.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        elem = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.ID, element_id)))
        elem.click()

    def helper_click_element_by_name(self, element_name: str):
        """
        Waits for an element by name and clicks it.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        elem = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.NAME, element_name)))
        elem.click()

    def helper_click_element_by_partial_link_text(self, partial_link_text: str):
        """
        Waits for an element by partial link text and clicks it.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        elem = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 
            f"{partial_link_text}")))
        elem.click()

    def helper_ensure_checkbox_is_checked_by_name(self, checkbox_name: str):
        """
        Waits for a checkbox element by name and clicks it if it is not already selected.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        checkbox = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, 
            f"//input[@type='checkbox' and @name='{checkbox_name}']")))
        
        if checkbox.is_selected() == False:
            checkbox.click()
    
    def helper_ensure_checkbox_is_unchecked_by_name(self, checkbox_name: str):
        """
        Waits for a checkbox element by name and clicks it if it is already selected, to make
        sure it is not checked.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        checkbox = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, 
            f"//input[@type='checkbox' and @name='{checkbox_name}']")))
        
        if checkbox.is_selected():
            checkbox.click()

    def helper_ensure_element_text_matches_expected_value_by_xpath(self, element_xpath, expected_text):
        """
        Waits for an element by XPATH and checks whether its text matches the expected text.
        """
        print(DEPRECATION_WARNING_MESSAGE)

        elem = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, 
            element_xpath)))
        
        return elem.text == expected_text
    
    def helper_wait_for_element_containing_specific_text(self, expected_element_text, wait_time_in_seconds=30):
        """
        Waits for an element containing specific text raises an exception if it does not 
        appear in the time allotted (default = 30 seconds).
        """
        print(DEPRECATION_WARNING_MESSAGE)

        try:
            WebDriverWait(self.driver, wait_time_in_seconds).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{expected_element_text}')]")))
        except:
            raise Exception(f'Element with text "{expected_element_text}" not found within {wait_time_in_seconds} seconds.')

### END TODO #########################################################################################################



    def download_latest_report_from_report_queue_reportworks(self, destination_directory_path: str = '.', 
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
        self.ensure_on_desired_path(REPORT_QUEUE_REPORTWORKS_PAGE_PATH)

        # Pause briefly to give the just-submitted report time to get into the queue
        time.sleep(5)

        # Confirm that the page has loaded
        elem = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, 'prReloadButton')))
        elem.click()
        logging.info('Refresh button on report page has loaded. Refreshing.')
        
        while True:
            # TODO: Add a counter so this function can't get stuck in an infinte loop.
            try:
                # Confirm no reports are running
                self.driver.find_element(By.XPATH, "//p[contains(text(), 'No reports running or pending!')]")
                
                # TODO: Is the below refresh necessary when we're refreshing upon first hitting this page?
                # There is occasional flakiness where the "No reports running or pending!" message 
                #    shows up but the latest report is not in the list for downloading yet, so refresh 
                #    the page one more time.
                time.sleep(1)
                elem = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, 'prReloadButton')))
                elem.click()
                time.sleep(1)
            except NoSuchElementException: # Because reports ARE running
                time.sleep(5)
                elem = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, 'prReloadButton')))
                elem.click()
                logging.info('PowerSchool report is not ready, refreshing and waiting.')
                time.sleep(3)
            else:
                # Download the first report in table
                queued_reports = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((
                    By.XPATH, '//*[@id="queuecontent"]/table/tbody/tr[2]/td[8]/a')))
                download_link = queued_reports.get_attribute('href')
                original_files_list = os.listdir(destination_directory_path)
                self.driver.get(download_link) #downloads the file
                logging.info('PowerSchool report downloaded.')
                break

        self._wait_for_new_file_in_folder(destination_directory_path, original_files_list)
        self._rename_recent_file_in_dir(destination_directory_path, file_postfix)
        logging.info('Successfully renamed the downloaded file.')

        return True

    def download_latest_report_from_report_queue_system(self, destination_directory_path: str = '.', 
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
        self.ensure_on_desired_path(REPORT_QUEUE_SYSTEM_PAGE_PATH)

        # Pause briefly to give the just-submitted report time to get into the queue
        time.sleep(5)

        # Confirm that the page has loaded
        elem = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, 'prReloadButton')))
        elem.click()
        logging.info('Refresh button on report page has loaded. Refreshing.')

        while True:
            try:
                # Try to find a running report
                self.driver.find_element(By.XPATH, "//td[text()='Running']")

                # If yes, keep going here
                time.sleep(5)
                elem = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, 'prReloadButton')))
                elem.click()
                logging.info('PowerSchool report is not ready, refreshing and waiting.')
                time.sleep(3)
            except NoSuchElementException: # Because all reports are done running
                logging.info('No currently running reports. Downloading the most recently completed report.')
                break

        top_completed_report_view_link = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH,
            "//*[@id='content-main']/div[3]/table/tbody/tr[1]/td[a[text()='View']][1]/a"))) 
            # Note: The above XPATH seems to change a lot as PowerSchool makes changes to which column the link is in.
            # This is the hard-coded XPATH for the 6th column: '//*[@id="content-main"]/div[3]/table/tbody/tr[1]/td[6]/a'
            # The above XPATH tries to dynamically determine which column the link is in to be robust to these changes.
        top_completed_report_view_link.click()

        try:
            # Look for a result file link
            logging.info('Looking for the result file link.')
            download_link = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((
                By.LINK_TEXT, 'Click to Download Result File')))
            original_files_list = os.listdir(destination_directory_path)
            download_link.click()
            logging.info('Downloading PowerSchool report.')

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
    
    def upload_student_csv_quick_import(self, filename):
        """
        Uploads a file to Quick Import. Requires your file to
        1. be a CSV
        2. have a header row
        3. have header names that can be auto-matched by PowerSchool
        4. have a column called "student_number"
        """
        
        import_data = pd.read_csv(filename, dtype=str)
        final_student_number = import_data.iloc[-1]['student_number']
        
        self.upload_csv_quick_import(filename, final_student_number, 'Students')
        
    def upload_csv_quick_import(self, filename, final_value, table_name):
        """
        Uploads a CSV file to quick import.
        
        Arguments:
        filename: Path to the file.
        final_value: A value in the final row of the file that can be used to identify
            when PS is done processing the file.
        table_name: Exact value of the table name from the PS UI
        """
        
        # Convert the file to a tab-delimited file
        import_data = pd.read_csv(filename, encoding='mac_roman', dtype=str)
        
        new_filename = filename + ".tsv"
        
        import_data.to_csv(
            new_filename,
            index=False,
            sep='\t',
            encoding='mac_roman',
            # The "CR" option in PS's quick import, which is the default, is in fact "\n"
            lineterminator = "\r",
        )
        
        self.upload_quick_import(new_filename, final_value, table_name)
        
    def upload_quick_import(self, filename, final_value, table_name):
        """
        Uploads a tab-delimited file to quick import.
        
        Arguments:
        filename: Path to the file.
        final_value: A value in the final row of the file that can be used to identify
            when PS is done processing the file.
        """
        
        # Upload may cover multiple schools, so should be done at the District Office level
        self.switch_to_school('District Office')

        # Go to Quick Import page
        self.ensure_on_desired_path('admin/importexport/quickimport/quickimport1.html')

        # Upload to designated table
        logging.info(f"Selecting {table_name} for table")
        select_visible_text_in_element_by_id(self.driver, 'filenumber', table_name)
        
        # Choose file to upload
        type_in_element_by_id(self.driver, 'filename', filename)

        # Submit file
        click_element_by_id(self.driver, 'btnImport')

        # Choose "Check to exclude first row"
        click_element_by_name(self.driver, 'skipFirstRow')

        # Choose "Update the student's record with the information from the file being imported."
        click_element_by_id(self.driver, 'rdioc_update')

        # Submit
        click_element_by_id(self.driver, 'btnSubmit')
        logging.info("Submitting file")

        # Check that file finished processing
        logging.info(f'Waiting for student ID #{final_value} to appear to indicate that the file is finished processing.')
        wait_for_element_containing_specific_text(self.driver, final_value, 60)
        logging.info('Final student found. Upload file finished processing.')
        
    def upload_data_import_manager(self, file_path, table_name, max_processing_wait_time_in_seconds = 60, 
        override_existing_record = False):
        """
        Uploads a tab-delimited file to the Data Import Manager.
        
        Arguments:
        file_path: Path to the tab-delimited file.
        table_name: The name of the PowerSchool table to upload to.
        max_processing_wait_time_in_seconds: The maximum number of seconds to wait for the file to processing.
            The processing check happens every 10 seconds, so this number will be divided by 10 and rounded down
            to determine how many checks to make. e.g., a value of 35 will check 3 times, which is roughly 30 seconds.
        override_existing_record: Defaults to False. Submit as True to have the function select the option to override
            existing records as part of the import. WARNING: Be very careful when using this feature, since overriding 
            records in PowerSchool requires very precisely formatted files, and if anything is incorrect, the system
            will likely create duplicate records. Please extensively test the file you are importing.
        """

        df_row_count = pd.read_csv(file_path)
        num_data_rows = df_row_count.shape[0]

        if num_data_rows == 0:
            raise Exception(f'Upload file at path "{file_path}" does not contain any rows of data.')

        num_rows_in_file = num_data_rows + 1 # Add 1 to account for the header row

        logging.info('Switching to the "District Office" for a Data Import Manager upload.')
        self.switch_to_school('District Office')

        self.ensure_on_desired_path(DATA_IMPORT_MANAGER_PATH)

        logging.info('Choosing the upload file.')
        type_in_element_by_id(self.driver, 'idFilename', file_path)

        logging.info('Selecting the upload table.')
        select_visible_text_in_element_by_id(self.driver, 'moduleSelect', table_name)
        
        # Need to give the UI a moment to catch up to the fact that a table has been selected.
        # (The button is already clickable when a table is unselected, but gives an error)
        time.sleep(5)
        logging.info('Clicking Next')
        click_element_by_id(self.driver, 'nextButton0')

        # Brief pause to allow for loading next part of the screen
        time.sleep(10)

        # Double-check that there is no overlay that will intercept the clicks
        WebDriverWait(self.driver, 30).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ui-widget-overlay")))

        logging.info('Assuming all fields mapped properly.')
        click_element_by_id(self.driver, 'nextButton1')

        # WARNING: Be VERY careful when overriding existing records, because PowerSchool can create duplicates if the upload
        #   file is not precisely what the system expects.
        if override_existing_record:
            logging.info('Because override_existing_record was specified as True, clicking the corresponding radio button.')
            click_element_by_id(self.driver, 'override_existing_value_override')

        logging.info('Beginning import.')
        click_element_by_id(self.driver, 'btnImport')

        logging.info('Checking for message to indicate processing is complete.')
        # Note: the ":,d" turns the number into a *comma-delimited* string, which is what Powerschool does (e.g. 1234 = "1,234")
        # Without this, the function will fail for files with >= 1000 (or: "1,000") rows
        finished_processing_text = f'Processed {num_rows_in_file:,d} out of {num_rows_in_file:,d} records'
        done_processing = False

        num_of_loops = math.floor(max_processing_wait_time_in_seconds // 10)
        
        for i in range(num_of_loops):
            try:
                logging.info(f'Check #{i + 1} of {num_of_loops}')
                wait_for_element_containing_specific_text(self.driver, finished_processing_text, 10)
                logging.info('File is done processing.')
                done_processing = True
                break
            except:
                logging.info('Message not found yet. Refreshing.')
                self.refresh()

        if done_processing == False:
            raise Exception(f'Something went wrong. File did not finish processing within {max_processing_wait_time_in_seconds} seconds.')

        logging.info('Checking whether all records imported successfully.')
            
        # Same thing here as above with ':,d' to turn 1234 => "1,234"
        successful_import_text = f'Imported:  {num_rows_in_file:,d}'
        imported_element_text = self.driver.find_element(By.XPATH, "//div[@id='importResultsContent']/div[2]/h3").text 

        # Using the old wait_for_element_containing_specific_text() function did not work for finding the right message, so the above
        #    line gets the "Imported:  X" message 

        assert imported_element_text == successful_import_text, 'Import message indicates not all files imported successfully.'

        logging.info('All records imported successfully. Upload is complete.')

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
