import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest  # noqa: E402

import config  # noqa: E402
from bots import Robot  # noqa: E402
from game import World  # noqa: E402
from player import Controls  # noqa: E402

DT = 1.0 / 60


def idle_controls(activity=True):
    return [Controls(activity=activity), Controls(activity=activity)]


@pytest.fixture
def world():
    w = World(seed=123)
    w.spawner.timer = 1e9          # no random spawns unless a test wants them
    return w


@pytest.fixture
def playing(world):
    world.step(DT, [Controls(join_pressed=True), Controls()])
    assert world.mode == "play"
    world.spawner.timer = 1e9
    return world


def place_bot(world, x, y=None, good=False, kind="gear", speed=0.0, direction=1):
    y = config_floor() if y is None else y
    b = Robot(kind, good, x, y, direction)
    b.base_speed = speed
    world.robots.append(b)
    return b


def config_floor():
    import level
    return float(level.FLOOR_Y)


def run(world, seconds, controls=None):
    for _ in range(int(round(seconds / DT))):
        world.step(DT, controls() if callable(controls) else (controls or idle_controls()))
