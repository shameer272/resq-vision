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
