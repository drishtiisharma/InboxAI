from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from db import get_refresh_token
import os

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

def get_credentials_for_user(email: str):
    refresh_token = get_refresh_token(email)

    if not refresh_token:
        raise Exception("User not authenticated")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )

    creds.refresh(Request())
    return creds
