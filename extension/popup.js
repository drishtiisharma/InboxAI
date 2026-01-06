// ===================== ELEMENTS =====================
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const chatMessages = document.getElementById("chatMessages");
const themeToggle = document.getElementById("themeToggle");
const body = document.body;
let conversationHistory = [];

// ===================== THEME =====================
const savedTheme = localStorage.getItem("theme") || "light";
if (savedTheme === "dark") body.classList.add("dark");

themeToggle.addEventListener("click", () => {
  body.classList.toggle("dark");
  localStorage.setItem(
    "theme",
    body.classList.contains("dark") ? "dark" : "light"
  );
});

// ===================== SPEECH =====================
let voices = [];
let speechUnlocked = false;

function loadVoices() {
  voices = window.speechSynthesis.getVoices();
}
window.speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();

document.addEventListener(
  "click",
  () => {
    if (!speechUnlocked) {
      const unlock = new SpeechSynthesisUtterance(" ");
      unlock.volume = 0;
      speechSynthesis.speak(unlock);
      speechUnlocked = true;
    }
  },
  { once: true }
);

function speak(text) {
  if (!speechUnlocked || !text.trim()) return;

  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";

  const voice =
    voices.find(v => v.lang === "en-US") ||
    voices.find(v => v.lang.startsWith("en")) ||
    voices[0];

  if (voice) utterance.voice = voice;
  speechSynthesis.speak(utterance);
}

// ===================== CHAT HELPERS =====================
function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = `message ${type}`;

  const html = text
    .split("\n\n")
    .map(p => `<p>${p.replace(/\n/g, "<br>")}</p>`)
    .join("");

  div.innerHTML = html;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  if (type === "bot") speak(text);
}

function showThinking() {
  const div = document.createElement("div");
  div.id = "thinking";
  div.className = "thinking";
  div.innerHTML = `
    <div class="thinking-dots">
      <span></span><span></span><span></span>
    </div>
    <p>Thinking...</p>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeThinking() {
  const t = document.getElementById("thinking");
  if (t) t.remove();
}

// ===================== SEND COMMAND =====================
async function sendCommand() {
  const command = input.value.trim();
  if (!command) return;

  addMessage(command, "user");
  input.value = "";
  showThinking();

  try {
    const res = await fetch(
      "https://inboxai-backend-tb5j.onrender.com/command",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command, history: conversationHistory })
      }
    );

    // Update history with user's command after sending
    conversationHistory.push({ role: "user", content: command });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    console.log("Backend response:", data);
    removeThinking();

    // ✅ SINGLE SOURCE OF TRUTH
    if (typeof data.reply === "string") {
      addMessage(data.reply, "bot");
      conversationHistory.push({ role: "assistant", content: data.reply });
      return;
    }

    // Safety fallback (should never hit)
    addMessage("Something went wrong, but I’m still alive 👀", "bot");

  } catch (err) {
    removeThinking();
    console.error(err);
    addMessage("Backend error. Check console.", "bot");
  }
}

// ===================== EVENTS =====================
sendBtn.addEventListener("click", sendCommand);

input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendCommand();
  }
});

// ===================== GREETING =====================
const greetingText = "Hi, this is InboxAI. How can I help you?";

window.onload = () => {
  // show greeting text immediately
  const div = document.createElement("div");
  div.className = "message bot";
  div.textContent = greetingText;
  chatMessages.appendChild(div);
  scrollToBottom();
};

// 🔓 After first user interaction → speak greeting
document.addEventListener("click", () => {
  if (!speechUnlocked) {
    const unlock = new SpeechSynthesisUtterance(" ");
    unlock.volume = 0;
    window.speechSynthesis.speak(unlock);
    speechUnlocked = true;
  }

  speak(greetingText);
}, { once: true });

