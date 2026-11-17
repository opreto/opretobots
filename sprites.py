"""Original pixel-art sprites, defined as ASCII grids and built into Surfaces.

Each character maps to a palette entry; '.' is transparent.  Robot body
colours are swapped per GOOD/BAD state, but faces, eyebrows, mouths, horns
and symbols also differ so the state never relies on colour alone.
"""

import pygame

OUTLINE = (20, 16, 28)

# ---------------------------------------------------------------- palettes
BASE = {
    "K": OUTLINE,
    "W": (255, 250, 240),
    "P": (20, 16, 28),
    "M": (60, 16, 30),
    "T": (255, 255, 255),
    "G": (176, 186, 200),
    "g": (100, 108, 124),
    "Y": (255, 236, 80),
    "R": (255, 240, 90),     # glowing eye core (bad)
    "r": (255, 120, 40),     # glowing eye rim (bad)
    "h": (255, 120, 150),    # heart pink (good cheeks)
}

GOOD_PAL = {
    "gear": {"B": (64, 214, 110), "D": (24, 140, 80), "H": (190, 255, 200), "L": (150, 255, 90), "A": (176, 186, 200)},
    "bolt": {"B": (50, 200, 200), "D": (20, 120, 140), "H": (190, 255, 250), "L": (150, 255, 90), "A": (176, 186, 200)},
    "box": {"B": (90, 210, 240), "D": (36, 120, 180), "H": (210, 245, 255), "L": (150, 255, 90), "A": (176, 186, 200)},
}
BAD_PAL = {
    "gear": {"B": (232, 48, 56), "D": (140, 16, 40), "H": (255, 140, 120), "L": (255, 40, 40), "A": (110, 20, 40)},
    "bolt": {"B": (210, 30, 70), "D": (120, 10, 50), "H": (255, 120, 140), "L": (255, 40, 40), "A": (110, 20, 40)},
    "box": {"B": (225, 50, 140), "D": (130, 20, 90), "H": (255, 150, 200), "L": (255, 40, 40), "A": (110, 20, 40)},
}

# ------------------------------------------------------------ little robots
# GearBot: round gear-toothed body, little feet, big expressive eyes.
GEAR_GOOD = [
    "......KK......",
    ".....KLLK.....",
    "......KK......",
    "......KK......",
    "..KK.KAAK.KK..",
    "..KBKKKKKKBK..",
    ".KKBHHBBBBBKK.",
    ".KBWWWBBWWWBK.",
    "KBBWPPBBWPPBBK",
    "KBBWPPBBWPPBBK",
    ".KhWWWBBWWWhK.",
    ".KBBBBBBBBBBK.",
    "KKBBMBBBBMBBKK",
    "..KBBMMMMBBK..",
    "...KDDDDDDK...",
    "....KKKKKK....",
]
GEAR_BAD = [
    "..K........K..",
    "..KAK....KAK..",
    "...KAK..KAK...",
    "....KAKKAK....",
    "..KK.KKKK.KK..",
    "..KBKKBBKKBK..",
    ".KKKKBBBBKKKK.",
    ".KBBBKKBKKBBK.",
    "KBBKKKBBBKKKBK",
    "KBBKRrBBBrRKBK",
    ".KBBKKBBBKKBK.",
    ".KBBBBBBBBBBK.",
    "KKBKKKKKKKKBKK",
    "..KKTKTKTKTK..",
    "...KKDKDKDK...",
    "....KKKKKK....",
]
GEAR_LEGS = [
    ["....KK..KK....", "...KKK..KKK..."],
    [".....KK..KK...", "....KKK.KKK..."],
]

