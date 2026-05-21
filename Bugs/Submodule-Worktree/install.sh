#!/usr/bin/env bash
# Kilo Submodule Worktree Fix — One-Command Installer
# ====================================================
# This script installs the persistent auto-repair timer for Kilo's
# submodule worktree bug. Run it once per machine.
#
# Usage:
#     ./install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Installing Kilo submodule worktree fix..."

# Ensure target directories exist
mkdir -p ~/.local/bin
mkdir -p ~/.config/systemd/user

# Copy repair script
cp "${SCRIPT_DIR}/kilo-fix-submodules.py" ~/.local/bin/
chmod +x ~/.local/bin/kilo-fix-submodules.py
echo "[+] Script installed to ~/.local/bin/kilo-fix-submodules.py"

# Copy systemd units
cp "${SCRIPT_DIR}/systemd/kilo-fix-submodules.service" ~/.config/systemd/user/
cp "${SCRIPT_DIR}/systemd/kilo-fix-submodules.timer"   ~/.config/systemd/user/
echo "[+] Systemd units installed to ~/.config/systemd/user/"

# Reload daemon and enable timer
systemctl --user daemon-reload
systemctl --user enable --now kilo-fix-submodules.timer
echo "[+] Timer enabled and started"

# Run once immediately to clean any existing corruption
echo "[*] Running initial repair..."
~/.local/bin/kilo-fix-submodules.py

# Show status
echo ""
echo "[*] Timer status:"
systemctl --user list-timers kilo-fix-submodules.timer --no-pager

echo ""
echo "[*] Done. The fix will run automatically every 60 seconds."
echo "    To check logs: journalctl --user -u kilo-fix-submodules.service"
