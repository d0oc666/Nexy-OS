#pragma once
// =============================================================================
// desktop_ui.h  -  Nexy OS Desktop Shell
// Full graphical desktop: wallpaper + taskbar + icons (Files, Recycle Bin)
// =============================================================================

#include <stdint.h>
#include "vbe.h"
#include "font.h"
#include "icon_files.h"
#include "icon_recycle.h"

// ---------------------------------------------------------------------------
// Colour palette
// ---------------------------------------------------------------------------
static const uint32_t D_TASKBAR_BG   = rgb(18,  18,  28);
static const uint32_t D_TASKBAR_LINE = rgb(0,  140, 255);
static const uint32_t D_ICON_LABEL_FG= rgb(255, 255, 255);
static const uint32_t D_ICON_SHADOW  = rgb(0,   0,   0);
static const uint32_t D_CLOCK_FG     = rgb(200, 210, 230);
static const uint32_t D_START_BG     = rgb(0,  120, 220);
static const uint32_t D_START_FG     = rgb(255, 255, 255);

// ---------------------------------------------------------------------------
// Geometry
// ---------------------------------------------------------------------------
static const int TASKBAR_H   = 40;
static const int ICON_W      = 64;
static const int ICON_COL_X  = 20;
static const int ICON_START_Y= 20;
static const int ICON_SPACING= 90;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
static inline int dstrlen(const char* s)
{
    int n = 0; while (s[n]) ++n; return n;
}

// Draw label directly onto framebuffer (transparent background)
static void draw_icon_label_transparent(int cx, int y, const char* label)
{
    int len = dstrlen(label);
    int px  = cx - (len * FONT_W) / 2;

    for (const char* p = label; *p; ++p, px += FONT_W)
    {
        if ((unsigned char)*p < 32 || (unsigned char)*p > 127) continue;
        const uint8_t* glyph = FONT8X16[(unsigned char)*p - 32];
        for (int row = 0; row < FONT_H; ++row)
        {
            uint8_t byte = glyph[row];
            for (int bit = 7; bit >= 0; --bit)
            {
                if (byte & (1 << bit))
                {
                    int sx = px + (7 - bit);
                    vbe_put_pixel(sx + 1, y + row + 1, D_ICON_SHADOW);
                    vbe_put_pixel(sx,     y + row,     D_ICON_LABEL_FG);
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Draw a single desktop icon: RGBA image + label underneath
// ---------------------------------------------------------------------------
static void draw_icon_rgba(int ix, int iy,
                           const uint8_t* img_data, int img_w, int img_h,
                           const char* label)
{
    // Center the image in the ICON_W slot
    int ox = ix + (ICON_W - img_w) / 2;

    // Drop shadow (2px offset)
    for (int row = 0; row < img_h; ++row)
        for (int col = 0; col < img_w; ++col)
        {
            const uint8_t* p = img_data + (row * img_w + col) * 4;
            if (p[3] > 32)
                vbe_put_pixel(ox + col + 2, iy + row + 2, rgb(0, 0, 0));
        }

    // Actual icon
    vbe_draw_image_rgba(ox, iy, img_w, img_h, img_data);

    // Label
    draw_icon_label_transparent(ix + ICON_W / 2, iy + img_h + 5, label);
}

// ---------------------------------------------------------------------------
// Desktop Icons
// ---------------------------------------------------------------------------
static void draw_desktop_icons()
{
    draw_icon_rgba(ICON_COL_X, ICON_START_Y,
                   ICON_FILES_DATA,   ICON_FILES_W,   ICON_FILES_H,
                   "Files");

    draw_icon_rgba(ICON_COL_X, ICON_START_Y + ICON_SPACING,
                   ICON_RECYCLE_DATA, ICON_RECYCLE_W, ICON_RECYCLE_H,
                   "Recycle Bin");
}

// ---------------------------------------------------------------------------
// Taskbar
// ---------------------------------------------------------------------------
static void draw_taskbar()
{
    int W = (int)g_fb.width;
    int H = (int)g_fb.height;
    int y = H - TASKBAR_H;

    // Background
    vbe_fill_rect(0, y, W, TASKBAR_H, D_TASKBAR_BG);

    // Top accent line
    vbe_fill_rect(0, y, W, 2, D_TASKBAR_LINE);

    // ---- Start button ------------------------------------------------------
    int btn_x = 8;
    int btn_y = y + 6;
    int btn_w = 80;
    int btn_h = TASKBAR_H - 12;

    vbe_fill_rect(btn_x, btn_y, btn_w, btn_h, D_START_BG);
    vbe_fill_rect(btn_x, btn_y, btn_w, 1,     rgb(100, 180, 255));
    vbe_fill_rect(btn_x, btn_y, 1,     btn_h, rgb(100, 180, 255));

    const char* btn_lbl = "Nexy";
    int lbl_x = btn_x + btn_w / 2 - (dstrlen(btn_lbl) * FONT_W) / 2;
    int lbl_y = btn_y + btn_h / 2 - FONT_H / 2;
    int bx = lbl_x;
    for (const char* p = btn_lbl; *p; ++p, bx += FONT_W)
        vbe_draw_bitmap(bx, lbl_y, FONT_W, FONT_H,
                        FONT8X16[(unsigned char)*p - 32],
                        D_START_FG, D_START_BG, 1);

    // ---- Clock / label (right side) ----------------------------------------
    const char* clock_str = "Nexy OS";
    int cw   = dstrlen(clock_str) * FONT_W;
    int cl_x = W - cw - 12;
    int cl_y = y + (TASKBAR_H - FONT_H) / 2;

    vbe_fill_rect(cl_x - 8, y + 6, 1, TASKBAR_H - 12, rgb(50, 60, 90));

    int cx2 = cl_x;
    for (const char* p = clock_str; *p; ++p, cx2 += FONT_W)
        if ((unsigned char)*p >= 32)
            vbe_draw_bitmap(cx2, cl_y, FONT_W, FONT_H,
                            FONT8X16[(unsigned char)*p - 32],
                            D_CLOCK_FG, D_TASKBAR_BG, 1);
}

// ---------------------------------------------------------------------------
// Main entry: draw the full desktop
// ---------------------------------------------------------------------------
static void draw_desktop(const uint8_t* wallpaper_data, int wp_w, int wp_h)
{
    int W = (int)g_fb.width;
    int H = (int)g_fb.height;

    // 1. Wallpaper
    if (wallpaper_data)
    {
        vbe_clear(rgb(5, 5, 15));
        int ox = (W - wp_w) / 2;
        int oy = (H - TASKBAR_H - wp_h) / 2;
        if (ox < 0) ox = 0;
        if (oy < 0) oy = 0;
        vbe_draw_image_rgba(ox, oy, wp_w, wp_h, wallpaper_data);
    }
    else
    {
        vbe_clear(rgb(10, 15, 40));
    }

    // 2. Icons
    draw_desktop_icons();

    // 3. Taskbar
    draw_taskbar();
}
