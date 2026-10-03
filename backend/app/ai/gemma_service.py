import json
import time
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any, Literal
from app.core.config import settings
from app.schemas.incident import (
    RawIncidentExtraction,
    IncidentAnalysisResponse,
    Observation,
    PotentialConcern,
    ActionTraceStep,
    TimelineEvent,
    RAGSource
)
from app.safety.safety_service import safety_service
from app.rag.rag_service import rag_service

class GemmaServiceError(Exception):
    """Base exception for Gemma multimodal service errors."""
    pass

class APIKeyMissingError(GemmaServiceError):
    """Raised when GEMINI_API_KEY is not configured on the server."""
    pass

class GemmaService:
    """
    Multimodal Situation Intelligence Service powered by Gemma 4.
    Utilizes the official Google GenAI SDK (google-genai).
    Implements evidence-linked multimodal reasoning across image(s), text, voice, and context.
    """

    SYSTEM_INSTRUCTION = """You are ResQ Vision, an advanced Multimodal Emergency Situation Intelligence assistant powered by Gemma 4.
Your mission is to transform fragmented emergency scene inputs (photographs, bystander descriptions, voice transcripts, and context) into structured, evidence-linked, and explainable situational intelligence.

CRITICAL OPERATIONAL & SAFETY CONSTRAINTS:
1. You do NOT replace human emergency dispatchers or first responders.
2. You do NOT autonomously dispatch emergency vehicles or personnel.
3. You do NOT provide medical diagnosis or assess medical vital status.
4. You do NOT instruct untrained bystanders to take hazardous physical actions (e.g. entering burning structures, touching downed cables, approaching hazardous materials).
5. DATA PROVENANCE DISTINCTION:
   - "observed": Visual features directly identifiable in the image (e.g. damaged vehicle bumper, smoke plume).
   - "user_reported": Information explicitly provided by the user text or voice transcript.
   - "inferred": Situational deduction by the AI requiring on-scene verification.
6. EVIDENCE MANDATE: For every observation and potential concern, provide the exact visual or textual EVIDENCE.
7. EPISTEMIC HUMILITY: Explicitly identify uncertainties and missing information.

You must respond ONLY with a valid JSON object matching this schema:
{
  "incident_summary": "Concise 2-3 sentence overview of the situation",
  "incident_type": "One of: road_accident | smoke_fire | flooding | severe_weather | structural_damage | blocked_road | ambiguous | no_emergency",
  "observations": [
    {
      "description": "Specific observation",
      "source": "observed" | "user_reported" | "inferred",
      "confidence": "high" | "medium" | "low",
      "evidence": "Visual cues from image or specific phrase from user"
    }
  ],
  "user_reported_information": ["List of distinct facts reported by user"],
  "potential_concerns": [
    {
      "concern": "Identified potential safety hazard",
      "reason": "Operational reason or consequence",
      "evidence": "Observed visual cue or reported detail",
      "confidence": "high" | "medium" | "low",
      "requires_human_verification": true
    }
  ],
  "uncertainties": ["Things that cannot be determined from imagery alone (e.g. injuries, structural integrity, active fire)"],
  "missing_information": ["Critical items needed by dispatchers (e.g. exact mile-marker, hazardous placards, trapped counts)"],
  "recommended_information_to_communicate": ["Key bullet points for caller to tell emergency operators"],
  "confidence_notes": ["Evaluation of image quality, lighting, angle, and ambiguities"],
  "safety_disclaimer": "AI-generated decision support. Human verification required."
}
"""

    def __init__(self):
        self.model_name = settings.GEMMA_MODEL
        self.fallback_model = settings.FALLBACK_MODEL
        self._client = None

    @staticmethod
    def _is_transient_capacity_error(error: Exception) -> bool:
        """
        Determines whether an error represents a genuine transient model availability or capacity condition.
        - HTTP 429 (Too Many Requests / Resource Exhausted)
        - HTTP 503 (Service Unavailable / High Demand)
        
        Explicitly excludes:
        - 400 Bad Request / Invalid Argument
        - 401 Unauthorized / Invalid API Key
        - 403 Forbidden / Permission Denied
        - 404 Model Not Found
        - Standard programming / validation exceptions
        """
        if isinstance(error, (TypeError, ValueError, KeyError, AttributeError, IndexError, NameError)):
            return False

        code = getattr(error, "code", None)
        msg = str(error).lower()

        # Permanent client, auth, and parameter errors must NOT fall back
        if code in (400, 401, 403, 404):
            return False
        if any(term in msg for term in [
            "invalid api key", "api_key_invalid", "unauthenticated",
            "unauthorized", "permission_denied", "model not found",
            "not_found", "invalid_argument", "bad request"
        ]):
            return False

        # Genuine transient capacity / rate limit / availability conditions (429, 500, 502, 503, 504)
        if code in (429, 500, 502, 503, 504):
            return True

        transient_indicators = [
            "429", "500", "502", "503", "504", "resource_exhausted", "unavailable",
            "high demand", "spikes in demand", "temporarily unavailable",
            "overloaded", "rate limit", "too many requests", "internal error encountered",
            "internal error", "timeout", "timed out", "deadline_exceeded"
        ]
        return any(term in msg for term in transient_indicators)

    def _get_client(self):
        # Read from environment or settings
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise APIKeyMissingError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in the server .env or configuration tab to enable Gemma 4 multimodal inference."
            )
        
        from google import genai
        return genai.Client(api_key=api_key)

    def _build_prompt(
        self,
        user_text: Optional[str],
        voice_transcript: Optional[str],
        location: Optional[str],
        category: Optional[str],
        image_count: int,
        rag_sources: List[RAGSource]
    ) -> str:
        prompt_parts = [
            self.SYSTEM_INSTRUCTION,
            f"\n--- EMERGENCY INCIDENT INPUT ({image_count} image(s) attached) ---"
        ]
        
        if user_text:
            prompt_parts.append(f"\n[USER TEXT DESCRIPTION]:\n{user_text.strip()}")
        if voice_transcript:
            prompt_parts.append(f"\n[USER VOICE TRANSCRIPT]:\n{voice_transcript.strip()}")
        if location:
            prompt_parts.append(f"\n[REPORTED LOCATION/CONTEXT]:\n{location.strip()}")
        if category and category != "auto":
            prompt_parts.append(f"\n[REPORTED CATEGORY HINT]:\n{category.strip()}")

        if rag_sources:
            prompt_parts.append("\n[OFFICIAL PUBLIC SAFETY KNOWLEDGE BASE CITATIONS]:")
            for src in rag_sources:
                prompt_parts.append(f"- {src.title} ({src.source}): {src.relevance_snippet}")

        prompt_parts.append(
            "\nAnalyze all images and descriptions together. Adhere strictly to the required JSON schema."
        )
        return "\n".join(prompt_parts)

    async def analyze_multimodal(
        self,
        images: List[Tuple[bytes, str]], # List of (bytes, mime_type)
        user_text: Optional[str] = None,
        voice_transcript: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en"
    ) -> IncidentAnalysisResponse:
        """
        Executes multimodal analysis using Gemma 4 via Google GenAI SDK.
        Supports single and multi-image inputs (up to 4 images).
        """
        start_time = time.time()
        incident_id = f"RESQ-{int(time.time())}"
        now_iso = datetime.now(timezone.utc).isoformat()

        action_trace: List[ActionTraceStep] = []
        timeline: List[TimelineEvent] = []

        def log_step(
            step_name: str,
            desc: str,
            status: Literal["completed", "in_progress", "failed", "skipped"] = "completed",
            details: Optional[str] = None
        ):
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
            action_trace.append(ActionTraceStep(
                step=step_name,
                description=desc,
                status=status,
                timestamp=ts,
                details=details
            ))
            timeline.append(TimelineEvent(
                stage=step_name,
                title=desc,
                timestamp=ts,
                status="completed" if status == "completed" else "failed"
            ))

        log_step("Incident received", f"{len(images)} image(s) and accompanying context ingested")

        # 1. Query RAG Knowledge Base
        combined_text = f"{user_text or ''} {voice_transcript or ''} {location or ''}"
        rag_sources = rag_service.query(combined_text, incident_type=category, top_k=2)
        log_step("RAG Knowledge Retrieval", f"Retrieved {len(rag_sources)} official safety references from local KB")

        # 2. Get Client
        client = self._get_client()
        log_step("Gemma Client Initialization", f"Connected to Google GenAI SDK (Model: {self.model_name})")

        # 3. Construct Multimodal Contents
        from google.genai import types
        from PIL import Image
        import io

        contents = []
        # Add optimized image parts
        for idx, (img_bytes, mime_type) in enumerate(images):
            try:
                pil_img = Image.open(io.BytesIO(img_bytes))
                if pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")
                max_dim = 1200
                if max(pil_img.size) > max_dim:
                    pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                out_buf = io.BytesIO()
                pil_img.save(out_buf, format="JPEG", quality=85, optimize=True)
                opt_bytes = out_buf.getvalue()
                image_part = types.Part.from_bytes(data=opt_bytes, mime_type="image/jpeg")
            except Exception:
                image_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
            contents.append(image_part)
        
        # Add text prompt
        text_prompt = self._build_prompt(
            user_text=user_text,
            voice_transcript=voice_transcript,
            location=location,
            category=category,
            image_count=len(images),
            rag_sources=rag_sources
        )
        contents.append(text_prompt)
        log_step("Multimodal Fusion", f"Fused {len(images)} image(s) with textual context and RAG citations")

        # 4. Invoke Gemma 4
        active_model = self.model_name
        response_text = None
        fallback_reason = None

        config = types.GenerateContentConfig(
            temperature=0.2,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )

        # 1. Primary Model: Always attempt self.model_name (gemma-4-31b-it) first
        log_step("Multimodal Analysis", f"Executing multimodal inference on primary model {self.model_name}")
        inference_latency_sec = 0.0
        t_model_start = time.time()
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            inference_latency_sec = time.time() - t_model_start
            if response and response.text:
                response_text = response.text
                active_model = self.model_name
        except Exception as primary_error:
            is_transient = self._is_transient_capacity_error(primary_error)
            can_fallback = is_transient and self.fallback_model and self.fallback_model != self.model_name

            if can_fallback:
                fallback_reason = f"Primary model {self.model_name} transient error: {primary_error}"
                print(
                    f"[GemmaService] Primary model {self.model_name} encountered transient condition ({primary_error}). "
                    f"Initiating fallback to {self.fallback_model}..."
                )
                log_step(
                    "Model Fallback",
                    f"Fell back to {self.fallback_model} due to transient availability condition on {self.model_name}: {primary_error}"
                )
                try:
                    t_fb_start = time.time()
                    fb_response = client.models.generate_content(
                        model=self.fallback_model,
                        contents=contents,
                        config=config
                    )
                    inference_latency_sec = time.time() - t_fb_start
                    if fb_response and fb_response.text:
                        response_text = fb_response.text
                        active_model = self.fallback_model
                except Exception as fb_error:
                    log_step("Inference Error", f"Fallback model {self.fallback_model} also failed: {fb_error}", status="failed")
                    raise GemmaServiceError(
                        f"Gemma analysis failed on both primary model {self.model_name} ({primary_error}) "
                        f"and fallback model {self.fallback_model} ({fb_error})"
                    )
            else:
                # Auth errors, invalid API key, invalid model, bad requests, and programming errors MUST NOT silently fall back
                log_step("Inference Error", f"Primary model {self.model_name} failed: {primary_error}", status="failed")
                raise GemmaServiceError(f"Gemma analysis failed on primary model {self.model_name}: {primary_error}")

        if not response_text:
            log_step("Inference Error", f"Model {active_model} returned empty response", status="failed")
            raise GemmaServiceError(f"Gemma analysis failed: Model {active_model} returned empty response")

        # 5. Parse and Validate JSON
        parsed_data = None
        def _extract_json_str(text: str) -> str:
            cleaned = text.strip()
            if "```" in cleaned:
                f_start = cleaned.find("```")
                nl = cleaned.find("\n", f_start)
                f_end = cleaned.rfind("```")
                if nl != -1 and f_end > nl:
                    cleaned = cleaned[nl:f_end].strip()
            if "{" in cleaned and "}" in cleaned:
                s = cleaned.find("{")
                e = cleaned.rfind("}") + 1
                cleaned = cleaned[s:e]
            return cleaned

        try:
            json_str = _extract_json_str(response_text)
            raw_dict = json.loads(json_str)
            parsed_data = RawIncidentExtraction(**raw_dict)
            log_step("Observation Extraction", "Structured JSON extracted and validated against Pydantic schema")
        except Exception as parse_err:
            # Attempt repair prompt
            print(f"[GemmaService] JSON parse error: {parse_err}. Attempting repair prompt...")
            try:
                repair_prompt = f"The following JSON was malformed or missing required keys: {response_text}\n\nRepair and return ONLY valid JSON matching the exact schema."
                repair_res = client.models.generate_content(
                    model=active_model,
                    contents=[repair_prompt],
                    config=config
                )
                repair_text = repair_res.text
                if not repair_text:
                    raise GemmaServiceError(f"Model {active_model} returned empty repair response")
                rep_json_str = _extract_json_str(repair_text)
                raw_dict = json.loads(rep_json_str)
                parsed_data = RawIncidentExtraction(**raw_dict)
                log_step("JSON Repair", "Schema repaired via automated self-correction prompt")
            except Exception as rep_err:
                log_step("Schema Error", f"Validation failed after repair: {rep_err}", status="failed")
                raise GemmaServiceError(f"Malformed model response could not be validated: {rep_err}")

        # 6. Safety Validation Layer
        sanitized_data, safety_mods = safety_service.validate_and_sanitize_incident(parsed_data)
        log_step(
            "Safety Validation",
            f"Safety filter verified. {len(safety_mods)} calibrating adjustments made.",
            details="; ".join(safety_mods) if safety_mods else "Zero safety violations detected"
        )

        # 7. Construct Full Incident Analysis Response
        analysis_response = IncidentAnalysisResponse(
            incident_id=incident_id,
            timestamp=now_iso,
            location=location,
            language=language,
            image_count=len(images),
            image_names=[f"scene_image_{i+1}" for i in range(len(images))],
            incident_summary=sanitized_data.incident_summary,
            incident_type=sanitized_data.incident_type,
            observations=sanitized_data.observations,
            user_reported_information=sanitized_data.user_reported_information,
            potential_concerns=sanitized_data.potential_concerns,
            uncertainties=sanitized_data.uncertainties,
            missing_information=sanitized_data.missing_information,
            recommended_information_to_communicate=sanitized_data.recommended_information_to_communicate,
            confidence_notes=sanitized_data.confidence_notes,
            safety_disclaimer=sanitized_data.safety_disclaimer,
            rag_sources=rag_sources,
            action_trace=action_trace,
            timeline=timeline,
            model_used=active_model,
            primary_model=self.model_name,
            fallback_used=(active_model != self.model_name),
            fallback_reason=fallback_reason,
            inference_time_seconds=round(inference_latency_sec, 3),
            status="analyzed"
        )

        log_step("Report Generation", f"Completed in {round(time.time() - start_time, 2)}s")
        return analysis_response

gemma_service = GemmaService()
