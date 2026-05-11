# FIX: import path changed from "services.llm_client" to just "llm_client"
# because this file lives inside the services/ folder itself.
# "services.llm_client" only works if called from the project root with a package
# structure — using a relative-style import keeps it correct regardless.
try:
    from llm_client import call_llm               # when run from inside services/
except ImportError:
    from services.llm_client import call_llm      # when imported from project root

MAX_CATEGORY_BODY_CHARS = 500


def get_email_category(body: str, sender: str, subject: str = "") -> str:
    # Trim body aggressively — categorisation does NOT need the full text
    if body and len(body) > MAX_CATEGORY_BODY_CHARS:
        body = body[:MAX_CATEGORY_BODY_CHARS] + "..."

    prompt = (
        "Categorize the email into ONE category:\n"
        "Primary, Promotions, Social, Spam, Updates\n\n"
        f"Sender: {sender}\n"
        f"Subject: {subject}\n"
        f"Body: {body}\n\n"
        "Respond with ONLY the category name."
    )

    category = call_llm(prompt).strip()

    allowed = {"Primary", "Promotions", "Social", "Spam", "Updates"}
    return category if category in allowed else "Primary"