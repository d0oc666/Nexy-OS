#!/usr/bin/env python3
# =============================================================================
# app_index.py - אינדקס אפליקציות
# קורא קבצי .desktop מכל המיקומים הסטנדרטיים (freedesktop + Flatpak + Snap)
# =============================================================================

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

# תיקיות לחיפוש קבצי .desktop
_SEARCH_DIRS: list[Path] = [
    Path("/usr/share/applications"),
    Path("/usr/local/share/applications"),
    Path.home() / ".local/share/applications",
    # Flatpak
    Path("/var/lib/flatpak/exports/share/applications"),
    Path.home() / ".local/share/flatpak/exports/share/applications",
    # Snap
    Path("/var/lib/snapd/desktop/applications"),
]

# מיפוי קטגוריות freedesktop → שם בעברית
CATEGORY_NAMES: dict[str, str] = {
    "AudioVideo":   "מולטימדיה",
    "Audio":        "מולטימדיה",
    "Video":        "מולטימדיה",
    "Development":  "פיתוח",
    "Education":    "חינוך",
    "Game":         "משחקים",
    "Graphics":     "גרפיקה",
    "Network":      "אינטרנט",
    "Office":       "משרד",
    "Science":      "מדע",
    "Settings":     "הגדרות",
    "System":       "מערכת",
    "Utility":      "כלי עזר",
}

# סדר הקטגוריות בתצוגה
CATEGORY_ORDER = [
    "אינטרנט", "משרד", "גרפיקה", "פיתוח",
    "משחקים", "מולטימדיה", "מערכת", "הגדרות", "כלי עזר", "חינוך", "מדע",
]


@dataclass
class AppEntry:
    """מייצג אפליקציה אחת."""
    app_id: str                     # שם קובץ .desktop ללא סיומת
    name: str                       # שם להצגה (עברית אם קיים)
    name_en: str                    # שם באנגלית
    icon: str                       # שם האייקון
    exec_str: str                   # מחרוזת Exec מנוקה
    categories: list[str]           # קטגוריות בעברית
    desktop_file: Path              # נתיב המלא
    gapp: Optional[object] = None   # GDesktopAppInfo

    # טקסט נרמול לחיפוש (מחושב בהמשך)
    search_text: str = field(default="", repr=False)

    def __post_init__(self):
        self.search_text = (
            self.name.lower() + " " +
            self.name_en.lower() + " " +
            " ".join(self.categories).lower()
        )


def _clean_exec(exec_str: str) -> str:
    """מסיר קודי שדות כמו %u %F %i %c %k מתוך Exec."""
    return re.sub(r"%[uUfFdDnNickvm]", "", exec_str).strip()


def _parse_desktop_file(path: Path) -> Optional[AppEntry]:
    """מנתח קובץ .desktop ומחזיר AppEntry או None אם יש להסתיר."""
    try:
        gapp = Gio.DesktopAppInfo.new_from_filename(str(path))
    except Exception:
        return None

    if gapp is None:
        return None

    # מסנן אפליקציות מוסתרות
    if gapp.get_nodisplay() or gapp.get_is_hidden():
        return None

    # שם — מעדיף עברית
    name_he = gapp.get_string("Name[he]") or ""
    name_en = gapp.get_name() or path.stem
    name = name_he if name_he else name_en

    # אייקון
    icon_name = gapp.get_string("Icon") or "application-x-executable"

    # Exec
    exec_str = _clean_exec(gapp.get_string("Exec") or "")

    # קטגוריות
    cats_raw = gapp.get_string("Categories") or ""
    categories: list[str] = []
    seen: set[str] = set()
    for cat in cats_raw.split(";"):
        cat = cat.strip()
        heb = CATEGORY_NAMES.get(cat)
        if heb and heb not in seen:
            categories.append(heb)
            seen.add(heb)
    if not categories:
        categories = ["כלי עזר"]

    return AppEntry(
        app_id=path.stem,
        name=name,
        name_en=name_en,
        icon=icon_name,
        exec_str=exec_str,
        categories=categories,
        desktop_file=path,
        gapp=gapp,
    )


def build_index() -> list[AppEntry]:
    """
    בונה ומחזיר את רשימת כל האפליקציות הזמינות,
    ממוינות לפי שם (א–ת / A–Z).
    """
    seen_ids: set[str] = set()
    apps: list[AppEntry] = []

    for search_dir in _SEARCH_DIRS:
        if not search_dir.is_dir():
            continue
        for desktop_file in sorted(search_dir.glob("*.desktop")):
            app_id = desktop_file.stem
            if app_id in seen_ids:
                continue
            entry = _parse_desktop_file(desktop_file)
            if entry:
                seen_ids.add(app_id)
                apps.append(entry)

    apps.sort(key=lambda a: a.name.lower())
    return apps


def launch_app(entry: AppEntry) -> None:
    """מפעיל אפליקציה ומנתק אותה מהתהליך הנוכחי."""
    try:
        if entry.gapp:
            ctx = entry.gapp.launch([], None)
            return
    except Exception:
        pass
    # גיבוי — הפעלה ישירה
    os.spawnlp(os.P_NOWAIT, "gio", "gio", "launch", str(entry.desktop_file))


def launch_app_as_root(entry: AppEntry) -> None:
    """מפעיל אפליקציה עם הרשאות root (pkexec)."""
    os.spawnlp(os.P_NOWAIT, "pkexec", "pkexec", entry.exec_str)


def group_by_category(apps: list[AppEntry]) -> dict[str, list[AppEntry]]:
    """מקבץ אפליקציות לפי קטגוריה עיקרית."""
    groups: dict[str, list[AppEntry]] = {}
    for app in apps:
        cat = app.categories[0] if app.categories else "כלי עזר"
        groups.setdefault(cat, []).append(app)
    # מיון לפי הסדר המוגדר
    ordered: dict[str, list[AppEntry]] = {}
    for cat in CATEGORY_ORDER:
        if cat in groups:
            ordered[cat] = groups[cat]
    # קטגוריות שלא הוגדרו בסדר — בסוף
    for cat, lst in groups.items():
        if cat not in ordered:
            ordered[cat] = lst
    return ordered
