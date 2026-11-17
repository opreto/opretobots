"""Critical rules: bot states, stomping, inspection, scoring and the AI Compass."""
import config
import level
from conftest import DT, idle_controls, place_bot, run
from player import Controls


def drop_player_on(world, bot, height=18):
    p = world.players[0]
    p.x = bot.x
    p.y = bot.top - height
    p.vy = 0.0
    p.vx = 0.0
    p.ground = None
    p.invuln = 0.0
    return p


def test_stomp_bad_turns_good(playing):
    b = place_bot(playing, 150, good=False)
    drop_player_on(playing, b)
    run(playing, 0.4)
    assert b.good
    assert "fix" in playing.drain_events() or b.good


def test_stomp_good_turns_bad(playing):
    b = place_bot(playing, 150, good=True)
    drop_player_on(playing, b)
    run(playing, 0.4)
    assert not b.good


def test_single_landing_toggles_once(playing):
    b = place_bot(playing, 150, good=False)
    p = drop_player_on(playing, b)
    toggles = 0
    last = b.good
    for _ in range(12):           # player stays overlapping/landing for several frames
        playing.step(DT, idle_controls())
        if b.good != last:
            toggles += 1
            last = b.good
    assert toggles == 1
    assert p.vy < 0               # bounced upward


def test_toggle_cooldown_blocks_double_toggle(playing):
    b = place_bot(playing, 150, good=False)
    assert b.toggle()
    assert not b.toggle()
    assert b.good


def test_stomp_does_not_award_points(playing):
    b = place_bot(playing, 150, good=False)
    drop_player_on(playing, b)
    run(playing, 0.4)
    assert b.good and playing.score == 0


def test_side_contact_with_bad_bot_stuns(playing):
    p = playing.players[0]
    p.invuln = 0.0
    run(playing, 0.1)
    b = place_bot(playing, p.x + 4, good=False)
    playing.step(DT, idle_controls())
    assert p.stun > 0 and p.invuln > 0
    assert not b.good             # side contact never toggles


def test_side_contact_with_good_bot_is_harmless(playing):
    p = playing.players[0]
    p.invuln = 0.0
    run(playing, 0.1)
    place_bot(playing, p.x + 4, good=True)
    run(playing, 0.2)
    assert p.stun == 0


def test_hit_from_below_does_not_toggle(playing):
    p = playing.players[0]
    b = place_bot(playing, 150, y=level.T1_Y + 25, good=False)   # floating test bot
    b.state = "inspect"   # keep it still
    p.x, p.y, p.vy, p.ground = 150, b.y + p.h + 2, -200.0, None
    p.invuln = 1.0
    run(playing, 0.15)
    assert not b.good


def test_good_bot_passes_inspection_and_scores(playing):
    b = place_bot(playing, 60, good=True, speed=30, direction=-1)
    run(playing, 3.0)
    assert playing.score == config.SCORE_PER_ACCEPTED
    assert b.state in ("exit", "gone")


def test_bad_bot_is_rejected_without_points(playing):
    b = place_bot(playing, 330, good=False, speed=30, direction=1)
    run(playing, 3.0)
    assert playing.score == 0
    assert b.state in ("reject", "gone")


def test_toggle_during_scan_uses_state_at_decision(playing):
    b = place_bot(playing, 30, good=False, speed=30, direction=-1)
    run(playing, 0.5)
    assert b.state == "inspect"
    b.toggle()
    run(playing, 2.0)
    assert playing.score == config.SCORE_PER_ACCEPTED


def test_attract_mode_never_scores(world):
    place_bot(world, 60, good=True, speed=30, direction=-1)
    run(world, 3.0, lambda: [Controls(), Controls()])
    assert world.mode == "attract" and world.score == 0


# ------------------------------------------------------------------ AI Compass
def hit_compass(world):
    p = world.players[0]
    p.x = world.compass.cx
    p.y = level.FLOOR_Y
    p.ground = world.floor
    world.step(DT, [Controls(jump_pressed=True, jump_held=True, activity=True), Controls()])
    run(world, 0.4)


def test_compass_fixes_all_bad_bots_only(playing):
    bad = [place_bot(playing, x, y=level.T2_Y, good=False) for x in (20, 60, 300)]
    good = place_bot(playing, 100, y=level.T2_Y, good=True)
    hit_compass(playing)
    assert all(b.good for b in bad)
    assert good.good
    assert playing.compass.charges == config.COMPASS_START_CHARGES - 1
    assert playing.score == 0      # no immediate points


def test_compass_no_charge_used_without_bad_bots(playing):
    place_bot(playing, 60, y=level.T2_Y, good=True)
    hit_compass(playing)
    assert playing.compass.charges == config.COMPASS_START_CHARGES


def test_compass_single_activation_per_hit(playing):
    for x in (20, 60):
        place_bot(playing, x, y=level.T2_Y, good=False)
    hit_compass(playing)
    for x in (20, 60):
        place_bot(playing, x, y=level.T3_Y, good=False)
    run(playing, 0.2)     # standing/bumping contact does not refire
    assert playing.compass.charges == config.COMPASS_START_CHARGES - 1


def test_compass_empty_does_nothing(playing):
    playing.compass.charges = 0
    b = place_bot(playing, 20, y=level.T2_Y, good=False)
    hit_compass(playing)
    assert not b.good and playing.compass.charges == 0


def test_compass_recharges_after_12_inspections(playing):
    c = playing.compass
    c.charges = 1
    for i in range(config.COMPASS_RECHARGE_INSPECTIONS - 1):
        assert not c.on_accepted()
    assert c.charges == 1
    assert c.on_accepted()
    assert c.charges == config.COMPASS_START_CHARGES
