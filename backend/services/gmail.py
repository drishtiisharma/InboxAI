import re
from services.llm_client import summarize_text

# ============================ CLEANING ============================

def clean_email_for_llm(text: str) -> str:
    text = re.sub(r"\ufeff|\u2007", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(tap to apply|click here|unsubscribe)", "", text, flags=re.I)
    return text.strip()


# ============================ EMAIL SUMMARY ============================

def summarize_email(body: str, sender: str) -> str:
    clean_body = clean_email_for_llm(body)

    prompt = f"""
Explain the email clearly in natural language in 2–3 sentences.

Rules:
- Do NOT mention formatting, bullet points, or email structure
- Do NOT quote the email
- No greetings or opinions

Instead:
- Say what the email is about
- Why it was sent
- Who sent it
- What the user is expected to do (if anything)

Sender: {sender}

Email:
{clean_body[:1200]}
"""

    return summarize_text(prompt)
