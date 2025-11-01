from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FlashcardWidget(QWidget):
    """Widget interactif pour parcourir un paquet de flashcards."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("flashcardViewer")

        self._cards: list[dict] = []
        self._index = 0
        self._show_front = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card_frame = QFrame()
        self.card_frame.setObjectName("flashcardFrame")
        self.card_frame.setMinimumSize(640, 400)
        self.card_frame.setMaximumWidth(900)
        self.card_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.card_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.card_frame.installEventFilter(self)

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card_label = QLabel("Aucune carte disponible.")
        self.card_label.setObjectName("flashcardLabel")
        self.card_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_label.setWordWrap(True)
        self.card_label.setTextFormat(Qt.TextFormat.MarkdownText)

        self.card_hint = QLabel("Cliquez pour retourner la carte")
        self.card_hint.setObjectName("flashcardHint")
        self.card_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(self.card_label)
        card_layout.addWidget(self.card_hint)

        layout.addWidget(self.card_frame)

        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(12)

        self.prev_button = QPushButton("◀ Précédent")
        self.prev_button.setProperty("variant", "ghost")
        self.prev_button.clicked.connect(self._go_prev)

        self.next_button = QPushButton("Suivant ▶")
        self.next_button.setProperty("variant", "ghost")
        self.next_button.clicked.connect(self._go_next)

        nav_layout.addStretch(1)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch(1)

        layout.addLayout(nav_layout)

        self.counter_label = QLabel("")
        self.counter_label.setObjectName("flashcardCounter")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.counter_label)

        self._update_card()

    def set_flashcards(self, cards: list[dict]) -> None:
        if cards:
            self._cards = [card if isinstance(card, dict) else {"front": str(card)} for card in cards]
        else:
            self._cards = []
        self._index = 0
        self._show_front = True
        self._update_card()

    def clear(self) -> None:
        self.set_flashcards([])

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # type: ignore[override]
        if watched is self.card_frame and event.type() == QEvent.Type.MouseButtonRelease:
            self._toggle_side()
            return True
        return super().eventFilter(watched, event)

    def _toggle_side(self) -> None:
        if not self._cards:
            return
        self._show_front = not self._show_front
        self._update_card()

    def _go_prev(self) -> None:
        if self._index > 0:
            self._index -= 1
            self._show_front = True
            self._update_card()

    def _go_next(self) -> None:
        if self._index < len(self._cards) - 1:
            self._index += 1
            self._show_front = True
            self._update_card()

    def _update_card(self) -> None:
        if not self._cards:
            self.card_label.setText("Aucune carte disponible.")
            self.card_hint.setVisible(False)
            self.card_frame.setProperty("state", "empty")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.counter_label.setText("")
            self._refresh(self.card_frame)
            return

        card = self._cards[self._index]
        front = (card.get("front") or card.get("question") or "Carte").strip()
        back = (card.get("back") or card.get("answer") or "").strip() or "*Pas de contenu*"

        if self._show_front:
            self.card_label.setText(front)
            self.card_hint.setText("Cliquez pour afficher la réponse")
            self.card_frame.setProperty("state", "front")
        else:
            self.card_label.setText(back)
            self.card_hint.setText("Cliquez pour revenir au recto")
            self.card_frame.setProperty("state", "back")

        self.card_hint.setVisible(True)
        self.prev_button.setEnabled(self._index > 0)
        self.next_button.setEnabled(self._index < len(self._cards) - 1)
        self.counter_label.setText(f"{self._index + 1} / {len(self._cards)}")
        self._refresh(self.card_frame)

    @staticmethod
    def _refresh(widget: QWidget) -> None:
        style = widget.style()
        if style is not None:
            style.unpolish(widget)
            style.polish(widget)
        widget.update()