# BoltBot: tall, narrow, two antennae, blocky head, short legs.
BOLT_GOOD = [
    ".KK......KK.",
    "KLLK....KLLK",
    ".KK......KK.",
    "..K......K..",
    ".KKKKKKKKKK.",
    "KBHHBBBBBBBK",
    "KBWWWBBWWWBK",
    "KBWWPBBWWPBK",
    "KBWWPBBWWPBK",
    "KBhBBBBBBhBK",
    "KBBMBBBBMBBK",
    "KBBBMMMMBBBK",
    ".KKKKKKKKKK.",
    "..KDDDDDDK..",
    "..KDDDDDGK..",
    "..KDDDDGDK..",
    "..KDGDGDDK..",
    "..KDDGDDDK..",
    "...KKKKKK...",
]
BOLT_BAD = [
    "K..........K",
    "KAK......KAK",
    ".KAK....KAK.",
    "..KK....KK..",
    ".KKKKKKKKKK.",
    "KBKKBBBBKKBK",
    "KBBBKBBKBBBK",
    "KBKKKBBKKKBK",
    "KBKRrBBrRKBK",
    "KBBKKBBKKBBK",
    "KBBBBBBBBBBK",
    "KBKTKTKTKTBK",
    ".KKKKKKKKKK.",
    "..KDDDDDDK..",
    "..KDLDDLDK..",
    "..KDDLLDDK..",
    "..KDDLLDDK..",
    "..KDLDDLDK..",
    "...KKKKKK...",
]
BOLT_LEGS = [
    ["...KK..KK...", "..KKK..KKK.."],
    ["....KK.KK...", "...KKK.KKK.."],
]

# BoxBot: squat square body, huge face, stubby arms.
BOX_GOOD = [
    "..KKKKKKKKKKKKKK..",
    "..KBHHBBBBBBBLLK..",
    "..KBHBBBBBBBBLLK..",
    "..KBWWWBBBBWWWBK..",
    ".KKBWWPPBBWWPPBKK.",
    "KDKBWWPPBBWWPPBKDK",
    "KDKBhWWWBBWWWhBKDK",
    ".KKBBBBBBBBBBBBKK.",
    "..KBBMBBBBBBMBBK..",
    "..KBBBMMMMMMBBBK..",
    "..KDDDDDDDDDDDDK..",
    "...KKKKKKKKKKKK...",
]
BOX_BAD = [
    "..KKKKKKKKKKKKKK..",
    "..KBKKBBBBBBKKLK..",
    "..KBBBKKBBKKBBBK..",
    "..KBBBBBKKBBBBBK..",
    ".KKBKKKKBBKKKKBKK.",
    "KDKBKRrKBBKrRKBKDK",
    "KDKBBKKBBBBKKBBKDK",
    ".KKBBBBBBBBBBBBKK.",
    "..KBKKKKKKKKKKBK..",
    "..KBKTKTKTKTKKBK..",
    "..KDDDDDDDDDDDDK..",
    "...KKKKKKKKKKKK...",
]
BOX_LEGS = [
    ["....KK....KK......", "...KKKK..KKKK....."],
    ["......KK....KK....", ".....KKKK..KKKK..."],
]

ROBOT_ART = {
    "gear": (GEAR_GOOD, GEAR_BAD, GEAR_LEGS),
    "bolt": (BOLT_GOOD, BOLT_BAD, BOLT_LEGS),
    "box": (BOX_GOOD, BOX_BAD, BOX_LEGS),
}

# ------------------------------------------------------------------ mechanics
MECH_PAL_COMMON = {
    "K": OUTLINE,
    "O": (255, 150, 30),     # hard hat
    "o": (190, 90, 10),
    "H": (255, 220, 120),    # hat highlight
    "S": (250, 200, 160),    # skin
    "s": (210, 140, 100),
    "m": (90, 50, 30),       # moustache
    "Y": (238, 238, 230),    # shirt
    "y": (170, 170, 170),
    "b": (90, 60, 40),       # boots
    "G": (210, 216, 228),    # wrench
    "g": (120, 128, 140),
    "W": (255, 255, 255),
}
MECH_PAL = [
    {"C": (50, 100, 240), "c": (24, 50, 150)},     # P1 blue overalls
    {"C": (225, 50, 50), "c": (130, 20, 30)},      # P2 red overalls
]

