from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...application.services.localization_service import LocalizationService


class NewProjectDialog(QDialog):
    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self.setWindowTitle(self._localization.text("dialog.new_project.title"))
        self.setModal(True)
        self.resize(600, 340)

        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._refresh_project_preview)
        self._directory_edit = QLineEdit(str(Path.home() / "GPRMax Projects"))
        self._directory_edit.textChanged.connect(self._refresh_project_preview)

        self._browse_button = QPushButton()
        self._browse_button.clicked.connect(self._browse_directory)

        directory_row = QHBoxLayout()
        directory_row.addWidget(self._directory_edit, 1)
        directory_row.addWidget(self._browse_button)

        form = QFormLayout()
        self._project_name_label = QLabel()
        self._project_directory_label = QLabel()
        form.addRow(self._project_name_label, self._name_edit)
        form.addRow(self._project_directory_label, self._wrap_layout(directory_row))

        self._intro = QLabel()
        self._intro.setWordWrap(True)
        self._path_preview = QLabel()
        self._path_preview.setObjectName("SectionBody")
        self._path_preview.setWordWrap(True)
        self._validation_hint = QLabel()
        self._validation_hint.setObjectName("SectionBody")
        self._validation_hint.setWordWrap(True)
        self._folder_warning = QLabel()
        self._folder_warning.setObjectName("StatusBadge")
        self._folder_warning.setProperty("statusTone", "neutral")
        self._folder_warning.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        self._buttons = buttons

        layout = QVBoxLayout(self)
        layout.addWidget(self._intro)
        layout.addLayout(form)
        layout.addWidget(self._path_preview)
        layout.addWidget(self._validation_hint)
        layout.addWidget(self._folder_warning)
        layout.addStretch(1)
        layout.addWidget(buttons)

        self.retranslate_ui()
        self._refresh_project_preview()

    def project_name(self) -> str:
        return self._name_edit.text().strip()

    def project_root(self) -> Path:
        return Path(self._directory_edit.text().strip()).expanduser()

    def _browse_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            self._localization.text("dialog.new_project.choose_directory"),
            str(self.project_root()),
        )
        if path:
            self._directory_edit.setText(path)

    def _accept_if_valid(self) -> None:
        name = self.project_name()
        directory = self._directory_edit.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                self._localization.text("message.new_project.title"),
                self._localization.text("dialog.new_project.name_required"),
            )
            return

        if not directory:
            QMessageBox.warning(
                self,
                self._localization.text("message.new_project.title"),
                self._localization.text("dialog.new_project.directory_required"),
            )
            return

        self.accept()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self._localization.text("dialog.new_project.title"))
        self._browse_button.setText(self._localization.text("common.browse"))
        self._name_edit.setPlaceholderText(
            self._localization.text("dialog.new_project.name_placeholder")
        )
        self._directory_edit.setPlaceholderText(
            self._localization.text("dialog.new_project.directory_placeholder")
        )
        self._project_name_label.setText(
            self._localization.text("dialog.new_project.project_name")
        )
        self._project_directory_label.setText(
            self._localization.text("dialog.new_project.project_directory")
        )
        self._intro.setText(self._localization.text("dialog.new_project.intro"))
        self._refresh_project_preview()

    def _refresh_project_preview(self) -> None:
        directory = self._directory_edit.text().strip()
        name = self.project_name()

        self._set_field_state(self._name_edit, "error" if not name else "")
        self._set_field_state(self._directory_edit, "error" if not directory else "")

        if directory:
            target = self.project_root()
            self._path_preview.setText(
                self._localization.text(
                    "dialog.new_project.path_preview",
                    path=target,
                )
            )
        else:
            self._path_preview.setText(
                self._localization.text("dialog.new_project.path_preview_empty")
            )

        if not name:
            self._validation_hint.setText(
                self._localization.text("dialog.new_project.name_required")
            )
        elif not directory:
            self._validation_hint.setText(
                self._localization.text("dialog.new_project.directory_required")
            )
        else:
            self._validation_hint.setText(
                self._localization.text("dialog.new_project.ready_hint")
            )

        self._refresh_folder_warning()

    def _refresh_folder_warning(self) -> None:
        directory = self._directory_edit.text().strip()
        if not directory:
            self._set_warning_text(
                self._localization.text("dialog.new_project.warning_choose_folder"),
                "neutral",
            )
            return

        target = self.project_root()
        if not target.exists():
            self._set_warning_text(
                self._localization.text("dialog.new_project.folder_will_be_created"),
                "info",
            )
            return

        try:
            has_entries = any(target.iterdir())
        except OSError:
            self._set_warning_text(
                self._localization.text("dialog.new_project.folder_unavailable"),
                "warning",
            )
            return

        if has_entries:
            self._set_warning_text(
                self._localization.text("dialog.new_project.folder_not_empty"),
                "warning",
            )
            return

        self._set_warning_text(
            self._localization.text("dialog.new_project.folder_empty"),
            "neutral",
        )

    def _set_warning_text(self, text: str, tone: str) -> None:
        self._folder_warning.setText(text)
        self._folder_warning.setProperty("statusTone", tone)
        style = self._folder_warning.style()
        style.unpolish(self._folder_warning)
        style.polish(self._folder_warning)

    def _set_field_state(self, widget: QLineEdit, state: str) -> None:
        widget.setProperty("validationState", state)
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)

    def _wrap_layout(self, layout: QHBoxLayout) -> QWidget:
        container = QWidget()
        container.setLayout(layout)
        return container
