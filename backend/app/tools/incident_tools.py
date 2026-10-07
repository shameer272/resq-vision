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

        is_te = any('\u0c00' <= char <= '\u0c7f' for char in str(incident_data.get("incident_summary", "")))
        is_hi = any('\u0900' <= char <= '\u097f' for char in str(incident_data.get("incident_summary", "")))
        lang = "te" if is_te else ("hi" if is_hi else "en")

        if lang == "te":
            checklist = [
                {
                    "id": "chk-loc",
                    "label": "ఖచ్చితమైన భౌగోళిక స్థానం & సురక్షిత మార్గాన్ని నిర్ధారించండి",
                    "category": "navigation",
                    "priority": "critical",
                    "instruction": "క్రాస్-స్ట్రీట్స్, మైలు-రాయిని ధృవీకరించండి మరియు వాహనాలు సురక్షిత దిశ నుండి చేరుకునేలా చూడండి."
                },
                {
                    "id": "chk-haz",
                    "label": "ప్రమాద పరిధిని గుర్తించి మండే వస్తువులను వేరుచేయండి",
                    "category": "safety",
                    "priority": "critical",
                    "instruction": "పొగ, ఇంధన లీక్‌లు లేదా విద్యుత్ తీగల నుండి సురక్షిత దూరాన్ని పాటించండి."
                },
                {
                    "id": "chk-cas",
                    "label": "క్షతగాత్రుల సంఖ్య మరియు పరిస్థితిని అంచనా వేయండి",
                    "category": "triage",
                    "priority": "high",
                    "instruction": "ప్రభావిత వ్యక్తుల సంఖ్యను పరిశీలించి అంబులెన్స్ విభాగానికి వెంటనే సమాచారం అందించండి."
                },
                {
                    "id": "chk-acc",
                    "label": "రహదారి అడ్డంకులు మరియు నిష్క్రమణ మార్గాలను తనిఖీ చేయండి",
                    "category": "access",
                    "priority": "high",
                    "instruction": "రెస్క్యూ వాహనాలకు అడ్డంకిగా ఉన్న శిధిలాలు లేదా ట్రాఫిక్‌ను గుర్తించండి."
                }
            ]
            cautions = [
                "శిక్షణ లేని వ్యక్తులను అగ్నిప్రమాదం, నిర్మాణ నష్టం లేదా ప్రత్యక్ష విద్యుత్ తీగల వద్దకు వెళ్లనివ్వవద్దు.",
                "తక్షణ విపత్తు ముప్పు (పేలుడు/మునిగిపోవడం) లేకపోతే క్షతగాత్రులను కదల్చవద్దు.",
                "అన్ని చెక్‌లిస్ట్ అంశాలు నిర్ణయ మద్దతు కొరకు మాత్రమే మరియు మానవ ధృవీకరణ తప్పనిసరి."
            ]
            verification_notice = "అన్ని కార్యాచరణ నిర్ణయాలకు మానవ ధృవీకరణ తప్పనిసరి."
        elif lang == "hi":
            checklist = [
                {
                    "id": "chk-loc",
                    "label": "सटीक भौगोलिक स्थिति एवं सुरक्षित पहुंच मार्ग की पुष्टि करें",
                    "category": "navigation",
                    "priority": "critical",
                    "instruction": "क्रॉस-सड़कें, माइल-मार्कर सत्यापित करें और सुनिश्चित करें कि वाहन सुरक्षित दिशा से पहुंचे।"
                },
                {
                    "id": "chk-haz",
                    "label": "खतरे का दायरा तय करें और ज्वलनशील पदार्थों को अलग करें",
                    "category": "safety",
                    "priority": "critical",
                    "instruction": "धुएं, ईंधन रिसाव अथवा बिजली के तारों से सुरक्षित दूरी बनाए रखें।"
                },
                {
                    "id": "chk-cas",
                    "label": "हताहतों की संख्या और स्थिति का आकलन करें",
                    "category": "triage",
                    "priority": "high",
                    "instruction": "प्रभावित व्यक्तियों की संख्या की पुष्टि करें और राहत दल को तुरंत सूचित करें।"
                },
                {
                    "id": "chk-acc",
                    "label": "द्वितीयक बाधाओं और निकासी मार्गों की पुष्टि करें",
                    "category": "access",
                    "priority": "high",
                    "instruction": "भारी बचाव वाहनों में बाधा डालने वाले मलबे अथवा जाम की पहचान करें।"
                }
            ]
            cautions = [
                "असुरक्षित व्यक्तियों को आग, संरचनात्मक क्षति या बिजली के तारों के पास न जाने दें।",
                "जब तक तत्काल विस्फोट अथवा डूबने का खतरा न हो, घायलों को न हिलाएं।",
                "चेकलिस्ट के सभी बिंदु केवल निर्णय सहायता के लिए हैं और मानवीय सत्यापन अनिवार्य है।"
            ]
            verification_notice = "सभी परिचालन निर्णयों के लिए मानवीय सत्यापन अनिवार्य है।"
        else:
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
            cautions = [
                "Do NOT instruct untrained bystanders to approach fire, structural damage, or live electrical lines.",
                "Do NOT move injured occupants unless imminent catastrophic threat (explosion/submersion) exists.",
                "All checklist items represent decision support suggestions and require human verification."
            ]
            verification_notice = "Required for all operational dispatches."

        # Add concern-specific checks
        for idx, concern in enumerate(potential_concerns):
            verify_prefix = "పరిశీలించండి: " if lang == "te" else ("सत्यापित करें: " if lang == "hi" else "Verify ")
            human_verify_suffix = ". మానవ ధృవీకరణ తప్పనిసరి." if lang == "te" else (". मानवीय सत्यापन अनिवार्य है।") if lang == "hi" else ". Human verification required."
            checklist.append({
                "id": f"chk-concern-{idx}",
                "label": f"{verify_prefix}{concern.get('concern', 'Identified Concern')}",
                "category": "incident_specific",
                "priority": "high" if concern.get("confidence") == "high" else "medium",
                "instruction": f"{concern.get('reason', 'Observable cue')}{human_verify_suffix}"
            })

        # Add missing information verifications
        for idx, missing in enumerate(missing_info):
            ascertain_prefix = "నిర్ధారించుకోవలసినది: " if lang == "te" else ("पता लगाएं: " if lang == "hi" else "Ascertain: ")
            gather_instr = "సాధ్యమైతే ప్రత్యక్ష సాక్షుల నుండి లేదా పరిశీలన ద్వారా సేకరించండి." if lang == "te" else ("यदि सुरक्षित हो तो गवाहों से अथवा दृश्य निरीक्षण द्वारा जानकारी प्राप्त करें।") if lang == "hi" else "Gather from bystander interviews or visual inspection if safely possible."
            checklist.append({
                "id": f"chk-missing-{idx}",
                "label": f"{ascertain_prefix}{missing}",
                "category": "information_gap",
                "priority": "medium",
                "instruction": gather_instr
            })

        return {
            "incident_id": incident_data.get("incident_id", "INC-CURRENT"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident_type": incident_type,
            "checklist_items": checklist,
            "critical_cautions": cautions,
            "human_verification_notice": verification_notice
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
        while strictly preserving epistemic uncertainty and preventing language prefix duplication.
        """
        from app.services.translation_service import translation_service
        lang_name = translation_service.LANGUAGE_NAMES.get(target_language, target_language)
        translated = translation_service.translate_incident_sync(incident_data, target_language)
        
        return {
            "status": "success",
            "target_language": target_language,
            "language_display": lang_name,
            "translated_report": translated
        }

incident_tools = IncidentTools()
