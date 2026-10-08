; =============================================================
; nexy_super.ahk - מקש Super פותח תפריט NEXY
; AutoHotkey v2
; =============================================================

; הפעל את התפריט ברקע בהתחלה
Run 'wsl.exe bash -c "LIBGL_ALWAYS_SOFTWARE=1 python3 \"/mnt/c/Users/hemig/Downloads/Nexy OS/startmenu/main.py\""',, "Hide"

Sleep 2000  ; המתן שהתפריט יעלה

; ── מקש Super — הצג/הסתר תפריט ──────────────────────────────
LWin::
{
    if WinExist("תפריט NEXY")
    {
        if WinActive("תפריט NEXY")
        {
            WinHide
        }
        else
        {
            WinShow
            WinActivate "תפריט NEXY"
        }
    }
    else
    {
        ; הפעל מחדש אם נסגר
        Run 'wsl.exe bash -c "LIBGL_ALWAYS_SOFTWARE=1 python3 \"/mnt/c/Users/hemig/Downloads/Nexy OS/startmenu/main.py\""',, "Hide"
    }
}

; ── בלוק את תפריט Windows המקורי ─────────────────────────────
LWin up::  return
