"""Fixed single-screen factory layout (384 x 216 logical pixels).

    y=11  HUD bar
    y=44  T4   [feeder]=========          ========[feeder]
    y=82  T3   ===        ===============            ===
    y=104      (arm platforms, raised position)
    y=122 T2   =================          ================
    y=142      (arm platforms, lowered position)
    y=162 T1   ==============        [AI]       ==============
    y=200 FLOOR [KINOPTYX]===========================[KINOPTYX]

Every tier overlaps the tier above it horizontally and is <=40 px below it,
so the whole map can always be climbed with a normal jump (jump apex ~52 px),
whatever position the robot-arm platforms are in.
"""

from physics import Platform
import config

W = config.LOGICAL_W

FLOOR_Y = 200
T1_Y = 162
T2_Y = 122
T3_Y = 82
T4_Y = 44
HUD_H = 11

# AI Compass block (solid box: stand on top, bump from below)
COMPASS_X1, COMPASS_X2 = 184, 200
COMPASS_TOP, COMPASS_BOTTOM = 164, 178

# Kinoptyx stations: robots walking on the floor toward an edge get captured
STATION_ZONE = 38            # px from the screen edge
STATION_SCAN_OFFSET = 22     # scan position (bot centre) from screen edge

# Feeder mouths
FEEDER_W = 26
FEEDER_SPAWN_INSET = 6       # bot appears this far from the edge, inside the housing


def build_platforms():
    return [
        Platform("floor", 0, W, FLOOR_Y, 0, kind="floor", thickness=16),
        Platform("t1l", 0, 112, T1_Y, -1),
        Platform("t1r", 272, W, T1_Y, +1),
        Platform("t2l", 0, 136, T2_Y, +1),
        Platform("t2r", 248, W, T2_Y, -1),
        Platform("t3l", 0, 32, T3_Y, -1),
        Platform("t3c", 104, 280, T3_Y, +1),
        Platform("t3r", 352, W, T3_Y, +1),
        Platform("t4l", 0, 120, T4_Y, +1),
        Platform("t4r", 264, W, T4_Y, -1),
    ]


def build_compass_platform():
    return Platform("compass", COMPASS_X1, COMPASS_X2, COMPASS_TOP, 0, kind="compass",
                    thickness=COMPASS_BOTTOM - COMPASS_TOP)


# Robot arm definitions: platform width, the two authored positions (x1, y)
# and the floor base position.  Position "A" is the default configuration.
ARM_PLATFORM_W = 40
ARMS = [
    dict(name="arm_l", base_x=98, pos_a=(118, 142), pos_b=(146, 104), elbow_side=-1),
    dict(name="arm_r", base_x=286, pos_a=(226, 142), pos_b=(198, 104), elbow_side=+1),
]

# Attract-mode information panel (x1, y1, x2, y2); demo stomps avoid bots behind it.
ATTRACT_PANEL = (96, 46, 288, 124)
