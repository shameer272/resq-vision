from typing import Optional
from app.core.config import settings
from app.ai.gemma_service import gemma_service, GemmaService, GemmaServiceError, APIKeyMissingError
from app.ai.do_inference_service import do_inference_service, DigitalOceanInferenceService, DOInferenceServiceError, DOAuthKeyMissingError

def get_ai_service(provider: Optional[str] = None):
    """
    Returns the appropriate AI inference service based on the requested provider or server configuration.
    Supported providers:
    - 'google': Gemma 4 via Google GenAI SDK (default)
    - 'digitalocean': Open-weight foundation models via DigitalOcean GenAI Serverless Inference
    """
    chosen = (provider or settings.AI_PROVIDER or "google").strip().lower()
    if chosen == "digitalocean":
        return do_inference_service
    return gemma_service

__all__ = [
    "gemma_service",
    "do_inference_service",
    "get_ai_service",
    "GemmaService",
    "DigitalOceanInferenceService",
    "GemmaServiceError",
    "APIKeyMissingError",
    "DOInferenceServiceError",
    "DOAuthKeyMissingError"
]
