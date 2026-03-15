from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtWidgets import QDoubleSpinBox, QLabel


def build_float_spinbox(
    *,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
    decimals: int = 6,
    step: float = 0.001,
) -> QDoubleSpinBox:
    spinbox = QDoubleSpinBox()
    spinbox.setRange(minimum, maximum)
    spinbox.setDecimals(decimals)
    spinbox.setSingleStep(step)
    return spinbox


def parse_tags(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def tags_to_text(tags: Iterable[str]) -> str:
    return ", ".join(item for item in tags if item)


def parse_csv_values(raw: str) -> list[str]:
    normalized = raw.replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def build_status_label(empty_text: str) -> QLabel:
    label = QLabel(empty_text)
    label.setWordWrap(True)
    return label


def join_messages(messages: list[str], empty_text: str) -> str:
    if not messages:
        return empty_text
    return "\n".join(messages)
