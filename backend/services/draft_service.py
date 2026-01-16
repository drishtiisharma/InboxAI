# services/draft_service.py
from typing import List, Dict
import openai
import os

# Set your OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

def generate_email_drafts(intent: str, receiver: str, tone: str = "professional", context: str = "") -> List[Dict[str, str]]:
    """
    Generate multiple email draft options using GPT.
    """
    try:
        prompt = f"""
        Generate 3 email draft options with these specifications:
        
        Recipient: {receiver}
        Intent: {intent}
        Tone: {tone}
        Additional context: {context}
        
        Please provide 3 different options, each with:
        1. A subject line
        2. The email body
        
        Format your response as:
        OPTION 1:
        Subject: [subject here]
        Body: [email body here]
        
        OPTION 2:
        Subject: [subject here]
        Body: [email body here]
        
        OPTION 3:
        Subject: [subject here]
        Body: [email body here]
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional email writing assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Parse the response into structured data
        drafts = []
        current_option = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('OPTION'):
                if current_option:
                    drafts.append(current_option)
                current_option = {"subject": "", "body": ""}
            elif line.startswith('Subject:'):
                if current_option:
                    current_option["subject"] = line.replace('Subject:', '').strip()
            elif line.startswith('Body:'):
                if current_option:
                    current_option["body"] = line.replace('Body:', '').strip()
            elif current_option and line and not line.startswith('OPTION'):
                # Append to body if we're in the middle of an option
                if current_option["body"]:
                    current_option["body"] += "\n" + line
        
        # Add the last option
        if current_option:
            drafts.append(current_option)
        
        # Ensure we have exactly 3 drafts
        while len(drafts) < 3:
            drafts.append({
                "subject": f"Follow up: {intent[:50]}",
                "body": f"Dear {receiver.split('@')[0]},\n\nThis is regarding: {intent}\n\nBest regards,\n[Your Name]"
            })
        
        return drafts[:3]
        
    except Exception as e:
        print(f"Error generating drafts: {e}")
        # Fallback drafts
        return [
            {
                "subject": f"Regarding: {intent[:50]}",
                "body": f"Hello,\n\n{intent}\n\nBest regards,\n[Your Name]"
            },
            {
                "subject": f"Follow up: {intent[:50]}",
                "body": f"Dear {receiver.split('@')[0]},\n\nI wanted to follow up about: {intent}\n\nSincerely,\n[Your Name]"
            },
            {
                "subject": f"Quick update: {intent[:50]}",
                "body": f"Hi,\n\nJust wanted to share: {intent}\n\nThanks,\n[Your Name]"
            }
        ]