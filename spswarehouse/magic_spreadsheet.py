import pandas as pd
import logging

from .warehouse import create_warehouse
from .googlesheets import create_sheets
from .googledrive import create_drive

from gspread_formatting import (
    set_data_validation_for_cell_range,
    BooleanCondition,
    BooleanRule,
    CellFormat,
    ConditionalFormatRule,
    get_conditional_format_rules,
    GridRange,
    textFormat,
    format_cell_range,
    color,
)

"""
This module defines a number of functions to create and manage 
"Magic Spreadsheets" - Google Sheets that automatically update based on
the results of a SQL query run against the warehouse.

Magic Spreadsheets are more sophisticated than a simple export in that they 
preserve existing columns, so they support users of the sheet adding notes
and other columns that will maintain their associations even as students
are added/removed from the sheet.

We use this in production in the SY24 "Main Enrollment Forms Tracker" (MEFT)
and the SY24 Child Find tool.

Typical sequence of calls:
    * Create or fetch the spreadsheets: `spreadsheet_object, spreadsheet_already_exists = create_or_retrieve_magic_spreadsheet_and_add_missing_worksheets(...)`
    * Add the static worksheets: `check_for_static_worksheets_and_add_them_with_protection(...)`
    * Update the spreadsheet with query results: `update_magic_spreadsheet_with_new_query_results(...)`
    * If desired, update specific cells (like the "Last Updated" field): `update_specific_cell(...)`
"""

def _run_warehouse_query_for_worksheet(query_list: list):
    """
    Take a list of queries stored as dictionaries. Run each query at the provided
    path with the provided parameters. Take the output of all queries in the list,
    combine them, remove NAs, and return the resulting combined dataframe.
    """
    df_combined_query_output = None

    for query_dict in query_list:
        query_path = query_dict['path']
        query_parameters = query_dict['parameters']

        with open(query_path, "r") as f:
            if query_parameters == {}:
                warehouse_query = f.read()
            else:
                warehouse_query = f.read().format(**query_parameters)

        Warehouse = create_warehouse()

        # Raise logging level to limit warehouse output to logs
        logger = logging.getLogger()
        logger.setLevel(logging.WARNING)

        df_query_output = Warehouse.read_sql(warehouse_query)

         # Reset logging level
        logger.setLevel(logging.INFO)

        if df_combined_query_output is None:
            df_combined_query_output = df_query_output
        else:
            df_combined_query_output = pd.concat([df_combined_query_output, df_query_output], axis=0)
        
    df_combined_query_output.fillna('', inplace=True)

    return df_combined_query_output

def _add_formulas_to_worksheet(worksheet_object, formulas_list):
    """
    Given a list of formulas in the format below, add the formula to the specified row of the
    column, then copy it down the entire column.
    """
    
    for formula in formulas_list:
        formula_column = formula['column']
        formula_row_start = formula['row_of_first_formula_cell']
        formula_text = formula['formula_text']
        
        # First, add the formula to the specified row of the given column
        source_cell = f'{formula_column}{formula_row_start}'
        worksheet_object.update(source_cell, formula_text, value_input_option='USER_ENTERED')
        
        # Then, copy that formula down the whole column
        destination_range = f'{formula_column}{formula_row_start}:{formula_column}'
        
        worksheet_object.copy_range(source_cell, destination_range, paste_type='PASTE_FORMULA')

def _add_data_validations_to_worksheet(worksheet_object, data_validations_list):
    """
    Given a list of data validations in the format below, clears any existing rules in
    the provided range and adds each rule from the list to the worksheet object. This
    function assumes one validation rule for any given range; otherwise, later rules 
    in the list would overwrite earlier ones.
    
    List format:
        [
            {
                'range': 'P4:P',
                'validation_rule' : DataValidationRule(
                    BooleanCondition('ONE_OF_LIST', ['True', 'False']),
                    showCustomUi=True
                )
            },
        ]
    """
    for data_validation in data_validations_list:
        validation_range = data_validation['range']
        validation_rule = data_validation['validation_rule']
        
        # Clear any existing validation rules in the range
        set_data_validation_for_cell_range(worksheet_object, validation_range, None)
    
        # Add validation rule from list to the range
        set_data_validation_for_cell_range(worksheet_object, validation_range, validation_rule)

