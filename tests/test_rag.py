import pytest
from app.rag.rag_service import rag_service

def test_rag_knowledge_entries_loaded():
    assert len(rag_service.knowledge_entries) >= 6

def test_rag_road_query():
    results = rag_service.query("Vehicle collision on highway with fuel leak", incident_type="road_accident")
    assert len(results) > 0
    categories = [r.category for r in results]
    assert "road_incidents" in categories or "emergency_reporting" in categories

def test_rag_flood_query():
    results = rag_service.query("Water rising up to vehicle doors in underpass", incident_type="flooding")
    assert len(results) > 0
    categories = [r.category for r in results]
    assert "flooding" in categories or "emergency_reporting" in categories

def test_rag_citations_have_sources():
    results = rag_service.query("Smoke and flames visible in residential unit")
    for r in results:
        assert r.source is not None
        assert len(r.title) > 0
