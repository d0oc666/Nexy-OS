#!/usr/bin/env python3
# =============================================================================
# settings.py - ניהול הגדרות התפריט
# קובץ: ~/.config/nexy/startmenu.json
# =============================================================================

import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "nexy" / "startmenu.json"

# ערכי ברירת מחדל
_DEFAULTS: dict = {
    "pinned": [
        "org.gnome.Nautilus",
        "org.gnome.Terminal",
        "firefox",
        "org.gnome.Settings",
        "org.gnome.gedit",
        "org.libreoffice.Writer",
    ],
    "view_mode": "categories",   # "categories" | "list" | "grid"
    "theme": "dark",
    "position": "center",        # "center" | "left"
    "blur": True,
    "show_recent": True,
}


def load() -> dict:
    """טוען הגדרות מהקובץ, ממלא ברירות מחדל לשדות חסרים."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # ממלא שדות חסרים
            for key, val in _DEFAULTS.items():
                data.setdefault(key, val)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def save(data: dict) -> None:
    """שומר הגדרות לקובץ JSON."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
