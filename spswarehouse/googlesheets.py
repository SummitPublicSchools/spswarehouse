import gspread
import os
import pickle

from .credentials import google_config

from oauth2client.service_account import ServiceAccountCredentials

def get_google_service_account_email():
    """
    Returns the service account email to share spreadsheets with.
    """
    return google_config['service-account']['client_email']

def initialize_credentials():
    """
    initialize_credentials: -> oauth2client.service_account.ServiceAccountCredentials

    Returns credentials that allows you to access your Google Drive &
    Sheets using the Google Sheets API.

    You still need to share spreadsheets with the service account email.
    """
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        google_config['service-account'],
        scopes=google_config['scopes'],
    )
    print(
        'To access your Google spreadsheet data, share the spreadsheet with {email}'
        .format(email=google_config['service-account']['client_email'])
    )
    return credentials

def create_client(credentials):
    """
    create_engine:

    Sets up Google Sheets API access using credentials (see above).
    """
    client = gspread.authorize(credentials)
    return client

# Set up credentials
credentials = initialize_credentials()

# This is a wrapper for gspread.Client
GoogleSheets = create_client(credentials)