MECH_IDLE = [
    "....KKKKK.......",
    "...KOOHOOK......",
    "..KOOOHOOOK.....",
    "..KOOOOOOOOKK...",
    ".KKKKKKKKKKKKK..",
    "...KSSSSKSK.....",
    "...KSSSSKSSK....",
    "...KSSmmmmK.....",
    "....KSSSSK...GG.",
    "...KCYCCYCK..KG.",
    "..KYKCCCCKSK.G..",
    "..KSKCCCCKSKG...",
    "...KCCCCCCKK....",
    "...KCCKKCCK.....",
    "..KbbbK.KbbbK...",
    "..KKKKK.KKKKK...",
]
MECH_WALK1 = [
    "....KKKKK.......",
    "...KOOHOOK......",
    "..KOOOHOOOK.....",
    "..KOOOOOOOOKK...",
    ".KKKKKKKKKKKKK..",
    "...KSSSSKSK.....",
    "...KSSSSKSSK....",
    "...KSSmmmmK.....",
    "....KSSSSK...GG.",
    "...KCYCCYCK..KG.",
    "..KYKCCCCKSK.G..",
    "..KSKCCCCKSKG...",
    "...KCCCCCCKK....",
    "..KCCKKKCCCK....",
    ".KbbbK..KbbbK...",
    ".KKKK....KKKK...",
]
MECH_WALK2 = [
    "................",
    "....KKKKK.......",
    "...KOOHOOK......",
    "..KOOOHOOOK.....",
    "..KOOOOOOOOKK...",
    ".KKKKKKKKKKKKK..",
    "...KSSSSKSK.....",
    "...KSSSSKSSK.GG.",
    "...KSSmmmmK..KG.",
    "...KCYCCYCK..G..",
    "..KYKCCCCKSKG...",
    "..KSKCCCCKSK....",
    "...KCCCCCCK.....",
    "....KCCKCK......",
    "...KbbbKbbK.....",
    "...KKKKKKKK.....",
]
MECH_JUMP = [
    "....KKKKK...GG..",
    "...KOOHOOK..KG..",
    "..KOOOHOOOK.G...",
    "..KOOOOOOOOKKK..",
    ".KKKKKKKKKKKKSK.",
    "...KSSSSKSK.KK..",
    "...KSSSSKSSKCK..",
    "...KSSmmmmKCK...",
    "..KKKSSSSKCK....",
    ".KSYKCYCCYCK....",
    ".KKKCCCCCCK.....",
    "...KCCCCCCK.....",
    "...KCCKKCCCK....",
    "..KbbbK.KCCK....",
    "..KKKK..KbbbK...",
    "........KKKKK...",
]
MECH_SWING = [
    "....KKKKK.......",
    "...KOOHOOK......",
    "..KOOOHOOOK.....",
    "..KOOOOOOOOKK...",
    ".KKKKKKKKKKKKK..",
    "...KSSSSKSK.....",
    "...KSSSSKSSK....",
    "...KSSmmmmK.....",
    "....KSSSSK......",
    "...KCYCCYCKKKK..",
    "..KYKCCCCKSSKGGG",
    "..KSKCCCCKKKKGKG",
    "...KCCCCCCK..G.G",
    "...KCCKKCCCK....",
    "..KbbbK.KbbbK...",
    "..KKKKK.KKKKK...",
]
MECH_STUN = [
    "................",
    "....KKKKK.......",
    "...KOOHOOK......",
    "..KOOOHOOOK.....",
    "..KOOOOOOOOKK...",
    ".KKKKKKKKKKKKK..",
    "...KSSSSKKK.....",
    "...KSSKSSKSK....",
    "...KSSmmmmK.....",
    "..KSKSSSSKSK....",
    "..KYKCYCYCYK....",
    "...KCCCCCCK.....",
    "...KCCCCCCK.GG..",
    "...KCCKKCCK.KG..",
    "..KbbbK.KbbbG...",
    "..KKKKK.KKKKK...",
]
MECH_FRAMES = {
    "idle": MECH_IDLE, "walk1": MECH_WALK1, "walk2": MECH_WALK2,
    "jump": MECH_JUMP, "swing": MECH_SWING, "stun": MECH_STUN,
}

