import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.core.config import settings

class StorageService:
    """
    Dual-mode persistence layer:
    - Primary: MongoDB (if MONGODB_URI is provided and accessible)
    - Fallback: Local JSON database (data/storage/incidents.json)
    Never crashes if MongoDB is unconfigured or unreachable.
    """

    def __init__(self):
        self.local_file = os.path.join(settings.LOCAL_STORAGE_DIR, "incidents.json")
        self.mongo_client = None
        self.db = None
        self.using_mongo = False
        self._init_backend()

    def _init_backend(self):
        if settings.MONGODB_URI:
            try:
                from pymongo import MongoClient
                self.mongo_client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
                # verify connection
                self.mongo_client.admin.command('ping')
                self.db = self.mongo_client[settings.DATABASE_NAME]
                self.using_mongo = True
                print("[Storage] Connected to MongoDB.")
            except Exception as e:
                print(f"[Storage] MongoDB not available ({e}). Falling back to local storage.")
                self.using_mongo = False
        else:
            self.using_mongo = False

        try:
            os.makedirs(os.path.dirname(self.local_file), exist_ok=True)
            if not os.path.exists(self.local_file):
                with open(self.local_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
        except OSError as e:
            print(f"[Storage] Notice: Local storage file init failed ({e}).")

    def _read_local_incidents(self) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(self.local_file):
                return []
            with open(self.local_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_local_incidents(self, incidents: List[Dict[str, Any]]):
        try:
            os.makedirs(os.path.dirname(self.local_file), exist_ok=True)
            with open(self.local_file, "w", encoding="utf-8") as f:
                json.dump(incidents, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Storage] Warning: Failed to write to local storage file: {e}")

    def save_incident(self, incident_data: Dict[str, Any]) -> str:
        incident_id = incident_data.get("incident_id")
        if not incident_id:
            incident_id = f"INC-{int(datetime.now().timestamp())}"
            incident_data["incident_id"] = incident_id
        
        if "saved_at" not in incident_data:
            incident_data["saved_at"] = datetime.now(timezone.utc).isoformat()

        if self.using_mongo and self.db is not None:
            try:
                self.db.incidents.update_one(
                    {"incident_id": incident_id},
                    {"$set": incident_data},
                    upsert=True
                )
                return incident_id
            except Exception as e:
                print(f"[Storage] MongoDB write failed ({e}); falling back to local file.")

        # Local fallback
        incidents = self._read_local_incidents()
        # Check if already exists
        existing_idx = next((i for i, item in enumerate(incidents) if item.get("incident_id") == incident_id), None)
        if existing_idx is not None:
            incidents[existing_idx] = incident_data
        else:
            incidents.insert(0, incident_data)
        
        self._write_local_incidents(incidents)
        return incident_id

    def get_incidents(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.using_mongo and self.db is not None:
            try:
                items = list(self.db.incidents.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
                return items
            except Exception as e:
                print(f"[Storage] MongoDB read failed ({e}); using local file.")
        
        return self._read_local_incidents()[:limit]

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        if self.using_mongo and self.db is not None:
            try:
                doc = self.db.incidents.find_one({"incident_id": incident_id}, {"_id": 0})
                if doc:
                    return doc
            except Exception:
                pass
        
        incidents = self._read_local_incidents()
        for inc in incidents:
            if inc.get("incident_id") == incident_id:
                return inc
        return None

    def delete_incident(self, incident_id: str) -> bool:
        deleted = False
        if self.using_mongo and self.db is not None:
            try:
                res = self.db.incidents.delete_one({"incident_id": incident_id})
                deleted = res.deleted_count > 0
            except Exception:
                pass

        incidents = self._read_local_incidents()
        new_list = [inc for inc in incidents if inc.get("incident_id") != incident_id]
        if len(new_list) < len(incidents):
            self._write_local_incidents(new_list)
            deleted = True

        return deleted

storage_service = StorageService()
