"""Unit tests for alias cluster refine + display-name picking."""

from __future__ import annotations

import unittest

from rollup import (
    apply_alias_clusters,
    cluster_has_identity_conflict,
    refine_character_alias_clusters,
)


class AliasRefineTests(unittest.TestCase):
    def test_baley_minnim_cluster_conflicts(self) -> None:
        cluster = [
            "Albert Minnim",
            "Baley",
            "Elijah Baley",
            "Jessie Baley",
        ]
        self.assertTrue(cluster_has_identity_conflict(cluster))

    def test_partition_keeps_elijah_with_short_baley(self) -> None:
        cluster = [
            "Albert Minnim",
            "Baley",
            "Elijah Baley",
            "Jessie Baley",
        ]
        counts = {
            "Albert Minnim": 2,
            "Baley": 3,
            "Elijah Baley": 15,
            "Jessie Baley": 1,
        }
        parts, warnings = refine_character_alias_clusters(
            [cluster], chapter_counts=counts
        )
        self.assertTrue(warnings)
        flat = {frozenset(p) for p in parts}
        self.assertIn(frozenset({"Elijah Baley", "Baley"}), flat)
        self.assertIn(frozenset({"Albert Minnim"}), flat)
        self.assertIn(frozenset({"Jessie Baley"}), flat)

    def test_safe_leebig_aliases_untouched(self) -> None:
        cluster = ["Dr. Leebig (Jothan)", "Jothan Leebig", "Leebig"]
        self.assertFalse(cluster_has_identity_conflict(cluster))
        parts, warnings = refine_character_alias_clusters(
            [cluster],
            chapter_counts={
                "Dr. Leebig (Jothan)": 1,
                "Jothan Leebig": 2,
                "Leebig": 3,
            },
        )
        self.assertEqual(warnings, [])
        self.assertEqual(len(parts), 1)
        self.assertEqual(set(parts[0]), set(cluster))

    def test_husband_wife_delmarre_split(self) -> None:
        cluster = [
            "Dr. Rikaine Delmarre",
            "Mrs. Delmarre (Gladia)",
            "Gladia Delmarre",
        ]
        self.assertTrue(cluster_has_identity_conflict(cluster))

    def test_display_prefers_chapter_count(self) -> None:
        rollup = {
            "chapters_included": [1, 2],
            "characters": [
                {
                    "name": "Albert Minnim",
                    "notes": ["Undersecretary"],
                    "chapters": [1],
                },
                {
                    "name": "Elijah Baley",
                    "notes": ["Detective"],
                    "chapters": [1, 2, 3, 4, 5],
                },
                {
                    "name": "Baley",
                    "notes": ["Earthman"],
                    "chapters": [2],
                },
            ],
            "themes": [],
        }
        # Even if LLM wrongly merges Minnim+Baleys, refine should split;
        # Elijah+Baley keep Elijah as display by chapter count.
        merged = apply_alias_clusters(
            rollup,
            {
                "characters": [
                    ["Albert Minnim", "Elijah Baley", "Baley"],
                ],
                "themes": [],
            },
        )
        by_name = {c["name"]: c for c in merged["characters"]}
        self.assertIn("Elijah Baley", by_name)
        self.assertIn("Albert Minnim", by_name)
        self.assertEqual(
            set(by_name["Elijah Baley"]["aliases"]),
            {"Elijah Baley", "Baley"},
        )
        self.assertTrue(merged.get("alias_warnings"))

    def test_serving_robot_and_code_split_from_daneel(self) -> None:
        cluster = [
            "Daneel",
            "Daneel Olivaw",
            "R. Daneel Olivaw (imposter)",
            "R. Daneel Olivaw (mentioned)",
            "RX-2475",
            "Serving Robot",
        ]
        counts = {name: 1 for name in cluster}
        counts["Daneel Olivaw"] = 10
        parts, warnings = refine_character_alias_clusters(
            [cluster], chapter_counts=counts
        )
        self.assertTrue(warnings)
        flat = {frozenset(p) for p in parts}
        daneel_group = next(p for p in flat if "Daneel Olivaw" in p)
        self.assertIn("Daneel", daneel_group)
        self.assertNotIn("Serving Robot", daneel_group)
        self.assertNotIn("RX-2475", daneel_group)

    def test_ambiguous_dr_delmarre_stays_singleton(self) -> None:
        cluster = [
            "Dr. Delmarre",
            "Dr. Rikaine Delmarre",
            "Gladia Delmarre",
            "Mrs. Delmarre (Gladia)",
        ]
        counts = {
            "Dr. Delmarre": 4,
            "Dr. Rikaine Delmarre": 2,
            "Gladia Delmarre": 8,
            "Mrs. Delmarre (Gladia)": 10,
        }
        parts, _ = refine_character_alias_clusters(
            [cluster], chapter_counts=counts
        )
        flat = {frozenset(p) for p in parts}
        self.assertIn(frozenset({"Dr. Delmarre"}), flat)
        gladia = next(p for p in flat if "Gladia Delmarre" in p)
        self.assertIn("Mrs. Delmarre (Gladia)", gladia)
        self.assertNotIn("Dr. Rikaine Delmarre", gladia)


if __name__ == "__main__":
    unittest.main()
