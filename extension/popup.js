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
  const output = document.getElementById("output");
  output.innerText = "Thinking...";

  try {
    const res = await fetch(
      "https://inboxai-backend-tb5j.onrender.com/command",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ command: commandText }),
      }
    );

    if (!res.ok) {
      throw new Error(`Backend error: ${res.status}`);
    }

    const data = await res.json();
    console.log("Backend response:", data);

    // ✅ HANDLE UNREAD EMAIL SUMMARY
    if (data.summaries && data.summaries.length > 0) {
      let text = `You have ${data.email_count} unread emails.\n\n`;

      data.summaries.forEach((item, index) => {
        text += `${index + 1}. From ${item.sender}:\n${item.summary}\n\n`;
      });

      output.innerText = text;
      speak(`You have ${data.email_count} unread emails. I have summarized them.`);
      return;
    }

    // fallback
    const reply = data.message || "I received a response but couldn't understand it.";
    output.innerText = reply;
    speak(reply);

  } catch (err) {
    console.error(err);
    output.innerText = "Something went wrong while talking to the backend.";
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
