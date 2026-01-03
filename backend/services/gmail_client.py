import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


CLIENT_SECRET_PATH = "/etc/secrets/client_secret.json"
TOKEN_PATH = "/etc/secrets/token.json"

def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            TOKEN_PATH, SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 🚫 DO NOT run OAuth flow on Render
            raise RuntimeError(
                "OAuth token missing or invalid. Generate token.json locally."
            )

    return build('gmail', 'v1', credentials=creds)

def get_unread_emails(max_results=10):
    service = get_gmail_service()
    results = service.users().messages().list(
        userId='me',
        labelIds=['UNREAD'],
        maxResults=max_results
    ).execute()
    
    messages = results.get('messages', [])
    
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()
        
        # Extract headers
        headers = msg_data['payload']['headers']
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        
        # Extract body
        body = ""
        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        else:
            if 'data' in msg_data['payload']['body']:
                body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
        
        emails.append({
            "id": msg['id'],
            "sender": sender,
            "subject": subject,
            "body": body
        })
    
    return emails