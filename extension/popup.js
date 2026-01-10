const greetingText = "Hi, this is InboxAI. How can I help you?";
let greetingSpoken = false;

// ===================== ELEMENTS =====================
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const chatMessages = document.getElementById("chatMessages");
const themeToggle = document.getElementById("themeToggle");
const body = document.body;
const loginBtn = document.getElementById("loginWithGoogle");
const logoutBtn = document.getElementById("logout");
const userStatus = document.getElementById("userStatus");

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
const sendMeetingInviteBtn = document.getElementById("sendMeetingInvite");
const cancelMeetingBtn = document.getElementById("cancelMeeting");
const copyMeetingLinkBtn = document.getElementById("copyMeetingLink");

// ===================== VIEW ELEMENTS =====================
const chatView = document.getElementById("chatView");
const draftView = document.getElementById("draftView");
const modeSteps = document.querySelectorAll(".step");

let conversationHistory = [];
let draftSuggestions = [];
let selectedDraftIndex = null;
let generatedMeetingData = null;
let voices = [];
let speechUnlocked = false;
let isGenerating = false;
let currentUser = null;

// ===================== BACKEND URL =====================
const BACKEND_URL = "https://inboxai-backend-tb5j.onrender.com";

// ===================== AUTH FUNCTIONS =====================
async function checkAuthStatus() {
  try {
    const response = await fetch(`${BACKEND_URL}/auth/status`, {
      method: "GET",
      credentials: "include"
    });

    if (response.ok) {
      const data = await response.json();
      if (data.logged_in && data.user) {
        currentUser = data.user;
        updateUIForLoggedInUser();
      } else {
        currentUser = null;
        updateUIForLoggedOutUser();
      }
    } else {
      currentUser = null;
      updateUIForLoggedOutUser();
    }
  } catch (error) {
    console.error("Auth check failed:", error);
    currentUser = null;
    updateUIForLoggedOutUser();
  }
}

function updateUIForLoggedInUser() {
  if (loginBtn) loginBtn.style.display = "none";
  if (logoutBtn) logoutBtn.style.display = "block";
  if (userStatus) {
    userStatus.textContent = `Logged in as: ${currentUser}`;
    userStatus.style.display = "block";
  }
  
  // Enable all action buttons
  const actionButtons = [sendBtn, generateDraftsBtn, generateMeetingBtn];
  actionButtons.forEach(btn => {
    if (btn) btn.disabled = false;
  });
}

function updateUIForLoggedOutUser() {
  if (loginBtn) loginBtn.style.display = "block";
  if (logoutBtn) logoutBtn.style.display = "none";
  if (userStatus) userStatus.style.display = "none";
  
  // Disable action buttons requiring auth
  const actionButtons = [generateDraftsBtn, generateMeetingBtn];
  actionButtons.forEach(btn => {
    if (btn) btn.disabled = true;
  });
}

// ===================== LOGIN/LOGOUT HANDLERS =====================
if (loginBtn) {
  loginBtn.addEventListener("click", () => {
    
    chrome.tabs.create({
      url: `${BACKEND_URL}/auth/google`
    });
    
  });
}


