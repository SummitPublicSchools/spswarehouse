import gspread
import os
import pickle

from .credentials import google_config

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession, Request

def initialize_credentials():
    """
    initialize_credentials: -> google.oauth2.credentials.Credentials

    Returns credentials that allows you to access your Google Drive &
    Sheets using the Google Sheets API.

    If you haven't authorized access prior to this, it will prompt you
    to login via your browser using your Google login.
    """
    creds = None

    # Try to load existing user credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in
    if creds is None or not creds.valid:
        if creds is not None and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                {'installed': google_config['oauth2-client-id']},
                google_config['scopes'],
            )
            creds = flow.run_local_server()

        # Save the credentials for next time
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def create_client(credentials):
    """
    create_engine:

    Sets up Google Sheets API access using credentials (see above).
    """
    client = gspread.Client(auth=credentials)
    client.session = AuthorizedSession(credentials)
    return client

# Set up credentials
credentials = initialize_credentials()

# This is a wrapper for gspread.Client
GoogleSheets = create_client(credentials)
