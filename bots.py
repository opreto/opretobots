"""Little cartoon robots: GearBot, BoltBot and BoxBot, each GOOD or BAD."""

import config
import level
from physics import find_landing, find_support, wrap_x

W = config.LOGICAL_W

# Hitbox sizes match the sprite bodies (antennae/horns are not part of the hitbox).
KINDS = {
    "gear": dict(speed=34.0, w=12, h=13, label="GEARBOT"),
    "bolt": dict(speed=29.0, w=10, h=16, label="BOLTBOT"),
    "box": dict(speed=25.0, w=14, h=12, label="BOXBOT"),
}
KIND_NAMES = ("gear", "bolt", "box")

_next_id = 1


class Robot:
    def __init__(self, kind, good, x, y, direction, speed_mult=1.0):
        global _next_id
        self.id = _next_id
        _next_id += 1
        spec = KINDS[kind]
        self.kind = kind
        self.good = good
        self.x = float(x)
        self.y = float(y)
        self.dir = direction
        self.vy = 0.0
        self.w = spec["w"]
        self.h = spec["h"]
        self.base_speed = spec["speed"] * speed_mult
        self.ground = None
        self.state = "walk"         # walk | fall | inspect | exit | reject | gone
        self.age = 0.0
        self.anim = 0.0
        self.toggle_cooldown = 0.0
        self.transform_timer = 0.0  # >0 while showing the squash/flash transformation
        self.dropping = False       # failsafe: ignore everything but the floor
        self.tumble = 0.0           # rotation for rejected bots
        self.vx_extra = 0.0
        self.demo_target = False
        self.prev_x = self.x

    # -- properties ------------------------------------------------------------
    @property
    def top(self):
        return self.y - self.h

    @property
    def alive(self):
        return self.state in ("walk", "fall", "inspect")

    @property
    def stompable(self):
        return self.state in ("walk", "fall", "inspect")

    @property
    def speed(self):
        s = self.base_speed
        if not self.good:
            s *= config.BOT_BAD_SPEED_MULT
        return s

    # -- state changes ---------------------------------------------------------
    def toggle(self):
        """Flip GOOD<->BAD.  Returns True if the toggle happened."""
        if self.toggle_cooldown > 0 or not self.stompable:
            return False
        self.good = not self.good
        self.toggle_cooldown = config.BOT_TOGGLE_COOLDOWN
        self.transform_timer = config.BOT_TRANSFORM_TIME
        return True

    def make_good(self):
        """AI Compass: force GOOD (ignores the stomp cooldown)."""
        if self.good or not self.stompable:
            return False
        self.good = True
        self.toggle_cooldown = config.BOT_TOGGLE_COOLDOWN
        self.transform_timer = config.BOT_TRANSFORM_TIME
        return True

    # -- simulation ------------------------------------------------------------
    def update(self, dt, platforms, speed_mult=1.0):
        self.age += dt
        self.anim += dt
        if self.toggle_cooldown > 0:
            self.toggle_cooldown -= dt
        if self.transform_timer > 0:
            self.transform_timer -= dt
        if self.age > config.BOT_FAILSAFE_LIFETIME:
            self.dropping = True

        if self.state == "exit":
            self.x += self.dir * 34.0 * dt
            if self.x < -12 or self.x > W + 12:
                self.state = "gone"
            return
        if self.state == "reject":
            self.vy = min(self.vy + config.BOT_GRAVITY * dt, 260.0)
            self.y += self.vy * dt
            self.x += self.vx_extra * dt
            self.tumble += dt
            if self.y - self.h > config.LOGICAL_H + 4:
                self.state = "gone"
            return
        if self.state == "inspect":
            return  # the station drives the bot
        if self.age > config.BOT_HARD_LIFETIME:
            self.state = "gone"
            return

        usable = platforms
        if self.dropping:
            usable = [p for p in platforms if p.kind == "floor"]

        # Squash pause while transforming keeps the change readable.
        moving = self.transform_timer <= config.BOT_TRANSFORM_TIME * 0.45

        if self.state == "walk":
            ground = self.ground  # arm-platform carrying is applied by World
            if moving:
                belt = ground.belt_dir * config.BOT_BELT_SPEED if ground is not None else 0.0
                self.x += (self.dir * self.speed * speed_mult + belt) * dt
            on_floor = ground is not None and ground.kind == "floor"
            if not on_floor:
                self.x = wrap_x(self.x)
            else:
                self.x = max(-8.0, min(W + 8.0, self.x))
            support = find_support(usable, self.x, self.y)
            if support is None:
                self.state = "fall"
                self.ground = None
                self.vy = 0.0
            else:
                self.ground = support
                self.y = support.y
        if self.state == "fall":
            prev = self.y
            self.vy = min(self.vy + config.BOT_GRAVITY * dt, config.BOT_MAX_FALL)
            self.y += self.vy * dt
            self.x = wrap_x(self.x)
            land = find_landing(usable, self.x, prev, self.y)
            if land is not None:
                self.y = land.y
                self.vy = 0.0
                self.ground = land
                self.state = "walk"
            elif self.y > config.LOGICAL_H + 20:
                self.state = "gone"
