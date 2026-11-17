const conversation = [];
const tokenInput = document.querySelector("#api-token");
const form = document.querySelector("#chat-form");
const promptInput = document.querySelector("#prompt");
const imageInput = document.querySelector("#image");
const imageName = document.querySelector("#image-name");
const knowledgeInput = document.querySelector("#use-knowledge");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send");

tokenInput.value = localStorage.getItem("medical-chat-token") || "";

function addMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const label = document.createElement("strong");
  label.textContent = role === "user" ? "You" : "Assistant";
  const body = document.createElement("p");
  body.textContent = text;
  article.append(label, body);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

imageInput.addEventListener("change", () => {
  imageName.textContent = imageInput.files[0]?.name || "";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = promptInput.value.trim();
  const file = imageInput.files[0];
  if (!text || sendButton.disabled) return;
  if (file && !file.type.startsWith("image/")) {
    addMessage("error", "Please select an image file.");
    return;
  }
  if (file && file.size > 4 * 1024 * 1024) {
    addMessage("error", "Images must be smaller than 4 MB.");
    return;
  }

  sendButton.disabled = true;
  addMessage("user", text + (file ? `\n[Image: ${file.name}]` : ""));
  const pendingMessages = [...conversation, { role: "user", content: text }];
  const image = file
    ? await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error("Could not read the selected image."));
        reader.readAsDataURL(file);
      }).catch((error) => {
        addMessage("error", error.message);
        return null;
      })
    : null;

  if (file && !image) {
    sendButton.disabled = false;
    return;
  }

  try {
    localStorage.setItem("medical-chat-token", tokenInput.value.trim());
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${tokenInput.value.trim()}`,
      },
      body: JSON.stringify({
        messages: pendingMessages,
        image,
        use_knowledge: knowledgeInput.checked,
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || `Request failed (${response.status}).`);

    addMessage("assistant", result.reply);
    conversation.push({ role: "user", content: text }, { role: "assistant", content: result.reply });
    promptInput.value = "";
    imageInput.value = "";
    imageName.textContent = "";
  } catch (error) {
    addMessage("error", error.message);
  } finally {
    sendButton.disabled = false;
    promptInput.focus();
  }
});