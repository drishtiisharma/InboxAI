from services.llm_client import call_llm

def generate_email_drafts(intent: str, receiver: str, tone: str, context: str = ""):
    prompt = f"""
You are an email assistant.

Generate 3 email drafts.
Rules:
- Be concise
- Match the tone
- Include a subject line

Intent: {intent}
Receiver: {receiver}
Tone: {tone}
Extra context: {context}

Return only numbered drafts.
"""

    response = call_llm(prompt)
    return response
