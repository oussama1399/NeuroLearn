from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class JSONDataStore:
    """Simple JSON-backed store used to persist generated course content."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        base_path = (
            Path(storage_path)
            if storage_path is not None
            else Path(__file__).resolve().parents[1] / "neurolearn_data.json"
        )
        self._storage_path = base_path.expanduser().resolve()
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {"courses": []}
        self._load_data()

    def save_new_course(
        self,
        *,
        filename: str,
        summary: str,
        quiz_data: Any,
        flashcards_data: Any,
    ) -> str:
        """Persist a newly generated course and return its identifier."""

        course_id = str(uuid.uuid4())
        creation_date = datetime.now().isoformat(timespec="seconds")

        new_course = {
            "id": course_id,
            "filename": filename,
            "creation_date": creation_date,
            "summary": summary,
            "quiz": quiz_data,
            "flashcards": flashcards_data,
        }

        self._data.setdefault("courses", []).append(new_course)
        self._save_data()
        return course_id

    def get_all_course_metadata(self) -> List[Dict[str, str]]:
        """Return metadata for all stored courses ordered by creation date desc."""

        courses = list(self._data.get("courses", []))
        try:
            courses.sort(key=lambda course: course.get("creation_date", ""), reverse=True)
        except TypeError:
            pass

        metadata: List[Dict[str, str]] = []
        for course in courses:
            metadata.append(
                {
                    "id": str(course.get("id", "")),
                    "filename": str(course.get("filename", "Cours")),
                    "creation_date": str(course.get("creation_date", "")),
                }
            )
        return metadata

    def get_course_by_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        for course in self._data.get("courses", []):
            if course.get("id") == course_id:
                return course
        return None

    def delete_course(self, course_id: str) -> bool:
        """Delete a course by its ID. Returns True if deleted, False if not found."""
        courses = self._data.get("courses", [])
        for i, course in enumerate(courses):
            if course.get("id") == course_id:
                courses.pop(i)
                self._save_data()
                return True
        return False

    def _load_data(self) -> None:
        if not self._storage_path.exists():
            self._save_data()
            return

        try:
            with self._storage_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError):
            backup_path = self._storage_path.with_suffix(self._storage_path.suffix + ".bak")
            try:
                self._storage_path.replace(backup_path)
            except OSError:
                pass
            self._data = {"courses": []}
            self._save_data()
            return

        if isinstance(payload, dict) and isinstance(payload.get("courses"), list):
            self._data = payload
        else:
            self._data = {"courses": []}
            self._save_data()

    def _save_data(self) -> None:
        with self._storage_path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, ensure_ascii=False, indent=2)
