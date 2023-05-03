import time
from spswarehouse.powerschool.powerschool import (
    navigate_to_specific_state_report, 
    download_latest_report_from_report_queue_reportworks, 
    download_latest_report_from_report_queue_system,
    switch_to_school,
    powerschool_report_helper_type_in_element_by_id,
    powerschool_report_helper_type_in_element_by_name,
    powerschool_report_helper_select_visible_text_in_element_by_id,
    powerschool_report_helper_select_visible_text_in_element_by_name,
    powerschool_report_helper_click_element_by_id,
    )

from selenium.webdriver.chrome.webdriver import WebDriver

def download_calpads_report_for_school(driver: WebDriver, school_full_name: str, report_name: str, 
        school_subdistrict_name: str, file_postfix: str, destination_directory_path: str, 
        report_parameters: dict, validation_only_run: bool=False):
    """
    Switches to the desired school in PowerSchool and calls the function to generate the desired
    report. Note: This function currently only supports EOY reports. Fall 1 and Fall 2 reports
    should not use this function until it is expanded to differentiate based on the CALPADS
    submission window.
    """

    # The SCSC report needs to be run from the District Office level in order to properly generate 
    #   LEA IDs without dropping leading zeros
    if report_name == "Student Course Section Records":
        switch_to_school(driver, 'District Office')
    else:
        switch_to_school(driver, school_full_name)

    if(report_name == "Student Incident Records (SINC)"):
        return download_calpads_report_for_school_student_incident_records_sinc(
            driver=driver, 
            report_name=report_name, 
            file_postfix=file_postfix, 
            destination_directory_path=destination_directory_path, 
            report_parameters=report_parameters,
            validation_only_run=validation_only_run
            )
    elif(report_name in ("Student Incident Results Records (SIRS)", "Student Offense Records (SOFF)")):
        return download_calpads_report_for_school_student_incident_results_records_sirs_or_student_offense_records_soff(
            driver=driver,
            report_name=report_name,
            file_postfix=file_postfix, 
            destination_directory_path=destination_directory_path, 
            report_parameters=report_parameters,
            validation_only_run=validation_only_run
            )
    elif(report_name == "Student Absence Summary"):
        return download_calpads_report_for_school_student_absence_summary(
            driver=driver,
            report_name=report_name,
            file_postfix=file_postfix, 
            destination_directory_path=destination_directory_path, 
            report_parameters=report_parameters,
            validation_only_run=validation_only_run
            )
    elif(report_name == "Student Program Records"):
        return download_calpads_report_for_school_student_program_records(
            driver=driver,
            report_name=report_name,
            file_postfix=file_postfix, 
            destination_directory_path=destination_directory_path, 
            report_parameters=report_parameters,
            validation_only_run=validation_only_run
            )
    elif(report_name == "Course Section Records"):
        return download_calpads_report_for_school_course_section_records(
            driver=driver,
            report_name=report_name,
            file_postfix=file_postfix, 
            destination_directory_path=destination_directory_path, 
            report_parameters=report_parameters,
            validation_only_run=validation_only_run
            )
    elif(report_name == "Student Course Section Records"):
        return download_calpads_report_for_school_student_course_section_records(
            driver=driver,
            report_name=report_name,
            file_postfix=file_postfix, 
            destination_directory_path=destination_directory_path, 
            report_parameters=report_parameters,
            # The below is an additional parameter compared to the function calls earlier in the 
            #   if-else tree
            school_subdistrict_name=school_subdistrict_name, 
            validation_only_run=validation_only_run,
            )

    else:
        raise Exception("CALPADS report name not supported")

def download_calpads_report_for_school_student_incident_records_sinc(driver: WebDriver, 
    file_postfix: str, destination_directory_path: str, report_name: str, report_parameters: dict, 
    validation_only_run: bool=False):
    """
    Switches to the Student Incident Records (SINC) report in PowerSchool and downloads it.
    """
    navigate_to_specific_state_report(driver, report_name)
    
    # Enter specific parameters for this report
    powerschool_report_helper_type_in_element_by_id(driver, 'reportStartDate', 
        report_parameters['report_start_date'])
    powerschool_report_helper_type_in_element_by_id(driver, 'reportEndDate', 
        report_parameters['report_end_date'])
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'reportMode', 
        'Submission mode') # Only 'Submission mode' is supported by this tool
    time.sleep(1) # Give page time to react
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'bypassValidation', 
        'No' if validation_only_run else 'Yes')

    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'submitReportSDKRuntimeParams')

    # Download report zipfile
    return download_latest_report_from_report_queue_reportworks(driver, destination_directory_path, 
        file_postfix)

def download_calpads_report_for_school_student_incident_results_records_sirs_or_student_offense_records_soff(
    driver: WebDriver, file_postfix: str, destination_directory_path: str, report_name: str, 
    report_parameters: dict, validation_only_run: bool=False):
    """
    Switches to the Student Incident Results Records (SIRS) or Student Offense Records (SOFF) 
    report in PowerSchool and downloads it.
    """
    navigate_to_specific_state_report(driver, report_name)
    
    # Enter specific parameters for this report
    powerschool_report_helper_type_in_element_by_id(driver, 'reportStartDate', 
        report_parameters['report_start_date'])
    powerschool_report_helper_type_in_element_by_id(driver, 'reportEndDate', 
        report_parameters['report_end_date'])
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'bypassValidation', 
        'No' if validation_only_run else 'Yes')
    
    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'submitReportSDKRuntimeParams')

    # Download report zipfile
    return download_latest_report_from_report_queue_reportworks(driver, destination_directory_path, 
        file_postfix)

