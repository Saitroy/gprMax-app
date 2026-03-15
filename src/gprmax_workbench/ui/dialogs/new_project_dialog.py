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
        self.resize(520, 220)

        self._name_edit = QLineEdit()
        self._directory_edit = QLineEdit(str(Path.home() / "GPRMax Projects"))

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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        self._buttons = buttons

        layout = QVBoxLayout(self)
        layout.addWidget(self._intro)
        layout.addLayout(form)
        layout.addStretch(1)
        layout.addWidget(buttons)

        self.retranslate_ui()

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
        self._project_name_label.setText(
            self._localization.text("dialog.new_project.project_name")
        )
        self._project_directory_label.setText(
            self._localization.text("dialog.new_project.project_directory")
        )
        self._intro.setText(self._localization.text("dialog.new_project.intro"))

    def _wrap_layout(self, layout: QHBoxLayout) -> QWidget:
        container = QWidget()
        container.setLayout(layout)
        return container
