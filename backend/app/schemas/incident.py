from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal, Dict, Any

class Observation(BaseModel):
    description: str = Field(..., description="What was observed or inferred")
    source: Literal["observed", "user_reported", "inferred"] = Field(
        ..., description="Data provenance: directly observed in image, user reported, or inferred"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Confidence level of observation"
    )
    evidence: str = Field(
        ..., description="Visual or textual evidence supporting this observation"
    )

class PotentialConcern(BaseModel):
    concern: str = Field(..., description="Potential safety hazard or concern")
    reason: str = Field(..., description="Underlying mechanism or situational context")
    evidence: str = Field(..., description="Observable evidence indicating this potential concern")
    confidence: Literal["high", "medium", "low"] = Field(..., description="Confidence level")
    requires_human_verification: bool = Field(
        default=True, description="Safety mandate: must be verified by on-scene human responders"
    )

class RAGSource(BaseModel):
    id: str
    title: str
    source: str
    source_url: Optional[str] = None
    category: str
    relevance_snippet: str

class ActionTraceStep(BaseModel):
    step: str
    description: str
    status: Literal["completed", "in_progress", "failed", "skipped"]
    timestamp: str
    details: Optional[str] = None

class TimelineEvent(BaseModel):
    stage: str
    title: str
    timestamp: str
    status: Literal["completed", "pending", "failed"]

class RawIncidentExtraction(BaseModel):
    incident_summary: str = Field(..., description="Concise summary of the situation")
    incident_type: str = Field(..., description="Categorization (e.g. road_accident, smoke_fire, flooding, structural_damage, blocked_road, ambiguous)")
    observations: List[Observation] = Field(default_factory=list)
    user_reported_information: List[str] = Field(default_factory=list)
    potential_concerns: List[PotentialConcern] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommended_information_to_communicate: List[str] = Field(default_factory=list)
    confidence_notes: List[str] = Field(default_factory=list)
    safety_disclaimer: str = Field(
        default="AI-generated intelligence for operational support only. Does not replace professional human dispatch or medical diagnosis. Human verification required."
    )
    # Extended structured specification fields
    observed_evidence: List[str] = Field(default_factory=list, description="Observed evidence citations")
    potential_hazards: List[str] = Field(default_factory=list, description="Identified scene hazards")
    severity_estimate: Literal["critical", "high", "moderate", "low"] = Field(
        default="moderate", description="Severity estimate"
    )
    confidence_or_uncertainty: List[str] = Field(
        default_factory=list, description="Combined confidence and epistemic uncertainty indicators"
    )
    recommended_actions: List[str] = Field(
        default_factory=list, description="Actionable recommendations for human responders"
    )
    limitations: List[str] = Field(
        default_factory=list, description="Operational and observational constraints"
    )

    @model_validator(mode="after")
    def populate_extended_fields(self):
        if not self.observed_evidence and self.observations:
            self.observed_evidence = [
                f"[{obs.source.upper()}] {obs.description} (Evidence: {obs.evidence})"
                for obs in self.observations if obs.evidence
            ]
        if not self.potential_hazards and self.potential_concerns:
            self.potential_hazards = [
                f"{c.concern}: {c.reason}" for c in self.potential_concerns
            ]
        if not self.confidence_or_uncertainty:
            combined = []
            if self.confidence_notes:
                combined.extend(self.confidence_notes)
            if self.uncertainties:
                combined.extend(self.uncertainties)
            self.confidence_or_uncertainty = combined
        if not self.recommended_actions and self.recommended_information_to_communicate:
            self.recommended_actions = list(self.recommended_information_to_communicate)
        if not self.limitations:
            limits = [
                "Decision support only: does not substitute for certified fire, medical, or police dispatch.",
                "Multimodal evaluation bounded by submitted image resolution, perspective, and lighting."
            ]
            if self.uncertainties:
                for unc in self.uncertainties:
                    if unc not in limits:
                        limits.append(unc)
            self.limitations = limits

        # Calibrate severity estimate if default
        if self.severity_estimate == "moderate":
            high_types = {"smoke_fire", "flooding", "structural_damage"}
            has_high_concern = any(
                c.confidence == "high" for c in self.potential_concerns
            )
            has_urgent_keywords = any(
                kw in self.incident_summary.lower()
                for kw in ["fire", "explosion", "flame", "collapse", "drowning", "trapped"]
            )
            if has_urgent_keywords or (self.incident_type in high_types and has_high_concern):
                self.severity_estimate = "critical"
            elif self.incident_type in high_types or has_high_concern:
                self.severity_estimate = "high"
            elif self.incident_type in {"no_emergency", "ambiguous"}:
                self.severity_estimate = "low"
            else:
                self.severity_estimate = "moderate"

        return self


