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


class NewProjectDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(520, 220)

        self._name_edit = QLineEdit()
        self._directory_edit = QLineEdit(str(Path.home() / "GPRMax Projects"))

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_directory)

        directory_row = QHBoxLayout()
        directory_row.addWidget(self._directory_edit, 1)
        directory_row.addWidget(browse_button)

        form = QFormLayout()
        form.addRow("Project name", self._name_edit)
        form.addRow("Project directory", self._wrap_layout(directory_row))

        intro = QLabel(
            "Create a project root folder with a project manifest and the standard "
            "generated/runs/results/assets directories."
        )
        intro.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(form)
        layout.addStretch(1)
        layout.addWidget(buttons)

    def project_name(self) -> str:
        return self._name_edit.text().strip()

    def project_root(self) -> Path:
        return Path(self._directory_edit.text().strip()).expanduser()

    def _browse_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Choose Project Directory",
            str(self.project_root()),
        )
        if path:
            self._directory_edit.setText(path)

    def _accept_if_valid(self) -> None:
        name = self.project_name()
        directory = self._directory_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "New Project", "Project name is required.")
            return

        if not directory:
            QMessageBox.warning(self, "New Project", "Project directory is required.")
            return

        self.accept()

    def _wrap_layout(self, layout: QHBoxLayout) -> QWidget:
        container = QWidget()
        container.setLayout(layout)
        return container
