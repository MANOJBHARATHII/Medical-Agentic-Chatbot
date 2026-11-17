const conversation = [];
const tokenInput = document.querySelector("#api-token");
const form = document.querySelector("#chat-form");
const promptInput = document.querySelector("#prompt");
const imageInput = document.querySelector("#image");
const imageName = document.querySelector("#image-name");
const imagePreview = document.querySelector("#image-preview");
const imagePreviewImg = document.querySelector("#image-preview-img");
const removeImageButton = document.querySelector("#remove-image");
const knowledgeInput = document.querySelector("#use-knowledge");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send");
const micButton = document.querySelector("#mic");
const cameraButton = document.querySelector("#camera");
const snapButton = document.querySelector("#snap");
const cameraPanel = document.querySelector("#camera-panel");
const cameraPreview = document.querySelector("#camera-preview");
const mediaStatus = document.querySelector("#media-status");
const newChatButton = document.querySelector("#new-chat");
const menuButton = document.querySelector("#menu-button");

const ICONS = {
  listen: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15 9a5 5 0 0 1 0 6m3-9a9 9 0 0 1 0 12"/></svg>',
  mic: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 18v3m-4 0h8"/></svg>',
  camera: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8h3l1.5-2h7L17 8h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>',
};

if (tokenInput) tokenInput.value = localStorage.getItem("medical-chat-token") || "";
let selectedImage = null;
let cameraStream = null;
let recognition = null;

function addMessage(role, text, { listen = false, image = null } = {}) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const body = document.createElement("p");
  body.textContent = text;
  if (image && role === "user") {
    const thumbnail = document.createElement("img");
    thumbnail.className = "message-image";
    thumbnail.src = image;
    thumbnail.alt = "Image attached to your message";
    article.append(thumbnail);
  }
  article.append(body);
  if (role === "assistant" && listen && "speechSynthesis" in window) {
    const listenButton = document.createElement("button");
    listenButton.type = "button";
    listenButton.className = "listen-button";
    listenButton.setAttribute("aria-label", "Listen to response");
    listenButton.innerHTML = `${ICONS.listen}<span>Listen</span>`;
    listenButton.addEventListener("click", () => {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = document.documentElement.lang || "en";
      window.speechSynthesis.speak(utterance);
    });
    article.append(listenButton);
  }
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

newChatButton.addEventListener("click", () => {
  conversation.length = 0;
  messages.replaceChildren();
  const welcome = document.createElement("div");
  const mark = document.createElement("div");
  mark.className = "welcome-mark";
  const markImage = document.createElement("img");
  markImage.src = "/static/medical-icon.svg";
  markImage.alt = "";
  mark.append(markImage);
  const heading = document.createElement("h1");
  heading.textContent = "What would you like to understand?";
  const kicker = document.createElement("p");
  kicker.className = "welcome-kicker";
  kicker.textContent = "A thoughtful health companion";
  const description = document.createElement("p");
  description.textContent = "Ask a health question, share an image, or explore your medical reference.";
  welcome.className = "welcome";
  const suggestionButtons = document.createElement("div");
  suggestionButtons.className = "suggestions";
  [
    ["Questions to ask your doctor", "What questions should I ask my doctor about a new medication?"],
    ["Track a symptom", "What information is helpful to track when I have a headache?"],
    ["Understand a health topic", "Explain this health topic in simple terms: "],
  ].forEach(([label, prompt]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.prompt = prompt;
    button.textContent = label;
    suggestionButtons.append(button);
  });
  welcome.append(mark, kicker, heading, description, suggestionButtons);
  messages.append(welcome);
  clearImage();
  promptInput.value = "";
  resizePrompt();
  mediaStatus.textContent = "";
  document.body.classList.remove("sidebar-open");
  promptInput.focus();
});

messages.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-prompt]");
  if (!button) return;
  promptInput.value = button.dataset.prompt;
  promptInput.focus();
  promptInput.setSelectionRange(promptInput.value.length, promptInput.value.length);
});

menuButton.addEventListener("click", () => {
  document.body.classList.toggle("sidebar-open");
});

function resizePrompt() {
  promptInput.style.height = "auto";
  promptInput.style.height = `${Math.min(promptInput.scrollHeight, 180)}px`;
}

promptInput.addEventListener("input", resizePrompt);

promptInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

function showImage(dataUrl, name) {
  selectedImage = dataUrl;
  imagePreviewImg.src = dataUrl;
  imagePreview.hidden = false;
  imageName.textContent = name;
}

function clearImage() {
  selectedImage = null;
  imagePreviewImg.removeAttribute("src");
  imagePreview.hidden = true;
  imageInput.value = "";
  imageName.textContent = "";
}

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    addMessage("error", "Please select an image file.");
    clearImage();
    return;
  }
  if (file.size > 4 * 1024 * 1024) {
    addMessage("error", "Images must be smaller than 4 MB.");
    clearImage();
    return;
  }
  const reader = new FileReader();
  reader.onload = () => showImage(reader.result, file.name);
  reader.onerror = () => {
    addMessage("error", "Could not read the selected image.");
    clearImage();
  };
  reader.readAsDataURL(file);
});

