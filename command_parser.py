import re

# ============================ CLEAN TEXT ============================
def clean_for_speech(text):
    text = re.sub(r"[*•\-+]", " ", text)
    text = re.sub(r"[()\[\]{}<>]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ============================ PARSE COMMAND ============================
def parse_command(command: str) -> dict:
    command = normalize_command(command)

    email_keywords = ["email", "emails", "mail", "inbox"]
    summarize_keywords = ["summarize", "summarise", "summary", "read", "check", "tell"]

    if any(w in command for w in email_keywords) and \
       any(w in command for w in summarize_keywords):
        return {
            "intent": "SUMMARIZE_EMAILS",
            "source": "gmail"
        }

    if any(w in command for w in ["exit", "stop", "quit", "close"]):
        return {
            "intent": "EXIT"
        }

    return {
        "intent": "UNKNOWN",
        "raw": command
    }

# ============================ NORMALIZE COMMAND =============================
def normalize_command(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ============================ INTENT VALIDATION ============================
VALID_INTENTS = {
    "SUMMARIZE_EMAILS",
    "EXIT",
    "UNKNOWN"
}

def is_valid_intent(intent: str) -> bool:
    return intent in VALID_INTENTS
