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
    return {"status": "InboxAI backend running", "docs": "/docs"}


# ============================ HELPERS ============================
def get_unread_emails_summary():
    try:
        emails = get_unread_emails()
        summaries = []

        for idx, email in enumerate(emails, start=1):
            category = get_email_category(
                body=email["body"],
                sender=email["from"],
                subject=email.get("subject", "")
            )

            summary = summarize_email_logic(
                body=email["body"],
                sender=email["from"],
                subject=email.get("subject", ""),
                attachments=email.get("attachment_text", "")
            )

            summaries.append({
                "summary_number": idx,
                "sender": email["from"],
                "subject": email.get("subject", "No Subject"),
                "category": category,
                "summary": summary,
                "has_attachments": bool(email.get("attachment_text"))
            })

        return {
            "email_count": len(summaries),
            "summaries": summaries
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def get_last_email_summary():
    try:
        emails = get_unread_emails(max_results=1)

        if not emails:
            return {"response": "No unread emails found."}

        email = emails[0]

        category = get_email_category(
            body=email["body"],
            sender=email["from"],
            subject=email.get("subject", "")
        )

        summary = summarize_email_logic(
            body=email["body"],
            sender=email["from"],
            subject=email.get("subject", ""),
            attachments=email.get("attachment_text", "")
        )

        return {
            "sender": email["from"],
            "category": category,
            "summary": summary,
            "has_attachments": bool(email.get("attachment_text"))
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def get_unread_email_categories():
    emails = get_unread_emails()
    results = []

    for email in emails:
        category = get_email_category(
            body=email["body"],
            sender=email["from"],
            subject=email.get("subject", "")
        )

        results.append({
            "sender": email["from"],
            "subject": email.get("subject", "No Subject"),
            "category": category
        })

    return {
        "email_count": len(results),
        "categories": results
    }


def check_emails_from_sender(sender_query: str):
    emails = get_unread_emails()

    matched = [
        email for email in emails
        if sender_query.lower() in email["from"].lower()
    ]

    return {
        "sender_query": sender_query,
        "count": len(matched),
        "emails": [
            {
                "from": email["from"],
                "subject": email.get("subject", "No Subject")
            }
            for email in matched
        ]
    }


# ============================ COMMAND HANDLER ============================
@app.post("/command")
def handle_command(payload: CommandPayload):
    try:
        command = payload.command.lower().strip()

        # 🔍 RULE-BASED sender lookup (NOT LLM)
        if "email from" in command or "emails from" in command:
            command.split("from")[-1]
            sender_query = re.sub(r"[^\w\s@.]", "", sender_query).strip()

            if not sender_query:
                return {
    "type": "conversation",
    "message": "Whose emails should I check?"
}


            result = check_emails_from_sender(sender_query)

            if result["count"] == 0:
                return {
                    "response": f"You have no unread emails from {sender_query}."
                }

            return {
    "type": "conversation",
    "message": (
        f"You have {result['count']} unread emails from {sender_query}. "
        "Do you want me to summarize them?"
    ),
    "data": result
}


        # 🧠 LLM-controlled SAFE commands only
        function_map = {
            "get_unread_emails_summary": get_unread_emails_summary,
            "get_last_email_summary": get_last_email_summary,
            "get_unread_email_categories": get_unread_email_categories
        }

        return intelligent_command_handler(payload.command, function_map)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================ LEGACY ============================
@app.post("/summarize/unread")
def summarize_unread_emails():
    return get_unread_emails_summary()
