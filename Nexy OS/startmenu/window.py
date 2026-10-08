#!/usr/bin/env python3
# =============================================================================
# window.py - חלון תפריט ההתחלה הראשי
# =============================================================================

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Adw, Gdk, GLib, GdkPixbuf, Gio, Pango

import settings as cfg
import app_index as idx
from app_index import AppEntry, launch_app, launch_app_as_root
from search_engine import search as fuzzy_search
from recent import load_recent, open_recent, format_modified, RecentEntry
import power

# נתיב ל-CSS
_CSS_PATH = Path(__file__).parent / "style.css"


def _load_css() -> None:
    provider = Gtk.CssProvider()
    provider.load_from_path(str(_CSS_PATH))
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def _make_app_icon(icon_name: str, size: int = 48) -> Gtk.Image:
    """יוצר Gtk.Image מאייקון freedesktop עם גיבוי."""
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    img = Gtk.Image()
    if theme.has_icon(icon_name):
        img.set_from_icon_name(icon_name)
    else:
        img.set_from_icon_name("application-x-executable")
    img.set_pixel_size(size)
    return img


def _truncate(text: str, max_chars: int = 12) -> str:
    """חותך טקסט ארוך."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


# =============================================================================
# StartMenuWindow
# =============================================================================

class StartMenuWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- הגדרות בסיסיות ---
        self.set_title("תפריט NEXY")
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_default_size(700, 560)
        self.add_css_class("start-menu-window")

        _load_css()

        # --- מצב ---
        self._settings   = cfg.load()
        self._all_apps: list[AppEntry] = []
        self._view_mode  = self._settings.get("view_mode", "categories")
        self._is_visible = False

        # --- בניית ממשק ---
        self._build_ui()

        # --- טעינת נתונים ברקע ---
        GLib.idle_add(self._load_data)

        # --- מקש Escape לסגירה ---
        esc = Gtk.ShortcutController()
        esc.set_scope(Gtk.ShortcutScope.GLOBAL)
        esc.add_shortcut(
            Gtk.Shortcut.new(
                Gtk.KeyvalTrigger.new(Gdk.KEY_Escape, 0),
                Gtk.CallbackAction.new(lambda *_: self.hide_menu()),
            )
        )
        self.add_controller(esc)

        # --- לחיצה מחוץ לחלון ---
        click = Gtk.GestureClick()
        click.set_button(0)
        click.connect("pressed", self._on_outside_click)
        self.add_controller(click)

    # ─────────────────────────────────────────────────────────────
    # בניית ממשק
    # ─────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.set_direction(Gtk.TextDirection.RTL)
        self.set_child(root)

        # 1. שורת חיפוש
        root.append(self._build_search_bar())

        # 2. אזור גוף גלילה
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(380)
        root.append(scroll)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body.set_direction(Gtk.TextDirection.RTL)
        scroll.set_child(body)
        self._body = body

        # 3. תוצאות חיפוש (מוסתר בהתחלה)
        self._search_results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._search_results_box.add_css_class("search-results-box")
        self._search_results_box.set_visible(False)
        body.append(self._search_results_box)

        # 4. מוצמד
        self._pinned_section = self._build_pinned_section()
        body.append(self._pinned_section)

        # 5. מפריד
        sep1 = Gtk.Separator()
        sep1.add_css_class("sm-separator")
        body.append(sep1)

        # 6. אחרונים
        self._recent_section = self._build_recent_section()
        body.append(self._recent_section)

        # 7. מפריד
        sep2 = Gtk.Separator()
        sep2.add_css_class("sm-separator")
        body.append(sep2)

        # 8. כל האפליקציות
        self._all_apps_section = self._build_all_apps_section()
        body.append(self._all_apps_section)

        # 9. סרגל תחתון
        root.append(self._build_bottom_bar())

    # ─── שורת חיפוש ───────────────────────────────────────────

    def _build_search_bar(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add_css_class("search-bar-box")

        entry = Gtk.SearchEntry()
        entry.set_placeholder_text("חיפוש אפליקציות, הגדרות ומסמכים")
        entry.add_css_class("search-entry")
        entry.set_direction(Gtk.TextDirection.RTL)
        entry.connect("search-changed", self._on_search_changed)
        entry.connect("activate", self._on_search_activate)

        # ניווט בחצים — EventControllerKey
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_search_key)
        entry.add_controller(key_ctrl)
        box.append(entry)
        self._search_entry = entry

        # תוצאת מחשבון
        calc_box = Gtk.Box()
        calc_box.add_css_class("calc-result-box")
        calc_box.set_visible(False)
        calc_lbl = Gtk.Label()
        calc_lbl.add_css_class("calc-result-label")
        calc_box.append(calc_lbl)
        box.append(calc_box)
        self._calc_box  = calc_box
        self._calc_label= calc_lbl

        return box

    # ─── אזור מוצמד ───────────────────────────────────────────

    def _build_pinned_section(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # כותרת
        header = self._make_section_header("מוצמד", "הצג הכל",
                                           self._on_show_all_pinned)
        box.append(header)

        # רשת 6×2
        grid = Gtk.FlowBox()
        grid.set_max_children_per_line(6)
        grid.set_min_children_per_line(6)
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.set_homogeneous(True)
        grid.add_css_class("app-grid")
        grid.set_direction(Gtk.TextDirection.RTL)
        box.append(grid)
        self._pinned_grid = grid

        return box

    # ─── אזור אחרונים ─────────────────────────────────────────

    def _build_recent_section(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        header = self._make_section_header("אחרונים", "הצג הכל",
                                           self._on_show_all_recent)
        box.append(header)

        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        list_box.add_css_class("recent-list")
        list_box.set_direction(Gtk.TextDirection.RTL)
        box.append(list_box)
        self._recent_list = list_box

        return box

    # ─── כל האפליקציות ────────────────────────────────────────

    def _build_all_apps_section(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # כותרת + בחירת תצוגה
        header_box = Gtk.Box(spacing=8)
        header_box.add_css_class("section-header")
        header_box.set_direction(Gtk.TextDirection.RTL)

        title = Gtk.Label(label="הכל")
        title.add_css_class("section-title")
        header_box.append(title)

        # בורר תצוגה
        view_combo = Gtk.DropDown.new_from_strings(["קטגוריות", "רשימה", "רשת"])
        mode_map = {"categories": 0, "list": 1, "grid": 2}
        view_combo.set_selected(mode_map.get(self._view_mode, 0))
        view_combo.connect("notify::selected", self._on_view_mode_changed)
        header_box.append(view_combo)
        self._view_combo = view_combo

        box.append(header_box)

        # תוכן גלילה
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add_css_class("all-apps-scroll")

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        inner.add_css_class("all-apps-list")
        inner.set_direction(Gtk.TextDirection.RTL)
        scroll.set_child(inner)
        box.append(scroll)
        self._all_apps_inner = inner

        return box

    # ─── סרגל תחתון ───────────────────────────────────────────

    def _build_bottom_bar(self) -> Gtk.Box:
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.add_css_class("bottom-bar")
        bar.set_direction(Gtk.TextDirection.RTL)

        # ─ כפתור משתמש (ימין ב-RTL) ─
        user_btn = Gtk.Button()
        user_btn.add_css_class("user-button")
        user_btn.connect("clicked", self._on_user_clicked)

        user_inner = Gtk.Box(spacing=8)
        user_inner.set_direction(Gtk.TextDirection.RTL)

        # תמונת משתמש
        avatar_path = power.get_avatar_path()
        if avatar_path:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    avatar_path, 36, 36, True)
                avatar_img = Gtk.Image.new_from_pixbuf(pixbuf)
            except Exception:
                avatar_img = Gtk.Image.new_from_icon_name("avatar-default")
                avatar_img.set_pixel_size(36)
        else:
            avatar_img = Gtk.Image.new_from_icon_name("avatar-default")
            avatar_img.set_pixel_size(36)
        avatar_img.add_css_class("avatar")
        user_inner.append(avatar_img)

        username = Gtk.Label(label=power.get_username())
        username.add_css_class("username-label")
        user_inner.append(username)

        user_btn.set_child(user_inner)
        bar.append(user_btn)

        # ─ מרווח ─
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        bar.append(spacer)

        # ─ כפתור כיבוי (שמאל ב-RTL) ─
        power_btn = Gtk.MenuButton()
        power_btn.add_css_class("power-button")
        power_btn.set_icon_name("system-shutdown-symbolic")
        power_btn.set_tooltip_text("כיבוי ואפשרויות")

        power_menu = Gio.Menu()
        power_menu.append("כיבוי",             "app.power-poweroff")
        power_menu.append("הפעלה מחדש",        "app.power-reboot")
        power_menu.append("שינה",              "app.power-suspend")
        power_menu.append("שינה עמוקה",        "app.power-hibernate")
        power_menu.append("נעילת מסך",         "app.power-lock")
        power_menu.append("התנתקות",           "app.power-logout")

        power_btn.set_menu_model(power_menu)

        # רישום פעולות
        app = self.get_application()
        power_actions = [
            ("power-poweroff",  power.poweroff),
            ("power-reboot",    power.reboot),
            ("power-suspend",   power.suspend),
            ("power-hibernate", power.hibernate),
            ("power-lock",      power.lock_screen),
            ("power-logout",    power.logout),
        ]
        for name, fn in power_actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda _a, _b, f=fn: (f(), self.hide_menu()))
            if app:
                app.add_action(action)

        bar.append(power_btn)

        return bar

    # ─────────────────────────────────────────────────────────────
    # עזרים לבניית ממשק
    # ─────────────────────────────────────────────────────────────

    def _make_section_header(self, title: str, btn_label: str,
                              btn_callback) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        box.add_css_class("section-header")
        box.set_direction(Gtk.TextDirection.RTL)

        lbl = Gtk.Label(label=title)
        lbl.add_css_class("section-title")
        lbl.set_hexpand(True)
        lbl.set_halign(Gtk.Align.START)
        box.append(lbl)

        btn = Gtk.Button(label=btn_label)
        btn.add_css_class("section-show-all")
        btn.connect("clicked", btn_callback)
        box.append(btn)

        return box

    def _make_app_button(self, entry: AppEntry, size: int = 48) -> Gtk.Button:
        """כפתור אייקון אפליקציה עם שם."""
        btn = Gtk.Button()
        btn.add_css_class("app-icon-button")
        btn.set_direction(Gtk.TextDirection.RTL)
        btn.set_tooltip_text(entry.name)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.set_halign(Gtk.Align.CENTER)

        icon = _make_app_icon(entry.icon, size)
        vbox.append(icon)

        lbl = Gtk.Label(label=_truncate(entry.name))
        lbl.add_css_class("app-icon-label")
        lbl.set_justify(Gtk.Justification.CENTER)
        lbl.set_wrap(True)
        lbl.set_max_width_chars(10)
        vbox.append(lbl)

        btn.set_child(vbox)
        btn.connect("clicked", lambda _b, e=entry: self._launch(e))

        # תפריט קליק ימני
        self._attach_context_menu(btn, entry)

        return btn

    def _attach_context_menu(self, btn: Gtk.Button, entry: AppEntry) -> None:
        """מחבר תפריט הקשר לכפתור אפליקציה."""
        gesture = Gtk.GestureClick()
        gesture.set_button(Gdk.BUTTON_SECONDARY)
        gesture.connect("pressed", self._on_icon_right_click, entry, btn)
        btn.add_controller(gesture)

    # ─────────────────────────────────────────────────────────────
    # טעינת נתונים
    # ─────────────────────────────────────────────────────────────

    def _load_data(self) -> bool:
        self._all_apps = idx.build_index()
        self._populate_pinned()
        self._populate_recent()
        self._populate_all_apps()
        return False  # GLib.idle_add — רץ פעם אחת

    def _populate_pinned(self) -> None:
        """ממלא את אזור המוצמד."""
        # נקה
        while child := self._pinned_grid.get_first_child():
            self._pinned_grid.remove(child)

        pinned_ids: list[str] = self._settings.get("pinned", [])
        app_map = {a.app_id: a for a in self._all_apps}

        shown = 0
        for app_id in pinned_ids:
            if app_id in app_map and shown < 12:  # 6×2
                btn = self._make_app_button(app_map[app_id])
                self._pinned_grid.append(btn)
                shown += 1

        # אם אין מוצמדים — הצג את ה-12 הראשונים
        if shown == 0:
            for entry in self._all_apps[:12]:
                btn = self._make_app_button(entry)
                self._pinned_grid.append(btn)

    def _populate_recent(self) -> None:
        """ממלא את אזור האחרונים."""
        # נקה
        while child := self._recent_list.get_first_child():
            self._recent_list.remove(child)

        if not self._settings.get("show_recent", True):
            self._recent_section.set_visible(False)
            return

        recent_items = load_recent()
        if not recent_items:
            self._recent_section.set_visible(False)
            return

        # 2 עמודות
        grid = Gtk.Grid(column_spacing=4, row_spacing=2)
        grid.set_direction(Gtk.TextDirection.RTL)

        for i, item in enumerate(recent_items[:8]):
            row = self._make_recent_row(item)
            col = i % 2
            rownum = i // 2
            grid.attach(row, col, rownum, 1, 1)

        self._recent_list.append(grid)

    def _make_recent_row(self, item: RecentEntry) -> Gtk.Button:
        btn = Gtk.Button()
        btn.add_css_class("recent-row")
        btn.set_direction(Gtk.TextDirection.RTL)
        btn.set_hexpand(True)
        btn.connect("clicked", lambda _b, e=item: (open_recent(e), self.hide_menu()))

        hbox = Gtk.Box(spacing=8)
        hbox.set_direction(Gtk.TextDirection.RTL)

        icon = _make_app_icon(item.icon, 32)
        hbox.append(icon)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_lbl = Gtk.Label(label=_truncate(item.title, 18))
        name_lbl.add_css_class("recent-name")
        name_lbl.set_halign(Gtk.Align.START)
        name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        vbox.append(name_lbl)

        time_lbl = Gtk.Label(label=format_modified(item))
        time_lbl.add_css_class("recent-time")
        time_lbl.set_halign(Gtk.Align.START)
        vbox.append(time_lbl)

        hbox.append(vbox)
        btn.set_child(hbox)
        return btn

    def _populate_all_apps(self) -> None:
        """ממלא את אזור כל האפליקציות לפי מצב תצוגה."""
        # נקה
        while child := self._all_apps_inner.get_first_child():
            self._all_apps_inner.remove(child)

        if self._view_mode == "categories":
            self._populate_categories()
        elif self._view_mode == "grid":
            self._populate_grid_all()
        else:
            self._populate_list_all()

    def _populate_categories(self) -> None:
        groups = idx.group_by_category(self._all_apps)
        for cat, apps in groups.items():
            # כותרת קטגוריה
            cat_lbl = Gtk.Label(label=cat)
            cat_lbl.add_css_class("category-label")
            cat_lbl.set_halign(Gtk.Align.START)
            self._all_apps_inner.append(cat_lbl)

            for app in apps:
                row = self._make_list_app_row(app)
                self._all_apps_inner.append(row)

    def _populate_list_all(self) -> None:
        current_letter = ""
        for app in self._all_apps:
            first = (app.name[0].upper() if app.name else "?")
            if first != current_letter:
                current_letter = first
                ltr_lbl = Gtk.Label(label=current_letter)
                ltr_lbl.add_css_class("category-label")
                ltr_lbl.set_halign(Gtk.Align.START)
                self._all_apps_inner.append(ltr_lbl)
            self._all_apps_inner.append(self._make_list_app_row(app))

    def _populate_grid_all(self) -> None:
        flow = Gtk.FlowBox()
        flow.set_max_children_per_line(6)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_direction(Gtk.TextDirection.RTL)
        for app in self._all_apps:
            flow.append(self._make_app_button(app, 40))
        self._all_apps_inner.append(flow)

    def _make_list_app_row(self, entry: AppEntry) -> Gtk.Button:
        btn = Gtk.Button()
        btn.add_css_class("all-app-row")
        btn.set_direction(Gtk.TextDirection.RTL)
        btn.connect("clicked", lambda _b, e=entry: self._launch(e))

        hbox = Gtk.Box(spacing=10)
        hbox.set_direction(Gtk.TextDirection.RTL)

        icon = _make_app_icon(entry.icon, 32)
        hbox.append(icon)

        lbl = Gtk.Label(label=entry.name)
        lbl.add_css_class("all-app-name")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        hbox.append(lbl)

        btn.set_child(hbox)
        self._attach_context_menu(btn, entry)
        return btn

    # ─────────────────────────────────────────────────────────────
    # חיפוש
    # ─────────────────────────────────────────────────────────────

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        query = entry.get_text()

        # נקה תוצאות קודמות
        while child := self._search_results_box.get_first_child():
            self._search_results_box.remove(child)

        if not query.strip():
            self._search_results_box.set_visible(False)
            self._calc_box.set_visible(False)
            self._pinned_section.set_visible(True)
            self._recent_section.set_visible(True)
            self._all_apps_section.set_visible(True)
            return

        # הסתר אזורים רגילים
        self._pinned_section.set_visible(False)
        self._recent_section.set_visible(False)
        self._all_apps_section.set_visible(False)
        self._search_results_box.set_visible(True)

        results, calc_result, is_shell = fuzzy_search(query, self._all_apps)

        # תוצאת מחשבון
        if calc_result:
            self._calc_label.set_text(f"= {calc_result}")
            self._calc_box.set_visible(True)
        else:
            self._calc_box.set_visible(False)

        # פקודת shell
        if is_shell:
            cmd_lbl = Gtk.Label(
                label=f"הרץ: {query.lstrip('!$').strip()}"
            )
            cmd_lbl.add_css_class("search-result-name")
            btn = Gtk.Button()
            btn.add_css_class("search-result-row")
            btn.set_child(cmd_lbl)
            btn.connect("clicked",
                lambda _b, q=query: self._run_shell(q.lstrip("!$").strip()))
            self._search_results_box.append(btn)
            return

        if not results:
            no_res = Gtk.Label(label="לא נמצאו תוצאות")
            no_res.add_css_class("search-result-desc")
            no_res.set_halign(Gtk.Align.CENTER)
            no_res.set_margin_top(20)
            self._search_results_box.append(no_res)
            return

        for res in results:
            row = self._make_search_result_row(res.entry)
            self._search_results_box.append(row)

    def _make_search_result_row(self, entry: AppEntry) -> Gtk.Button:
        btn = Gtk.Button()
        btn.add_css_class("search-result-row")
        btn.set_direction(Gtk.TextDirection.RTL)
        btn.connect("clicked", lambda _b, e=entry: self._launch(e))

        hbox = Gtk.Box(spacing=10)
        hbox.set_direction(Gtk.TextDirection.RTL)

        icon = _make_app_icon(entry.icon, 36)
        hbox.append(icon)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_lbl = Gtk.Label(label=entry.name)
        name_lbl.add_css_class("search-result-name")
        name_lbl.set_halign(Gtk.Align.START)
        vbox.append(name_lbl)

        cat_lbl = Gtk.Label(label=" · ".join(entry.categories))
        cat_lbl.add_css_class("search-result-desc")
        cat_lbl.set_halign(Gtk.Align.START)
        vbox.append(cat_lbl)

        hbox.append(vbox)
        btn.set_child(hbox)
        return btn

    def _on_search_activate(self, entry: Gtk.SearchEntry) -> None:
        """Enter — הפעל את התוצאה הראשונה."""
        query = entry.get_text().strip()
        if not query:
            return
        if query.startswith(("!", "$")):
            self._run_shell(query.lstrip("!$").strip())
            return
        results, calc_result, _ = fuzzy_search(query, self._all_apps, max_results=1)
        if results:
            self._launch(results[0].entry)

    def _on_search_key(self, controller, keyval, keycode, state) -> bool:
        """ניווט בחצים בין תוצאות."""
        return False  # placeholder — ניווט מלא בגרסה עתידית

    # ─────────────────────────────────────────────────────────────
    # תפריט הקשר
    # ─────────────────────────────────────────────────────────────

    def _on_icon_right_click(self, gesture, n, x, y,
                              entry: AppEntry, widget: Gtk.Widget) -> None:
        popover = Gtk.Popover()
        popover.set_parent(widget)
        popover.set_has_arrow(False)

        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        actions = [
            ("פתח",                      lambda e=entry: self._launch(e)),
            ("הפעל כ-root",              lambda e=entry: launch_app_as_root(e)),
            ("הוסף לשולחן העבודה",       lambda e=entry: self._add_to_desktop(e)),
            ("הצמד / בטל הצמדה",        lambda e=entry: self._toggle_pin(e)),
            ("פתח מיקום קובץ",           lambda e=entry: self._open_location(e)),
        ]

        for label, callback in actions:
            btn = Gtk.Button(label=label)
            btn.add_css_class("power-button")
            btn.connect("clicked",
                lambda _b, cb=callback: (cb(), popover.popdown()))
            menu_box.append(btn)

        popover.set_child(menu_box)
        popover.popup()

    def _toggle_pin(self, entry: AppEntry) -> None:
        pinned = self._settings.setdefault("pinned", [])
        if entry.app_id in pinned:
            pinned.remove(entry.app_id)
        else:
            pinned.append(entry.app_id)
        cfg.save(self._settings)
        self._populate_pinned()

    def _add_to_desktop(self, entry: AppEntry) -> None:
        desktop = Path.home() / "Desktop"
        desktop.mkdir(exist_ok=True)
        target = desktop / entry.desktop_file.name
        try:
            import shutil
            shutil.copy2(str(entry.desktop_file), str(target))
            os.chmod(str(target), 0o755)
        except Exception:
            pass

    def _open_location(self, entry: AppEntry) -> None:
        folder = str(entry.desktop_file.parent)
        subprocess.Popen(["xdg-open", folder])

    # ─────────────────────────────────────────────────────────────
    # פעולות כפתור משתמש
    # ─────────────────────────────────────────────────────────────

    def _on_user_clicked(self, btn: Gtk.Button) -> None:
        popover = Gtk.Popover()
        popover.set_parent(btn)
        popover.set_has_arrow(True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        user_actions = [
            ("הגדרות חשבון",    lambda: subprocess.Popen(["gnome-control-center", "user-accounts"])),
            ("נעילת מסך",      power.lock_screen),
            ("החלפת משתמש",    power.switch_user),
            ("התנתקות",        power.logout),
        ]

        for label, callback in user_actions:
            b = Gtk.Button(label=label)
            b.add_css_class("power-button")
            b.connect("clicked",
                lambda _b, cb=callback: (cb(), popover.popdown(), self.hide_menu()))
            vbox.append(b)

        popover.set_child(vbox)
        popover.popup()

    # ─────────────────────────────────────────────────────────────
    # בחירת תצוגה
    # ─────────────────────────────────────────────────────────────

    def _on_view_mode_changed(self, combo: Gtk.DropDown, _param) -> None:
        modes = ["categories", "list", "grid"]
        idx_sel = combo.get_selected()
        self._view_mode = modes[idx_sel] if idx_sel < len(modes) else "categories"
        self._settings["view_mode"] = self._view_mode
        cfg.save(self._settings)
        self._populate_all_apps()

    # ─────────────────────────────────────────────────────────────
    # הצג הכל
    # ─────────────────────────────────────────────────────────────

    def _on_show_all_pinned(self, _btn) -> None:
        """עבור לתצוגת כל האפליקציות."""
        self._view_combo.set_selected(2)  # grid
        self._all_apps_section.set_visible(True)

    def _on_show_all_recent(self, _btn) -> None:
        pass  # placeholder — גרסה עתידית תפתח חלון נפרד

    # ─────────────────────────────────────────────────────────────
    # הפעלה
    # ─────────────────────────────────────────────────────────────

    def _launch(self, entry: AppEntry) -> None:
        self.hide_menu()
        GLib.timeout_add(50, lambda: launch_app(entry) or False)

    def _run_shell(self, cmd: str) -> None:
        self.hide_menu()
        subprocess.Popen(
            ["bash", "-c", cmd],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # ─────────────────────────────────────────────────────────────
    # חשיפה / הסתרה + אנימציה
    # ─────────────────────────────────────────────────────────────

    def toggle(self) -> None:
        if self._is_visible:
            self.hide_menu()
        else:
            self.show_menu()

    def show_menu(self) -> None:
        self._dummy_hide()
        self.set_default_size(700, 560)
        self.set_visible(True)
        self.present()
        self._is_visible = True
        self._search_entry.set_text("")
        self._search_entry.grab_focus()
        self._populate_recent()

    def hide_menu(self) -> None:
        self._is_visible = False
        self.set_visible(False)
        self._dummy_show()

    def _dummy_show(self) -> None:
        """חלון 1×1 בלתי נראה שמונע יציאת האפליקציה."""
        if not hasattr(self, "_dummy"):
            self._dummy = Gtk.Window(application=self.get_application())
            self._dummy.set_default_size(1, 1)
            self._dummy.set_decorated(False)
            self._dummy.set_opacity(0)
        self._dummy.set_visible(True)

    def _dummy_hide(self) -> None:
        if hasattr(self, "_dummy"):
            self._dummy.set_visible(False)

    def _position_window(self) -> None:
        """ממקם את החלון מרכז תחתית / שמאל תחתית."""
        display = Gdk.Display.get_default()
        if not display:
            return
        monitor = display.get_monitors().get_item(0)
        if not monitor:
            return
        geo = monitor.get_geometry()
        w = self.get_width()  or 700
        h = self.get_height() or 560

        position = self._settings.get("position", "center")
        if position == "left":
            x = 10
        else:
            x = (geo.width - w) // 2

        # 60px מהתחתית (גובה פאנל טיפוסי)
        y = geo.height - h - 60

        # GTK4 — מיקום ידני דרך surface במקום move()
        # (בסביבות Wayland — ניתן רק עם layer-shell)
        try:
            self.set_default_size(700, 560)
        except Exception:
            pass

    def _on_outside_click(self, gesture, n, x, y) -> None:
        # בדיקה אם הלחיצה היתה מחוץ לחלון
        w = self.get_width()
        h = self.get_height()
        if x < 0 or y < 0 or x > w or y > h:
            self.hide_menu()
