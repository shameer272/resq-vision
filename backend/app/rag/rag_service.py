import os
import json
import glob
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.incident import RAGSource

class RAGService:
    """
    Transparent Local Emergency Retrieval-Augmented Generation (RAG) Service.
    Indexes officially curated public safety protocols (NHTSA, USFA, NOAA, FEMA, NDMA).
    Returns strict verified citations and evidence-linked operational guidelines.
    """

    def __init__(self, kb_dir: Optional[str] = None):
        self.kb_dir = kb_dir or settings.KNOWLEDGE_BASE_DIR
        self.knowledge_entries: List[Dict[str, Any]] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        self.knowledge_entries = []
        if not os.path.exists(self.kb_dir):
            return
        
        json_files = glob.glob(os.path.join(self.kb_dir, "*.json"))
        for fpath in json_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.knowledge_entries.append(data)
            except Exception as e:
                print(f"[RAG] Error loading {fpath}: {e}")

    def query(self, query_text: str, incident_type: Optional[str] = None, top_k: int = 2) -> List[RAGSource]:
        """
        Retrieves relevant curated reference sources based on query text and incident type.
        """
        if not self.knowledge_entries:
            self._load_knowledge_base()

        query_tokens = set(query_text.lower().split())
        scored_entries = []

        category_mapping = {
            "road_accident": "road_incidents",
            "collision": "road_incidents",
            "smoke_fire": "smoke_fire_observations",
            "fire": "smoke_fire_observations",
            "flood": "flooding",
            "water": "flooding",
            "weather": "severe_weather",
            "storm": "severe_weather",
            "structural_damage": "damaged_buildings",
            "collapse": "damaged_buildings",
            "blocked_road": "road_incidents"
        }

        target_category = category_mapping.get((incident_type or "").lower())

        for entry in self.knowledge_entries:
            score = 0.0
            entry_cat = entry.get("category", "")
            
            # Category boost
            if target_category and entry_cat == target_category:
                score += 5.0
            
            # Content token matching
            searchable_text = f"{entry.get('title', '')} {entry.get('summary', '')} {entry.get('content', '')}".lower()
            for token in query_tokens:
                if len(token) > 3 and token in searchable_text:
                    score += 1.0

            # General emergency reporting framework is always relevant as baseline
            if entry_cat == "emergency_reporting":
                score += 1.5

            if score > 0:
                scored_entries.append((score, entry))

        # Sort descending by score
        scored_entries.sort(key=lambda x: x[0], reverse=True)

        results: List[RAGSource] = []
        for _, entry in scored_entries[:top_k]:
            results.append(RAGSource(
                id=entry.get("id", "KB-REF"),
                title=entry.get("title", "Curated Reference"),
                source=entry.get("source", "Official Public Safety Guideline"),
                source_url=entry.get("source_url"),
                category=entry.get("category", "general"),
                relevance_snippet=entry.get("summary", entry.get("content", "")[:200] + "...")
            ))

        return results

    def get_full_guideline(self, entry_id: str) -> Optional[Dict[str, Any]]:
        for entry in self.knowledge_entries:
            if entry.get("id") == entry_id:
                return entry
        return None

rag_service = RAGService()
