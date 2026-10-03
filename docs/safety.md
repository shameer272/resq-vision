# Safety, Guardrails & Ethical Boundaries

Emergency situations demand absolute ethical and operational discipline. An AI system that hallucinates certainty, invents medical diagnoses, or directs untrained bystanders into dangerous zones can cause grave harm.

ResQ Vision enforces a multi-tier safety architecture before any output reaches dispatchers or bystanders.

## 1. Safety Directives & Prohibitions

1. **No Autonomous Dispatch**:
   The system never autonomously deploys emergency services, police, or medical assets. All recommendations are presented as decision-support packages for human dispatchers.

2. **No Medical Diagnosis**:
   ResQ Vision does not diagnose clinical conditions (e.g. "patient has internal bleeding" or "fractured femur"). Such language is intercepted and converted to observational physical distress notes.

3. **No Hazardous Bystander Directives**:
   Phrases such as *"Go and disconnect the power line"*, *"Enter the collapsed room"*, or *"Fight the blaze"* are detected and automatically rewritten into safe stand-off perimeters (e.g. *"Do not approach electrical cables; maintain a safe perimeter and alert utility responders"*).

4. **Zero Unsupported Assertions**:
   Every visual observation must be backed by concrete observable evidence from the submitted imagery. Overconfident phrases like *"Fire is definitely present"* are calibrated to *"Smoke-like material is visible; an active fire hazard cannot be confirmed from the image alone."*

## 2. Automated Safety Validation Engine

Implemented in `backend/app/safety/safety_service.py`, the validation layer runs regex and contextual token analysis on every output:

- **Dangerous Actions Interceptor**: Identifies dangerous verbs associated with fire, power lines, structural collapse, and hazardous materials.
- **Overconfidence Filter**: Intercepts deterministic guarantees and replaces them with evidence-calibrated statements.
- **Diagnosis Neutralizer**: Converts clinical terms into neutral physical descriptions.
- **Mandatory Disclaimer Enforcer**: Injects the legal disclaimer requiring on-scene human verification across all views and PDF reports.

## 3. Epistemic Uncertainty Highlighting

ResQ Vision explicitly isolates what it **cannot** know:
- **`UNCERTAINTIES`**: Highlights factors hidden from the camera view (e.g. passenger vital signs, thermal expansion behind walls, toxic gas concentration).
- **`MISSING_INFORMATION`**: Generates a checklist of critical facts dispatchers must ask callers to establish safe response packages.
