import os
import sys
import json
import httpx
import pytest

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_PATH = os.path.join(BASE_DIR, "frontend", "public", "demo-assets", "accident.jpg")
if not os.path.exists(IMAGE_PATH):
    IMAGE_PATH = r"c:\Users\Shameer\.gemini\antigravity-ide\scratch\resq-vision\frontend\public\demo-assets\accident.jpg"

TEST_TEXT = "There is a damaged vehicle with visible smoke and the road appears partially blocked."

def is_backend_online():
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get(f"{BACKEND_URL}/health")
            return resp.status_code == 200
    except Exception:
        return False

@pytest.mark.skipif(not is_backend_online(), reason="Backend server is not running at 127.0.0.1:8000")
def test_e2e_complete_live():
    results = {}

    print("=================================================================")
    print("STARTING RESQ VISION COMPLETE END-TO-END TEST SUITE")
    print("=================================================================\n")

    # 1, 2, 3: Verify Health, API Key, Model, Storage
    print("--- [1, 2, 3] Checking Health Endpoint ---")
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{BACKEND_URL}/health")
        assert resp.status_code == 200, f"Health check failed with {resp.status_code}"
        health_data = resp.json()
        print("Health Data:", json.dumps(health_data, indent=2))
        assert health_data["gemini_api_key_configured"] is True, "GEMINI_API_KEY is not configured!"
        assert "gemma-4" in health_data["model"], f"Unexpected model: {health_data['model']}"
        assert health_data["storage_mode"] in ["MongoDB", "Local File Storage"], f"Unexpected storage mode: {health_data['storage_mode']}"
        results["backend_env"] = "PASSED"
        results["model_name"] = health_data["model"]
        results["storage_mode"] = health_data["storage_mode"]

    # 5: Check Frontend (non-blocking if dev server not launched)
    print("\n--- [5] Checking Frontend Availability ---")
    try:
        with httpx.Client(timeout=3.0) as client:
            f_resp = client.get(FRONTEND_URL)
            if f_resp.status_code == 200:
                print(f"Frontend returned 200 OK (HTML bytes: {len(f_resp.content)})")
                results["frontend_status"] = "PASSED"
            else:
                results["frontend_status"] = f"HTTP_{f_resp.status_code}"
    except Exception as fe:
        print(f"Frontend server offline at {FRONTEND_URL} (optional for backend test): {fe}")
        results["frontend_status"] = "OFFLINE"

    # 6-11, 13: Real Multimodal Request with Gemma 4
    print("\n--- [6-11, 13] Executing Real Multimodal Gemma 4 Request ---")
    print(f"Image: {IMAGE_PATH}")
    print(f"Text: '{TEST_TEXT}'")

    with open(IMAGE_PATH, "rb") as img_file:
        img_bytes = img_file.read()

    files = {"image": ("accident.jpg", img_bytes, "image/jpeg")}
    form_data = {
        "user_text": TEST_TEXT,
        "location": "Route 101 Northbound, Mile Marker 42",
        "category": "road_accident",
        "language": "en"
    }

    with httpx.Client(timeout=180.0) as client:
        res = client.post(f"{BACKEND_URL}/api/analyze", files=files, data=form_data)
        assert res.status_code == 200, f"Analysis failed with {res.status_code}: {res.text}"
        analysis = res.json()

    incident_id = analysis["incident_id"]
    print(f"\nAnalysis Succeeded! Incident ID: {incident_id}")
    print(f"Model Used: {analysis['model_used']}")
    print(f"Incident Type: {analysis['incident_type']}")
    print(f"Incident Summary: {analysis['incident_summary']}")

    # Confirm model
    assert analysis["model_used"] in ["gemma-4-31b-it", "gemma-4-26b-a4b-it"], f"Unexpected model: {analysis['model_used']}"
    assert len(analysis["incident_summary"]) > 10, "Summary too short"

    print(f"\nObservations ({len(analysis['observations'])}):")
    sources_found = set()
    for obs in analysis["observations"]:
        src = obs["source"]
        sources_found.add(src)
        print(f"  - [{src.upper()}] (Conf: {obs['confidence']}): {obs['description']}")
        print(f"    Evidence: {obs['evidence']}")

    # Verify provenance distinctions
    print("\nData Provenance Sources Found:", sources_found)
    assert any(s in sources_found for s in ["observed", "user_reported", "inferred"]), "Missing provenance distinctions"

    # Safety disclaimer
    print(f"\nSafety Disclaimer: {analysis['safety_disclaimer']}")
    assert len(analysis["safety_disclaimer"]) > 10, "Safety disclaimer missing!"

    # RAG sources
    print(f"\nRAG Sources Retrieved ({len(analysis['rag_sources'])}):")
    for r in analysis["rag_sources"]:
        print(f"  - Title: {r['title']} ({r['source']}) | Relevance: {r['relevance_snippet'][:80]}...")
    assert len(analysis["rag_sources"]) > 0, "RAG sources missing!"

    results["multimodal_analysis"] = "PASSED"
    results["model_verified"] = analysis["model_used"]

    # Tool: Generate Incident Report (METHANE)
    print("\n--- [15] Testing Tool: Generate Incident Report (METHANE) ---")
    with httpx.Client(timeout=30.0) as client:
        rep_res = client.post(f"{BACKEND_URL}/api/incident/report", json=analysis)
        assert rep_res.status_code == 200, f"Report generation failed: {rep_res.text}"
        report_data = rep_res.json()
        print("METHANE Report ID:", report_data.get("report_id"))
        results["report_tool"] = "PASSED"

    # Tool: Generate Responder Checklist
    print("\n--- [16] Testing Tool: Generate Responder Checklist ---")
    with httpx.Client(timeout=30.0) as client:
        chk_res = client.post(f"{BACKEND_URL}/api/incident/checklist", json=analysis)
        assert chk_res.status_code == 200, f"Checklist generation failed: {chk_res.text}"
        checklist_data = chk_res.json()
        items = checklist_data.get("checklist_items", [])
        assert len(items) > 0, "No checklist items returned!"
        results["checklist_tool"] = "PASSED"

    # Tool: Translation
    print("\n--- [17] Testing Telugu Translation ---")
    with httpx.Client(timeout=120.0) as client:
        trans_payload = {
            "text": analysis.get("incident_summary", ""),
            "incident_data": analysis,
            "target_language": "te"
        }
        trans_res = client.post(f"{BACKEND_URL}/api/translate", json=trans_payload)
        assert trans_res.status_code == 200, f"Translation failed: {trans_res.text}"
        results["telugu_translation"] = "PASSED"

    # Tool: Agent Workflow
    print("\n--- [12] Testing Agent Workflow Orchestration ---")
    with httpx.Client(timeout=60.0) as client:
        agent_payload = {
            "incident_data": analysis,
            "goals": ["location_context", "safety_guidance", "checklist", "report", "save"]
        }
        agent_res = client.post(f"{BACKEND_URL}/api/agent/workflow", json=agent_payload)
        assert agent_res.status_code == 200, f"Agent workflow failed: {agent_res.text}"
        results["agent_workflow"] = "PASSED"

    # Tool: Save Incident
    print("\n--- [18] Saving Incident ---")
    with httpx.Client(timeout=10.0) as client:
        save_payload = {"incident_data": analysis}
        save_res = client.post(f"{BACKEND_URL}/api/incident/save", json=save_payload)
        assert save_res.status_code == 200, f"Save failed: {save_res.text}"
        saved_info = save_res.json()
        results["save_incident"] = "PASSED"

    # Tool: Retrieve Incident
    print("\n--- [19] Retrieving Incident ---")
    with httpx.Client(timeout=10.0) as client:
        get_res = client.get(f"{BACKEND_URL}/api/incidents/{incident_id}")
        assert get_res.status_code == 200, f"Retrieve failed: {get_res.text}"
        retrieved = get_res.json()
        assert retrieved.get("incident_id") == incident_id, "Incident ID mismatch!"
        results["retrieve_incident"] = "PASSED"

    print("\n=================================================================")
    print("ALL REAL BACKEND END-TO-END TESTS COMPLETED SUCCESSFULLY!")
    print("=================================================================")
    for k, v in results.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    test_e2e_complete_live()
