import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service(token_json: dict):
    """
    token_json = stored OAuth token dict
    """
    creds = Credentials.from_authorized_user_info(token_json, SCOPES)
    service = build("gmail", "v1", credentials=creds)
    return service


def _decode_body(payload):
    """
    Extract + decode email body safely
    """
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part["body"].get("data")
                if data:
                    body += base64.urlsafe_b64decode(data).decode("utf-8")
    else:
        data = payload["body"].get("data")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8")

    return body.strip()


def fetch_latest_emails(service, max_results=5):
    """
    Returns list of plain-text email bodies
    """
    results = service.users().messages().list(
        userId="me",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        payload = msg_data.get("payload", {})
        body = _decode_body(payload)

        if body:
            emails.append(body)

    return emails
