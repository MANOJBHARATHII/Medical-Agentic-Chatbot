import hmac
import ipaddress
import logging
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from groq import APIError

from app.agent import respond
from app.config import settings


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Medical Information Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "static"), name="static")

bearer_scheme = HTTPBearer(auto_error=False)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)
    image: str | None = Field(default=None, max_length=6_000_000)
    use_knowledge: bool = True


def require_api_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    client_host = request.client.host if request.client else ""
    try:
        if ipaddress.ip_address(client_host).is_loopback:
            return
    except ValueError:
        pass

    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not hmac.compare_digest(credentials.credentials, settings.API_TOKEN)
    ):
        raise HTTPException(status_code=401, detail="A valid bearer token is required.")


@app.get("/")
def home():
    return FileResponse(PROJECT_ROOT / "templates" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "provider": "groq"}


@app.post("/api/chat", dependencies=[Depends(require_api_token)])
def chat(request: ChatRequest):
    if request.image:
        if not request.image.startswith("data:image/") or ";base64," not in request.image:
            raise HTTPException(status_code=400, detail="Image must be a base64-encoded data URL.")
        if not any(message.role == "user" for message in request.messages):
            raise HTTPException(status_code=400, detail="An image must accompany a user message.")

    messages = [message.model_dump() for message in request.messages]
    try:
        answer = respond(
            messages,
            image_url=request.image,
            use_knowledge=request.use_knowledge,
        )
    except APIError as exc:
        logger.error(
            "Groq request failed with HTTP %s: %s",
            exc.status_code,
            exc.message,
        )
        if exc.status_code in (401, 403):
            detail = "Groq rejected the API key. Check GROQ_API_KEY."
        elif exc.status_code == 404:
            detail = "The configured Groq model is unavailable. Check GROQ_CHAT_MODEL and GROQ_VISION_MODEL."
        elif exc.status_code == 429:
            detail = "Groq rate limit or usage quota reached. Try again later or check your Groq account limits."
        elif exc.status_code == 400:
            detail = f"Groq rejected the request: {exc.message}"
        else:
            detail = f"Groq request failed (HTTP {exc.status_code})."
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"reply": answer, "provider": "groq"}