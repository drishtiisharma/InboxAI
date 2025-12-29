from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel

from ai_logic.email import summarize_email_logic
from services.gmail_client import get_last_email


app = FastAPI(title="InboxAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================ MODELS ============================
class EmailPayload(BaseModel):
    body: str
    sender: str

# ============================ HEALTH CHECK ============================
@app.get("/")
def health_check():
    return {"status": "InboxAI backend running"}

# ============================ MANUAL EMAIL SUMMARY ============================
@app.post("/summarize/email")
def summarize_email_endpoint(payload: EmailPayload):
    summary = summarize_email_logic(
        body=payload.body,
        sender=payload.sender
    )
    return {"summary": summary}

# ============================ LAST GMAIL SUMMARY ============================
@app.post("/summarize/last-email")
def summarize_last_email():
    email = get_last_email()

    if not email or not email["body"]:
        return {"summary": "No readable email found."}

    summary = summarize_email_logic(
        body=email["body"],
        sender=email["sender"]
    )

    return {"summary": summary}