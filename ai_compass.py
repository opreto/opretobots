"""AI Compass power block: bump it from below to fix every BAD bot on screen."""

import config
import level


class Compass:
    def __init__(self):
        self.x1 = level.COMPASS_X1
        self.x2 = level.COMPASS_X2
        self.top = level.COMPASS_TOP
        self.bottom = level.COMPASS_BOTTOM
        self.reset()

    def reset(self):
        self.charges = config.COMPASS_START_CHARGES
        self.recharge_count = 0
        self.cooldown = 0.0
        self.bump = 0.0         # bump animation timer
        self.flash = 0.0        # activation flash
        self.anim = 0.0

    @property
    def box(self):
        return (self.x1, self.x2, self.bottom)

    @property
    def cx(self):
        return (self.x1 + self.x2) * 0.5

    def update(self, dt):
        self.anim += dt
        for name in ("cooldown", "bump", "flash"):
            v = getattr(self, name)
            if v > 0:
                setattr(self, name, max(0.0, v - dt))

    def hit(self, bots):
        """Handle a bump from below.  Returns "fired", "no_targets", "empty" or "cooldown"."""
        if self.cooldown > 0:
            return "cooldown"
        self.bump = 0.18
        self.cooldown = config.COMPASS_COOLDOWN
        if self.charges <= 0:
            return "empty"
        targets = [b for b in bots if b.stompable and not b.good]
        if not targets:
            return "no_targets"
        self.charges -= 1
        self.flash = 0.6
        for b in targets:
            b.make_good()
        return "fired"

    def on_accepted(self):
        """Called for every successful inspection.  Returns True if recharged."""
        if self.charges >= config.COMPASS_START_CHARGES:
            self.recharge_count = 0
            return False
        self.recharge_count += 1
        if self.recharge_count >= config.COMPASS_RECHARGE_INSPECTIONS:
            self.charges = config.COMPASS_START_CHARGES
            self.recharge_count = 0
            return True
        return False
