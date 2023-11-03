from datetime import datetime, date
import time
import pandas as pd

from .powerschool import PowerSchool

from spswarehouse.general.selenium import (
    helper_type_in_element_by_name,
    helper_select_visible_text_in_element_by_name,
    helper_click_element_by_id,
    helper_ensure_checkbox_is_unchecked_by_name,
    helper_ensure_checkbox_is_checked_by_name,
    helper_type_in_element_by_id,
    helper_select_visible_text_in_element_by_id,
)

PS_REPORT_LINK_TEXT = {
    'SINC': 'Student Incident Records (SINC)',
    'SIRS': 'Student Incident Results Records (SIRS)',
    'SOFF': 'Student Offense Records (SOFF)',
    'STAS': 'Student Absence Summary',
    'SPRG': 'Student Program Records',
    'CRSC': 'Course Section Records',
    'SCSC': 'Student Course Section Records',
    'SENR': 'SSID Enrollment Records',
    'SELA': 'Student EL Acquisition Records',
    'SINF': 'Student Information Records',
}

# Used for making the standard modifications to the Student English Language Acquistion (SELA) upload file; column #'s from the CALPADS file specifications
SELA_COLUMN_NAMES = [
    'Record Type Code', # 12.01
    'Transaction Type Code', # 12.02
    'Local Record ID', #12.03
    'Reporting LEA', #12.04
    'School of Attendance', #12.05
    'Academic Year ID', #12.06
    'SSID', #12.07
    'Student Legal First Name', #12.08
    'Student Legal Last Name', #12.09
    'Student Birth Date', #12.10
    'Student Gender Code', #12.11
    'Local Student ID', #12.12
    'English Language Acquisition Status Code', #12.13
    'English Language Acquisition Status Start Date', #12.14
    'Primary Language Code', #12.15
    'Correction Reason Code', #12.16
]

