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

window.onload = () => {
  // ===== GREETING =====
  speak("Hi, this is InboxAI. How can I help you?");

  // ===== SEND BUTTON =====
  const sendBtn = document.getElementById("send");
  if (sendBtn) {
    sendBtn.onclick = () => {
      const text = document.getElementById("input").value.trim();
      if (!text) return;
      sendCommand(text);
    };
  }

  // ===== MIC BUTTON (optional) =====
  const micBtn = document.getElementById("mic");
  if (micBtn && recognition) {
    micBtn.onclick = () => recognition.start();
  }

  // ===== THEME TOGGLE =====
  const themeToggle = document.getElementById("themeToggle");
  const body = document.body;

  const currentTheme = localStorage.getItem("theme") || "light";
  if (currentTheme === "dark") {
    body.classList.add("dark");
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      body.classList.toggle("dark");
      const theme = body.classList.contains("dark") ? "dark" : "light";
      localStorage.setItem("theme", theme);
    });
  }
};
