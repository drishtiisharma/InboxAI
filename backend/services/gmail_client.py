import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ai_logic.readers.attachment_processor import (
    process_all_attachments,
    create_attachment_summary
)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )

    if not creds.refresh_token:
        raise RuntimeError("Missing GMAIL_REFRESH_TOKEN env var")

    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


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
        parts = payload.get("parts", [])

        # -------- Headers --------
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")

        # -------- Body --------
        body = ""
        if parts:
            for part in parts:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(
                        part["body"]["data"]
                    ).decode("utf-8", errors="ignore")
                    break
        else:
            if payload.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(
                    payload["body"]["data"]
                ).decode("utf-8", errors="ignore")

        # -------- Attachments --------
        attachments = []

        for part in parts:
            if part.get("filename") and part.get("body", {}).get("attachmentId"):
                att_id = part["body"]["attachmentId"]

                att = service.users().messages().attachments().get(
                    userId="me",
                    messageId=msg["id"],
                    id=att_id
                ).execute()

                file_data = base64.urlsafe_b64decode(att["data"].encode("UTF-8"))

                os.makedirs("temp_attachments", exist_ok=True)
                file_path = f"temp_attachments/{part['filename']}"

                with open(file_path, "wb") as f:
                    f.write(file_data)

                attachments.append({
                    "filename": part["filename"],
                    "path": file_path
                })

        # -------- Process attachments --------
        attachment_text = ""
        if attachments:
            processed = process_all_attachments(attachments)
            attachment_text = create_attachment_summary(processed)

        # -------- Final email object --------
        emails.append({
            "id": msg["id"],
            "from": sender,
            "subject": subject,
            "body": body,
            "attachment_text": attachment_text
        })

    return emails
