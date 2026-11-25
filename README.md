# 📥 InboxAI

InboxAI is an AI-assisted Chrome extension for managing Gmail and Google Calendar from a single popup interface. It combines conversational commands, email summaries, AI-generated drafts, attachment text extraction, and Google Meet scheduling.

## 🚀 Features

- **AI inbox assistant** - Ask about unread emails, recent messages, or senders through a conversational interface.
- **Email summaries** - Summarize unread Gmail messages and the text of supported attachments.
- **Email drafting** - Generate three professional draft options, select one, review it, and send it through Gmail.
- **Calendar scheduling** - Create Google Calendar events with Google Meet links and attendee invitations.
- **Google OAuth** - Authenticate with PKCE and maintain per-user refresh tokens in SQLite.
- **Attachment support** - Extract text from PDF, Word, Excel, CSV, and image attachments.
- **Light and dark themes** - Persist the selected theme in the browser.

## 🗂️ Project Structure

```text
InboxAI/
├── backend/
│   ├── app.py                  # FastAPI application and API routes
│   ├── models.py               # Request models
│   ├── db.py                   # SQLite initialization and conversation storage
│   ├── client_secret.json      # Google OAuth web credentials (create locally)
│   ├── .env                    # Local backend configuration (create locally)
│   ├── ai_logic/
│   │   └── readers/            # PDF, Word, Excel, CSV, and OCR processors
│   └── services/
│       ├── auth.py             # Google OAuth flow and session endpoints
│       ├── gmail_client.py     # Gmail read/send operations
│       ├── email_drafter.py    # AI email draft generation
│       ├── calendar_service.py # Google Calendar event creation
│       ├── llm_client.py       # Groq function-calling integration
│       └── meeting_routes.py   # Meeting API routes
└── extension/
    ├── manifest.json           # Chrome extension manifest (MV3)
    ├── popup.html              # Extension interface
    ├── popup.js                # Authentication and UI behavior
    └── images/                 # Extension icons
```

## 🛠️ Technology Stack

- **Extension:** HTML, CSS, JavaScript, Chrome Extensions Manifest V3
- **Backend:** Python, FastAPI, Uvicorn
- **AI:** Groq Llama 3.3 70B
- **Google Services:** Gmail API, Google Calendar API, Google OAuth 2.0
- **Storage:** SQLite
- **Document Processing:** pdfplumber, python-docx, openpyxl, Pillow, Tesseract

## 📋 Prerequisites

- Python 3.10 or later
- Google Chrome or Chromium
- A Google Cloud project
- A Groq API key
- Tesseract OCR installed and available on `PATH` for image text extraction

## ☁️ Google Cloud Setup

1. Create or select a Google Cloud project.
2. Enable the **Gmail API** and **Google Calendar API**.
3. Configure the OAuth consent screen.
4. Add the following scopes:

   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/calendar`
5. Create an **OAuth 2.0 Client ID** for a web application.
6. Add this authorized redirect URI:

   ```text
   http://localhost:8000/auth/google/callback
   ```
7. Download the client credentials JSON and save it as:

   ```text
   InboxAI/backend/client_secret.json
   ```

For deployed environments, replace the localhost redirect URI and `BACKEND_BASE_URL` with the public HTTPS origin.

## 🖥️ Backend Setup

```powershell
cd "InboxAI\backend"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env`:

```dotenv
GROQ_API_KEY=your_groq_api_key
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
BACKEND_BASE_URL=http://localhost:8000
SESSION_SECRET=replace_with_a_long_random_value
```

Start the API:

```powershell
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Verify the backend at [http://localhost:8000](http://localhost:8000). FastAPI documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

## 🔌 Chrome Extension Setup

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Select **Load unpacked**.
4. Choose the `InboxAI/extension` folder.
5. Open the InboxAI extension from the Chrome toolbar.
6. Select **Login with Google** and grant the requested Gmail and Calendar permissions.

The popup currently uses `https://inboxai-backend-tb5j.onrender.com` by default. For local backend development, update `BACKEND_URL` in `extension/popup.js` to `http://localhost:8000` and add that origin to `host_permissions` in `manifest.json`.

## 🔍 API Overview

| Method   | Endpoint                  | Purpose                               |
| -------- | ------------------------- | ------------------------------------- |
| `GET`  | `/`                     | Health check                          |
| `GET`  | `/auth/google`          | Start Google OAuth                    |
| `GET`  | `/auth/google/callback` | Complete OAuth and create a session   |
| `GET`  | `/auth/status`          | Check current authentication state    |
| `POST` | `/auth/logout`          | Clear the session                     |
| `POST` | `/command`              | Process AI inbox commands             |
| `POST` | `/email/draft`          | Generate email drafts                 |
| `POST` | `/email/send`           | Send an email                         |
| `POST` | `/meeting/create`       | Create a Calendar event and Meet link |

## ✍ Example Commands

- “Show my unread emails.”
- “Summarize my most recent unread email.”
- “Do I have unread emails from GitHub?”
- “Schedule a meeting tomorrow at 4 PM with john@example.com.”
- “Create a call titled Product Review for 45 minutes.”

## 🔐 Data and Security Notes

- OAuth refresh tokens and conversation history are stored in `backend/users.db`.
- Keep `.env`, `client_secret.json`, database files, and refresh tokens out of source control.
- Use a strong `SESSION_SECRET` in deployed environments.
- The session middleware currently permits HTTP for local development. Enable HTTPS and secure-cookie settings for production.
- Gmail content and OAuth data are sent to the configured Groq API for AI processing; use Groq only with appropriate authorization and privacy controls.

## 👩‍💻 Development Notes

- Run the backend from `InboxAI/backend` so relative paths for `client_secret.json`, `users.db`, and temporary attachments resolve correctly.
- The backend initializes its SQLite tables automatically at startup.
- Attachment files are temporarily stored under `backend/temp_attachments`.
- The meeting and draft interfaces use the backend session cookie, so the extension must run against an origin allowed by the backend CORS configuration.
