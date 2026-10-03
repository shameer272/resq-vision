import pytest
from app.schemas.incident import (
    Observation,
    PotentialConcern,
    RawIncidentExtraction,
    IncidentAnalysisResponse
)

def test_observation_provenance():
    # Valid observation
    obs = Observation(
        description="Crushed front bumper",
        source="observed",
        confidence="high",
        evidence="Visible front-end impact crushing"
    )
    assert obs.source == "observed"
    assert obs.confidence == "high"

def test_potential_concern_requires_verification():
    concern = PotentialConcern(
        concern="Electrical wire hazard",
        reason="Overhead lines on ground",
        evidence="Black cables on wet road",
        confidence="medium",
        requires_human_verification=True
    )
    assert concern.requires_human_verification is True

def test_raw_incident_extraction_validation():
    data = {
        "incident_summary": "Two vehicles collided at intersection.",
        "incident_type": "road_accident",
        "observations": [
            {
                "description": "Sedan with front impact",
                "source": "observed",
                "confidence": "high",
                "evidence": "Bent bumper and broken headlight"
            }
        ],
        "user_reported_information": ["Loud bang heard"],
        "potential_concerns": [
            {
                "concern": "Traffic obstruction",
                "reason": "Blocking middle lane",
                "evidence": "Vehicle positioned perpendicularly",
                "confidence": "high",
                "requires_human_verification": True
            }
        ],
        "uncertainties": ["Injury severity unknown"],
        "missing_information": ["Number of passengers"],
        "recommended_information_to_communicate": ["Location and lane blockage"],
        "confidence_notes": ["Good lighting"],
        "safety_disclaimer": "Human verification required."
    }
    extracted = RawIncidentExtraction(**data)
    assert extracted.incident_type == "road_accident"
    assert len(extracted.observations) == 1
    assert len(extracted.potential_concerns) == 1
