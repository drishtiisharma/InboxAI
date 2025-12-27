# app.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from ai_logic.email import summarize_email

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

# ============================ CHECKING ============================
@app.get("/")
def health_check():
    return {"status": "InboxAI backend running"}

# ============================ EMAIL SUMMARY ============================

@app.post("/summarize/email")
def summarize_email_endpoint(payload: EmailPayload):
    summary = summarize_email(
        body=payload.body,
        sender=payload.sender
    )

    return {
        "summary": summary
    }