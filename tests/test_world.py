"""Level geometry, robot routing, arms, spawning and long-run stability."""
import random
from collections import Counter

import config
import level
from bots import Robot
from conftest import DT, place_bot, run
from game import World
from player import Controls

JUMP_HEIGHT = config.PLAYER_JUMP_VELOCITY ** 2 / (2 * config.GRAVITY)


def test_every_tier_is_reachable_from_below():
    plats = level.build_platforms()
    tiers = sorted({p.y for p in plats})
    for upper, lower in zip(tiers, tiers[1:]):
        assert lower - upper < JUMP_HEIGHT - 6, (upper, lower)
        ups = [p for p in plats if p.y == upper]
        lows = [p for p in plats if p.y == lower]
        for u in ups:
            assert any(min(u.x2, l.x2) - max(u.x1, l.x1) >= 12 for l in lows), u.name


def test_spawned_bots_reach_inspection():
    w = World(seed=5)
    w.step(DT, [Controls(join_pressed=True), Controls()])
    w.players[0].x = 0  # keep out of the way
    outcomes = Counter()
    seen = set()
    for i in range(int(120 / DT)):
        w.step(DT, [Controls(activity=True), Controls()])
        for b in w.robots:
            if b.state in ("exit", "reject") and b.id not in seen:
                seen.add(b.id)
                outcomes[b.state] += 1
        for b in w.robots:
            assert b.age < config.BOT_FAILSAFE_LIFETIME + 15, "bot stuck"
    assert outcomes["exit"] > 5 and outcomes["reject"] > 5


def test_bad_probability_and_varieties():
    w = World(seed=9)
    rng_bad = 0
    kinds = Counter()
    n = 4000
    for _ in range(n):
        b = w.spawner.make_robot(w.feeders[0], config.INITIAL_BAD_PROBABILITY)
        rng_bad += not b.good
        kinds[b.kind] += 1
    assert abs(rng_bad / n - 0.6) < 0.03
    assert set(kinds) == {"gear", "bolt", "box"}


def test_max_active_bots_cap():
    w = World(seed=2)
    w.step(DT, [Controls(join_pressed=True), Controls()])
    for _ in range(int(60 / DT)):
        w.step(DT, [Controls(activity=True), Controls()])
        assert len(w.alive_robots()) <= config.MAX_ACTIVE_BOTS


def test_arms_move_between_positions_and_carry_riders(playing):
    arm = playing.arms[0]
    pl = arm.platform
    b = place_bot(playing, pl.cx, y=pl.y, good=True)
    b.ground = pl
    p = playing.players[0]
    p.x, p.y, p.ground = pl.cx + 8, pl.y, pl
    run(playing, config.ARM_CYCLE_TIME + 0.2)
    assert (pl.x1, pl.y) == arm.pos_b
    assert b.ground is pl and abs(b.y - pl.y) < 0.01
    assert p.ground is pl and abs(p.y - pl.y) < 0.01
    run(playing, config.ARM_CYCLE_TIME)
    assert (pl.x1, pl.y) == arm.pos_a


def test_second_arm_offset():
    w = World(seed=1)
    run(w, config.ARM_CYCLE_TIME - config.ARM_MOVE_TIME + 0.1, lambda: [Controls(), Controls()])
    assert w.arms[0].state == "move" and w.arms[1].state == "hold"


def test_failsafe_drops_stuck_bot(playing):
    b = place_bot(playing, 60, y=level.T2_Y, good=True)
    b.age = config.BOT_FAILSAFE_LIFETIME + 1
    run(playing, 2.0)
    assert b.ground is playing.floor or b.state != "walk"


def test_long_unattended_run_stays_bounded():
    """Simulated hour of mixed attract/play: no unbounded growth."""
    w = World(seed=11)
    rng = random.Random(4)
    d = 0
    active_for = 0
    for i in range(int(3600 / DT)):
        if i % 600 == 0:
            active_for = rng.choice([0, 0, 900, 3000])
        if i % 20 == 0:
            d = rng.choice([-1, 0, 1])
        on = active_for > 0
        active_for -= 1
        c = Controls(dir=d if on else 0, jump_held=on, jump_pressed=on and rng.random() < 0.05,
                     join_pressed=on and i % 300 == 0, activity=on)
        w.step(DT, [c, Controls()])
        w.drain_events()
        assert len(w.robots) <= config.MAX_ACTIVE_BOTS + 4
        assert len(w.effects.particles) <= 400
    assert w.effects.popups is not None
