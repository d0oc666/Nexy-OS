#!/usr/bin/env bash
# =============================================================================
# build.sh - One-shot build script for Nexy OS (run inside WSL or Linux)
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
cd "$ROOT"

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

# ---------------------------------------------------------------------------
# Check required tools
# ---------------------------------------------------------------------------
info "Checking required tools..."

check_tool() {
    command -v "$1" &>/dev/null || fail "'$1' not found. Install with: $2"
}

check_tool nasm       "sudo apt install nasm"
check_tool g++        "sudo apt install gcc g++ gcc-multilib g++-multilib"
check_tool ld         "sudo apt install binutils"
check_tool grub-mkrescue "sudo apt install grub-pc-bin grub-common"
check_tool xorriso    "sudo apt install xorriso"

ok "All tools found."

# ---------------------------------------------------------------------------
# Optional: convert Logo.png → kernel/logo.h
# ---------------------------------------------------------------------------
if [ -f "Logo.png" ]; then
    if command -v python3 &>/dev/null && python3 -c "import PIL" &>/dev/null 2>&1; then
        info "Converting Logo.png → kernel/logo.h ..."
        python3 tools/img2c.py Logo.png kernel/logo.h 200 60
        ok "Logo converted."
    else
        warn "Python3 + Pillow not available — using built-in placeholder logo."
        warn "Install with: pip3 install pillow"
    fi
fi

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
info "Building Nexy OS..."
make clean
make -j"$(nproc)"

ok "Build complete → build/nexy.iso"

# ---------------------------------------------------------------------------
# Offer to launch in QEMU
# ---------------------------------------------------------------------------
if command -v qemu-system-i386 &>/dev/null; then
    echo ""
    read -rp "Launch in QEMU now? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        make run
    fi
else
    warn "QEMU not installed. Install with: sudo apt install qemu-system-x86"
    info "To test: load build/nexy.iso in VirtualBox."
fi
