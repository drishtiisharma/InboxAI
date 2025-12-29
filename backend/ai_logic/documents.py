# ============================ DOCUMENT SUMMARIZATION ============================

from services.llm_client import summarize_text

def summarize_document(text: str) -> str:
    return summarize_text(text, context="document")
