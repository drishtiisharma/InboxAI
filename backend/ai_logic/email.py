from services.llm_client import call_llm


def summarize_email_logic(body: str, sender: str, subject: str = "", attachments: str = ""):
    """
    Summarize email body and attachments in a natural, conversational way
    
    Args:
        body: Email body text
        sender: Email sender
        subject: Email subject line
        attachments: Already-processed attachment text (string)
    """
    
    print(f"\n=== Summarizing email from {sender} ===")
    print(f"Subject: {subject}")
    print(f"Body length: {len(body)} chars")
    print(f"Attachment text length: {len(attachments)} chars")
    
    # Build the context
    context_parts = []
    
    # Subject line
    if subject and subject.strip():
        context_parts.append(f"Subject: {subject}")
    
    # Email body
    if body and body.strip():
        body_preview = body[:2000] if len(body) > 2000 else body
        context_parts.append(f"\nEmail Body:\n{body_preview}")
    else:
        context_parts.append("\nEmail Body:\n[No body text]")
    
    # Attachments (already processed as text)
    if attachments and attachments.strip():
        context_parts.append(f"\n{attachments}")
    
    # Create a natural, conversational prompt
    full_prompt = f"""You're a friendly email assistant. Summarize this email naturally and conversationally, like you're telling a friend about it.

Keep it brief (1-2 sentences max). Be casual and human. Don't include URLs, links, or technical formatting. Just tell me what the email is about in plain language.

Email from: {sender}

{chr(10).join(context_parts)}

Quick summary:"""
    
    print(f"Prompt length: {len(full_prompt)} chars")
    
    # Call LLM
    try:
        summary = call_llm(full_prompt)
        print(f"Summary generated successfully")
        return summary.strip()
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        
        # Fallback summary
        if body and body.strip():
            preview = body[:80].strip()
            return f"It's about {preview}..."
        elif subject:
            return f"Email about: {subject}"
        else:
            return "Email received (couldn't read the content)"