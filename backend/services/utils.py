import os
import db  # FIX: was referenced but never imported

from google.oauth2.credentials import Credentials  # FIX: missing import
from google.auth.transport.requests import Request  # FIX: missing import

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")         # FIX: was used but never defined
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")  # FIX: was used but never defined


def get_credentials_for_user(email: str) -> Credentials:
    refresh_token = db.get_refresh_token(email)

    if not refresh_token:
        raise Exception(f"No refresh token found for user: {email}")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token"
    )

    # Only refresh if the token is not already valid
    if not creds.valid:
        creds.refresh(Request())

    return creds