import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.core.config import settings
from app.ai.gemma_service import gemma_service, APIKeyMissingError, GemmaServiceError
from app.tools.incident_tools import incident_tools
from app.agent.agent_service import agent_service
from app.services.translation_service import translation_service
from app.services.storage_service import storage_service
from app.services.report_service import report_service
from app.services.evaluation_service import evaluation_service
from app.schemas.incident import (
    IncidentAnalysisResponse,
    IncidentReport,
    ResponderChecklist,
    TranslationRequest,
    TranslationResponse,
    SaveIncidentRequest,
    EvaluationMetrics,
    LiveEvaluationRequest,
    LiveEvaluationMetrics
)

router = APIRouter()

class SetApiKeyRequest(BaseModel):
    api_key: str

@router.get("/health", tags=["System"])
async def health_check():
    """System health check and configuration audit."""
    has_api_key = bool(settings.GEMINI_API_KEY)
    masked_key = f"{settings.GEMINI_API_KEY[:4]}...{settings.GEMINI_API_KEY[-4:]}" if has_api_key and len(settings.GEMINI_API_KEY) > 8 else ("Configured" if has_api_key else "Not Configured")
    
    return {
        "status": "healthy",
        "service": "ResQ Vision Multimodal Emergency Situation Intelligence",
        "model": settings.GEMMA_MODEL,
        "fallback_model": settings.FALLBACK_MODEL,
        "sdk": "google-genai",
        "gemini_api_key_configured": has_api_key,
        "api_key_preview": masked_key,
        "storage_mode": "MongoDB" if storage_service.using_mongo else "Local File Storage",
        "rag_knowledge_base_items": len(evaluation_service.get_scenarios())
    }

@router.post("/api/config/api-key", tags=["Configuration"])
async def set_api_key(req: SetApiKeyRequest):
    """
    Sets the Gemini API Key server-side for the current session.
    Never exposes this key back to the client.
    """
    cleaned = req.api_key.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="API Key cannot be blank")
    
    settings.GEMINI_API_KEY = cleaned
    return {
        "status": "success",
        "message": f"Server-side Gemini API key configured successfully for model {settings.GEMMA_MODEL}."
    }

@router.post("/api/analyze", response_model=IncidentAnalysisResponse, tags=["Analysis"])
async def analyze_incident(
    image: UploadFile = File(...),
    user_text: Optional[str] = Form(None),
    voice_transcript: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    language: Optional[str] = Form("en")
):
    """
    Primary Multimodal Situation Intelligence Endpoint.
    Analyzes single scene image + text + voice transcript + geographic context using Gemma 4.
    """
    # 1. Validate file extension
    filename = image.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if not image.filename or ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format: '{ext}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Read bytes and check size
    img_bytes = await image.read()
    if len(img_bytes) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded image exceeds maximum allowed limit of {settings.MAX_IMAGE_SIZE_MB}MB."
        )

    mime_type = image.content_type or "image/jpeg"

    try:
        result = await gemma_service.analyze_multimodal(
            images=[(img_bytes, mime_type)],
            user_text=user_text,
            voice_transcript=voice_transcript,
            location=location,
            category=category,
            language=language or "en"
        )
        # Automatically persist to storage
        storage_service.save_incident(result.model_dump())
        return result
    except APIKeyMissingError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except GemmaServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during incident analysis: {str(e)}"
        )

@router.post("/api/analyze/multi-image", response_model=IncidentAnalysisResponse, tags=["Analysis"])
async def analyze_multi_image_incident(
    images: List[UploadFile] = File(...),
    user_text: Optional[str] = Form(None),
    voice_transcript: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    language: Optional[str] = Form("en")
):
    """
    Multi-Image Situation Fusion Endpoint.
    Analyzes up to 4 scene perspectives simultaneously with Gemma 4 multimodal reasoning.
    """
    if len(images) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A maximum of 4 images can be processed simultaneously for multi-image fusion."
        )

    processed_images = []
    for img in images:
        filename = img.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        if not img.filename or ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image {filename} has unsupported format '{ext}'."
            )
        data = await img.read()
        if len(data) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image {img.filename} exceeds {settings.MAX_IMAGE_SIZE_MB}MB size limit."
            )
        processed_images.append((data, img.content_type or "image/jpeg"))

    try:
        result = await gemma_service.analyze_multimodal(
            images=processed_images,
            user_text=user_text,
            voice_transcript=voice_transcript,
            location=location,
            category=category,
            language=language or "en"
        )
        storage_service.save_incident(result.model_dump())
        return result
    except APIKeyMissingError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except GemmaServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/api/incident/report", response_model=IncidentReport, tags=["Tools"])
