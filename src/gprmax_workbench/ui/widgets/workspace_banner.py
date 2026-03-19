from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ...application.services.localization_service import LocalizationService
from ..layouts.flow_layout import FlowLayout
from .metric_tile import MetricTile


class WorkspaceBanner(QFrame):
    """Persistent workspace context strip shown above the page content."""

    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self.setObjectName("WorkspaceBanner")

        self._eyebrow = QLabel()
        self._eyebrow.setObjectName("BannerEyebrow")
        self._title = QLabel()
        self._title.setObjectName("BannerTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("BannerSubtitle")
        self._subtitle.setWordWrap(True)
        self._meta = QLabel()
        self._meta.setObjectName("BannerMeta")
        self._meta.setWordWrap(True)

        self._project_state_tile = MetricTile()
        self._validation_tile = MetricTile()
        self._runtime_tile = MetricTile()
        self._activity_tile = MetricTile()

        metrics = FlowLayout(horizontal_spacing=12, vertical_spacing=12)
        metrics.addWidget(self._project_state_tile)
        metrics.addWidget(self._validation_tile)
        metrics.addWidget(self._runtime_tile)
        metrics.addWidget(self._activity_tile)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        layout.addWidget(self._eyebrow)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._meta)
        layout.addLayout(metrics)

        self.retranslate_ui()

    def set_empty_state(self) -> None:
        self._title.setText(self._localization.text("workspace.banner.title.empty"))
        self._subtitle.setText(
            self._localization.text("workspace.banner.subtitle.empty")
        )
        self._meta.setText(self._localization.text("workspace.banner.meta.empty"))
        self._project_state_tile.set_content(
            eyebrow=self._localization.text("workspace.metric.project_state"),
            value=self._localization.text("workspace.value.no_project"),
        )
        self._validation_tile.set_content(
            eyebrow=self._localization.text("workspace.metric.validation"),
            value=self._localization.text("workspace.value.awaiting_project"),
        )
        self._runtime_tile.set_content(
            eyebrow=self._localization.text("workspace.metric.runtime"),
            value=self._localization.text("workspace.value.runtime_ready"),
        )
        self._activity_tile.set_content(
            eyebrow=self._localization.text("workspace.metric.activity"),
            value=self._localization.text("workspace.value.no_run"),
        )

    def set_workspace_state(
        self,
        *,
        project_name: str,
        model_title: str,
        project_root: str,
        project_state: str,
        validation_state: str,
        runtime_state: str,
        activity_state: str,
    ) -> None:
        self._title.setText(
            self._localization.text(
                "workspace.banner.title.project",
                project_name=project_name,
            )
        )
        self._subtitle.setText(
            self._localization.text(
                "workspace.banner.subtitle.project",
                model_title=model_title,
            )
        )
        self._meta.setText(
            self._localization.text(
                "workspace.banner.meta.project",
                project_root=project_root,
            )
        )
        self._project_state_tile.set_content(
            eyebrow=self._localization.text("workspace.metric.project_state"),
            value=project_state,
        )
        self._validation_tile.set_content(
            eyebrow=self._localization.text("workspace.metric.validation"),
            value=validation_state,
        )
        self._runtime_tile.set_content(
            eyebrow=self._localization.text("workspace.metric.runtime"),
            value=runtime_state,
        )
        self._activity_tile.set_content(
            eyebrow=self._localization.text("workspace.metric.activity"),
            value=activity_state,
        )

    def retranslate_ui(self) -> None:
        self._eyebrow.setText(self._localization.text("workspace.banner.eyebrow"))
        self.set_empty_state()
