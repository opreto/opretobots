"""Player activation, inactivity timeouts, reset to attract mode."""
import config
from conftest import DT, place_bot, run
from player import Controls


def ctl(p1=False, p2=False, join1=False, join2=False):
    return [Controls(activity=p1, join_pressed=join1), Controls(activity=p2, join_pressed=join2)]


def test_both_slots_start_inactive(world):
    assert world.mode == "attract"
    assert not any(p.active for p in world.players)


def test_either_player_can_join_first(world):
    world.step(DT, ctl(join2=True))
    assert world.players[1].active and not world.players[0].active
    assert world.mode == "play"


def test_second_player_joins_without_reset(playing):
    playing.score = 700
    playing.step(DT, ctl(p1=True, join2=True))
    assert playing.players[1].active and playing.score == 700


def test_join_press_does_not_also_jump(world):
    world.step(DT, [Controls(join_pressed=True, jump_pressed=True, jump_held=True), Controls()])
    world.step(DT, [Controls(activity=True), Controls()])
    assert world.players[0].ground is not None


def test_independent_idle_timers_and_score_persists(playing):
    playing.step(DT, ctl(p1=True, join2=True))
    playing.score = 1200
    # P1 keeps playing, P2 goes idle
    run(playing, config.PLAYER_IDLE_TIMEOUT + 0.5, lambda: ctl(p1=True))
    assert playing.players[0].active
    assert not playing.players[1].active
    assert playing.mode == "play" and playing.score == 1200


def test_held_direction_counts_as_activity(playing):
    run(playing, config.PLAYER_IDLE_TIMEOUT + 1, lambda: [Controls(dir=1, activity=True), Controls()])
    assert playing.players[0].active


def test_all_inactive_resets_to_attract(playing):
    playing.score = 900
    playing.compass.charges = 0
    playing.play_time = 500
    place_bot(playing, 150, good=False)
    playing.arms[0].platform.move_to(10, 10)
    run(playing, config.PLAYER_IDLE_TIMEOUT + 0.5, lambda: ctl())
    assert playing.mode == "attract"
    assert playing.score == 0
    assert playing.compass.charges == config.COMPASS_START_CHARGES
    assert playing.play_time == 0
    assert playing.arms[0].platform.x1 == playing.arms[0].pos_a[0]
    assert all(b.age < 1 for b in playing.robots)   # old bots removed


def test_rejoin_after_timeout(playing):
    run(playing, config.PLAYER_IDLE_TIMEOUT + 0.5, lambda: ctl())
    assert playing.mode == "attract"
    playing.step(DT, ctl(join1=True))
    assert playing.players[0].active and playing.mode == "play"


def test_disconnect_deactivates_only_that_player(playing):
    playing.step(DT, ctl(p1=True, join2=True))
    playing.score = 300
    playing.step(DT, ctl(p1=True, p2=True), disconnected=[1])
    assert playing.players[0].active and not playing.players[1].active
    assert playing.score == 300 and playing.mode == "play"


def test_start_from_attract_clears_demo_bots(world):
    world.spawner.timer = 0
    run(world, 5, lambda: ctl())
    assert world.robots
    world.step(DT, ctl(join1=True))
    assert world.score == 0 and len(world.robots) <= 1
