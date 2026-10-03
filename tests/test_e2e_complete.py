import os
import sys
import json
import httpx

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_PATH = os.path.join(BASE_DIR, "frontend", "public", "demo-assets", "accident.jpg")
if not os.path.exists(IMAGE_PATH):
    IMAGE_PATH = r"c:\Users\Shameer\.gemini\antigravity-ide\scratch\resq-vision\frontend\public\demo-assets\accident.jpg"

TEST_TEXT = "There is a damaged vehicle with visible smoke and the road appears partially blocked."

results = {}

print("=================================================================")
print("STARTING RESQ VISION COMPLETE END-TO-END TEST SUITE")
print("=================================================================\n")

# 1, 2, 3: Verify Health, API Key, Model, MongoDB
print("--- [1, 2, 3] Checking Health Endpoint ---")
with httpx.Client(timeout=10.0) as client:
    resp = client.get(f"{BACKEND_URL}/health")
    assert resp.status_code == 200, f"Health check failed with {resp.status_code}"
    health_data = resp.json()
    print("Health Data:", json.dumps(health_data, indent=2))
    assert health_data["gemini_api_key_configured"] is True, "GEMINI_API_KEY is not configured!"
    assert health_data["model"] == "gemma-4-31b-it", f"Model is not gemma-4-31b-it: {health_data['model']}"
    assert health_data["storage_mode"] == "MongoDB", f"Storage mode is not MongoDB: {health_data['storage_mode']}"
    results["backend_env"] = "PASSED"
    results["model_name"] = health_data["model"]
    results["mongodb_mode"] = health_data["storage_mode"]

# 5: Verify Frontend
print("\n--- [5] Checking Frontend Availability ---")
with httpx.Client(timeout=10.0) as client:
    f_resp = client.get(FRONTEND_URL)
    assert f_resp.status_code == 200, f"Frontend check failed with {f_resp.status_code}"
    print(f"Frontend returned 200 OK (HTML bytes: {len(f_resp.content)})")
    results["frontend_status"] = "PASSED"

# 6, 7, 8, 9, 10, 11, 13: Real Multimodal Request with Gemma 4
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

# 7 & 8: Confirm real model & primary model name gemma-4-31b-it
assert analysis.get("primary_model") == "gemma-4-31b-it", f"Expected primary model gemma-4-31b-it, but got: {analysis.get('primary_model')}"
assert analysis["model_used"] in ["gemma-4-31b-it", "gemma-4-26b-a4b-it"], f"Unexpected model: {analysis['model_used']}"
assert len(analysis["incident_summary"]) > 20, "Summary too short"

print(f"\nObservations ({len(analysis['observations'])}):")
sources_found = set()
for obs in analysis["observations"]:
    src = obs["source"]
    sources_found.add(src)
    print(f"  - [{src.upper()}] (Conf: {obs['confidence']}): {obs['description']}")
    print(f"    Evidence: {obs['evidence']}")

# 10: Verify OBSERVED, USER_REPORTED, INFERRED distinctions
print("\nData Provenance Sources Found:", sources_found)
assert "observed" in sources_found or "user_reported" in sources_found or "inferred" in sources_found, "Missing provenance distinctions"

print(f"\nUser Reported Info ({len(analysis['user_reported_information'])} items):")
for uri in analysis["user_reported_information"]:
    print(f"  - {uri}")

print(f"\nPotential Concerns ({len(analysis['potential_concerns'])} items):")
for pc in analysis["potential_concerns"]:
    print(f"  - {pc['concern']} (Reason: {pc['reason']}, Human Verification: {pc.get('requires_human_verification')})")

print(f"\nUncertainties ({len(analysis['uncertainties'])} items):")
for unc in analysis["uncertainties"]:
    print(f"  - {unc}")

# 11: Safety validation verification
print(f"\nSafety Disclaimer: {analysis['safety_disclaimer']}")
assert len(analysis["safety_disclaimer"]) > 10, "Safety disclaimer missing!"

# 13: RAG information and source metadata
print(f"\nRAG Sources Retrieved ({len(analysis['rag_sources'])}):")
for r in analysis["rag_sources"]:
    print(f"  - Title: {r['title']} ({r['source']}) | Relevance: {r['relevance_snippet'][:80]}...")
assert len(analysis["rag_sources"]) > 0, "RAG sources missing!"

# Action Trace
print(f"\nAction Trace ({len(analysis['action_trace'])} steps):")
for at in analysis["action_trace"]:
    print(f"  -> Step '{at['step']}': {at['description']} [{at['status']}]")

results["multimodal_analysis"] = "PASSED"
results["model_verified"] = analysis["model_used"]
results["provenance_distinction"] = list(sources_found)
results["rag_sources_count"] = len(analysis["rag_sources"])

