SENDER_CATEGORY_MAP = {
    "linkedin.com": "Promotions",
    "github.com": "Work",
    "google.com": "Updates",
    "bank": "Finance",
    "no-reply": "Updates",
}

def categorize_by_sender(sender: str) -> str | None:
    sender = sender.lower()

    for key, category in SENDER_CATEGORY_MAP.items():
        if key in sender:
            return category

    return None
