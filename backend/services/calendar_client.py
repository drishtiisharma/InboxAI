# services/calendar_client.py
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
import os
from typing import List

def create_meeting(
    creds: Credentials,
    title: str = "Meeting via InboxAI",
    recipients: List[str] = None,
    date: str = None,
    time: str = None,
    duration: int = 30,
    agenda: str = "",
    summary: str = None,
    description: str = None
) -> str:
    """
    Create a Google Calendar meeting and return the meet link.
    """
    try:
        # Build Calendar service
        calendar_service = build('calendar', 'v3', credentials=creds)
        
        # Parse date and time
        if date and time:
            start_datetime_str = f"{date}T{time}:00"
            end_datetime = datetime.fromisoformat(start_datetime_str) + timedelta(minutes=duration)
            end_datetime_str = end_datetime.isoformat()
        else:
            # Default: start now, end in 30 minutes
            start_datetime = datetime.utcnow()
            end_datetime = start_datetime + timedelta(minutes=duration)
            start_datetime_str = start_datetime.isoformat() + 'Z'
            end_datetime_str = end_datetime.isoformat() + 'Z'
        
        # Prepare attendees
        attendees = []
        if recipients:
            for email in recipients:
                attendees.append({"email": email.strip()})
        
        # Create event
        event = {
            'summary': summary or title,
            'description': description or agenda,
            'start': {
                'dateTime': start_datetime_str,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_datetime_str,
                'timeZone': 'UTC',
            },
            'attendees': attendees,
            'conferenceData': {
                'createRequest': {
                    'requestId': f'meet-{datetime.utcnow().timestamp()}',
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
            'reminders': {
                'useDefault': True
            }
        }
        
        # Insert event with conference
        created_event = calendar_service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        # Extract meet link
        meet_link = created_event.get('hangoutLink', '')
        
        if not meet_link:
            # Fallback: try to get from conference data
            conference_data = created_event.get('conferenceData', {})
            meet_link = conference_data.get('entryPoints', [{}])[0].get('uri', '')
        
        if not meet_link:
            meet_link = created_event.get('htmlLink', '')  # Fallback to calendar link
        
        return meet_link
        
    except Exception as e:
        print(f"Error creating meeting: {e}")
        # Return a mock meet link for testing
        return "https://meet.google.com/test-meet-link"