"""Book-level structured rollup from per-chapter Reader analyses (no LLM)."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any


_TITLE_PREFIXES = frozenset(
    {
        "dr",
        "mr",
        "mrs",
        "ms",
        "miss",
        "sir",
        "lady",
        "lord",
        "r",
        "prof",
        "professor",
        "captain",
        "capt",
    }
)
_NAME_STOPWORDS = frozenset({"of", "the", "and", "a", "an", "de", "van", "von", "da"})
_META_PAREN_TOKENS = frozenset(
    {
        "mentioned",
        "impostor",
        "imposter",
        "alias",
        "aka",
        "robot",
        "serving",
    }
)


def normalize_character_key(name: str) -> str:
    """Casefold, collapse space, strip a leading 'the '."""
    key = " ".join(name.strip().split()).casefold()
    if key.startswith("the "):
        key = key[4:]
    return key


def normalize_theme_key(theme: str) -> str:
    return " ".join(theme.strip().split()).casefold()


def _pick_display_name(name_counts: Counter[str]) -> str:
    """Most frequent raw name; ties → longer, then alphabetical."""
    return max(
        name_counts.keys(),
        key=lambda n: (name_counts[n], len(n), n.casefold()),
    )


def _pick_display_theme(theme_counts: Counter[str]) -> str:
    return max(
        theme_counts.keys(),
        key=lambda t: (theme_counts[t], len(t), t.casefold()),
    )


def _word_tokens(text: str) -> list[str]:
    parts = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    out: list[str] = []
    for part in parts:
        token = part.casefold().strip("'")
        if not token or token in _TITLE_PREFIXES or token in _NAME_STOPWORDS:
            continue
        out.append(token)
    return out


def _main_and_paren_tokens(label: str) -> tuple[list[str], list[str]]:
    paren_bits = re.findall(r"\(([^)]*)\)", label)
    main = re.sub(r"\([^)]*\)", " ", label)
    paren_tokens: list[str] = []
    for bit in paren_bits:
        for token in _word_tokens(bit):
            if token not in _META_PAREN_TOKENS:
                paren_tokens.append(token)
    return _word_tokens(main), paren_tokens


def _identity_keys(label: str) -> tuple[set[str], set[str]]:
    """Heuristic (givens, surnames) for conflict checks."""
    main, paren = _main_and_paren_tokens(label)
    givens: set[str] = set()
    surnames: set[str] = set()
    if len(main) >= 2:
        givens.add(main[0])
        surnames.add(main[-1])
    elif len(main) == 1:
        surnames.add(main[0])
    for token in paren:
        givens.add(token)
    return givens, surnames


def _is_strong_identity(label: str) -> bool:
    """True when the label asserts a given name (full name or titled + paren)."""
    main, paren = _main_and_paren_tokens(label)
    if len(main) >= 2:
        return True
    if main and paren:
        return True
    return False


def _pair_identity_conflict(a: str, b: str) -> bool:
    """True if two strong labels look like distinct people."""
    if not _is_strong_identity(a) or not _is_strong_identity(b):
        return False
    g1, s1 = _identity_keys(a)
    g2, s2 = _identity_keys(b)
    if not g1 or not g2 or not g1.isdisjoint(g2):
        return False
    # Distinct givens + overlapping surname → family / spouse collision
    if s1 and s2 and not s1.isdisjoint(s2):
        return True
    # Distinct givens + distinct surnames → different people
    if s1 and s2 and s1.isdisjoint(s2):
        return True
    # Distinct givens when at least one side lacks surname still refuse
    return True


def cluster_has_identity_conflict(aliases: list[str]) -> bool:
    """True if a cluster mixes distinct strong identities."""
    strong = [a for a in aliases if _is_strong_identity(a)]
    for i, left in enumerate(strong):
        for right in strong[i + 1 :]:
            if _pair_identity_conflict(left, right):
                return True
    return False


def _surname_overlap(a: str, b: str) -> bool:
    _, s1 = _identity_keys(a)
    _, s2 = _identity_keys(b)
    return bool(s1 and s2 and not s1.isdisjoint(s2))


def _has_title_prefix(label: str) -> bool:
    first = label.strip().split()[0].rstrip(".").casefold() if label.strip() else ""
    return first in _TITLE_PREFIXES


def _partition_character_cluster(
    aliases: list[str],
    *,
    chapter_counts: dict[str, int],
) -> list[list[str]]:
    """Split an unsafe cluster into conflict-free groups; attach short aliases."""
    strong = [a for a in aliases if _is_strong_identity(a)]
    weak = [a for a in aliases if not _is_strong_identity(a)]

    groups: list[list[str]] = [[name] for name in strong]
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                candidate = groups[i] + groups[j]
                if not cluster_has_identity_conflict(candidate):
                    groups[i] = candidate
                    groups.pop(j)
                    changed = True
                    break
            if changed:
                break

    for short in weak:
        candidates: list[tuple[int, int, int]] = []
        for i, group in enumerate(groups):
            if cluster_has_identity_conflict(group + [short]):
                continue
            base = 0
            if any(_surname_overlap(short, member) for member in group):
                base += 10
            short_cf = short.casefold()
            if any(
                short_cf == member.casefold()
                or short_cf in member.casefold()
                or member.casefold() in short_cf
                for member in group
            ):
                base += 3
            if base == 0:
                continue
            chapters = max(
                (chapter_counts.get(member, 0) for member in group),
                default=0,
            )
            candidates.append((base, chapters, i))
        if not candidates:
            groups.append([short])
            continue
        # Titled short forms (Dr. X) matching multiple people → leave singleton.
        if _has_title_prefix(short) and len(candidates) > 1:
            groups.append([short])
            continue
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        groups[candidates[0][2]].append(short)

    if not groups:
        return [[name] for name in aliases]
    return groups


def refine_character_alias_clusters(
    clusters: list[list[str]],
    *,
    chapter_counts: dict[str, int],
) -> tuple[list[list[str]], list[str]]:
    """Split identity-conflicting character clusters; return (clusters, warnings)."""
    refined: list[list[str]] = []
    warnings: list[str] = []
    for cluster in clusters:
        if len(cluster) <= 1 or not cluster_has_identity_conflict(cluster):
            refined.append(list(cluster))
            continue
        parts = _partition_character_cluster(
            cluster, chapter_counts=chapter_counts
        )
        warnings.append(
            "Split unsafe character cluster "
            f"{cluster!r} → {parts!r}"
        )
        refined.extend(parts)
    return refined, warnings


def build_book_rollup(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge characters and themes across chapter analysis dicts.

    Characters match on normalized name (case-insensitive, optional leading
    "The "). Themes match on case-insensitive exact string. No fuzzy alias
    merge (Queen vs Queen of Hearts stay separate).
    """
    char_raw_names: dict[str, Counter[str]] = defaultdict(Counter)
    char_chapters: dict[str, set[int]] = defaultdict(set)
    char_notes: dict[str, list[str]] = defaultdict(list)
    char_notes_seen: dict[str, set[str]] = defaultdict(set)

    theme_raw: dict[str, Counter[str]] = defaultdict(Counter)
    theme_chapters: dict[str, set[int]] = defaultdict(set)

    chapters_included: list[int] = []

    for analysis in sorted(analyses, key=lambda a: int(a.get("chapter", 0))):
        chapter = int(analysis["chapter"])
        chapters_included.append(chapter)

        for entry in analysis.get("characters") or []:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not name or not isinstance(name, str):
                continue
            key = normalize_character_key(name)
            if not key:
                continue
            char_raw_names[key][name.strip()] += 1
            char_chapters[key].add(chapter)
            note = entry.get("note")
            if isinstance(note, str):
                note = note.strip()
                if note and note not in char_notes_seen[key]:
                    char_notes_seen[key].add(note)
                    char_notes[key].append(note)

        for theme in analysis.get("themes") or []:
            if not isinstance(theme, str):
                continue
            theme = theme.strip()
            if not theme:
                continue
            key = normalize_theme_key(theme)
            theme_raw[key][theme] += 1
            theme_chapters[key].add(chapter)

    characters = []
    for key in sorted(char_raw_names.keys(), key=lambda k: _pick_display_name(char_raw_names[k]).casefold()):
        characters.append(
            {
                "name": _pick_display_name(char_raw_names[key]),
                "notes": char_notes[key],
                "chapters": sorted(char_chapters[key]),
            }
        )

    themes = []
    for key in sorted(theme_raw.keys(), key=lambda k: _pick_display_theme(theme_raw[k]).casefold()):
        themes.append(
            {
                "theme": _pick_display_theme(theme_raw[key]),
                "chapters": sorted(theme_chapters[key]),
            }
        )

    return {
        "chapters_included": chapters_included,
        "characters": characters,
        "themes": themes,
    }


