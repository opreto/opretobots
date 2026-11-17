"""Kinoptyx camera inspection stations at the bottom-left and bottom-right exits."""

import config
import level

W = config.LOGICAL_W


class Station:
    def __init__(self, side):
        self.side = side                      # -1 = left, +1 = right
        if side < 0:
            self.scan_x = float(level.STATION_SCAN_OFFSET)
        else:
            self.scan_x = float(W - level.STATION_SCAN_OFFSET)
        self.reset()

    def reset(self):
        self.state = "idle"                   # idle | approach | scan | result
        self.timer = 0.0
        self.bot = None
        self.result = None                    # "pass" | "reject"
        self.flash = 0.0                      # result light flash timer
        self.trapdoor = 0.0                   # >0 while the reject trapdoor is open
        self.ejector = 0.0                    # ejector piston animation
        self.anim = 0.0

    @property
    def busy(self):
        return self.state != "idle"

    def in_zone(self, x):
        if self.side < 0:
            return x < level.STATION_ZONE
        return x > W - level.STATION_ZONE

    def queue_x(self):
        """Where a bot waits while the station is busy."""
        if self.side < 0:
            return level.STATION_ZONE + 6.0
        return W - level.STATION_ZONE - 6.0

    def capture(self, bot):
        self.state = "approach"
        self.bot = bot
        self.timer = 0.0
        self.result = None
        bot.state = "inspect"
        bot.dir = self.side

    def update(self, dt, world):
        self.anim += dt
        for name in ("flash", "trapdoor", "ejector"):
            v = getattr(self, name)
            if v > 0:
                setattr(self, name, max(0.0, v - dt))
        bot = self.bot
        if self.state == "approach":
            if bot is None or bot.state != "inspect":
                self.reset_soft()
                return
            step = max(bot.speed, 20.0) * dt
            d = self.scan_x - bot.x
            if abs(d) <= step:
                bot.x = self.scan_x
                self.state = "scan"
                self.timer = 0.0
                world.emit("scan")
            else:
                bot.x += step if d > 0 else -step
        elif self.state == "scan":
            self.timer += dt
            if bot is None or bot.state != "inspect":
                self.reset_soft()
                return
            if self.timer >= config.INSPECTION_SCAN_TIME:
                self._decide(world)
        elif self.state == "result":
            self.timer += dt
            if self.timer >= config.INSPECTION_RESULT_HOLD:
                self.reset_soft()

    def reset_soft(self):
        self.state = "idle"
        self.bot = None
        self.timer = 0.0

    def _decide(self, world):
        bot = self.bot
        self.state = "result"
        self.timer = 0.0
        self.flash = 0.8
        if bot.good:
            self.result = "pass"
            bot.state = "exit"
            bot.dir = self.side
            world.on_inspection_pass(self, bot)
        else:
            self.result = "reject"
            bot.state = "reject"
            bot.vy = -110.0
            bot.vx_extra = -self.side * 10.0
            self.trapdoor = 0.9
            self.ejector = 0.35
            world.on_inspection_reject(self, bot)
