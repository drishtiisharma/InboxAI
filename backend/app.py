from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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


# ============================ ROOT ============================
@app.get("/")
def root():
    return {
        "reply": "InboxAI backend running",
        "data": {"docs": "/docs"}
    }


# ============================ HELPERS ============================
def get_unread_emails_summary():
    emails = get_unread_emails() or []

    if not emails:
        return {
            "reply": "You have no unread emails.",
            "data": {"email_count": 0, "summaries": []}
        }

    summaries = []

    for idx, email in enumerate(emails, start=1):
        body = email.get("body", "")
        sender = email.get("from", "Unknown sender")
        subject = email.get("subject", "")

        category = get_email_category(
            body=body,
            sender=sender,
            subject=subject
        )

        summary = summarize_email_logic(
            body=body,
            sender=sender,
            subject=subject,
            attachments=email.get("attachment_text", "")
        )

        summaries.append({
            "summary_number": idx,
            "sender": sender,
            "subject": subject or "No Subject",
            "category": category,
            "summary": summary,
            "has_attachments": bool(email.get("attachment_text"))
        })

    return {
        "reply": f"You have {len(summaries)} unread emails.",
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

    summary = summarize_email_logic(
        body=email.get("body", ""),
        sender=email.get("from", "Unknown sender"),
        subject=email.get("subject", ""),
        attachments=email.get("attachment_text", "")
    )

    return {
        "reply": summary,
        "data": {
            "sender": email.get("from"),
            "category": get_email_category(
                body=email.get("body", ""),
                sender=email.get("from", ""),
                subject=email.get("subject", "")
            ),
            "has_attachments": bool(email.get("attachment_text"))
        }
    }


def get_unread_email_categories():
    emails = get_unread_emails() or []

    results = [
        {
            "sender": email.get("from", ""),
            "subject": email.get("subject", "No Subject"),
            "category": get_email_category(
                body=email.get("body", ""),
                sender=email.get("from", ""),
                subject=email.get("subject", "")
            )
        }
        for email in emails
    ]

    return {
        "reply": f"I found {len(results)} unread emails with categories.",
        "data": {
            "email_count": len(results),
            "categories": results
        }
    }


def normalize(text: str) -> str:
    """
    Normalize text for loose matching:
    - lowercase
    - remove all non-alphabet characters
    """
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


# ============================ COMMAND HANDLER ============================
@app.post("/command")
def handle_command(payload: CommandPayload):
    try:
        command = payload.command.strip().lower()

        # 🔍 RULE-BASED sender lookup
        if "email from" in command or "emails from" in command:
            sender_query = command.split("from")[-1]
            sender_query = re.sub(r"[^\w\s@.]", "", sender_query).strip()

            if not sender_query:
                return {
                    "reply": "Whose emails should I check?",
                    "data": None
                }

            return check_emails_from_sender(sender_query)

        # 🧠 LLM SAFE COMMANDS
        function_map = {
            "get_unread_emails_summary": get_unread_emails_summary,
            "get_last_email_summary": get_last_email_summary,
            "get_unread_email_categories": get_unread_email_categories
        }

        result = intelligent_command_handler(payload.command, function_map)

        # ✅ NORMALIZATION (THIS WAS MISSING)
        if isinstance(result, dict):
            return {
                "reply": result.get("reply") or result.get("message") or "",
                "data": result.get("data")
            }

        return {
            "reply": str(result),
            "data": None
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Command processing failed"
        )


@app.post("/summarize/unread")
def summarize_unread_emails():
    try:
        return get_unread_emails_summary()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to summarize unread emails"
        )
