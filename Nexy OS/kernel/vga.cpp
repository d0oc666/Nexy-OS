// =============================================================================
// vga.cpp - VGA Text Mode 80x25 Driver Implementation
// =============================================================================

#include "vga.h"

// ---- I/O port helpers (inline assembly) ------------------------------------
static inline void outb(uint16_t port, uint8_t val)
{
    asm volatile ("outb %0, %1" : : "a"(val), "Nd"(port));
}

// ---- Internal state --------------------------------------------------------
static volatile uint16_t* const s_buf   = VGA_TEXT_BUFFER;
static int     s_col   = 0;
static int     s_row   = 0;
static uint8_t s_color = 0;

// ---- Hardware cursor -------------------------------------------------------
void vga_set_cursor(int col, int row)
{
    uint16_t pos = (uint16_t)(row * VGA_WIDTH + col);
    outb(0x3D4, 0x0F);
    outb(0x3D5, (uint8_t)(pos & 0xFF));
    outb(0x3D4, 0x0E);
    outb(0x3D5, (uint8_t)((pos >> 8) & 0xFF));
}

// ---- Scroll up one line ----------------------------------------------------
static void scroll()
{
    // Move every row up by one
    for (int row = 1; row < VGA_HEIGHT; ++row)
        for (int col = 0; col < VGA_WIDTH; ++col)
            s_buf[(row - 1) * VGA_WIDTH + col] = s_buf[row * VGA_WIDTH + col];

    // Blank the last row
    uint16_t blank = vga_entry(' ', s_color);
    for (int col = 0; col < VGA_WIDTH; ++col)
        s_buf[(VGA_HEIGHT - 1) * VGA_WIDTH + col] = blank;

    s_row = VGA_HEIGHT - 1;
}

// ---- Public API ------------------------------------------------------------
void vga_init()
{
    s_color = vga_color(VGA_WHITE, VGA_BLACK);
    vga_clear();
}

void vga_clear(VGAColor bg)
{
    s_color = vga_color(VGA_WHITE, bg);
    uint16_t blank = vga_entry(' ', s_color);
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT; ++i)
        s_buf[i] = blank;
    s_col = 0;
    s_row = 0;
    vga_set_cursor(0, 0);
}

void vga_setcolor(uint8_t color)
{
    s_color = color;
}

void vga_putchar(char c)
{
    if (c == '\n') {
        s_col = 0;
        ++s_row;
        if (s_row >= VGA_HEIGHT) scroll();
        vga_set_cursor(s_col, s_row);
        return;
    }

    if (c == '\r') {
        s_col = 0;
        vga_set_cursor(s_col, s_row);
        return;
    }

    if (c == '\t') {
        // Advance to next 4-column tab stop
        s_col = (s_col + 4) & ~3;
        if (s_col >= VGA_WIDTH) {
            s_col = 0;
            ++s_row;
            if (s_row >= VGA_HEIGHT) scroll();
        }
        vga_set_cursor(s_col, s_row);
        return;
    }

    s_buf[s_row * VGA_WIDTH + s_col] = vga_entry(c, s_color);
    ++s_col;

    if (s_col >= VGA_WIDTH) {
        s_col = 0;
        ++s_row;
        if (s_row >= VGA_HEIGHT) scroll();
    }

    vga_set_cursor(s_col, s_row);
}

void vga_puts(const char* str)
{
    while (*str)
        vga_putchar(*str++);
}

void vga_puts_at(int col, int row, const char* str, uint8_t color)
{
    uint8_t old = s_color;
    s_color = color;
    int c = col;
    while (*str && c < VGA_WIDTH) {
        s_buf[row * VGA_WIDTH + c] = vga_entry(*str, s_color);
        ++str;
        ++c;
    }
    s_color = old;
}
