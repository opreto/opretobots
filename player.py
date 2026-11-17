"""Hard-hat factory mechanics (player characters)."""

import config
import level
from physics import approach, find_landing, find_support, wrap_x


class Controls:
    """Per-slot input snapshot for one simulation step."""

    __slots__ = ("dir", "jump_held", "jump_pressed", "join_pressed", "activity")

    def __init__(self, dir=0, jump_held=False, jump_pressed=False, join_pressed=False, activity=False):
        self.dir = dir
        self.jump_held = jump_held
        self.jump_pressed = jump_pressed
        self.join_pressed = join_pressed
        self.activity = activity


class Player:
    def __init__(self, slot):
        self.slot = slot
        self.active = False
        self.w = config.PLAYER_W
        self.h = config.PLAYER_H
        self.reset_body()

    def reset_body(self):
        sx, sy = config.PLAYER_SPAWN[self.slot]
        self.x = sx
        self.y = sy
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1 if self.slot == 0 else -1
        self.ground = None
        self.coyote = 0.0
        self.jump_buffer = 0.0
        self.stun = 0.0
        self.invuln = 0.0
        self.idle = 0.0
        self.anim = 0.0
        self.swing = 0.0          # wrench swing animation timer
        self.land_timer = 0.0
        self.spawn_timer = 0.0
        self.step_timer = 0.0
        self.jumping = False      # rising from a real jump (enables variable height)
        self.prev_y = self.y

    # -- lifecycle -------------------------------------------------------------
    def activate(self):
        self.reset_body()
        self.active = True
        self.spawn_timer = 0.6
        self.invuln = 1.0

    def deactivate(self):
        self.active = False

    @property
    def top(self):
        return self.y - self.h

    @property
    def half_w(self):
        return self.w * 0.5

    # -- simulation ------------------------------------------------------------
    def update(self, dt, ctl, platforms, compass_box, events):
        """Advance one fixed step.  ``compass_box`` = (x1, x2, bottom)."""
        self.anim += dt
        for name in ("stun", "invuln", "swing", "land_timer", "spawn_timer"):
            v = getattr(self, name)
            if v > 0:
                setattr(self, name, max(0.0, v - dt))

        stunned = self.stun > 0
        move_dir = 0 if stunned else ctl.dir
        if move_dir:
            self.facing = move_dir

        target = move_dir * config.PLAYER_RUN_SPEED
        if self.ground is not None:
            rate = config.PLAYER_GROUND_ACCEL if move_dir else config.PLAYER_GROUND_DECEL
        else:
            rate = config.PLAYER_AIR_ACCEL
        if stunned:
            rate = 260.0
        self.vx = approach(self.vx, target, rate * dt)

        # jump buffering + coyote time
        if ctl.jump_pressed and not stunned:
            self.jump_buffer = config.PLAYER_JUMP_BUFFER
        elif self.jump_buffer > 0:
            self.jump_buffer -= dt
        if self.ground is not None:
            self.coyote = config.PLAYER_COYOTE_TIME
        elif self.coyote > 0:
            self.coyote -= dt

        if self.jump_buffer > 0 and self.coyote > 0 and not stunned:
            self.vy = -config.PLAYER_JUMP_VELOCITY
            self.ground = None
            self.coyote = 0.0
            self.jump_buffer = 0.0
            self.jumping = True
            events.append("jump")

        if self.jumping and self.vy < 0 and not ctl.jump_held:
            if self.vy < -config.PLAYER_JUMP_CUT_VELOCITY:
                self.vy = -config.PLAYER_JUMP_CUT_VELOCITY
            self.jumping = False

        # horizontal motion with wraparound
        self.x = wrap_x(self.x + self.vx * dt)

        if self.ground is not None:
            support = find_support(platforms, self.x, self.y, self.half_w - 2)
            if support is None:
                self.ground = None
                self.vy = 0.0
            else:
                self.ground = support
                self.y = support.y
                if abs(self.vx) > 20:
                    self.step_timer -= dt
                    if self.step_timer <= 0:
                        self.step_timer = 0.22
                        events.append("step")

        if self.ground is None:
            prev_bottom = self.y
            prev_top = self.top
            self.vy = min(self.vy + config.GRAVITY * dt, config.PLAYER_MAX_FALL)
            self.y += self.vy * dt
            if self.vy < 0:
                cx1, cx2, cbottom = compass_box
                if (self.x + self.half_w - 1 > cx1 and self.x - self.half_w + 1 < cx2
                        and prev_top >= cbottom - 0.5 and self.top <= cbottom):
                    self.y = cbottom + self.h
                    self.vy = 30.0
                    self.jumping = False
                    events.append(("compass_hit", self.slot))
            if self.vy >= 0:
                land = find_landing(platforms, self.x, prev_bottom, self.y, self.half_w - 2)
                if land is not None:
                    self.y = land.y
                    self.vy = 0.0
                    self.ground = land
                    self.jumping = False
                    self.land_timer = 0.09
                    events.append("land")
            if self.y > config.LOGICAL_H + 30:   # should never happen; floor is solid
                self.reset_body()

    def stomp_bounce(self):
        self.vy = -config.PLAYER_STOMP_BOUNCE
        self.ground = None
        self.coyote = 0.0
        self.jumping = True       # holding jump keeps the bigger bounce
        self.swing = 0.22

    def hurt(self, from_x):
        if self.invuln > 0 or self.stun > 0:
            return False
        away = 1 if self.x >= from_x else -1
        self.vx = away * config.PLAYER_KNOCKBACK_X
        self.vy = -config.PLAYER_KNOCKBACK_Y
        self.ground = None
        self.jumping = False
        self.stun = config.PLAYER_STUN_TIME
        self.invuln = config.PLAYER_INVULN_TIME
        return True
