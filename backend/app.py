# app.py - Fix middleware
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from db import init_db
init_db()

from services.auth import auth_router

from models import (
    CommandPayload,
    SendEmailRequest,
    DraftRequest,
    MeetingRequest
)


from services.gmail_client import (
    get_gmail_service,
    send_email,
    get_unread_emails,
    summarize_email,
    get_credentials_for_user
)

app = FastAPI()
from services.calendar_client import create_meeting
from services.draft_service import generate_email_drafts
# ===================== MIDDLEWARE =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow ALL origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Add this line
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "super-secret-session-key-change-me"),
    session_cookie="inboxai_session",
    same_site="none",
    https_only=True  
)


# ===================== ROUTERS =====================
app.include_router(auth_router)

# ===================== HEALTH =====================
@app.get("/")
async def health():
    return {"status": "InboxAI backend running 🚀"}

# ===================== COMMAND HANDLER =====================
@app.post("/command")
async def handle_command(payload: CommandPayload, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        creds = get_credentials_for_user(user_email)
        gmail_service = get_gmail_service(creds)

        command = payload.command.lower()

        if "unread" in command:
            return get_unread_emails_summary(creds)

        if "last email" in command:
            return get_last_email_summary(creds)

        if "from" in command:
            return check_emails_from_sender(creds, command)

        if "schedule" in command or "meeting" in command:
            return await create_meeting_from_command(command, request)

        return {"reply": "Sorry, I didn't understand that command."}

    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Command processing failed")

# ===================== EMAIL DRAFT =====================
@app.post("/email/draft")
async def draft_email(payload: DraftRequest, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Generate drafts using AI
        drafts = generate_email_drafts(
            intent=payload.intent,
            receiver=payload.receiver,
            tone=payload.tone,
            context=payload.context
        )
        
        return {
            "data": {
                "drafts": drafts
            }
        }
        
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to generate drafts")

# ===================== CREATE MEETING =====================
@app.post("/meeting/create")
async def create_meeting_route(payload: MeetingRequest, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        creds = get_credentials_for_user(user_email)
        
        meet_link = create_meeting(
            creds=creds,
            title=payload.title,
            recipients=payload.recipients,
            date=payload.date,
            time=payload.time,
            duration=payload.duration,
            agenda=payload.agenda
        )
        
        return {
            "data": {
                "meet_link": meet_link
            }
        }
        
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create meeting")

# ===================== EMAIL HELPERS =====================
def get_unread_emails_summary(creds): 
    emails = get_unread_emails(creds)  
    if not emails:
        return {"reply": "No unread emails 🎉"}

    service = get_gmail_service(creds)  
    summaries = [summarize_email(service, e["id"]) for e in emails[:3]]
    return {"reply": "\n\n".join(summaries)}

def get_last_email_summary(creds):  
    emails = get_unread_emails(creds, max_results=1)  
    if not emails:
        return {"reply": "No emails found."}

    service = get_gmail_service(creds)  
    summary = summarize_email(service, emails[0]["id"])
    return {"reply": summary}

def check_emails_from_sender(creds, command: str): 
    sender = command.split("from")[-1].strip()
    emails = get_unread_emails(creds, query=f"from:{sender}") 

    if not emails:
        return {"reply": f"No unread emails from {sender}."}

    return {"reply": f"You have {len(emails)} unread emails from {sender}."}

# ===================== MEETING =====================
async def create_meeting_from_command(command: str, request: Request):
    user_email = request.session.get("user")
    creds = get_credentials_for_user(user_email)

    meet_link = create_meeting(
        creds=creds,
        summary="Meeting via InboxAI",
        description=command
    )

    return {
        "reply": "Meeting created successfully.",
        "meet_link": meet_link
    }

# ===================== SEND EMAIL =====================
@app.post("/email/send")
async def send_email_route(req: SendEmailRequest, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        creds = get_credentials_for_user(user_email)
        service = get_gmail_service(creds)

        result = send_email(
            service=service,
            to=req.to,
            subject=req.subject,
            body=req.body
        )

        return {
            "reply": f"Email successfully sent to {req.to}.",
            "data": {
                "message_id": result.get("id")
            }
        }

    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to send email")
    

@app.on_event("startup")
async def startup_event():
    print("\n=== Registered Routes ===")
    for route in app.routes:
        print(f"{route.methods} {route.path}")
    print("=======================\n")