if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/auth/logout`, {
        method: "POST",
        credentials: "include"
      });

      if (response.ok) {
        currentUser = null;
        updateUIForLoggedOutUser();
        alert("Logged out successfully");
      }
    } catch (error) {
      console.error("Logout failed:", error);
      alert("Logout failed. Please try again.");
    }
  });
}

// ===================== THEME =====================
const savedTheme = localStorage.getItem("theme") || "light";
if (savedTheme === "dark") body.classList.add("dark");

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    body.classList.toggle("dark");
    localStorage.setItem(
      "theme",
      body.classList.contains("dark") ? "dark" : "light"
    );
  });
}

// ===================== SPEECH =====================
function loadVoices() {
  voices = window.speechSynthesis.getVoices();
}

if ('speechSynthesis' in window) {
  window.speechSynthesis.onvoiceschanged = loadVoices;
  loadVoices();
  
  // Speech unlock on user interaction
  const unlockSpeech = () => {
    if (!speechUnlocked && speechSynthesis) {
      try {
        const unlock = new SpeechSynthesisUtterance(" ");
        unlock.volume = 0;
        speechSynthesis.speak(unlock);
        speechUnlocked = true;
        if (!greetingSpoken) {
          speak(greetingText);
        }
      } catch (error) {
        console.error("Speech synthesis initialization failed:", error);
        speechUnlocked = false;
      }
    }
  };
  
  // Multiple interaction types to unlock speech
  document.addEventListener('click', unlockSpeech, { once: true });
  document.addEventListener('keydown', unlockSpeech, { once: true });
  document.addEventListener('touchstart', unlockSpeech, { once: true });
}

function speak(text) {
  if (!speechUnlocked || !text.trim() || !window.speechSynthesis) return;
  
  try {
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    const voice =
      voices.find(v => v.lang === "en-US") ||
      voices.find(v => v.lang.startsWith("en")) ||
      voices[0];

    if (voice) utterance.voice = voice;
    speechSynthesis.speak(utterance);
  } catch (error) {
    console.error("Speech failed:", error);
  }
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
  chatView.style.display = "none";
  draftView.style.display = "none";
  meetingView.style.display = "none";

  modeSteps.forEach(step => {
    step.classList.remove("active");
    if (step.dataset.mode === mode) {
      step.classList.add("active");
    }
  });

  if (mode === "chat") {
    chatView.style.display = "block";
    showChatGreeting();
  } else if (mode === "draft") {
    draftView.style.display = "block";
    showStep(1);
    if (!currentUser) {
      alert("Please log in to use email drafting feature.");
    }
  } else if (mode === "meeting") {
    meetingView.style.display = "block";
    resetMeetingMode();
    if (!currentUser) {
      alert("Please log in to schedule meetings.");
    }
  }
}

function showChatGreeting() {
  if (greetingSpoken) return;
  addMessage(greetingText, "bot");
  greetingSpoken = true;
}

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
if (generateDraftsBtn) {
  generateDraftsBtn.addEventListener("click", async () => {
    // Check authentication
    if (!currentUser) {
      alert("Please log in to generate email drafts.");
      return;
    }

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
        `${BACKEND_URL}/email/draft`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            intent: intent,
            receiver: recipient,
            tone: "professional",
            context: ""
          }),
          credentials: "include" // CRITICAL: Send cookies for user identification
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication required. Please log in.");
        }
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
      alert(err.message || "Failed to generate draft suggestions. Please try again.");
      
      // If auth error, update UI
      if (err.message.includes("Authentication")) {
        checkAuthStatus();
      }
    } finally {
      generateDraftsBtn.disabled = false;
      generateDraftsBtn.textContent = "Generate Draft Suggestions";
    }
  });
}

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
  if (confirmSelectionBtn) confirmSelectionBtn.disabled = false;
}

// ===================== CONFIRM SELECTION =====================
if (confirmSelectionBtn) {
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
}

// ===================== SEND EMAIL =====================
if (sendEmailBtn) {
  sendEmailBtn.addEventListener("click", async () => {
    // Check authentication
    if (!currentUser) {
      alert("Please log in to send emails.");
      return;
    }

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

    sendEmailBtn.disabled = true;
    sendEmailBtn.textContent = "Sending...";

    try {
      const response = await fetch(
        `${BACKEND_URL}/email/send`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            to: recipient,
            subject: selectedDraft.subject,
            body: selectedDraft.body
          }),
          credentials: "include" // CRITICAL: Send cookies for user identification
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication required. Please log in.");
        }
        throw new Error("Email send failed");
      }

      alert(`Email sent successfully to ${recipient}`);

      recipientEmail.value = "";
      emailIntent.value = "";
      draftSuggestions = [];
      selectedDraftIndex = null;
      showStep(1);

    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to send email.");
      
      // If auth error, update UI
      if (err.message.includes("Authentication")) {
        checkAuthStatus();
      }
    } finally {
      sendEmailBtn.disabled = false;
      sendEmailBtn.textContent = "Send Email";
    }
  });
}

// ===================== CANCEL SEND =====================
if (cancelSendBtn) {
  cancelSendBtn.addEventListener("click", () => {
    showStep(2);
  });
}

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
      `${BACKEND_URL}/command`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          command,
          history: trimmedHistory
        }),
        credentials: "include" // CRITICAL: Send cookies for user identification
      }
    );

    conversationHistory.push({ role: "user", content: command });

    if (!res.ok) {
      if (res.status === 401) {
        throw new Error("Authentication required. Please log in.");
      }
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
    
    if (err.message.includes("Authentication")) {
      addMessage("Please log in to use chat features.", "bot");
      checkAuthStatus();
    } else {
      addMessage("Backend error. Check console.", "bot");
    }
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
if (document.getElementById("meetingDate")) {
  document.getElementById("meetingDate").valueAsDate = new Date();
}

if (document.getElementById("meetingTimeType")) {
  document.getElementById("meetingTimeType").addEventListener("change", (e) => {
    const timeInput = document.getElementById("meetingTime");

    if (e.target.value === "instant") {
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      timeInput.value = `${hh}:${mm}`;
      timeInput.disabled = true;
    } else {
      timeInput.disabled = false;
      timeInput.value = "";
    }
  });
}

// Generate meeting link
if (generateMeetingBtn) {
  generateMeetingBtn.addEventListener("click", async () => {
    // Check authentication
    if (!currentUser) {
      alert("Please log in to schedule meetings.");
      return;
    }

    const recipientsRaw = document.getElementById("meetingRecipients").value.trim();
    const date = document.getElementById("meetingDate").value;
    const time = document.getElementById("meetingTime").value;
    const duration = Number(document.getElementById("meetingDuration").value || 30);
    const title = document.getElementById("meetingTitle").value.trim();
    const agenda = document.getElementById("meetingAgenda").value.trim();

    if (!recipientsRaw || !date || !time) {
      alert("Please fill recipients, date and time");
      return;
    }

    // ✅ CLEAN + VALIDATE RECIPIENTS
    const recipients = recipientsRaw
      .split(",")
      .map(e => e.trim())
      .filter(Boolean);

    if (recipients.length === 0) {
      alert("Please enter at least one valid email");
      return;
    }

    // ✅ TIME FORMAT GUARD (CRITICAL)
    if (!/^\d{2}:\d{2}$/.test(time)) {
      alert("Invalid time format. Please reselect the meeting time.");
      return;
    }

    generateMeetingBtn.disabled = true;
    generateMeetingBtn.textContent = "Scheduling...";

    try {
      const response = await fetch(
        `${BACKEND_URL}/meeting/create`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: title || "Meeting",
            date,
            time,
            duration,
            recipients,
            agenda
          }),
          credentials: "include" // CRITICAL: Send cookies for user identification
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication required. Please log in.");
        }
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const data = await response.json();

      if (!data?.data?.meetLink) {
        throw new Error("Meeting created but no Meet link returned");
      }

      const meetLink = data.data.meetLink;

      document.getElementById("generatedMeetingLink").textContent = meetLink;
      document.getElementById("meetingLinkDisplay").style.display = "block";

      document.getElementById("confirmMeetingRecipients").textContent = recipients.join(", ");
      document.getElementById("confirmMeetingTime").textContent =
        new Date(`${date}T${time}`).toLocaleString();
      document.getElementById("confirmMeetingDuration").textContent =
        `${duration} minutes`;
      document.getElementById("confirmMeetingLink").textContent = meetLink;

      document.getElementById("meetingConfirmation").style.display = "block";

      generatedMeetingData = data.data;

    } catch (err) {
      console.error("Meeting scheduling failed:", err);
      alert(err.message || "Failed to schedule meeting.");
      
      // If auth error, update UI
      if (err.message.includes("Authentication")) {
        checkAuthStatus();
      }
    } finally {
      generateMeetingBtn.disabled = false;
      generateMeetingBtn.textContent = "Generate Meeting & Send Invites";
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
if (sendMeetingInviteBtn) {
  sendMeetingInviteBtn.addEventListener("click", async () => {
    try {
      alert("Meeting invites sent successfully!");
      resetMeetingMode();
    } catch (error) {
      console.error("Error sending invites:", error);
    }
  });
}

// Cancel meeting
if (cancelMeetingBtn) {
  cancelMeetingBtn.addEventListener("click", resetMeetingMode);
}

function resetMeetingMode() {
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
async function initializeApp() {
  // Check auth status on startup
  await checkAuthStatus();
  
  // Set up periodic auth checks
  setInterval(checkAuthStatus, 30000); // Check every 30 seconds
  
  // Start with chat mode
  switchMode("chat");
}

// Start the app
initializeApp();