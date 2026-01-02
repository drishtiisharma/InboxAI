from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from services.gmail_client import get_unread_emails
from ai_logic.email import summarize_email_logic
from services.llm_client import intelligent_command_handler

load_dotenv()

app = FastAPI(title="InboxAI Backend")

# ============================ CORS ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================ MODELS ============================
class CommandPayload(BaseModel):
    command: str


# ============================ ROOT ============================
@app.get("/")
def root():
    return {"status": "InboxAI backend running", "docs": "/docs"}


# ============================ HELPER FUNCTIONS ============================
def get_unread_emails_summary():
    """Get all unread emails with summaries"""
    emails = get_unread_emails()

    if not emails:
        return {"email_count": 0, "summaries": []}

    summaries = []
    for idx, email in enumerate(emails, start=1):
        summary = summarize_email_logic(
            body=email["body"],
            sender=email["sender"],
        )
        summaries.append({
            "summary_number": idx,
            "sender": email["sender"],
            "summary": summary
        })

    return {
        "email_count": len(summaries),
        "summaries": summaries
    }


def get_last_email_summary():
    """Get the last unread email with summary"""
    emails = get_unread_emails(max_results=1)

    if not emails:
        return {"error": "No unread emails found"}

    email = emails[0]
    summary = summarize_email_logic(
        body=email["body"],
        sender=email["sender"],
    )

    return {
        "sender": email["sender"],
        "summary": summary
    }


# ============================ COMMAND HANDLER (NEW) ============================
@app.post("/command")
def handle_command(payload: CommandPayload):
    """
    Intelligent command handler using LLM function calling
    """
    
    # Map function names to actual Python functions
    function_map = {
        "get_unread_emails_summary": get_unread_emails_summary,
        "get_last_email_summary": get_last_email_summary
    }
    
    # Use intelligent handler
    result = intelligent_command_handler(payload.command, function_map)
    
    return result


# ============================ OLD ENDPOINTS (Keep for backward compatibility) ============================
@app.post("/summarize/unread")
def summarize_unread_emails():
    return get_unread_emails_summary()