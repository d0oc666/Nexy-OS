#pragma once
// =============================================================================
// vga.h - VGA Text Mode 80x25 Driver
// =============================================================================

#include <stdint.h>
#include <stddef.h>

// VGA text buffer lives at physical address 0xB8000
#define VGA_TEXT_BUFFER  ((volatile uint16_t*)0xB8000)
#define VGA_WIDTH        80
#define VGA_HEIGHT       25

// VGA colour attribute nibbles
enum VGAColor : uint8_t
{
    VGA_BLACK         = 0,
    VGA_BLUE          = 1,
    VGA_GREEN         = 2,
    VGA_CYAN          = 3,
    VGA_RED           = 4,
    VGA_MAGENTA       = 5,
    VGA_BROWN         = 6,
    VGA_LIGHT_GREY    = 7,
    VGA_DARK_GREY     = 8,
    VGA_LIGHT_BLUE    = 9,
    VGA_LIGHT_GREEN   = 10,
    VGA_LIGHT_CYAN    = 11,
    VGA_LIGHT_RED     = 12,
    VGA_LIGHT_MAGENTA = 13,
    VGA_LIGHT_BROWN   = 14,   // Yellow
    VGA_WHITE         = 15,
};

// Pack fg/bg colour into one byte
inline uint8_t vga_color(VGAColor fg, VGAColor bg)
{
    return (uint8_t)(fg | ((uint8_t)bg << 4));
}

// Pack character + colour into a VGA cell word
inline uint16_t vga_entry(char c, uint8_t color)
{
    return (uint16_t)c | ((uint16_t)color << 8);
}

// ---- Public API ------------------------------------------------------------
void vga_init();
void vga_clear(VGAColor bg = VGA_BLACK);
void vga_setcolor(uint8_t color);
void vga_putchar(char c);
void vga_puts(const char* str);
void vga_puts_at(int col, int row, const char* str, uint8_t color);
void vga_set_cursor(int col, int row);
