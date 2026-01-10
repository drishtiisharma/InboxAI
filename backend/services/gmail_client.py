import os
import base64
import re
from googleapiclient.discovery import build
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

from ai_logic.readers.attachment_processor import (
    process_all_attachments,
    create_attachment_summary
)

# ============================ CREDENTIALS ============================
def get_credentials_for_user(email: str):
    """
    Get Google credentials for a specific user using their refresh token from DB.
    """
    # Import here to avoid circular imports
    from db import get_refresh_token
    
    refresh_token = get_refresh_token(email)
    if not refresh_token:
        raise Exception(f"No credentials found for user: {email}")
    
    # Get client ID and secret from environment
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise Exception("Google OAuth credentials not configured")
    
    # Create credentials from refresh token
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=[
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid"
        ]
    )
    
    # Refresh token if needed
    if creds.expired or not creds.valid:
        try:
            creds.refresh(GoogleRequest())
        except Exception as e:
            raise Exception(f"Failed to refresh credentials: {str(e)}")
    
    return creds

# ============================ GMAIL SERVICE ============================

def get_gmail_service(creds):
    """
    Build Gmail service using already-authenticated credentials.
    creds MUST be a valid google.oauth2.credentials.Credentials object.
    """
    if not creds:
        raise RuntimeError("Missing Google credentials")

    return build("gmail", "v1", credentials=creds)

# ============================ EMAIL SUMMARIZATION ============================

def summarize_email(service, message_id: str):
    """
    Summarize a single email by its ID.
    This function is called from app.py - MUST EXIST!
    """
    try:
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
        
        # Clean up body - remove HTML tags
        clean_body = re.sub(r'<[^>]+>', '', body)
        clean_body = clean_body.replace('\r', '').replace('\n', ' ').strip()
        
        # Simple summary - first 150 chars
        if len(clean_body) > 150:
            summary = clean_body[:147] + "..."
        else:
            summary = clean_body
        
        return f"From: {sender}\nSubject: {subject}\nSummary: {summary}"
        
    except Exception as e:
        print(f"Error summarizing email {message_id}: {e}")
        return f"Error summarizing email"

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

# ============================ READ UNREAD EMAILS ============================

def get_unread_emails(creds, max_results=10, query: str = None):
    """
    Fetch unread emails for the authenticated user.
    """
    service = get_gmail_service(creds)
    
    # Build query
    query_params = ["is:unread"]
    if query:
        query_params.append(query)
    
    full_query = " ".join(query_params)

    results = service.users().messages().list(
        userId="me",
        q=full_query,
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
                print(f"Error processing attachments: {e}")
                attachment_text = "[Error processing attachments]"

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
    """
    Send an email using an already-built Gmail service.
    """
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