// =============================================================================
// vbe.cpp - VBE / VESA Linear Framebuffer Driver Implementation
// =============================================================================

#include "vbe.h"

// Global framebuffer state
FramebufferInfo g_fb = { nullptr, 0, 0, 0, 0, false };

// -----------------------------------------------------------------------------
// vbe_init: Walk the Multiboot2 tag list and find the framebuffer tag
// -----------------------------------------------------------------------------
bool vbe_init(void* mbi_ptr)
{
    if (!mbi_ptr) return false;

    MB2InfoHeader* hdr = reinterpret_cast<MB2InfoHeader*>(mbi_ptr);
    uint32_t total = hdr->total_size;

    // First tag starts right after the 8-byte header
    uint8_t* ptr = reinterpret_cast<uint8_t*>(mbi_ptr) + 8;
    uint8_t* end = reinterpret_cast<uint8_t*>(mbi_ptr) + total;

    while (ptr < end)
    {
        MB2Tag* tag = reinterpret_cast<MB2Tag*>(ptr);

        if (tag->type == 0)   // End tag
            break;

        if (tag->type == 8)   // Framebuffer tag
        {
            MB2TagFramebuffer* fb = reinterpret_cast<MB2TagFramebuffer*>(tag);

            // Only handle direct-colour (type 2) or unspecified (type 0)
            if (fb->framebuffer_bpp == 32 || fb->framebuffer_bpp == 24)
            {
                g_fb.base   = reinterpret_cast<uint8_t*>(
                                    static_cast<uintptr_t>(fb->framebuffer_addr));
                g_fb.width  = fb->framebuffer_width;
                g_fb.height = fb->framebuffer_height;
                g_fb.pitch  = fb->framebuffer_pitch;
                g_fb.bpp    = fb->framebuffer_bpp;
                g_fb.valid  = true;
                return true;
            }
        }

        // Tags are 8-byte aligned
        uint32_t next = (tag->size + 7) & ~7u;
        ptr += next;
    }

    return false;   // No usable framebuffer tag found
}

// -----------------------------------------------------------------------------
// vbe_put_pixel: Write one 32-bpp pixel
// -----------------------------------------------------------------------------
void vbe_put_pixel(int x, int y, uint32_t color)
{
    if (!g_fb.valid) return;
    if ((unsigned)x >= g_fb.width || (unsigned)y >= g_fb.height) return;

    uint8_t* pixel = g_fb.base + (uint32_t)y * g_fb.pitch + (uint32_t)x * (g_fb.bpp / 8);
    pixel[0] = (uint8_t)(color & 0xFF);          // Blue
    pixel[1] = (uint8_t)((color >> 8)  & 0xFF);  // Green
    pixel[2] = (uint8_t)((color >> 16) & 0xFF);  // Red
    if (g_fb.bpp == 32)
        pixel[3] = 0xFF;                          // Alpha (ignored by hardware)
}

// -----------------------------------------------------------------------------
// vbe_fill_rect
// -----------------------------------------------------------------------------
void vbe_fill_rect(int x, int y, int w, int h, uint32_t color)
{
    for (int row = y; row < y + h; ++row)
        for (int col = x; col < x + w; ++col)
            vbe_put_pixel(col, row, color);
}

// -----------------------------------------------------------------------------
// vbe_clear
// -----------------------------------------------------------------------------
void vbe_clear(uint32_t color)
{
    if (!g_fb.valid) return;
    vbe_fill_rect(0, 0, (int)g_fb.width, (int)g_fb.height, color);
}

// -----------------------------------------------------------------------------
// vbe_draw_bitmap: render a packed 1-bit bitmap (MSB first) with magnification
// Each byte covers 8 horizontal pixels.
// -----------------------------------------------------------------------------
void vbe_draw_bitmap(int x, int y, int w, int h,
                     const uint8_t* bitmap, uint32_t fg, uint32_t bg,
                     int scale)
{
    int bytes_per_row = (w + 7) / 8;

    for (int row = 0; row < h; ++row)
    {
        for (int col = 0; col < w; ++col)
        {
            int byte_idx = row * bytes_per_row + col / 8;
            int bit      = 7 - (col % 8);
            bool set     = (bitmap[byte_idx] >> bit) & 1;
            uint32_t c   = set ? fg : bg;

            for (int sy = 0; sy < scale; ++sy)
                for (int sx = 0; sx < scale; ++sx)
                    vbe_put_pixel(x + col * scale + sx,
                                  y + row * scale + sy, c);
        }
    }
}

// -----------------------------------------------------------------------------
// vbe_draw_image_rgba: blit a raw RGBA image
// data layout: row-major, 4 bytes per pixel: R, G, B, A
// -----------------------------------------------------------------------------
void vbe_draw_image_rgba(int x, int y, int img_w, int img_h,
                         const uint8_t* data)
{
    for (int row = 0; row < img_h; ++row)
    {
        for (int col = 0; col < img_w; ++col)
        {
            const uint8_t* p = data + (row * img_w + col) * 4;
            uint32_t color = ((uint32_t)p[0] << 16) |   // R
                             ((uint32_t)p[1] << 8)  |   // G
                             ((uint32_t)p[2]);           // B
            vbe_put_pixel(x + col, y + row, color);
        }
    }
}
