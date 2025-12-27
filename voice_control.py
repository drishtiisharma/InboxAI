import speech_recognition as sr
import pyttsx3
import re

# ============================ SPEECH ENGINE ============================
def get_engine():
    """Get a fresh TTS engine instance"""
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)  # Max volume
    return engine

recognizer = sr.Recognizer()

# ============================ CLEAN TEXT ============================
def clean_for_speech(text):
    text = re.sub(r"[*•\-+]", " ", text)
    text = re.sub(r"[()\[\]{}<>]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ============================ SPEAK ============================
def speak(text):
    """Speak text with better error handling"""
    if not text or not text.strip():
        print("⚠️ Empty text, skipping speech")
        return
    
    safe_text = clean_for_speech(text)
    print(f"🔊 Speaking: {safe_text[:100]}...")  # Debug output
    
    try:
        engine = get_engine()
        engine.say(safe_text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"❌ Speech error: {e}")
        # Fallback: print to console
        print(f"📢 [SPEECH]: {safe_text}")

# ============================ LISTEN ============================
def listen_command():
    with sr.Microphone() as source:
        print("🎤 Listening for command...")
        recognizer.adjust_for_ambient_noise(source, duration=0.4)

        try:
            audio = recognizer.listen(
                source,
                timeout=5,          # wait max 5 sec for speech to start
                phrase_time_limit=8 # max length of command
            )
        except sr.WaitTimeoutError:
            print("⏱️ No speech detected")
            return ""

    try:
        command = recognizer.recognize_google(audio)
        print(f"✅ You said: {command}")
        return command.lower()

    except sr.UnknownValueError:
        print("❌ Could not understand audio")
        return ""

    except sr.RequestError as e:
        print(f"❌ Speech service unavailable: {e}")
        return ""


# ============================ PARSE COMMAND ============================
def parse_command(command):
    command = command.lower()

    email_keywords = ["email", "emails", "mail", "inbox"]
    summarize_keywords = ["summarize", "summarise", "summary", "read", "check", "tell"]

    if any(word in command for word in email_keywords) and \
       any(word in command for word in summarize_keywords):
        return "SUMMARIZE_EMAILS"

    if any(word in command for word in ["exit", "stop", "quit", "close"]):
        return "EXIT"

    return "UNKNOWN"