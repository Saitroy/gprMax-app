from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.infrastructure.gprmax.command_registry import GprMaxCommandRegistry


class CommandRegistryTests(unittest.TestCase):
    def test_registry_exposes_multiple_categories_and_templates(self) -> None:
        registry = GprMaxCommandRegistry()

        categories = registry.categories()
        templates = registry.templates()

        self.assertIn("general", categories)
        self.assertIn("imports", categories)
        self.assertGreaterEqual(len(templates), 20)
        self.assertIsNotNone(registry.get("geometry_read"))


if __name__ == "__main__":
    unittest.main()