# 15: Generate an incident report (METHANE)
print("\n--- [15] Testing Tool: Generate Incident Report (METHANE) ---")
with httpx.Client(timeout=30.0) as client:
    rep_res = client.post(f"{BACKEND_URL}/api/incident/report", json=analysis)
    assert rep_res.status_code == 200, f"Report generation failed: {rep_res.text}"
    report_data = rep_res.json()
    print("METHANE Report ID:", report_data.get("report_id"))
    print("Executive Summary:", report_data.get("executive_summary")[:80])
    for section_k, section_v in report_data.get("methane_structure", {}).items():
        print(f"  {section_k}: {section_v}")
    results["report_tool"] = "PASSED"

# 16: Generate responder checklist
print("\n--- [16] Testing Tool: Generate Responder Checklist ---")
with httpx.Client(timeout=30.0) as client:
    chk_res = client.post(f"{BACKEND_URL}/api/incident/checklist", json=analysis)
    assert chk_res.status_code == 200, f"Checklist generation failed: {chk_res.text}"
    checklist_data = chk_res.json()
    items = checklist_data.get("checklist_items", [])
    print("Checklist Items Count:", len(items))
    assert len(items) > 0, "No checklist items returned!"
    for item in items[:4]:
        print(f"  [ ] ({item['priority'].upper()}): {item['label']} - {item['instruction']}")
    results["checklist_tool"] = "PASSED"

# 17: Test Telugu translation
print("\n--- [17] Testing Telugu Translation ---")
with httpx.Client(timeout=120.0) as client:
    trans_payload = {
        "text": analysis.get("incident_summary", ""),
        "incident_data": analysis,
        "target_language": "te"
    }
    trans_res = client.post(f"{BACKEND_URL}/api/translate", json=trans_payload)
    assert trans_res.status_code == 200, f"Translation failed: {trans_res.text}"
    trans_data = trans_res.json()
    print("Language Display:", trans_data.get("language_display", "").encode("ascii", "replace").decode("ascii"))
    print("Preservation Notice:", trans_data.get("preservation_notice"))
    translated_content = trans_data.get("translated_content", {})
    summary_te = str(translated_content.get("incident_summary", ""))
    print(f"Telugu Summary Generated (length: {len(summary_te)})")
    assert len(summary_te) > 0, "Telugu translation is empty!"
    results["telugu_translation"] = "PASSED"

# 12: Verify Agent / Tool Workflow
print("\n--- [12] Testing Agent Workflow Orchestration ---")
with httpx.Client(timeout=60.0) as client:
    agent_payload = {
        "incident_data": analysis,
        "goals": ["location_context", "safety_guidance", "checklist", "report", "save"]
    }
    agent_res = client.post(f"{BACKEND_URL}/api/agent/workflow", json=agent_payload)
    assert agent_res.status_code == 200, f"Agent workflow failed: {agent_res.text}"
    agent_data = agent_res.json()
    print("Agent Status:", agent_data.get("status"))
    print("Agent Trace Steps:", len(agent_data.get("trace", [])))
    for tr in agent_data.get("trace", []):
        print(f"  [Tool: {tr.get('tool')}] -> {tr.get('step')} ({tr.get('status')})")
    results["agent_workflow"] = "PASSED"

# 18: Save incident to MongoDB
print("\n--- [18] Saving Incident to MongoDB ---")
with httpx.Client(timeout=10.0) as client:
    save_payload = {"incident_data": analysis}
    save_res = client.post(f"{BACKEND_URL}/api/incident/save", json=save_payload)
    assert save_res.status_code == 200, f"Save failed: {save_res.text}"
    saved_info = save_res.json()
    print(f"Saved to MongoDB with status: {saved_info.get('status')}, ID: {saved_info.get('incident_id')}")
    results["save_to_mongodb"] = "PASSED"

# 19: Retrieve saved incident from MongoDB
print("\n--- [19] Retrieving Saved Incident from MongoDB ---")
with httpx.Client(timeout=10.0) as client:
    get_res = client.get(f"{BACKEND_URL}/api/incidents/{incident_id}")
    assert get_res.status_code == 200, f"Retrieve failed: {get_res.text}"
    retrieved = get_res.json()
    assert retrieved.get("incident_id") == incident_id, "Incident ID mismatch!"
    print(f"Retrieved incident '{retrieved.get('incident_id')}' successfully from MongoDB!")
    print(f"Stored Summary: {retrieved.get('incident_summary')[:100]}...")
    results["retrieve_from_mongodb"] = "PASSED"

print("\n=================================================================")
print("ALL REAL BACKEND END-TO-END TESTS COMPLETED SUCCESSFULLY!")
print("=================================================================")
for k, v in results.items():
    print(f"{k}: {v}")
