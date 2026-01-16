def get_credentials_for_user(email):
    refresh_token = db.get_refresh_token(email)

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token"
    )

    creds.refresh(Request())
    return creds
