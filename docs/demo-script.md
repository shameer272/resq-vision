# ResQ Vision Demo Script & Judge Walkthrough

A structured 3-minute demonstration script for Hacktoberfest Hack Day Hyderabad × NIAT judges.

---

## 1. Introduction (0:00 – 0:30)

> "Good evening, judges! Emergency responders lose critical minutes sorting through chaotic phone calls, shaky bystander photos, and contradictory testimonies. When dispatchers make assumptions, units arrive unprepared.
> 
> We built **ResQ Vision**: Multimodal Emergency Situation Intelligence powered by Google's **Gemma 4**.
> 
> Our core message: *'See the situation. Understand the risk. Communicate the response.'*"

---

## 2. Ingesting Fragmented Inputs (0:30 – 1:15)

1. Navigate to **Demo Scenarios** tab.
2. Select **Scenario 1: Road Accident Scene** (Outer Ring Road Gachibowli).
3. Click **"Load into Gemma 4 Pipeline"**.
4. Show the judge:
   - Real scene photography with damaged vehicles.
   - User text description: *"There is smoke coming from the vehicle and traffic is blocked."*
   - Audio recording transcript: *"There is smoke coming from the vehicle and traffic is blocked. A crowd is gathering around."*
   - Geographic context: *Outer Ring Road Exit 12, Gachibowli, Hyderabad*.
5. Click **"Analyze Incident"**.

---

## 3. Evidence-Linked Reasoning & Gemma 4 (1:15 – 2:00)

1. Point out the **Action Trace & Timeline**:
   - Ingestion -> RAG Knowledge Retrieval -> Gemma 4 Multimodal Reasoning -> Safety Filter -> Output.
2. Highlight the **Evidence-Linked Observations**:
   - **OBSERVED**: *"Front bumper and hood crumpled on two passenger sedans"* (Evidence: visible structural crushing).
   - **USER REPORTED**: *"Smoke observed by bystander"*.
   - **INFERRED**: *"Secondary traffic collision hazard"* (Subject to on-scene verification).
3. Point out the **Epistemic Humility**:
   - Explicit **Uncertainties**: *"Actual injury or fire status cannot be verified from imagery alone."*
   - **Missing Information**: *"Number of vehicle occupants requiring transport."*

---

## 4. Agent Tools, Translation & Export (2:00 – 2:45)

1. Click **"Generate Checklist"**:
   - Show the triage checklist tailored for field responders.
2. Click **"తెలుగు (Telugu)"**:
   - Demonstrate that the report translates seamlessly into Telugu while strictly preserving uncertainty qualifiers and safety disclaimers.
3. Click **"Read Aloud"**:
   - Demonstrate the browser SpeechSynthesis speaking the situational summary aloud for eyes-busy field operators.
4. Click **"Download PDF"**:
   - Open the generated METHANE standard operational PDF with full data provenance tables.

---

## 5. Conclusion (2:45 – 3:00)

> "ResQ Vision doesn't replace emergency heroes; it gives them instant, evidence-linked situational clarity when every second counts. Powered genuinely by Gemma 4 and the Google GenAI SDK. Thank you!"
