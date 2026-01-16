# models.py
from pydantic import BaseModel
from typing import List, Optional

class CommandPayload(BaseModel):
    command: str
    history: Optional[List[dict]] = []

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str

class DraftRequest(BaseModel):
    intent: str
    receiver: str
    tone: str = "professional"
    context: str = ""

class MeetingRequest(BaseModel):
    title: str = "Meeting via InboxAI"
    recipients: List[str]
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    duration: int = 30  # minutes
    agenda: str = ""