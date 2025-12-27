# Supposed File Structure:

```text
InboxAI/
│
├── backend/                 # Python lives here (Render)
│   │
│   ├── app.py               # Server entry point (Flask / FastAPI)
│   │
│   ├── ai_logic/
│   │   ├── summarizer.py    # Core summary logic
│   │   ├── email.py         # Email summarization
│   │   ├── documents.py    # Document summarization
│   │   └── __init__.py
│   │
│   ├── requirements.txt    # Dependencies for Render
│   ├── .env                # API keys (local only, gitignored)
│   └── README.md
│
├── extension/               # Browser Extension (user installs this)
│   │
│   ├── manifest.json       # Permissions + entry points
│   ├── popup.html          # Extension UI
│   ├── popup.js            # Mic + backend API calls
│   ├── background.js       # Long-running tasks (optional)
│   ├── icons/
│   │   ├── icon16.png
│   │   ├── icon48.png
│   │   └── icon128.png
│   └── README.md
│
├── dev-tools/               # Dev-only tools (never shipped)
│   │
│   ├── run_backend.bat     # Start backend locally
│   └── set_env.bat         # Load env variables
│
└── README.md                # Project overview
```
