#pragma once
// =============================================================================
// vbe.h - VBE / VESA Linear Framebuffer Driver
// Reads the framebuffer address/dimensions from the Multiboot2 info struct
// and provides pixel-level drawing primitives.
// =============================================================================

#include <stdint.h>
#include <stddef.h>

// -----------------------------------------------------------------------------
// Multiboot2 tag structures (minimal subset we need)
// -----------------------------------------------------------------------------

// Generic tag header
struct MB2Tag
{
    uint32_t type;
    uint32_t size;
} __attribute__((packed));

// Tag type 8: framebuffer info
struct MB2TagFramebuffer
{
    uint32_t type;          // = 8
    uint32_t size;
    uint64_t framebuffer_addr;
    uint32_t framebuffer_pitch;     // bytes per row
    uint32_t framebuffer_width;     // pixels
    uint32_t framebuffer_height;    // pixels
    uint8_t  framebuffer_bpp;       // bits per pixel
    uint8_t  framebuffer_type;      // 1 = indexed, 2 = direct RGB
    uint16_t reserved;
    // Followed by colour info — we skip it
} __attribute__((packed));

// Multiboot2 info header
struct MB2InfoHeader
{
    uint32_t total_size;
    uint32_t reserved;
} __attribute__((packed));

// -----------------------------------------------------------------------------
// Framebuffer state (set by vbe_init)
// -----------------------------------------------------------------------------
struct FramebufferInfo
{
    uint8_t*  base;         // linear address of framebuffer
    uint32_t  width;
    uint32_t  height;
    uint32_t  pitch;        // bytes per scanline
    uint8_t   bpp;          // bits per pixel (expect 32)
    bool      valid;
};

extern FramebufferInfo g_fb;

// -----------------------------------------------------------------------------
// Public API
// -----------------------------------------------------------------------------

// Call once with the Multiboot2 info pointer
bool vbe_init(void* mbi_ptr);

// Pack R/G/B into a 32-bit pixel (assumes 32 bpp, 0x00RRGGBB)
inline uint32_t rgb(uint8_t r, uint8_t g, uint8_t b)
{
    return ((uint32_t)r << 16) | ((uint32_t)g << 8) | (uint32_t)b;
}

// Draw a single pixel
void vbe_put_pixel(int x, int y, uint32_t color);

// Fill a rectangle
void vbe_fill_rect(int x, int y, int w, int h, uint32_t color);

// Clear the entire screen with one colour
void vbe_clear(uint32_t color);

// Draw a 1-bit (monochrome) bitmap glyph — useful for font rendering
// bitmap: array of bytes, each bit = one pixel (MSB first)
// scale: pixel magnification factor
void vbe_draw_bitmap(int x, int y, int w, int h,
                     const uint8_t* bitmap, uint32_t fg, uint32_t bg,
                     int scale = 1);

// Draw a raw RGBA/RGB pixel array (e.g. logo converted with xxd/bin2c)
// img_w * img_h * 4 bytes (RGBA order, A is ignored)
void vbe_draw_image_rgba(int x, int y, int img_w, int img_h,
                         const uint8_t* data);
