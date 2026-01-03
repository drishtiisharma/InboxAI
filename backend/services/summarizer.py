import re

def clean_sender(sender: str) -> str:
    # "Team Unstop <noreply@x.com>" → "Team Unstop"
    return sender.split("<")[0].strip()


def clean_body(text: str) -> str:
    text = re.sub(r"http\S+", "", text)        # remove links
    text = re.sub(r"\s+", " ", text)            # normalize spaces
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove weird unicode
    return text.strip()


def summarize_emails(llm, emails):
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

        response = llm.invoke(prompt)

        summaries.append({
            "summary_number": i,
            "sender": sender,
            "summary": response.content.strip()
        })

    return {
        "email_count": len(summaries),
        "summaries": summaries
    }
