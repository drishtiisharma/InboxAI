// ===================== SPEECH SETUP =====================
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
  alert("Speech Recognition not supported in this browser");
}

const recognition = new SpeechRecognition();
recognition.lang = "en-US";
recognition.continuous = false;
recognition.interimResults = false;

// ===================== SPEAK FUNCTION =====================
function speak(text) {
  if (!text || !text.trim()) {
    console.warn("Nothing to speak");
    return;
  }

  // Stop anything already speaking
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 1;
  utterance.pitch = 1;

  // Ensure voices are loaded
  const voices = window.speechSynthesis.getVoices();
  if (voices.length > 0) {
    utterance.voice = voices.find(v => v.lang === "en-US") || voices[0];
  }

  window.speechSynthesis.speak(utterance);
}

// ===================== GREETING =====================
window.onload = () => {
  speak("Hi, this is InboxAI. How can I help you?");
};

// ===================== VOICE RESULT =====================
recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  document.getElementById("input").value = transcript;
  sendCommand(transcript);
};

// ===================== MIC BUTTON =====================
//document.getElementById("mic").onclick = () => {
//  recognition.start();
//};

// ===================== SEND BUTTON =====================
document.getElementById("send").onclick = () => {
  const text = document.getElementById("input").value.trim();
  if (!text) return;
  sendCommand(text);
};

// ===================== SEND COMMAND TO BACKEND =====================
async function sendCommand(command) {
  try {
    const responseBox = document.getElementById("response");
    responseBox.textContent = "Thinking...";

    const res = await fetch("/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command })
    });

    const data = await res.json();

    if (!data || !data.response) {
      responseBox.textContent = "No response from backend.";
      return;
    }

    // 1️⃣ PRINT
    responseBox.textContent = data.response;

    // 2️⃣ SPEAK (THIS WAS MISSING / MISPLACED BEFORE)
    speak(data.response);

  } catch (err) {
    console.error(err);
    document.getElementById("response").textContent =
      "Something went wrong while talking to the backend.";
  }
}

// ===================== THEME TOGGLE =====================
const themeToggle = document.getElementById("themeToggle");
const body = document.body;

const currentTheme = localStorage.getItem("theme") || "light";
if (currentTheme === "dark") {
  body.classList.add("dark");
}

themeToggle.addEventListener("click", () => {
  body.classList.toggle("dark");
  const theme = body.classList.contains("dark") ? "dark" : "light";
  localStorage.setItem("theme", theme);
});
