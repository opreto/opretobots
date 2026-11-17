"""Huge orange industrial robot arms that reposition platforms.

The arm is purely kinematic: each cycle it holds, flashes a warning light,
then smoothly interpolates its platform between two authored positions.
Platforms stay horizontal.  Joint angles for drawing come from 2-link IK.
"""

import math

import config
from physics import Platform, ease_in_out
import level

FLOOR = level.FLOOR_Y


class RobotArm:
    UPPER = 50.0
    LOWER = 48.0

    def __init__(self, name, base_x, pos_a, pos_b, elbow_side, phase_offset):
        self.name = name
        self.base_x = base_x
        self.pos_a = pos_a
        self.pos_b = pos_b
        self.elbow_side = elbow_side
        self.phase_offset = phase_offset
        self.platform = Platform(name, pos_a[0], pos_a[0] + level.ARM_PLATFORM_W, pos_a[1],
                                 0, kind="arm", thickness=5)
        self.reset()

    def reset(self):
        self.clock = -self.phase_offset
        self.at_b = False           # current resting position
        self.state = "hold"
        self.progress = 0.0
        self.platform.move_to(*self.pos_a)
        self.platform.begin_step()

    @property
    def shoulder(self):
        return (self.base_x, FLOOR - 16)

    def _schedule(self):
        cycle = config.ARM_CYCLE_TIME
        hold = cycle - config.ARM_WARNING_TIME - config.ARM_MOVE_TIME
        return cycle, hold

    def update(self, dt):
        """Advance the arm.  Returns list of event names."""
        events = []
        cycle, hold = self._schedule()
        self.clock += dt
        if self.clock < 0:
            return events
        t = self.clock % cycle
        prev_state = self.state
        if t < hold:
            self.state = "hold"
        elif t < hold + config.ARM_WARNING_TIME:
            self.state = "warn"
        else:
            self.state = "move"
            self.progress = (t - hold - config.ARM_WARNING_TIME) / config.ARM_MOVE_TIME
        if prev_state == "move" and self.state != "move":
            self.at_b = not self.at_b
            self.progress = 0.0
        if self.state == "warn" and prev_state != "warn":
            events.append("arm_warn")
        if self.state == "move" and prev_state != "move":
            events.append("arm_move")

        start, end = (self.pos_b, self.pos_a) if self.at_b else (self.pos_a, self.pos_b)
        if self.state == "move":
            k = ease_in_out(self.progress)
        else:
            k = 0.0
        x1 = start[0] + (end[0] - start[0]) * k
        y = start[1] + (end[1] - start[1]) * k
        self.platform.move_to(x1, y)
        return events

    # -- geometry for rendering -------------------------------------------
    def wrist(self):
        p = self.platform
        return (p.cx, p.y + p.thickness + 7)

    def joints(self):
        """(shoulder, elbow, wrist) points from 2-link inverse kinematics."""
        sx, sy = self.shoulder
        wx, wy = self.wrist()
        dx, dy = wx - sx, wy - sy
        dist = math.hypot(dx, dy)
        a, b = self.UPPER, self.LOWER
        dist = max(abs(a - b) + 0.01, min(a + b - 0.01, dist))
        # angle at shoulder between shoulder->wrist and shoulder->elbow
        cos_s = (a * a + dist * dist - b * b) / (2 * a * dist)
        ang_s = math.acos(max(-1.0, min(1.0, cos_s)))
        base_ang = math.atan2(dy, dx)
        # "elbow up" pose, like a real floor-mounted industrial robot
        cand1 = base_ang + ang_s
        cand2 = base_ang - ang_s
        e1 = (sx + a * math.cos(cand1), sy + a * math.sin(cand1))
        e2 = (sx + a * math.cos(cand2), sy + a * math.sin(cand2))
        elbow = e1 if e1[1] < e2[1] else e2
        return (sx, sy), elbow, (wx, wy)

    @property
    def light_on(self):
        if self.state == "warn":
            return int(self.clock * 8) % 2 == 0
        if self.state == "move":
            return int(self.clock * 6) % 2 == 0
        return False
