from services.llm_client import call_llm

def get_email_category(body: str, sender: str, subject: str = "") -> str:
    prompt = f"""
    Categorize the email into ONE category:
    Primary, Promotions, Social, Spam, Updates

    Sender: {sender}
    Subject: {subject}
    Body: {body}

    Respond with ONLY the category name.
    """

    category = call_llm(prompt).strip()
    return category
