import os
from pydantic import model_validator, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

_ROOT_ENV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

def is_vercel_environment() -> bool:
    """Checks if currently executing in Vercel or AWS Lambda serverless function environment."""
    return bool(
        os.environ.get("VERCEL")
        or os.environ.get("VERCEL_ENV")
        or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("NOW_REGION")
    )

def resolve_storage_dir(configured_dir: Optional[str] = None) -> str:
    """
    Determines the appropriate writable storage directory.
    - On Vercel / serverless: Returns '/tmp/resq-vision' because the root filesystem is strictly read-only.
    - On local development: Preserves local 'data/storage' directory or explicitly configured path.
    """
    if is_vercel_environment():
        if not configured_dir or not configured_dir.startswith("/tmp"):
            return "/tmp/resq-vision"
        return configured_dir

    if configured_dir:
        return os.path.abspath(configured_dir)

    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "storage")
    )

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
    LOCAL_STORAGE_DIR: str = Field(
        default="",
        validation_alias=AliasChoices("LOCAL_STORAGE_DIR", "STORAGE_DIR")
    )
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://resq-vision-alpha.vercel.app",
        "https://resq-vision-71gv.vercel.app"
    ]

    @model_validator(mode="after")
    def validate_storage_paths(self):
        self.LOCAL_STORAGE_DIR = resolve_storage_dir(self.LOCAL_STORAGE_DIR)
        return self


settings = Settings()

def ensure_storage_directories(target_dir: Optional[str] = None) -> bool:
    """
    Safely creates required directories with error-handling.
    Guarantees the application will never crash at import time on read-only serverless filesystems.
    """
    directory = target_dir or settings.LOCAL_STORAGE_DIR
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except OSError as err:
        print(f"[Config] Notice: Could not create directory '{directory}': {err}")
        if is_vercel_environment() and directory != "/tmp/resq-vision":
            try:
                os.makedirs("/tmp/resq-vision", exist_ok=True)
                settings.LOCAL_STORAGE_DIR = "/tmp/resq-vision"
                return True
            except OSError:
                pass
        return False

# Attempt safe directory setup at initialization without raising unhandled exceptions
ensure_storage_directories(settings.LOCAL_STORAGE_DIR)

try:
    if not os.path.exists(settings.KNOWLEDGE_BASE_DIR):
        os.makedirs(settings.KNOWLEDGE_BASE_DIR, exist_ok=True)
except OSError:
    pass

