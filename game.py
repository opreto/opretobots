"""Main gameplay state.  ``World`` is pure simulation (no rendering, no pygame),
which keeps the rules unit-testable and deterministic for a given seed."""

import random

import config
import level
from ai_compass import Compass
from bots import Robot
from conveyor import Feeder, Spawner
from effects import Effects, Ghost
from inspection import Station
from physics import wrap_dx, wrap_x
from player import Controls, Player
from robot_arm import RobotArm

GOOD_BURST = ((80, 240, 140), (180, 255, 210), (255, 255, 255), (60, 220, 230))
BAD_BURST = ((255, 70, 70), (255, 170, 60), (255, 255, 255), (230, 50, 140))
CYAN = (90, 230, 255)
P_COLORS = (((60, 110, 255), (255, 160, 40), (255, 255, 255)),
            ((235, 60, 60), (255, 160, 40), (255, 255, 255)))


class World:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.static_platforms = level.build_platforms()
        self.floor = self.static_platforms[0]
        self.compass_platform = level.build_compass_platform()
        self.arms = [RobotArm(a["name"], a["base_x"], a["pos_a"], a["pos_b"], a["elbow_side"],
                              phase_offset=i * config.ARM_PHASE_OFFSET)
                     for i, a in enumerate(level.ARMS)]
        self.arm_platforms = [a.platform for a in self.arms]
        self.platforms = self.static_platforms + self.arm_platforms + [self.compass_platform]
        self.players = [Player(0), Player(1)]
        self.compass = Compass()
        self.stations = [Station(-1), Station(+1)]
        self.feeders = [Feeder(-1), Feeder(+1)]
        self.spawner = Spawner(self.rng)
        self.effects = Effects(self.rng)
        self.robots = []
        self.events = []
        self.time = 0.0
        self.mode = "attract"
        self.accepted_total = 0
        self.rejected_total = 0
        self.reset_session()

    # ------------------------------------------------------------------ helpers
    def emit(self, name):
        self.events.append(name)

    def drain_events(self):
        ev, self.events = self.events, []
        return ev

    def active_players(self):
        return [p for p in self.players if p.active]

    def alive_robots(self):
        return [b for b in self.robots if b.alive]

    @property
    def difficulty(self):
        return Spawner.difficulty_level(self.play_time)

    # --------------------------------------------------------------- lifecycle
    def reset_session(self):
        """Score, charges, difficulty, robots, effects and level back to defaults."""
        self.score = 0
        self.play_time = 0.0
        self.robots = []
        self.effects.clear()
        self.compass.reset()
        for arm in self.arms:
            arm.reset()
        for st in self.stations:
            st.reset()
        self.spawner.reset()
        self.demo_timer = 1.5
        self.attract_time = 0.0

    def enter_attract(self):
        self.reset_session()
        self.mode = "attract"
        self.emit("attract")

    def join(self, slot):
        p = self.players[slot]
        if p.active:
            return
        if self.mode != "play":
            self.reset_session()
            self.mode = "play"
            self.emit("game_start")
        p.activate()
        self.effects.burst(p.x, p.y - 8, P_COLORS[slot], count=22, speed=60, life=0.6, gravity=40)
        self.effects.popup("P%d READY!" % (slot + 1), p.x, p.y - 22, (255, 230, 90))
        self.emit("join")

    def leave(self, slot):
        p = self.players[slot]
        if not p.active:
            return
        p.deactivate()
        self.effects.burst(p.x, p.y - 8, P_COLORS[slot], count=26, speed=50, life=0.7, gravity=-30)
        self.emit("leave")
        if not self.active_players():
            self.enter_attract()

    # -------------------------------------------------------------------- step
    def step(self, dt, controls=None, disconnected=()):
        if controls is None:
            controls = [Controls(), Controls()]
        self.time += dt

        for slot in disconnected:
            self.leave(slot)

        joined = set()
        for slot, ctl in enumerate(controls):
            p = self.players[slot]
            if not p.active:
                if ctl.join_pressed:
                    self.join(slot)
                    joined.add(slot)
            else:
                if ctl.activity:
                    p.idle = 0.0
                else:
                    p.idle += dt
                    if p.idle >= config.PLAYER_IDLE_TIMEOUT:
                        self.leave(slot)

        if self.mode == "play":
            self.play_time += dt
        else:
            self.attract_time += dt

        # machinery first, then carry anything riding it
        for pl in self.platforms:
            pl.begin_step()
        for arm in self.arms:
            for ev in arm.update(dt):
                self.emit(ev)
        self._carry_riders()

        for slot, p in enumerate(self.players):
            if not p.active:
                continue
            ctl = controls[slot]
            if slot in joined:
                ctl = Controls(dir=ctl.dir)
            p.prev_y = p.y
            evs = []
            p.update(dt, ctl, self.platforms, self.compass.box, evs)
            for ev in evs:
                if isinstance(ev, tuple) and ev[0] == "compass_hit":
                    self._compass_hit(p)
                else:
                    self.emit(ev)

        speed_mult = Spawner.speed_mult(self.play_time) if self.mode == "play" else 1.0
        for b in self.robots:
            b.prev_x = b.x
            b.update(dt, self.platforms, speed_mult)
            if not b.good and b.alive and self.rng.random() < config.BOT_SPARK_CHANCE * dt:
                self.effects.spark(b.x + self.rng.uniform(-5, 5), b.top + self.rng.uniform(0, 4))

        self._player_robot_interactions()
        self._update_stations(dt)
        self.robots = [b for b in self.robots if b.state != "gone"]
        self._spawn(dt)
        if self.mode == "attract":
            self._attract(dt)

        self.compass.update(dt)
        for f in self.feeders:
            f.update(dt)
        self.effects.update(dt)

    # ---------------------------------------------------------------- riders
    def _carry_riders(self):
        for pl in self.arm_platforms:
            if pl.dx == 0 and pl.dy == 0:
                continue
            for p in self.players:
                if p.active:
                    self._carry(p, pl, p.half_w - 2)
            for b in self.robots:
                if b.state == "walk":
                    self._carry(b, pl, None)

    def _carry(self, ent, pl, half_w):
        if ent.ground is pl:
            ent.x = wrap_x(ent.x + pl.dx)
            ent.y = pl.y
            return
        # a rising platform scoops up anything standing in its path
        if ent.ground is not None and pl.dy < 0 and pl.prev_y >= ent.y - 0.01 and pl.y <= ent.y:
            ok = pl.supports_point(ent.x) if half_w is None else pl.supports_span(ent.x, half_w)
            if ok:
                ent.ground = pl
                ent.y = pl.y

    # ------------------------------------------------------------ interactions
    def _player_robot_interactions(self):
        for p in self.players:
            if not p.active:
                continue
            stomped = False
            for b in self.robots:
                if not b.stompable:
                    continue
                dx = wrap_dx(p.x, b.x)
                if abs(dx) >= (p.w + b.w) * 0.5 - 1:
                    continue
                if p.y <= b.top or p.top >= b.y:
                    continue
                from_above = (p.prev_y <= b.top + config.PLAYER_STOMP_TOLERANCE
                              and p.y >= p.prev_y - 0.01 and p.stun <= 0)
                if from_above:
                    stomped = True
                    if b.toggle():
                        self._on_toggled(b, by_player=p)
                    p.y = b.top
                    p.stomp_bounce()
                    self.emit("bounce")
            if stomped:
                continue
            for b in self.robots:
                if b.good or b.state not in ("walk", "fall") or b.transform_timer > 0:
                    continue
                dx = wrap_dx(p.x, b.x)
                if abs(dx) >= (p.w + b.w) * 0.5 - 2:
                    continue
                if p.y <= b.top + 1 or p.top >= b.y - 1:
                    continue
                if p.hurt(b.x):
                    self.effects.burst(p.x, p.top + 4, ((255, 255, 120), (255, 255, 255)), count=8,
                                       speed=50, life=0.3, gravity=0)
                    self.emit("hurt")
                    break

    def _on_toggled(self, b, by_player=None):
        cx, cy = b.x, b.y - b.h * 0.5
        if b.good:
            self.effects.burst(cx, cy, GOOD_BURST, count=18, speed=80)
            self.emit("fix")
        else:
            self.effects.burst(cx, cy, BAD_BURST, count=18, speed=80)
            self.emit("break")

    def _compass_hit(self, p):
        result = self.compass.hit(self.robots)
        cx = self.compass.cx
        if result == "fired":
            fixed = [b for b in self.robots if b.transform_timer > config.BOT_TRANSFORM_TIME - 0.01]
            for b in fixed:
                self.effects.burst(b.x, b.y - b.h * 0.5, GOOD_BURST, count=10, speed=60)
            self.effects.pulse(cx, self.compass.top + 6, 0.9, 440, CYAN)
            self.effects.pulse(cx, self.compass.top + 6, 0.6, 220, (255, 255, 255))
            self.effects.show_banner("AI COMPASS!", "ALL BOTS FIXED!", 1.9)
            self.effects.screen_flash = 0.25
            self.effects.shake = 0.3
            self.emit("compass")
        elif result == "no_targets":
            self.effects.popup("NO BAD BOTS", cx, self.compass.top - 4, (150, 220, 255), 0.9)
            self.emit("bonk")
        elif result == "empty":
            self.effects.popup("RECHARGING", cx, self.compass.top - 4, (255, 150, 90), 0.9)
            self.emit("bonk")

    # --------------------------------------------------------------- stations
    def _update_stations(self, dt):
        for b in self.robots:
            if b.state != "walk" or b.ground is not self.floor:
                continue
            for st in self.stations:
                if b.dir != st.side:
                    continue
                if st.busy:
                    qx = st.queue_x()
                    beyond = (b.x < qx) if st.side < 0 else (b.x > qx)
                    if beyond:
                        prev_beyond = (b.prev_x < qx) if st.side < 0 else (b.prev_x > qx)
                        b.x = b.prev_x if prev_beyond else qx
                elif st.in_zone(b.x):
                    st.capture(b)
        for st in self.stations:
            st.update(dt, self)

    def on_inspection_pass(self, st, bot):
        y = level.FLOOR_Y - 30
        if self.mode == "play":
            self.score += config.SCORE_PER_ACCEPTED
            self.accepted_total += 1
            self.effects.popup("PASS +%d" % config.SCORE_PER_ACCEPTED, st.scan_x, y, (120, 255, 140))
            if self.compass.on_accepted():
                self.effects.popup("AI COMPASS RECHARGED!", config.LOGICAL_W / 2, level.COMPASS_TOP - 14,
                                   CYAN, 1.6)
                self.emit("recharge")
        else:
            self.effects.popup("PASS", st.scan_x, y, (120, 255, 140))
        self.effects.burst(bot.x, bot.y - 6, GOOD_BURST, count=8, speed=40)
        self.emit("pass")

    def on_inspection_reject(self, st, bot):
        self.rejected_total += 1 if self.mode == "play" else 0
        self.effects.popup("REJECT", st.scan_x, level.FLOOR_Y - 30, (255, 90, 90))
        self.emit("reject")

    # ---------------------------------------------------------------- spawning
    def _spawn(self, dt):
        alive = len(self.alive_robots())
        if self.mode == "play":
            interval = Spawner.interval(len(self.active_players()), self.play_time)
            cap = config.MAX_ACTIVE_BOTS
            bad_p = Spawner.bad_probability(self.play_time)
        else:
            interval = config.ATTRACT_SPAWN_INTERVAL
            cap = config.ATTRACT_MAX_BOTS
            bad_p = config.INITIAL_BAD_PROBABILITY
        bot = self.spawner.update(dt, interval, alive < cap, self.feeders, bad_p)
        if bot is not None:
            self.robots.append(bot)
            self.emit("spawn")

    # ----------------------------------------------------------------- attract
    @staticmethod
    def _behind_panel(b):
        x1, y1, x2, y2 = level.ATTRACT_PANEL
        return x1 - 8 < b.x < x2 + 8 and y1 < b.y < y2 + 16

    def _attract(self, dt):
        self.demo_timer -= dt
        if self.demo_timer <= 0:
            self.demo_timer = config.ATTRACT_DEMO_STOMP_INTERVAL
            targets = [b for b in self.robots
                       if b.state == "walk" and not b.good and not b.demo_target
                       and b.ground is not None and b.ground.kind != "floor" and b.age > 1.5
                       and 30 < b.x < config.LOGICAL_W - 30 and not self._behind_panel(b)]
            if targets:
                b = self.rng.choice(targets)
                b.demo_target = True
                self.effects.ghosts.append(Ghost(b))
        for g in self.effects.ghosts:
            g.life -= dt
            b = g.bot
            if not g.done:
                g.vy += config.GRAVITY * dt
                g.y += g.vy * dt
                g.x = b.x
                if not b.alive:
                    g.done = True
                elif g.y >= b.top:
                    g.y = b.top
                    g.vy = -config.PLAYER_STOMP_BOUNCE
                    g.done = True
                    if b.toggle():
                        self._on_toggled(b)
                        self.effects.popup("FIXED!", b.x, b.top - 10, (140, 255, 170), 0.9)
            else:
                g.vy += config.GRAVITY * dt
                g.y += g.vy * dt
            if not b.alive:
                b.demo_target = False
        self.effects.ghosts = [g for g in self.effects.ghosts if g.life > 0]
