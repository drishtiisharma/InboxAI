import json
from services.llm_client import call_llm

def generate_email_drafts(intent: str, receiver: str, tone: str, context: str = ""):
    prompt = f"""
Generate 3 email drafts as VALID JSON.

Rules:
- Respond ONLY with JSON
- No markdown
- No explanation

Format:
[
  {{ "subject": "...", "body": "..." }},
  {{ "subject": "...", "body": "..." }},
  {{ "subject": "...", "body": "..." }}
]

Intent: {intent}
Receiver: {receiver}
Tone: {tone}
Context: {context}
"""

    response = call_llm(prompt)

    # 🧠 IMPORTANT: parse LLM output safely
    try:
        return json.loads(response)
    except Exception:
        raise ValueError("LLM returned invalid JSON")
