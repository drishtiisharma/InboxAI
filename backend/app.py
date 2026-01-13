# app.py - Fix middleware
import traceback
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
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

# ===================== CONVERSATION MEMORY =====================
def get_user_conversation_history(email: str, limit: int = 10):
    """Get conversation history for a user from database"""
    return get_conversation_history(email, limit)

def save_user_message(email: str, role: str, content: str):
    """Save a message to user's conversation history"""
    save_conversation(email, role, content)

# ===================== AI CHAT FUNCTION =====================
async def chat_with_ai(user_email: str, user_message: str, context: dict = None):
    """Chat with Groq AI with conversation memory"""
    if not groq_client:
        return "AI service is currently unavailable. Please try basic commands."
    
    # Get conversation history
    history = get_user_conversation_history(user_email, limit=10)
    
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
            model="llama3-70b-8192",  # or "mixtral-8x7b-32768" or "gemma2-9b-it"
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_reply = response.choices[0].message.content
        
        # Save conversation to database
        save_user_message(user_email, "user", user_message)
        save_user_message(user_email, "assistant", ai_reply)
        
        return ai_reply
        
    except Exception as e:
        print(f"Groq API error: {e}")
        return "I encountered an error. Please try again or use specific commands like 'check emails' or 'schedule meeting'."

# ===================== SMART COMMAND PARSER =====================
def parse_and_execute_command(user_email: str, creds, command: str, request: Request):
    """Parse command and execute appropriate action"""
    command_lower = command.lower()
    
    # Check for email-related commands
    if any(word in command_lower for word in ["email", "inbox", "unread", "message", "mail"]):
        if "unread" in command_lower:
            return get_unread_emails_summary(creds)
        elif "last" in command_lower:
            return get_last_email_summary(creds)
        elif "from" in command_lower:
            return check_emails_from_sender(creds, command)
        else:
            return {"reply": "I can help with emails. Try:\n• 'Check unread emails'\n• 'Show last email'\n• 'Emails from John'"}

    # Check for meeting commands
    elif any(word in command_lower for word in ["meeting", "schedule", "calendar", "event", "appointment"]):
        if "create" in command_lower or "schedule" in command_lower or "set up" in command_lower:
            # Extract meeting details from command
            return {
                "reply": "To schedule a meeting, please use the 'Meeting' tab in the interface where you can specify recipients, date, time, and agenda.",
                "action": "open_meeting_tab"
            }
        else:
            return {"reply": "I can help schedule meetings. Use the 'Meeting' tab or say 'schedule a meeting with team tomorrow at 3pm'"}

    # Check for email drafting
    elif any(word in command_lower for word in ["write", "compose", "draft", "send email", "email to"]):
        return {
            "reply": "To write an email, please use the 'Draft' tab where you can specify recipient, subject, and content.",
            "action": "open_draft_tab"
        }

    # If no specific command matched, use AI chat
    else:
        return None

# ===================== UPDATED COMMAND HANDLER =====================
@app.post("/command")
async def handle_command(payload: CommandPayload, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Get user credentials for Gmail/Calendar actions
        creds = get_credentials_for_user(user_email) if "email" in payload.command.lower() or "meeting" in payload.command.lower() else None
        
        # First try to parse as specific command
        command_result = parse_and_execute_command(user_email, creds, payload.command, request)
        
        if command_result:
            # Save command to history
            save_user_message(user_email, "user", payload.command)
            save_user_message(user_email, "assistant", command_result.get("reply", ""))
            return command_result
        else:
            # Use AI for general conversation
            ai_response = await chat_with_ai(user_email, payload.command)
            return {"reply": ai_response}

    except Exception as e:
        traceback.print_exc()
        # Fallback to AI
        try:
            user_email = request.session.get("user")
            if user_email:
                ai_response = await chat_with_ai(user_email, f"I got an error but want to respond to: {payload.command}")
                return {"reply": ai_response}
        except:
            pass
        
        raise HTTPException(status_code=500, detail="Command processing failed")

# ===================== OTHER ROUTES (keep as is) =====================
@app.get("/")
async def health():
    return {"status": "InboxAI backend running 🚀"}

@app.post("/email/draft")
async def draft_email(payload: DraftRequest, request: Request):
    # ... keep existing code ...

@app.post("/meeting/create")
async def create_meeting_route(payload: MeetingRequest, request: Request):
    # ... keep existing code ...

# ... keep all your existing helper functions ...

@app.on_event("startup")
async def startup_event():
    print("\n=== Registered Routes ===")
    for route in app.routes:
        print(f"{route.methods} {route.path}")
    print("=======================\n")