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
//function speak(text) {
//  const utterance = new SpeechSynthesisUtterance(text);
//  utterance.lang = "en-US";
//  window.speechSynthesis.speak(utterance);
// }

// ===================== SEND COMMAND =====================
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

// ===================== VOICE INPUT =====================
recognition.onresult = (event) => {
  const commandText = event.results[0][0].transcript.toLowerCase();
  console.log("Heard:", commandText);
  sendCommand(commandText);
};

recognition.onerror = (event) => {
  console.error("Speech recognition error:", event.error);
};

// ===================== BUTTON HANDLER =====================
document.getElementById("micBtn").addEventListener("click", () => {
  recognition.start();
});
