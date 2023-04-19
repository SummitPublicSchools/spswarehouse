import time
from spswarehouse.powerschool.powerschool import navigate_to_specific_state_report, download_latest_report_from_report_queue, switch_to_school

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def download_calpads_report_for_school(driver: WebDriver, school_full_name: str, report_name: str, file_postfix: str, destination_directory_path: str, report_parameters: dict):
    switch_to_school(driver, school_full_name)

    if(report_name == "Student Incident Records (SINC)"):
        download_calpads_report_for_school_student_incident_records_sinc(driver, school_full_name, report_name, file_postfix, destination_directory_path, 
                                                             report_start_date=report_parameters['report_start_date'],
                                                             report_end_date=report_parameters['report_end_date'],
                                                             run_validations=report_parameters['run_validations'])
    else:
        raise Exception("CALPADS report name not supported")

def download_calpads_report_for_school_student_incident_records_sinc(driver: WebDriver, school_full_name: str, report_name: str, file_postfix: str, destination_directory_path: str, 
                                                        report_start_date: str, report_end_date: str, run_validations: bool):
    
    navigate_to_specific_state_report(driver, "Student Incident Records (SINC)")
    
    # Enter specific parameters for this report
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'reportStartDate')))
    elem.clear()
    elem.send_keys(report_start_date)

    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'reportEndDate')))
    elem.clear()
    elem.send_keys(report_end_date)

    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'reportMode')))
    select = Select(elem)
    select.select_by_visible_text("Submission mode")

    time.sleep(1)

    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'bypassValidation')))
    select = Select(elem)
    if run_validations:
        select.select_by_visible_text("No")
    else:
        select.select_by_visible_text("Yes")

    # Submit report
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'submitReportSDKRuntimeParams')))
    elem.click()

    download_latest_report_from_report_queue(driver, destination_directory_path, file_postfix)