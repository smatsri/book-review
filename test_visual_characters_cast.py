"""Unit tests for visual-characters illustration cast selection."""

from __future__ import annotations

import unittest

from agents.visual_characters import select_illustration_cast


def _row(name: str, chapters: list[int]) -> dict:
    return {"name": name, "chapters": chapters, "notes": [], "aliases": [name]}


class IllustrationCastTests(unittest.TestCase):
    def test_naked_sun_style_keeps_baley_drops_robots(self) -> None:
        rows = [
            _row("Elijah Baley", list(range(1, 16))),
            _row("Gladia Delmarre", list(range(1, 14))),
            _row("Daneel Olivaw", list(range(1, 11))),
            _row("Jothan Leebig", [1, 2, 3, 4, 5, 6]),
            _row("Rikaine Delmarre", [1, 2, 3, 4, 5, 6]),
            _row("Hannis Gruer", [1, 2, 3, 4, 5]),
            _row("Dr. Quemot", [1, 2, 3, 4]),
            _row("Klorissa Cantoro", [1, 2, 3]),
            _row("Dr. Altim Thool", [1, 2, 3]),
            _row("Albert Minnim", [1, 2]),
            _row("ACC-1129", [4]),
            _row("Serving Robot", [5]),
            _row("Jessie Baley", [1]),
        ]
        selected = select_illustration_cast(rows)
        names = [r["name"] for r in selected]
        self.assertEqual(names[0], "Elijah Baley")
        self.assertIn("Gladia Delmarre", names)
        self.assertIn("Daneel Olivaw", names)
        self.assertNotIn("ACC-1129", names)
        self.assertNotIn("Serving Robot", names)
        self.assertNotIn("Jessie Baley", names)
        self.assertNotIn("Albert Minnim", names)
        self.assertLessEqual(len(selected), 12)

    def test_always_keeps_number_one_even_if_below_threshold(self) -> None:
        rows = [
            _row("Only Lead", [1, 2]),
            _row("Walk-on A", [1]),
            _row("Walk-on B", [1]),
        ]
        selected = select_illustration_cast(
            rows, min_chapters=3, min_cast=3, max_cast=12
        )
        names = [r["name"] for r in selected]
        self.assertEqual(names[0], "Only Lead")
        self.assertEqual(len(selected), 3)

    def test_caps_at_max(self) -> None:
        rows = [_row(f"C{i}", list(range(1, 10))) for i in range(20)]
        selected = select_illustration_cast(rows, max_cast=12)
        self.assertEqual(len(selected), 12)


if __name__ == "__main__":
    unittest.main()
