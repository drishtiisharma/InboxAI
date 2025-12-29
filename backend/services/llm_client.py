import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def summarize_text(text: str, context: str = "general") -> str:
    prompt = f"""
"You are an assistant that summarizes emails in a short, natural paragraph. "
"Provide brief context about what the email is about and the key information, "
"in 2–3 clear sentences. Avoid bullet points unless absolutely necessary."

TEXT:
{text[:3000]}
"""

    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {
            "role": "system",
            "content": "You summarize emails into 2–3 natural sentences with brief context."
        },
        {
            "role": "user",
            "content": text[:3000]
        }
    ],
    temperature=0.3
)


    return response.choices[0].message.content.strip()
