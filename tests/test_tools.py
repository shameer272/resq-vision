import os
import pytest
from app.tools.incident_tools import incident_tools
from app.agent.agent_service import agent_service

SAMPLE_INCIDENT = {
    "incident_id": "TEST-INC-001",
    "timestamp": "2026-10-01T12:00:00Z",
    "incident_type": "road_accident",
    "incident_summary": "Two sedans collided on Gachibowli flyover with traffic blocked.",
    "location": "Gachibowli Flyover, Hyderabad",
    "observations": [
        {
            "description": "Front bumper crushed on silver sedan",
            "source": "observed",
            "confidence": "high",
            "evidence": "Visible metal deformation"
        }
    ],
    "user_reported_information": ["Smoke observed by bystander"],
    "potential_concerns": [
        {
            "concern": "Traffic pileup hazard",
            "reason": "Vehicle blocking fast lane",
            "evidence": "Car positioned across lane",
            "confidence": "high",
            "requires_human_verification": True
        }
    ],
    "uncertainties": ["Exact passenger injuries unverified"],
    "missing_information": ["Fuel leak presence"],
    "recommended_information_to_communicate": ["Alert Cyberabad Traffic Police"],
    "safety_disclaimer": "Human verification required."
}

def test_generate_incident_report():
    res = incident_tools.generate_incident_report(SAMPLE_INCIDENT)
    assert res["status"] == "success"
    report = res["report"]
    assert "METHANE" in str(report.keys()) or "methane_structure" in report
    assert report["methane_structure"]["T - Type of Incident"] == "Road Accident"

def test_generate_responder_checklist():
    res = incident_tools.generate_responder_checklist(SAMPLE_INCIDENT)
    items = res["checklist_items"]
    assert len(items) >= 4
    labels = [i["label"] for i in items]
    assert any("Geolocation" in l for l in labels)
    assert any("Traffic pileup" in l for l in labels)

def test_get_location_context():
    res = incident_tools.get_location_context("Gachibowli, Hyderabad")
    assert "Cyberabad" in str(res)
    assert res["is_demo_data"] is False

def test_pdf_export_generation():
    res = incident_tools.export_report(SAMPLE_INCIDENT, format_type="pdf")
    assert res["status"] == "success"
    assert os.path.exists(res["filepath"])

def test_retrieve_safety_guidance():
    res = incident_tools.retrieve_safety_guidance("collision on road", "road_accident")
    assert res["citations_found"] > 0
    assert len(res["sources"]) > 0

def test_save_incident():
    res = incident_tools.save_incident(SAMPLE_INCIDENT)
    assert res["status"] == "success"
    assert "incident_id" in res

def test_translate_report_tool():
    res = incident_tools.translate_report(SAMPLE_INCIDENT, target_language="te")
    assert res["status"] == "success"
    assert res["target_language"] == "te"
    assert "Telugu" in res["language_display"]

@pytest.mark.anyio
async def test_agent_workflow_orchestration():
    res = await agent_service.run_agentic_workflow(
        SAMPLE_INCIDENT,
        requested_goals=["location_context", "safety_guidance", "checklist", "report", "translate", "save", "export"]
    )
    assert res["incident_id"] == "TEST-INC-001"
    assert len(res["execution_trace"]) >= 5
    assert "report" in res["tool_outputs"]
    assert "checklist" in res["tool_outputs"]
