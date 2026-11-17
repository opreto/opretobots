"""Conveyor feeder mouths (upper corners) and the robot spawner."""

import config
import level
from bots import KIND_NAMES, Robot

W = config.LOGICAL_W


class Feeder:
    def __init__(self, side):
        self.side = side            # -1 left corner, +1 right corner
        self.open = 0.0             # shutter animation timer
        self.anim = 0.0

    def spawn_point(self):
        if self.side < 0:
            return float(level.FEEDER_SPAWN_INSET), float(level.T4_Y), +1
        return float(W - level.FEEDER_SPAWN_INSET), float(level.T4_Y), -1

    def update(self, dt):
        self.anim += dt
        if self.open > 0:
            self.open = max(0.0, self.open - dt)


class Spawner:
    def __init__(self, rng):
        self.rng = rng
        self.reset()

    def reset(self):
        self.timer = 1.0
        self.last_side = None

    @staticmethod
    def difficulty_level(play_time):
        return int(play_time // config.DIFFICULTY_STEP_TIME)

    @staticmethod
    def interval(active_players, play_time):
        base = config.DUO_SPAWN_INTERVAL if active_players >= 2 else config.SOLO_SPAWN_INTERVAL
        lvl = Spawner.difficulty_level(play_time)
        return max(config.MIN_SPAWN_INTERVAL, base * (config.DIFFICULTY_SPAWN_MULT ** lvl))

    @staticmethod
    def speed_mult(play_time):
        lvl = Spawner.difficulty_level(play_time)
        return min(config.DIFFICULTY_MAX_SPEED_MULT, 1.0 + config.DIFFICULTY_SPEED_STEP * lvl)

    @staticmethod
    def bad_probability(play_time):
        lvl = Spawner.difficulty_level(play_time)
        return min(config.MAX_BAD_PROBABILITY,
                   config.INITIAL_BAD_PROBABILITY + config.DIFFICULTY_BAD_STEP * lvl)

    def make_robot(self, feeder, bad_probability):
        x, y, direction = feeder.spawn_point()
        kind = self.rng.choice(KIND_NAMES)
        good = self.rng.random() >= bad_probability
        bot = Robot(kind, good, x, y, direction)
        bot.ground = None
        feeder.open = 0.7
        return bot

    def update(self, dt, interval, can_spawn, feeders, bad_probability):
        """Returns a new Robot or None."""
        self.timer -= dt
        if self.timer > 0 or not can_spawn:
            if self.timer < 0:
                self.timer = 0.0
            return None
        self.timer = interval * self.rng.uniform(0.85, 1.15)
        # alternate sides most of the time so both feeders look busy
        if self.last_side is None or self.rng.random() < 0.25:
            feeder = self.rng.choice(feeders)
        else:
            feeder = feeders[0] if self.last_side > 0 else feeders[1]
        self.last_side = feeder.side
        return self.make_robot(feeder, bad_probability)
