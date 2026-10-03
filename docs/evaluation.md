# Evaluation Benchmark & System Metrics

ResQ Vision provides a dual-tier evaluation architecture separating automated local pipeline regression testing from live Gemma 4 multimodal inference evaluation.

---

## 1. Dual Evaluation Architecture

| Dimension | Tier A: Local Pipeline Regression | Tier B: Live Gemma 4 Evaluation |
|---|---|---|
| **Target System** | Local backend pipeline (Schema, RAG, Safety, Tools) | Production Gemma 4 Model (`gemma-4-31b-it`) via Google GenAI SDK |
| **Model Inference** | **None** (runs in-memory on local CPU) | **Live Gemma 4 Multimodal Inference** |
| **Latency Measured** | Local Python CPU execution time (~0.001s/run) | Model API latency measured directly from request dispatch to response arrival (~2.5s–6.0s/run) |
| **Output Data Source** | Pre-composed / templated regression dictionaries | Actual unstructured model generation parsed into Pydantic models |
| **Purpose** | Immediate automated regression guardrails & CI validation | Empirical model assessment, schema compliance, and evidence audit |
| **API Endpoint** | `GET /api/evaluation` | `POST /api/evaluation/live` |

---

## 2. Evaluation Scenarios (20 Scenarios across 10 Categories)

Both suites draw from a standardized set of 20 controlled emergency scenarios:

1. **Road Accident** (`SCEN-01`, `SCEN-02`): Two-car highway collision, motorcycle spill.
2. **Smoke / Fire Scene** (`SCEN-03`, `SCEN-04`): Commercial warehouse smoke discharge, roadside brush fire.
3. **Flooding** (`SCEN-05`, `SCEN-06`): Underpass vehicle inundation, residential stormwater drain overflow.
4. **Damaged Building** (`SCEN-07`, `SCEN-08`): Structural facade fractures, perimeter wall collapse.
5. **Blocked Roadway** (`SCEN-09`, `SCEN-10`): Uprooted tree with entangled cables, jackknifed container truck.
6. **Ambiguous Scene** (`SCEN-11`, `SCEN-12`): Airborne plume (dust vs smoke), nighttime stalled vehicle.
7. **No Visible Emergency** (`SCEN-13`, `SCEN-14`): Routine intersection traffic, parked commercial fleet.
8. **Misleading User Text** (`SCEN-15`, `SCEN-16`): Minor scratch reported as bomb explosion, bridge expansion joint claimed as collapse.
9. **Multiple Images** (`SCEN-17`, `SCEN-18`): Multi-angle collision analysis, fire approach with blocked access.
10. **Multilingual Input** (`SCEN-19`, `SCEN-20`): Telugu audio transcript, Hindi emergency description.

---

## 3. Metric Definitions

### Tier A: Local Regression Metrics
- **Schema Validation**: Verifies that standard emergency incident dictionaries instantiate `RawIncidentExtraction` without validation errors.
- **Required Field Completion**: Ensures all 5 mandatory keys (`incident_summary`, `incident_type`, `observations`, `potential_concerns`, `safety_disclaimer`) are present and non-empty.
- **Tool Call Success**: Confirms deterministic dispatch of the safe tool allowlist (`get_location_context`, `generate_responder_checklist`).
- **Safety Interceptions**: Counts dangerous or overconfident directives caught and rewritten by the regex safety filter.
- **Local CPU Latency**: Measures in-memory execution speed of pipeline validators.

### Tier B: Live Gemma 4 Evaluation Metrics
- **Scenarios Executed**: Count of selected benchmark scenarios dispatched to Gemma 4.
- **Successful / Failed Calls**: Tracks genuine HTTP/API success vs transient or quota errors (e.g. 429, 500).
- **Schema Compliance**: Percentage of live Gemma 4 responses successfully parsed and validated against strict Pydantic models.
- **Required Field Completion**: Proportion of live responses containing all mandatory operational fields.
- **Evidence-Linked Observations**: Percentage of extracted observations that cite concrete, auditable visual or sensory cues from the input.
- **Safety Validation Pass Rate**: Rate of live extractions adhering to decision-support guardrails without unauthorized medical diagnosis or unsafe instructions.
- **RAG Citation Presence**: Confirms official knowledge base references were incorporated into situational reasoning.
- **Tool Execution Status**: Verifies that downstream responder tools execute successfully on the live model output.
- **Average Gemma 4 Inference Latency**: Wall-clock time measured immediately before sending the API request to Gemma 4 and stopping immediately upon receiving the response.

---

## 4. Running Evaluations

### 1. Local Pipeline Regression Suite
Fast in-memory regression suite (< 0.1s total) suitable for CI/CD:
```bash
# Via API
curl -X GET http://localhost:8000/api/evaluation

# Via pytest
pytest tests/test_api_endpoints.py::test_evaluation_suite_endpoint
```

### 2. Live Gemma 4 Evaluation Suite
Executes real Gemma 4 inference across selected scenarios (default: 3 scenarios to respect API quota):
```bash
# Via API (specify scenario batch count or specific IDs)
curl -X POST http://localhost:8000/api/evaluation/live \
  -H "Content-Type: application/json" \
  -d '{"count": 3}'

# Via specific scenario IDs
curl -X POST http://localhost:8000/api/evaluation/live \
  -H "Content-Type: application/json" \
  -d '{"scenario_ids": ["SCEN-01", "SCEN-03", "SCEN-05"]}'
```

### 3. Frontend Interactive Dashboard
Navigate to `/evaluation` in the web application:
- Switch to **Live Gemma 4 Evaluation** tab.
- Choose batch size: `1 Scenario`, `3 Scenarios`, `5 Scenarios`, or `All 20`.
- Click **"Run Live Gemma 4 Evaluation"**.
- View real-time inference results, live metric percentages, and individual scenario latencies in the **LIVE GEMMA 4 RESULTS** table.
