/* =============================================================================
   linker.ld - Nexy OS Linker Script
   Links kernel to physical address 1 MiB (0x100000)
   Produces ELF32 executable for GRUB to load
   ============================================================================= */

OUTPUT_FORMAT("elf32-i386")
OUTPUT_ARCH(i386)
ENTRY(_start)

SECTIONS
{
    /* Load kernel at 1 MiB physical */
    . = 0x100000;

    /* ------------------------------------------------------------------ */
    /* Multiboot2 header MUST be in the first 32 KiB of the binary        */
    /* ------------------------------------------------------------------ */
    .multiboot2_header ALIGN(8) :
    {
        KEEP(*(.multiboot2_header))
    }

    /* ------------------------------------------------------------------ */
    /* Code                                                                */
    /* ------------------------------------------------------------------ */
    .text ALIGN(4096) :
    {
        *(.text)
        *(.text.*)
    }

    /* ------------------------------------------------------------------ */
    /* Read-only data (string literals, vtables, etc.)                    */
    /* ------------------------------------------------------------------ */
    .rodata ALIGN(4096) :
    {
        *(.rodata)
        *(.rodata.*)
    }

    /* ------------------------------------------------------------------ */
    /* Initialized data                                                    */
    /* ------------------------------------------------------------------ */
    .data ALIGN(4096) :
    {
        *(.data)
        *(.data.*)
    }

    /* ------------------------------------------------------------------ */
    /* C++ static constructors / destructors                               */
    /* ------------------------------------------------------------------ */
    .init_array ALIGN(4) :
    {
        __init_array_start = .;
        KEEP(*(SORT(.init_array.*)))
        KEEP(*(.init_array))
        __init_array_end = .;
    }

    .fini_array ALIGN(4) :
    {
        __fini_array_start = .;
        KEEP(*(SORT(.fini_array.*)))
        KEEP(*(.fini_array))
        __fini_array_end = .;
    }

    /* ------------------------------------------------------------------ */
    /* Uninitialized data (zero-filled at startup)                         */
    /* ------------------------------------------------------------------ */
    .bss ALIGN(4096) :
    {
        *(COMMON)
        *(.bss)
        *(.bss.*)
    }

    /* Discard DWARF / debug info not needed in the kernel image */
    /DISCARD/ :
    {
        *(.eh_frame)
        *(.note.GNU-stack)
        *(.comment)
    }
}
