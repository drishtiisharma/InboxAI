# app.py — InboxAI (PURE LLM-FIRST)

import os
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from services.gmail_client import get_unread_emails
from ai_logic.readers.attachment_processor import (
    process_all_attachments,
    create_attachment_summary
)
from db import init_db, save_conversation, get_conversation_history
init_db()

# ===================== IMPORTS =====================
from models import (
    CommandPayload,
    SendEmailRequest,
    DraftRequest,
    MeetingRequest
)

from services.auth import auth_router
from services.gmail_client import (
    get_gmail_service,
    get_unread_emails,
    send_email,
    get_credentials_for_user
)
from services.gmail_client import summarize_email

from services.calendar_client import create_meeting
from services.draft_service import generate_email_drafts
from services.llm_client import intelligent_command_handler

# ===================== APP =====================
app = FastAPI(title="InboxAI Backend")

# ===================== MIDDLEWARE =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "change-me"),
    session_cookie="inboxai_session",
    same_site="none",
    https_only=True
)

# ===================== EMAIL HELPERS =====================
def get_unread_emails_summary(user_email: str):
    creds = get_credentials_for_user(user_email)
    emails = get_unread_emails(creds)

    if not emails:
        return {"reply": "You have no unread emails 🎉"}

    service = get_gmail_service(creds)
    summaries = [summarize_email(service, e["id"]) for e in emails[:3]]
    return {"reply": "\n\n".join(summaries)}


def get_last_email_summary(user_email: str):
    creds = get_credentials_for_user(user_email)
    emails = get_unread_emails(creds, max_results=1)

    if not emails:
        return {"reply": "You have no unread emails."}

    service = get_gmail_service(creds)
    return {"reply": summarize_email(service, emails[0]["id"])}


def check_emails_from_sender(user_email: str, sender_query: str):
    creds = get_credentials_for_user(user_email)
    emails = get_unread_emails(creds, query=f"from:{sender_query}")

    if not emails:
        return {"reply": f"No unread emails from {sender_query}."}

    return {"reply": f"You have {len(emails)} unread emails from {sender_query}."}


def get_unread_email_categories_handler(user_email: str):
    return {
        "reply": "Email categories feature is under development.",
        "data": None
    }


# ===================== COMMAND ROUTE =====================
@app.post("/command")
async def handle_command(payload: CommandPayload, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        command = payload.command.strip()

        function_map = {
    "get_unread_emails_summary": lambda **_: get_unread_emails_summary(user_email),

    "get_last_email_summary": lambda **_: get_last_email_summary(user_email),

    "check_emails_from_sender": lambda **kwargs: check_emails_from_sender(
        user_email,
        kwargs.get("sender_query")
    ),

    "get_unread_email_categories": lambda **_: get_unread_email_categories_handler(user_email),

    "create_meeting": lambda **kwargs: {
        "reply": "Meeting created successfully.",
        "data": {
            "meet_link": create_meeting(
                creds=get_credentials_for_user(user_email),
                **kwargs
            )
        }
    }
}
        attachment_summary = ""
        try:
            creds = get_credentials_for_user(user_email)
            emails = get_unread_emails(creds, max_results=1)

            if emails and isinstance(emails[0].get("attachments"), list):
                processed = process_all_attachments(emails[0]["attachments"])
                attachment_summary = create_attachment_summary(processed)
        except Exception:
            attachment_summary = ""

        save_conversation(user_email, "user", command)

        result = intelligent_command_handler(
    user_message=command,
    function_map=function_map,  
    history=get_conversation_history(user_email),
    attachment_summary=attachment_summary,
)



        save_conversation(user_email, "assistant", result.get("reply", ""))

        return result

    except Exception as e:
        traceback.print_exc()
        return {"reply": f"Backend error: {str(e)}"}


# ===================== EMAIL DRAFT =====================
@app.post("/email/draft")
async def draft_email(payload: DraftRequest, request: Request):
    user_email = request.session.get("user")
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")

    drafts = generate_email_drafts(
        intent=payload.intent,
        receiver=payload.receiver,
        tone=payload.tone,
        context=payload.context
    )

    return {"data": {"drafts": drafts}}

# ===================== SEND EMAIL =====================
@app.post("/email/send")
async def send_email_route(req: SendEmailRequest, request: Request):
    user_email = request.session.get("user")
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")

    creds = get_credentials_for_user(user_email)
    service = get_gmail_service(creds)
    result = send_email(service, req.to, req.subject, req.body)

    return {"reply": f"Email sent to {req.to}.", "data": result}

# ===================== AUTH =====================
app.include_router(auth_router)

# ===================== LOGOUT =====================
@app.post("/auth/logout")
def logout(request: Request):
    response = JSONResponse({"success": True})
    request.session.clear()
    response.delete_cookie("inboxai_session")
    return response

# ===================== HEALTH =====================
@app.get("/")
def health():
    return {"status": "InboxAI backend running 🚀"}
