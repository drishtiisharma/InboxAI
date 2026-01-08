const greetingText = "Hi, this is InboxAI. How can I help you?";
let greetingSpoken = false;

// ===================== ELEMENTS =====================
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const chatMessages = document.getElementById("chatMessages");
const themeToggle = document.getElementById("themeToggle");
const body = document.body;

// ===================== EMAIL DRAFT ELEMENTS =====================
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

// ===================== MEETING ELEMENTS =====================
const meetingView = document.getElementById("meetingView");

const generateMeetingBtn = document.getElementById("generateMeeting");

const cancelMeetingBtn = document.getElementById("cancelMeeting");
const copyMeetingLinkBtn = document.getElementById("copyMeetingLink");

// ===================== VIEW ELEMENTS =====================
const chatView = document.getElementById("chatView");
const draftView = document.getElementById("draftView");
const modeSteps = document.querySelectorAll(".step"); // Renamed to avoid conflict

let conversationHistory = [];
let draftSuggestions = [];
let selectedDraftIndex = null;
let generatedMeetingData = null;
let voices = [];
let speechUnlocked = false;

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

// ===================== MODE SWITCHING =====================
function switchMode(mode) {
  // Hide all views
  chatView.style.display = "none";
  draftView.style.display = "none";
  meetingView.style.display = "none";

  // Update step indicators
  modeSteps.forEach(step => {
    step.classList.remove("active");
    if (step.dataset.mode === mode) {
      step.classList.add("active");
    }
  });

  // Show selected view
  if (mode === "chat") {
    chatView.style.display = "block";
    showChatGreeting();
  } else if (mode === "draft") {
    draftView.style.display = "block";
    showStep(1); // Start at step 1 for draft mode
  } else if (mode === "meeting") {
    meetingView.style.display = "block";
    resetMeetingMode(); // Reset meeting form when entering
  }
}

function showChatGreeting() {
  if (greetingSpoken) return;
  addMessage(greetingText, "bot");
  greetingSpoken = true;
}

// Mode step click handlers
modeSteps.forEach(step => {
  step.addEventListener("click", () => {
    const mode = step.dataset.mode;
    switchMode(mode);
  });
});

