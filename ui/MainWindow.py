from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
import os

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLayout,
    QLayoutItem,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QLineEdit,
    QDialog,
    QSpinBox,
)

from utils.generation import GenerationWorker
from ui.FlashcardWidget import FlashcardWidget
from ui.QuizWidget import QuizWidget
from utils.json_datastore import JSONDataStore


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application NeuroLearn."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NeuroLearn")
        self.resize(1100, 720)

        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)

        # Ajout de la mention d'auteur
        author_label = QLabel("Made by Kaddouri Oussama")
        author_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        author_label.setStyleSheet("color: #888; font-size: 12px; margin: 0 8px 4px 0;")
        self._status_bar.addPermanentWidget(author_label)

        self._status_message = QLabel("Prêt")
        self._status_message.setObjectName("statusMessage")
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedWidth(140)
        self._progress.setFixedHeight(14)
        self._progress.setTextVisible(False)
        self._progress.hide()
        self._status_bar.addWidget(self._status_message)
        self._status_bar.addPermanentWidget(self._progress)

        self._datastore = JSONDataStore()
        self._current_pdf_name: Optional[str] = None
        self._current_summary: Optional[str] = None
        self._current_quiz: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self._current_flashcards: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self._generation_error = False

        self.worker_thread: QThread | None = None
        self.worker: GenerationWorker | None = None
        self._build_ui()
        self._connect_signals()
        self._connect_history_signals()
        self._refresh_history_list()

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        central_widget.setLayout(main_layout)

        self.load_button = QPushButton("Charger un cours")
        self.load_button.setObjectName("loadButton")
        main_layout.addWidget(self.load_button)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        main_layout.addLayout(content_layout, stretch=1)

        self.history_panel = QWidget()
        self.history_panel.setObjectName("historyPanel")
        self.history_panel.setFixedWidth(260)
        history_layout = QVBoxLayout()
        history_layout.setContentsMargins(12, 12, 12, 12)
        history_layout.setSpacing(8)
        self.history_panel.setLayout(history_layout)

        history_title = QLabel("Historique")
        history_title.setObjectName("historyTitle")
        history_layout.addWidget(history_title)

        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.setAlternatingRowColors(False)
        self.history_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        history_layout.addWidget(self.history_list, stretch=1)

        self.delete_button = QPushButton("Supprimer le cours sélectionné")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setEnabled(False)
        history_layout.addWidget(self.delete_button)

        self.history_empty_label = QLabel("Aucun cours enregistré pour le moment.")
        self.history_empty_label.setObjectName("historyEmpty")
        self.history_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        history_layout.addWidget(self.history_empty_label)

        content_layout.addWidget(self.history_panel, stretch=0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("contentTabs")
        content_layout.addWidget(self.tabs, stretch=1)

        self.summary_edit = QTextBrowser()
        self.summary_edit.setReadOnly(True)
        self.summary_edit.setObjectName("summaryArea")
        summary_container = QWidget()
        summary_layout = QVBoxLayout()
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.addWidget(self.summary_edit)
        summary_container.setLayout(summary_layout)
        self.tabs.addTab(summary_container, "Résumé")

        self.quiz_layout = QVBoxLayout()
        self.quiz_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.quiz_layout.setContentsMargins(12, 12, 12, 12)
        self.quiz_layout.setSpacing(16)
        quiz_container = QWidget()
        quiz_container.setLayout(self.quiz_layout)
        self.quiz_scroll = QScrollArea()
        self.quiz_scroll.setWidgetResizable(True)
        self.quiz_scroll.setWidget(quiz_container)
        quiz_tab = QWidget()
        quiz_tab_layout = QVBoxLayout(quiz_tab)
        quiz_tab_layout.setContentsMargins(0, 0, 0, 0)
        quiz_tab_layout.addWidget(self.quiz_scroll)
        self.tabs.addTab(quiz_tab, "Quiz")

        flashcard_tab = QWidget()
        flashcard_tab_layout = QVBoxLayout(flashcard_tab)
        flashcard_tab_layout.setContentsMargins(12, 12, 12, 12)
        flashcard_tab_layout.setSpacing(12)
        self.flashcard_widget = FlashcardWidget()
        flashcard_tab_layout.addWidget(self.flashcard_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.tabs.addTab(flashcard_tab, "Flashcards")

        # Bouton Paramètres dans le coin en bas à droite
        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setToolTip("Paramètres")
        self.settings_button.clicked.connect(self._open_settings_dialog)
        self._status_bar.addPermanentWidget(self.settings_button)

        self._toggle_tabs(False)
        self._apply_tab_icons()

    def _connect_signals(self) -> None:
        self.load_button.clicked.connect(self._on_load_clicked)

    def _connect_history_signals(self) -> None:
        self.history_list.itemSelectionChanged.connect(self._on_history_selection_changed)
        self.delete_button.clicked.connect(self._on_delete_clicked)

    def _on_load_clicked(self) -> None:
        pdf_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un cours",
            str(Path.home()),
            "Fichiers PDF (*.pdf)",
        )
        if pdf_path:
            self._start_generation(pdf_path)

    def _start_generation(self, pdf_path: str) -> None:
        if self.worker_thread is not None and self.worker_thread.isRunning():
            QMessageBox.warning(
                self,
                "Traitement en cours",
                "Veuillez patienter que la génération actuelle se termine.",
            )
            return

        # Récupérer le nombre de questions depuis les paramètres
        default_questions = int(os.environ.get("DEFAULT_QUIZ_QUESTIONS", "10"))
        num_questions = default_questions

        self._set_busy(True, "Génération en cours…")
        self.load_button.setEnabled(False)
        self._toggle_tabs(False)
        self._clear_results()
        self.history_list.clearSelection()

        self._current_pdf_name = Path(pdf_path).name
        self._current_summary = None
        self._current_quiz = None
        self._current_flashcards = None
        self._generation_error = False

        self.worker_thread = QThread(self)
        self.worker = GenerationWorker(pdf_path, num_questions=num_questions)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self._cleanup_thread)

        self.worker.finished.connect(self._on_generation_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished_summary.connect(self.display_summary)
        self.worker.finished_quiz.connect(self.display_quiz)
        self.worker.finished_flashcards.connect(self.display_flashcards)

        self.worker_thread.start()

    def _clear_results(self) -> None:
        self.summary_edit.clear()
        self._clear_layout(self.quiz_layout)
        self.flashcard_widget.clear()

    def _clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)

    def display_summary(self, summary_text: str) -> None:
        stripped = summary_text.strip()
        self.summary_edit.setMarkdown(stripped)
        self.tabs.setTabEnabled(0, True)
        self._current_summary = stripped

    def display_quiz(self, quiz_payload: Union[List[dict], dict]) -> None:
        quiz_items: Iterable[dict]
        if isinstance(quiz_payload, dict):
            quiz_items = quiz_payload.get("questions") or quiz_payload.get("quiz") or []
        else:
            quiz_items = quiz_payload

        quiz_list: List[Dict[str, Any]] = list(quiz_items)
        self._clear_layout(self.quiz_layout)
        count = 0
        for item in quiz_list:
            question = item.get("question") or item.get("prompt") or "Question"
            options = item.get("options") or item.get("choices") or []
            answer = item.get("answer") or item.get("correct_answer") or ""
            self.quiz_layout.addWidget(QuizWidget(question, options, answer))
            count += 1

        if count == 0:
            self.quiz_layout.addWidget(QuizWidget("Aucune question disponible.", [], ""))
        self.tabs.setTabEnabled(1, True)
        self._current_quiz = {"questions": quiz_list}

    def display_flashcards(self, flashcard_payload: Union[List[dict], dict]) -> None:
        flashcard_items: Iterable[dict]
        if isinstance(flashcard_payload, dict):
            flashcard_items = (
                flashcard_payload.get("flashcards")
                or flashcard_payload.get("cards")
                or []
            )
        else:
            flashcard_items = flashcard_payload

        flashcard_list: List[Dict[str, Any]] = list(flashcard_items)
        self.flashcard_widget.set_flashcards(flashcard_list)
        self.tabs.setTabEnabled(2, True)
        self._current_flashcards = {"flashcards": flashcard_list}

    def _on_generation_finished(self) -> None:
        self._set_busy(False, "Génération terminée")
        self.load_button.setEnabled(True)
        self._toggle_tabs(True)
        if not self._generation_error:
            self._persist_generated_course()

    def _on_worker_error(self, message: str) -> None:
        self._set_busy(False, "Erreur pendant la génération")
        self.load_button.setEnabled(True)
        QMessageBox.critical(self, "Erreur", message)
        self._toggle_tabs(False)
        self._generation_error = True

    def _cleanup_thread(self) -> None:
        if self.worker_thread is not None:
            self.worker_thread.deleteLater()
        self.worker_thread = None
        self.worker = None

    def _toggle_tabs(self, enabled: bool) -> None:
        for index in range(self.tabs.count()):
            self.tabs.setTabEnabled(index, enabled)

    def _set_busy(self, busy: bool, message: str | None = None) -> None:
        if busy:
            self._progress.show()
            self._status_message.setText(message or "Traitement en cours…")
        else:
            self._progress.hide()
            self._status_message.setText(message or "Prêt")

    def _apply_tab_icons(self) -> None:
        icon_names = [
            "tab_summary.png",
            "tab_quiz.png",
            "tab_flashcards.png",
        ]
        base = Path(__file__).resolve().parent.parent / "assets"
        for index, filename in enumerate(icon_names):
            icon_path = base / filename
            if icon_path.exists():
                self.tabs.setTabIcon(index, QIcon(str(icon_path)))

    def _persist_generated_course(self) -> None:
        if (
            not self._current_pdf_name
            or self._current_summary is None
            or self._current_quiz is None
            or self._current_flashcards is None
        ):
            return

        try:
            course_id = self._datastore.save_new_course(
                filename=self._current_pdf_name,
                summary=self._current_summary,
                quiz_data=self._current_quiz,
                flashcards_data=self._current_flashcards,
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Enregistrement",
                f"Impossible d'enregistrer le cours généré : {exc}",
            )
            return

        self._refresh_history_list(select_course_id=course_id)

    def _refresh_history_list(self, select_course_id: str | None = None) -> None:
        metadata = self._datastore.get_all_course_metadata()
        has_items = bool(metadata)

        target_id = select_course_id
        if target_id is None:
            current_item = self.history_list.currentItem()
            if current_item is not None:
                target_id = current_item.data(Qt.ItemDataRole.UserRole)

        self.history_list.blockSignals(True)
        self.history_list.clear()
        item_to_select: QListWidgetItem | None = None
        for meta in metadata:
            display_text = f"{meta.get('filename', 'Cours')}\n{meta.get('creation_date', '')}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, meta.get("id"))
            self.history_list.addItem(item)
            if target_id and meta.get("id") == target_id:
                item_to_select = item
        self.history_list.blockSignals(False)

        if item_to_select is not None:
            self.history_list.setCurrentItem(item_to_select)

        self.history_list.setVisible(has_items)
        self.history_empty_label.setVisible(not has_items)

    def _on_history_selection_changed(self) -> None:
        selected_items = self.history_list.selectedItems()
        self.delete_button.setEnabled(bool(selected_items))
        if not selected_items:
            return

        course_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not course_id:
            return

        course = self._datastore.get_course_by_id(str(course_id))
        if not course:
            QMessageBox.warning(
                self,
                "Historique",
                "Impossible de charger ce cours. L'entrée semble corrompue.",
            )
            self._refresh_history_list()
            return

        summary = course.get("summary", "")
        quiz = course.get("quiz", [])
        flashcards = course.get("flashcards", [])

        self.display_summary(summary)
        self.display_quiz(quiz)
        self.display_flashcards(flashcards)
        self._toggle_tabs(True)
        self.tabs.setCurrentIndex(0)
        self._current_pdf_name = course.get("filename", "Cours")

    def _on_delete_clicked(self) -> None:
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Suppression", "Veuillez sélectionner un cours à supprimer.")
            return

        course_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not course_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer ce cours ? Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._datastore.delete_course(str(course_id)):
                self._refresh_history_list()
                self._clear_results()
                self._toggle_tabs(False)
                QMessageBox.information(self, "Suppression", "Le cours a été supprimé avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer le cours.")

    def _open_settings_dialog(self):
        """Ouvre une fenêtre de dialogue pour les paramètres."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Paramètres")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("⚙️ Paramètres de l'application")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2563eb;")
        layout.addWidget(title)
        
        # Section API Key
        api_section = QLabel("Clé API Gemini")
        api_section.setStyleSheet("font-size: 14px; font-weight: 600; margin-top: 12px;")
        layout.addWidget(api_section)
        
        api_key_input = QLineEdit()
        api_key_input.setPlaceholderText("Entrez votre clé API Google Gemini...")
        api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Charger la clé existante si elle existe
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("GOOGLE_API_KEY="):
                    api_key_input.setText(line.split("=", 1)[1])
                    break
        
        layout.addWidget(api_key_input)
        
        # Section Quiz
        quiz_section = QLabel("Paramètres du Quiz")
        quiz_section.setStyleSheet("font-size: 14px; font-weight: 600; margin-top: 12px;")
        layout.addWidget(quiz_section)
        
        quiz_layout = QHBoxLayout()
        quiz_label = QLabel("Nombre de questions par défaut:")
        quiz_layout.addWidget(quiz_label)
        
        self.quiz_questions_spin = QSpinBox()
        self.quiz_questions_spin.setRange(1, 50)
        self.quiz_questions_spin.setValue(10)  # default
        quiz_layout.addWidget(self.quiz_questions_spin)
        layout.addLayout(quiz_layout)
        
        # Charger la valeur existante si elle existe
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("DEFAULT_QUIZ_QUESTIONS="):
                    try:
                        val = int(line.split("=", 1)[1])
                        self.quiz_questions_spin.setValue(val)
                    except ValueError:
                        pass
        
        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(lambda: self._save_settings_from_dialog(api_key_input.text(), self.quiz_questions_spin.value(), dialog))
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _save_settings_from_dialog(self, api_key: str, quiz_questions: int, dialog: QDialog):
        """Enregistre la clé API et les paramètres du quiz depuis la fenêtre de dialogue."""
        api_key = api_key.strip()
        if api_key:
            # Enregistre la clé dans le fichier .env
            env_path = Path(__file__).resolve().parent.parent / ".env"
            lines = []
            if env_path.exists():
                lines = env_path.read_text(encoding="utf-8").splitlines()
                # Supprime les anciennes lignes
                lines = [l for l in lines if not l.startswith("GOOGLE_API_KEY=") and not l.startswith("DEFAULT_QUIZ_QUESTIONS=")]
            lines.append(f"GOOGLE_API_KEY={api_key}")
            lines.append(f"DEFAULT_QUIZ_QUESTIONS={quiz_questions}")
            env_path.write_text("\n".join(lines), encoding="utf-8")
            
            # Mise à jour immédiate de la variable d'environnement pour utilisation sans redémarrage
            import os
            os.environ["GOOGLE_API_KEY"] = api_key
            
            QMessageBox.information(self, "Paramètres enregistrés", "Les paramètres ont été enregistrés et sont prêts à être utilisés.")
            dialog.accept()
        else:
            QMessageBox.warning(self, "Champ vide", "Veuillez entrer une clé API valide.")

    def _save_api_key(self):
        """Ancienne méthode (conservée pour compatibilité mais non utilisée)."""
        pass
