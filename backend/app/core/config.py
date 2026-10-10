import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

_ROOT_ENV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=[_ROOT_ENV, ".env"], extra="ignore")

    APP_NAME: str = "ResQ Vision"
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # AI Provider Selection ("google" or "digitalocean")
    AI_PROVIDER: str = "google"

    # Gemma / Gemini AI Settings
    GEMINI_API_KEY: str = ""
    GEMMA_MODEL: str = "gemma-4-31b-it"
    FALLBACK_MODEL: str = "gemma-4-26b-a4b-it"

    # DigitalOcean GenAI Serverless Inference Settings
    DO_INFERENCE_ENDPOINT: str = "https://inference.do-ai.run/v1"
    DO_INFERENCE_TOKEN: str = ""
    DO_MODEL: str = "meta-llama/Meta-Llama-3.2-11B-Vision-Instruct"
    DO_FALLBACK_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct"
    
    # MongoDB Settings
    MONGODB_URI: str = ""
    DATABASE_NAME: str = "resq_vision_db"
    
    # Storage & Upload Limits
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp"]
    
    # Knowledge Base Path
    KNOWLEDGE_BASE_DIR: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "knowledge-base")
    )
    
    # Local Storage Path Fallback
    LOCAL_STORAGE_DIR: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "storage")
    )
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]


settings = Settings()

# Ensure local directories exist
os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
os.makedirs(settings.KNOWLEDGE_BASE_DIR, exist_ok=True)