class PowerSchoolCALPADS(PowerSchool):
    """
    This class extends the PowerSchool class in order to download CALPADS
    reports.
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
        
        super().__init__(config, username, password, host, headless, download_location, chrome_option_prefs)

    def download_calpads_report_for_school(self, school_full_name: str, submission_window: str, 
        calpads_report_abbreviation: str, ps_school_subdistrict_name: str, file_postfix: str, 
        destination_directory_path: str, report_parameters: dict, ps_school_year_dropdown=None, 
        validation_only_run: bool=False):
        """
        Switches to the desired school in PowerSchool and calls the function to generate the desired
        report for the specified submission window. Note: This function currently only supports EOY 
        reports and some All Year reports. Fall 1 and Fall 2 reports should not use this function until 
        it is expanded.
        """

        report_kwargs = {
            'ps_report_link_text': PS_REPORT_LINK_TEXT[calpads_report_abbreviation], 
            'file_postfix': file_postfix, 
            'destination_directory_path': destination_directory_path, 
            'report_parameters': report_parameters,
            'validation_only_run': validation_only_run
        }
        
        # Choose the school year if one is provided
        if ps_school_year_dropdown is not None:
            self.switch_to_school_year(ps_school_year_dropdown)

        # The SCSC report needs to be run from the District Office level in order to properly generate 
        #   LEA IDs without dropping leading zeros
        if calpads_report_abbreviation == "SCSC":
            self.switch_to_school('District Office')
        else:
            self.switch_to_school(school_full_name)

        if(submission_window == 'EOY'):
            if(calpads_report_abbreviation == "SINC"):
                return self._download_eoy_report_for_student_incident_records_sinc(**report_kwargs)
            elif(calpads_report_abbreviation in ('SIRS', 'SOFF')):
                return self._download_eoy_report_for_student_incident_results_records_sirs_or_student_offense_records_soff(
                    **report_kwargs
                )
            elif(calpads_report_abbreviation == 'STAS'):
                return self._download_eoy_report_for_student_absence_summary_stas(**report_kwargs)
            elif(calpads_report_abbreviation == 'SPRG'):
                return self._download_eoy_report_for_student_program_records_sprg(**report_kwargs)
            elif(calpads_report_abbreviation == 'CRSC'):
                return self._download_eoy_report_for_course_section_records_crsc(**report_kwargs)
            elif(calpads_report_abbreviation == 'SCSC'):
                return self._download_eoy_report_for_student_course_section_records_scsc(
                    **report_kwargs,
                    # The below is an additional parameter compared to the function calls earlier in the 
                    #   if-else tree
                    ps_school_subdistrict_name=ps_school_subdistrict_name, 
                )
            else:
                raise Exception("CALPADS EOY report name not supported")
        elif(submission_window == 'All Year'):
            if(calpads_report_abbreviation == 'SENR'):
                return self._download_all_year_report_for_ssid_enrollment_records_senr(**report_kwargs)
            elif(calpads_report_abbreviation == 'SELA'):
                return self._download_all_year_report_for_student_english_language_acquisition_records_sela(
                    **report_kwargs
                )
            elif(calpads_report_abbreviation == 'SINF'):
                return self._download_all_year_report_for_student_information_records_sinf(**report_kwargs)
            else:
                raise Exception("CALPADS All Year report name not supported")
        elif submission_window == 'Fall 1':
            if calpads_report_abbreviation == 'SPRG':
                return self._download_eoy_report_for_student_program_records_sprg(**report_kwargs)
            else:
                raise Exception("CALPADS Fall 1 report name not supported")
        else:
            raise Exception("Submission window name not supported")
        

    # All Year Reports #################

    def _download_all_year_report_for_ssid_enrollment_records_senr(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        validation_only_run: bool=False):
        """
        Switches to the SSID Enrollment Records (SENR) report in PowerSchool and downloads it.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)
        
        # Enter specific parameters for this report
        helper_type_in_element_by_name(self.driver, 'StartDate', 
            report_parameters['report_start_date'])
        helper_type_in_element_by_name(self.driver, 'EndDate', 
            report_parameters['report_end_date'])
        helper_select_visible_text_in_element_by_name(self.driver, 'submissionMode', 
            'Non-submission mode (all records)') # Only 'Non-submission mode' is supported by this tool
        time.sleep(1) # Give page time to react
        helper_select_visible_text_in_element_by_name(self.driver, 'ssidOption', 
            report_parameters['student_selection_filter'])
        helper_select_visible_text_in_element_by_name(self.driver, 'bypass_validation', 
            'No' if validation_only_run else 'Yes')

        # Submit report
        helper_click_element_by_id(self.driver, 'btnSubmit')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_system(destination_directory_path, 
            file_postfix)
    
    def _download_all_year_report_for_student_english_language_acquisition_records_sela(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        validation_only_run: bool=False):
        """
        Switches to the Student English Language Acquisition (SELA) report in 
        PowerSchool and downloads it.

        IMPORTANT NOTE #1: You need to run the remove_sela_records_beginning_before_report_start_date()
        function on the final text file to filter out any records whose start
        dates are before your intended report start date. PowerSchool's
        filtering does not work properly for this.

        IMPORTANT NOTE #2: There is an edge case that this code and PowerSchool 
        are not equipped to handle. If you have a student who received an English
        Language Acquisition status at another district before your report_start_date
        and you store that status in PowerSchool, there is no easy way to decline to
        report that record to CALPADS. But if you do report that record, CALPADS will
        reject it and your whole upload file. 
        
        For instance, if a student enrolled at another district and received a TBD 
        status in September and then they joined your district in October, if you 
        enter that TBD status into PowerSchool, the SELA file will error out in CALPADS.
        
        The proper fix is to only include records that start when a student is enrolled
        with you, but that would be complicated to do through the PowerSchool UI. Summit
        will likely solve this issue by manually setting any impacted English Language
        Acquisition statuses to have a start date in PowerSchool of before the school year 
        begins. That way, they'll be excluded from this tool. If this is a problem for you, 
        you may want to do something similar or find a way to pull enrollment data into 
        your code to do additional filtering on the upload file.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)

        # SELA requires some very specific setup to export in a way that CALPADS will accept. Specifically,
        #   you can only include students that are currently rostered to you in CALPADS, so this function
        #   will only pull currently enrolled students or students who were enrolled on the report end date
        #   if that date is in the past. Usually, the report end date will be the last day of school, so this
        #   will enable submissions after the school year has ended.

        report_end_date_datetime_object = datetime.strptime(report_parameters['report_end_date'], '%m/%d/%Y').date()
        today_datetime_object = date.today()

        if today_datetime_object > report_end_date_datetime_object:
            date_for_report = report_parameters['report_end_date']
        else:
            date_for_report = today_datetime_object.strftime('%m/%d/%Y')
        
        # Enter specific parameters for this report
        helper_type_in_element_by_name(self.driver, 'startDate', date_for_report)
        helper_type_in_element_by_name(self.driver, 'endDate', date_for_report)

        helper_type_in_element_by_name(self.driver, 'status_start_date', '') # Make sure this field is cleared
        helper_type_in_element_by_name(self.driver, 'status_end_date', '') # Make sure this field is cleared

        helper_select_visible_text_in_element_by_name(self.driver, 'deltaOff', # Unclear why this is the element name
            'Non-submission mode (all records)') # Only 'Non-submission mode' is supported by this tool
        time.sleep(1) # Give page time to react

        helper_select_visible_text_in_element_by_name(self.driver, 'bypass_validation', 
            'No' if validation_only_run else 'Yes')
        
        # Below defaults to "No Group Selected" because school should already be chosen
        helper_select_visible_text_in_element_by_name(self.driver, 'schoolGroup', '[No Group Selected]') 

        # Submit report
        helper_click_element_by_id(self.driver, 'btnSubmit')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_system(destination_directory_path, 
            file_postfix)

    def _download_all_year_report_for_student_information_records_sinf(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        validation_only_run: bool=False):
        """
        Switches to the Student Information Records (SINF) report in PowerSchool and downloads it.
        This function assumes that the export will be run repeatedly over the course of the year
        and therefore doesn't use the "Check for Fall Submission" functionality. This is because
        there are occasionally needs for updating SINF outside of Fall 1, such as for Pandemic
        EBT benefits.

        Uploading an updated SINF file does not seem to close out existing Demographics and
        Address  records, except when the "Effective Start Date" is greater than the most 
        recent "Effective Start Date" in CALPADS. Thus, the "Make Effective Start Date Match 
        Enrollment Start Date" checkbox (described just below) should mean existing records
        just get updated, rather than new records being created.

        Important notes about how the SINF report parameters in PowerSchool work:
        - The "Check for Fall Submission" checkbox means it will only submit records for students
        enrolled on the Census Date that you enter. This function intentionally does not use
        this setting, so it will guarantee that box is not checked.
        - The "Make Effective Start Date Match Enrollment Start Date" will give all records the 
        student's enrollment date for the year as the start date.
        - The "Start Date" will be the date at which the report looks for enrollments, and it will
        report data for any student enrolled any time up to the "End Date". The "Effective Start
        Date" in the final file will be the student's enrollment date for the year, so long as the
        "Make Effective Start Date Match Enrollment Start Date" box is checked.
        - The "End Date" cannot be greater than the current date for this report, so this function
        will enter the report_end_date or the current date, whichever is earlier.
        - The "Include Students' Preferred Names (If Different From Legal)" will include data in
        those fields if "Yes" is selected. For student privacy reasons, defaulting to "No" here is 
        preferred, especially for students whose lived name may differ from their legal name.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)
        
        # Enter specific parameters for this report
        helper_ensure_checkbox_is_unchecked_by_name(self.driver, 'SubmissionType')
        time.sleep(1) # Give page time to react

        helper_ensure_checkbox_is_checked_by_name(self.driver, 'effectiveStartDate')

        helper_type_in_element_by_name(self.driver, 'StartDate', 
            report_parameters['report_start_date'])
        
        # If the provided report_end_date is in the future, use today's date instead
        end_date_string = report_parameters['report_end_date']
        report_end_date_object = datetime.strptime(end_date_string, '%m/%d/%Y').date()
        current_date = date.today()
        if report_end_date_object > current_date:
            end_date_string = current_date.strftime("%m/%d/%Y")
        helper_type_in_element_by_name(self.driver, 'EndDate', end_date_string)

        helper_select_visible_text_in_element_by_name(self.driver, 'deltaOff',
            'Non-submission mode (all records)') # Only 'Non-submission mode' is supported by this tool
        time.sleep(1) # Give page time to react

        helper_select_visible_text_in_element_by_name(self.driver, 'bypass_validation', 
            'No' if validation_only_run else 'Yes')
        
        # See note in function definition
        helper_select_visible_text_in_element_by_name(self.driver, 'includePreferredName', 'No')

        # Submit report
        helper_click_element_by_id(self.driver, 'btnSubmit')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_system(destination_directory_path, 
            file_postfix)
    

    # EOY Reports ######################

    def _download_eoy_report_for_student_incident_records_sinc(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        validation_only_run: bool=False):
        """
        Switches to the Student Incident Records (SINC) report in PowerSchool and downloads it.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)
        
        # Enter specific parameters for this report
        helper_type_in_element_by_id(self.driver, 'reportStartDate', 
            report_parameters['report_start_date'])
        helper_type_in_element_by_id(self.driver, 'reportEndDate', 
            report_parameters['report_end_date'])
        helper_select_visible_text_in_element_by_id(self.driver, 'reportMode', 
            'Submission mode') # Only 'Submission mode' is supported by this tool
        time.sleep(1) # Give page time to react
        helper_select_visible_text_in_element_by_id(self.driver, 'bypassValidation', 
            'No' if validation_only_run else 'Yes')

        # Submit report
        helper_click_element_by_id(self.driver, 'submitReportSDKRuntimeParams')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_reportworks(destination_directory_path, 
            file_postfix)

    def _download_eoy_report_for_student_incident_results_records_sirs_or_student_offense_records_soff(
        self, file_postfix: str, destination_directory_path: str, ps_report_link_text: str, 
        report_parameters: dict, validation_only_run: bool=False):
        """
        Switches to the Student Incident Results Records (SIRS) or Student Offense Records (SOFF) 
        report in PowerSchool and downloads it.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)
        
        # Enter specific parameters for this report
        helper_type_in_element_by_id(self.driver, 'reportStartDate', 
            report_parameters['report_start_date'])
        helper_type_in_element_by_id(self.driver, 'reportEndDate', 
            report_parameters['report_end_date'])
        helper_select_visible_text_in_element_by_id(self.driver, 'bypassValidation', 
            'No' if validation_only_run else 'Yes')
        
        # Submit report
        helper_click_element_by_id(self.driver, 'submitReportSDKRuntimeParams')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_reportworks(destination_directory_path, 
            file_postfix)

    def _download_eoy_report_for_student_absence_summary_stas(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        validation_only_run: bool=False):
        """
        Switches to the Student Absence Summary (STAS) report in PowerSchool and downloads it.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)
        
        # Enter specific parameters for this report
        helper_type_in_element_by_name(self.driver, 'StartDate', 
            report_parameters['report_start_date'])
        helper_type_in_element_by_name(self.driver, 'EndDate', 
            report_parameters['report_end_date'])
        # Below 'adaFlag' defaults to 'Yes'
        helper_select_visible_text_in_element_by_name(self.driver, 'adaFlag', 'Yes') 
        helper_select_visible_text_in_element_by_name(self.driver, 'bypass_validation', 
            'No' if validation_only_run else 'Yes')
        # Below defaults to "No Group Selected" because school should already be chosen
        helper_select_visible_text_in_element_by_name(self.driver, 'schoolGroup', 
            '[No Group Selected]') 
        
        # Submit report
        helper_click_element_by_id(self.driver, 'btnSubmit')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_system(destination_directory_path, 
            file_postfix)

    def _download_eoy_report_for_student_program_records_sprg(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        validation_only_run: bool=False):
        """
        Switches to the Student Program Records (SPRG) report in PowerSchool and downloads it.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)
        
        # Enter specific parameters for this report
        helper_type_in_element_by_name(self.driver, 'startDate', 
            report_parameters['report_start_date'])
        helper_type_in_element_by_name(self.driver, 'endDate', 
            report_parameters['report_end_date'])
        helper_select_visible_text_in_element_by_name(self.driver, 'selectProgs', 
            report_parameters['submission_type'])

        # I believe 'Non-submission mode (all records)' is the one we want to use for repeated 
        #   submissions, but there's also 'Replacement Submission Mode' which has a different flow 
        #   after clicking Submit.
        helper_select_visible_text_in_element_by_name(self.driver, 'submissionMode', 
            'Non-submission mode (all records)') 

        helper_select_visible_text_in_element_by_name(self.driver, 'bypass_validation', 
            'No' if validation_only_run else 'Yes')
        # Below defaults to "No Group Selected" because school should already be chosen
        helper_select_visible_text_in_element_by_name(self.driver, 'schoolGroup', 
            '[No Group Selected]')

        # Submit report
        helper_click_element_by_id(self.driver, 'btnSubmit')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_system(destination_directory_path, 
            file_postfix)

    def _download_eoy_report_for_course_section_records_crsc(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        validation_only_run: bool=False):
        """
        Switches to the Course Section Completion (CRSC) report in PowerSchool and downloads it.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)
        
        # Enter specific parameters for this report
        helper_select_visible_text_in_element_by_id(self.driver, 'submission', 
            report_parameters['submission_type'])

        # Date fields need time to appear
        time.sleep(1) 
        helper_type_in_element_by_id(self.driver, 'startDate', 
            report_parameters['report_start_date'])
        helper_type_in_element_by_id(self.driver, 'endDate', 
            report_parameters['report_end_date'])
        helper_select_visible_text_in_element_by_id(self.driver, 'bypassValidation', 
            'No' if validation_only_run else 'Yes')
        # The below indicates to not "Include Records For Course Code 1000"
        helper_select_visible_text_in_element_by_id(self.driver, 'selectCourseCode', 'No') 

        # Submit report
        helper_click_element_by_id(self.driver, 'submitReportSDKRuntimeParams')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_reportworks(destination_directory_path, 
            file_postfix)

    def _download_eoy_report_for_student_course_section_records_scsc(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        ps_school_subdistrict_name:str, validation_only_run: bool=False):
        """
        Switches to the Student Course Completion (SCSC) report in PowerSchool and downloads it.
        """
        self.navigate_to_specific_state_report(ps_report_link_text)
        
        # Enter specific parameters for this report
        helper_select_visible_text_in_element_by_name(self.driver, 'submission', 
            report_parameters['submission_type'])
        helper_type_in_element_by_name(self.driver, 'storeCodeList', 
            report_parameters['eoy_store_code_list'])
        # Below defaults to 'No' for 'Extract Credits for Grades 7 and 8' 
        # TODO: Research if this is correct
        helper_select_visible_text_in_element_by_name(self.driver, 'msExtract', 'No') 


        helper_type_in_element_by_name(self.driver, 'startDate', 
            report_parameters['report_start_date'])
        helper_type_in_element_by_name(self.driver, 'endDate', 
            report_parameters['report_end_date'])

        helper_select_visible_text_in_element_by_name(self.driver, 'bypass_validation', 
            'No' if validation_only_run else 'Yes')
        helper_select_visible_text_in_element_by_name(self.driver, 'selectCourseCode', 
            'No') # Do not "Include Records For Course Code 1000"

        helper_select_visible_text_in_element_by_name(self.driver, 'subDistrict', 
            ps_school_subdistrict_name)

        # Submit report
        helper_click_element_by_id(self.driver, 'btnSubmit')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_system(destination_directory_path, 
            file_postfix)
    
# Helper Functions #################

#    Note: These functions are intentionally not in the class, because one may want to access
#    them separately from downloading files from PowerSchool.

def swap_value_in_column_of_calpads_file(file_path: str, column_names_of_file: list, 
    column_name_for_swap: str, existing_value: str, new_value: str, encoding: str='utf-8'):
    """
    Opens a CALPADS upload file, looks for the existing_value in the provided column and replaces it
    with the new_value. Writes the new file to the same folder but with "_modified" added to the
    filename. Returns the new file path.

    Parameters:
    file_path: The path of the file that needs to be modified.
    column_names_of_file: A list storing the CALPADS column names for the relevant file. Needs to be 
        in order and exactly matching the number of columns in the file. File specifications available at: https://www.cde.ca.gov/ds/sp/cl/systemdocs.asp
    column_name_for_swap: The name of the column being modified.
    existing_value: The existing value in that column that needs to be swapped out.
    new_value: The value that will replace the existing_value.

    Returns:
    str: The path of the modified file
    """

    df_to_edit = pd.read_csv(file_path, sep='^', header=None, names=column_names_of_file, dtype=str, encoding=encoding)

    df_to_edit.loc[df_to_edit[column_name_for_swap] == existing_value, column_name_for_swap] = new_value

    df_to_edit.fillna('', inplace=True)

    updated_file_path = file_path.replace('.txt', '_modified.txt')
    df_to_edit.to_csv(updated_file_path, sep='^', header=False, index=False, na_rep='')

    return updated_file_path

def remove_sela_records_beginning_before_report_start_date(sela_file_path: str, 
    report_start_date: str):
    """
    Take the SELA file at the provided path, filter so it contains only the
    records with an ELA status start date greater than or equal to the report
    start date, and return the path to the modified file.
    """

    # Load existing upload file
    df_to_edit = pd.read_csv(sela_file_path, sep='^', header=None, names=SELA_COLUMN_NAMES, dtype=str, encoding='cp1252')

    # Convert report_start_date to a string in the format of 'YYYYMMDD' to match the upload file column
    report_start_date_object = datetime.strptime(report_start_date, '%m/%d/%Y')
    reformatted_report_start_date_string = report_start_date_object.strftime('%Y%m%d')

    # Keep only records greater than or equal to the report_start_date
    filtered_df = df_to_edit[df_to_edit['English Language Acquisition Status Start Date'] >= reformatted_report_start_date_string]

    # Output new upload file
    updated_file_path = sela_file_path.replace('.txt', '_modified.txt')
    filtered_df.to_csv(updated_file_path, sep='^', header=False, index=False, na_rep='')

    return updated_file_path