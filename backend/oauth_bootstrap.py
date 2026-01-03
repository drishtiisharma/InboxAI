from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        SCOPES
    )

    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent"
    )

    print("\n===== COPY THESE VALUES =====\n")
    print("GMAIL_ACCESS_TOKEN =", creds.token)
    print("GMAIL_REFRESH_TOKEN =", creds.refresh_token)
    print("GOOGLE_CLIENT_ID =", creds.client_id)
    print("GOOGLE_CLIENT_SECRET =", creds.client_secret)
    print("\n=============================\n")

if __name__ == "__main__":
    main()
