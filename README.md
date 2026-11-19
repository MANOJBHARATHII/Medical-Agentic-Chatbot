# 🩺 Care Companion — Medical Agentic Chatbot

> A thoughtful health companion. Ask a health question, share an image, or explore your medical reference.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-black.svg)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Powered_by-Groq-orange.svg)](https://groq.com/)
[![Pinecone](https://img.shields.io/badge/Vector_DB-Pinecone-teal.svg)](https://www.pinecone.io/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

**Live Demo:** Coming Soon on Render • **Author:** MANOJBHARATHII

---

## ✨ What is this?

Care Companion is not a normal chatbot. It is an **Agentic AI** system.

You ask a question → The Agent thinks → It decides whether to:
1. Search your **Medical Knowledge Base**
2. Search the **Live Web** for latest info
3. Analyze your **Uploaded Image**
4. Or just answer directly

Then it gives a safe, clear, cited answer. Not a diagnosis — but a thoughtful explanation to help you understand and talk to your doctor.

![App Screenshot](https://via.placeholder.com/900x450?text=Care+Companion+-+What+would+you+like+to+understand%3F)

---

## 🚀 Features

### 💬 Smart Medical Chat
- Natural, ChatGPT-style chat UI
- Multi-turn conversation with memory — it remembers your previous questions
- Quick actions: `Questions to ask your doctor` / `Track a symptom` / `Understand a health topic`
- New Chat + Chat History in sidebar

### 🧠 Agentic Workflow with LangGraph
- Built on **LangGraph** — the agent routes your query intelligently
- **KB Node:** Searches Pinecone vector DB for trusted medical docs
- **Web Node:** Searches live web via **Tavily** for latest guidelines
- **Answer Node:** Synthesizes KB + Web + History into one clean answer
- Shows `ROUTE:` — so you know where the answer came from

### 🖼️ Medical Image Analysis
- Upload a photo — skin rash, report, prescription, X-ray, etc.
- **Qwen Vision Model on Groq** describes the image
- Agent combines image description + your question to answer
- Preview with `Selected image` before sending

### 📚 Reference Mode
- Tick `Reference` in chat box to force Knowledge Base search
- Perfect for studying a health topic from your own documents

### 🔒 Security Built-in
- **Bearer Token Auth** — Remote access settings in sidebar
- **HMAC Signature Verification** for requests
- **IP Allowlist** — only trusted IPs can access API
- `.env` based secrets — no keys in code

### ⚡ Super Fast
- Powered by **Groq** — `qwen/qwen3-8-27b` for chat + vision
- Sub-second LLM responses, even with RAG

---

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| **Frontend** | HTML, CSS, Vanilla JS |
| **Backend** | FastAPI, Uvicorn, Python |
| **Agent** | LangGraph, LangChain |
| **LLM** | Groq - Qwen Qwen3-8-27b |
| **Vector DB** | Pinecone |
| **Web Search** | Tavily API |
| **Security** | HMAC, Bearer Token, IP Allowlist |

---

## 🏗️ How It Works

```mermaid
User Question / Image
        ↓
[ FastAPI Backend ]
        ↓
[ LangGraph Agent ]
   ↙      ↘       ↘
[KB Search] [Web Search] [Image Analysis]
  Pinecone    Tavily       Groq Vision
        ↓
[ Answer Synthesis - Groq LLM ]
        ↓
Clean Answer + Route + Sources
