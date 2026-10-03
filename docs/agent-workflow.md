# Agent & Tool Workflow

ResQ Vision implements a structured agentic workflow using the Google GenAI tool-calling paradigm.

## 1. Tool Allowlist

To eliminate security risks and prevent arbitrary code or network execution, ResQ Vision enforces a strict tool allowlist:

| Tool Name | Purpose | Return Value |
|---|---|---|
| `generate_incident_report` | Compiles operational report conforming to international METHANE standard | Structured JSON + Report ID |
| `generate_responder_checklist` | Creates priority-ordered triage checklist for first responders | Actionable verification list |
| `get_location_context` | Resolves regional emergency jurisdiction, trauma centers, and terrain hazards | Geographic operational context |
| `retrieve_safety_guidance` | Queries local RAG knowledge base for official protocols (NHTSA, FEMA, NDMA) | Verified citations with URLs |
| `save_incident` | Persists incident record to MongoDB or local storage fallback | Confirmation & Incident ID |
| `export_report` | Compiles printable and downloadable high-contrast PDF document | PDF Filepath & MIME Type |

## 2. Multi-Step Execution Lifecycle

```
[Incident Ingestion] 
         |
         v
1. get_location_context(location)
         |
         v
2. retrieve_safety_guidance(query, category)
         |
         v
3. gemma_4_multimodal_analysis(images, voice, text, rag_citations)
         |
         v
4. safety_validation_layer()
         |
         v
5. generate_responder_checklist()
         |
         v
6. generate_incident_report()
         |
         v
7. save_incident()
```

## 3. Human-in-the-Loop Principle

At no stage does the AI agent make unverified operational commitments:
- Checklists highlight items requiring human confirmation.
- Reports are flagged with mandatory human verification notices before dispatch.
- Physical intervention directives for untrained persons are forbidden.
