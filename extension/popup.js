// ===================== ELEMENTS =====================
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const chatMessages = document.getElementById("chatMessages");
const themeToggle = document.getElementById("themeToggle");
const body = document.body;

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

// ===================== SPEECH (FIXED) =====================
let voices = [];
let speechUnlocked = false;

// Load voices properly
function loadVoices() {
  voices = window.speechSynthesis.getVoices();
}

window.speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();

// 🔓 Unlock speech on first user interaction
document.addEventListener("click", () => {
  if (!speechUnlocked) {
    const unlock = new SpeechSynthesisUtterance(" ");
    unlock.volume = 0;
    window.speechSynthesis.speak(unlock);
    speechUnlocked = true;
  }
}, { once: true });

function speak(text) {
  if (!speechUnlocked || !text.trim()) return;

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 1;
  utterance.pitch = 1;

  const voice =
    voices.find(v => v.lang === "en-US") ||
    voices.find(v => v.lang.startsWith("en")) ||
    voices[0];

  if (voice) utterance.voice = voice;

  window.speechSynthesis.speak(utterance);
}

// ===================== CHAT =====================
function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = `message ${type}`;
  
  // Convert \n\n to paragraphs and \n to <br>
  const htmlContent = text
    .split('\n\n')
    .map(para => `<p>${para.replace(/\n/g, '<br>')}</p>`)
    .join('');
  
  div.innerHTML = htmlContent;
  chatMessages.appendChild(div);
  scrollToBottom();

  if (type === "bot") {
    speak(text);
  }
}

function showThinking() {
  const div = document.createElement("div");
  div.className = "thinking";
  div.id = "thinking";
  div.innerHTML = `
    <div class="thinking-dots">
      <span></span><span></span><span></span>
    </div>
    <p>Thinking...</p>
  `;
  chatMessages.appendChild(div);
  scrollToBottom();
}

function removeThinking() {
  const t = document.getElementById("thinking");
  if (t) t.remove();
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===================== SEND COMMAND =====================
// ===================== SEND COMMAND (FIXED) =====================
// ===================== SEND COMMAND (WITH DEBUG) =====================
async function sendCommand() {
  const command = input.value.trim();
  if (!command) return;

  addMessage(command, "user");
  input.value = "";

  showThinking();

  try {
    const res = await fetch("https://inboxai-backend-tb5j.onrender.com/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command })
    });

    // Check if response is OK
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    console.log("Backend response:", data); // DEBUG: Check what we're getting
    removeThinking();

    let reply = "";

    // Handle different response types
    if (data.type === "conversation") {
      reply = data.message;
    } 
    else if (data.type === "single_email" && data.data) {
      const cleanSender = data.data.sender.replace(/<[^>]*>/g, '').trim();
      const cleanSummary = data.data.summary.replace(/^Summary of email from[^:]*:\s*/i, '');
      reply = `Your last email was from ${cleanSender}:\n\n${cleanSummary}`;
    } 
    else if (data.type === "multiple_emails" && data.data && data.data.summaries) {
      const emailCount = data.data.email_count;
      const intro = `You have ${emailCount} unread email${emailCount > 1 ? 's' : ''}.\n\n`;
      
      const formattedEmails = data.data.summaries.map((s, index) => {
        const cleanSender = s.sender.replace(/<[^>]*>/g, '').trim();
        const cleanSummary = s.summary.replace(/^Summary of email from[^:]*:\s*/i, '');
        const ordinal = index === 0 ? '1st' : index === 1 ? '2nd' : index === 2 ? '3rd' : `${index + 1}th`;
        return `Your ${ordinal} unread email is from ${cleanSender}:\n${cleanSummary}`;
      }).join("\n\n---\n\n");
      
      reply = intro + formattedEmails;
    }
    // FALLBACK: Handle old response format (backward compatibility)
    else if (data.summaries && Array.isArray(data.summaries)) {
      const emailCount = data.summaries.length;
      const intro = `You have ${emailCount} unread email${emailCount > 1 ? 's' : ''}.\n\n`;
      
      const formattedEmails = data.summaries.map((s, index) => {
        const cleanSender = s.sender.replace(/<[^>]*>/g, '').trim();
        const cleanSummary = s.summary.replace(/^Summary of email from[^:]*:\s*/i, '');
        const ordinal = index === 0 ? '1st' : index === 1 ? '2nd' : index === 2 ? '3rd' : `${index + 1}th`;
        return `Your ${ordinal} unread email is from ${cleanSender}:\n${cleanSummary}`;
      }).join("\n\n---\n\n");
      
      reply = intro + formattedEmails;
    }
    else if (data.summary) {
      const cleanSender = data.sender.replace(/<[^>]*>/g, '').trim();
      const cleanSummary = data.summary.replace(/^Summary of email from[^:]*:\s*/i, '');
      reply = `Your last email was from ${cleanSender}:\n\n${cleanSummary}`;
    }
    else if (data.error) {
      reply = data.error;
    }
    else if (data.message) {
      reply = data.message;
    }
    else {
      console.error("Unexpected response format:", data);
      reply = "Received an unexpected response format.";
    }

    addMessage(reply, "bot");

  } catch (err) {
    removeThinking();
    console.error("Error details:", err);
    addMessage(`Error: ${err.message}. Please check console for details.`, "bot");
  }
}
// ===================== EVENTS =====================
sendBtn.addEventListener("click", sendCommand);

input.addEventListener("keydown", (e) => {
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