def _hide_header_rows_and_left_columns_in_worksheet(worksheet_object, num_header_rows_to_hide, num_left_columns_to_hide):

    worksheet_object.hide_rows(0, num_header_rows_to_hide)
    worksheet_object.hide_columns(0, num_left_columns_to_hide)

def _set_basic_filter_on_worksheet(worksheet_object, row_number_for_filter, final_row_number):
    num_columns = worksheet_object.col_count
    final_col_letter = col_to_letter(num_columns)

    worksheet_object.set_basic_filter(f'A{row_number_for_filter}:{final_col_letter}{final_row_number}')

def _refresh_conditional_formatting_on_worksheet(worksheet_object, num_header_rows: int,
    conditional_formatting_rules_dict: dict, colors_dict: dict):

    # logging.info("Store the current conditional formatting rules.")
    rules = get_conditional_format_rules(worksheet_object)
    
    # logging.info("Delete all the existing rules.")
    rules.clear()

    # logging.info("Iterating through conditional formatting rules.")
    for color in conditional_formatting_rules_dict.keys():
        for new_rule in conditional_formatting_rules_dict[color]:
            new_rule_starts_with_text = new_rule[0]
            new_rule_start_column = new_rule[1]
            new_rule_end_column = new_rule[2]

            color_object = colors_dict[color]

            new_rule_range = f'{new_rule_start_column}{num_header_rows+1}:{new_rule_end_column}'

            new_condition = ConditionalFormatRule(
                ranges=[GridRange.from_a1_range(new_rule_range, worksheet_object)],
                booleanRule=BooleanRule(
                    condition=BooleanCondition("TEXT_STARTS_WITH", [new_rule_starts_with_text]),
                    format=CellFormat(
                        textFormat=textFormat(
                            foregroundColor=color_object
                        )
                    )
                )
            )

            # logging.info(f'Appending rule to rules list: text starting with "{new_rule_starts_with_text}" in column {new_rule_start_column} through column {new_rule_end_column} is {color}.')
            rules.append(new_condition)

    # logging.info("Posting the new rules back to the worksheet.")
    rules.save()

    # logging.info("Conditional formatting updated.")

def create_or_retrieve_magic_spreadsheet_and_add_missing_worksheets(drive_folder_id: str,
    spreadsheet_name: str, template_spreadsheet_id: str, worksheet_name_list):

    gs = create_sheets()

    spreadsheet_already_exists, spreadsheet_object = _check_if_spreadsheet_exists_and_retrieve_it(
        drive_folder_id=drive_folder_id,
        spreadsheet_name=spreadsheet_name,
        gs = gs,
    )

    if spreadsheet_already_exists == False:
        spreadsheet_object = _create_spreadsheet_from_template(
            output_spreadsheet_name = spreadsheet_name, 
            output_folder_id = drive_folder_id, 
            template_spreadsheet_id = template_spreadsheet_id, 
            worksheet_name_list = worksheet_name_list,
            gs = gs,
            )
    else:
        template_spreadsheet_object = gs.open_by_key(template_spreadsheet_id)

        _check_for_missing_worksheets_and_create_them(target_spreadsheet_object = spreadsheet_object, 
            template_spreadsheet_object = template_spreadsheet_object, 
            worksheet_name_list = worksheet_name_list)
        
    return spreadsheet_object, spreadsheet_already_exists

def _check_if_spreadsheet_exists_and_retrieve_it(drive_folder_id: str, spreadsheet_name: str, gs):
    
    google_drive = create_drive()

    folder_files = google_drive.ListFile({'q': f"'{drive_folder_id}' in parents"}).GetList()

    spreadsheet_already_exists = False

    # Get spreadsheet if it exists
    for file in folder_files:
        if file['title'] == spreadsheet_name:
            spreadsheet_already_exists = True
            current_spreadsheet = gs.open_by_key(file['id'])

    if spreadsheet_already_exists == True:
        return spreadsheet_already_exists, current_spreadsheet
    else:
        return spreadsheet_already_exists, None

