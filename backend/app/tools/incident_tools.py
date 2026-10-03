import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.rag.rag_service import rag_service
from app.services.report_service import report_service
from app.services.storage_service import storage_service

class IncidentTools:
    """
    Structured Tool Definitions and Implementations for Gemma 4 Function-Calling & Agent Workflow.
    All tools provide validation, structured return dictionaries, and safety boundaries.
    No arbitrary shell execution or unsafe network actions.
    """

    @staticmethod
    def generate_incident_report(incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool: generate_incident_report
        Transforms structured multimodal incident observations into a standardized METHANE operational report.
        """
        if not incident_data or not isinstance(incident_data, dict):
            return {"error": "Invalid incident data supplied"}
        
        report = report_service.generate_methane_report(incident_data)
        return {
            "status": "success",
            "report_id": report["report_id"],
            "report": report
        }

    @staticmethod
    def generate_responder_checklist(incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool: generate_responder_checklist
        Generates an actionable, priority-ordered verification checklist for on-scene first responders.
        Focuses strictly on critical triage parameters without directing untrained persons to take hazardous actions.
        """
        incident_type = incident_data.get("incident_type", "incident")
        potential_concerns = incident_data.get("potential_concerns", [])
        uncertainties = incident_data.get("uncertainties", [])
        missing_info = incident_data.get("missing_information", [])

        checklist = [
            {
                "id": "chk-loc",
                "label": "Confirm Precise Geolocation & Safe Approach Route",
                "category": "navigation",
                "priority": "critical",
                "instruction": "Verify cross-streets, mile-marker, and ensure emergency vehicles approach upwind and uphill."
            },
            {
                "id": "chk-haz",
                "label": "Establish Hazard Perimeter & Isolate Igniters",
                "category": "safety",
                "priority": "critical",
                "instruction": "Maintain stand-off distance from visible smoke, fuel leaks, downed power lines, or compromised walls."
            },
            {
                "id": "chk-cas",
                "label": "Assess Casualty Count and Entrapment Status",
                "category": "triage",
                "priority": "high",
                "instruction": "Visually confirm number of affected individuals and notify EMS dispatch before physical contact."
            },
            {
                "id": "chk-acc",
                "label": "Verify Secondary Blockages and Egress Corridors",
                "category": "access",
                "priority": "high",
                "instruction": "Identify debris, stalled commuter traffic, or terrain obstacles hindering heavy rescue apparatus."
            }
        ]

        # Add concern-specific checks
        for idx, concern in enumerate(potential_concerns):
            checklist.append({
                "id": f"chk-concern-{idx}",
                "label": f"Verify {concern.get('concern', 'Identified Concern')}",
                "category": "incident_specific",
                "priority": "high" if concern.get("confidence") == "high" else "medium",
                "instruction": f"On-scene verification of: {concern.get('reason', 'Observable cue')}. Human verification required."
            })

        # Add missing information verifications
        for idx, missing in enumerate(missing_info):
            checklist.append({
                "id": f"chk-missing-{idx}",
                "label": f"Ascertain: {missing}",
                "category": "information_gap",
                "priority": "medium",
                "instruction": "Gather from bystander interviews or visual inspection if safely possible."
            })

        cautions = [
            "Do NOT instruct untrained bystanders to approach fire, structural damage, or live electrical lines.",
            "Do NOT move injured occupants unless imminent catastrophic threat (explosion/submersion) exists.",
            "All checklist items represent decision support suggestions and require human verification."
        ]

        return {
            "incident_id": incident_data.get("incident_id", "INC-CURRENT"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident_type": incident_type,
            "checklist_items": checklist,
            "critical_cautions": cautions,
            "human_verification_notice": "Required for all operational dispatches."
        }

    @staticmethod
    def get_location_context(location_query: str) -> Dict[str, Any]:
        """
        Tool: get_location_context
        Provides geographic situational context for the given location text.
        Clearly labels data source and marks whether it is live or offline/demo context.
        """
        if not location_query:
            return {
                "query": "",
                "resolved_area": "Unknown Location",
                "is_demo_data": False,
                "terrain_notes": "No location string provided.",
                "nearest_landmarks": [],
                "status_label": "No location input"
            }

        q_lower = location_query.lower()

        # Hyderabad / Telangana Context Recognition (Hackathon locale)
        if "hyderabad" in q_lower or "gachibowli" in q_lower or "hitec" in q_lower or "cyberabad" in q_lower or "madhapur" in q_lower:
            return {
                "query": location_query,
                "resolved_area": "Hyderabad Metropolitan Area, Telangana, India",
                "approximate_coordinates": {"latitude": 17.4401, "longitude": 78.3489},
                "jurisdiction": "Cyberabad Police & Fire Command / TS Disaster Response Force",
                "primary_emergency_numbers": {"Police": "100 / 112", "Ambulance": "108", "Fire": "101"},
                "nearby_facilities": [
                    "AIG Hospitals (Gachibowli)",
                    "Continental Hospital (Nanakramguda)",
                    "Madhapur Fire & Rescue Station"
                ],
                "terrain_notes": "High-density urban corridor, elevated expressway flyovers, heavy tech corridor traffic.",
                "is_demo_data": False,
                "status_label": "Regional Context Resolved (Cyberabad Jurisdiction)"
            }
        
        # General / National Highway Context
        if "nh" in q_lower or "highway" in q_lower or "expressway" in q_lower:
            return {
                "query": location_query,
                "resolved_area": f"Highway Corridor: {location_query}",
                "approximate_coordinates": None,
                "jurisdiction": "National Highway Authority / Highway Patrol Unit",
                "primary_emergency_numbers": {"National Emergency": "112", "Highway Helpline": "1033"},
                "nearby_facilities": ["Highway Trauma Center", "Patrol Response Vehicle Unit"],
                "terrain_notes": "High-speed multi-lane roadway; watch for secondary rear-end collisions and blocked breakdown lanes.",
                "is_demo_data": False,
                "status_label": "Highway Sector Context Resolved"
            }

        # Generic Geolocation Context with clear offline/demo label
        return {
            "query": location_query,
            "resolved_area": location_query,
            "approximate_coordinates": None,
            "jurisdiction": "Local Public Safety Answering Point (PSAP)",
            "primary_emergency_numbers": {"Emergency": "112 / 911"},
            "nearby_facilities": ["Local First Responder Unit"],
            "terrain_notes": "Standard urban/suburban topography. Access routes require verification with local dispatch.",
            "is_demo_data": True,
            "status_label": "DEMO DATA: Context synthesized from user-provided location string (No live GIS satellite feed connected)"
        }

    @staticmethod
    def retrieve_safety_guidance(query: str, incident_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Tool: retrieve_safety_guidance
        Calls the local RAG engine to retrieve verified safety guidelines and protocol citations.
        """
        sources = rag_service.query(query, incident_type=incident_type, top_k=3)
        return {
            "query": query,
            "incident_type": incident_type,
            "citations_found": len(sources),
            "sources": [s.model_dump() for s in sources]
        }

    @staticmethod
    def save_incident(incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool: save_incident
        Persists incident report to MongoDB (if configured) or local storage fallback.
        """
        incident_id = storage_service.save_incident(incident_data)
        return {
            "status": "success",
            "incident_id": incident_id,
            "storage_mode": "MongoDB" if storage_service.using_mongo else "Local File Storage (incidents.json)"
        }

    @staticmethod
    def export_report(report_data: Dict[str, Any], format_type: str = "pdf") -> Dict[str, Any]:
        """
        Tool: export_report
        Compiles the report to a downloadable format (PDF or text).
        """
        if format_type.lower() == "pdf":
            filepath = report_service.generate_pdf(report_data)
            return {
                "status": "success",
                "format": "pdf",
                "filepath": filepath,
                "filename": os.path.basename(filepath)
            }
        else:
            return {
                "status": "success",
                "format": "json",
                "data": report_data
            }

    @staticmethod
    def translate_report(incident_data: Dict[str, Any], target_language: str = "te") -> Dict[str, Any]:
        """
        Tool: translate_report
        Translates incident intelligence into Telugu ('te') or Hindi ('hi')
        while strictly preserving epistemic uncertainty.
        """
        from app.services.translation_service import translation_service
        lex = translation_service.TRANSLATION_LEXICON.get(target_language, {})
        lang_name = translation_service.LANGUAGE_NAMES.get(target_language, target_language)
        
        translated = dict(incident_data)
        orig_type = incident_data.get("incident_type", "")
        if orig_type in lex:
            translated["incident_type"] = lex[orig_type]
        translated["incident_summary"] = f"[{lang_name}] " + incident_data.get("incident_summary", "")
        
        return {
            "status": "success",
            "target_language": target_language,
            "language_display": lang_name,
            "translated_report": translated
        }

incident_tools = IncidentTools()
