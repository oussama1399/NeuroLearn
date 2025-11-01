from pathlib import Path

from pypdf import PdfReader


def get_text_from_pdf(pdf_path: str) -> str:
    """Lit un PDF et renvoie son contenu textuel."""

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Le fichier sélectionné n'est pas un PDF.")

    text_parts: list[str] = []
    with path.open("rb") as pdf_file:
        reader = PdfReader(pdf_file)
        if not reader.pages:
            raise ValueError("Le PDF ne contient aucune page.")

        for index, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:  # pragma: no cover - dépend de pypdf
                raise ValueError(f"Impossible de lire la page {index}: {exc}") from exc
            cleaned = page_text.strip()
            if cleaned:
                text_parts.append(cleaned)

    if not text_parts:
        raise ValueError("Aucun texte n'a pu être extrait du PDF.")

    return "\n\n".join(text_parts)


__all__ = ["get_text_from_pdf"]