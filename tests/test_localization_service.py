from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import (
    LocalizationService,
)


class LocalizationServiceTests(unittest.TestCase):
    def test_switches_between_languages(self) -> None:
        service = LocalizationService("ru")

        self.assertEqual(service.text("menu.file"), "Файл")

        service.set_language("en")

        self.assertEqual(service.text("menu.file"), "File")

    def test_translates_known_runtime_message_to_russian(self) -> None:
        service = LocalizationService("ru")

        translated = service.translate_message(
            "Python executable not found: C:/Python/python.exe"
        )

        self.assertEqual(
            translated,
            "Python executable не найден: C:/Python/python.exe",
        )

    def test_keeps_runtime_message_in_english_when_selected(self) -> None:
        service = LocalizationService("en")
        original = "No output files are available for this run."

        self.assertEqual(service.translate_message(original), original)


if __name__ == "__main__":
    unittest.main()
