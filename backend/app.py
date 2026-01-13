# app.py - Fix middleware
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from fastapi.responses import JSONResponse
from db import init_db, save_conversation, get_conversation_history
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "super-secret-session-key-change-me"),
    session_cookie="inboxai_session",
    same_site="none",
    https_only=True  
)

# ===================== GROQ AI SETUP =====================
import groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    groq_client = groq.Groq(api_key=GROQ_API_KEY)
else:
    print("⚠️ GROQ_API_KEY not set. AI features will be limited.")
    groq_client = None

# ===================== AI CHAT FUNCTION =====================
async def chat_with_ai(user_email: str, user_message: str):
    """Chat with Groq AI with conversation memory"""
    if not groq_client:
        return "AI service is currently unavailable. Please try basic commands."
    
    # Get conversation history
    history = get_conversation_history(user_email, limit=10)
    
    # Prepare messages for AI
    messages = [
        {
            "role": "system",
            "content": """You are InboxAI, a helpful email and calendar assistant. 
            You can help users with:
            1. Checking and reading emails from Gmail
            2. Writing and sending emails
            3. Scheduling meetings and events on Google Calendar
            4. Summarizing email content
            5. General conversation about email and calendar management
            
            When user asks about emails, you can use commands like:
            - "check unread emails"
            - "show emails from [person]"
            - "what's my last email?"
            
            When user wants to send emails, guide them to use the email draft feature.
            When user wants to schedule meetings, guide them to use the meeting scheduler.
            
            Be friendly, helpful, and concise. If you can't do something, suggest an alternative."""
        }
    ]
    
    # Add conversation history
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_reply = response.choices[0].message.content
        
        # Save conversation to database
        save_conversation(user_email, "user", user_message)
        save_conversation(user_email, "assistant", ai_reply)
        
        return ai_reply
        
    except Exception as e:
        print(f"Groq API error: {e}")
        return "I encountered an error. Please try again or use specific commands."

# ===================== SMART COMMAND PARSER =====================
def parse_and_execute_command(user_email: str, creds, command: str, request: Request):
    """Parse command and execute appropriate action"""
    command_lower = command.lower()
    
    # Simple greetings
    greetings = ["hi", "hello", "hey", "hi there", "hello there", "greetings", "good morning", "good afternoon", "good evening"]
    if any(greet in command_lower for greet in greetings):
        return {"reply": "Hello! 👋 I'm InboxAI. I can help you with:\n• Checking emails\n• Writing email drafts\n• Scheduling meetings\n\nWhat would you like to do?"}
    
    if "help" in command_lower:
        return {"reply": "I can help you with:\n• 'show unread emails' - Check your inbox\n• 'write email to john@example.com about meeting' - Draft an email\n• 'schedule meeting with team tomorrow' - Create a calendar event\n• 'check emails from boss' - See messages from someone"}
    
    if "thank" in command_lower:
        return {"reply": "You're welcome! 😊 How else can I help you?"}
    
    # Check for email-related commands
    email_keywords = ["email", "inbox", "unread", "message", "mail", "gmail"]
    if any(word in command_lower for word in email_keywords):
        if "unread" in command_lower or "new" in command_lower or "inbox" in command_lower:
            return get_unread_emails_summary(creds)
        elif "last" in command_lower or "recent" in command_lower:
            return get_last_email_summary(creds)
        elif "from" in command_lower:
            return check_emails_from_sender(creds, command)
        elif "send" in command_lower or "write" in command_lower or "compose" in command_lower or "draft" in command_lower:
            return {
                "reply": "To write an email, please use the 'Draft' tab where you can specify recipient and content.",
                "action": "open_draft_tab"
            }
        else:
            return {"reply": "I can help with emails. Try:\n• 'Check unread emails'\n• 'Show last email'\n• 'Emails from John'\n• Or use the 'Draft' tab to write emails"}

    # Check for meeting commands
    meeting_keywords = ["meeting", "schedule", "calendar", "event", "appointment", "meet", "call"]
    if any(word in command_lower for word in meeting_keywords):
        if "create" in command_lower or "schedule" in command_lower or "set up" in command_lower or "book" in command_lower:
            return {
                "reply": "To schedule a meeting, please use the 'Meeting' tab where you can specify recipients, date, time, and agenda.",
                "action": "open_meeting_tab"
            }
        else:
            return {"reply": "I can help schedule meetings. Use the 'Meeting' tab or say 'schedule a meeting with team tomorrow at 3pm'"}

    # If no specific command matched, return None to use AI
    return None

# ===================== UPDATED COMMAND HANDLER =====================
@app.post("/command")
async def handle_command(payload: CommandPayload, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Get user credentials for Gmail/Calendar actions
        creds = None
        try:
            # Only get credentials if command might need them
            command_lower = payload.command.lower()
            email_meeting_keywords = ["email", "mail", "inbox", "meeting", "schedule", "calendar"]
            if any(word in command_lower for word in email_meeting_keywords):
                creds = get_credentials_for_user(user_email)
        except Exception as e:
            print(f"Warning: Could not get credentials: {e}")
            creds = None
        
        # First try to parse as specific command
        command_result = parse_and_execute_command(user_email, creds, payload.command, request)
        
        if command_result:
            # Save command to history
            save_conversation(user_email, "user", payload.command)
            if "reply" in command_result:
                save_conversation(user_email, "assistant", command_result["reply"])
            return command_result
        else:
            # Use AI for general conversation
            ai_response = await chat_with_ai(user_email, payload.command)
            return {"reply": ai_response}

    except Exception as e:
        traceback.print_exc()
        # Try AI fallback
        try:
            user_email = request.session.get("user")
            if user_email:
                ai_response = await chat_with_ai(user_email, f"I got an error: {str(e)}. User asked: {payload.command}")
                return {"reply": ai_response}
        except:
            pass
        
        return {"reply": "Sorry, I encountered an error. Please try again or use a specific command like 'check emails' or 'schedule meeting'."}

# ===================== ROUTERS =====================
app.include_router(auth_router)

# ===================== HEALTH =====================
@app.get("/")
async def health():
    return {"status": "InboxAI backend running 🚀"}

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

# ===================== LOGOUT =====================
@app.post("/auth/logout")
def logout(request: Request):
    response = JSONResponse({"success": True})
    
    # Clear session
    request.session.clear()
    
    # Clear cookies
    response.delete_cookie("session")
    response.delete_cookie("user")
    response.delete_cookie("inboxai_session")

    return response

# ===================== STARTUP =====================
@app.on_event("startup")
async def startup_event():
    print("\n=== Registered Routes ===")
    for route in app.routes:
        print(f"{route.methods} {route.path}")
    print("=======================\n")