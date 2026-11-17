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

    OPENAI_API_KEY: str 
    PINECONE_API_KEY: str
    TAVILY_API_KEY: str
    PINECONE_INDEX: str = "medical-agent-demo"
    OPENAI_CHAT_MODEL: str = "gpt-4.1-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    OPENAI_VISION_MODEL: str = "gpt-4.1-vision"
    API_TOKEN: str 
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

settings = Settings()
