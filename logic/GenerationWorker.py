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

    def __init__(self, pdf_path: str, model_name: Optional[str] = None) -> None:
        super().__init__()
        self.pdf_path = pdf_path
        env_model = os.environ.get("GEMINI_MODEL")
        self.model_name = model_name or env_model or "gemini-2.5-flash"

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

            quiz = self._generate_quiz(model, document_text)
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
            if not self.model_name.startswith("models/"):
                candidates.append(f"models/{self.model_name}-latest")

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                return genai.GenerativeModel(candidate)
            except Exception as exc:  # pragma: no cover - dépend de l'API distante
                last_error = exc
        raise RuntimeError(
            "Impossible d'initialiser le modèle Gemini. Vérifiez le nom dans GEMINI_MODEL "
            f"(actuel: {self.model_name}) et consultez https://ai.google.dev/gemini-api/docs/models."
        ) from last_error

    def _generate_summary(self, model: genai.GenerativeModel, document_text: str) -> str:
        prompt = (
            "Tu es un assistant pédagogique francophone.\n"
            "Fournis un résumé structuré et lisible du document suivant, en 4 à 6 sections "
            "maximales, avec des puces lorsque pertinent."
        )
        response = model.generate_content(
            [prompt, f"=== DOCUMENT ===\n{document_text}"],
            generation_config={"temperature": 0.5},
        )
        summary_text = self._response_to_text(response).strip()
        if not summary_text:
            raise ValueError("Le modèle n'a renvoyé aucun résumé.")
        return summary_text

    def _generate_quiz(self, model: genai.GenerativeModel, document_text: str) -> List[dict]:
        prompt = (
            "Génère un quiz en JSON basé sur le document ci-dessous.\n"
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
        if getattr(response, "text", None):
            return response.text

        texts: List[str] = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", "")
                if text:
                    texts.append(text)
        return "\n".join(texts)

    @staticmethod
    def _parse_json_list(payload: str, field_name: str) -> List[dict]:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON invalide renvoyé par Gemini : {exc}\nPayload reçu : {payload}") from exc

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            field_value = data.get(field_name)
            if isinstance(field_value, list):
                return field_value

        raise ValueError(f"Le JSON renvoyé ne contient pas le champ '{field_name}'.")
