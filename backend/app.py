from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from dotenv import load_dotenv
import traceback
import re

from services.email_categorizer import get_email_category
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
    history: Optional[List[Dict[str, str]]] = None

# ============================ ROOT ============================
@app.get("/")
def root():
    return {
        "reply": "InboxAI backend running",
        "data": {"docs": "/docs"}
    }

# ============================ HELPERS ============================
def normalize(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


def check_emails_from_sender(sender_query: str):
    emails = get_unread_emails() or []
    normalized_query = normalize(sender_query)

    matched = [
        email for email in emails
        if normalized_query in normalize(email.get("from", ""))
    ]

    if not matched:
        return {
            "reply": f"You have no unread emails from {sender_query}.",
            "data": None
        }

    return {
        "reply": f"You have {len(matched)} unread email{'s' if len(matched) > 1 else ''} from {sender_query}.",
        "data": {
            "sender_query": sender_query,
            "count": len(matched),
            "emails": [
                {
                    "from": email.get("from"),
                    "subject": email.get("subject", "No Subject")
                }
                for email in matched
            ]
        }
    }


def get_unread_emails_summary():
    emails = get_unread_emails() or []

    if not emails:
        return {
            "reply": "You have no unread emails.",
            "data": None
        }

    summaries = []
    spoken_parts = []

    for idx, email in enumerate(emails, start=1):
        sender = email.get("from", "Unknown sender")
        subject = email.get("subject", "No Subject")

        summary = summarize_email_logic(
            body=email.get("body", ""),
            sender=sender,
            subject=subject,
            attachments=email.get("attachment_text", "")
        )

        summaries.append({
            "sender": sender,
            "subject": subject,
            "summary": summary
        })

        spoken_parts.append(
            f"Email {idx} is from {sender}. {summary}"
        )

    spoken_reply = (
        f"You have {len(summaries)} unread emails.\n\n" +
        "\n\n".join(spoken_parts)
    )

    return {
        "reply": spoken_reply,
        "data": {
            "email_count": len(summaries),
            "summaries": summaries
        }
    }


def get_last_email_summary():
    emails = get_unread_emails(max_results=1) or []

    if not emails:
        return {
            "reply": "You have no unread emails.",
            "data": None
        }

    email = emails[0]

    return {
        "reply": summarize_email_logic(
            body=email.get("body", ""),
            sender=email.get("from", "Unknown sender"),
            subject=email.get("subject", ""),
            attachments=email.get("attachment_text", "")
        ),
        "data": {
            "sender": email.get("from"),
            "category": get_email_category(
                email.get("body", ""),
                email.get("from", ""),
                email.get("subject", "")
            ),
            "has_attachments": bool(email.get("attachment_text"))
        }
    }


def get_unread_email_categories():
    emails = get_unread_emails() or []

    return {
        "reply": f"I found {len(emails)} unread emails with categories.",
        "data": {
            "email_count": len(emails),
            "categories": [
                {
                    "sender": email.get("from", ""),
                    "subject": email.get("subject", "No Subject"),
                    "category": get_email_category(
                        email.get("body", ""),
                        email.get("from", ""),
                        email.get("subject", "")
                    )
                }
                for email in emails
            ]
        }
    }

# ============================ COMMAND ROUTER ============================
@app.post("/command")
def handle_command(payload: CommandPayload):
    try:
        command = payload.command.strip().lower()
        history = payload.history or []

        # ⚡ FAST RULE-BASED SHORTCUTS
        if "email from" in command or "emails from" in command:
            sender_query = command.split("from")[-1]
            sender_query = re.sub(r"[^\w\s@.]", "", sender_query).strip()

            if not sender_query:
                return {"reply": "Whose emails should I check?", "data": None}

            return check_emails_from_sender(sender_query)

        if command in ["summarize", "summarize them", "summarise them"]:
            return get_unread_emails_summary()

        # 🧠 LLM FUNCTION MAP
        function_map = {
            "get_unread_emails_summary": get_unread_emails_summary,
            "get_last_email_summary": get_last_email_summary,
            "get_unread_email_categories": get_unread_email_categories,
            "check_emails_from_sender": check_emails_from_sender,
        }

        # ✅ CORRECT CALL (THIS WAS THE BUG)
        result = intelligent_command_handler(
            payload.command,   # ← positional, NOT keyword
            function_map,
            history
        )

        if isinstance(result, dict):
            return {
                "reply": result.get("reply", ""),
                "data": result.get("data")
            }

        return {"reply": str(result), "data": None}

    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Command processing failed")

# ============================ DIRECT ROUTES ============================
@app.post("/summarize/unread")
def summarize_unread_emails():
    try:
        return get_unread_emails_summary()
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to summarize unread emails"
        )
