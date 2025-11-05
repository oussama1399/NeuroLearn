from __future__ import annotations

import json
import os
from typing import Any, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

import google.generativeai as genai

from utils.rag_utils import get_text_from_pdf


class GenerationWorker(QObject):
    """Worker qui exécute les appels longs (lecture PDF + API Gemini)."""

    finished = pyqtSignal()
    error = pyqtSignal(str)
    finished_summary = pyqtSignal(str)
    finished_quiz = pyqtSignal(list)
    finished_flashcards = pyqtSignal(list)

    def __init__(self, pdf_path: str, model_name: Optional[str] = None, num_questions: int = 10) -> None:
        super().__init__()
        self.pdf_path = pdf_path
        env_model = os.environ.get("GEMINI_MODEL")
        self.model_name = model_name or env_model or "gemini-2.5-flash"
        self.num_questions = num_questions

    def run(self) -> None:
        try:
            document_text = get_text_from_pdf(self.pdf_path)
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise RuntimeError("La variable d'environnement GOOGLE_API_KEY est introuvable.")

            genai.configure(api_key=api_key)
            model = self._init_model()

            summary = self._generate_summary(model, document_text)
            self.finished_summary.emit(summary)

            quiz = self._generate_quiz(model, document_text, self.num_questions)
            self.finished_quiz.emit(quiz)

            flashcards = self._generate_flashcards(model, document_text)
            self.finished_flashcards.emit(flashcards)

        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

    def _init_model(self) -> genai.GenerativeModel:
        """Initialise le modèle Gemini en gérant les éventuels changements de nom."""

        candidates = [self.model_name]
        if not self.model_name.startswith("models/"):
            candidates.append(f"models/{self.model_name}")
        if not self.model_name.endswith("-latest"):
            candidates.append(f"{self.model_name}-latest")

        last_exc: Exception | None = None
        for candidate in candidates:
            try:
                return genai.GenerativeModel(candidate)
            except Exception as exc:
                last_exc = exc
                continue

        raise RuntimeError(
            f"Impossible d'initialiser le modèle {self.model_name}. "
            f"Dernière erreur: {last_exc}"
        )

    def _generate_summary(self, model: genai.GenerativeModel, document_text: str) -> str:
        prompt = (
            "Résume en Markdown ce document de manière claire et structurée :\n\n"
            f"{document_text}"
        )
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.3},
        )
        return self._response_to_text(response)

    def _generate_quiz(self, model: genai.GenerativeModel, document_text: str, num_questions: int = 10) -> List[dict]:
        prompt = (
            f"Génère un quiz en JSON basé sur le document ci-dessous. Le quiz doit contenir exactement {num_questions} questions.\n"
            "Tu dois renvoyer exactement le format suivant : {\"questions\": [{"
            "\"question\": \"...\", \"options\": [\"...\"], \"answer\": \"...\"}]}"
        )
        response = model.generate_content(
            [prompt, f"=== DOCUMENT ===\n{document_text}"],
            generation_config={
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        )
        return self._parse_json_list(self._response_to_text(response), "questions")

    def _generate_flashcards(self, model: genai.GenerativeModel, document_text: str) -> List[dict]:
        prompt = (
            "Crée une liste de flashcards JSON basée sur le document ci-dessous.\n"
            "Format exigé : {\"flashcards\": [{\"front\": \"...\", \"back\": \"...\"}]}"
        )
        response = model.generate_content(
            [prompt, f"=== DOCUMENT ===\n{document_text}"],
            generation_config={
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        )
        return self._parse_json_list(self._response_to_text(response), "flashcards")

    @staticmethod
    def _response_to_text(response: Any) -> str:
        """Extrait le texte d'une réponse Gemini."""

        if hasattr(response, "text"):
            return response.text or ""
        if hasattr(response, "parts"):
            parts = getattr(response, "parts", [])
            return "".join(getattr(p, "text", "") for p in parts)
        return str(response)

    @staticmethod
    def _parse_json_list(raw: str, key: str) -> List[dict]:
        """Parse un JSON de la forme {key: [...]} et renvoie la liste."""

        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Réponse JSON invalide : {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError("Le JSON doit être un objet avec une clé de liste.")
        if key not in data:
            raise ValueError(f"Clé '{key}' introuvable dans la réponse JSON.")
        result = data[key]
        if not isinstance(result, list):
            raise ValueError(f"La valeur de '{key}' doit être une liste.")
        return result
