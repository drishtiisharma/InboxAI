from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.gmail_client import get_google_credentials
from services.calendar_service import create_google_meeting

# ============================ ROUTER ============================
meeting_router = APIRouter(prefix="/meeting", tags=["Meeting"])

# ============================ MODELS ============================

class CreateMeetingRequest(BaseModel):
    title: str
    date: str              # YYYY-MM-DD
    time: str              # HH:MM
    duration: int          # minutes
    recipients: List[str]
    agenda: Optional[str] = ""


# ============================ ROUTES ============================

@meeting_router.post("/create")
def create_meeting(req: CreateMeetingRequest):
    try:
        creds = get_google_credentials()

        meeting_data = {
            "title": req.title,
            "agenda": req.agenda,
            "start": f"{req.date}T{req.time}",
            "duration": req.duration,
            "recipients": req.recipients
        }

        result = create_google_meeting(creds, meeting_data)

        return {
            "reply": "Meeting created successfully.",
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create meeting: {str(e)}"
        )
