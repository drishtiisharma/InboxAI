from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import traceback
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
        print("\n=== Starting get_unread_emails_summary ===")
        emails = get_unread_emails()
        print(f"Retrieved {len(emails)} emails")

        summaries = []

        for idx, email in enumerate(emails, start=1):
            print(f"\nProcessing email {idx}")
            print(f"Sender: {email['from']}")
            print(f"Subject: {email.get('subject', 'No Subject')}")
            print(f"Body length: {len(email['body'])} chars")
            print(f"Has attachments: {bool(email.get('attachment_text'))}")

            has_attachments = bool(email.get("attachment_text"))

            category = get_email_category(
                body=email["body"],
                sender=email["from"],
                subject=email.get("subject", "")
            )
            
            # Provide better context to the AI
            summary = summarize_email_logic(
                body=email["body"],
                sender=email["from"],
                subject=email.get("subject", ""),
                attachments=email.get("attachment_text", "")  # This is already a string - correct!
            )

            summaries.append({
    "summary_number": idx,
    "sender": email["from"],
    "subject": email.get("subject", "No Subject"),
    "category": category,
    "summary": summary,
    "has_attachments": has_attachments
})


        return {
            "email_count": len(summaries),
            "summaries": summaries
        }

    except Exception as e:
        print("\n!!! ERROR in get_unread_emails_summary !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def get_last_email_summary():
    try:
        emails = get_unread_emails(max_results=1)

        if not emails:
            return {"error": "No unread emails found"}

        email = emails[0]

        category = get_email_category(
    body=email["body"],
    sender=email["from"],
    subject=email.get("subject", "")
)


        summary = summarize_email_logic(
            body=email["body"],
            sender=email["from"],
            attachments=email.get("attachment_text", "")
        )

        return {
    "sender": email["from"],
    "category": category,
    "summary": summary,
    "has_attachments": bool(email.get("attachment_text"))
}


    except Exception as e:
        print("\n!!! ERROR in get_last_email_summary !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================ COMMAND HANDLER ============================
@app.post("/command")
def handle_command(payload: CommandPayload):
    try:
        function_map = {
            "get_unread_emails_summary": get_unread_emails_summary,
            "get_last_email_summary": get_last_email_summary
        }

        return intelligent_command_handler(payload.command, function_map)

    except Exception as e:
        print("\n!!! ERROR in handle_command !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================ LEGACY ============================
@app.post("/summarize/unread")
def summarize_unread_emails():
    return get_unread_emails_summary()