def _create_worksheet_from_template_if_does_not_exist(target_spreadsheet_object, template_spreadsheet_object, worksheet_name):

    new_worksheet_created = False

    # Get the list of worksheet titles in the target spreadsheet
    worksheet_list = target_spreadsheet_object.worksheets()

    # Check if a specific worksheet exists
    worksheet_exists = any(worksheet.title == worksheet_name for worksheet in worksheet_list)

    if worksheet_exists == False:
        # Get worksheet in template
        template_worksheet = template_spreadsheet_object.worksheet(worksheet_name)
        
        # Copy worksheet to the target spreadsheet
        target_worksheet_info_dict = template_worksheet.copy_to(target_spreadsheet_object.id)
        target_worksheet_object = target_spreadsheet_object.worksheet(target_worksheet_info_dict['title'])
        
        # Rename worksheet at destination to remove 'Copy of'
        target_worksheet_object.update_title(worksheet_name)

        new_worksheet_created = True
       
    return new_worksheet_created

def _check_for_missing_worksheets_and_create_them(target_spreadsheet_object, template_spreadsheet_object, worksheet_name_list):
    for worksheet_name in worksheet_name_list:
        _create_worksheet_from_template_if_does_not_exist(target_spreadsheet_object = target_spreadsheet_object, 
            template_spreadsheet_object = template_spreadsheet_object, worksheet_name = worksheet_name)

def _create_spreadsheet_from_template(output_spreadsheet_name: str, output_folder_id: str, 
    template_spreadsheet_id: str, worksheet_name_list: list, gs):
    
    # Create spreadsheet
    spreadsheet = gs.create(output_spreadsheet_name, folder_id=output_folder_id)
    
    # Get the template
    template_spreadsheet = gs.open_by_key(template_spreadsheet_id)
    
    # Copy tabs from template to the spreadsheet
    _check_for_missing_worksheets_and_create_them(target_spreadsheet_object = spreadsheet, 
        template_spreadsheet_object = template_spreadsheet, 
        worksheet_name_list = worksheet_name_list)

    # Delete the default sheet
    default_worksheet_to_delete = spreadsheet.worksheet("Sheet1")
    spreadsheet.del_worksheet(default_worksheet_to_delete)
    
    return spreadsheet

def update_magic_spreadsheet_with_new_query_results(spreadsheet_object, worksheet_information_dict: dict, 
        school_information_dict: dict, other_query_parameters_dict: dict, primary_identifier: str,
        secondary_optional_identifier: str = '', colors_dict: dict = {}, worksheet_order_name_list = [], 
        general_editor_list = [],
        # Optional Parameters: Getting Data From Different Source
        # get_data_from_different_source: bool = False, 
        **kwargs,
        # different_source_worksheet_object = None, 
        # different_source_number_of_header_rows = None, different_source_num_columns_on_left_not_to_keep = None,
        # different_source_columns_to_rename = [],
    ):

    # Update all worksheets with fresh query results
    for worksheet_name in worksheet_information_dict.keys():
        logging.info('='*75)
        logging.info(f'Begin updating "{worksheet_name}" worksheet.')

        worksheet_to_update = spreadsheet_object.worksheet(worksheet_name)
        _update_magic_spreadsheet_worksheet_with_new_query_results(
            worksheet_object = worksheet_to_update,
            single_worksheet_information_dict = worksheet_information_dict[worksheet_name],
            query_parameters_dict = {**school_information_dict, **other_query_parameters_dict},
            colors_dict = colors_dict,
            primary_identifier = primary_identifier,
            secondary_optional_identifier = secondary_optional_identifier,
            # get_data_from_different_source = get_data_from_different_source, 
            **kwargs,
            # different_source_worksheet_object = different_source_worksheet_object, 
            # different_source_number_of_header_rows = different_source_number_of_header_rows, 
            # different_source_num_columns_on_left_not_to_keep = different_source_num_columns_on_left_not_to_keep,
            # different_source_columns_to_rename = different_source_columns_to_rename,
        )

        logging.info(f'Done updating "{worksheet_name}" worksheet.')
        
    # Reorder worksheets
    if len(worksheet_order_name_list) > 0:
        _reorder_worksheets(spreadsheet_object, worksheet_order_name_list)
        
    # Re-confirm spreadsheet is shared with all general editors and all school editors
    spreadsheet_editor_list = school_information_dict['spreadsheet_editors']
    full_editor_list = general_editor_list + spreadsheet_editor_list

    for editor in full_editor_list:
        spreadsheet_object.share(editor, perm_type='user', role='writer', notify=False)

