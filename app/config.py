import os
import certifi
from dotenv import load_dotenv

# ---Audomate SSL Fix for python Environment---

ssl_cert = os.environ.get('SSL_CERT_FILE')
if ssl_cert and not os.path.exists(ssl_cert):
    os.environ['SSL_CERT_FILE'] = certifi.where()
elif not ssl_cert:
    os.environ['SSL_CERT_FILE'] = certifi.where()
#----------------------------------------------------
load_dotenv()
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    GROQ_API_KEY: str
    PINECONE_API_KEY: str
    TAVILY_API_KEY: str
    PINECONE_INDEX: str = "medical-agent-local-embeddings"
    LOCAL_EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    GROQ_CHAT_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_VISION_MODEL: str = "qwen/qwen3.8-27b"
    API_TOKEN: str
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    @property
    def chat_model(self) -> str:
        return self.GROQ_CHAT_MODEL

    @property
    def vision_model(self) -> str:
        return self.GROQ_VISION_MODEL

settings = Settings()
