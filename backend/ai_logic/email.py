import re
from ai_logic.llm_client import call_llm


def clean_sender(sender: str) -> str:
    return sender.split("<")[0].strip()


def clean_body(text: str) -> str:
    text = re.sub(r"http\S+", "", text)     # remove links
    text = re.sub(r"\S+@\S+", "", text)     # remove emails
    text = re.sub(r"\s+", " ", text)        # normalize spaces
    return text.strip()


def clean_summary(text: str) -> str:
    bad_starts = [
        "here's a summary",
        "here is a summary",
        "here's the summary",
        "here is the summary",
    ]

    text = text.strip()
    lower = text.lower()

    for phrase in bad_starts:
        if lower.startswith(phrase):
            return text.split("\n", 1)[-1].strip()

    return text


def summarize_email_logic(body: str, sender: str) -> str:
    sender_name = clean_sender(sender)
    clean_text = clean_body(body)

    prompt = f"""
Summarize the following email in 2–3 sentences.

Rules:
- Do NOT include links
- Do NOT include email addresses
- Do NOT mention promotions or footers
- Do NOT say "here is the summary"
- Just explain the gist clearly

Email:
{clean_text}
"""

    summary = call_llm(prompt)
    summary = clean_summary(summary)

    return f"Summary of email from {sender_name}:\n{summary}"
