import os
import sys
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.schemas.incident import IncidentAnalysisResponse, Observation, PotentialConcern, RAGSource
from app.ai.gemma_service import GemmaServiceError

@pytest.mark.anyio
async def test_local_evaluation_endpoint_still_works():
    """1. Local regression benchmark GET /api/evaluation works and returns 20 scenarios."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/evaluation")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scenarios_evaluated"] == 20
        assert data["schema_validation_success_rate"] >= 0.95
        assert data["average_latency_seconds"] < 0.1

@pytest.mark.anyio
async def test_live_evaluation_endpoint_exists_and_validates():
    """2 & 3. Live evaluation endpoint exists, accepts scenario selection count and IDs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test options or post structure with mocked gemma call
        fake_response = IncidentAnalysisResponse(
            incident_id="RESQ-TEST-001",
            timestamp="2026-10-03T12:00:00Z",
            location="Route 101",
            incident_summary="Two vehicle collision with roadway blockage",
            incident_type="road_accident",
            observations=[
                Observation(description="Front bumper damage", source="observed", confidence="high", evidence="Crumpled front grill")
            ],
            potential_concerns=[
                PotentialConcern(concern="Thermal hazard", reason="Radiator fluid leak", evidence="Fluid on road", confidence="medium", requires_human_verification=True)
            ],
            safety_disclaimer="Decision support only. Human verification required.",
            rag_sources=[RAGSource(id="RAG-1", title="Highway Safety", source="DOT", relevance_snippet="Clear lane", category="road_accident")],
            model_used="gemma-4-31b-it",
            primary_model="gemma-4-31b-it",
            inference_time_seconds=3.456,
            status="analyzed"
        )

        with patch("app.services.evaluation_service.gemma_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = fake_response
            response = await client.post("/api/evaluation/live", json={"count": 2})
            assert response.status_code == 200
            data = response.json()
            assert data["model_name"] == "Gemma 4 31B IT"
            assert data["model_id"] == "gemma-4-31b-it"
            assert data["scenarios_executed"] == 2
            assert data["successful_calls"] == 2
            assert data["failed_calls"] == 0
            assert data["schema_compliance_rate"] == 1.0
            assert data["required_field_completion_rate"] == 1.0
            assert data["evidence_completion_rate"] == 1.0
            assert data["average_inference_latency_seconds"] == 3.456
            assert len(data["scenario_results"]) == 2
            assert data["scenario_results"][0]["gemma_status"] == "passed"
            assert data["scenario_results"][0]["inference_latency_sec"] == 3.456
            assert mock_analyze.call_count == 2

@pytest.mark.anyio
async def test_live_evaluation_scenario_ids_selection():
    """3. Specific scenario_ids can be requested."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_response = IncidentAnalysisResponse(
            incident_id="RESQ-TEST-002",
            timestamp="2026-10-03T12:00:00Z",
            location="Banjara Hills",
            incident_summary="Downed electric utility pole",
            incident_type="blocked_road",
            observations=[Observation(description="Pole down", source="observed", confidence="high", evidence="Tree on wires")],
            potential_concerns=[PotentialConcern(concern="Electrocution risk", reason="Live lines", evidence="Wires on road", confidence="high", requires_human_verification=True)],
            safety_disclaimer="Safety notice",
            rag_sources=[RAGSource(id="RAG-2", title="Electric Safety", source="OSHA", relevance_snippet="High voltage", category="blocked_road")],
            model_used="gemma-4-31b-it",
            primary_model="gemma-4-31b-it",
            inference_time_seconds=2.85,
            status="analyzed"
        )

        with patch("app.services.evaluation_service.gemma_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = fake_response
            response = await client.post("/api/evaluation/live", json={"scenario_ids": ["SCEN-09"]})
            assert response.status_code == 200
            data = response.json()
            assert data["scenarios_executed"] == 1
            assert data["scenario_results"][0]["id"] == "SCEN-09"
            assert data["scenario_results"][0]["category"] == "blocked_road"
            assert mock_analyze.call_count == 1

@pytest.mark.anyio
async def test_live_evaluation_reports_failure_honestly():
    """6 & 7. Failed Gemma calls are reported as failures without synthetic substitution."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.services.evaluation_service.gemma_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = GemmaServiceError("Google API 429: Resource has been exhausted (rate limit)")
            response = await client.post("/api/evaluation/live", json={"count": 1})
            assert response.status_code == 200
            data = response.json()
            assert data["scenarios_executed"] == 1
            assert data["successful_calls"] == 0
            assert data["failed_calls"] == 1
            assert data["schema_compliance_rate"] == 0.0
            assert data["required_field_completion_rate"] == 0.0
            scen_res = data["scenario_results"][0]
            assert scen_res["gemma_status"] in ("error", "failed")
            assert scen_res["schema_valid"] is False
            assert "429" in scen_res["error_message"]
            # Verify no synthetic payload was substituted
            assert scen_res["fields_complete"] is False

@pytest.mark.anyio
async def test_api_key_not_exposed_in_evaluation():
    """9. API key is never exposed to the frontend in evaluation responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.get("/api/evaluation")
        assert "api_key" not in res1.text
        assert "AIza" not in res1.text
        assert "AQ." not in res1.text

        with patch("app.services.evaluation_service.gemma_service.analyze_multimodal", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = IncidentAnalysisResponse(
                incident_id="RESQ-TEST-003",
                timestamp="2026-10-03T12:00:00Z",
                incident_summary="Test incident",
                incident_type="road_accident",
                observations=[],
                potential_concerns=[],
                safety_disclaimer="Safety notice",
                model_used="gemma-4-31b-it",
                primary_model="gemma-4-31b-it",
                inference_time_seconds=1.23,
                status="analyzed"
            )
            res2 = await client.post("/api/evaluation/live", json={"count": 1})
            assert "api_key" not in res2.text
            assert "AIza" not in res2.text
            assert "AQ." not in res2.text
