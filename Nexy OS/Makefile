# =============================================================================
# Makefile - Nexy OS Build System
#
# Requirements (install via your Linux/WSL package manager):
#   sudo apt install nasm xorriso grub-pc-bin grub-common
#   sudo apt install gcc-multilib g++-multilib
#
# Cross-compiler (preferred):
#   i686-elf-gcc / i686-elf-g++ / i686-elf-ld
#   Build guide: https://wiki.osdev.org/GCC_Cross-Compiler
#   OR use the native gcc with -m32 flags (no ELF cross needed on Linux)
#
# Usage:
#   make          - build nexy.iso
#   make run      - build + launch in QEMU (quick test)
#   make clean    - remove build artifacts
# =============================================================================

# ---------------------------------------------------------------------------
# Toolchain configuration
# ---------------------------------------------------------------------------
# If you have the cross-compiler, set PREFIX to its bin directory:
#   PREFIX := /usr/local/cross/bin/i686-elf-
# Otherwise use the native compiler with -m32 (Linux only):
PREFIX  :=

# Uncomment ONE of these blocks depending on your setup:

# --- Option A: i686-elf cross-compiler (recommended) ---
# CC  := $(PREFIX)gcc
# CXX := $(PREFIX)g++
# AS  := nasm
# LD  := $(PREFIX)ld

# --- Option B: Native Linux gcc -m32 ---
CC  := gcc
CXX := g++
AS  := nasm
LD  := ld

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
# Common flags for both C and C++
COMMON_FLAGS := \
    -m32                    \
    -ffreestanding          \
    -fno-exceptions         \
    -fno-rtti               \
    -fno-stack-protector    \
    -fno-pie                \
    -fno-PIC                \
    -mno-red-zone           \
    -O2                     \
    -Wall                   \
    -Wextra                 \
    -Ikernel

CFLAGS   := $(COMMON_FLAGS) -std=c11
CXXFLAGS := $(COMMON_FLAGS) -std=c++17

ASFLAGS  := -f elf32

LDFLAGS  := \
    -m elf_i386             \
    -T linker.ld            \
    --no-dynamic-linker     \
    -static                 \
    -nostdlib

# ---------------------------------------------------------------------------
# Directories & Output
# ---------------------------------------------------------------------------
BUILD_DIR  := build
ISO_DIR    := $(BUILD_DIR)/iso
KERNEL_ELF := $(BUILD_DIR)/nexy.elf
ISO_FILE   := $(BUILD_DIR)/nexy.iso

# ---------------------------------------------------------------------------
# Source files → Object files
# ---------------------------------------------------------------------------
BOOT_SRCS  := boot/boot.asm
KERNEL_SRCS := \
    kernel/kmain.cpp    \
    kernel/vga.cpp      \
    kernel/vbe.cpp

BOOT_OBJS   := $(BUILD_DIR)/boot.o
KERNEL_OBJS := $(patsubst kernel/%.cpp,$(BUILD_DIR)/%.o,$(KERNEL_SRCS))

ALL_OBJS := $(BOOT_OBJS) $(KERNEL_OBJS)

# ---------------------------------------------------------------------------
# Default target: build the ISO
# ---------------------------------------------------------------------------
.PHONY: all
all: $(ISO_FILE)

# ---------------------------------------------------------------------------
# Assemble boot.asm
# ---------------------------------------------------------------------------
$(BUILD_DIR)/boot.o: boot/boot.asm | $(BUILD_DIR)
	@echo "[ASM]  $<"
	$(AS) $(ASFLAGS) $< -o $@

# ---------------------------------------------------------------------------
# Compile C++ kernel sources
# ---------------------------------------------------------------------------
$(BUILD_DIR)/%.o: kernel/%.cpp | $(BUILD_DIR)
	@echo "[CXX]  $<"
	$(CXX) $(CXXFLAGS) -c $< -o $@

# ---------------------------------------------------------------------------
# Link the kernel ELF
# ---------------------------------------------------------------------------
$(KERNEL_ELF): $(ALL_OBJS) linker.ld
	@echo "[LD]   $(KERNEL_ELF)"
	$(LD) $(LDFLAGS) $(ALL_OBJS) -o $(KERNEL_ELF)
	@echo "[INFO] Kernel size:"
	@size $(KERNEL_ELF)

# ---------------------------------------------------------------------------
# Build the bootable ISO
# ---------------------------------------------------------------------------
$(ISO_FILE): $(KERNEL_ELF) grub/grub.cfg
	@echo "[ISO]  Creating directory tree..."
	mkdir -p $(ISO_DIR)/boot/grub

	@echo "[ISO]  Copying kernel ELF..."
	cp $(KERNEL_ELF) $(ISO_DIR)/boot/nexy.elf

	@echo "[ISO]  Copying GRUB config..."
	cp grub/grub.cfg $(ISO_DIR)/boot/grub/grub.cfg

	@echo "[ISO]  Running grub-mkrescue..."
	grub-mkrescue -o $(ISO_FILE) $(ISO_DIR) \
	    --locales="" --fonts="" --themes=""  \
	    2>&1 | grep -v "^$$"

	@echo ""
	@echo "============================================"
	@echo "  Build successful!"
	@echo "  ISO: $(ISO_FILE)"
	@echo "============================================"

# ---------------------------------------------------------------------------
# Create build directory
# ---------------------------------------------------------------------------
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# ---------------------------------------------------------------------------
# Run in QEMU (fast iteration — no VirtualBox needed for testing)
# ---------------------------------------------------------------------------
.PHONY: run
run: $(ISO_FILE)
	@echo "[QEMU] Launching Nexy OS..."
	qemu-system-i386                    \
	    -cdrom $(ISO_FILE)              \
	    -m 128M                         \
	    -vga std                        \
	    -display sdl                    \
	    -no-reboot                      \
	    -serial stdio

# ---------------------------------------------------------------------------
# Clean build artifacts
# ---------------------------------------------------------------------------
.PHONY: clean
clean:
	@echo "[CLEAN] Removing build directory..."
	rm -rf $(BUILD_DIR)
	@echo "[CLEAN] Done."

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
.PHONY: help
help:
	@echo ""
	@echo "Nexy OS Build System"
	@echo "--------------------"
	@echo "  make         - Build nexy.iso"
	@echo "  make run     - Build + run in QEMU"
	@echo "  make clean   - Remove build artifacts"
	@echo ""
	@echo "Required tools:"
	@echo "  nasm          (assembler)"
	@echo "  gcc/g++ -m32  (or i686-elf cross-compiler)"
	@echo "  ld -m elf_i386"
	@echo "  grub-mkrescue (from grub-pc-bin)"
	@echo "  xorriso       (ISO builder)"
	@echo ""
