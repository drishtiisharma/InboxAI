from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from db import get_refresh_token
import os

SCOPES = [
    # FIX: gmail.modify was listed in gmail_client.py but missing here
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]


def get_credentials_for_user(email: str) -> Credentials:
    refresh_token = get_refresh_token(email)

    if not refresh_token:
        raise Exception(f"User not authenticated: {email}")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )

    # FIX: only refresh when actually needed (expired or no valid token)
    if not creds.valid:
        creds.refresh(Request())

    return creds