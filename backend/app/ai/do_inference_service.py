import base64
import io
import json
import time
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any, Literal
import httpx
from PIL import Image

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

class DOInferenceServiceError(Exception):
    """Base exception for DigitalOcean Inference service errors."""
    pass

class DOAuthKeyMissingError(DOInferenceServiceError):
    """Raised when DO_INFERENCE_TOKEN is not configured."""
    pass

class DigitalOceanInferenceService:
    """
    Multimodal Situation Intelligence Service powered by DigitalOcean GenAI Serverless Inference.
    Connects to official DigitalOcean Inference endpoints (https://inference.do-ai.run/v1)
    using OpenAI-compatible chat completions with open-weight foundation models.
    Default Model: meta-llama/Meta-Llama-3.2-11B-Vision-Instruct
    Fallback Model: meta-llama/Llama-3.3-70B-Instruct
    """

    SYSTEM_INSTRUCTION = """You are ResQ Vision, an advanced Multimodal Emergency Situation Intelligence assistant powered by DigitalOcean GenAI Inference.
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
        self.endpoint = settings.DO_INFERENCE_ENDPOINT
        self.model_name = settings.DO_MODEL
        self.fallback_model = settings.DO_FALLBACK_MODEL

    def _get_token(self) -> str:
        token = settings.DO_INFERENCE_TOKEN.strip()
        if not token:
            raise DOAuthKeyMissingError(
                "DigitalOcean Inference token is not configured. "
                "Please set DO_INFERENCE_TOKEN in .env or server settings to enable DigitalOcean Inference."
            )
        return token

    @staticmethod
    def _is_transient_error(status_code: int, error_text: str) -> bool:
        """Determines if the HTTP response indicates a transient capacity or rate-limit condition."""
        if status_code in (429, 500, 502, 503, 504):
            return True
        lowered = error_text.lower()
        transient_phrases = ["rate limit", "too many requests", "capacity", "overloaded", "timeout", "temporarily unavailable"]
        return any(p in lowered for p in transient_phrases)

    @staticmethod
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

    def _build_prompt_text(
        self,
        user_text: Optional[str],
        voice_transcript: Optional[str],
        location: Optional[str],
        category: Optional[str],
        image_count: int,
        rag_sources: List[RAGSource]
    ) -> str:
        prompt_parts = [
            f"--- EMERGENCY INCIDENT INPUT ({image_count} image(s) attached) ---"
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
            "\nAnalyze all provided inputs (imagery, bystander notes, voice transcript). Adhere strictly to the required JSON schema without any surrounding markdown commentary."
        )
        return "\n".join(prompt_parts)

    def _prepare_user_content(
        self,
        prompt_text: str,
        images: List[Tuple[bytes, str]]
    ) -> Any:
        if not images:
            return prompt_text

        content_parts: List[Dict[str, Any]] = [
            {"type": "text", "text": prompt_text}
        ]

        for img_bytes, mime_type in images:
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
                actual_mime = "image/jpeg"
            except Exception:
                opt_bytes = img_bytes
                actual_mime = mime_type or "image/jpeg"

            b64_data = base64.b64encode(opt_bytes).decode("utf-8")
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{actual_mime};base64,{b64_data}"
                }
            })

        return content_parts

    async def analyze_multimodal(
        self,
        images: List[Tuple[bytes, str]],
        user_text: Optional[str] = None,
        voice_transcript: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en"
    ) -> IncidentAnalysisResponse:
        """
        Executes multimodal analysis via DigitalOcean GenAI Serverless Inference API.
        """
        start_time = time.time()
        incident_id = f"RESQ-DO-{int(time.time())}"
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

        # 2. Validate token and construct payload
        token = self._get_token()
        log_step("DigitalOcean Client Initialization", f"Targeting {self.endpoint} (Model: {self.model_name})")

        prompt_text = self._build_prompt_text(
            user_text=user_text,
            voice_transcript=voice_transcript,
            location=location,
            category=category,
            image_count=len(images),
            rag_sources=rag_sources
        )

        user_content = self._prepare_user_content(prompt_text, images)
        messages = [
            {"role": "system", "content": self.SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_content}
        ]

        active_model = self.model_name
        fallback_used = False
        fallback_reason = None
        response_text = None
        inference_latency_sec = 0.0

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        completions_url = f"{self.endpoint.rstrip('/')}/chat/completions"

        # 3. Execute inference with transient fallback
        async with httpx.AsyncClient(timeout=60.0) as client:
            t0 = time.time()
            try:
                log_step("Model Inference", f"Executing DigitalOcean inference with {active_model}...")
                resp = await client.post(
                    completions_url,
                    headers=headers,
                    json={
                        "model": active_model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 2048,
                        "response_format": {"type": "json_object"}
                    }
                )
                if resp.status_code == 400 and "response_format" in resp.text:
                    # Retry without response_format if model endpoint doesn't support structured outputs
                    resp = await client.post(
                        completions_url,
                        headers=headers,
                        json={
                            "model": active_model,
                            "messages": messages,
                            "temperature": 0.2,
                            "max_tokens": 2048
                        }
                    )
                
                if resp.status_code >= 400:
                    err_body = resp.text
                    if self._is_transient_error(resp.status_code, err_body):
                        log_step(
                            "Transient Warning",
                            f"Primary model {active_model} encountered capacity/rate limit ({resp.status_code}). Triggering fallback.",
                            status="completed"
                        )
                        fallback_used = True
                        fallback_reason = f"HTTP {resp.status_code}: {err_body[:200]}"
                        active_model = self.fallback_model
                        
                        # Fallback call
                        t_fb = time.time()
                        fb_resp = await client.post(
                            completions_url,
                            headers=headers,
                            json={
                                "model": active_model,
                                "messages": messages,
                                "temperature": 0.2,
                                "max_tokens": 2048
                            }
                        )
                        if fb_resp.status_code >= 400:
                            raise DOInferenceServiceError(
                                f"DigitalOcean fallback model {active_model} also failed with HTTP {fb_resp.status_code}: {fb_resp.text[:200]}"
                            )
                        fb_data = fb_resp.json()
                        response_text = fb_data["choices"][0]["message"]["content"]
                        inference_latency_sec = time.time() - t_fb
                    else:
                        raise DOInferenceServiceError(
                            f"DigitalOcean Inference failed with HTTP {resp.status_code}: {err_body[:300]}"
                        )
                else:
                    data = resp.json()
                    response_text = data["choices"][0]["message"]["content"]
                    inference_latency_sec = time.time() - t0

            except httpx.RequestError as req_err:
                log_step("Inference Error", f"Network error connecting to DigitalOcean: {req_err}", status="failed")
                raise DOInferenceServiceError(f"Failed to connect to DigitalOcean Inference endpoint: {req_err}")

        if not response_text:
            log_step("Inference Error", f"Model {active_model} returned empty response", status="failed")
            raise DOInferenceServiceError(f"DigitalOcean model {active_model} returned empty response")

        # 4. Parse JSON Response
        try:
            json_str = self._extract_json_str(response_text)
            raw_dict = json.loads(json_str)
            parsed_data = RawIncidentExtraction(**raw_dict)
            log_step("Observation Extraction", f"Structured JSON extracted from DigitalOcean ({active_model})")
        except Exception as parse_err:
            log_step("Schema Error", f"Validation failed on model response: {parse_err}", status="failed")
            raise DOInferenceServiceError(f"Malformed DigitalOcean model response could not be validated: {parse_err}")

        # 5. Deterministic Safety Validation Layer
        sanitized_data, safety_mods = safety_service.validate_and_sanitize_incident(parsed_data)
        log_step(
            "Safety Validation",
            f"Safety filter verified. {len(safety_mods)} calibrating adjustments made.",
            details="; ".join(safety_mods) if safety_mods else "Zero safety violations detected"
        )

        # 6. Construct IncidentAnalysisResponse
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
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            inference_time_seconds=round(inference_latency_sec, 3),
            status="analyzed"
        )

        log_step("Report Generation", f"Completed in {round(time.time() - start_time, 2)}s")
        return analysis_response

do_inference_service = DigitalOceanInferenceService()