class IncidentAnalysisResponse(RawIncidentExtraction):
    incident_id: str
    timestamp: str
    location: Optional[str] = None
    language: str = "en"
    image_count: int = 1
    image_names: List[str] = Field(default_factory=list)
    location_context: Optional[Dict[str, Any]] = None
    rag_sources: List[RAGSource] = Field(default_factory=list)
    action_trace: List[ActionTraceStep] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    model_used: str = "gemma-4-31b-it"
    primary_model: str = "gemma-4-31b-it"
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    inference_time_seconds: Optional[float] = None
    status: str = "analyzed"

class ResponderChecklist(BaseModel):
    incident_id: str
    timestamp: str
    incident_type: str
    location: Optional[str] = None
    checklist_items: List[Dict[str, Any]]
    critical_cautions: List[str]
    human_verification_notice: str

class IncidentReport(BaseModel):
    report_id: str
    incident_id: str
    generated_at: str
    location: Optional[str] = None
    incident_type: str
    executive_summary: str
    methane_structure: Dict[str, str]
    observed_facts: List[Dict[str, str]]
    user_reported_facts: List[str]
    potential_hazards: List[Dict[str, Any]]
    critical_uncertainties: List[str]
    missing_critical_info: List[str]
    recommended_dispatch_advisory: List[str]
    knowledge_base_citations: List[Dict[str, str]]
    ai_limitations_and_disclaimer: str

class TranslationRequest(BaseModel):
    text: Optional[str] = ""
    target_language: Literal["en", "te", "hi"]
    preserve_uncertainty: bool = True
    incident_data: Optional[Dict[str, Any]] = None

class TranslationResponse(BaseModel):
    target_language: str
    translated_content: Dict[str, Any]
    language_display: str
    preservation_notice: str

class LocationContextRequest(BaseModel):
    location_query: str

class LocationContextResponse(BaseModel):
    query: str
    resolved_area: str
    approximate_coordinates: Optional[Dict[str, float]] = None
    terrain_notes: str
    nearest_landmarks: List[str]
    is_demo_data: bool
    status_label: str

class SaveIncidentRequest(BaseModel):
    incident_data: Dict[str, Any]

class EvaluationMetrics(BaseModel):
    total_scenarios_evaluated: int
    structured_output_success_rate: float
    required_field_completion_rate: float
    schema_validation_success_rate: float
    tool_call_success_rate: float
    multilingual_fidelity_rate: float
    safety_rule_violations_caught: int
    average_latency_seconds: float
    scenarios_summary: List[Dict[str, Any]]

class LiveEvaluationRequest(BaseModel):
    scenario_ids: Optional[List[str]] = None
    count: Optional[int] = 3

class LiveScenarioResult(BaseModel):
    id: str
    category: str
    title: str
    gemma_status: str  # "passed", "failed", "error"
    model_used: Optional[str] = None
    schema_valid: bool = False
    fields_complete: bool = False
    evidence_coverage: bool = False
    rag_citations_present: bool = False
    tools_executed: bool = False
    safety_pass: bool = False
    inference_latency_sec: float = 0.0
    error_message: Optional[str] = None
    action_trace_summary: Optional[str] = None

class LiveEvaluationMetrics(BaseModel):
    model_name: str
    model_id: str
    scenarios_executed: int
    successful_calls: int
    failed_calls: int
    schema_compliance_rate: float
    required_field_completion_rate: float
    evidence_completion_rate: float
    safety_validation_pass_rate: float
    rag_citation_rate: float
    tool_execution_rate: float
    average_inference_latency_seconds: float
    scenario_results: List[LiveScenarioResult]
