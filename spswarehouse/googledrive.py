import os
import pickle

from .credentials import google_config

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

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

    # This prevents us from erroring out trying to construct credentials
    # from incomplete information.
    service_account = google_config.get('service-account', {})
    private_key = service_account.get('private_key', None)
    if not private_key:
        print(
            "You're missing Google service account credentials",
            "in credentials.py.",
            "To access your Google Drive data,",
            "fill out the Google service account information."
        )
        return None

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        google_config['service-account'],
        scopes=google_config['scopes'],
    )
    print(
        'To access your Google Drive file, share the file with {email}'
        .format(email=get_google_service_account_email())
    )
    return credentials

def create_client(credentials):
    """
    create_engine:

    Sets up Google Sheets API access using credentials (see above).
    """
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    return drive

# Set up credentials
credentials = initialize_credentials()

# This is a wrapper for gspread.Client
GoogleDrive = None if credentials is None else create_client(credentials)
