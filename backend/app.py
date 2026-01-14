# app.py — InboxAI (LLM-first, non-hardcoded)

import os
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

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
    summarize_email,
    get_credentials_for_user
)
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

# ===================== GROQ SETUP =====================
import groq

groq_client = None
if os.environ.get("GROQ_API_KEY"):
    groq_client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])

# ===================== CHAT FALLBACK =====================
async def chat_with_ai(user_email: str, message: str):
    if not groq_client:
        return "AI service is currently unavailable."

    history = get_conversation_history(user_email, limit=10)

    messages = [
        {
            "role": "system",
            "content": (
                "You are InboxAI, a smart email and calendar assistant.\n"
                "You can chat normally and also decide when to use tools.\n"
                "If something is casual conversation, just reply normally."
            )
        }
    ]

    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": message})

    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )

        reply = response.choices[0].message.content

        save_conversation(user_email, "user", message)
        save_conversation(user_email, "assistant", reply)

        return reply

    except Exception:
        traceback.print_exc()
        return "I ran into an issue. Try again."

# ===================== EMAIL HELPERS =====================
def get_unread_emails_summary(creds):
    emails = get_unread_emails(creds)
    if not emails:
        return {"reply": "You have no unread emails 🎉"}

    service = get_gmail_service(creds)
    summaries = [summarize_email(service, e["id"]) for e in emails[:3]]

    return {"reply": "\n\n".join(summaries)}

def get_last_email_summary(creds):
    emails = get_unread_emails(creds, max_results=1)
    if not emails:
        return {"reply": "You have no unread emails."}

    service = get_gmail_service(creds)
    return {"reply": summarize_email(service, emails[0]["id"])}

def check_emails_from_sender(creds, sender: str):
    emails = get_unread_emails(creds, query=f"from:{sender}")
    if not emails:
        return {"reply": f"No unread emails from {sender}."}

    return {"reply": f"You have {len(emails)} unread emails from {sender}."}

# ===================== COMMAND ROUTE =====================
@app.post("/command")
async def handle_command(payload: CommandPayload, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        command = payload.command.strip()

        # 🔹 trivial shortcuts (NO AI)
        if command.lower() in ["hi", "hello", "hey"]:
            return {"reply": "Hi 👋 What can I help you with?"}

        if "thank" in command.lower():
            return {"reply": "Anytime 😊"}

        # 🔹 creds only if needed
        creds = None
        if any(k in command.lower() for k in ["email", "mail", "inbox", "calendar", "meeting"]):
            creds = get_credentials_for_user(user_email)

        # 🔹 FUNCTION MAP (RESTORED)
        function_map = {
            "get_unread_emails_summary": lambda: get_unread_emails_summary(creds),
            "get_last_email_summary": lambda: get_last_email_summary(creds),
            "check_emails_from_sender": lambda sender=None: check_emails_from_sender(creds, sender),
        }

        # 🔹 LLM decides what to do
        result = intelligent_command_handler(
            command=command,
            function_map=function_map,
            history=get_conversation_history(user_email)
        )

        if isinstance(result, dict):
            save_conversation(user_email, "user", command)
            save_conversation(user_email, "assistant", result.get("reply", ""))
            return result

        # 🔹 fallback to chat
        reply = await chat_with_ai(user_email, command)
        return {"reply": reply}

    except Exception:
        traceback.print_exc()
        return {"reply": "Something went wrong. Try again."}

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

# ===================== CREATE MEETING =====================
@app.post("/meeting/create")
async def create_meeting_route(payload: MeetingRequest, request: Request):
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

    return {"data": {"meet_link": meet_link}}

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
