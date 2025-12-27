from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
import subprocess
from bs4 import BeautifulSoup

from voice_control import speak, listen_command, parse_command
import time

from image_reader import extract_text_from_image
from pdf_reader import extract_text_from_pdf
from word_reader import extract_text_from_docx
from excel_reader import extract_text_from_xlsx
from csv_reader import extract_text_from_csv
import re


# ============================ SETTINGS ============================
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# ============================ GMAIL SERVICE ============================
def get_gmail_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("gmail", "v1", credentials=creds)

# ============================ EMAIL BODY EXTRACTION ============================
def get_email_body(msg):
    def decode(data):
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    def walk_parts(parts):
        for part in parts:
            mime = part.get("mimeType", "")
            body = part.get("body", {}).get("data")

            if mime == "text/plain" and body:
                return decode(body)

            if mime == "text/html" and body:
                soup = BeautifulSoup(decode(body), "html.parser")
                return soup.get_text(separator=" ")

            if "parts" in part:
                result = walk_parts(part["parts"])
                if result:
                    return result
        return ""

    payload = msg.get("payload", {})
    if "parts" in payload:
        return walk_parts(payload["parts"])

    body = payload.get("body", {}).get("data")
    if body:
        if payload.get("mimeType") == "text/html":
            soup = BeautifulSoup(decode(body), "html.parser")
            return soup.get_text(separator=" ")
        return decode(body)

    return ""

# ============================ SENDER EXTRACTION ============================
def get_sender(msg):
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == "from":
            return h["value"]
    return "Unknown sender"

#============================EMAIL SUMMARIZATION============================
def clean_email_for_llm(text):
    text = re.sub(r"\ufeff|\u2007", " ", text)  # invisible junk
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(tap to apply|click here|unsubscribe)", "", text, flags=re.I)
    return text.strip()


def summarize_email(body, sender):
    clean_body = clean_email_for_llm(body)
    prompt = (
        "Explain the email clearly in natural language.\n\n"
        "Rules:\n"
        "- Do NOT read subject lines, signatures, or formatting\n"
        "- Do NOT mention email structure or bullet points\n"
        "- Do NOT copy lines from the email\n\n"
        "Instead:\n"
        "- Explain what the email is about\n"
        "- Explain why it was sent\n"
        "- Mention who sent it using their name naturally\n"
        "- Explain what is expected from the user, if anything\n\n"
        "Speak like you're explaining it to the user.\n"
        "No greetings. No opinions.\n\n"
        f"Sender: {sender}\n\n"
        f"{clean_body[:1200]}"
    )

    try:
        result = subprocess.run(
        ["ollama", "run", "llama3.2:3b", prompt],
        capture_output=True,
        timeout=90
    )
        return result.stdout.decode("utf-8", errors="ignore").strip()

    except subprocess.TimeoutExpired:
        return "This email is long and promotional. Here is a brief summary instead."


#============================ATTACHMENTS============================
def get_attachments(service, msg):
    attachments = []
    payload = msg.get("payload", {})
    parts = payload.get("parts", [])

    for part in parts:
        body = part.get("body", {})
        mime = part.get("mimeType", "")
        filename = part.get("filename")

        if "attachmentId" not in body:
            continue

        if not filename:
            if mime == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                filename = "attachment.xlsx"
            elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                filename = "attachment.docx"
            elif mime == "application/pdf":
                filename = "attachment.pdf"
            elif mime == "text/csv" or mime == "application/vnd.ms-excel":
                filename = "attachment.csv"
            else:
                continue

        attachment = service.users().messages().attachments().get(
            userId="me",
            messageId=msg["id"],
            id=body["attachmentId"]
        ).execute()

        file_data = base64.urlsafe_b64decode(attachment["data"])
        with open(filename, "wb") as f:
            f.write(file_data)

        attachments.append(filename)
        print("Saved attachment:", filename)

    return attachments


#============================DOCUMENT SUMMARIZATION============================
def summarize_document(text):
    prompt = (
        "Summarize the attached document clearly and concisely.\n"
        "Firstly brief what is the document about in 1-2 lines, in a semantic manner.\n"
        "Focus on key points and purpose.\n"
        "Use bullet points.\n"
        "Only explain what is mentioned in the document and what it is about, do not add extra from your own end(if the document is 1-2 paged)"
        "If the document is lengthy, just explain the gist of what the document contains on the superficial end"
        "If the document is an excel sheet, explain what kind of data it contains and what insights can be drawn from it\n\n"
        "No greetings. No opinions.\n\n"
        f"{text[:3000]}"
    )

    result = subprocess.run(
        ["ollama", "run", "llama3.2:3b", prompt],
        capture_output=True
    )
    return result.stdout.decode("utf-8", errors="ignore").strip()

