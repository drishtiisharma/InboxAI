from googleapiclient.discovery import build
from datetime import datetime, timedelta
import uuid


def create_google_meeting(creds, meeting_data):
    """
    Creates a Google Calendar event with a Google Meet link
    """

    service = build("calendar", "v3", credentials=creds)

    # Parse start & end time
    start_dt = datetime.fromisoformat(meeting_data["start"])
    end_dt = start_dt + timedelta(minutes=meeting_data["duration"])

    event = {
        "summary": meeting_data["title"],
        "description": meeting_data.get("agenda", ""),
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "attendees": [
            {"email": email} for email in meeting_data.get("recipients", [])
        ],
        "conferenceData": {
            "createRequest": {
                # MUST be unique every time
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                }
            }
        }
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1,
        sendUpdates="all"
    ).execute()

    # Safely extract Meet link
    meet_link = None
    conference_data = created_event.get("conferenceData", {})
    entry_points = conference_data.get("entryPoints", [])

    for entry in entry_points:
        if entry.get("entryPointType") == "video":
            meet_link = entry.get("uri")
            break

    return {
        "eventId": created_event.get("id"),
        "meetLink": meet_link,
        "htmlLink": created_event.get("htmlLink"),
        "status": created_event.get("status")
    }
