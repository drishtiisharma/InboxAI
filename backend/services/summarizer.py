import os
from groq import Groq

# Load API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in environment variables")

client = Groq(api_key=GROQ_API_KEY)


def summarize_email(email_body: str, sender: str = "Email") -> str:
    """
    Summarizes an email using Groq LLM (FREE tier).
    """

    prompt = f"""
You are an AI assistant called InboxAI.

Summarize the following email clearly and concisely.
- Keep it short
- Use simple language
- Preserve important action items
- Do NOT hallucinate

Sender: {sender}

Email:
{email_body}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You summarize emails into 2–3 natural sentences with brief context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Groq error:", e)
        return "Failed to summarize email."
