// =============================================================================
// kmain.cpp - Nexy OS Kernel Entry Point
// =============================================================================

#include <stdint.h>
#include <stddef.h>
#include "vga.h"
#include "vbe.h"
#include "font.h"
#include "logo.h"
#include "desktop.h"       // wallpaper pixel data (DESKTOP_DATA, DESKTOP_W, DESKTOP_H)
#include "desktop_ui.h"    // draw_desktop()

// =============================================================================
// VGA Text fallback (when no VBE framebuffer is available)
// =============================================================================
static void show_text_boot()
{
    vga_init();
    vga_clear(VGA_BLACK);

    // Title bar
    for (int i = 0; i < VGA_WIDTH; ++i)
        vga_puts_at(i, 0, " ", vga_color(VGA_WHITE, VGA_BLUE));

    vga_puts_at(30, 0, "  Nexy OS v0.1.0  ",
                vga_color(VGA_LIGHT_BROWN, VGA_BLUE));

    vga_puts_at(20, 4,  " _   _ _______  ____   __   _  ", vga_color(VGA_LIGHT_CYAN, VGA_BLACK));
    vga_puts_at(20, 5,  "| \\ | | ____\\ \\/ /\\ \\ / /  | | ", vga_color(VGA_LIGHT_CYAN, VGA_BLACK));
    vga_puts_at(20, 6,  "|  \\| |  _|  \\  /  \\ V /   | | ", vga_color(VGA_CYAN,       VGA_BLACK));
    vga_puts_at(20, 7,  "| |\\  | |___ /  \\   | |    |_| ", vga_color(VGA_BLUE,       VGA_BLACK));
    vga_puts_at(20, 8,  "|_| \\_|_____/_/\\_\\  |_|    (_) ", vga_color(VGA_LIGHT_BLUE, VGA_BLACK));

    vga_puts_at(22, 10, "A Bare-Metal Operating System",
                vga_color(VGA_LIGHT_GREY, VGA_BLACK));

    for (int i = 2; i < VGA_WIDTH - 2; ++i)
        vga_puts_at(i, 12, "-", vga_color(VGA_DARK_GREY, VGA_BLACK));

    vga_puts_at(4, 14, "Architecture : x86 32-bit Protected Mode", vga_color(VGA_LIGHT_GREEN, VGA_BLACK));
    vga_puts_at(4, 15, "Display mode : VGA Text 80x25 (Fallback)",  vga_color(VGA_LIGHT_GREEN, VGA_BLACK));
    vga_puts_at(4, 16, "Kernel base  : 0x00100000",                 vga_color(VGA_LIGHT_BROWN, VGA_BLACK));
    vga_puts_at(4, 17, "Status       : [ OK ] Kernel loaded",       vga_color(VGA_LIGHT_GREEN, VGA_BLACK));

    for (int i = 0; i < VGA_WIDTH; ++i)
        vga_puts_at(i, VGA_HEIGHT - 1, " ", vga_color(VGA_WHITE, VGA_BLUE));

    vga_puts_at(2, VGA_HEIGHT - 1,
        "Nexy OS v0.1.0  |  2026.10.06",
        vga_color(VGA_LIGHT_BROWN, VGA_BLUE));
}

// =============================================================================
// Static constructors
// =============================================================================
typedef void (*constructor_t)();
extern constructor_t __init_array_start[];
extern constructor_t __init_array_end[];

static void call_constructors()
{
    for (constructor_t* fn = __init_array_start; fn != __init_array_end; ++fn)
        (*fn)();
}

// =============================================================================
// kmain
// =============================================================================
extern "C" void kmain(uint32_t /*mb_magic*/, void* mbi_ptr)
{
    call_constructors();

    bool gfx = vbe_init(mbi_ptr);

    if (gfx)
    {
        // Draw the full desktop: wallpaper + icons + taskbar
#ifdef DESKTOP_DATA_AVAILABLE
        draw_desktop(DESKTOP_DATA, DESKTOP_W, DESKTOP_H);
#else
        draw_desktop(nullptr, 0, 0);
#endif
    }
    else
    {
        show_text_boot();
    }

    for (;;)
        asm volatile ("hlt");
}