removeImageButton.addEventListener("click", clearImage);

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
  cameraPreview.srcObject = null;
  cameraPanel.hidden = true;
  cameraButton.innerHTML = ICONS.camera;
  cameraButton.title = "Use camera";
  cameraButton.setAttribute("aria-label", "Use camera");
  snapButton.disabled = true;
}

cameraButton.addEventListener("click", async () => {
  if (cameraStream) {
    stopCamera();
    mediaStatus.textContent = "Camera stopped.";
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    mediaStatus.textContent = "Camera access requires HTTPS or localhost and a supported browser.";
    return;
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
      audio: false,
    });
    cameraPreview.srcObject = cameraStream;
    cameraPanel.hidden = false;
    cameraButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
    cameraButton.title = "Stop camera";
    cameraButton.setAttribute("aria-label", "Stop camera");
    snapButton.disabled = false;
    mediaStatus.textContent = "Camera ready. Take a snapshot when ready.";
  } catch (error) {
    mediaStatus.textContent = error.name === "NotAllowedError"
      ? "Camera permission was denied."
      : "Could not start the camera. Check that it is available and permitted.";
  }
});

snapButton.addEventListener("click", () => {
  if (!cameraStream || !cameraPreview.videoWidth) {
    mediaStatus.textContent = "Wait for the camera preview, then try again.";
    return;
  }
  const maxDimension = 1280;
  const scale = Math.min(1, maxDimension / Math.max(cameraPreview.videoWidth, cameraPreview.videoHeight));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(cameraPreview.videoWidth * scale);
  canvas.height = Math.round(cameraPreview.videoHeight * scale);
  canvas.getContext("2d").drawImage(cameraPreview, 0, 0, canvas.width, canvas.height);
  const dataUrl = canvas.toDataURL("image/jpeg", 0.82);
  if (dataUrl.length > 5_500_000) {
    mediaStatus.textContent = "Snapshot is too large to send. Move closer or use a lower-resolution camera.";
    return;
  }
  showImage(dataUrl, "Camera snapshot");
  stopCamera();
  mediaStatus.textContent = "Snapshot attached. Add a question and send it.";
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
  micButton.disabled = true;
  micButton.title = "Speech recognition is not supported in this browser.";
} else {
  recognition = new SpeechRecognition();
  recognition.lang = document.documentElement.lang || "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.addEventListener("start", () => {
    micButton.innerHTML = `${ICONS.mic}<span class="sr-only">Listening</span>`;
    micButton.classList.add("is-listening");
    mediaStatus.textContent = "Speak now.";
  });
  recognition.addEventListener("result", (event) => {
    const transcript = event.results[0][0].transcript.trim();
    promptInput.value = [promptInput.value.trim(), transcript].filter(Boolean).join(" ");
    promptInput.focus();
    mediaStatus.textContent = "Dictation added to your message.";
  });
  recognition.addEventListener("error", (event) => {
    mediaStatus.textContent = event.error === "not-allowed"
      ? "Microphone permission was denied."
      : `Microphone error: ${event.error}.`;
  });
  recognition.addEventListener("end", () => {
    micButton.innerHTML = ICONS.mic;
    micButton.classList.remove("is-listening");
  });
  micButton.addEventListener("click", () => {
    try {
      recognition.start();
    } catch (error) {
      mediaStatus.textContent = "Microphone is already listening.";
    }
  });
}

window.addEventListener("pagehide", () => {
  stopCamera();
  if (recognition) recognition.abort();
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = promptInput.value.trim();
  if ((!text && !selectedImage) || sendButton.disabled) {
    if (!text && !selectedImage) mediaStatus.textContent = "Enter a question or attach an image first.";
    return;
  }

  sendButton.disabled = true;
  const messageText = text || "Please describe this image.";
  addMessage("user", text || "Please describe this image.", { image: selectedImage });
  const pendingMessages = [...conversation, { role: "user", content: messageText }];

  try {
    const token = tokenInput?.value.trim() || "";
    if (token) localStorage.setItem("medical-chat-token", token);
    else localStorage.removeItem("medical-chat-token");
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        messages: pendingMessages,
        image: selectedImage,
        use_knowledge: knowledgeInput.checked,
      }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("Remote access requires a valid bearer token. For local use, open this app at 127.0.0.1 or localhost.");
      }
      throw new Error(result.detail || `Request failed (${response.status}).`);
    }

    addMessage("assistant", result.reply, { listen: true });
    conversation.push({ role: "user", content: messageText }, { role: "assistant", content: result.reply });
    promptInput.value = "";
    clearImage();
    mediaStatus.textContent = "";
  } catch (error) {
    addMessage("error", error.message);
  } finally {
    sendButton.disabled = false;
    promptInput.focus();
  }
});