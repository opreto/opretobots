# Opreto Bots

A single-screen, two-player co-op arcade platformer for an unattended
tradeshow kiosk. Two hard-hat mechanics work inside a chaotic robot factory.
Jump on the **bad** (red, angry) robots to turn them **good** (green, happy).
Good robots that reach the **Kinoptyx** inspection cameras score 100 points;
bad robots get rejected. Two huge orange industrial robot arms keep moving the
platforms around. Bump the **AI Compass** block from below to fix every bot on
screen at once.

Built with Python 3 and Pygame 2 for Raspberry Pi 5 (1920×1080, two USB
NES-style controllers). All art, fonts and sounds are original and generated
from code, so there are no asset files to lose and the game runs fully
offline.

---

## Quick start (development)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py --windowed          # 3x window; Esc quits
.venv/bin/python -m pytest -q tests          # automated rule tests
```

Command-line options:

| Option | Effect |
|---|---|
| `--windowed` | Run in a window (software scaling) |
| `--scale N` | Window scale with `--windowed` (default 3) |
| `--software` | Use the software scaler in fullscreen |
| `--no-audio` | Disable sound |
| `--fps` | Show the FPS counter (F2 toggles it at runtime) |
| `--seed N` | Fixed random seed |

### Keyboard (development only)

| | Player 1 | Player 2 |
|---|---|---|
| Move | ← → | A D |
| Jump | Z / X / ↑ | G / H / W |
| Start | 1 / Enter | 2 |

**Admin exit:** Ctrl+Shift+Q (always). Esc quits only in windowed mode.

---

## How to play

| Control | Action |
|---|---|
| D-pad left/right | Move |
| A **or** B | Jump (hold for a higher jump/bounce) |
| Start | Join / rejoin (any button also joins an idle slot) |

* **Land on a robot** to toggle it: BAD → GOOD or GOOD → BAD. You bounce off.
  Toggling never scores by itself.
* **Bad robots hurt from the side.** Touching one stuns you briefly, then you
  blink and are invulnerable for a moment. Good robots are harmless. There
  are no lives and no game over.
* **Kinoptyx inspection** (bottom-left and bottom-right): good robots pass
  and score **+100**. Bad robots are dropped through the reject trapdoor.
* **AI Compass** (bottom centre): jump up into it to turn every bad robot
  good. It has 3 charges and refills after 12 more accepted robots. It does
  not use a charge when there are no bad robots.
* **Robot arms** move their platforms every 10 s (amber lights flash first).
  Ride them to reach other tiers.
* The screen wraps horizontally.

### Kiosk lifecycle

* Both slots start idle and the game shows the animated **attract mode**.
* Press Start (or any button) on either controller to start right away.
  The other player can join at any time without resetting the score.
* After **45 s** without input a player's mechanic vanishes and its slot
  shows `PRESS START` again. A held D-pad direction counts as input. In the
  last 10 s, `STILL THERE?` and a countdown appear above the player.
* When **both** players are idle, the score, AI Compass charges, difficulty,
  robots and arm positions all reset, and attract mode resumes.
* Unplugging a controller removes only that player. Plugging one back in takes
  the free slot.

---

## Project layout

| File | Purpose |
|---|---|
| `main.py` | Entry point: display, fixed-timestep loop, logging, crash handling |
| `config.py` | **All tunable settings** (timings, physics, spawn rates, audio, kiosk) |
| `game.py` | `World`: the full simulation (pure logic, no rendering) |
| `player.py` | Mechanics: movement, coyote time, jump buffering, stun |
| `bots.py` | GearBot / BoltBot / BoxBot, GOOD/BAD state, routing, failsafes |
| `level.py` | Fixed platform layout and key coordinates |
| `physics.py` | One-way platforms, wraparound, landing/support queries |
| `conveyor.py` | Feeder mouths and the spawner/difficulty curve |
| `robot_arm.py` | Industrial arms: schedule, interpolation, 2-link IK for drawing |
| `inspection.py` | Kinoptyx stations: capture, scan, pass/reject |
| `ai_compass.py` | AI Compass charges, recharge, activation |
| `effects.py` | Particles, popups, pulses, banners (capped) |
| `renderer.py` | All pixel-art drawing and HUD at 384×216 |
| `sprites.py` | Original sprites as ASCII pixel grids |
| `font.py` | Original 3×5 and 5×7 bitmap fonts |
| `audio.py` | 8-bit sound effects synthesized at start-up |
| `input_manager.py` | Controllers, hot-plug, slot assignment, mappings |
| `tools/controller_diagnostics.py` | Live controller viewer + mapping wizard |
| `tools/screenshot.py`, `tools/preview_sprites.py` | Headless screenshots / sprite sheet |
| `tests/` | Automated tests for the critical rules |
| `deploy/` | Kiosk launcher, autostart entry, Pi install script |

### Tuning

Edit `config.py`, or leave it alone and create `settings_local.json` next to
it with just the values you want to change:

```json
{ "AUDIO_ENABLED": false, "PLAYER_IDLE_TIMEOUT": 60, "SOLO_SPAWN_INTERVAL": 3.0 }
```

The log lists which overrides were applied at start-up.

---

## Raspberry Pi kiosk deployment

Target: Raspberry Pi 5, Raspberry Pi OS (64-bit, Bookworm) Desktop, 1080p HDMI.

1. Copy this folder to the Pi, e.g. `~/opretobots`.
2. Run the installer as the desktop user (not with sudo):
   ```bash
   cd ~/opretobots
   ./deploy/install_pi.sh
   ```
   It installs `python3-pygame` from apt, adds an XDG autostart entry
   (`~/.config/autostart/opretobots.desktop`) and turns off screen blanking
   with `raspi-config`.
3. Plug in both controllers and check them:
   `python3 tools/controller_diagnostics.py` (see below).
4. Reboot. The game starts fullscreen and runs on its own.

`deploy/run_kiosk.sh` is what autostart launches. It:

* restarts the game after a crash, with back-off. A normal exit (admin
  Ctrl+Shift+Q, or system shutdown) stops it.
* refuses to start a second copy.
* disables X11 screen saver/DPMS when running under X11.
* writes `logs/launcher.log` and `logs/stdout.log` (size-limited).

The game writes `logs/opretobots.log` (rotating, 5×1 MB), including a
heartbeat every 10 minutes with FPS, robot/particle counts, memory and
controller count. This is useful for the 8-hour soak test.

To remove autostart: `./deploy/uninstall_pi.sh`.

**If the game doesn't autostart** on a customised desktop, add
`<path>/deploy/run_kiosk.sh` to your compositor's autostart, e.g.
`~/.config/labwc/autostart` (labwc) or the `[autostart]` section of
`~/.config/wayfire.ini` (Wayfire).

### Display

The game renders at 384×216 and scales by exactly 5× to 1920×1080 with
nearest-neighbour filtering. The default `RENDER_BACKEND = "scaled"` makes
SDL do the upscale on the GPU. If a particular setup shows black bars or
blurring, try `--software` (or `"RENDER_BACKEND": "software"` in
`settings_local.json`).

### Audio

Sounds are synthesized at start-up. If there is no audio device the game
runs silently and logs a warning. Settings: `AUDIO_ENABLED`,
`MASTER_VOLUME`, `ATTRACT_AUDIO` (off by default to keep the booth quiet),
`FOOTSTEP_SOUNDS`. For HDMI audio, select the HDMI output in the Pi's
desktop volume menu.

---

## Controllers

Generic USB NES clones vary a lot, so the game assumes no fixed button
numbers:

* Every button that isn't configured as Select jumps, and any button joins
  an idle slot. A brand-new controller works without setup.
* The D-pad works whether the controller reports it as a hat, an axis, or
  buttons. Axis movement below 0.5 is ignored as noise.
* Controllers are tracked by SDL **instance id**, so two identical
  controllers with the same name still act independently.

### Diagnostics and mapping

```bash
python3 tools/controller_diagnostics.py            # add --fullscreen on the kiosk
```

This shows every connected controller with its live buttons, axes and hats,
and what the game will do with them (`GAME SEES: LEFT JUMP ...`). Press
**M**, then follow the prompts on one controller: A, B, START, SELECT, LEFT,
RIGHT. The profile is saved to `controller_map.json`, keyed by controller
name, and loaded the next time the game starts. Identical controllers share
one profile.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| A player walks by itself | A worn D-pad or an axis resting off-centre. Check in diagnostics; remap, or raise `AXIS_DEADZONE`. |
| A button does nothing | Run diagnostics. If its role is `SELECT`, remap with M. |
| No sound | Check `logs/opretobots.log` for "audio unavailable" and pick the HDMI output in the desktop. |
| Screen goes blank after 10 min | Re-run `sudo raspi-config nonint do_blanking 1` and reboot. |
| Game won't start at boot | Check `logs/launcher.log`. Run `deploy/run_kiosk.sh` from a terminal to see errors. |
| Low FPS | Make sure `RENDER_BACKEND` is `"scaled"`. Press F2 for the FPS counter. |

---

## Tests

`pytest` covers stomp toggling (including once per landing), side contact,
inspection scoring, attract-mode no-score, every AI Compass rule, the player
lifecycle (independent idle timers, reset to attract, rejoin, disconnects),
reachability of every tier, robots always reaching inspection, spawn odds and
the bot cap, arm movement and carrying riders, and a simulated hour of
unattended play with bounded memory. Controller handling is tested with fake
joysticks: identical devices, hot-plug, hats, axis noise and per-device
profiles.

The hardware checks still have to be done on the real Pi with the real
controllers (milestone 5): fullscreen output, autostart, controller
quirks, and the 8-hour soak test.

### Branding assets

The **OPRETO BOTS**, **KINOPTYX**, **AI COMPASS** and **OPRETO** wordmarks are
currently drawn in the game's own pixel font. To use official logos, draw
them in `Renderer._draw_title_sign`, `_draw_station_front` and
`_build_background` in `renderer.py`. Keep the logos small and low-colour so
they suit the 384×216 pixel art.
