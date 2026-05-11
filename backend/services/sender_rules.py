from typing import Optional  # FIX: str | None requires Python 3.10+; use Optional for 3.9 compat

SENDER_CATEGORY_MAP = {
    "linkedin.com": "Promotions",
    "github.com": "Work",
    "google.com": "Updates",
    "bank": "Finance",
    "no-reply": "Updates",
}


def categorize_by_sender(sender: str) -> Optional[str]:
    sender = sender.lower()

    for key, category in SENDER_CATEGORY_MAP.items():
        if key in sender:
            return category

    return None