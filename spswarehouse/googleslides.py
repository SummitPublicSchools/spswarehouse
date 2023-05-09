import os
import pickle

try:
    from .credentials import google_config
except ModuleNotFoundError:
    print("No credentials file found in spswarehouse. This could cause issues.")

from googleapiclient.discovery import build

from oauth2client.service_account import ServiceAccountCredentials

def get_google_service_account_email():
    """
    Returns the service account email to share slides with.
    """
    return google_config['service-account']['client_email']

def initialize_credentials():
    """
    initialize_credentials: -> oauth2client.service_account.ServiceAccountCredentials

    Returns credentials that allows you to access your Google Slides
    using the Google Sheets API.

    You still need to share slides with the service account email.
    """

    # This prevents us from erroring out trying to construct credentials
    # from incomplete information.
    service_account = google_config.get('service-account', {})
    private_key = service_account.get('private_key', None)
    if not private_key:
        print(
            "You're missing Google service account credentials",
            "in credentials.py.",
            "To access your Google Slides,",
            "fill out the Google service account information."
        )
        return None

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        google_config['service-account'],
        scopes=google_config['scopes'],
    )
    print(
        'To access your Google Slides, share the file with {email}'
        .format(email=get_google_service_account_email())
    )
    return credentials

def create_client(credentials):
    """
    create_engine:

    Sets up Google Drive API access using credentials (see above).
    """
    slides = build('slides', 'v1', credentials=credentials)
    return slides

# Set up credentials
credentials = initialize_credentials()

# This is a wrapper for a standard Google Slides engine
GoogleSlides = None if credentials is None else create_client(credentials)