// ===================== DRAFT STEP NAVIGATION =====================
function showStep(stepNumber) {
  if (inputForm) {
    inputForm.style.display = stepNumber === 1 ? "block" : "none";
  }
  
  if (draftSelection) {
    draftSelection.style.display = stepNumber === 2 ? "block" : "none";
  }
  
  if (confirmationStep) {
    confirmationStep.style.display = stepNumber === 3 ? "block" : "none";
  }
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
  generateDraftsBtn.textContent = "Generating...";

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
      throw new Error(`Draft generation failed: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data.data || !data.data.drafts || !Array.isArray(data.data.drafts)) {
      throw new Error("Invalid response structure");
    }

    draftSuggestions = data.data.drafts;
    displayDraftCards();
    showStep(2);

  } catch (err) {
    console.error("Error generating drafts:", err);
    alert("Failed to generate draft suggestions. Please try again.");
  } finally {
    generateDraftsBtn.disabled = false;
    generateDraftsBtn.textContent = "Generate Draft Suggestions";
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
  document.querySelectorAll(".draft-card").forEach(card => {
    card.classList.remove("selected");
  });

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

  confirmRecipient.textContent = recipient;
  confirmSubject.textContent = selectedDraft.subject;
  confirmBody.textContent = selectedDraft.body;

  showStep(3);
});

// ===================== SEND EMAIL =====================
sendEmailBtn.addEventListener("click", async () => {
  if (selectedDraftIndex === null) {
    alert("Please select a draft first");
    return;
  }

  const selectedDraft = draftSuggestions[selectedDraftIndex];
  const recipient = recipientEmail.value.trim();

  if (!recipient) {
    alert("Recipient email is missing");
    return;
  }

  showThinking();

  try {
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
    addMessage(`Email sent successfully to ${recipient}`, "bot");

    // Reset form
    recipientEmail.value = "";
    emailIntent.value = "";
    draftSuggestions = [];
    selectedDraftIndex = null;
    showStep(1);

  } catch (err) {
    removeThinking();
    console.error(err);
    addMessage("Failed to send email.", "bot");
  }
});

// ===================== CANCEL SEND =====================
cancelSendBtn.addEventListener("click", () => {
  showStep(2);
});

// ===================== SEND COMMAND =====================
async function sendCommand() {
  const command = input.value.trim();
  if (!command) return;

  addMessage(command, "user");
  input.value = "";
  showThinking();
const trimmedHistory = conversationHistory.slice(-10);
  try {
    const res = await fetch(
      "https://inboxai-backend-tb5j.onrender.com/command",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        

body: JSON.stringify({
  command,
  history: trimmedHistory
})

      }
    );

    conversationHistory.push({ role: "user", content: command });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
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

// ===================== CHAT EVENT LISTENERS =====================
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

// ===================== MEETING FUNCTIONS =====================
// Initialize meeting date field
if (document.getElementById("meetingDate")) {
  document.getElementById("meetingDate").valueAsDate = new Date();
}

// Time type toggle
if (document.getElementById("meetingTimeType")) {
  document.getElementById("meetingTimeType").addEventListener("change", (e) => {
    const timeInput = document.getElementById("meetingTime");
    if (e.target.value === "instant") {
      const now = new Date();
      timeInput.value = now.toTimeString().slice(0, 5);
      timeInput.disabled = true;
    } else {
      timeInput.disabled = false;
    }
  });
}

// Parse natural language command


// Generate meeting link
if (generateMeetingBtn) {
  generateMeetingBtn.addEventListener("click", async () => {
    const recipients = document.getElementById("meetingRecipients").value.trim();
    const date = document.getElementById("meetingDate").value;
    const time = document.getElementById("meetingTime").value;
    const duration = Number(
  document.getElementById("meetingDuration").value || 30
);

    const title = document.getElementById("meetingTitle").value.trim();
    const agenda = document.getElementById("meetingAgenda").value.trim();

    if (!recipients || !date || !time) {
      alert("Please fill recipients, date and time");
      return;
    }

    generateMeetingBtn.disabled = true;
    generateMeetingBtn.textContent = "Scheduling...";

    try {
      const response = await fetch(
        "https://inboxai-backend-tb5j.onrender.com/meeting/create",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: title || "Meeting",
            date,
            time,
            duration: Number(duration),
            recipients: recipients.split(",").map(e => e.trim()),
            agenda
          })
        }
      );

      if (!response.ok) throw new Error("Meeting creation failed");

      const data = await response.json();

      const meetLink = data.data.meetLink;

      // UI updates
      document.getElementById("generatedMeetingLink").textContent = meetLink;
      document.getElementById("meetingLinkDisplay").style.display = "block";

      document.getElementById("confirmMeetingRecipients").textContent = recipients;
      document.getElementById("confirmMeetingTime").textContent =
        new Date(`${date}T${time}`).toLocaleString();
      document.getElementById("confirmMeetingDuration").textContent =
        `${duration} minutes`;
      document.getElementById("confirmMeetingLink").textContent = meetLink;

      document.getElementById("meetingConfirmation").style.display = "block";

      generatedMeetingData = data.data;

    } catch (err) {
      console.error(err);
      alert("Failed to schedule meeting");
    } finally {
      generateMeetingBtn.disabled = false;
      generateMeetingBtn.textContent = "Schedule Meeting";
    }
  });
}


// Copy meeting link
if (copyMeetingLinkBtn) {
  copyMeetingLinkBtn.addEventListener("click", () => {
    const link = document.getElementById("generatedMeetingLink").textContent;
    navigator.clipboard.writeText(link).then(() => {
      copyMeetingLinkBtn.textContent = "Copied!";
      setTimeout(() => {
        copyMeetingLinkBtn.textContent = "Copy Link";
      }, 2000);
    }).catch(err => {
      console.error("Copy failed:", err);
    });
  });
}

// Send meeting invites


// Cancel meeting
if (cancelMeetingBtn) {
  cancelMeetingBtn.addEventListener("click", resetMeetingMode);
}

function resetMeetingMode() {
  if (document.getElementById("meetingCommand")) {
    document.getElementById("meetingCommand").value = "";
  }
  if (document.getElementById("meetingRecipients")) {
    document.getElementById("meetingRecipients").value = "";
  }
  if (document.getElementById("meetingDate")) {
    document.getElementById("meetingDate").valueAsDate = new Date();
  }
  if (document.getElementById("meetingTime")) {
    document.getElementById("meetingTime").value = "";
  }
  if (document.getElementById("meetingTimeType")) {
    document.getElementById("meetingTimeType").value = "custom";
    const timeInput = document.getElementById("meetingTime");
    if (timeInput) timeInput.disabled = false;
  }
  if (document.getElementById("meetingDuration")) {
    document.getElementById("meetingDuration").value = "30";
  }
  if (document.getElementById("meetingTitle")) {
    document.getElementById("meetingTitle").value = "";
  }
  if (document.getElementById("meetingAgenda")) {
    document.getElementById("meetingAgenda").value = "";
  }
  
  const linkDisplay = document.getElementById("meetingLinkDisplay");
  const confirmation = document.getElementById("meetingConfirmation");
  
  if (linkDisplay) linkDisplay.style.display = "none";
  if (confirmation) confirmation.style.display = "none";
  
  generatedMeetingData = null;
}

// ===================== INITIALIZATION =====================
// Start in chat mode
switchMode("chat");

// Initial greeting (speech)
document.addEventListener("click", () => {
  if (!speechUnlocked) {
    const unlock = new SpeechSynthesisUtterance(" ");
    unlock.volume = 0;
    window.speechSynthesis.speak(unlock);
    speechUnlocked = true;
  }
  speak(greetingText);
}, { once: true });