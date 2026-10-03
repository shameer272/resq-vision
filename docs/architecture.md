# ResQ Vision Architecture

"See the situation. Understand the risk. Communicate the response."

## 1. High-Level Architecture Overview

ResQ Vision is architected as an end-to-end multimodal situation intelligence platform designed for public safety answering points (PSAPs), disaster relief coordinators, and first-responder dispatchers.

```
+-------------------------------------------------------------------------+
|                            USER INPUT LAYER                             |
|  - Scene Photography (1 to 4 Images)                                   |
|  - Real-Time Voice Recording & Browser Transcription                   |
|  - Natural Language Witness Description                                 |
|  - Geographic Landmark / Coordinates                                    |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                             REACT FRONTEND                              |
|  - Vite + React 19 + Tailwind CSS + Lucide Icons + Recharts             |
|  - Strict Client-Side Privacy: ZERO API Keys in Browser                 |
|  - Epistemic Uncertainty Highlighting & Provenance Badges              |
+-------------------------------------------------------------------------+
                                     |  HTTP REST / Multipart
                                     v
+-------------------------------------------------------------------------+
|                            FASTAPI BACKEND                              |
|  - App Entrypoint & CORS Enforcement                                    |
|  - Input Validation & Image Size Verification (<10MB)                  |
|  - Modular Model Provider Layer                                         |
+-------------------------------------------------------------------------+
          |                         |                         |
          v                         v                         v
+------------------+      +------------------+      +------------------+
|    RAG ENGINE    |      | GEMMA 4 REASONING|      |  SAFETY SHIELD   |
| Local Curated KB |      | Google GenAI SDK |      | Regex & Lexicon  |
| FEMA, NOAA, NDMA |      | Multimodal Model |      | Sanitization     |
+------------------+      +------------------+      +------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                         AGENT & TOOL WORKFLOW                           |
|  - generate_incident_report (METHANE Standard)                          |
|  - generate_responder_checklist (Triage Items)                          |
|  - get_location_context (Regional Infrastructure)                       |
|  - retrieve_safety_guidance (Verified Protocols)                        |
|  - translate_report (Telugu, Hindi, English)                            |
|  - export_report (ReportLab PDF Generation)                             |
|  - save_incident (MongoDB / Local File Storage Fallback)                |
+-------------------------------------------------------------------------+
```

## 2. Component Breakdown

### Frontend (React + Vite)
- **`src/pages/AnalyzePage.jsx`**: Primary multimodal analysis control center.
- **`src/pages/IncidentsPage.jsx`**: Incident history registry and document browser.
- **`src/pages/EvaluationPage.jsx`**: 20-scenario empirical benchmark dashboard with Recharts visualization.
- **`src/pages/DemoPage.jsx`**: 4 preloaded safe operational scenarios.
- **`src/components/AudioRecorder.jsx`**: Speech-to-text recording, timer, audio playback, and editable fallback.
- **`src/components/ImageUploader.jsx`**: Multi-image drag-and-drop uploader with camera capture.
- **`src/components/ObservationCard.jsx`**: Provenance-linked observation cards displaying source (Observed, User Reported, Inferred) and evidence citations.

### Backend (FastAPI + Python 3.12)
- **`backend/app/ai/gemma_service.py`**: Model initialization and multimodal execution using official `google-genai` SDK.
- **`backend/app/agent/agent_service.py`**: Safe tool dispatching, schema validation, and multi-step execution.
- **`backend/app/safety/safety_service.py`**: Real-time pattern interception converting dangerous bystander directives into safe stand-off perimeters and stripping medical diagnoses.
- **`backend/app/rag/rag_service.py`**: Keyword & semantic indexer over official emergency documentation.
- **`backend/app/services/report_service.py`**: ReportLab PDF compiler conforming to the international ETHANE/METHANE protocol.
- **`backend/app/services/storage_service.py`**: Dual-mode storage engine (MongoDB with automated fallback to local JSON file persistence).

## 3. Data Flow & Provenance Segregation

To prevent catastrophic hallucinations during emergencies, ResQ Vision enforces strict data provenance:
1. **`observed`**: Direct visual features detected in the scene photograph (e.g. radiator liquid pooling, broken headlight, structural crack).
2. **`user_reported`**: Information provided exclusively in witness voice transcripts or text.
3. **`inferred`**: Deductions made by the AI model that are explicitly tagged as requiring human on-scene verification.
4. **`uncertainties`**: Epistemic boundaries explicitly acknowledged by the model (e.g. occupant vital status cannot be determined from imagery).
