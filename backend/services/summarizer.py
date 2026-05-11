import re

# FIX: original used llm.invoke(prompt) — LangChain style — but this project uses
# Groq directly via call_llm. Replaced the signature and all invocation calls.
try:
    from llm_client import call_llm
except ImportError:
    from services.llm_client import call_llm


def clean_sender(sender: str) -> str:
    # "Team Unstop <noreply@x.com>" → "Team Unstop"
    return sender.split("<")[0].strip()


def clean_body(text: str) -> str:
    text = re.sub(r"http\S+", "", text)           # remove links
    text = re.sub(r"\s+", " ", text)              # normalise spaces
    text = re.sub(r"[^\x00-\x7F]+", " ", text)   # remove non-ASCII
    return text.strip()


# FIX: removed the `llm` parameter — call_llm is used directly
def summarize_emails(emails: list) -> dict:
    if not emails:
        return {
            "email_count": 0,
            "summaries": []
        }

    summaries = []

    for i, email in enumerate(emails, start=1):
        sender = clean_sender(email.get("from", "Unknown sender"))
        body = clean_body(email.get("body", ""))
        attachments = email.get("attachment_text", "").strip()

        full_text = body
        if attachments:
            full_text += "\n\n" + attachments

        if not full_text.strip():
            summaries.append({
                "summary_number": i,
                "sender": sender,
                "summary": "This email contains no readable text in the body or attachments."
            })
            continue

        prompt = f"""
You are an email assistant.

Summarize the email below in **2–3 short sentences**.

Rules:
- Do NOT include links
- Do NOT include email addresses
- Do NOT copy text from the email
- Do NOT mention greetings, signatures, or promotions
- Focus only on the main purpose of the email
- Use simple, clear language

Email:
{full_text}
"""

        # FIX: was `llm.invoke(prompt).content.strip()` — now uses call_llm which
        # returns a plain string directly
        summary_text = call_llm(prompt)

        summaries.append({
            "summary_number": i,
            "sender": sender,
            "summary": summary_text
        })

    return {
        "email_count": len(summaries),
        "summaries": summaries
    }