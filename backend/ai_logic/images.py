from services.llm_client import summarize_text

def summarize_image(extracted_text):
    return summarize_text(extracted_text, context="image content")
