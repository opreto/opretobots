#!/usr/bin/env bash
# Opreto Bots kiosk launcher.
#  * keeps the game running, restarting it after a crash (with back-off)
#  * exit code 0 (admin Ctrl+Shift+Q, or system shutdown) stops the loop
#  * only one copy can run at a time
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$APP_DIR/logs"
mkdir -p "$LOG_DIR"

exec 9>"${XDG_RUNTIME_DIR:-/tmp}/opretobots.lock"
if ! flock -n 9; then
    echo "$(date '+%F %T') already running - not starting a second copy" >> "$LOG_DIR/launcher.log"
    exit 0
fi

PY="${OPRETOBOTS_PYTHON:-}"
if [ -z "$PY" ]; then
    if [ -x "$APP_DIR/.venv/bin/python" ]; then PY="$APP_DIR/.venv/bin/python"; else PY=python3; fi
fi

# Keep the screen awake on X11 sessions (Wayland: install_pi.sh disables blanking).
if [ -n "${DISPLAY:-}" ] && command -v xset >/dev/null 2>&1; then
    xset s off -dpms s noblank 2>/dev/null || true
fi

# give the desktop a moment to settle on boot
sleep "${OPRETOBOTS_START_DELAY:-3}"

backoff=2
while true; do
    # keep stdout log bounded across long shows
    if [ -f "$LOG_DIR/stdout.log" ] && [ "$(stat -c %s "$LOG_DIR/stdout.log")" -gt 5000000 ]; then
        mv -f "$LOG_DIR/stdout.log" "$LOG_DIR/stdout.log.1"
    fi
    start=$(date +%s)
    "$PY" "$APP_DIR/main.py" "$@" >> "$LOG_DIR/stdout.log" 2>&1
    code=$?
    if [ "$code" -eq 0 ]; then
        echo "$(date '+%F %T') game exited normally" >> "$LOG_DIR/launcher.log"
        exit 0
    fi
    ran=$(( $(date +%s) - start ))
    if [ "$ran" -gt 60 ]; then backoff=2; elif [ "$backoff" -lt 30 ]; then backoff=$(( backoff * 2 )); fi
    echo "$(date '+%F %T') game exited with code $code after ${ran}s - restarting in ${backoff}s" >> "$LOG_DIR/launcher.log"
    sleep "$backoff"
done
