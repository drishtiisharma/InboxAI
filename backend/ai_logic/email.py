#============================EMAIL SUMMARIZATION============================
import re
import subprocess

def clean_email_for_llm(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\ufeff|\u2007", " ", text) 
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(tap to apply|click here|unsubscribe)", "", text, flags=re.I)
    return text.strip()


def clean_email_for_llm(text: str) -> str:
    text = re.sub(r"\ufeff|\u2007", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(tap to apply|click here|unsubscribe)", "", text, flags=re.I)
    return text.strip()


def summarize_email(body: str, sender: str) -> str:
    if not body or not body.strip():
        return "No readable email content was found."

    clean_body = clean_email_for_llm(body)

    prompt = (
        "Explain the email clearly in natural language.\n\n"
        "Rules:\n"
        "- Do NOT read subject lines, signatures, or formatting\n"
        "- Do NOT mention email structure or bullet points\n"
        "- Do NOT copy lines from the email\n\n"
        "Instead:\n"
        "- Explain what the email is about\n"
        "- Explain why it was sent\n"
        "- Mention who sent it using their name naturally\n"
        "- Explain what is expected from the user, if anything\n\n"
        "Explain briefly in 2–3 sentences, concise and direct.\n"
        "Avoid repetition. Avoid filler.\n"
        "No greetings. No opinions.\n\n"
        f"Sender: {sender}\n\n"
        f"{clean_body[:1200]}"
    )

    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2:3b"],
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=60
        )

        return result.stdout.decode("utf-8", errors="ignore").strip()

    except Exception as e:
        return f"Failed to summarize email: {e}"
