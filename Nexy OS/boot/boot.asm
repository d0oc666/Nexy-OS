; =============================================================================
; boot.asm - Nexy OS Multiboot2 Header + Entry Point
; Assembled with NASM
; =============================================================================

bits 32

; -----------------------------------------------------------------------------
; Multiboot2 Magic Constants
; -----------------------------------------------------------------------------
MULTIBOOT2_MAGIC        equ 0xE85250D6
MULTIBOOT2_ARCH_I386    equ 0           ; Protected mode i386
MULTIBOOT2_HEADER_LEN   equ multiboot2_header_end - multiboot2_header_start
MULTIBOOT2_CHECKSUM     equ -(MULTIBOOT2_MAGIC + MULTIBOOT2_ARCH_I386 + MULTIBOOT2_HEADER_LEN)

; -----------------------------------------------------------------------------
; Multiboot2 Header (must be 8-byte aligned, within first 32KB of kernel)
; -----------------------------------------------------------------------------
section .multiboot2_header
align 8
multiboot2_header_start:
    dd MULTIBOOT2_MAGIC                 ; Magic number
    dd MULTIBOOT2_ARCH_I386             ; Architecture: 32-bit protected mode
    dd MULTIBOOT2_HEADER_LEN            ; Header length
    dd MULTIBOOT2_CHECKSUM              ; Checksum

    ; --- Framebuffer tag: request VBE/VESA graphics mode ---
    align 8
    dw 5                                ; Tag type: framebuffer
    dw 1                                ; Flags (optional)
    dd 20                               ; Tag size
    dd 1024                             ; Width  (pixels)
    dd 768                              ; Height (pixels)
    dd 32                               ; Depth  (bits per pixel)

    ; --- End tag ---
    align 8
    dw 0                                ; Type: end
    dw 0                                ; Flags
    dd 8                                ; Size
multiboot2_header_end:

; -----------------------------------------------------------------------------
; BSS: Stack
; -----------------------------------------------------------------------------
section .bss
align 16
stack_bottom:
    resb 65536          ; 64 KiB stack
stack_top:

; Multiboot info pointer storage (passed to kmain)
global multiboot_info_ptr
multiboot_info_ptr:
    resd 1

; -----------------------------------------------------------------------------
; Text Section: _start
; -----------------------------------------------------------------------------
section .text
global _start
extern kmain

_start:
    ; GRUB passes:
    ;   eax = 0x36D76289  (Multiboot2 magic)
    ;   ebx = physical address of Multiboot2 info structure

    ; Save multiboot info pointer
    mov [multiboot_info_ptr], ebx

    ; Set up stack
    mov esp, stack_top

    ; Clear EFLAGS
    push 0
    popf

    ; Call C++ kernel entry
    ; void kmain(uint32_t magic, void* mbi)
    push ebx            ; arg2: multiboot info pointer
    push eax            ; arg1: magic number
    call kmain

    ; Should never return — hang forever
.hang:
    cli
    hlt
    jmp .hang
