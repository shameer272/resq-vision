import pytest
from app.safety.safety_service import safety_service
from app.schemas.incident import RawIncidentExtraction, Observation, PotentialConcern

def test_dangerous_action_rewriting():
    unsafe_input = "Bystanders should go and touch the electrical wire immediately to clear it."
    sanitized, mods = safety_service.sanitize_text(unsafe_input)
    assert len(mods) > 0
    assert "Do not approach or touch electrical cables" in sanitized

def test_overconfidence_calibrated():
    overconfident = "Fire is definitely present inside the car and guaranteed to blow up."
    sanitized, mods = safety_service.sanitize_text(overconfident)
    assert len(mods) > 0
    assert "Smoke-like material or thermal discoloration is visible" in sanitized

def test_medical_diagnosis_converted():
    diagnosis_text = "The driver has a fracture and internal bleeding."
    sanitized, mods = safety_service.sanitize_text(diagnosis_text)
    assert len(mods) > 0
    assert "precise medical diagnosis must be conducted by healthcare professionals" in sanitized

def test_incident_safety_validation_enforces_disclaimer():
    raw = RawIncidentExtraction(
        incident_summary="Small brush fire near highway.",
        incident_type="smoke_fire",
        observations=[
            Observation(
                description="Bystander should fight the fire yourself.",
                source="inferred",
                confidence="medium",
                evidence="Smoke rising"
            )
        ],
        user_reported_information=["Flames visible"],
        potential_concerns=[
            PotentialConcern(
                concern="Fire spreading",
                reason="Dry brush",
                evidence="Yellow grass",
                confidence="high",
                requires_human_verification=True
            )
        ],
        uncertainties=["Wind speed"],
        missing_information=["Water source"],
        recommended_information_to_communicate=["Call fire services"],
        confidence_notes=[],
        safety_disclaimer=""
    )
    validated, mods = safety_service.validate_and_sanitize_incident(raw)
    assert "Do not attempt direct firefighting" in validated.observations[0].description
    assert safety_service.MANDATORY_DISCLAIMER == validated.safety_disclaimer
    assert validated.potential_concerns[0].requires_human_verification is True
