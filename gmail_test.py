from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

#============================SETTING PERMISSION================================
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    creds = None
#============================AUTHENTICATION FLOW=================================

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

#============================FETCHING EMAIL LIST=================================

    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me", maxResults=5
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        print("No emails found.")
        return

    print("Latest emails:")
    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", id=msg["id"]
        ).execute()

        headers = msg_data["payload"]["headers"]
        subject = next(
            (h["value"] for h in headers if h["name"] == "Subject"),
            "(No Subject)"
        )

        print("-", subject)

if __name__ == "__main__":
    main()
