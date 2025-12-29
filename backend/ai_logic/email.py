from services.llm_client import summarize_text

def summarize_email(body: str, sender: str):
    context = f"Email from {sender}"
    return summarize_text(body, context=context)
