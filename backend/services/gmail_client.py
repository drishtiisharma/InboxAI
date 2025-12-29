import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    creds = Credentials(
        token=os.getenv("GMAIL_ACCESS_TOKEN"),
        refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=creds)


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


def extract_email_body(msg: dict) -> str:
    payload = msg.get("payload", {})

    def walk(parts):
        for part in parts:
            mime = part.get("mimeType")
            body = part.get("body", {}).get("data")

            if mime == "text/plain" and body:
                return _decode(body)

            if mime == "text/html" and body:
                soup = BeautifulSoup(_decode(body), "html.parser")
                return soup.get_text(separator=" ")

            if "parts" in part:
                found = walk(part["parts"])
                if found:
                    return found
        return ""

    if "parts" in payload:
        return walk(payload["parts"])

    if payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])

    return ""


def get_last_email():
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me",
        maxResults=1
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return None

    msg = service.users().messages().get(
        userId="me",
        id=messages[0]["id"],
        format="full"
    ).execute()

    headers = msg.get("payload", {}).get("headers", [])
    sender = next(
        (h["value"] for h in headers if h["name"].lower() == "from"),
        "Unknown sender"
    )

    body = extract_email_body(msg)

    return {"sender": sender, "body": body}
