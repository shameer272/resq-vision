import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.core.config import settings

class ReportService:
    """
    Generates operational incident reports conforming to the international
    ETHANE / METHANE standard and produces downloadable PDF artifacts.
    """

    def generate_methane_report(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        incident_id = incident.get("incident_id", f"INC-{int(datetime.now().timestamp())}")
        created_at = incident.get("timestamp", datetime.now(timezone.utc).isoformat())
        location = incident.get("location") or "Unspecified location (Scene imagery provided)"
        incident_type = incident.get("incident_type", "unclassified_incident")
        summary = incident.get("incident_summary", "No summary provided.")

        observations = incident.get("observations", [])
        potential_concerns = incident.get("potential_concerns", [])
        user_reported = incident.get("user_reported_information", [])
        uncertainties = incident.get("uncertainties", [])
        missing_info = incident.get("missing_information", [])
        recommended_comm = incident.get("recommended_information_to_communicate", [])
        rag_sources = incident.get("rag_sources", [])

        # Formulate METHANE operational sections
        methane = {
            "M - Major Incident Standby": (
                "STANDBY / SITUATIONAL INTELLIGENCE. Field evidence indicates active hazard dynamics; "
                "on-scene incident commander must verify scale before full declaration."
            ),
            "E - Exact Location": location,
            "T - Type of Incident": incident_type.replace("_", " ").title(),
            "H - Hazards Present / Suspected": "; ".join([c.get("concern", "") for c in potential_concerns]) or "None clearly observable.",
            "A - Access and Egress": (
                "Assess road blockages and emergency vehicle corridors. Advise units to approach from upwind/uphill."
            ),
            "N - Number & Severity of Casualties": (
                "Unconfirmed from imagery alone. On-scene responder triage required. Do not rely on AI for vital signs."
            ),
            "E - Emergency Services Required": (
                "Recommended triage package: Police/Traffic control, Fire & Rescue standby, EMS evaluation based on verification."
            )
        }

        report_data = {
            "report_id": f"REP-{incident_id}",
            "incident_id": incident_id,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "location": location,
            "incident_type": incident_type,
            "executive_summary": summary,
            "methane_structure": methane,
            "observed_facts": [
                {
                    "description": o.get("description", ""),
                    "source": o.get("source", "observed"),
                    "confidence": o.get("confidence", "medium"),
                    "evidence": o.get("evidence", "")
                } for o in observations
            ],
            "user_reported_facts": user_reported,
            "potential_hazards": potential_concerns,
            "critical_uncertainties": uncertainties,
            "missing_critical_info": missing_info,
            "recommended_dispatch_advisory": recommended_comm,
            "knowledge_base_citations": [
                {
                    "id": s.get("id", ""),
                    "title": s.get("title", ""),
                    "source": s.get("source", "")
                } for s in rag_sources
            ],
            "ai_limitations_and_disclaimer": (
                "LEGAL & SAFETY NOTICE: This report was synthesized using multimodal reasoning by Gemma 4. "
                "It serves strictly as situational decision support for human responders. It does NOT constitute medical diagnosis, "
                "does NOT autonomously dispatch assets, and DOES NOT supersede official emergency communications."
            )
        }
        return report_data

    def generate_pdf(self, report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Renders a clean, high-contrast, professional emergency PDF document using ReportLab.
        Consumes either a synthesized METHANE report or raw incident intelligence, ensuring
        complete, non-empty situational intelligence in the output document.
        """
        import re
        def safe_xml(s: Any) -> str:
            if not s:
                return ""
            return re.sub(r"&(?!(amp|lt|gt|quot|apos);)", "&amp;", str(s))

        # 1. Normalize report_data: If passed raw incident intelligence or missing methane_structure/executive_summary,
        # compile full standardized METHANE report and merge.
        if not report_data.get("methane_structure") or not report_data.get("executive_summary"):
            compiled = self.generate_methane_report(report_data)
            merged = dict(compiled)
            for k, v in report_data.items():
                if v:
                    merged[k] = v
            if not report_data.get("executive_summary"):
                merged["executive_summary"] = compiled.get("executive_summary") or report_data.get("incident_summary", "Operational incident assessment compiled.")
            if not report_data.get("methane_structure"):
                merged["methane_structure"] = compiled.get("methane_structure", {})
            if not report_data.get("observed_facts"):
                merged["observed_facts"] = compiled.get("observed_facts", [])
            if not report_data.get("potential_hazards"):
                merged["potential_hazards"] = compiled.get("potential_hazards", [])
            if not report_data.get("ai_limitations_and_disclaimer"):
                merged["ai_limitations_and_disclaimer"] = compiled.get("ai_limitations_and_disclaimer", "")
            if not report_data.get("report_id"):
                merged["report_id"] = compiled.get("report_id", f"REP-{report_data.get('incident_id', 'INCIDENT')}")
            if not report_data.get("generated_at"):
                merged["generated_at"] = compiled.get("generated_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
            report_data = merged

        report_id = report_data.get("report_id") or (f"REP-{report_data.get('incident_id')}" if report_data.get('incident_id') else "REP-RESQ-OPERATIONAL")
        incident_id = report_data.get("incident_id") or report_id.replace("REP-", "")
        generated_at = report_data.get("generated_at") or report_data.get("timestamp") or report_data.get("saved_at") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        executive_summary = report_data.get("executive_summary") or report_data.get("incident_summary") or "Operational incident assessment compiled."

        methane = report_data.get("methane_structure") or {}
        if not methane:
            compiled = self.generate_methane_report(report_data)
            methane = compiled.get("methane_structure", {})

        observed_facts = report_data.get("observed_facts")
        if not observed_facts:
            raw_obs = report_data.get("observations", [])
            observed_facts = [
                {
                    "description": o.get("description", ""),
                    "source": o.get("source", "observed"),
                    "confidence": o.get("confidence", "verified"),
                    "evidence": o.get("evidence", "")
                } for o in raw_obs
            ]

        potential_hazards = report_data.get("potential_hazards")
        if not potential_hazards:
            raw_concerns = report_data.get("potential_concerns", [])
            potential_hazards = [
                {
                    "concern": c.get("concern") if isinstance(c, dict) else str(c),
                    "confidence": c.get("confidence", "medium") if isinstance(c, dict) else "medium",
                    "reason": c.get("reason", "") if isinstance(c, dict) else "",
                    "evidence": c.get("evidence", c.get("reason", "")) if isinstance(c, dict) else ""
                } for c in raw_concerns
            ]

        disclaimer = report_data.get("ai_limitations_and_disclaimer") or report_data.get("safety_disclaimer") or (
            "LEGAL & SAFETY NOTICE: This report was synthesized using multimodal reasoning by Gemma 4. "
            "It serves strictly as situational decision support for human responders. It does NOT constitute medical diagnosis, "
            "does NOT autonomously dispatch assets, and DOES NOT supersede official emergency communications."
        )

        if not output_path:
            filename = f"report_{incident_id}.pdf"
            output_path = os.path.join(settings.LOCAL_STORAGE_DIR, filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom palette
        header_color = colors.HexColor("#0f172a") # Slate 900
        accent_color = colors.HexColor("#dc2626") # Red 600
        muted_color = colors.HexColor("#475569")  # Slate 600

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=header_color
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=muted_color
        )
        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=header_color,
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1e293b")
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerCustom",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#991b1b")
        )

        elements = []

        # Header Banner
        elements.append(Paragraph("RESQ VISION — SITUATIONAL INTELLIGENCE REPORT", title_style))
        elements.append(Paragraph(
            f"Report ID: {safe_xml(report_id)}  |  Incident: {safe_xml(incident_id)}  |  Generated: {safe_xml(generated_at)}",
            subtitle_style
        ))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=6, spaceAfter=10))

        # Executive Summary
        elements.append(Paragraph("1. EXECUTIVE SITUATION SUMMARY", h2_style))
        elements.append(Paragraph(safe_xml(executive_summary), body_style))
        elements.append(Spacer(1, 8))

        # METHANE Matrix Table
        elements.append(Paragraph("2. METHANE OPERATIONAL FRAMEWORK", h2_style))
        table_data = [
            [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Operational Assessment</b>", body_style)]
        ]
        for key, val in methane.items():
            table_data.append([
                Paragraph(f"<b>{safe_xml(key)}</b>", body_style),
                Paragraph(safe_xml(val), body_style)
            ])

        m_table = Table(table_data, colWidths=[160, 380])
        m_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(m_table)
        elements.append(Spacer(1, 10))

        # Evidence-Linked Observations
        elements.append(Paragraph("3. EVIDENCE-LINKED OBSERVATIONS (DATA PROVENANCE)", h2_style))
        obs_table_data = [
            [Paragraph("<b>Source</b>", body_style), Paragraph("<b>Observation & Cues</b>", body_style), Paragraph("<b>Evidence / Confidence</b>", body_style)]
        ]
        for o in observed_facts:
            src_text = safe_xml(o.get('source', 'observed')).upper()
            desc_text = safe_xml(o.get('description', ''))
            evid_text = safe_xml(o.get('evidence', ''))
            conf_text = safe_xml(o.get('confidence', 'verified')).upper()
            obs_table_data.append([
                Paragraph(f"<font color='#0284c7'><b>{src_text}</b></font>", body_style),
                Paragraph(desc_text, body_style),
                Paragraph(f"{evid_text}<br/><b>Confidence:</b> {conf_text}", body_style)
            ])
        o_table = Table(obs_table_data, colWidths=[90, 270, 180])
        o_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(o_table)
        elements.append(Spacer(1, 10))

        # Potential Concerns & Safety
        elements.append(Paragraph("4. POTENTIAL CONCERNS & VERIFICATION MANDATES", h2_style))
        for idx, c in enumerate(potential_hazards, 1):
            concern_name = safe_xml(c.get('concern') or c.get('label') or f"Concern #{idx}")
            conf_level = safe_xml(c.get('confidence', 'medium')).upper()
            evid_str = safe_xml(c.get('evidence') or c.get('reason') or "Observable situational cues require verification.")
            concern_p = f"<b>{idx}. {concern_name}</b> (Confidence: {conf_level})<br/>" \
                        f"<i>Observable Evidence:</i> {evid_str}<br/>" \
                        f"<i>Action Requirement:</i> Human on-scene verification required before intervention."
            elements.append(Paragraph(concern_p, body_style))
            elements.append(Spacer(1, 4))

        # Disclaimer
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceBefore=10, spaceAfter=8))
        elements.append(Paragraph(safe_xml(disclaimer), disclaimer_style))

        doc.build(elements)
        return output_path

report_service = ReportService()
