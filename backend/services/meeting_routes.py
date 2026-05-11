from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional

from services.gmail_client import get_credentials_for_user 
from services.calendar_service import create_google_meeting

meeting_router = APIRouter(prefix="/meeting", tags=["Meeting"])

class CreateMeetingRequest(BaseModel):
    title: str
    date: str
    time: str
    duration: int
    recipients: List[str]
    agenda: Optional[str] = ""

@meeting_router.post("/create")
def create_meeting(req: CreateMeetingRequest, request: Request):
    try:
        user_email = request.session.get("user")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")

        creds = get_credentials_for_user(user_email)  

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
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")

@meeting_router.get("/ping")
def ping():
    return {"ok": True}