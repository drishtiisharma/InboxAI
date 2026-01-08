import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.message import EmailMessage
from ai_logic.readers.attachment_processor import (
    process_all_attachments,
    create_attachment_summary
)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/calendar"]


TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "client_secret.json"


# ============================ GMAIL SERVICE ============================

def get_gmail_service():
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, force OAuth login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise RuntimeError("Missing client_secret.json for Gmail OAuth")

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=0, prompt="consent")

        # Save token for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ============================ BODY EXTRACTION ============================

def extract_body(payload):
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8", errors="ignore")

    parts = payload.get("parts", [])
    html_body = ""

    for part in parts:
        mime = part.get("mimeType")

        if mime == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(
                part["body"]["data"]
            ).decode("utf-8", errors="ignore")

        if mime == "text/html" and part.get("body", {}).get("data"):
            html_body = base64.urlsafe_b64decode(
                part["body"]["data"]
            ).decode("utf-8", errors="ignore")

        if part.get("parts"):
            nested = extract_body(part)
            if nested:
                return nested

    return html_body


# ============================ ATTACHMENTS ============================

def extract_attachments(payload, service, message_id, attachments_list):
    parts = payload.get("parts", [])

    for part in parts:
        if part.get("filename") and part.get("body", {}).get("attachmentId"):
            att_id = part["body"]["attachmentId"]

            att = service.users().messages().attachments().get(
                userId="me",
                messageId=message_id,
                id=att_id
            ).execute()

            file_data = base64.urlsafe_b64decode(att["data"].encode("UTF-8"))

            os.makedirs("temp_attachments", exist_ok=True)
            file_path = f"temp_attachments/{part['filename']}"

            with open(file_path, "wb") as f:
                f.write(file_data)

            attachments_list.append({
                "filename": part["filename"],
                "path": file_path
            })

        if part.get("parts"):
            extract_attachments(part, service, message_id, attachments_list)


# ============================ MAIN FUNCTION ============================

def get_unread_emails(max_results=10):
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me",
        labelIds=["UNREAD"],
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
        headers = payload.get("headers", [])

        sender = next(
            (h["value"] for h in headers if h["name"].lower() == "from"),
            "Unknown"
        )

        subject = next(
            (h["value"] for h in headers if h["name"].lower() == "subject"),
            "No Subject"
        )

        body = extract_body(payload)

        attachments = []
        extract_attachments(payload, service, msg["id"], attachments)

        attachment_text = ""
        if attachments:
            try:
                processed = process_all_attachments(attachments)
                attachment_text = create_attachment_summary(processed)
            except Exception as e:
                attachment_text = f"[Error processing {len(attachments)} attachment(s)]"

        emails.append({
            "id": msg["id"],
            "from": sender,
            "subject": subject,
            "body": body,
            "attachments": attachments,
            "attachment_text": attachment_text
        })

    return emails
# ============================ SEND EMAIL ============================
def send_email(service, to: str, subject: str, body: str):
    message = EmailMessage()
    message.set_content(body)

    message["To"] = to
    message["From"] = "me"
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    send_body = {
        "raw": encoded_message
    }

    sent_message = (
        service.users()
        .messages()
        .send(userId="me", body=send_body)
        .execute()
    )

    return sent_message

def get_google_credentials():
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError("Google user not authenticated")

    creds = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds
