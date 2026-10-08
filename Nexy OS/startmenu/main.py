#!/usr/bin/env python3
# =============================================================================
# main.py - NEXY Start Menu
# =============================================================================

import sys
import signal
import os

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

APP_ID = "org.nexy.startmenu.dev"


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # כפה non-unique instance
    app = Gtk.Application(
        application_id=APP_ID,
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )

    def on_activate(a):
        print("[DEBUG] on_activate called", flush=True)
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from window import StartMenuWindow
        win = StartMenuWindow(application=a)
        a.__window = win

        # מנע סגירה — הסתר במקום
        win.connect("close-request", lambda w: w.minimize() or True)

        win.show_menu()
        print("[DEBUG] show_menu returned", flush=True)

    app.connect("activate", on_activate)
    print("[DEBUG] calling app.run()", flush=True)
    ret = app.run(sys.argv)
    print(f"[DEBUG] app.run() returned {ret}", flush=True)
    return ret


if __name__ == "__main__":
    sys.exit(main())
