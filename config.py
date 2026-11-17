"""Opreto Bots - central configuration.

Every gameplay timing, physics value and kiosk setting lives here so the game
can be tuned during playtesting without touching game code.

Values can be overridden without editing this file by creating
``settings_local.json`` next to it (or pointing the OPRETOBOTS_CONFIG
environment variable at a JSON file).  Keys are the UPPERCASE names below, e.g.

    {"AUDIO_ENABLED": false, "PLAYER_IDLE_TIMEOUT": 60}
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# Display
# --------------------------------------------------------------------------
DISPLAY_W, DISPLAY_H = 1920, 1080
LOGICAL_W, LOGICAL_H = 384, 216
FULLSCREEN = True
# "scaled": SDL renderer does the 5x nearest-neighbour upscale on the GPU
#           (fastest on Raspberry Pi).
# "software": pygame.transform.scale into a 1920x1080 surface each frame.
RENDER_BACKEND = "scaled"
VSYNC = True
TARGET_FPS = 60
WINDOW_SCALE = 3            # used with --windowed
SHOW_FPS = False            # F2 toggles at runtime

# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------
PHYSICS_HZ = 60
MAX_PHYSICS_STEPS_PER_FRAME = 5

# --------------------------------------------------------------------------
# Player physics (logical pixels / seconds)
# --------------------------------------------------------------------------
PLAYER_W = 10
PLAYER_H = 15
PLAYER_RUN_SPEED = 84.0
PLAYER_GROUND_ACCEL = 900.0
PLAYER_GROUND_DECEL = 1100.0
PLAYER_AIR_ACCEL = 650.0
GRAVITY = 900.0
PLAYER_MAX_FALL = 330.0
PLAYER_JUMP_VELOCITY = 305.0       # apex ~52 px; tiers are 38-40 px apart
PLAYER_JUMP_CUT_VELOCITY = 120.0   # releasing jump early clamps upward speed
PLAYER_STOMP_BOUNCE = 190.0
PLAYER_COYOTE_TIME = 0.10
PLAYER_JUMP_BUFFER = 0.13
PLAYER_STUN_TIME = 0.55
PLAYER_KNOCKBACK_X = 95.0
PLAYER_KNOCKBACK_Y = 130.0
PLAYER_INVULN_TIME = 1.6
PLAYER_STOMP_TOLERANCE = 5.0       # px of overlap still treated as "from above"
PLAYER_SPAWN = [(56.0, 200.0), (328.0, 200.0)]

# --------------------------------------------------------------------------
# Little robots
# --------------------------------------------------------------------------
BOT_GRAVITY = 620.0
BOT_MAX_FALL = 220.0
BOT_BAD_SPEED_MULT = 1.18
BOT_BELT_SPEED = 7.0               # conveyor push added to bot walking speed
BOT_TOGGLE_COOLDOWN = 0.30         # one landing == one toggle
BOT_FAILSAFE_LIFETIME = 70.0       # after this a bot drops straight to the floor
BOT_HARD_LIFETIME = 120.0          # absolute removal failsafe
BOT_TRANSFORM_TIME = 0.35
BOT_SPARK_CHANCE = 0.9             # sparks per second for bad bots

INITIAL_BAD_PROBABILITY = 0.60
MAX_BAD_PROBABILITY = 0.72
SOLO_SPAWN_INTERVAL = 2.6
DUO_SPAWN_INTERVAL = 2.0
MIN_SPAWN_INTERVAL = 1.3
MAX_ACTIVE_BOTS = 10

DIFFICULTY_STEP_TIME = 45.0
DIFFICULTY_SPAWN_MULT = 0.93       # interval multiplier per difficulty step
DIFFICULTY_SPEED_STEP = 0.05       # +5% bot speed per step
DIFFICULTY_MAX_SPEED_MULT = 1.40
DIFFICULTY_BAD_STEP = 0.02

# --------------------------------------------------------------------------
# Kinoptyx inspection
# --------------------------------------------------------------------------
INSPECTION_SCAN_TIME = 0.65
INSPECTION_RESULT_HOLD = 0.35
SCORE_PER_ACCEPTED = 100

# --------------------------------------------------------------------------
# Industrial robot arms
# --------------------------------------------------------------------------
ARM_CYCLE_TIME = 10.0
ARM_PHASE_OFFSET = 5.0
ARM_WARNING_TIME = 0.75
ARM_MOVE_TIME = 1.25

# --------------------------------------------------------------------------
# AI Compass
# --------------------------------------------------------------------------
COMPASS_START_CHARGES = 3
COMPASS_RECHARGE_INSPECTIONS = 12
COMPASS_COOLDOWN = 0.6

# --------------------------------------------------------------------------
# Players / kiosk lifecycle
# --------------------------------------------------------------------------
PLAYER_IDLE_TIMEOUT = 45.0
JOIN_WITH_ANY_BUTTON = True        # any button (not only Start) joins an idle slot
AXIS_DEADZONE = 0.5

# --------------------------------------------------------------------------
# Attract mode
# --------------------------------------------------------------------------
ATTRACT_SPAWN_INTERVAL = 2.4
ATTRACT_MAX_BOTS = 7
ATTRACT_DEMO_STOMP_INTERVAL = 3.2
ATTRACT_FOOTER = "BUILT WITH CLAUDE CODE BY OPRETO"

# --------------------------------------------------------------------------
# Audio
# --------------------------------------------------------------------------
AUDIO_ENABLED = True
MASTER_VOLUME = 0.55
AUDIO_FREQUENCY = 22050
AUDIO_BUFFER = 512
ATTRACT_AUDIO = False              # keep the booth quiet when nobody plays
FOOTSTEP_SOUNDS = True

# --------------------------------------------------------------------------
# Input / admin
# --------------------------------------------------------------------------
CONTROLLER_MAP_FILE = os.path.join(BASE_DIR, "controller_map.json")
KEYBOARD_PLAYERS = True            # handy for development; harmless on kiosk
# Admin exit: hold Ctrl+Shift and press Q.  (Esc also quits in windowed mode.)

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_MAX_BYTES = 1_000_000
LOG_BACKUPS = 5


def load_overrides(path=None):
    """Apply JSON overrides on top of the defaults above.  Returns list of keys set."""
    path = path or os.environ.get("OPRETOBOTS_CONFIG") or os.path.join(BASE_DIR, "settings_local.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    applied = []
    g = globals()
    for key, value in data.items():
        if key.isupper() and key in g:
            g[key] = value
            applied.append(key)
    return applied
