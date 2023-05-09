# Code adapted from original code by Yusuph in the dops-calpad repo

# Author: Howard Shen
# Last Edited 5/8/2023

import logging
import os
import pandas as pd
import time

from datetime import date, datetime

from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException
)

from ducttape.utils import DriverBuilder
try:
    from .credentials import calpads_config
except ModuleNotFoundError:
    print("No credentials file found in spswarehouse. This could cause issues.")

class CALPADS():
    
    def __init__(
        self,
        config=None,
        username=None,
        password=None,
        host=None,
        download_location="./",
        headless=True,
    ):
        """
        By default, the class will pull the username and password from the
        credentials file in the module. You can override the credentials file
        by passing either a config dictionary or both a username and password.
        
        Parameters:
        config: A dictionary containing a username and password key. Optional.
            Supercedes the username and password in credentials.py in this module.
            Also supercedes a username and password combo passed to this function in
            addition to the config.  May also contain a host key that will supercede
            both the host parameter and the host from credentials.py
        username: A CALPADS username, which should be in the form of an email address.
            Must be paired with a password. Supercedes credentials.py.
        password: Password for the given CALPADS username. Must be paired with a username
            Supercedes credentials.py
        host: The URL for CALPADS, in the format `https://www.calpads.org`. Optional.
            Supercedes the host from credentials.py
        download_location: The local folder that you want to save files too. Defaults
            to whatever the current folder is. (Not currently used, but functionality
            planned.)
        headless: Selenium headless value. Default to True.
        """
        
        self.host = None
        if config is not None:
            username = config['username']
            password = config['password']
            if 'host' in config:
                self.host = config['host']
        elif username is not None and password is not None:
            username = username
            password = password
        else:
            username = calpads_config['username']
            password = calpads_config['password']
        
        if self.host is None and host is not None:
            self.host = host
        elif self.host is None:
            self.host = calpads_config['host']
        else:
            pass
               
        self.driver = DriverBuilder().get_driver(headless=headless)
        self._login_to_calpads(username, password)

    def quit(self):
        self.driver.quit()

    def upload_file(self, lea, submission_type, file_path):
        """
        To be used in conjunction with the create_extract method, uploads the extract via File Submission on CALPADS.

        Parameters:
        lea: The numerical value of the LEA on the CALPADS site. Find by inspecting the
            dropdown on the CALPADS page.
        submission_type: The four letter code, in all caps, for the file type you're 
            uploading
        file_path: The file path to the file you want to upload. Absolute path is
            recommended (`os.path.abspath()`). Relative path behavior untested

        Returns:
        bool: True for a successful upload, else False
        """
        
        self._select_lea(lea)
        self.driver.get(f'{self.host}/FileSubmission/FileUpload')
