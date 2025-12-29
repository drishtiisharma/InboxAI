import re
from services.llm_client import call_llm

def clean_email(text: str) -> str:
    text = re.sub(r"\ufeff|\u2007", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(unsubscribe|click here|tap to apply)", "", text, flags=re.I)
    return text.strip()


def summarize_email(body: str, sender: str) -> str:
    body = clean_email(body)

    prompt = f"""
Explain the email clearly in 2–3 sentences.

- Say what the email is about
- Why it was sent
- Who sent it
- What the user should do (if anything)

Sender: {sender}

Email:
{body[:1200]}
"""

    return call_llm(prompt)
