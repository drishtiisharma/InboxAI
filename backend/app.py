from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from services.gmail_client import get_unread_emails
from ai_logic.email import summarize_email_logic

load_dotenv()

app = FastAPI(title="InboxAI Backend")

# ============================ CORS ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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


# ============================ UNREAD SUMMARY ============================
@app.post("/summarize/unread")
def summarize_unread_emails():
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


# ============================ COMMAND HANDLER ============================
@app.post("/command")
def handle_command(payload: CommandPayload):
    command = payload.command.lower().strip()

    # Normalize common variations
    command = command.replace("emails", "email")
    command = command.replace("mails", "mail")

    # -------- UNREAD EMAILS --------
    if "summarize" in command and "unread" in command:
        return summarize_unread_emails()

    # -------- LAST EMAIL --------
    if "summarize" in command and "last" in command:
        emails = get_unread_emails(max_results=1)

        if not emails:
            return {"summary": "No unread emails found."}

        email = emails[0]
        summary = summarize_email_logic(
            body=email["body"],
            sender=email["sender"],
        )

        return {
            "sender": email["sender"],
            "summary": summary
        }

    # -------- FALLBACK --------
    return {
        "error": "Command not understood",
        "received": payload.command,
        "hint": "Try: 'summarize my unread emails' or 'summarize my last email'"
    }