async def generate_report_endpoint(incident_data: dict):
    """
    Tool Endpoint: generate_incident_report
    Generates a structured METHANE incident report from incident data.
    """
    tool_res = incident_tools.generate_incident_report(incident_data)
    if "error" in tool_res:
        raise HTTPException(status_code=400, detail=tool_res["error"])
    return tool_res["report"]

@router.post("/api/incident/checklist", response_model=ResponderChecklist, tags=["Tools"])
async def generate_checklist_endpoint(incident_data: dict):
    """
    Tool Endpoint: generate_responder_checklist
    Generates operational triage checklist for human first responders.
    """
    return incident_tools.generate_responder_checklist(incident_data)

@router.post("/api/translate", response_model=TranslationResponse, tags=["Multilingual"])
async def translate_endpoint(req: TranslationRequest):
    """
    Translates incident intelligence to Telugu or Hindi while strictly preserving epistemic uncertainty.
    """
    incident_dict = req.incident_data or {"incident_summary": req.text}
    translated = await translation_service.translate_incident_data(incident_dict, req.target_language)
    return TranslationResponse(
        target_language=req.target_language,
        translated_content=translated["translated_content"],
        language_display=translated["language_display"],
        preservation_notice=translated["preservation_notice"]
    )

@router.post("/api/incident/save", tags=["Incidents"])
async def save_incident_endpoint(req: SaveIncidentRequest):
    """Saves incident intelligence to persistence storage."""
    inc_id = storage_service.save_incident(req.incident_data)
    return {"status": "success", "incident_id": inc_id}

@router.get("/api/incidents", tags=["Incidents"])
async def list_incidents(limit: int = 50):
    """Retrieves history of analyzed incidents."""
    return storage_service.get_incidents(limit=limit)

@router.get("/api/incidents/{incident_id}", tags=["Incidents"])
async def get_incident(incident_id: str):
    """Retrieves specific incident by ID."""
    inc = storage_service.get_incident_by_id(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return inc

@router.delete("/api/incidents/{incident_id}", tags=["Incidents"])
async def delete_incident(incident_id: str):
    """Deletes an incident by ID."""
    success = storage_service.delete_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found or could not be removed.")
    return {"status": "success", "deleted_incident_id": incident_id}

@router.post("/api/export", tags=["Tools"])
async def export_report_endpoint(report_data: dict, format: str = "pdf"):
    """Generates and exports an incident report."""
    if format.lower() == "pdf":
        filepath = report_service.generate_pdf(report_data)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Failed to compile PDF.")
        filename = os.path.basename(filepath)
        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    return {"status": "success", "data": report_data}

@router.get("/api/evaluation", response_model=EvaluationMetrics, tags=["Evaluation"])
async def run_evaluation_suite():
    """Runs the 20-scenario local regression benchmark suite and returns system metrics."""
    return evaluation_service.run_benchmark_suite()

@router.post("/api/evaluation/live", response_model=LiveEvaluationMetrics, tags=["Evaluation"])
async def run_live_evaluation_endpoint(req: LiveEvaluationRequest):
    """Executes real Gemma 4 inference across selected benchmark scenarios and returns live metrics."""
    return await evaluation_service.run_live_evaluation(
        scenario_ids=req.scenario_ids,
        count=req.count
    )

@router.get("/api/demo-scenarios", tags=["Demo"])
async def get_demo_scenarios():
    """Returns the 4 preloaded safe demonstration scenarios with benchmark inputs."""
    return evaluation_service.get_demo_scenarios()

@router.post("/api/agent/workflow", tags=["Agent"])
async def execute_agent_workflow(payload: dict):
    """
    Executes multi-step agentic workflow using the safe tool allowlist.
    """
    incident_data = payload.get("incident_data", {})
    goals = payload.get("goals")
    return await agent_service.run_agentic_workflow(incident_data, goals)
