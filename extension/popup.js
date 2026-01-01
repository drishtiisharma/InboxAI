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
  if (!window.speechSynthesis) return;

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1;
  utterance.pitch = 1;
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
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
async function sendCommand(commandText) {
  console.log("Sending command:", commandText);

  try {
    const res = await fetch("http://localhost:8000/command", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        command: commandText,
      }),
    });

    if (!res.ok) {
      throw new Error(`Backend error: ${res.status}`);
    }

    const data = await res.json();
    console.log("Backend response:", data);

    if (data.response) {
      speak(data.response);
    } else {
      speak("I got a response, but it was empty.");
    }
  } catch (err) {
    console.error("Command failed:", err);
    speak("Something went wrong while talking to the backend.");
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