def col_to_letter(column_int):
    """
    Adapted from: https://stackoverflow.com/a/23862195
    """
    start_index = 1   #  it can start either at 0 or at 1
    letter = ''
    while column_int > 25 + start_index:   
        letter += chr(65 + int((column_int-start_index)/26) - 1)
        column_int = column_int - (int((column_int-start_index)/26))*26
    letter += chr(65 - start_index + (int(column_int)))

    return letter

def check_for_static_worksheets_and_add_them_with_protection(target_spreadsheet_object, 
    template_spreadsheet_id, static_worksheets_list, primary_editor_email = '', 
    info_team_group_email = '', other_individual_editors_list=[]):

    gs = create_sheets()

    template_spreadsheet_object = gs.open_by_key(template_spreadsheet_id)

    for static_worksheet in static_worksheets_list:
        static_worksheet_name = static_worksheet['worksheet_name']
        _create_worksheet_from_template_if_does_not_exist(target_spreadsheet_object, template_spreadsheet_object, static_worksheet_name)

        if static_worksheet['protected'] == True:
            static_worksheet_object = target_spreadsheet_object.worksheet(static_worksheet_name)
            protected_range_list = target_spreadsheet_object.list_protected_ranges(static_worksheet_object.id)

            target_description = f'"{static_worksheet_name}" Sheet-wide Protection'

            if any(protected_range["description"] == target_description for protected_range in protected_range_list):
                logging.info('Protected range already exists.')
            else:
                logging.info('Protect range not found. Creating new one.')

                individual_editors = [primary_editor_email] + other_individual_editors_list

                num_worksheet_columns = static_worksheet_object.col_count
                final_column_letter = col_to_letter(num_worksheet_columns)

                static_worksheet_object.add_protected_range(name=f'A:{final_column_letter}', 
                    editor_users_emails = individual_editors, 
                    editor_groups_emails=[info_team_group_email], 
                    description = target_description
                )

def update_specific_cell(spreadsheet_object, worksheet_name, cell_a1_notation, text_string):
    worksheet = spreadsheet_object.worksheet(worksheet_name)
    cell = worksheet.acell(cell_a1_notation)
    cell.value = text_string
    worksheet.update_cell(cell.row, cell.col, cell.value)

