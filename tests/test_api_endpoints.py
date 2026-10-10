import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "gemma-4" in data["model"]

@pytest.mark.anyio
async def test_demo_scenarios_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/demo-scenarios")
        assert response.status_code == 200
        demos = response.json()
        assert len(demos) == 4
        assert demos[0]["badge"] == "DEMO SCENARIO"

@pytest.mark.anyio
async def test_evaluation_suite_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/evaluation")
        assert response.status_code == 200
        metrics = response.json()
        assert metrics["total_scenarios_evaluated"] == 20
        assert metrics["schema_validation_success_rate"] >= 0.95
        assert metrics["tool_call_success_rate"] >= 0.95

@pytest.mark.anyio
async def test_translation_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/translate", json={
            "text": "Road accident with smoke",
            "target_language": "te",
            "incident_data": {
                "incident_type": "road_accident",
                "incident_summary": "Two vehicles collided",
                "observations": [{"description": "Damaged car", "source": "observed"}],
                "potential_concerns": []
            }
        })
        assert response.status_code == 200
        res = response.json()
        assert res["target_language"] == "te"
        assert "Telugu" in res["language_display"]

@pytest.mark.anyio
async def test_missing_google_api_key_returns_clear_error():
    """Verifies that missing Gemini API key returns clean 503 error with actionable message."""
    from app.core.config import settings
    orig_key = settings.GEMINI_API_KEY
    orig_provider = settings.AI_PROVIDER
    try:
        settings.GEMINI_API_KEY = ""
        settings.AI_PROVIDER = "google"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            fake_img = (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00", "image/jpeg")
            files = {"image": ("test.jpg", fake_img[0], fake_img[1])}
            response = await client.post("/api/analyze", files=files, data={"user_text": "Accident on highway"})
            assert response.status_code == 503
            data = response.json()
            assert "Gemini API key is not configured" in data["detail"]
    finally:
        settings.GEMINI_API_KEY = orig_key
        settings.AI_PROVIDER = orig_provider

@pytest.mark.anyio
async def test_missing_do_token_returns_clear_error_when_do_requested():
    """Verifies that requesting DigitalOcean without token returns clean 503 error."""
    from app.core.config import settings
    orig_token = settings.DO_INFERENCE_TOKEN
    try:
        settings.DO_INFERENCE_TOKEN = ""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            fake_img = (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00", "image/jpeg")
            files = {"image": ("test.jpg", fake_img[0], fake_img[1])}
            response = await client.post(
                "/api/analyze",
                files=files,
                data={"user_text": "Accident", "provider": "digitalocean"}
            )
            assert response.status_code == 503
            data = response.json()
            assert "DigitalOcean Inference token is not configured" in data["detail"]
    finally:
        settings.DO_INFERENCE_TOKEN = orig_token

