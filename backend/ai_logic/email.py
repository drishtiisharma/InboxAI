from services.summarizer import summarize_email

def summarize_email_logic(body: str, sender: str):
    return summarize_email(body, sender)