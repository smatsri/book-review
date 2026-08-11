"""Unit tests for opt-in paragraph_budget packing (no EPUB I/O)."""

from __future__ import annotations

import unittest

from book import pack_paragraphs_by_word_budget


class PackParagraphsByWordBudgetTests(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(pack_paragraphs_by_word_budget([], 100), [])

    def test_single_oversized_paragraph_stays_alone(self) -> None:
        para = " ".join(["word"] * 50)
        parts = pack_paragraphs_by_word_budget([para], target_words=10)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], [para])

    def test_greedy_cuts_at_budget(self) -> None:
        # 10 paras × 10 words = 100; budget 35 → parts of ~30 then remainder.
        paras = [" ".join(["w"] * 10) for _ in range(10)]
        parts = pack_paragraphs_by_word_budget(paras, target_words=35)
        sizes = [sum(len(p.split()) for p in part) for part in parts]
        self.assertTrue(all(s <= 35 or len(part) == 1 for part, s in zip(parts, sizes)))
        self.assertEqual(sum(sizes), 100)
        self.assertGreaterEqual(len(parts), 3)

    def test_rejects_bad_budget(self) -> None:
        with self.assertRaises(ValueError):
            pack_paragraphs_by_word_budget(["a"], 0)


if __name__ == "__main__":
    unittest.main()