def _apply_worksheet_formatting(worksheet_object, single_worksheet_information_dict: dict, number_of_header_rows: int, 
    updated_worksheet_row_count: int, colors_dict: dict):
    # Add any validation rules to the worksheet
    if 'data_validations' in single_worksheet_information_dict:
        logging.info('Add the data validations to the worksheet.')
        data_validations_list = single_worksheet_information_dict['data_validations']
        _add_data_validations_to_worksheet(worksheet_object, data_validations_list)
    
    # Re-add any formulas to the worksheet, since they would have been overwritten by hard-coded existing data
    if 'formulas' in single_worksheet_information_dict:
        logging.info('Add the formulas to the worksheet.')
        formulas_list = single_worksheet_information_dict['formulas']
        _add_formulas_to_worksheet(worksheet_object, formulas_list)

    # Hide rows and columns as specified
    if ('num_header_rows_to_hide' in single_worksheet_information_dict or 'num_left_columns_to_hide' in single_worksheet_information_dict):
        logging.info('Hide the specified rows and columns.')
        _hide_header_rows_and_left_columns_in_worksheet(
            worksheet_object = worksheet_object, 
            num_header_rows_to_hide = single_worksheet_information_dict['num_header_rows_to_hide'] if 'num_header_rows_to_hide' in single_worksheet_information_dict else 0,
            num_left_columns_to_hide = single_worksheet_information_dict['num_left_columns_to_hide'] if 'num_left_columns_to_hide' in single_worksheet_information_dict else 0
        )

    # Set basic filter
    if 'filter_on_final_header_row' in single_worksheet_information_dict and single_worksheet_information_dict['filter_on_final_header_row'] == True:
        logging.info('Set the filter on the worksheet.')
        _set_basic_filter_on_worksheet(
            worksheet_object = worksheet_object, 
            row_number_for_filter = number_of_header_rows, 
            final_row_number = updated_worksheet_row_count
        )

    # Refresh conditional formatting
    if 'conditional_formatting_rules' in single_worksheet_information_dict:
        logging.info('Refresh the conditional formatting on the worksheet.')
        _refresh_conditional_formatting_on_worksheet(
            worksheet_object = worksheet_object,
            num_header_rows = number_of_header_rows,
            conditional_formatting_rules_dict = single_worksheet_information_dict['conditional_formatting_rules'],
            colors_dict = colors_dict,
        )

    # Get the last column of the query
    query_column_end = col_to_letter(single_worksheet_information_dict['warehouse_query_number_of_columns'])

    # Update background color for query data to light gray
    background_color_row_start = number_of_header_rows + 1

    background_color_range = f'A{background_color_row_start}:{query_column_end}'

    background_color_format = CellFormat(
        backgroundColor = color(245/255, 245/255, 245/255), # Light Gray
        )

    logging.info('Format the warehouse data cells with the background color.')
    format_cell_range(worksheet_object, background_color_range, background_color_format)

    # Set cell dividing line on right side of query data
    query_data_border_range = f'{query_column_end}:{query_column_end}'
    borders_format = CellFormat(
        borders = {
            'right' : 
                {
                    "style": 'SOLID',
                    "width": 1,
                    "color": {
                        "red": 0,
                        "green": 0,
                        "blue": 0,
                        "alpha": 1
                        }, # Black
                }
            
        }
    )

    logging.info('Set the cell dividing line on the right side of the warehouse data cells.')
    format_cell_range(worksheet_object, query_data_border_range, borders_format)

def _reorder_worksheets(spreadsheet_object, worksheet_order_name_list):
    worksheet_objects_in_desired_order = []

    for worksheet_name in worksheet_order_name_list:
        worksheet = spreadsheet_object.worksheet(worksheet_name)
        worksheet_objects_in_desired_order.append(worksheet)

    spreadsheet_object.reorder_worksheets(worksheet_objects_in_desired_order)

def _get_all_manual_values_from_existing_worksheet(data_source_worksheet_object, data_source_number_of_header_rows,
    primary_identifier, secondary_optional_identifier, num_columns_on_left_not_to_keep, source_columns_to_rename = []):

    # Clear the filter on the worksheet
    data_source_worksheet_object.clear_basic_filter()

    ### Get all data from existing tab
    all_values = data_source_worksheet_object.get_all_values()

    # Turn all_values into a dataframe
    # These values are 0-based but number_of_header_rows is 1-based
    df_all_values = pd.DataFrame(all_values[data_source_number_of_header_rows:], columns=all_values[data_source_number_of_header_rows-1])

    # Rename columns in the different source if needed
    for column_tuple in source_columns_to_rename:
        original_column_name = column_tuple[0]
        new_column_name = column_tuple[1]

        if original_column_name in df_all_values.columns:
            # Rename the column
            df_all_values = df_all_values.rename(columns={original_column_name: new_column_name})

    # Keep only the columns from the spreadsheet that are not getting updated by the query + the identifiers
    # Assume that all worksheets need a primary_identifier column; they may or may not have an secondary_optional_identifier column
    identifier_columns_to_keep = [primary_identifier]

    secondary_optional_identifier_used_on_sheet = (secondary_optional_identifier in df_all_values.columns)

    if secondary_optional_identifier_used_on_sheet == True:
        identifier_columns_to_keep.append(secondary_optional_identifier)

    spreadsheet_keep_columns = identifier_columns_to_keep + list(df_all_values.columns[(num_columns_on_left_not_to_keep):])
    df_spreadsheet_values_to_keep = df_all_values[spreadsheet_keep_columns]

    return df_spreadsheet_values_to_keep, secondary_optional_identifier_used_on_sheet

