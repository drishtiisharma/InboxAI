# draft_service.py
# FIX: original used the deprecated openai.ChatCompletion.create (old SDK <1.0).
# This project already has email_drafter.py which does the same thing correctly
# using the shared llm_client (Groq). This file now delegates to that module so
# there is a single source of truth for draft generation.

from typing import List, Dict
from services.email_drafter import generate_email_drafts as _generate


def generate_email_drafts(
    intent: str,
    receiver: str,
    tone: str = "professional",
    context: str = ""
) -> List[Dict[str, str]]:
    """
    Generate multiple email draft options.
    Delegates to email_drafter which uses the shared Groq llm_client.
    """
    return _generate(intent=intent, receiver=receiver, tone=tone, context=context)