def download_calpads_report_for_school_student_absence_summary(driver: WebDriver, file_postfix: str, 
    destination_directory_path: str, report_name: str, report_parameters: dict, 
    validation_only_run: bool=False):
    """
    Switches to the Student Absence Summary (STAS) report in PowerSchool and downloads it.
    """
    navigate_to_specific_state_report(driver, report_name)
    
    # Enter specific parameters for this report
    powerschool_report_helper_type_in_element_by_name(driver, 'StartDate', 
        report_parameters['report_start_date'])
    powerschool_report_helper_type_in_element_by_name(driver, 'EndDate', 
        report_parameters['report_end_date'])
    # Below 'adaFlag' defaults to 'Yes'
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'adaFlag', 'Yes') 
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'bypass_validation', 
        'No' if validation_only_run else 'Yes')
    # Below defaults to "No Group Selected" because school should already be chosen
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'schoolGroup', 
        '[No Group Selected]') 
    
    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'btnSubmit')

    # Download report zipfile
    return download_latest_report_from_report_queue_system(driver, destination_directory_path, 
        file_postfix)

def download_calpads_report_for_school_student_program_records(driver: WebDriver, file_postfix: str, 
    destination_directory_path: str, report_name: str, report_parameters: dict, 
    validation_only_run: bool=False):
    """
    Switches to the Student Program Records (SPRG) report in PowerSchool and downloads it.
    """
    navigate_to_specific_state_report(driver, report_name)
    
    # Enter specific parameters for this report
    powerschool_report_helper_type_in_element_by_name(driver, 'startDate', 
        report_parameters['report_start_date'])
    powerschool_report_helper_type_in_element_by_name(driver, 'endDate', 
        report_parameters['report_end_date'])
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'selectProgs', 
        report_parameters['submission_type'])

    # I believe 'Non-submission mode (all records)' is the one we want to use for repeated 
    #   submissions, but there's also 'Replacement Submission Mode' which has a different flow 
    #   after clicking Submit.
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'submissionMode', 
        'Non-submission mode (all records)') 

    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'bypass_validation', 
        'No' if validation_only_run else 'Yes')
    # Below defaults to "No Group Selected" because school should already be chosen
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'schoolGroup', 
        '[No Group Selected]')

    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'btnSubmit')

    # Download report zipfile
    return download_latest_report_from_report_queue_system(driver, destination_directory_path, 
        file_postfix)

def download_calpads_report_for_school_course_section_records(driver: WebDriver, file_postfix: str, 
    destination_directory_path: str, report_name: str, report_parameters: dict, 
    validation_only_run: bool=False):
    """
    Switches to the Course Section Completion (CRSC) report in PowerSchool and downloads it.
    """
    navigate_to_specific_state_report(driver, report_name)
    
    # Enter specific parameters for this report
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'submission', 
        report_parameters['submission_type'])

    # Date fields need time to appear
    time.sleep(1) 
    powerschool_report_helper_type_in_element_by_id(driver, 'startDate', 
        report_parameters['report_start_date'])
    powerschool_report_helper_type_in_element_by_id(driver, 'endDate', 
        report_parameters['report_end_date'])
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'bypassValidation', 
        'No' if validation_only_run else 'Yes')
    powerschool_report_helper_select_visible_text_in_element_by_id(driver, 'selectCourseCode', 'No') # Do not "Include Records For Course Code 1000"

    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'submitReportSDKRuntimeParams')

    # Download report zipfile
    return download_latest_report_from_report_queue_reportworks(driver, destination_directory_path, 
        file_postfix)

def download_calpads_report_for_school_student_course_section_records(driver: WebDriver, 
    file_postfix: str, destination_directory_path: str, report_name: str, report_parameters: dict, 
    school_subdistrict_name:str, validation_only_run: bool=False):
    """
    Switches to the Student Course Completion (SCSC) report in PowerSchool and downloads it.
    """
    navigate_to_specific_state_report(driver, report_name)
    
    # Enter specific parameters for this report
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'submission', 
        report_parameters['submission_type'])
    powerschool_report_helper_type_in_element_by_name(driver, 'storeCodeList', 
        report_parameters['eoy_store_code_list'])
    # Below defaults to 'No' for 'Extract Credits for Grades 7 and 8' 
    # TODO: Research if this is correct
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'msExtract', 'No') 


    powerschool_report_helper_type_in_element_by_name(driver, 'startDate', 
        report_parameters['report_start_date'])
    powerschool_report_helper_type_in_element_by_name(driver, 'endDate', 
        report_parameters['report_end_date'])

    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'bypass_validation', 
        'No' if validation_only_run else 'Yes')
    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'selectCourseCode', 
        'No') # Do not "Include Records For Course Code 1000"

    powerschool_report_helper_select_visible_text_in_element_by_name(driver, 'subDistrict', 
        school_subdistrict_name)

    # Submit report
    powerschool_report_helper_click_element_by_id(driver, 'btnSubmit')

    # Download report zipfile
    return download_latest_report_from_report_queue_system(driver, destination_directory_path, 
        file_postfix)