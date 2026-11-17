"""Short-lived visual effects (particles, popups, pulses, banners).

Pure data: the renderer draws them.  Counts are capped so an unattended
kiosk can never accumulate unbounded effects.
"""

import math

MAX_PARTICLES = 400
MAX_POPUPS = 16


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "life", "max_life", "gravity", "size")

    def __init__(self, x, y, vx, vy, color, life, gravity=0.0, size=1):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.color = color
        self.life = self.max_life = life
        self.gravity = gravity
        self.size = size


class Popup:
    __slots__ = ("text", "x", "y", "color", "life", "max_life", "big")

    def __init__(self, text, x, y, color, life=1.1, big=False):
        self.text, self.x, self.y, self.color = text, x, y, color
        self.life = self.max_life = life
        self.big = big


class Pulse:
    __slots__ = ("x", "y", "life", "max_life", "max_r", "color")

    def __init__(self, x, y, life, max_r, color):
        self.x, self.y = x, y
        self.life = self.max_life = life
        self.max_r = max_r
        self.color = color

    @property
    def radius(self):
        t = 1.0 - self.life / self.max_life
        return self.max_r * (1 - (1 - t) ** 2)


class Ghost:
    """Attract-mode demo: a translucent mechanic drops onto a bad bot."""

    __slots__ = ("bot", "x", "y", "vy", "life", "done")

    def __init__(self, bot):
        self.bot = bot
        self.x = bot.x
        self.y = bot.top - 40
        self.vy = 0.0
        self.life = 1.6
        self.done = False


class Effects:
    def __init__(self, rng):
        self.rng = rng
        self.clear()

    def clear(self):
        self.particles = []
        self.popups = []
        self.pulses = []
        self.ghosts = []
        self.banner = None          # (text, sub, life, max_life)
        self.screen_flash = 0.0
        self.shake = 0.0

    def burst(self, x, y, colors, count=14, speed=70.0, life=0.45, gravity=120.0):
        rng = self.rng
        for _ in range(count):
            a = rng.uniform(0, math.tau)
            s = rng.uniform(speed * 0.35, speed)
            self.particles.append(Particle(x, y, math.cos(a) * s, math.sin(a) * s - 20,
                                           rng.choice(colors), rng.uniform(life * 0.6, life), gravity))
        self._cap()

    def spark(self, x, y):
        rng = self.rng
        for _ in range(2):
            self.particles.append(Particle(x, y, rng.uniform(-30, 30), rng.uniform(-50, -15),
                                           rng.choice(((255, 240, 120), (255, 255, 255), (120, 220, 255))),
                                           rng.uniform(0.15, 0.3), 200.0))
        self._cap()

    def popup(self, text, x, y, color, life=1.1, big=False):
        self.popups.append(Popup(text, x, y, color, life, big))
        if len(self.popups) > MAX_POPUPS:
            del self.popups[0]

    def pulse(self, x, y, life, max_r, color):
        self.pulses.append(Pulse(x, y, life, max_r, color))

    def show_banner(self, text, sub="", life=1.8):
        self.banner = [text, sub, life, life]

    def _cap(self):
        if len(self.particles) > MAX_PARTICLES:
            del self.particles[: len(self.particles) - MAX_PARTICLES]

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0:
                p.vy += p.gravity * dt
                p.x += p.vx * dt
                p.y += p.vy * dt
                alive.append(p)
        self.particles = alive
        for p in self.popups:
            p.life -= dt
            p.y -= 14 * dt
        self.popups = [p for p in self.popups if p.life > 0]
        for p in self.pulses:
            p.life -= dt
        self.pulses = [p for p in self.pulses if p.life > 0]
        if self.banner is not None:
            self.banner[2] -= dt
            if self.banner[2] <= 0:
                self.banner = None
        if self.screen_flash > 0:
            self.screen_flash = max(0.0, self.screen_flash - dt)
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt)
