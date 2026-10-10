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

def test_validate_incident_inputs():
    # Valid input with 1 image
    res = incident_tools.validate_incident_inputs(
        user_text="Smoke coming from engine bay after collision",
        location="ORR Exit 12",
        image_count=1,
        file_sizes_bytes=[1024 * 500],
        mime_types=["image/jpeg"]
    )
    assert res["is_valid"] is True
    assert len(res["issues"]) == 0

    # Invalid input: 0 images
    res_zero = incident_tools.validate_incident_inputs(image_count=0)
    assert res_zero["is_valid"] is False
    assert any("image is required" in iss for iss in res_zero["issues"])

def test_classify_incident_support():
    res_road = incident_tools.classify_incident_support("Two sedans had a head-on collision at the intersection with shattered glass")
    assert res_road["predicted_type"] == "road_accident"
    assert res_road["confidence"] in ["high", "medium"]

    res_fire = incident_tools.classify_incident_support("Black smoke and fire flames rising from warehouse roof")
    assert res_fire["predicted_type"] == "smoke_fire"

def test_manage_incident_history():
    res_list = incident_tools.manage_incident_history(action="list", limit=5)
    assert res_list["status"] == "success"
    assert "incidents" in res_list

