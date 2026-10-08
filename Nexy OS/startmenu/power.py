#!/usr/bin/env python3
# =============================================================================
# power.py - פעולות כיבוי ומשתמש דרך systemd / loginctl
# =============================================================================

import os
import subprocess
import pwd


def _run(cmd: list[str]) -> None:
    """מריץ פקודה ומנתק אותה מהתהליך."""
    subprocess.Popen(cmd, start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def poweroff() -> None:
    _run(["systemctl", "poweroff"])


def reboot() -> None:
    _run(["systemctl", "reboot"])


def suspend() -> None:
    _run(["systemctl", "suspend"])


def hibernate() -> None:
    _run(["systemctl", "hibernate"])


def lock_screen() -> None:
    # מנסה כמה שיטות לפי מה שמותקן
    for cmd in [
        ["loginctl", "lock-session"],
        ["gnome-screensaver-command", "--lock"],
        ["xdg-screensaver", "lock"],
        ["swaylock"],
    ]:
        try:
            _run(cmd)
            return
        except FileNotFoundError:
            continue


def logout() -> None:
    try:
        session_id = subprocess.check_output(
            ["loginctl", "show-user", str(os.getuid()), "--property=Sessions", "--value"],
            text=True,
        ).strip().split()[0]
        _run(["loginctl", "terminate-session", session_id])
    except Exception:
        # גיבוי — סגירת DE
        for cmd in [
            ["gnome-session-quit", "--logout", "--no-prompt"],
            ["openbox", "--exit"],
        ]:
            try:
                _run(cmd)
                return
            except FileNotFoundError:
                continue


def switch_user() -> None:
    for cmd in [
        ["dm-tool", "switch-to-greeter"],
        ["gdm-control", "--switch-to-greeter"],
    ]:
        try:
            _run(cmd)
            return
        except FileNotFoundError:
            continue


def get_username() -> str:
    """מחזיר שם המשתמש הנוכחי."""
    try:
        return pwd.getpwuid(os.getuid()).pw_gecos.split(",")[0] or os.getlogin()
    except Exception:
        return os.environ.get("USER", "משתמש")


def get_avatar_path() -> str | None:
    """מחזיר נתיב לתמונת המשתמש אם קיימת."""
    candidates = [
        os.path.expanduser("~/.face"),
        os.path.expanduser("~/.face.icon"),
        f"/var/lib/AccountsService/icons/{os.environ.get('USER', '')}",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None
