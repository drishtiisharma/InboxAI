#============================DOCUMENT SUMMARIZATION============================
import subprocess

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