def _update_magic_spreadsheet_worksheet_with_new_query_results(worksheet_object, single_worksheet_information_dict: dict,
        query_parameters_dict: dict, colors_dict: dict, primary_identifier: str,
        # Optional Parameters: Secondary Identifier
        secondary_optional_identifier: str = '', 
        # Optional Parameters: Getting Data from Different Source
        **kwargs
    ):

    # Add query to query_list and run query
    # TODO: Do we ever need to run multiple queries in one sheet? If not, refactor to run a single query

    query_list = [{
        'path' : single_worksheet_information_dict['warehouse_query_path'],
        'parameters' : query_parameters_dict,
    }]

    logging.info('Run worksheet query in data warehouse.')
    df_query_output = _run_warehouse_query_for_worksheet(query_list)

    # Load key metadata

    number_of_header_rows = single_worksheet_information_dict['number_of_header_rows']
    num_columns_in_query = single_worksheet_information_dict['warehouse_query_number_of_columns']
    
    ### Get all data from existing tab
    gs = create_sheets()

    # Check if parameters passed to get data from a different source
    if 'get_data_from_different_source' in kwargs and kwargs['get_data_from_different_source'] == True:
        # Atypical path: Loading data from a different worksheet than will be writing to
        logging.info('Load data from specified external worksheet.')
        different_source_spreadsheet_object = gs.open_by_key(kwargs['different_source_spreadsheet_id'])
        different_source_worksheet_object = different_source_spreadsheet_object.worksheet(kwargs['different_source_worksheet_name'])

        df_spreadsheet_values_to_keep, secondary_optional_identifier_used_on_sheet = _get_all_manual_values_from_existing_worksheet(
            data_source_worksheet_object = different_source_worksheet_object, 
            data_source_number_of_header_rows = kwargs['different_source_number_of_header_rows'],
            primary_identifier = primary_identifier, 
            secondary_optional_identifier = secondary_optional_identifier, 
            num_columns_on_left_not_to_keep = kwargs['different_source_num_columns_on_left_not_to_keep'],
            source_columns_to_rename = kwargs['different_source_columns_to_rename'],
        )
    else:
        # Standard path: loading data from same worksheet will be writing to
        logging.info('Load data from existing worksheet.')
        df_spreadsheet_values_to_keep, secondary_optional_identifier_used_on_sheet = _get_all_manual_values_from_existing_worksheet(
            data_source_worksheet_object = worksheet_object, 
            data_source_number_of_header_rows = number_of_header_rows,
            primary_identifier = primary_identifier, 
            secondary_optional_identifier = secondary_optional_identifier, 
            num_columns_on_left_not_to_keep = num_columns_in_query
        )
        
    logging.info('Connect user data from existing worksheet to new query output.')
    # Blank out the 'Not Assigned Yet' values in the primary_identifier column of the spreadsheet dataframe to avoid an incorrect join
    df_spreadsheet_values_to_keep[primary_identifier] = df_spreadsheet_values_to_keep[primary_identifier].apply(lambda x: '' if x == 'Not Assigned Yet' else x)
        
    ### Connect data from existing tab to query output in a new dataframe

    # Attempt a match on primary_identifier first
    df_matched_based_on_primary_identifier = df_query_output.merge(df_spreadsheet_values_to_keep, on=primary_identifier, how='left', indicator='primary_identifier_match')

    # Drop duplicate secondary_optional_identifier column
    df_matched_based_on_primary_identifier = df_matched_based_on_primary_identifier.rename(columns={f'{secondary_optional_identifier}_x': secondary_optional_identifier}).drop(f'{secondary_optional_identifier}_y', axis=1)

    # logging.info('Post primary_identifier_match:', df_matched_based_on_primary_identifier.columns)

    # Create a dataframe of successful matches on primary_identifier
    df_only_primary_identifier_matches = df_matched_based_on_primary_identifier[df_matched_based_on_primary_identifier['primary_identifier_match'] == 'both']
    df_only_primary_identifier_matches = df_only_primary_identifier_matches.drop('primary_identifier_match', axis=1)
    
    # Create df_only_failed_primary_identifier_matches for further processing
    df_only_failed_primary_identifier_matches = df_matched_based_on_primary_identifier[df_matched_based_on_primary_identifier['primary_identifier_match'] != 'both']
    df_only_failed_primary_identifier_matches = df_only_failed_primary_identifier_matches.drop('primary_identifier_match', axis=1)

    # Drop blank columns from first match attempt
    df_only_failed_primary_identifier_matches = df_only_failed_primary_identifier_matches.iloc[:,:(num_columns_in_query)]  

    # Adjustments based on whether there is a second identifier column
    if secondary_optional_identifier_used_on_sheet == True:

        # If a row in df_only_failed_primary_identifier_matches contains a number for primary_identifier and 'N/A' for secondary_optional_identifier,
        #   then they are likely a student newly added to the list. Put them in a dataframe so they can be stacked later.
        df_newly_added_students_with_no_primary_identifier_match_and_na_secondary_identifier = df_only_failed_primary_identifier_matches[pd.to_numeric(df_only_failed_primary_identifier_matches[primary_identifier], errors='coerce').notnull() & (df_only_failed_primary_identifier_matches[secondary_optional_identifier] == 'N/A')]
        
        # And then drop these students from df_only_failed_primary_identifier_matches
        df_only_failed_primary_identifier_matches = df_only_failed_primary_identifier_matches.drop(df_newly_added_students_with_no_primary_identifier_match_and_na_secondary_identifier.index)
        
        # Drop rows from existing spreadsheet data where secondary_optional_identifier is 'N/A' and convert columns for merging to numeric
        df_spreadsheet_values_to_keep = df_spreadsheet_values_to_keep[df_spreadsheet_values_to_keep[secondary_optional_identifier] != 'N/A']
        df_spreadsheet_values_to_keep[secondary_optional_identifier] = pd.to_numeric(df_spreadsheet_values_to_keep[secondary_optional_identifier])
        df_only_failed_primary_identifier_matches[secondary_optional_identifier] = pd.to_numeric(df_only_failed_primary_identifier_matches[secondary_optional_identifier])
        
        # Merge on secondary_optional_identifier
        df_secondary_optional_identifier_matches = df_only_failed_primary_identifier_matches.merge(df_spreadsheet_values_to_keep, on=secondary_optional_identifier, how='left')
        
        # Deal with duplicate primary_identifier column
        df_secondary_optional_identifier_matches = df_secondary_optional_identifier_matches.drop(f'{primary_identifier}_y', axis=1).rename(columns={f'{primary_identifier}_x': primary_identifier})
    else:
        # If a row in df_only_failed_primary_identifier_matches contains a number for primary_identifier and there is no secondary_optional_identifier column,
        #   then they are likely a student newly added to the list. Put them in a dataframe so they can be stacked later.
        df_newly_added_students_with_no_primary_identifier_match_and_na_secondary_identifier = df_only_failed_primary_identifier_matches[pd.to_numeric(df_only_failed_primary_identifier_matches[primary_identifier], errors='coerce').notnull()]
        
    # Successful primary_identifier matches and newly added students with no primary_identifier match are always included
    dataframes_to_combine = [
        df_only_primary_identifier_matches, 
        df_newly_added_students_with_no_primary_identifier_match_and_na_secondary_identifier
    ]

    # If there is an secondary_optional_identifier column, include secondary_optional_identifier matches (including matches that failed both primary_identifier and secondary_optional_identifier merges)
    if secondary_optional_identifier_used_on_sheet == True:
        dataframes_to_combine.append(df_secondary_optional_identifier_matches)
    # If there is no secondary_optional_identifier column, include failed primary_identifier matches
    else:
        dataframes_to_combine.append(df_only_failed_primary_identifier_matches)

    # Create single dataframe combining the initial primary_identifier matches, newly added students with no primary_identifier match, failed matches, and if necessary, the secondary_optional_identifier matches
    df_combined_matches = pd.concat(dataframes_to_combine, axis=0)

    # If sorting lists provided, sort the dataframe
    if 'sorting_column_list' in single_worksheet_information_dict and 'sorting_ascending_list' in single_worksheet_information_dict:
        df_combined_matches = df_combined_matches.sort_values(by=single_worksheet_information_dict['sorting_column_list'], 
            ascending=single_worksheet_information_dict['sorting_ascending_list'])

    # Fill NA's so they don't fail when updating the spreadsheet
    df_combined_matches.fillna('', inplace=True)

    # Drop duplicate rows to prevent duplicate identifiers from adding new rows exponentially
    df_combined_matches = df_combined_matches.drop_duplicates()
    
    ### Update existing tab with data from new dataframe

    # Prepare to clear existing tab
    existing_num_worksheet_columns = worksheet_object.col_count
    final_column_letter = col_to_letter(existing_num_worksheet_columns)

    # Check that the df_combined_matches dataframe is not too large for the worksheet before deleting any data
    new_num_worksheet_columns = df_combined_matches.shape[1]

    if(new_num_worksheet_columns > existing_num_worksheet_columns):
        logging.info('existing_num_worksheet_columns:', existing_num_worksheet_columns)
        logging.info('new_num_worksheet_columns:', new_num_worksheet_columns)
        logging.info('df_combined_matches columns:', df_combined_matches.columns.to_list())
        assert False, "Dataframe of updated data has more columns than the existing worksheet. Check for duplicate column names in source worksheet."

    # Clear existing tab
    logging.info('Clear the existing worksheet.')
    worksheet_object.batch_clear([f'A{number_of_header_rows+1}:{final_column_letter}'])

    # Delete all rows on worksheet after headers + first data row
    num_rows_to_delete = worksheet_object.row_count - number_of_header_rows - 1
    if num_rows_to_delete > 0:
        # Indexes are 1-based
        # First row to delete
        delete_start_index = number_of_header_rows + 2 
        # Last row to delete; subtract 1 from the number of rows to delete to get the row # of the last row to delete
        # e.g., deleting 1 row means start and end indexes are the same; deleting 2 rows means end index is 1 more than the start index
        delete_end_index = delete_start_index + num_rows_to_delete - 1
        worksheet_object.delete_rows(delete_start_index, delete_end_index)

    # Calculate the range for the destination worksheet
    updated_worksheet_row_count = df_combined_matches.shape[0] + number_of_header_rows # Number of records + number of header rows
    destination_range = f'A{number_of_header_rows+1}:{final_column_letter}{updated_worksheet_row_count}'

    # Update the destination worksheet
    logging.info('Update the existing worksheet with the new combined data.')
    worksheet_object.update(destination_range, df_combined_matches.values.tolist(), value_input_option='USER_ENTERED')

    # Apply worksheet formatting
    _apply_worksheet_formatting(
        worksheet_object = worksheet_object, 
        single_worksheet_information_dict = single_worksheet_information_dict, 
        number_of_header_rows = number_of_header_rows, 
        updated_worksheet_row_count = updated_worksheet_row_count, 
        colors_dict = colors_dict)
