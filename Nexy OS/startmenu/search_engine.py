#!/usr/bin/env python3
# =============================================================================
# search_engine.py - מנוע חיפוש fuzzy
# =============================================================================

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app_index import AppEntry


@dataclass
class SearchResult:
    """תוצאת חיפוש אחת עם ציון רלוונטיות."""
    entry: "AppEntry"
    score: int      # ציון גבוה יותר = רלוונטי יותר


def _fuzzy_score(query: str, text: str) -> int:
    """
    מחשב ציון fuzzy:
    100  - התאמה מדויקת בתחילת השם
    80   - שם מכיל את השאילתה כולה
    60   - כל מילות השאילתה מופיעות בטקסט
    1+   - התאמת תווים חלקית (levenshtein-style)
    0    - אין התאמה
    """
    q = query.strip().lower()
    t = text.lower()

    if not q:
        return 0

    # התאמה מדויקת בתחילה
    if t.startswith(q):
        return 100

    # השם מכיל את השאילתה כולה
    if q in t:
        return 80

    # כל מילות השאילתה קיימות
    words = q.split()
    if all(w in t for w in words):
        return 60

    # חיפוש תווים רצופים (fuzzy)
    qi = 0
    score = 0
    for ch in t:
        if qi < len(q) and ch == q[qi]:
            qi += 1
            score += 1
    if qi == len(q):
        return score
    return 0


def _is_math(query: str) -> bool:
    """האם השאילתה נראית כמו תרגיל חשבון."""
    return bool(re.match(r"^[\d\s\+\-\*\/\(\)\.]+$", query.strip()))


def _eval_math(query: str) -> str | None:
    """מחשב תרגיל חשבון בבטחה."""
    try:
        result = eval(  # noqa: S307
            query,
            {"__builtins__": {}},
            {}
        )
        return str(result)
    except Exception:
        return None


def _is_shell_command(query: str) -> bool:
    """האם השאילתה היא פקודת shell (מתחילה ב-! או $)."""
    return query.strip().startswith(("!", "$"))


def search(
    query: str,
    apps: list["AppEntry"],
    max_results: int = 12,
) -> tuple[list[SearchResult], str | None, bool]:
    """
    מחפש בכל הרשימה ומחזיר:
      - רשימת SearchResult ממוינת לפי ציון
      - תוצאת מחשבון (או None)
      - האם זו פקודת shell
    """
    q = query.strip()

    # פקודת shell
    if _is_shell_command(q):
        return [], None, True

    # מחשבון
    calc_result: str | None = None
    if _is_math(q):
        calc_result = _eval_math(q)

    if not q:
        return [], calc_result, False

    results: list[SearchResult] = []
    for app in apps:
        # בדיקה ראשונה על השם (ציון גבוה יותר)
        score_name = _fuzzy_score(q, app.name)
        score_en   = _fuzzy_score(q, app.name_en)
        score_full = _fuzzy_score(q, app.search_text)
        score = max(score_name * 2, score_en, score_full)

        if score > 0:
            results.append(SearchResult(entry=app, score=score))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:max_results], calc_result, False
