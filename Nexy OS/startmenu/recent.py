#!/usr/bin/env python3
# =============================================================================
# recent.py - קבצים שנפתחו לאחרונה
# קורא מ-~/.local/share/recently-used.xbel
# =============================================================================

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

XBEL_PATH = Path.home() / ".local/share/recently-used.xbel"
MAX_RECENT = 8


@dataclass
class RecentEntry:
    """פריט אחד מרשימת האחרונים."""
    uri: str
    title: str
    mime_type: str
    modified: float     # Unix timestamp
    icon: str = "text-x-generic"


def _relative_time(ts: float) -> str:
    """ממיר timestamp לטקסט יחסי בעברית."""
    diff = time.time() - ts
    if diff < 60:
        return "עכשיו"
    if diff < 3600:
        m = int(diff / 60)
        return f"לפני {m} דקות"
    if diff < 86400:
        h = int(diff / 3600)
        return f"לפני {h} שעות"
    d = int(diff / 86400)
    if d == 1:
        return "אתמול"
    return f"לפני {d} ימים"


def _mime_to_icon(mime: str) -> str:
    """ממיר mime type לשם אייקון."""
    mapping = {
        "application/pdf":                "application-pdf",
        "application/msword":             "x-office-document",
        "application/vnd.oasis.opendocument.text": "x-office-document",
        "image/":                         "image-x-generic",
        "video/":                         "video-x-generic",
        "audio/":                         "audio-x-generic",
        "text/":                          "text-x-generic",
    }
    for prefix, icon in mapping.items():
        if mime.startswith(prefix):
            return icon
    return "text-x-generic"


def load_recent() -> list[RecentEntry]:
    """טוען ומחזיר את הקבצים האחרונים."""
    if not XBEL_PATH.exists():
        return []

    try:
        tree = ET.parse(XBEL_PATH)
        root = tree.getroot()
    except ET.ParseError:
        return []

    entries: list[RecentEntry] = []
    ns = {"xbel": "http://www.freedesktop.org/standards/xbel/1.0/"}

    for bookmark in root.findall("bookmark"):
        uri = bookmark.get("href", "")
        modified_str = bookmark.get("modified", "")
        title_el = bookmark.find("title")
        title = title_el.text if title_el is not None else ""

        # שם קובץ כגיבוי לכותרת
        if not title:
            try:
                parsed = urlparse(uri)
                title = unquote(os.path.basename(parsed.path))
            except Exception:
                title = uri

        # זמן שינוי
        modified = 0.0
        if modified_str:
            try:
                import datetime
                dt = datetime.datetime.fromisoformat(
                    modified_str.replace("Z", "+00:00")
                )
                modified = dt.timestamp()
            except Exception:
                pass

        # mime type
        mime_el = bookmark.find(
            "info/metadata/mime:mime-type",
            {"mime": "http://www.freedesktop.org/standards/shared-mime-info"},
        )
        mime = mime_el.get("type", "") if mime_el is not None else ""

        entries.append(RecentEntry(
            uri=uri,
            title=title,
            mime_type=mime,
            modified=modified,
            icon=_mime_to_icon(mime),
        ))

    # מיון לפי זמן — הכי חדש ראשון
    entries.sort(key=lambda e: e.modified, reverse=True)
    return entries[:MAX_RECENT]


def open_recent(entry: RecentEntry) -> None:
    """פותח קובץ אחרון עם האפליקציה המתאימה."""
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gio, GLib

    try:
        file = Gio.File.new_for_uri(entry.uri)
        launcher = Gio.FileLauncher.new(file)
        launcher.launch(None, None, None)
    except Exception:
        os.system(f"xdg-open '{entry.uri}'")


def format_modified(entry: RecentEntry) -> str:
    return _relative_time(entry.modified)
