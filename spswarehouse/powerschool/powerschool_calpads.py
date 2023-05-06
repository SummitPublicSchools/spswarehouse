import time
from datetime import datetime, date
import pandas as pd

from spswarehouse.powerschool.powerschool import PowerSchool

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
    
    def __init__(self, username: str=None, password: str=None, host: str=None, headless: bool=True, 
        download_location: str='.'):
        
        super().__init__(username, password, host, headless, download_location)

    def download_calpads_report_for_school(self, school_full_name: str, submission_window: str, 
        calpads_report_abbreviation: str, ps_school_subdistrict_name: str, file_postfix: str, 
        destination_directory_path: str, report_parameters: dict, validation_only_run: bool=False):
        """
        Switches to the desired school in PowerSchool and calls the function to generate the desired
        report for the specified submission window. Note: This function currently only supports EOY 
        reports and some All Year reports. Fall 1 and Fall 2 reports should not use this function until 
        it is expanded.
        """

        # The SCSC report needs to be run from the District Office level in order to properly generate 
        #   LEA IDs without dropping leading zeros
        if calpads_report_abbreviation == "SCSC":
            self.switch_to_school('District Office')
        else:
            self.switch_to_school(school_full_name)

        if(submission_window == 'EOY'):
            if(calpads_report_abbreviation == "SINC"):
                return self._download_eoy_report_for_student_incident_records_sinc(
                    ps_report_link_text=PS_REPORT_LINK_TEXT[calpads_report_abbreviation], 
                    file_postfix=file_postfix, 
                    destination_directory_path=destination_directory_path, 
                    report_parameters=report_parameters,
                    validation_only_run=validation_only_run
                    )
            elif(calpads_report_abbreviation in ('SIRS', 'SOFF')):
                return self._download_eoy_report_for_student_incident_results_records_sirs_or_student_offense_records_soff(
                    ps_report_link_text=PS_REPORT_LINK_TEXT[calpads_report_abbreviation], 
                    file_postfix=file_postfix, 
                    destination_directory_path=destination_directory_path, 
                    report_parameters=report_parameters,
                    validation_only_run=validation_only_run
                    )
            elif(calpads_report_abbreviation == 'STAS'):
                return self._download_eoy_report_for_student_absence_summary_stas(
                    ps_report_link_text=PS_REPORT_LINK_TEXT[calpads_report_abbreviation], 
                    file_postfix=file_postfix, 
                    destination_directory_path=destination_directory_path, 
                    report_parameters=report_parameters,
                    validation_only_run=validation_only_run
                    )
            elif(calpads_report_abbreviation == 'SPRG'):
                return self._download_eoy_report_for_student_program_records_sprg(
                    ps_report_link_text=PS_REPORT_LINK_TEXT[calpads_report_abbreviation], 
                    file_postfix=file_postfix, 
                    destination_directory_path=destination_directory_path, 
                    report_parameters=report_parameters,
                    validation_only_run=validation_only_run
                    )
            elif(calpads_report_abbreviation == 'CRSC'):
                return self._download_eoy_report_for_course_section_records_crsc(
                    ps_report_link_text=PS_REPORT_LINK_TEXT[calpads_report_abbreviation], 
                    file_postfix=file_postfix, 
                    destination_directory_path=destination_directory_path, 
                    report_parameters=report_parameters,
                    validation_only_run=validation_only_run
                    )
            elif(calpads_report_abbreviation == 'SCSC'):
                return self._download_eoy_report_for_student_course_section_records_scsc(
                    ps_report_link_text=PS_REPORT_LINK_TEXT[calpads_report_abbreviation],
                    file_postfix=file_postfix, 
                    destination_directory_path=destination_directory_path, 
                    report_parameters=report_parameters,
                    # The below is an additional parameter compared to the function calls earlier in the 
                    #   if-else tree
                    ps_school_subdistrict_name=ps_school_subdistrict_name, 
                    validation_only_run=validation_only_run,
                    )
            else:
                raise Exception("CALPADS EOY report name not supported")
        elif(submission_window == 'All Year'):
            if(calpads_report_abbreviation == 'SENR'):
                return self._download_all_year_report_for_ssid_enrollment_records_senr(
                    ps_report_link_text=PS_REPORT_LINK_TEXT[calpads_report_abbreviation],
                    file_postfix=file_postfix, 
                    destination_directory_path=destination_directory_path, 
                    report_parameters=report_parameters,
                    validation_only_run=validation_only_run,
                    )
            elif(calpads_report_abbreviation == 'SELA'):
                return self._download_all_year_report_for_student_english_language_acquisition_records_sela(
                    ps_report_link_text=PS_REPORT_LINK_TEXT[calpads_report_abbreviation],
                    file_postfix=file_postfix, 
                    destination_directory_path=destination_directory_path, 
                    report_parameters=report_parameters,
                    validation_only_run=validation_only_run,
                    )
            else:
                raise Exception("CALPADS All Year report name not supported")
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
        self.helper_type_in_element_by_name('StartDate', 
            report_parameters['report_start_date'])
        self.helper_type_in_element_by_name('EndDate', 
            report_parameters['report_end_date'])
        self.helper_select_visible_text_in_element_by_name('submissionMode', 
            'Non-submission mode (all records)') # Only 'Non-submission mode' is supported by this tool
        time.sleep(1) # Give page time to react
        self.helper_select_visible_text_in_element_by_name('ssidOption', 
            report_parameters['student_selection_filter'])
        self.helper_select_visible_text_in_element_by_name('bypass_validation', 
            'No' if validation_only_run else 'Yes')

        # Submit report
        self.helper_click_element_by_id('btnSubmit')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_system(destination_directory_path, 
            file_postfix)
    
    def _download_all_year_report_for_student_english_language_acquisition_records_sela(self, file_postfix: str, 
        destination_directory_path: str, ps_report_link_text: str, report_parameters: dict, 
        validation_only_run: bool=False):
        """
        Switches to the Student English Language Acquisition (SELA) report in 
        PowerSchool and downloads it.

        IMPORTANT NOTE: You need to run the remove_sela_records_beginning_before_report_start_date()
        function on the final text file to filter out any records whose start
        dates are before your intended report start date. PowerSchool's
        filtering does not work properly for this.
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
        self.helper_type_in_element_by_name('startDate', date_for_report)
        self.helper_type_in_element_by_name('endDate', date_for_report)

        self.helper_type_in_element_by_name('status_start_date', '') # Make sure this field is cleared
        self.helper_type_in_element_by_name('status_end_date', '') # Make sure this field is cleared

        self.helper_select_visible_text_in_element_by_name('deltaOff', # Unclear why this is the element name
            'Non-submission mode (all records)') # Only 'Non-submission mode' is supported by this tool
        time.sleep(1) # Give page time to react

        self.helper_select_visible_text_in_element_by_name('bypass_validation', 
            'No' if validation_only_run else 'Yes')
        
        # Below defaults to "No Group Selected" because school should already be chosen
        self.helper_select_visible_text_in_element_by_name('schoolGroup', '[No Group Selected]') 

        # Submit report
        self.helper_click_element_by_id('btnSubmit')

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
        self.helper_type_in_element_by_id('reportStartDate', 
            report_parameters['report_start_date'])
        self.helper_type_in_element_by_id('reportEndDate', 
            report_parameters['report_end_date'])
        self.helper_select_visible_text_in_element_by_id('reportMode', 
            'Submission mode') # Only 'Submission mode' is supported by this tool
        time.sleep(1) # Give page time to react
        self.helper_select_visible_text_in_element_by_id('bypassValidation', 
            'No' if validation_only_run else 'Yes')

        # Submit report
        self.helper_click_element_by_id('submitReportSDKRuntimeParams')

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
        self.helper_type_in_element_by_id('reportStartDate', 
            report_parameters['report_start_date'])
        self.helper_type_in_element_by_id('reportEndDate', 
            report_parameters['report_end_date'])
        self.helper_select_visible_text_in_element_by_id('bypassValidation', 
            'No' if validation_only_run else 'Yes')
        
        # Submit report
        self.helper_click_element_by_id('submitReportSDKRuntimeParams')

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
        self.helper_type_in_element_by_name('StartDate', 
            report_parameters['report_start_date'])
        self.helper_type_in_element_by_name('EndDate', 
            report_parameters['report_end_date'])
        # Below 'adaFlag' defaults to 'Yes'
        self.helper_select_visible_text_in_element_by_name('adaFlag', 'Yes') 
        self.helper_select_visible_text_in_element_by_name('bypass_validation', 
            'No' if validation_only_run else 'Yes')
        # Below defaults to "No Group Selected" because school should already be chosen
        self.helper_select_visible_text_in_element_by_name('schoolGroup', 
            '[No Group Selected]') 
        
        # Submit report
        self.helper_click_element_by_id('btnSubmit')

        # Give the STAS report time to get into the report queue, since it can be slow
        time.sleep(5)

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
        self.helper_type_in_element_by_name('startDate', 
            report_parameters['report_start_date'])
        self.helper_type_in_element_by_name('endDate', 
            report_parameters['report_end_date'])
        self.helper_select_visible_text_in_element_by_name('selectProgs', 
            report_parameters['submission_type'])

        # I believe 'Non-submission mode (all records)' is the one we want to use for repeated 
        #   submissions, but there's also 'Replacement Submission Mode' which has a different flow 
        #   after clicking Submit.
        self.helper_select_visible_text_in_element_by_name('submissionMode', 
            'Non-submission mode (all records)') 

        self.helper_select_visible_text_in_element_by_name('bypass_validation', 
            'No' if validation_only_run else 'Yes')
        # Below defaults to "No Group Selected" because school should already be chosen
        self.helper_select_visible_text_in_element_by_name('schoolGroup', 
            '[No Group Selected]')

        # Submit report
        self.helper_click_element_by_id('btnSubmit')

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
        self.helper_select_visible_text_in_element_by_id('submission', 
            report_parameters['submission_type'])

        # Date fields need time to appear
        time.sleep(1) 
        self.helper_type_in_element_by_id('startDate', 
            report_parameters['report_start_date'])
        self.helper_type_in_element_by_id('endDate', 
            report_parameters['report_end_date'])
        self.helper_select_visible_text_in_element_by_id('bypassValidation', 
            'No' if validation_only_run else 'Yes')
        # The below indicates to not "Include Records For Course Code 1000"
        self.helper_select_visible_text_in_element_by_id('selectCourseCode', 'No') 

        # Submit report
        self.helper_click_element_by_id('submitReportSDKRuntimeParams')

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
        self.helper_select_visible_text_in_element_by_name('submission', 
            report_parameters['submission_type'])
        self.helper_type_in_element_by_name('storeCodeList', 
            report_parameters['eoy_store_code_list'])
        # Below defaults to 'No' for 'Extract Credits for Grades 7 and 8' 
        # TODO: Research if this is correct
        self.helper_select_visible_text_in_element_by_name('msExtract', 'No') 


        self.helper_type_in_element_by_name('startDate', 
            report_parameters['report_start_date'])
        self.helper_type_in_element_by_name('endDate', 
            report_parameters['report_end_date'])

        self.helper_select_visible_text_in_element_by_name('bypass_validation', 
            'No' if validation_only_run else 'Yes')
        self.helper_select_visible_text_in_element_by_name('selectCourseCode', 
            'No') # Do not "Include Records For Course Code 1000"

        self.helper_select_visible_text_in_element_by_name('subDistrict', 
            ps_school_subdistrict_name)

        # Submit report
        self.helper_click_element_by_id('btnSubmit')

        # Download report zipfile
        return self.download_latest_report_from_report_queue_system(destination_directory_path, 
            file_postfix)
    
    # Helper Functions #################

    def remove_sela_records_beginning_before_report_start_date(self, sela_file_path: str, 
        report_start_date: str):
        """
        Take the SELA file at the provided path, filter so it contains only the
        records with an ELA status start date greater than or equal to the report
        start date, and return the path to the modified file.
        """

        # Load existing upload file
        df_to_edit = pd.read_csv(sela_file_path, sep='^', header=None, names=SELA_COLUMN_NAMES, dtype=str, encoding='ansi')

        # Convert report_start_date to a string in the format of 'YYYYMMDD' to match the upload file column
        report_start_date_object = datetime.strptime(report_start_date, '%m/%d/%Y')
        reformatted_report_start_date_string = report_start_date_object.strftime('%Y%m%d')

        # Keep only records greater than or equal to the report_start_date
        filtered_df = df_to_edit[df_to_edit['English Language Acquisition Status Start Date'] >= reformatted_report_start_date_string]

        # Output new upload file
        updated_file_path = sela_file_path.replace('.txt', '_modified.txt')
        filtered_df.to_csv(updated_file_path, sep='^', header=False, index=False, na_rep='')

        return updated_file_path