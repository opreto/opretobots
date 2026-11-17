"""Collision and movement utilities.

Coordinate conventions (logical pixels):
  * entity ``x`` is the horizontal centre, ``y`` is the bottom (feet).
  * platform ``y`` is the walking surface; platforms are one-way (you can jump
    up through them and land on top), so nothing can ever be crushed.
  * the screen wraps horizontally; platforms touching a screen edge are treated
    as continuing across it.
"""

import config

W = config.LOGICAL_W


class Platform:
    def __init__(self, name, x1, x2, y, belt_dir=0, kind="belt", thickness=6):
        self.name = name
        self.x1 = float(x1)
        self.x2 = float(x2)
        self.y = float(y)
        self.prev_x1 = self.x1
        self.prev_y = self.y
        self.belt_dir = belt_dir
        self.kind = kind            # "belt", "floor", "arm", "compass"
        self.thickness = thickness
        self.dx = 0.0
        self.dy = 0.0

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def cx(self):
        return (self.x1 + self.x2) * 0.5

    @property
    def moving(self):
        return self.kind == "arm"

    def begin_step(self):
        self.prev_x1 = self.x1
        self.prev_y = self.y
        self.dx = 0.0
        self.dy = 0.0

    def move_to(self, x1, y):
        self.dx = x1 - self.x1
        self.dy = y - self.y
        w = self.width
        self.x1 = float(x1)
        self.x2 = self.x1 + w
        self.y = float(y)

    def span(self):
        """Horizontal span, extended across the screen edge if it touches one."""
        a, b = self.x1, self.x2
        if a <= 0:
            a = -W
        if b >= W:
            b = 2 * W
        return a, b

    def supports_point(self, x):
        a, b = self.span()
        return a <= x <= b

    def supports_span(self, x, half_w):
        a, b = self.span()
        return x + half_w > a and x - half_w < b


def wrap_x(x):
    return x % W


def wrap_dx(a, b):
    """Shortest horizontal distance from a to b on the wrapping screen."""
    d = (b - a) % W
    if d > W / 2:
        d -= W
    return d


def find_support(platforms, x, y, half_w=None, tol=0.75):
    """Platform the entity is standing on, or None."""
    best = None
    for p in platforms:
        if abs(p.y - y) > tol:
            continue
        ok = p.supports_point(x) if half_w is None else p.supports_span(x, half_w)
        if ok and (best is None or p.y < best.y):
            best = p
    return best


def find_landing(platforms, x, prev_bottom, bottom, half_w=None, ignore=None):
    """Platform crossed from above during this step (accounts for platform motion)."""
    best = None
    for p in platforms:
        if ignore is not None and ignore(p):
            continue
        ok = p.supports_point(x) if half_w is None else p.supports_span(x, half_w)
        if not ok:
            continue
        if prev_bottom <= p.prev_y + 0.01 and bottom >= p.y - 0.01:
            if best is None or p.prev_y < best.prev_y:
                best = p
    return best


def approach(value, target, delta):
    if value < target:
        return min(value + delta, target)
    return max(value - delta, target)


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
