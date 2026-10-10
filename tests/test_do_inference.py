import json
import pytest
import httpx
from unittest.mock import patch, AsyncMock
from app.core.config import settings
from app.ai.do_inference_service import (
    DigitalOceanInferenceService,
    DOAuthKeyMissingError,
    DOInferenceServiceError
)
from app.ai import get_ai_service, gemma_service, do_inference_service

SAMPLE_DO_RESPONSE_JSON = {
    "incident_summary": "Two-vehicle traffic accident with vehicle crush deformation and road obstruction.",
    "incident_type": "road_accident",
    "observations": [
        {
            "description": "Front crumple deformation on blue passenger sedan",
            "source": "observed",
            "confidence": "high",
            "evidence": "Observed severe bumper damage and hood buckle"
        }
    ],
    "user_reported_information": ["Bystander reported collision at intersection"],
    "potential_concerns": [
        {
            "concern": "Radiator fluid leak creates slippery road hazard",
            "reason": "Fluid may cause secondary skidding",
            "evidence": "Dark fluid pooled near tire line",
            "confidence": "medium",
            "requires_human_verification": True
        }
    ],
    "uncertainties": ["Internal vehicle passenger injuries unknown"],
    "missing_information": ["Exact number of vehicle occupants"],
    "recommended_information_to_communicate": ["Location and presence of fluid spill"],
    "confidence_notes": ["Good lighting, front angle clearly visible"],
    "safety_disclaimer": "AI decision support. Human verification required."
}

def test_service_factory_provider_selection():
    """Verifies that get_ai_service returns the correct service instance."""
    # Explicit google
    svc_google = get_ai_service("google")
    assert svc_google is gemma_service

    # Explicit digitalocean
    svc_do = get_ai_service("digitalocean")
    assert svc_do is do_inference_service

    # Case insensitive
    svc_do_caps = get_ai_service("DigitalOcean")
    assert svc_do_caps is do_inference_service

def test_do_service_missing_token_raises():
    """Verifies that missing DO token raises DOAuthKeyMissingError."""
    original_token = settings.DO_INFERENCE_TOKEN
    try:
        settings.DO_INFERENCE_TOKEN = ""
        service = DigitalOceanInferenceService()
        with pytest.raises(DOAuthKeyMissingError) as exc_info:
            service._get_token()
        assert "DO_INFERENCE_TOKEN" in str(exc_info.value)
    finally:
        settings.DO_INFERENCE_TOKEN = original_token

def test_do_transient_error_detection():
    """Verifies that transient errors (429, 500, 503, timeouts) are properly detected."""
    service = DigitalOceanInferenceService()
    assert service._is_transient_error(429, "Too Many Requests") is True
    assert service._is_transient_error(503, "Service Unavailable") is True
    assert service._is_transient_error(500, "Internal Server Error") is True
    assert service._is_transient_error(200, "OK") is False
    assert service._is_transient_error(400, "Bad Request") is False
    assert service._is_transient_error(401, "Unauthorized") is False

def test_do_user_content_preparation():
    """Verifies image and text payload formatting for OpenAI-compatible vision."""
    service = DigitalOceanInferenceService()
    
    # Text-only
    text_content = service._prepare_user_content("Hello emergency scene", [])
    assert text_content == "Hello emergency scene"

    # Multimodal with image
    fake_img = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
    mm_content = service._prepare_user_content("Check scene", [(fake_img, "image/jpeg")])
    assert isinstance(mm_content, list)
    assert len(mm_content) == 2
    assert mm_content[0]["type"] == "text"
    assert mm_content[1]["type"] == "image_url"
    assert "data:image/jpeg;base64," in mm_content[1]["image_url"]["url"]

@pytest.mark.anyio
async def test_do_inference_successful_mock():
    """Verifies end-to-end multimodal analysis execution via DigitalOcean mock."""
    original_token = settings.DO_INFERENCE_TOKEN
    try:
        settings.DO_INFERENCE_TOKEN = "do-test-mock-token-xyz"
        service = DigitalOceanInferenceService()

        mock_response_payload = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(SAMPLE_DO_RESPONSE_JSON)
                    }
                }
            ]
        }

        mock_http_response = httpx.Response(
            status_code=200,
            json=mock_response_payload,
            request=httpx.Request("POST", "https://inference.do-ai.run/v1/chat/completions")
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_http_response

            fake_img = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
            result = await service.analyze_multimodal(
                images=[(fake_img, "image/jpeg")],
                user_text="Two cars crashed at the junction",
                location="Intersection 5th and Main"
            )

            assert result.status == "analyzed"
            assert result.incident_type == "road_accident"
            assert len(result.observations) >= 1
            assert result.observations[0].evidence != ""
            assert result.primary_model == service.model_name
            assert result.fallback_used is False
            assert "informational aid" in result.safety_disclaimer.lower()
            assert len(result.action_trace) >= 4
    finally:
        settings.DO_INFERENCE_TOKEN = original_token

@pytest.mark.anyio
async def test_do_inference_fallback_on_429():
    """Verifies that a 429 transient capacity error gracefully falls back to DO_FALLBACK_MODEL."""
    original_token = settings.DO_INFERENCE_TOKEN
    try:
        settings.DO_INFERENCE_TOKEN = "do-test-mock-token-xyz"
        service = DigitalOceanInferenceService()

        # First call returns 429, second returns 200
        resp_429 = httpx.Response(
            status_code=429,
            text='{"error": "rate_limit_exceeded"}',
            request=httpx.Request("POST", "https://inference.do-ai.run/v1/chat/completions")
        )
        resp_200 = httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(SAMPLE_DO_RESPONSE_JSON)
                        }
                    }
                ]
            },
            request=httpx.Request("POST", "https://inference.do-ai.run/v1/chat/completions")
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [resp_429, resp_200]

            fake_img = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
            result = await service.analyze_multimodal(
                images=[(fake_img, "image/jpeg")],
                user_text="Crash scene"
            )

            assert result.status == "analyzed"
            assert result.fallback_used is True
            assert result.model_used == service.fallback_model
            assert "429" in result.fallback_reason
    finally:
        settings.DO_INFERENCE_TOKEN = original_token
