const greetingText = "Hi, this is InboxAI. How can I help you?";
let greetingSpoken = false;


// ===================== ELEMENTS =====================
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const chatMessages = document.getElementById("chatMessages");
const themeToggle = document.getElementById("themeToggle");
const body = document.body;

// ===================== NEW EMAIL DRAFT ELEMENTS =====================
const inputForm = document.getElementById("inputForm");
const draftSelection = document.getElementById("draftSelection");
const confirmationStep = document.getElementById("confirmationStep");
const recipientEmail = document.getElementById("recipientEmail");
const emailIntent = document.getElementById("emailIntent");
const generateDraftsBtn = document.getElementById("generateDrafts");
const draftCards = document.getElementById("draftCards");
const confirmSelectionBtn = document.getElementById("confirmSelection");
const sendEmailBtn = document.getElementById("sendEmail");
const cancelSendBtn = document.getElementById("cancelSend");
const confirmRecipient = document.getElementById("confirmRecipient");
const confirmSubject = document.getElementById("confirmSubject");
const confirmBody = document.getElementById("confirmBody");
const stepIndicator = document.getElementById("stepIndicator");

let conversationHistory = [];
let draftSuggestions = [];
let selectedDraftIndex = null;

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

// ===================== STEP NAVIGATION =====================
function updateStepIndicator(activeStep) {
  const steps = stepIndicator.querySelectorAll('.step');
  steps.forEach((step, index) => {
    if (index + 1 <= activeStep) {
      step.classList.add('active');
    } else {
      step.classList.remove('active');
    }
  });
}

function showStep(stepNumber) {
  inputForm.style.display = stepNumber === 1 ? 'block' : 'none';
  draftSelection.style.display = stepNumber === 2 ? 'block' : 'none';
  confirmationStep.style.display = stepNumber === 3 ? 'block' : 'none';
  updateStepIndicator(stepNumber);
}

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

// ===================== GENERATE DRAFTS =====================
generateDraftsBtn.addEventListener("click", async () => {
  const recipient = recipientEmail.value.trim();
  const intent = emailIntent.value.trim();

  if (!recipient || !intent) {
    alert("Please fill in both recipient and email intent");
    return;
  }

  generateDraftsBtn.disabled = true;
  showThinking();

  try {
    const response = await fetch(
      "https://inboxai-backend-tb5j.onrender.com/email/draft",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          intent: intent,
          receiver: recipient,
          tone: "professional",
          context: ""
        })
      }
    );

    if (!response.ok) {
      throw new Error("Draft generation failed");
    }

    const data = await response.json();
    removeThinking();

    draftSuggestions = data.data.drafts; // ✅ ARRAY
    displayDraftCards();
    showStep(2);

  } catch (err) {
    removeThinking();
    console.error(err);
    alert("Failed to generate draft suggestions.");
  } finally {
    generateDraftsBtn.disabled = false;
  }
});

    

// ===================== DISPLAY DRAFT CARDS =====================
function displayDraftCards() {
  draftCards.innerHTML = "";
  selectedDraftIndex = null;
  confirmSelectionBtn.disabled = true;

  draftSuggestions.forEach((draft, index) => {
    const card = document.createElement("div");
    card.className = "draft-card";
    card.innerHTML = `
      <div class="draft-card-radio"></div>
      <div class="draft-card-header">Option ${index + 1}</div>
      <div class="draft-card-subject">Subject: ${draft.subject}</div>
      <div class="draft-card-body">${draft.body}</div>
    `;

    card.addEventListener("click", () => selectDraft(index));
    draftCards.appendChild(card);
  });
}

// ===================== SELECT DRAFT =====================
function selectDraft(index) {
  // Remove selection from all cards
  document.querySelectorAll(".draft-card").forEach(card => {
    card.classList.remove("selected");
  });

  // Select the clicked card
  const cards = draftCards.children;
  cards[index].classList.add("selected");
  selectedDraftIndex = index;
  confirmSelectionBtn.disabled = false;
}

// ===================== CONFIRM SELECTION =====================
confirmSelectionBtn.addEventListener("click", () => {
  if (selectedDraftIndex === null) {
    alert("Please select a draft");
    return;
  }

  const selectedDraft = draftSuggestions[selectedDraftIndex];
  const recipient = recipientEmail.value.trim();

  // Populate confirmation details
  confirmRecipient.textContent = recipient;
  confirmSubject.textContent = selectedDraft.subject;
  confirmBody.textContent = selectedDraft.body;

  showStep(3);
});

// ===================== SEND EMAIL =====================
sendEmailBtn.addEventListener("click", async () => {

  // 🔒 GUARD FIRST — ALWAYS FIRST
  if (selectedDraftIndex === null) {
    alert("Please select a draft first");
    return;
  }

  const selectedDraft = draftSuggestions[selectedDraftIndex];
  const recipient = recipientEmail.value.trim();

  if (!recipient) {
    alert("Please enter recipient email");
    return;
  }

  showThinking();

  try {
    console.log("Sending email:", {
      to: recipient,
      subject: selectedDraft.subject,
      body: selectedDraft.body
    });

    const response = await fetch(
      "https://inboxai-backend-tb5j.onrender.com/email/send",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: recipient,
          subject: selectedDraft.subject,
          body: selectedDraft.body
        })
      }
    );

    if (!response.ok) {
      throw new Error("Email send failed");
    }

    removeThinking();
    addMessage(`✅ Email sent successfully to ${recipient}`, "bot");

    // 🔄 reset UI
    recipientEmail.value = "";
    emailIntent.value = "";
    draftSuggestions = [];
    selectedDraftIndex = null;
    showStep(1);

  } catch (err) {
    removeThinking();
    console.error(err);
    addMessage("❌ Failed to send email.", "bot");
  }
});


// ===================== CANCEL SEND =====================
cancelSendBtn.addEventListener("click", () => {
  showStep(2);
});

// ===================== SEND COMMAND (original functionality) =====================
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

    conversationHistory.push({ role: "user", content: command });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    console.log("Backend response:", data);
    removeThinking();

    if (typeof data.reply === "string") {
      addMessage(data.reply, "bot");
      conversationHistory.push({ role: "assistant", content: data.reply });
      return;
    }

    addMessage("Something went wrong, but I'm still alive 👀", "bot");

  } catch (err) {
    removeThinking();
    console.error(err);
    addMessage("Backend error. Check console.", "bot");
  }
}

// ===================== EVENTS =====================
if (sendBtn) {
  sendBtn.addEventListener("click", sendCommand);
}

if (input) {
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendCommand();
    }
  });
}

// ===================== GREETING =====================

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

function showChatGreeting() {
  if (greetingSpoken) return;

  addMessage(greetingText, "bot"); // text + speech handled here
  greetingSpoken = true;
}

// ===================== VIEW TOGGLE (CHAT / DRAFT) =====================
const chatView = document.getElementById("chatView");
const draftView = document.getElementById("draftView");
const steps = document.querySelectorAll(".step");

function switchMode(mode) {
  chatView.style.display = "none";
  draftView.style.display = "none";

  steps.forEach(step => step.classList.remove("active"));

  if (mode === "chat") {
    chatView.style.display = "block";
    steps[0].classList.add("active");

    showChatGreeting(); // 👈 THIS IS THE KEY
  }

  if (mode === "draft") {
    draftView.style.display = "block";
    steps[1].classList.add("active");
  }
}

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
// Dot clicks
steps.forEach(step => {
  step.addEventListener("click", () => {
    const mode = step.dataset.mode;
    switchMode(mode);
  });
});

// Default view
switchMode("chat");

