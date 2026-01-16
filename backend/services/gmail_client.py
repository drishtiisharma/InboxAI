import os
import base64
import re
from email.message import EmailMessage

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

from ai_logic.email import summarize_email_logic
from ai_logic.readers.attachment_processor import (
    process_all_attachments,
    create_attachment_summary
)

# ============================ CREDENTIALS ============================

def get_credentials_for_user(email: str):
    """
    Get Google credentials for a specific user using their refresh token from DB.
    """
    from db import get_refresh_token  # avoid circular import

    refresh_token = get_refresh_token(email)
    if not refresh_token:
        raise Exception(f"No credentials found for user: {email}")

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise Exception("Google OAuth credentials not configured")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=[
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid"
        ]
    )

    if creds.expired or not creds.valid:
        creds.refresh(GoogleRequest())

    return creds

# ============================ GMAIL SERVICE ============================

def get_gmail_service(creds):
    if not creds:
        raise RuntimeError("Missing Google credentials")

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

            file_data = base64.urlsafe_b64decode(att["data"].encode("utf-8"))

            os.makedirs("temp_attachments", exist_ok=True)
            file_path = os.path.join("temp_attachments", part["filename"])

            with open(file_path, "wb") as f:
                f.write(file_data)

            attachments_list.append({
                "filename": part["filename"],
                "path": file_path
            })

        if part.get("parts"):
            extract_attachments(part, service, message_id, attachments_list)

# ============================ TEXT CLEANING ============================

def clean_email_text(text: str):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)

    blacklist = [
        "unsubscribe",
        "view in browser",
        "privacy policy",
        "terms",
        "copyright"
    ]

    sentences = text.split(". ")
    useful = [
        s for s in sentences
        if not any(b in s.lower() for b in blacklist)
    ]

    return ". ".join(useful).strip()

# ============================ READ + AI SUMMARIZE EMAILS ============================

def get_unread_emails(creds, max_results=10, query: str = None):
    """
    Fetch unread emails and summarize them using AI.
    """
    service = get_gmail_service(creds)

    q = ["is:unread"]
    if query:
        q.append(query)

    results = service.users().messages().list(
        userId="me",
        q=" ".join(q),
        maxResults=max_results
    ).execute()

    emails = []

    for msg in results.get("messages", []):
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
        clean_body = clean_email_text(body)

        attachments = []
        extract_attachments(payload, service, msg["id"], attachments)

        attachment_text = ""
        if attachments:
            processed = process_all_attachments(attachments)
            attachment_text = create_attachment_summary(processed)

        summary = summarize_email_logic(
            body=clean_body,
            sender=sender,
            subject=subject,
            attachments=attachment_text
        )

        emails.append({
            "id": msg["id"],
            "from": sender,
            "subject": subject,
            "summary": summary,
            "attachments": attachments
        })

    return emails
def summarize_email(service, message_id: str):
    """
    Summarize a single email by ID.
    This exists because app.py IMPORTS IT.
    """
    msg_data = service.users().messages().get(
        userId="me",
        id=message_id,
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
    clean_body = clean_email_text(body)

    attachments = []
    extract_attachments(payload, service, message_id, attachments)

    attachment_text = ""
    if attachments:
        processed = process_all_attachments(attachments)
        attachment_text = create_attachment_summary(processed)

    return summarize_email_logic(
        body=clean_body,
        sender=sender,
        subject=subject,
        attachments=attachment_text
    )

# ============================ SEND EMAIL ============================

def send_email(service, to: str, subject: str, body: str):
    message = EmailMessage()
    message.set_content(body)

    message["To"] = to
    message["From"] = "me"
    message["Subject"] = subject

    encoded = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    return service.users().messages().send(
        userId="me",
        body={"raw": encoded}
    ).execute()
