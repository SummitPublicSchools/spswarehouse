import time
from spswarehouse.powerschool.powerschool import (
                                            navigate_to_specific_state_report, 
                                            download_latest_report_from_report_queue_reportworks, 
                                            download_latest_report_from_report_queue_system,
                                            switch_to_school)

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def download_calpads_report_for_school(driver: WebDriver, school_full_name: str, report_name: str, file_postfix: str, destination_directory_path: str, report_parameters: dict):
    switch_to_school(driver, school_full_name)

    if(report_name == "Student Incident Records (SINC)"):
        download_calpads_report_for_school_student_incident_records_sinc(driver, file_postfix, destination_directory_path, 
                                                            report_start_date=report_parameters['report_start_date'],
                                                            report_end_date=report_parameters['report_end_date']
                                                            )
    elif(report_name in ("Student Incident Results Records (SIRS)", "Student Offense Records (SOFF)")):
        download_calpads_report_for_school_student_incident_results_records_sirs_or_student_offense_records_soff(driver, file_postfix, destination_directory_path, 
                                                            report_name = report_name,
                                                            report_start_date=report_parameters['report_start_date'],
                                                            report_end_date=report_parameters['report_end_date']
                                                            )
    elif(report_name == "Student Absence Summary"):
        download_calpads_report_for_school_student_absence_summary(driver, file_postfix, destination_directory_path, 
                                                            report_name = report_name,
                                                            report_start_date=report_parameters['report_start_date'],
                                                            report_end_date=report_parameters['report_end_date']
                                                            )
    else:
        raise Exception("CALPADS report name not supported")

# TODO: Move these helper functions to the main powerschool.py file
def powerschool_report_helper_type_in_element_by_id(driver: WebDriver, element_id: str, input_to_type: str):
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
    elem.clear()
    elem.send_keys(input_to_type)

def powerschool_report_helper_type_in_element_by_name(driver: WebDriver, element_name: str, input_to_type: str):
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, element_name)))
    elem.clear()
    elem.send_keys(input_to_type)

def powerschool_report_helper_select_visible_text_in_element_by_id(driver: WebDriver, element_id: str, text_to_select: str):
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
    select = Select(elem)
    select.select_by_visible_text(text_to_select)

def powerschool_report_helper_select_visible_text_in_element_by_name(driver: WebDriver, element_name: str, text_to_select: str):
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, element_name)))
    select = Select(elem)
    select.select_by_visible_text(text_to_select)

def powerschool_report_helper_click_element_by_id(driver: WebDriver, element_id: str):
    elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, element_id)))
    elem.click()

def download_calpads_report_for_school_student_incident_records_sinc(driver: WebDriver, file_postfix: str, destination_directory_path: str, 
                                                        report_start_date: str, report_end_date: str):
    
    navigate_to_specific_state_report(driver, "Student Incident Records (SINC)")
    
    # Enter specific parameters for this report
    powerschool_report_helper_type_in_element_by_id(driver, 'reportStartDate', report_start_date)
    powerschool_report_helper_type_in_element_by_id(driver, 'reportEndDate', report_end_date)
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'reportMode', 'Submission mode') # Only 'Submission mode' is supported by this tool
    time.sleep(1) # Give page time to react
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'bypassValidation', 'Yes') # Only bypassing validations is supported by this tool

    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'submitReportSDKRuntimeParams')

    # Download report zipfile
    download_latest_report_from_report_queue_reportworks(driver, destination_directory_path, file_postfix)

def download_calpads_report_for_school_student_incident_results_records_sirs_or_student_offense_records_soff(driver: WebDriver, file_postfix: str, destination_directory_path: str, 
                                                        report_name: str, report_start_date: str, report_end_date: str):
    
    navigate_to_specific_state_report(driver, report_name)
    
    # Enter specific parameters for this report
    powerschool_report_helper_type_in_element_by_id(driver, 'reportStartDate', report_start_date)
    powerschool_report_helper_type_in_element_by_id(driver, 'reportEndDate', report_end_date)
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'bypassValidation', 'Yes') # Only bypassing validations is supported by this tool
    
    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'submitReportSDKRuntimeParams')

    # Download report zipfile
    download_latest_report_from_report_queue_reportworks(driver, destination_directory_path, file_postfix)

    return False

def download_calpads_report_for_school_student_absence_summary(driver: WebDriver, file_postfix: str, destination_directory_path: str, 
                                                        report_name: str, report_start_date: str, report_end_date: str):
    
    navigate_to_specific_state_report(driver, report_name)
    
    # Enter specific parameters for this report
    powerschool_report_helper_type_in_element_by_name(driver, 'StartDate', report_start_date)
    powerschool_report_helper_type_in_element_by_name(driver, 'EndDate', report_end_date)
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'adaFlag', 'Yes') # Defaulting to 'Yes'
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'bypass_validation', 'Yes') # Only bypassing validations is supported by this tool
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'schoolGroup', '[No Group Selected]') # Defaulting to "No Group Selected" because school should already be chosen
    
    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'btnSubmit')

    # Download report zipfile
    download_latest_report_from_report_queue_system(driver, destination_directory_path, file_postfix)

    return False