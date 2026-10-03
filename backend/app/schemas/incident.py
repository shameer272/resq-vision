from pydantic import BaseModel, Field
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