#============================IMAGE DESCRIPTION============================

def describe_image(image_path):
    prompt = (
        "Describe the image clearly in one or two sentences. "
        "Mention visible objects and what seems to be happening. "
        "If it looks like an illustration or artwork, say so."
    )

    try:
        with open(image_path, "rb") as img:
            result = subprocess.run(
                ["ollama", "run", "moondream", prompt],
                input=img.read(),
                capture_output=True
            )

        return result.stdout.decode("utf-8", errors="ignore").strip()

    except Exception as e:
        return f"Could not describe image: {e}"



def is_meaningful_text(text):
    text = text.strip()
    if len(text) < 30:
        return False
    if text.count("\n") > len(text) * 0.3:
        return False
    return True

# ============================ GMAIL CATEGORY ============================
def get_gmail_category(msg):
    labels = msg.get("labelIds", [])

    if "CATEGORY_PRIMARY" in labels:
        return "Primary"
    elif "CATEGORY_SOCIAL" in labels:
        return "Social"
    elif "CATEGORY_PROMOTIONS" in labels:
        return "Promotions"
    elif "CATEGORY_UPDATES" in labels:
        return "Updates"
    elif "CATEGORY_FORUMS" in labels:
        return "Forums"
    else:
        return "Other"


#============================MAIN============================
def main():
    print("InboxAI started...")
    speak("Inbox AI is running. How may I assist you?")

    service = get_gmail_service()


    while True:
        command = listen_command()

        # 🚫 Ignore empty / noise / echo
        if not command.strip():
            continue

        action = parse_command(command)

        if action == "SUMMARIZE_EMAILS":
            print("Reached summarize block")
            speak("Alright, summarizing your unread emails now.")
            time.sleep(0.5)
            print("Calling Gmail API...")
            results = service.users().messages().list(
                userId="me",
                q="is:unread",
                maxResults=5
            ).execute()
            print("Gmail API returned")
            messages = results.get("messages", [])
            print("Unread messages count:", len(messages))


            speech_buffer = []

            for msg in messages:
                full_msg = service.users().messages().get(
                    userId="me", id=msg["id"], format="full"
                ).execute()

                category = get_gmail_category(full_msg)
                sender = get_sender(full_msg)
                body = get_email_body(full_msg)
                attachments = get_attachments(service, full_msg)

                print("Summarizing email from:", sender)


                if body.strip():
                    email_summary = summarize_email(body, sender)
                    speech_buffer.append(
                        f"Email category is {category}. {email_summary}"
                    )
                else:
                    speech_buffer.append(
                        f"Email category is {category}. This email has no readable body."
                    )

                for file in attachments:
                    if file.lower().endswith((".pdf", ".docx", ".xlsx", ".csv")):
                        text = (
                            extract_text_from_pdf(file)
                            if file.endswith(".pdf")
                            else extract_text_from_docx(file)
                            if file.endswith(".docx")
                            else extract_text_from_xlsx(file)
                            if file.endswith(".xlsx")
                            else extract_text_from_csv(file)
                        )

                        if text.strip():
                            doc_summary = summarize_document(text)
                            speech_buffer.append(
                                "Attached document summary. " + doc_summary
                            )


            print(f"Speech buffer size: {len(speech_buffer)}")
            print("Finished summarizing emails")
            print("\n" + "="*60)
            print("📧 EMAIL SUMMARIES")
            print("="*60 + "\n")

            if speech_buffer:
                # Speak each email summary separately with pauses
                for idx, summary in enumerate(speech_buffer, 1):
                    print(f"\n--- Email {idx} ---")
                    print(summary)
                    print("-" * 60)
                    
                    speak(f"Email {idx}.")
                    speak(summary)
                    time.sleep(0.5)  # Brief pause between emails
                
                print("\n✅ All emails summarized\n")
                speak("Finished summarizing your emails.")
            else:
                print("📭 No unread emails found.\n")
                speak("No unread emails found.")

        elif action == "EXIT":
            speak("Goodbye")
            break

        else:
            speak("Sorry, I didn't understand that command.")


if __name__ == "__main__":
    main()