import re
from typing import Dict, Any, List, Tuple
from app.schemas.incident import RawIncidentExtraction, Observation, PotentialConcern

class SafetyService:
    """
    Independent Safety Validation Layer for ResQ Vision.
    Enforces ethical AI constraints, prevents autonomous decisions,
    replaces medical diagnosis with objective descriptions,
    sanitizes dangerous bystander directives into safe stand-off advisories,
    and tempers overconfident assertions with evidence requirements.
    """

    DANGEROUS_ACTION_PATTERNS = [
        (r"\b(go\s+and\s+|immediately\s+)?(touch|disconnect|cut|move)\s+(the\s+)?(wire|cable|electrical|power\s+line)\b",
         "Do not approach or touch electrical cables or equipment; maintain safe perimeter and alert trained utility responders."),
        (r"\b(enter|go\s+inside|walk\s+into)\s+(the\s+)?(burning|collapsed|damaged|compromised)\s+(building|structure|house|room)\b",
         "Do not enter the compromised structure; remain outside the collapse perimeter until certified structural personnel arrive."),
        (r"\b(extinguish|fight|put\s+out)\s+(the\s+)?(fire|blaze|flames)\s+(yourself|personally)?\b",
         "Do not attempt direct firefighting; maintain distance upwind and communicate fire indicators to emergency services."),
        (r"\b(administer|inject|prescribe|give)\s+(medicine|medication|drugs|injection)\b",
         "Do not administer medication without certified medical direction; keep patient still and monitor breathing until EMS arrives."),
        (r"\b(move|pull\s+out|drag)\s+(the\s+)?(injured|victim|casualty|person)\b",
         "Do not move injured individuals unless there is an immediate, catastrophic threat (e.g. encroaching fire or explosion).")
    ]

    OVERCONFIDENT_PATTERNS = [
        (r"\b(fire\s+is\s+definitely\s+present|definitely\s+on\s+fire)\b",
         "Smoke-like material or thermal discoloration is visible; an active fire hazard cannot be confirmed from the image alone and requires verification."),
        (r"\b(guaranteed|certainly|100%\s+sure|without\s+a\s+doubt|undoubtedly)\b",
         "appears likely based on visible cues, subject to on-scene verification"),
        (r"\b(confirmed\s+fatalities|confirmed\s+dead)\b",
         "apparent motionless individual(s) observed; medical or vital status cannot be determined by AI visual analysis")
    ]

    DIAGNOSIS_PATTERNS = [
        (r"\b(patient\s+has\s+a\s+|suffering\s+from\s+a\s+)?(fracture|broken\s+bone|internal\s+bleeding|concussion|cardiac\s+arrest|stroke)\b",
         "individual exhibiting possible physical trauma or distress; precise medical diagnosis must be conducted by healthcare professionals")
    ]

    AUTONOMOUS_DISPATCH_PATTERNS = [
        (r"\b(dispatching\s+units|ambulance\s+has\s+been\s+dispatched|fire\s+truck\s+is\s+en\s+route|we\s+have\s+sent)\b",
         "Recommended for priority transmission to human emergency dispatchers (system does not autonomously deploy response units)")
    ]

    MANDATORY_DISCLAIMER = (
        "AI-Generated Operational Intelligence: This analysis is an informational aid powered by Gemma 4. "
        "It does NOT replace trained emergency dispatchers, provide medical diagnoses, or autonomously dispatch units. "
        "All observations and concerns require verification by on-scene human personnel."
    )

    def __init__(self):
        self.violations_logged = 0

    def sanitize_text(self, text: str) -> Tuple[str, List[str]]:
        """
        Scans a text string and rewrites unsafe phrasing.
        Returns the sanitized text and a list of modifications made.
        """
        modifications = []
        sanitized = text

        for pattern, replacement in self.DANGEROUS_ACTION_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
                modifications.append(f"Dangerous action instruction tempered: '{pattern}' -> safe protocol")
                self.violations_logged += 1

        for pattern, replacement in self.OVERCONFIDENT_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
                modifications.append(f"Overconfident assertion calibrated: '{pattern}'")
                self.violations_logged += 1

        for pattern, replacement in self.DIAGNOSIS_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
                modifications.append("Medical diagnosis converted to descriptive observational note")
                self.violations_logged += 1

        for pattern, replacement in self.AUTONOMOUS_DISPATCH_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
                modifications.append("Autonomous dispatch statement restricted to recommendation")
                self.violations_logged += 1

        return sanitized, modifications

    def validate_and_sanitize_incident(self, raw_data: RawIncidentExtraction) -> Tuple[RawIncidentExtraction, List[str]]:
        """
        Validates the entire incident analysis structure against safety rules.
        """
        all_modifications: List[str] = []

        # 1. Sanitize summary
        raw_data.incident_summary, mods = self.sanitize_text(raw_data.incident_summary)
        all_modifications.extend(mods)

        # 2. Validate and sanitize observations
        sanitized_obs = []
        for obs in raw_data.observations:
            desc, mods = self.sanitize_text(obs.description)
            all_modifications.extend(mods)
            evidence, emods = self.sanitize_text(obs.evidence or "Visual features from submitted scene image")
            all_modifications.extend(emods)
            
            # Enforce valid source
            source = obs.source if obs.source in ["observed", "user_reported", "inferred"] else "inferred"
            
            sanitized_obs.append(Observation(
                description=desc,
                source=source,
                confidence=obs.confidence if obs.confidence in ["high", "medium", "low"] else "medium",
                evidence=evidence
            ))
        raw_data.observations = sanitized_obs

        # 3. Validate and sanitize potential concerns
        sanitized_concerns = []
        for c in raw_data.potential_concerns:
            concern_text, cmods = self.sanitize_text(c.concern)
            all_modifications.extend(cmods)
            reason_text, rmods = self.sanitize_text(c.reason)
            all_modifications.extend(rmods)
            evidence_text, emods = self.sanitize_text(c.evidence or "Scene assessment cues")
            all_modifications.extend(emods)

            sanitized_concerns.append(PotentialConcern(
                concern=concern_text,
                reason=reason_text,
                evidence=evidence_text,
                confidence=c.confidence if c.confidence in ["high", "medium", "low"] else "medium",
                requires_human_verification=True
            ))
        raw_data.potential_concerns = sanitized_concerns

        # 4. Sanitize uncertainty and missing information
        raw_data.uncertainties = [self.sanitize_text(u)[0] for u in raw_data.uncertainties]
        raw_data.missing_information = [self.sanitize_text(m)[0] for m in raw_data.missing_information]
        raw_data.recommended_information_to_communicate = [
            self.sanitize_text(r)[0] for r in raw_data.recommended_information_to_communicate
        ]

        # 5. Always enforce mandatory safety disclaimer
        raw_data.safety_disclaimer = self.MANDATORY_DISCLAIMER

        return raw_data, all_modifications

safety_service = SafetyService()
