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

    # FIX: strip markdown fences the model sometimes wraps around JSON
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(cleaned.split("\n")[1:])
    if cleaned.endswith("```"):
        cleaned = "\n".join(cleaned.split("\n")[:-1])
    cleaned = cleaned.strip()

    try:
        drafts = json.loads(cleaned)
        # Validate it's a non-empty list
        if isinstance(drafts, list) and drafts:
            return drafts
        raise ValueError("Parsed JSON is not a valid list")
    except Exception:
        # FIX: return safe fallback drafts instead of raising, keeping the caller alive
        receiver_name = receiver.split("@")[0] if "@" in receiver else receiver
        return [
            {
                "subject": f"Regarding: {intent[:50]}",
                "body": f"Hello {receiver_name},\n\n{intent}\n\nBest regards,\n[Your Name]"
            },
            {
                "subject": f"Follow up: {intent[:50]}",
                "body": f"Dear {receiver_name},\n\nI wanted to follow up about: {intent}\n\nSincerely,\n[Your Name]"
            },
            {
                "subject": f"Quick update: {intent[:50]}",
                "body": f"Hi {receiver_name},\n\nJust a quick note: {intent}\n\nThanks,\n[Your Name]"
            }
        ]