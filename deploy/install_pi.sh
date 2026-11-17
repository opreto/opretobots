#!/usr/bin/env bash
# One-time Raspberry Pi kiosk setup for Opreto Bots.
# Run as the desktop user (not root):   ./deploy/install_pi.sh
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Installing Opreto Bots from $APP_DIR"

echo "--> system packages"
sudo apt-get update
sudo apt-get install -y python3-pygame

echo "--> checking pygame"
python3 -c "import pygame; print('pygame', pygame.version.ver)"

echo "--> autostart entry"
mkdir -p "$HOME/.config/autostart"
sed "s#@APP_DIR@#$APP_DIR#g" "$APP_DIR/deploy/opretobots.desktop" > "$HOME/.config/autostart/opretobots.desktop"
chmod +x "$APP_DIR/deploy/run_kiosk.sh" "$APP_DIR/main.py"

echo "--> disabling screen blanking"
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_blanking 1 || echo "   (raspi-config blanking option not available)"
else
    echo "   raspi-config not found - disable screen blanking manually"
fi

mkdir -p "$APP_DIR/logs"
echo
echo "Done.  Reboot to start the kiosk:  sudo reboot"
echo "Test now without rebooting:       $APP_DIR/deploy/run_kiosk.sh"
echo "Admin exit while running:         Ctrl+Shift+Q"
echo "Map controllers:                  python3 $APP_DIR/tools/controller_diagnostics.py"