#         self.driver.refresh()
        
        try:
            elem = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((
                By.XPATH,
                '//*[@id="btnSearch"]'
            )))
        except TimeoutException:
            logging.info('Unable to successfully reach the File Submission web page for {}. Closing the driver.'.format(lea))
            return False

        #Choose file type for the upload
        select = Select(self.driver.find_element(By.XPATH, '//*[@id="tbFileUpload"]/tbody/tr/td[2]/select'))
        select.select_by_value(submission_type)

        #Find the file to upload by pulling the most recent file in the specific illuminate extract folder
        choose_file = self.driver.find_element(By.XPATH, '//*[@id="tbFileUpload"]/tbody/tr/td[4]/input')
        choose_file.send_keys(os.path.abspath(file_path))

        #Upload
        button = self.driver.find_element(By.XPATH, '//*[@id="btnSearch"]')
        button.click()

        try:
            success = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div.alert.alert-success.alert-dismissible.fade.in'))) #TODO: Confirm this reliably works. Otherwise, use text.
        except TimeoutException:
            logging.info('Something went wrong with the file upload for {}. Review files in directories and try again.'.format(lea)) #TODO: CALPADS provides error alerts in red on same page, should send to user
            #TODO: Provide more information on error if possible?
            return False
        else:
            logging.info('{} extract successfully uploaded for {}. Check the file submission status later.'.format(type(self).__name__, lea))
            return True
        
    def get_upload_results(self, lea, submission_type, max_wait=5):
        """
        Retrieves the validation errors for the most recent upload of the given
        submission type for the given LEA. Must be used within seven days of the upload
        (default range on CALPADS).

        Parameters:
        lea: The numerical value of the LEA on the CALPADS site. Find by inspecting the
            dropdown on the CALPADS page.
        submission_type: The four letter code, in all caps, for the file type you're 
            uploading
        max_wait: The maximum number of minutes to wait if the submission is still processing.
            Default is 5 minutes.

        Returns:
        submitted_date_string (string): ISO formate date of the submission whose errors were checked. Returns None if the file submission can't be found for whatever reason
        error_details (DataFrame): Returns a dataframe of error details, False if unable to find error details, True if file posted.
        """
        self._select_lea(lea)
        self.driver.get(f'{self.host}/FileSubmission/')
        try:
            file_elem = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, 'FileType'))
            )
        except TimeoutException:
            logging.info("Can't load View Submission page")
            return None, False

        # Filter the file list
        file_select = Select(file_elem)
        file_select.select_by_value(submission_type)
        apply_button = self.driver.find_element(By.ID, "fileSubSearch")
        apply_button.click()
        try:
            # The filtered page is identical, so sleep for a moment
            time.sleep(2)
            WebDriverWait(self.driver, 10).until(EC.text_to_be_present_in_element(
                (By.XPATH, '//*[@id="FileSubmissionSearchResults"]/table/tbody/tr[1]/td[6]'),
                submission_type
            ))
        except TimeoutException:
            logging.info(f"No recent submissions of type {submission_type}")
            return None, False

        # Process submission date
        date_text = self.driver.find_element(
            By.XPATH,
            '//*[@id="FileSubmissionSearchResults"]/table/tbody/tr[1]/td[3]'
        ).text

        submitted_datetime = datetime.strptime(date_text, "%m/%d/%Y %I:%M:%S %p")
        submitted_date_string = submitted_datetime.date().isoformat()

        file_status = self.driver.find_element(
            By.XPATH,
            '//*[@id="FileSubmissionSearchResults"]/table/tbody/tr[1]/td[8]'
        ).text

        for i in range(max_wait):
            if file_status in ['Posted', 'Failed', 'Rejected']:
                job_results_df = pd.read_html(self.driver.page_source)[0].head(1)
                break
            else:
                time.sleep(60)
                self.driver.refresh()
                time.sleep(3)
                file_status = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="FileSubmissionSearchResults"]/table/tbody/tr[1]/td[8]'
                ).text

        # Branch based on file status
        if file_status == 'Posted':
            logging.info(f"{submission_type} Posted on {submitted_date_string}")
            return submitted_date_string, job_results_df, True
        elif file_status == 'Failed':
            logging.info(f"{submission_type} Failed on {submitted_date_string}. Check manually")
            return submitted_date_string, job_results_df, False
        elif file_status == 'Rejected':
            view_errors = self.driver.find_element(
                By.XPATH,
                '//*[@id="FileSubmissionSearchResults"]/table/tbody/tr[1]/td[1]/a'
            )
            view_errors.click()
        else:
            logging.info(f"{submitted_date_string} {submission_type} not complete after {max_wait} minutes.")
            return submitted_date_string, False, False

        try:
            WebDriverWait(self.driver, 15).until(EC.text_to_be_present_in_element((
                By.XPATH,
                '//*[@id="main"]/div/div[2]/header/h1'), 'View Submission Details'
            ))
            time.sleep(2) # The file errors takes a moment to load
        except TimeoutException as t:
            logging.info('Something went wrong with loading the submission error details page.')
            return submitted_date_string, job_results_df, False

         #We expect the error details to be the second table in the HTML source
        error_details_df = pd.read_html(self.driver.page_source)[1]

        # Get errors if there are multiple pages
        error_has_next = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="FileErrors"]/div/a[3]')))

        all_error_details = []
        all_error_details.append(error_details_df)

        while 'disabled' not in error_has_next.get_attribute('class'):
            logging.info('Next Page')
            error_has_next.click()
            # Give time for next page to load
            time.sleep(10)
            next_details_df = pd.read_html(self.driver.page_source)[1] #TODO: Confirm that this is a completely new df
            all_error_details.append(next_details_df)
            error_has_next = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="FileErrors"]/div/a[3]')))

        all_error_details = pd.concat(all_error_details)
        logging.info("Successfully collected all errors from file submission error details for the {} {} extract.".format(submitted_date_string, submission_type))
        return submitted_date_string, job_results_df, all_error_details
    
    def get_certification_status(self, lea, academic_year, submission_name, **kwargs):
        """
        Retrieves the status of a Certification window.

        Parameters:
        lea: The numerical value of the LEA on the CALPADS site. Find by inspecting the
            dropdown on the CALPADS page.
        academic_year: Integer representing the academic year that you want to check (per team norms,
            this is the year when the school year ends)
        submission_name: The name of the certification window. As of this edit, the certification windows are
            Fall1, Fall2, EOY1, EOY2, EOY3, and EOY4.
        optional arguments (kwargs):
            rollover_date: Applies only to EOY3. An ISO format string (YYYY-MM-DD) representing the expected
                rollover date of your SIS. The SIS rollover is when exit dates and exit codes get put on 
                enrollment records. Prior to this, CALPADS will return CERT131 errors for every actively enrolled
                student. This function will begin scraping CERT131 the day after the rollover date.
                If you do not pass a rollover date, CERT131 will be scraped.

        Returns:
        cert_status (Boolean): Returns False if the certification window isn't open yet; returns True if it is.
        error_details (DataFrame): Returns a dataframe of error details, None if no errors,
            None if certification window isn't open.
        warning_details (DataFrame): Returns a dataframe of warningsdetails, None if no warnings,
            None if certification window isn't open.
        """
        
        # Fall1, EOY3, EOY4 have a SELPA approval, which
        # creates an extra table on the Cert status page, altering the XPATH
        if submission_name in ['Fall1', 'EOY3', 'EOY4']:
            data_div_num = 5
            data_table_num = 3
            error_table_num = 1
            warning_table_num = 2
        else:
            data_div_num = 4
            data_table_num = 2
            error_table_num = 0
            warning_table_num = 1
        
        # CERT131 is somewhat meaningless prior to the end of the year
        if submission_name == 'EOY3':
            try:
                rollover_date = date.fromisoformat(kwargs['rollover_date'])
                cert131_flag = date.today() > rollover_date
                logging.info(f"Today is {date.today()}, Rollover date is {rollover_date}, CERT131 = {cert131_flag}")
            except KeyError:
                # KeyError means rollover_date was not passed as an argument
                logging.info("No rollover date passed; scraping CERT131")
                cert131_flag = True
        else:
            cert131_flag = True
        
        self._select_lea(lea)
        
        academic_year_string = f"{academic_year-1}-{academic_year}"
        self.driver.get(f"https://www.calpads.org/StateReporting/Certification?AcademicYear={academic_year_string}&Snapshot={submission_name}")
        
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((
                By.XPATH,
                '/html/body/div[1]/main/div/div[2]/div[3]/div/div/div/div/table/tbody/tr/td[1]'
            )))
        except TimeoutException:
            logging.info(f"{submission_name} certification errors not available yet")
            return False, None, None
        
        error_and_warn_text = self.driver.find_element(
            By.XPATH,
            "/html/body/div[1]/main/div/div[2]/div[3]/div/div/div/div/table/tbody/tr/td[9]"
        ).text
        error_and_warn_count = int(error_and_warn_text)

        if error_and_warn_count > 0:
            cert_status_link = self.driver.find_element(
                By.XPATH,
                '/html/body/div[1]/main/div/div[2]/div[3]/div/div/div/div/table/tbody/tr/td[1]/a'
            )
            cert_status_link.click()
            try:
                WebDriverWait(self.driver, 10).until(EC.text_to_be_present_in_element(
                    (
                        By.XPATH,
                        '/html/body/div/main/div/div[2]/header/h1'
                    ),
                    'Certification Details - LEA'
                ))
            except TimeoutException:
                logging.info("Failed to load Certification Status page")
                raise RuntimeError("Failed to load Certification Status page")
            try:
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((
                    By.XPATH,
                    f'/html/body/div/main/div/div[2]/div[{data_div_num}]/div[1]/div[1]/div/ul/li/div/div/div/table/tbody/tr/td[4]/a'
                )))
                # Error list should be the second table
                errors_table = pd.read_html(self.driver.page_source)[error_table_num]
                error_df = pd.DataFrame()
                
                error_list_has_next = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="RequiredGrid_FATAL"]/div/a[3]'
                )
                while 'disabled' not in error_list_has_next.get_attribute('class'):
                    logging.info("Getting next page of errors list")
                    try:
                        error_list_has_next.click()
                    except ElementNotInteractableException:
                        banner = self.driver.find_element(
                            By.XPATH,
                            '//*[@id="CertificationErrorSummary"]/li/a'
                        )
                        banner.click()
                        error_list_has_next.click()
                    time.sleep(2)
                    errors_table = pd.concat(
                        [errors_table, pd.read_html(self.driver.page_source)[error_table_num]],
                        axis=0,
                        ignore_index=True
                    )
                    error_list_has_next = self.driver.find_element(
                        By.XPATH,
                        '//*[@id="RequiredGrid_FATAL"]/div/a[3]'
                    )
                
                for i in range(len(errors_table)):
                    error_id = errors_table["Message ID"][i]

                    if error_id == 'CERT131' and not cert131_flag:
                        logging.info("Skipping CERT131")
                        continue
                        
                    logging.info(f"Getting list for {error_id}")
                    error_dropdown = self.driver.find_element(
                        By.ID,
                        'CertificationEditQuery_ChildErrorCategory'
                    )
                    error_select = Select(error_dropdown)
                    error_select.select_by_value(error_id)
                    apply_button = self.driver.find_element(
                        By.XPATH,
                        '//*[@id="certDetails"]/div[1]/div[3]/div/div/form/div[3]/button'
                    )
                    apply_button.click()
                    
                    try:
                        WebDriverWait(self.driver, 15).until(EC.text_to_be_present_in_element(
                            (
                                By.XPATH,
                                f'/html/body/div/main/div/div[2]/div[{data_div_num}]/div[1]/div[4]/div/div/table/tbody/tr/td[10]/a'
                            ),
                            error_id
                        ))
                    except TimeoutException:
                        logging.info(f"Can't load errors for {error_id}")
                        raise RuntimeError(f"Can't load errors for {error_id}")
                    
                    error_has_next = self.driver.find_element(
                        By.XPATH,
                        '//*[@id="RequiredGrid"]/div/a[3]'
                    )
                    
                    error_df = pd.concat(
                        [error_df, pd.read_html(self.driver.page_source)[data_table_num]],
                        axis=0,
                        ignore_index=True,
                    )
                    
                    while 'disabled' not in error_has_next.get_attribute('class'):
                        logging.info("Getting next page")
                        error_has_next.click()
                        time.sleep(2)
                        error_df = pd.concat(
                            [error_df, pd.read_html(self.driver.page_source)[data_table_num]],
                            axis=0,
                            ignore_index=True,
                        )
                        error_has_next = self.driver.find_element(
                        By.XPATH,
                        '//*[@id="RequiredGrid"]/div/a[3]'
                        )
                    
                # Drop the "View" button column
                error_df.drop(columns="Error Record", inplace=True)
                
            except TimeoutException:
                logging.info(f"No errors for {submission_name}")
                error_df = None
            
            # Get Warnings
            try:
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((
                    By.XPATH,
                    f'/html/body/div/main/div/div[2]/div[{data_div_num}]/div[1]/div[2]/div/ul/li/div/div/div/table/tbody/tr/td[4]/a'
                )))
                # Warning list should be the third table
                warnings_table = pd.read_html(self.driver.page_source)[warning_table_num]
                warning_df = pd.DataFrame()
                
                warning_list_has_next = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="RequiredGrid_WARN"]/div/a[3]'
                )
                while 'disabled' not in warning_list_has_next.get_attribute('class'):
                    logging.info("Getting next page of warnings list")
                    try:
                        warning_list_has_next.click()
                    except ElementNotInteractableException:
                        banner = self.driver.find_element(
                            By.XPATH,
                            '//*[@id="CertificationWarnSummary"]/li/a'
                        )
                        banner.click()
                        warning_list_has_next.click()
                    time.sleep(2)
                    warnings_table = pd.concat(
                        [warnings_table, pd.read_html(self.driver.page_source)[warning_table_num]],
                        axis=0,
                        ignore_index=True
                    )
                    warning_list_has_next = self.driver.find_element(
                        By.XPATH,
                        '//*[@id="RequiredGrid_WARN"]/div/a[3]'
                    )
                
                for i in range(len(warnings_table)):
                    warning_id = warnings_table["Message ID"][i]
                        
                    logging.info(f"Getting list for {warning_id}")
                    warning_dropdown = self.driver.find_element(
                        By.ID,
                        'CertificationEditQuery_ChildErrorCategory'
                    )
                    warning_select = Select(warning_dropdown)
                    warning_select.select_by_value(warning_id)
                    apply_button = self.driver.find_element(
                        By.XPATH,
                        '//*[@id="certDetails"]/div[1]/div[3]/div/div/form/div[3]/button'
                    )
                    apply_button.click()
                    
                    try:
                        WebDriverWait(self.driver, 15).until(EC.text_to_be_present_in_element(
                            (
                                By.XPATH,
                               f'/html/body/div/main/div/div[2]/div[{data_div_num}]/div[1]/div[4]/div/div/table/tbody/tr/td[10]/a'
                            ),
                            warning_id
                        ))
                    except TimeoutException:
                        logging.info(f"Can't load errors for {warning_id}")
                        raise RuntimeError(f"Can't load errors for {warning_id}")
                    
                    warning_has_next = self.driver.find_element(
                        By.XPATH,
                        '//*[@id="RequiredGrid"]/div/a[3]'
                    )
                    
                    warning_df = pd.concat(
                        [warning_df, pd.read_html(self.driver.page_source)[data_table_num]],
                        axis=0,
                        ignore_index=True,
                    )
                    
                    while 'disabled' not in warning_has_next.get_attribute('class'):
                        logging.info("Getting next page")
                        warning_has_next.click()
                        time.sleep(2)
                        warning_df = pd.concat(
                            [warning_df, pd.read_html(self.driver.page_source)[data_table_num]],
                            axis=0,
                            ignore_index=True,
                        )
                        warning_has_next = self.driver.find_element(
                            By.XPATH,
                            '//*[@id="RequiredGrid"]/div/a[3]'
                        )
                    
                # Drop the "View" button column
                warning_df.drop(columns="Error Record", inplace=True)
                
            except TimeoutException:
                logging.info(f"No warnings for {submission_name}")
                warning_df = None
                
            return True, error_df, warning_df
        elif error_and_warn_count == 0:
            logging.info(f"No errors or warnings for {submission_name}")
            return True, None, None
        else:
            raise RuntimeError("Impossible part of error_and_warn_count if-elif-else reached.")
        
    def _login_to_calpads(self, username, password):
        self.driver.get(self.host)
        try:
            WebDriverWait(self.driver, 7).until(EC.presence_of_element_located((
                By.XPATH,
                '/html/body/div[3]/div/form/div/div[2]/fieldset/div[4]/div/button'
            )))
        except TimeoutException:
            logging.info("Was unable to reach the login page. Check the browser: {}".format(self.driver.title))
            return False
        except NoSuchElementException:
            logging.info("Was unable to reach the login page. Check the browser: {}".format(self.driver.title))
            return False
        user = self.driver.find_element(By.ID, "Username")
        user.send_keys(username)
        pw = self.driver.find_element(By.ID, "Password")
        pw.send_keys(password)
        agreement = self.driver.find_element(By.ID, "AgreementConfirmed")
        self.driver.execute_script("arguments[0].click();", agreement)
        btn = self.driver.find_element(
            By.XPATH,
            "/html/body/div[3]/div/form/div/div[2]/fieldset/div[4]/div/button"
        )
        btn.click()
        try:
            WebDriverWait(self.driver, 7).until(EC.presence_of_element_located((
                By.ID,
                'org-select'
            )))
        except TimeoutException:
            logging.info('Something went wrong with the login. Checking to see if there was an expected error message.')
            try:
                alert = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/div[3]/div/form/div[1]'
                )))
                if 'alert' in alert.get_attribute('class'):
                    logging.info("Found an expected alert during login: '{}'".format(
                        self.driver.find_element(
                            By.XPATH, '/html/body/div[3]/div/form/div[1]/div/ul/li'
                        ).text
                    ))
                    return False
                else:
                    logging.info('There was an unexpected message during login. See driver.')
                    return False
            except TimeoutException:
                logging.info('There was an unexpected error during login. See driver.')
                return False

        return True
    
    def _select_lea(self, lea):
        """
        Factored out common process for switching to a different LEA in the dropdown

        Parameters:
        lea: The numerical value of the LEA on the CALPADS site. Find by inspecting the
            dropdown on the CALPADS page.
        """
        select = Select(self.driver.find_element(By.ID, 'org-select'))
        select.select_by_value(lea)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, 'org-select')))
        
