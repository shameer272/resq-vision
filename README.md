# ResQ Vision
> "See the situation. Understand the risk. Communicate the response."

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Gemma 4](https://img.shields.io/badge/Model-Gemma_4_(31B--IT)-red.svg)](https://ai.google.dev/)
[![SDK: Google GenAI](https://img.shields.io/badge/SDK-google--genai-green.svg)](https://pypi.org/project/google-genai/)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![Frontend: React + Vite](https://img.shields.io/badge/Frontend-React_19_+_Vite-purple.svg)](https://vite.dev/)

**Hackathon Track:** Hacktoberfest Hack Day Hyderabad × NIAT  
**Target Challenge:** Best Use of Gemma 4  

---

## 1. Problem Statement

In the opening minutes of emergencies (road collisions, fires, flash floods, structural collapse), public safety answering points (PSAPs) are flooded with fragmented, contradictory bystander telephone calls and arbitrary mobile photos. Dispatchers face high cognitive overload:
- Unverified hearsay leads to incorrect emergency dispatch packages.
- Vital hazard cues (e.g. hazardous material placards, downed high-voltage lines, fuel leaks) are overlooked in chaotic witness photos.
- Generic AI chatbots hallucinate certainty, direct untrained citizens into fatal danger, or make unvetted medical diagnoses.

---

## 2. Solution: ResQ Vision

**ResQ Vision** is a multimodal emergency situation intelligence platform powered genuinely by Google's **Gemma 4**.

The system ingests:
1. **Scene Photography** (1 to 4 multi-angle perspectives)
2. **User Voice Recordings** with real-time transcription
3. **Bystander Text Descriptions**
4. **Geographic Landmarks & Context**

It subjects this fragmented data to unified multimodal reasoning, cross-references verified public safety protocols (FEMA, NHTSA, NOAA, NDMA) through a local transparent RAG layer, filters assertions through an automated safety validation shield, and executes an agentic tool workflow to compile official **METHANE** incident reports and first-responder triage checklists.

---

## 3. Why Gemma 4 is Central

> *"Gemma 4 performs multimodal analysis of incident images together with user-provided textual context, produces structured situational observations, and participates in the tool-driven incident workflow."*

Gemma 4 is not a cosmetic marketing label; it is the core analytical engine:
- **Encoder-Free Multimodal Reasoning:** Efficiently fuses high-resolution visual tokens with complex audio transcripts and witness text.
- **Multi-Image Scene Synthesis:** Analyzes up to 4 scene perspectives simultaneously (front crumple, road obstruction, surrounding terrain) without context degradation.
- **Strict Structured JSON Generation:** Conforms strictly to Pydantic typing schemas with self-correcting repair prompts.
- **Epistemic Humility:** Purpose-trained to explicitly surface `uncertainties` and `missing_information`.
- **Multilingual Support:** Delivers zero-shot translation into **Telugu (తెలుగు)** and **Hindi (हिन्दी)** while rigorously preserving uncertainty qualifiers and safety warnings.

---

## 4. Key Features

- **Evidence-Linked AI (Data Provenance):**
  - **`OBSERVED`**: Direct visual features physically verifiable in the image.
  - **`USER_REPORTED`**: Facts provided in witness text or voice transcript.
  - **`INFERRED`**: AI situational deductions requiring on-scene verification.
- **Multi-Image Fusion:** Synthesizes multiple camera perspectives into a unified situational model.
- **Voice Input & Verbal Dispatch:** Native browser Speech-to-Text recording with timer, audio playback, and editable fallback.
- **SpeechSynthesis Read Aloud:** Hands-free verbal briefing for field personnel.
- **Agentic Tool Calling:** Safe allowlist executing METHANE report generation, triage checklists, regional context lookup, and ReportLab PDF compilation.
- **Independent Safety Validation Shield:** Intercepts hazardous bystander actions, eliminates medical diagnoses, and enforces mandatory human verification.
- **Empirical Evaluation Dashboard:** 20 controlled scenarios measuring real schema compliance, latency, and safety triggers without fabricated statistics.
- **Interactive Demo Mode:** 4 preloaded safe operational scenarios (Accident, Flood, Fire, Obstruction).

---

## 5. Technology Stack

- **Frontend:** React 19, Vite 8, Tailwind CSS v4, Lucide Icons, Recharts.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, ReportLab, Uvicorn.
- **AI & SDK:** Google Gemma 4 (`gemma-4-31b-it` / `gemma-4-26b-a4b-it`) via official `google-genai` SDK.
- **Data & Persistence:** Dual-mode storage (MongoDB with automatic local file persistence fallback `data/storage/incidents.json`).
- **Testing:** Pytest (100% passing test suite across schemas, safety filters, RAG, tools, and endpoints).

---

## 6. Architecture & Security

```
React Frontend (Vite)
         |
         | HTTP / Multipart
         v
FastAPI Backend (Port 8000)
         |
         +---> Local Curated RAG KB (NHTSA, FEMA, NDMA, NOAA)
         |
         +---> Google GenAI SDK (google-genai) ---> Gemma 4 (gemma-4-31b-it)
         |
         +---> Automated Safety Filter & Regex Sanitizer
         |
         +---> Agent Tool Dispatcher (METHANE Reports, Checklists, PDF)
```

**Security Mandate:** The `GEMINI_API_KEY` remains strictly server-side. It is never exposed in client bundles or browser localStorage.

---

## 7. Project Structure

```
resq-vision/
├── frontend/                     # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── components/           # UI components (Audio, Uploader, Cards, Modals)
│   │   ├── pages/                # Landing, Analyze, Incidents, Evaluation, Demo, About
│   │   ├── services/             # API client services
│   │   └── App.jsx               # Application root
│   ├── public/demo-assets/       # Preloaded safe demonstration photography
│   ├── package.json
│   └── vite.config.js
│
├── backend/                      # FastAPI Python backend
│   ├── app/
│   │   ├── api/                  # REST endpoints
│   │   ├── core/                 # Configuration & settings
│   │   ├── schemas/              # Pydantic schemas (RawExtraction, Report, Checklist)
│   │   ├── ai/                   # Gemma 4 multimodal service (google-genai)
│   │   ├── agent/                # Agent orchestration & tool dispatcher
│   │   ├── tools/                # 7 registered operational incident tools
│   │   ├── rag/                  # Transparent local RAG engine
│   │   ├── safety/               # Safety validation & sanitization layer
│   │   ├── services/             # ReportLab PDF, storage, translation, evaluation
│   │   └── main.py               # FastAPI entrypoint
│   └── requirements.txt
│
├── data/
│   └── knowledge-base/           # Curated official emergency reference protocols
│
├── docs/                         # In-depth architectural & integration docs
│   ├── architecture.md
│   ├── gemma-integration.md
│   ├── agent-workflow.md
│   ├── safety.md
│   ├── evaluation.md
│   ├── demo-script.md
│   └── hackathon-submission.md
│
├── tests/                        # Pytest suite
│   ├── test_schemas.py
│   ├── test_safety.py
│   ├── test_rag.py
│   ├── test_tools.py
│   └── test_api_endpoints.py
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── LICENSE                       # Apache 2.0
└── README.md
```

---

## 8. Setup & Running Locally

### Prerequisites
- Python 3.10+ (Recommended: Python 3.12)
- Node.js 18+ & npm
- Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/))

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/resq-vision.git
cd resq-vision
```

### Step 2: Configure Environment Variables
Copy the template and add your Gemini API Key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMMA_MODEL=gemma-4-31b-it
FALLBACK_MODEL=gemma-4-26b-a4b-it
APP_ENV=development
```

### Step 3: Install & Start Backend
```bash
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

### Step 4: Install & Start Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 9. Running Automated Tests

Run the complete backend test suite:
```bash
# From the root directory:
pytest tests -v
```

---

## 10. Docker Deployment

Launch the entire stack with Docker Compose:
```bash
docker-compose up --build
```
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

---

## 11. Safety & Ethical Limitations

1. **Human-in-the-Loop:** ResQ Vision is an operational situational decision-support system. It does NOT autonomously dispatch emergency services or replace certified incident commanders.
2. **Medical Prohibitions:** The system does not diagnose clinical trauma or evaluate physiological vital signs.
3. **Environmental Visibility:** Image quality, heavy smoke, and nighttime conditions affect visual recognition. Inferences must be validated on-scene.

---

## 12. License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.