def _complete_clusters(known: list[str], clusters: list[list[str]]) -> list[list[str]]:
    """Keep valid non-overlapping clusters; add singletons for uncovered names."""
    used: set[str] = set()
    completed: list[list[str]] = []
    known_set = set(known)

    for cluster in clusters:
        cleaned: list[str] = []
        for name in cluster:
            if name in known_set and name not in used:
                used.add(name)
                cleaned.append(name)
        if cleaned:
            completed.append(cleaned)

    for name in known:
        if name not in used:
            completed.append([name])

    return completed


def _pick_display_from_aliases(
    aliases: list[str],
    *,
    chapter_counts: dict[str, int],
) -> str:
    """Most source chapters; ties → longer alias, then alphabetical."""
    return max(
        aliases,
        key=lambda a: (chapter_counts.get(a, 0), len(a), a.casefold()),
    )


def apply_alias_clusters(
    rollup: dict[str, Any],
    clusters: dict[str, list[list[str]]],
) -> dict[str, Any]:
    """Merge rollup characters/themes using alias clusters (no LLM).

    Invalid / overlapping cluster members are ignored; uncovered labels become
    singleton clusters. Character clusters that mix distinct strong identities
    are split before merge. Display name/theme = most source chapters (ties →
    longer alias, then alphabetical).
    """
    char_by_name = {
        c["name"]: c
        for c in rollup.get("characters") or []
        if isinstance(c, dict) and isinstance(c.get("name"), str)
    }
    theme_by_label = {
        t["theme"]: t
        for t in rollup.get("themes") or []
        if isinstance(t, dict) and isinstance(t.get("theme"), str)
    }

    char_chapter_counts = {
        name: len(entry.get("chapters") or [])
        for name, entry in char_by_name.items()
    }
    theme_chapter_counts = {
        label: len(entry.get("chapters") or [])
        for label, entry in theme_by_label.items()
    }

    refined_chars, alias_warnings = refine_character_alias_clusters(
        clusters.get("characters") or [],
        chapter_counts=char_chapter_counts,
    )
    char_clusters = _complete_clusters(
        list(char_by_name.keys()),
        refined_chars,
    )
    theme_clusters = _complete_clusters(
        list(theme_by_label.keys()),
        clusters.get("themes") or [],
    )

    characters = []
    for aliases in char_clusters:
        display = _pick_display_from_aliases(
            aliases, chapter_counts=char_chapter_counts
        )
        notes: list[str] = []
        notes_seen: set[str] = set()
        chapters: set[int] = set()
        for alias in aliases:
            entry = char_by_name[alias]
            for note in entry.get("notes") or []:
                if isinstance(note, str) and note and note not in notes_seen:
                    notes_seen.add(note)
                    notes.append(note)
            for ch in entry.get("chapters") or []:
                chapters.add(int(ch))
        characters.append(
            {
                "name": display,
                "aliases": sorted(aliases, key=str.casefold),
                "notes": notes,
                "chapters": sorted(chapters),
            }
        )

    themes = []
    for aliases in theme_clusters:
        display = _pick_display_from_aliases(
            aliases, chapter_counts=theme_chapter_counts
        )
        chapters: set[int] = set()
        for alias in aliases:
            entry = theme_by_label[alias]
            for ch in entry.get("chapters") or []:
                chapters.add(int(ch))
        themes.append(
            {
                "theme": display,
                "aliases": sorted(aliases, key=str.casefold),
                "chapters": sorted(chapters),
            }
        )

    characters.sort(key=lambda c: c["name"].casefold())
    themes.sort(key=lambda t: t["theme"].casefold())

    payload: dict[str, Any] = {
        "source": "book-rollup.json",
        "chapters_included": list(rollup.get("chapters_included") or []),
        "characters": characters,
        "themes": themes,
    }
    if alias_warnings:
        payload["alias_warnings"] = alias_warnings
    return payload