# --------------------------------------------------------------- misc icons
COMPASS_ICON = [
    "..KKKKK..",
    ".KCCWCCK.",
    "KCCCWCCCK",
    "KCCCWCCCK",
    "KWWWYWWWK",
    "KCCCRCCCK",
    "KCCCRCCCK",
    ".KCCRCCK.",
    "..KKKKK..",
]
COMPASS_ICON_PAL = {"K": OUTLINE, "C": (40, 150, 230), "W": (255, 255, 255), "R": (255, 80, 80), "Y": (255, 236, 80)}
COMPASS_ICON_EMPTY_PAL = {"K": OUTLINE, "C": (50, 60, 80), "W": (90, 100, 120), "R": (90, 100, 120), "Y": (90, 100, 120)}

HEART = [
    ".K.K.",
    "KhKhK",
    "KhhhK",
    ".KhK.",
    "..K..",
]
STAR = [
    "..Y..",
    ".YWY.",
    "YWWWY",
    ".YWY.",
    "..Y..",
]


def build(grid, palette):
    h = len(grid)
    w = max(len(r) for r in grid)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            col = palette.get(ch)
            if col is None:
                col = BASE.get(ch, (255, 0, 255))
            surf.set_at((x, y), col)
    return surf


def silhouette(surf, color=(255, 255, 255)):
    """Copy of ``surf`` with every opaque pixel set to ``color``."""
    out = surf.copy()
    w, h = out.get_size()
    for y in range(h):
        for x in range(w):
            if out.get_at((x, y)).a:
                out.set_at((x, y), color)
    return out


class SpriteBank:
    """Builds and caches every sprite once at start-up."""

    def __init__(self):
        self.robots = {}     # (kind, good, frame, facing) -> Surface
        self.robot_flash = {}
        for kind, (good_g, bad_g, legs) in ROBOT_ART.items():
            for good in (True, False):
                pal = dict(BASE)
                pal.update((GOOD_PAL if good else BAD_PAL)[kind])
                body = good_g if good else bad_g
                for f, leg_rows in enumerate(legs):
                    surf = build(body + leg_rows, pal)
                    flipped = pygame.transform.flip(surf, True, False)
                    self.robots[(kind, good, f, 1)] = surf
                    self.robots[(kind, good, f, -1)] = flipped
                    if f == 0:
                        self.robot_flash[kind] = silhouette(surf)
        self.mechs = {}      # (slot, frame, facing) -> Surface
        self.mech_white = {}
        for slot in (0, 1):
            pal = dict(MECH_PAL_COMMON)
            pal.update(MECH_PAL[slot])
            for name, grid in MECH_FRAMES.items():
                surf = build(grid, pal)
                self.mechs[(slot, name, 1)] = surf
                self.mechs[(slot, name, -1)] = pygame.transform.flip(surf, True, False)
            self.mech_white[slot] = silhouette(self.mechs[(slot, "idle", 1)], (200, 230, 255))
        self.compass_icon = build(COMPASS_ICON, COMPASS_ICON_PAL)
        self.compass_icon_empty = build(COMPASS_ICON, COMPASS_ICON_EMPTY_PAL)
        self.heart = build(HEART, BASE)
        self.star = build(STAR, BASE)

    def robot(self, kind, good, frame, facing):
        return self.robots[(kind, good, frame % 2, 1 if facing >= 0 else -1)]

    def mech(self, slot, frame, facing):
        return self.mechs[(slot, frame, 1 if facing >= 0 else -1)]
