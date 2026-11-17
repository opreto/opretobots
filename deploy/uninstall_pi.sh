#!/usr/bin/env bash
# Remove the Opreto Bots autostart entry (game files are left in place).
rm -f "$HOME/.config/autostart/opretobots.desktop"
echo "Autostart removed.  Re-enable screen blanking with: sudo raspi-config nonint do_blanking 0"
