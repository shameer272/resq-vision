# Hackathon Submission Details

**Hackathon:** Hacktoberfest Hack Day Hyderabad × NIAT  
**Project Name:** ResQ Vision  
**Target Challenge:** Best Use of Gemma 4  
**Tagline:** See the situation. Understand the risk. Communicate the response.  

**One-Line Pitch:**  
ResQ Vision uses Gemma 4's multimodal reasoning to transform images, voice, text, and context into structured, evidence-linked emergency situation intelligence.

---

## Executive Summary

During critical emergencies, responders lose precious minutes sifting through fragmented, panicky caller descriptions and ambiguous photographs. ResQ Vision is an operational situation intelligence platform that unifies up to 4 scene photographs, voice transcripts, bystander text, and geographic landmarks into standardized **METHANE** incident reports.

Unlike generic LLMs that hallucinate dangerous interventions or make unsupported claims, ResQ Vision:
1. Employs **Gemma 4** (`gemma-4-31b-it` / `gemma-4-26b-a4b-it`) via the official Google GenAI SDK.
2. Distinguishes data provenance: **OBSERVED** (visually supported by pixels), **USER_REPORTED** (stated by caller), and **INFERRED** (requiring verification).
3. Connects an auditable **visual evidence basis** to every single observation.
4. Enforces an automated **Safety Validation Shield** that rewrites hazardous directives into safe stand-off perimeters and prohibits medical diagnoses.
5. Deploys an **Agentic Tool Workflow** for responder checklists, regional context resolution, and ReportLab PDF compilation.
6. Delivers **Multilingual Support** in English, Telugu (తెలుగు), and Hindi (हिन्दी) that strictly preserves epistemic uncertainty.

---

## Why This is the "Best Use of Gemma 4"

1. **Gemma 4 is Central, Not Cosmetic**:
   The entire intelligence loop hinges on Gemma 4's multimodal encoder-free reasoning, image-text fusion, and structured JSON generation.
2. **True Multimodal Reasoning**:
   Simultaneously evaluates multiple photographs (front crumple, debris scatter, road blockages) alongside spoken audio transcripts.
3. **Epistemic Humility by Design**:
   Gemma 4 is constrained to explicitly output `uncertainties` and `missing_information`, preventing unwarranted certainty.
4. **Native Regional Language Capabilities**:
   Leverages Gemma 4's 140+ language support to render emergency advisories for first responders in Telangana and across India.

---

## 3-Minute Hackathon Pitch Script

- **[0:00 - 0:30] Hook:** "When a major collision occurs on the Hyderabad Outer Ring Road, 10 callers dial in. One says 'fire!', another says 'just steam', a third says 'traffic is blocked'. Dispatchers have 30 seconds to choose what response package to send."
- **[0:30 - 1:15] Demo:** "Watch ResQ Vision ingest two scene photographs, a witness voice recording, and location data. In seconds, Gemma 4 fuses these inputs into an evidence-linked situational report."
- **[1:15 - 2:00] Evidence & Safety:** "Notice how every fact shows its data provenance: Green for visually verified, Amber for unconfirmed inferences. Our safety shield ensures no bystander is told to touch downed wires or enter burning buildings."
- **[2:00 - 2:45] Tools & Telugu:** "With one click, Gemma 4 synthesizes a first-responder triage checklist, translates the report into Telugu while preserving uncertainty qualifiers, and compiles an official METHANE PDF."
- **[2:45 - 3:00] Close:** "ResQ Vision: Transforming fragmented emergency data into explainable, life-saving situational intelligence with Gemma 4."
