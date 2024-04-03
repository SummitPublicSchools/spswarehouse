import os
import pickle

try:
    from .credentials import google_config
except ModuleNotFoundError:
    print("No credentials file found in spswarehouse. This could cause issues.")

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from oauth2client.service_account import ServiceAccountCredentials

def get_google_service_account_email():
    """
    Returns the service account email to share Drive files with.
    """
    return google_config['service-account']['client_email']

def initialize_auth():
    """
    initialize_auth: -> pydrive2.auth.GoogleAuth

    Returns an Auth object that allows you to access your Google Drive &
    Sheets using the Google Drive API.

    You still need to share files with the service account email.

    Note: we use a GoogleAuth object rather than just passing a credentials
    file so that pydrive can create refresh tokens if necessary. This only
    is an issue when you want run a notebook for longer than an hour, but it
    does come up.
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

    gauth = GoogleAuth()
    gauth.client_config["client_user_email"] = get_google_service_account_email()
    gauth.client_config["client_json_dict"] = service_account
    gauth.settings["oauth_scope"] = google_config['scopes']
    gauth.ServiceAuth()
    print(
        'To access your Google Drive file, share the file with {email}'
        .format(email=gauth.client_config["client_user_email"])
    )
    return gauth

def create_client(gauth):
    """
    create_engine:

    Sets up Google Drive API access using an Auth object (see above).
    """
    return GoogleDrive(gauth)

# Set up credentials
gauth = initialize_auth()

# This is a wrapper for pydrive.GoogleDrive
GoogleDrive = None if gauth is None else create_client(gauth)
