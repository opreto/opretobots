"""Headless screenshots for visual review:
    python tools/screenshot.py OUT_PREFIX [attract_seconds] [play_seconds]
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))
from game import World  # noqa: E402
from player import Controls  # noqa: E402
from renderer import Renderer  # noqa: E402

prefix = sys.argv[1]
attract_s = float(sys.argv[2]) if len(sys.argv) > 2 else 6
play_s = float(sys.argv[3]) if len(sys.argv) > 3 else 20
w = World(seed=7)
r = Renderer()
dt = 1 / 60


def shot(name):
    surf = r.draw(w)
    pygame.image.save(pygame.transform.scale(surf, (surf.get_width() * 3, surf.get_height() * 3)),
                      "%s_%s.png" % (prefix, name))


for _ in range(int(attract_s * 60)):
    w.step(dt)
shot("attract")
w.step(dt, [Controls(join_pressed=True), Controls(join_pressed=True)])
rng = random.Random(1)
d = [0, 0]
for i in range(int(play_s * 60)):
    cs = []
    for k in range(2):
        if i % 40 == 0:
            d[k] = rng.choice([-1, 0, 1, 1])
        cs.append(Controls(dir=d[k], jump_held=True, jump_pressed=rng.random() < 0.04, activity=True))
    w.step(dt, cs)
shot("play")
w.robots[0].good = False if w.robots else None
for b in w.robots:
    b.good = False
w._compass_hit(w.players[0])
for _ in range(10):
    w.step(dt, [Controls(activity=True), Controls(activity=True)])
shot("compass")
print("ok", w.score, len(w.robots))
