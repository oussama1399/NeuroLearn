from __future__ import annotations

from typing import Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class QuizWidget(QWidget):
    """Carte interactive pour une question de quiz multi-choix."""

    def __init__(
        self,
        question: str,
        options: Iterable[str],
        answer: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("quizCard")

        self._option_displays = [self._sanitize_content(str(opt)) or "*Option vide*" for opt in options]
        self._option_plain = [self._to_plain_text(value) for value in self._option_displays]
        self._answer_display = self._sanitize_content(answer or "")
        self._answer_plain = self._to_plain_text(self._answer_display)
        self._checked = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(8)

        self.card_frame = QFrame()
        self.card_frame.setObjectName("quizCardFrame")
        self.card_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.card_frame.setProperty("status", "")

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        self.question_label = QLabel(self._sanitize_content(question) or "Question")
        self.question_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.question_label.setObjectName("quizQuestion")
        self.question_label.setWordWrap(True)
        card_layout.addWidget(self.question_label)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.option_buttons = []
        self.option_rows = []
        self.option_labels = []

        if self._option_displays:
            for idx, option_text in enumerate(self._option_displays):
                option_row = QFrame()
                option_row.setObjectName("quizOptionRow")
                option_row.setProperty("result", "")

                row_layout = QHBoxLayout(option_row)
                row_layout.setContentsMargins(14, 10, 14, 10)
                row_layout.setSpacing(12)

                radio = QRadioButton()
                radio.setProperty("role", "option")
                radio.setProperty("result", "")
                radio.setAutoExclusive(True)
                radio.setCursor(Qt.CursorShape.PointingHandCursor)
                self.button_group.addButton(radio, idx)

                option_label = QLabel(option_text)
                option_label.setObjectName("quizOptionLabel")
                option_label.setTextFormat(Qt.TextFormat.MarkdownText)
                option_label.setWordWrap(True)
                option_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                option_label.setProperty("result", "")

                row_layout.addWidget(radio)
                row_layout.addWidget(option_label, 1)

                self.option_buttons.append(radio)
                self.option_rows.append(option_row)
                self.option_labels.append(option_label)
                card_layout.addWidget(option_row)
        else:
            placeholder = QLabel("Aucune option fournie.")
            placeholder.setObjectName("quizPlaceholder")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignLeft)
            card_layout.addWidget(placeholder)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("quizFeedback")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.hide()
        card_layout.addWidget(self.feedback_label)

        layout.addWidget(self.card_frame)

        self.validate_button = QPushButton("Valider")
        self.validate_button.setProperty("variant", "ghost")
        self.validate_button.clicked.connect(self._validate)
        layout.addWidget(self.validate_button, alignment=Qt.AlignmentFlag.AlignRight)

        self._refresh(self.card_frame)

    def _validate(self) -> None:
        if self._checked:
            return

        selected_id = self.button_group.checkedId()
        if selected_id == -1:
            self.feedback_label.setText("Sélectionnez une option pour valider.")
            self.feedback_label.setProperty("state", "warning")
            self.feedback_label.show()
            self._refresh(self.feedback_label)
            return

        correct_indices = self._find_correct_indices()
        selected_index = selected_id
        is_correct = selected_index in correct_indices

        self._checked = True
        self.validate_button.setEnabled(False)

        for idx, button in enumerate(self.option_buttons):
            button.setEnabled(False)
            result = ""
            if idx in correct_indices:
                result = "correct"
            elif idx == selected_index:
                result = "incorrect"
            button.setProperty("result", result)
            row = self.option_rows[idx]
            label = self.option_labels[idx]
            row.setProperty("result", result)
            label.setProperty("result", result)
            self._refresh(button)
            self._refresh(row)
            self._refresh(label)

        status = "correct" if is_correct else "incorrect"
        self.card_frame.setProperty("status", status)
        self._refresh(self.card_frame)

        if is_correct:
            self.feedback_label.setText("✔️ Bonne réponse !")
            self.feedback_label.setProperty("state", "success")
        else:
            answer_text = ", ".join(self._option_displays[i] for i in correct_indices) if correct_indices else self._answer_display
            self.feedback_label.setText(f"❌ Mauvaise réponse. Solution : {answer_text}")
            self.feedback_label.setProperty("state", "error")
        self.feedback_label.show()
        self._refresh(self.feedback_label)

    def _find_correct_indices(self) -> list[int]:
        if not self._option_plain:
            return []
        normalized_answer = self._normalize(self._answer_plain)
        return [i for i, option in enumerate(self._option_plain) if self._normalize(option) == normalized_answer]

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.strip().lower().split())

    @staticmethod
    def _sanitize_content(value: str) -> str:
        text = (value or "").strip()
        if not text:
            return ""

        lowered = text.lower()
        if "<html" in lowered or "<body" in lowered or "<!doctype" in lowered:
            doc = QTextDocument()
            try:
                doc.setHtml(text)
                markdown = doc.toMarkdown().strip()
                if markdown:
                    return markdown
                return doc.toPlainText().strip()
            except Exception:
                fallback = QTextDocument()
                fallback.setPlainText(text)
                return fallback.toPlainText().strip()
        return text

    @staticmethod
    def _to_plain_text(value: str) -> str:
        doc = QTextDocument()
        doc.setMarkdown(value)
        plain = doc.toPlainText().strip()
        return plain or value.strip()

    @staticmethod
    def _refresh(widget: QWidget) -> None:
        style = widget.style()
        if style is not None:
            style.unpolish(widget)
            style.polish(widget)
        widget.update()
