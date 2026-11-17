"""Pixel-art rendering of the factory, characters, effects and HUD.

Everything is drawn onto a 384x216 logical surface; main.py scales it to the
display with integer nearest-neighbour scaling.
"""

import math

import pygame

import config
import font
import level
from sprites import SpriteBank

W, H = config.LOGICAL_W, config.LOGICAL_H

# palette ------------------------------------------------------------------
INK = (20, 16, 28)
WALL_TOP = (20, 24, 50)
WALL_BOT = (34, 30, 52)
PANEL_LINE = (30, 36, 66)
BELT_DARK = (40, 40, 54)
BELT_TREAD = (92, 94, 116)
STEEL = (122, 132, 150)
STEEL_HI = (176, 186, 204)
STEEL_DK = (70, 76, 92)
HAZARD_Y = (250, 200, 40)
ORANGE = (244, 124, 24)
ORANGE_HI = (255, 176, 70)
ORANGE_DK = (170, 70, 10)
JOINT = (78, 82, 96)
JOINT_HI = (140, 146, 160)
WHITE = (255, 255, 255)
CYAN = (90, 230, 255)
GREEN = (90, 255, 120)
RED = (255, 70, 70)
YELLOW = (255, 226, 70)
P_COLORS = ((90, 140, 255), (255, 90, 90))


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Renderer:
    def __init__(self):
        self.surface = pygame.Surface((W, H))
        self.sprites = SpriteBank()
        self.background = self._build_background()
        self.overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        self.title_surf = font.big.render("OPRETO BOTS", (255, 196, 60), 2, shadow=(120, 40, 10))
        self.title_surf_big = font.big.render("OPRETO BOTS", (255, 196, 60), 3, shadow=(120, 40, 10))
        self.show_fps = config.SHOW_FPS
        self.fps = 0.0

    # =============================================================== background
    def _build_background(self):
        bg = pygame.Surface((W, H))
        for y in range(H):
            bg.fill(_lerp(WALL_TOP, WALL_BOT, y / H), (0, y, W, 1))
        for x in range(0, W, 32):
            bg.fill(PANEL_LINE, (x, 11, 1, 189))
        for y in (63, 102, 142, 181):
            bg.fill(PANEL_LINE, (0, y, W, 1))
        # rivets
        for x in range(0, W, 32):
            for y in (63, 102, 142, 181):
                bg.fill((48, 56, 92), (x + 3, y - 2, 1, 1))
                bg.fill((48, 56, 92), (x + 28, y - 2, 1, 1))
        # background pipes
        for px, col in ((70, (44, 52, 84)), (314, (44, 52, 84)), (78, (38, 44, 72)), (306, (38, 44, 72))):
            bg.fill(col, (px, 11, 4, 189))
            bg.fill((58, 68, 104), (px, 11, 1, 189))
            for y in range(30, 200, 40):
                bg.fill((60, 70, 110), (px - 1, y, 6, 3))
        bg.fill((40, 48, 78), (70, 52, 244, 3))
        bg.fill((56, 66, 100), (70, 52, 244, 1))
        # distant factory windows
        for x in range(132, 252, 14):
            bg.fill((26, 34, 70), (x, 66, 10, 12))
            bg.fill((44, 60, 110), (x + 1, 67, 8, 4))
        # dim wall logo behind the arms
        logo = font.big.render("OPRETO", (40, 48, 86), 3)
        bg.blit(logo, (W // 2 - logo.get_width() // 2, 128))
        sub = font.small.render("AUTOMATION CELL 01", (46, 56, 96))
        bg.blit(sub, (W // 2 - sub.get_width() // 2, 152))
        # Kinoptyx wall signs above the stations
        for side in (-1, 1):
            text = "KINOPTYX VISION QC"
            tw = font.small.text_width(text)
            sx = 6 if side < 0 else W - 6 - tw - 6
            pygame.draw.rect(bg, (26, 32, 56), (sx, 130, tw + 6, 11))
            pygame.draw.rect(bg, (60, 72, 120), (sx, 130, tw + 6, 11), 1)
            bg.blit(font.small.render(text, (130, 200, 255)), (sx + 3, 133))
            ax = 22 if side < 0 else W - 22
            for i in range(3):
                bg.fill((70, 110, 170), (ax - 2 + i, 144 + i, 5 - 2 * i, 1))
        # floor
        fy = level.FLOOR_Y
        bg.fill((58, 62, 78), (0, fy, W, H - fy))
        bg.fill(STEEL_HI, (0, fy, W, 1))
        bg.fill(STEEL, (0, fy + 1, W, 2))
        for x in range(0, W, 8):
            bg.fill((44, 46, 60), (x, fy + 4, 1, H - fy - 4))
        for y in range(fy + 4, H, 4):
            bg.fill((44, 46, 60), (0, y, W, 1))
        return bg

    # ==================================================================== draw
    def draw(self, world, input_status=None):
        s = self.surface
        s.blit(self.background, (0, 0))
        t = world.time
        self._draw_title_sign(s, t)
        for arm in world.arms:
            self._draw_arm(s, arm, t)
        for pl in world.static_platforms[1:]:
            self._draw_belt(s, pl, t)
        for st in world.stations:
            self._draw_station_back(s, st, t)
        for f in world.feeders:
            self._draw_feeder_back(s, f)
        for arm in world.arms:
            self._draw_arm_platform(s, arm)
        self._draw_compass(s, world.compass, t)
        for b in world.robots:
            self._draw_robot(s, b, t)
        for st in world.stations:
            self._draw_station_front(s, st, t)
        for f in world.feeders:
            self._draw_feeder_front(s, f, t)
        for p in world.players:
            if p.active:
                self._draw_player(s, p, t)
        self._draw_effects(s, world, t)
        self._draw_hud(s, world, t)
        if world.mode == "attract":
            self._draw_attract(s, world, t)
        else:
            self._draw_join_prompts(s, world, t)
        self._draw_banner(s, world, t)
        if world.effects.screen_flash > 0:
            a = int(160 * world.effects.screen_flash / 0.25)
            self.overlay.fill((200, 245, 255, min(255, a)))
            s.blit(self.overlay, (0, 0))
        if self.show_fps:
            font.small.draw(s, "%2.0f FPS" % self.fps, W - 2, H - 7, YELLOW, align="right", outline=INK)
        return s

    def shake_offset(self, world):
        if world.effects.shake <= 0:
            return (0, 0)
        k = int(world.time * 60)
        return ((k * 7) % 3 - 1, (k * 5) % 3 - 1)

    # ================================================================ title
    def _draw_title_sign(self, s, t):
        x1, x2, y1, y2 = 124, 260, 14, 40
        pygame.draw.rect(s, (30, 20, 34), (x1, y1, x2 - x1, y2 - y1))
        pygame.draw.rect(s, (90, 50, 30), (x1, y1, x2 - x1, y2 - y1), 1)
        # marquee bulbs
        n = 0
        phase = int(t * 6)
        for x in range(x1 + 2, x2 - 1, 5):
            for y in (y1 + 1, y2 - 2):
                on = (n + phase) % 3 == 0
                s.fill((255, 230, 120) if on else (110, 70, 40), (x, y, 2, 1))
                n += 1
        ts = self.title_surf
        s.blit(ts, ((x1 + x2) // 2 - ts.get_width() // 2, y1 + 4))
        font.small.draw(s, "ROBOT FACTORY", (x1 + x2) // 2, y1 + 20, (120, 200, 255), align="center")

    # ================================================================= belts
    def _draw_belt(self, s, pl, t):
        x1, x2, y = int(pl.x1), int(pl.x2), int(pl.y)
        w = x2 - x1
        s.fill(INK, (x1, y - 1, w, 1))
        s.fill(BELT_DARK, (x1, y, w, 2))
        phase = int(t * 14) % 6
        off = phase if pl.belt_dir >= 0 else (6 - phase) % 6
        for x in range(x1 - 6 + off, x2, 6):
            a, b = max(x, x1), min(x + 2, x2)
            if b > a:
                s.fill(BELT_TREAD, (a, y, b - a, 1))
        s.fill(STEEL_HI, (x1, y + 2, w, 1))
        s.fill(STEEL, (x1, y + 3, w, 2))
        s.fill(INK, (x1, y + 5, w, 1))
        # direction chevrons
        for cx in range(x1 + 10, x2 - 6, 18):
            if pl.belt_dir > 0:
                s.fill(HAZARD_Y, (cx, y + 3, 1, 1))
                s.fill(HAZARD_Y, (cx + 1, y + 3, 1, 2))
                s.fill(HAZARD_Y, (cx, y + 4, 1, 1))
            elif pl.belt_dir < 0:
                s.fill(HAZARD_Y, (cx + 1, y + 3, 1, 1))
                s.fill(HAZARD_Y, (cx, y + 3, 1, 2))
                s.fill(HAZARD_Y, (cx + 1, y + 4, 1, 1))
        # rollers at free ends
        spin = int(t * 10) % 2
        for ex, edge in ((x1, x1 <= 0), (x2 - 1, x2 >= W)):
            if edge:
                continue
            cx = ex + (2 if ex == x1 else -2)
            pygame.draw.circle(s, INK, (cx, y + 3), 3)
            pygame.draw.circle(s, STEEL_DK, (cx, y + 3), 2)
            s.fill(STEEL_HI if spin else STEEL, (cx, y + 2 + spin, 1, 1))

    # ================================================================== arms
    @staticmethod
    def _link(s, p1, p2, thick, col, hi, dk):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln

        def quad(th):
            h = th / 2.0
            return [(p1[0] + nx * h, p1[1] + ny * h), (p2[0] + nx * h, p2[1] + ny * h),
                    (p2[0] - nx * h, p2[1] - ny * h), (p1[0] - nx * h, p1[1] - ny * h)]

        pygame.draw.polygon(s, INK, quad(thick + 2))
        pygame.draw.polygon(s, dk, quad(thick))
        pygame.draw.polygon(s, col, quad(thick - 2))
        h = thick / 2.0 - 2
        pygame.draw.line(s, hi, (p1[0] + nx * h, p1[1] + ny * h), (p2[0] + nx * h, p2[1] + ny * h))

    @staticmethod
    def _joint(s, p, r):
        pygame.draw.circle(s, INK, (int(p[0]), int(p[1])), r + 1)
        pygame.draw.circle(s, JOINT, (int(p[0]), int(p[1])), r)
        pygame.draw.circle(s, JOINT_HI, (int(p[0]) - 1, int(p[1]) - 1), max(1, r - 3))
        s.fill(INK, (int(p[0]), int(p[1]), 1, 1))

    def _draw_arm(self, s, arm, t):
        bx = arm.base_x
        fy = level.FLOOR_Y
        # pedestal
        pygame.draw.polygon(s, INK, [(bx - 14, fy), (bx - 10, fy - 13), (bx + 10, fy - 13), (bx + 14, fy)])
        pygame.draw.polygon(s, (60, 64, 80), [(bx - 13, fy), (bx - 9, fy - 12), (bx + 9, fy - 12), (bx + 13, fy)])
        for i in range(-12, 13, 4):
            s.fill(HAZARD_Y, (bx + i, fy - 4, 2, 2))
            s.fill(INK, (bx + i + 2, fy - 4, 2, 2))
        s.fill((96, 100, 120), (bx - 9, fy - 12, 18, 1))
        sh, el, wr = arm.joints()
        # turntable
        pygame.draw.rect(s, INK, (bx - 9, fy - 19, 18, 7))
        pygame.draw.rect(s, ORANGE_DK, (bx - 8, fy - 18, 16, 5))
        s.fill(ORANGE, (bx - 8, fy - 18, 16, 2))
        self._link(s, sh, el, 11, ORANGE, ORANGE_HI, ORANGE_DK)
        self._link(s, el, wr, 8, ORANGE, ORANGE_HI, ORANGE_DK)
        self._joint(s, sh, 6)
        self._joint(s, el, 5)
        self._joint(s, wr, 3)
        # tiny OPRETO label on the upper link
        mx, my = (sh[0] + el[0]) / 2, (sh[1] + el[1]) / 2
        s.fill(INK, (int(mx) - 2, int(my) - 1, 5, 3))
        s.fill(WHITE, (int(mx) - 1, int(my), 3, 1))
        # caution beacon on the forearm near the wrist
        bxl = int(el[0] + (wr[0] - el[0]) * 0.55)
        byl = int(el[1] + (wr[1] - el[1]) * 0.55) - 5
        on = arm.light_on
        if on:
            pygame.draw.circle(s, (120, 80, 20), (bxl, byl), 5)
        pygame.draw.rect(s, INK, (bxl - 2, byl - 2, 5, 5))
        s.fill((255, 200, 40) if on else (120, 80, 30), (bxl - 1, byl - 1, 3, 3))
        if on:
            s.fill(WHITE, (bxl - 1, byl - 1, 1, 1))
        # base beacon too
        s.fill((255, 200, 40) if on else (120, 80, 30), (bx - 1, fy - 22, 3, 2))
        s.fill(INK, (bx - 2, fy - 20, 5, 1))
        # gripper fingers up to the platform
        pl = arm.platform
        gx, gy = int(wr[0]), int(wr[1])
        top = int(pl.y + pl.thickness)
        for fx in (gx - 5, gx + 4):
            s.fill(INK, (fx - 1, top, 3, gy - top + 1))
            s.fill(JOINT_HI, (fx, top, 1, gy - top))
        s.fill(INK, (gx - 6, gy - 1, 13, 3))
        s.fill(JOINT, (gx - 5, gy, 11, 1))

    def _draw_arm_platform(self, s, arm):
        pl = arm.platform
        x1, y, w = int(round(pl.x1)), int(round(pl.y)), int(pl.width)
        s.fill(INK, (x1 - 1, y - 1, w + 2, pl.thickness + 2))
        for i in range(0, w, 4):
            s.fill(HAZARD_Y if (i // 4) % 2 == 0 else INK, (x1 + i, y, min(4, w - i), 2))
        s.fill(ORANGE, (x1, y + 2, w, 2))
        s.fill(ORANGE_DK, (x1, y + 4, w, 1))
        s.fill(ORANGE_HI, (x1, y + 2, w, 1))

    # ============================================================== stations
    def _station_geom(self, st):
        sx = int(st.scan_x)
        return sx, sx - 20, sx + 20

    def _draw_station_back(self, s, st, t):
        sx, hx1, hx2 = self._station_geom(st)
        fy = level.FLOOR_Y
        # inspection belt section of the floor
        zx = 0 if st.side < 0 else W - level.STATION_ZONE - 6
        zw = level.STATION_ZONE + 6
        s.fill((40, 44, 60), (zx, fy, zw, 3))
        bx = zx + zw - 3 if st.side < 0 else zx
        for yy in range(fy, H, 4):
            s.fill(HAZARD_Y, (bx, yy, 3, 2))
            s.fill(INK, (bx, yy + 2, 3, 2))
        # trapdoor (reject chute)
        tx = sx - 7
        if st.trapdoor > 0:
            s.fill((8, 6, 10), (tx, fy, 14, H - fy))
            s.fill((120, 30, 30), (tx, fy, 14, 1))
            hinge_x = tx if st.side > 0 else tx + 13
            s.fill(STEEL, (hinge_x, fy, 1, 9))
        else:
            s.fill((80, 40, 40), (tx, fy, 14, 1))
            s.fill(INK, (tx, fy + 1, 14, 1))
            s.fill((150, 60, 50), (tx + 1, fy + 2, 12, 1))
        # accept exit doorway at the screen edge
        ex = 0 if st.side < 0 else W - 4
        s.fill((10, 30, 20), (ex, fy - 22, 4, 22))
        lit = st.result == "pass" and st.flash > 0
        s.fill(GREEN if lit else (40, 120, 60), (ex if st.side > 0 else ex + 3, fy - 22, 1, 22))
        s.fill(GREEN if lit else (40, 120, 60), (ex, fy - 23, 4, 1))

    def _draw_station_front(self, s, st, t):
        sx, hx1, hx2 = self._station_geom(st)
        top = level.T1_Y + 6
        fy = level.FLOOR_Y
        # scan beam
        if st.state == "scan" or (st.state == "result" and st.flash > 0):
            if st.state == "scan":
                col = (90, 220, 255, 70)
            elif st.result == "pass":
                col = (90, 255, 120, 90)
            else:
                col = (255, 70, 70, 90)
            ov = self.overlay
            ov.fill((0, 0, 0, 0), (hx1 - 4, top, 48, fy - top))
            pygame.draw.polygon(ov, col, [(sx - 2, top + 12), (sx + 2, top + 12), (sx + 11, fy), (sx - 11, fy)])
            if st.state == "scan":
                ly = int(top + 13 + (fy - top - 13) * (0.5 + 0.5 * math.sin(t * 14)))
                w = int(4 + 18 * (ly - top - 12) / (fy - top - 12))
                ov.fill((200, 250, 255, 200), (sx - w // 2, ly, w, 1))
            s.blit(ov, (hx1 - 4, top), (hx1 - 4, top, 48, fy - top))
        # ejector plunger
        if st.ejector > 0:
            ext = int(16 * min(1.0, (0.35 - st.ejector) / 0.12 + 0.2))
            s.fill(INK, (sx - 2, top + 10, 5, ext))
            s.fill(STEEL_HI, (sx - 1, top + 10, 3, ext))
            s.fill(RED, (sx - 3, top + 10 + ext, 7, 2))
        # mounting bracket + housing
        s.fill(INK, (sx - 3, top, 7, 2))
        s.fill(INK, (hx1, top + 1, hx2 - hx1, 10))
        s.fill((44, 48, 64), (hx1 + 1, top + 2, hx2 - hx1 - 2, 8))
        s.fill((70, 76, 96), (hx1 + 1, top + 2, hx2 - hx1 - 2, 1))
        font.small.draw(s, "KINOPTYX", sx + 1, top + 4, WHITE, align="center")
        # status lights
        res_flash = st.flash > 0 and int(st.flash * 10) % 2 == 0
        g_on = st.result == "pass" and res_flash
        r_on = st.result == "reject" and res_flash
        s.fill(GREEN if g_on else (30, 80, 40), (hx1 + 1, top + 3, 2, 2))
        s.fill(RED if r_on else (90, 30, 30), (hx2 - 3, top + 3, 2, 2))
        # lens
        lens_col = CYAN if st.state == "scan" else (60, 110, 170)
        if g_on:
            lens_col = GREEN
        if r_on:
            lens_col = RED
        s.fill(INK, (sx - 4, top + 10, 9, 4))
        s.fill(STEEL, (sx - 3, top + 10, 7, 3))
        s.fill(lens_col, (sx - 2, top + 11, 5, 2))
        s.fill(WHITE, (sx - 1, top + 11, 1, 1))

    # ============================================================== feeders
    def _feeder_rect(self, f):
        fw = level.FEEDER_W
        x = 0 if f.side < 0 else W - fw
        return x, level.HUD_H + 2, fw, level.T4_Y - level.HUD_H - 2

    def _draw_feeder_back(self, s, f):
        x, y, w, h = self._feeder_rect(f)
        s.fill((10, 10, 16), (x, y + 12, w, h - 12))

    def _draw_feeder_front(self, s, f, t):
        x, y, w, h = self._feeder_rect(f)
        mouth_x = x + w - 9 if f.side < 0 else x
        mouth_y, mouth_h = y + 13, h - 13
        body = (90, 98, 120)
        # housing body except the mouth
        s.fill(INK, (x, y, w, 13))
        s.fill(body, (x + 1, y + 1, w - 2, 11))
        s.fill(STEEL_HI, (x + 1, y + 1, w - 2, 1))
        for i in range(0, w - 2, 4):
            s.fill(HAZARD_Y if (i // 4) % 2 == 0 else INK, (x + 1 + i, y + 9, min(4, w - 2 - i), 2))
        body_x = x if f.side < 0 else x + 9
        s.fill(INK, (body_x, mouth_y, w - 9, mouth_h))
        s.fill((70, 76, 96), (body_x + 1, mouth_y, w - 11, mouth_h))
        font.small.draw(s, "OPRETO", x + w // 2, y + 2, ORANGE_HI, align="center")
        # input chute pipe disappearing off the top of the screen edge
        # mouth frame and roll-up shutter
        s.fill(INK, (mouth_x, mouth_y - 1, 9, 1))
        shutter = 1.0
        if f.open > 0:
            k = f.open
            shutter = 0.0 if 0.25 < k < 1.0 else (1.0 - k / 0.25 if k <= 0.25 else 1.0 - (1.2 - k) / 0.2)
            shutter = max(0.0, min(1.0, shutter))
        sh = int(mouth_h * shutter)
        for yy in range(0, sh, 2):
            s.fill((140, 146, 160), (mouth_x, mouth_y + yy, 9, 1))
            s.fill((90, 94, 108), (mouth_x, mouth_y + yy + 1, 9, 1))
        # status light on the housing
        lit = f.open > 0 and int(t * 10) % 2 == 0
        lx = x + w - 4 if f.side < 0 else x + 2
        s.fill(YELLOW if lit else (90, 70, 30), (lx, y + 5, 2, 2))

    # =============================================================== compass
    def _draw_compass(self, s, c, t):
        x1, y1 = int(c.x1), int(c.top)
        w, h = int(c.x2 - c.x1), int(c.bottom - c.top)
        if c.bump > 0:
            y1 -= 2 if c.bump > 0.09 else 1
        active = c.charges > 0
        face = (40, 120, 220) if active else (54, 60, 80)
        if c.flash > 0 and int(c.flash * 20) % 2 == 0:
            face = (200, 250, 255)
        glow = 0.5 + 0.5 * math.sin(t * 4)
        if active:
            ring = _lerp((40, 160, 255), (160, 240, 255), glow)
            pygame.draw.rect(s, ring, (x1 - 1, y1 - 1, w + 2, h + 2), 1)
        s.fill(INK, (x1, y1, w, h))
        s.fill(face, (x1 + 1, y1 + 1, w - 2, h - 2))
        s.fill(_lerp(face, WHITE, 0.4), (x1 + 1, y1 + 1, w - 2, 1))
        cx, cy = x1 + w // 2, y1 + h // 2
        pygame.draw.circle(s, INK, (cx, cy), 6)
        pygame.draw.circle(s, (230, 240, 255) if active else (110, 120, 140), (cx, cy), 5)
        ang = math.sin(t * 1.7) * 0.6 + (t * 6 if c.flash > 0 else 0)
        nx, ny = math.sin(ang), -math.cos(ang)
        pygame.draw.line(s, RED if active else (120, 90, 90), (cx, cy), (cx + nx * 4, cy + ny * 4))
        pygame.draw.line(s, (60, 70, 90), (cx, cy), (cx - nx * 4, cy - ny * 4))
        s.fill(INK, (cx, cy, 1, 1))
        # label + charge pips
        font.small.draw(s, "AI COMPASS", cx + 1, y1 - 8, CYAN if active else (110, 120, 140), align="center",
                        outline=INK)
        for i in range(3):
            on = i < c.charges
            s.fill(INK, (cx - 7 + i * 5, y1 + h + 1, 4, 3))
            s.fill(CYAN if on else (50, 60, 80), (cx - 6 + i * 5, y1 + h + 2, 2, 1))

    # ================================================================ robots
    def _draw_robot(self, s, b, t):
        frame = int(b.anim * (8 if not b.good else 6)) % 2
        facing = b.dir
        ox = oy = 0
        if b.state == "walk":
            if b.good:
                oy = -1 if frame else 0
            else:
                k = int(t * 30 + b.id * 7)
                ox = (k * 13 % 3) - 1 if (k // 3) % 2 == 0 else 0
        surf = self.sprites.robot(b.kind, b.good, frame, facing)
        if b.state == "inspect":
            surf = self.sprites.robot(b.kind, b.good, 0, facing)
        if b.transform_timer > 0:
            from config import BOT_TRANSFORM_TIME as TT
            k = 1.0 - b.transform_timer / TT
            if k < 0.3:
                old = self.sprites.robot(b.kind, not b.good, 0, facing)
                sw, sh = old.get_size()
                surf = pygame.transform.scale(old, (int(sw * 1.3), max(4, int(sh * 0.6))))
            elif k < 0.5:
                surf = self.sprites.robot_flash[b.kind]
            elif k < 0.7:
                sw, sh = surf.get_size()
                surf = pygame.transform.scale(surf, (int(sw * 0.85), int(sh * 1.15)))
        if b.state == "reject":
            surf = pygame.transform.rotate(self.sprites.robot(b.kind, b.good, 0, facing),
                                           (int(b.tumble * 10) % 4) * 90)
        sw, sh = surf.get_size()
        x = int(round(b.x - sw / 2)) + ox
        y = int(round(b.y - sh)) + oy
        s.blit(surf, (x, y))
        wrap_ok = b.state in ("walk", "fall") and not (b.ground is not None and b.ground.kind == "floor")
        if wrap_ok and (x < 0 or x + sw > W):
            s.blit(surf, (x + W if x < 0 else x - W, y))
        if b.state == "exit" and int(t * 4) % 2 == 0:
            s.blit(self.sprites.heart, (int(b.x) - 2, int(b.y - b.h - 9)))

    # =============================================================== players
    def _draw_player(self, s, p, t):
        if p.stun > 0:
            frame = "stun"
        elif p.swing > 0:
            frame = "swing"
        elif p.ground is None:
            frame = "jump"
        elif abs(p.vx) > 8:
            frame = "walk1" if int(p.anim * 10) % 2 == 0 else "walk2"
        else:
            frame = "idle"
        surf = self.sprites.mech(p.slot, frame, p.facing)
        sw, sh = surf.get_size()
        if p.land_timer > 0 and frame == "idle":
            surf = pygame.transform.scale(surf, (sw + 2, sh - 2))
            sw, sh = surf.get_size()
        x = int(round(p.x - sw / 2)) + (1 if p.facing < 0 else -1)
        y = int(round(p.y - sh))
        blink = p.invuln > 0 and p.stun <= 0 and int(t * 16) % 2 == 0
        if p.spawn_timer > 0:
            k = p.spawn_timer / 0.6
            beam = pygame.Surface((10, int(p.y) - 11), pygame.SRCALPHA)
            beam.fill((255, 255, 200, int(120 * k)))
            s.blit(beam, (int(p.x) - 5, 11))
        if not blink:
            s.blit(surf, (x, y))
            if x < 0:
                s.blit(surf, (x + W, y))
            elif x + sw > W:
                s.blit(surf, (x - W, y))
        if p.stun > 0:
            for i in range(3):
                a = t * 8 + i * 2.1
                s.blit(self.sprites.star, (int(p.x + math.cos(a) * 7) - 2, int(p.top - 3 + math.sin(a) * 2) - 2))
        # player marker
        col = P_COLORS[p.slot]
        font.small.draw(s, "P%d" % (p.slot + 1), int(p.x) + 1, int(p.top) - 8, col, align="center", outline=INK)
        warn = config.PLAYER_IDLE_TIMEOUT - p.idle
        if warn < 10:
            if int(t * 4) % 2 == 0:
                font.small.draw(s, "STILL THERE? %d" % max(0, math.ceil(warn)), int(p.x) + 1, int(p.top) - 15,
                                YELLOW, align="center", outline=INK)

    # =============================================================== effects
    def _draw_effects(self, s, world, t):
        fx = world.effects
        for pu in fx.pulses:
            r = int(pu.radius)
            if r > 1:
                k = pu.life / pu.max_life
                col = _lerp((30, 60, 120), pu.color, k)
                pygame.draw.circle(s, col, (int(pu.x), int(pu.y)), r, 3)
                if r > 6:
                    pygame.draw.circle(s, _lerp((20, 30, 60), WHITE, k), (int(pu.x), int(pu.y)), r - 4, 1)
        for p in fx.particles:
            s.fill(p.color, (int(p.x), int(p.y), p.size, p.size))
        for g in fx.ghosts:
            surf = self.sprites.mech_white[0]
            k = max(0.0, min(1.0, g.life / 0.6))
            surf.set_alpha(int(170 * k))
            s.blit(surf, (int(g.x) - 8, int(g.y) - 16))
            surf.set_alpha(None)
        for pu in fx.popups:
            k = pu.life / pu.max_life
            if k < 0.25 and int(t * 20) % 2 == 0:
                continue
            f = font.big if pu.big else font.small
            x = max(f.text_width(pu.text) // 2 + 2, min(W - f.text_width(pu.text) // 2 - 2, int(pu.x)))
            f.draw(s, pu.text, x, int(pu.y), pu.color, align="center", outline=INK)

    def _draw_banner(self, s, world, t):
        b = world.effects.banner
        if not b:
            return
        text, sub, life, max_life = b
        k = 1.0 - life / max_life
        scale = 3 if k > 0.06 else 2
        col = CYAN if int(t * 12) % 2 == 0 else WHITE
        y = 86
        font.big.draw(s, text, W // 2, y, col, scale=scale, outline=INK, align="center")
        if sub:
            font.big.draw(s, sub, W // 2, y + 26, YELLOW, scale=1, outline=INK, align="center")

    # =================================================================== HUD
    def _draw_hud(self, s, world, t):
        s.fill((8, 8, 14), (0, 0, W, level.HUD_H))
        s.fill((70, 60, 90), (0, level.HUD_H, W, 1))
        blink = int(t * 2.5) % 2 == 0
        for slot in (0, 1):
            p = world.players[slot]
            col = P_COLORS[slot]
            x = 3 if slot == 0 else W - 3
            align = "left" if slot == 0 else "right"
            if p.active:
                warn = config.PLAYER_IDLE_TIMEOUT - p.idle
                label = "P%d PLAYING" % (slot + 1) if warn >= 10 else "P%d IDLE %d" % (slot + 1, math.ceil(warn))
                font.big.draw(s, label, x, 2, col, align=align)
            elif blink:
                font.big.draw(s, "P%d PRESS START" % (slot + 1), x, 2, col, align=align)
            else:
                font.big.draw(s, "P%d" % (slot + 1), x, 2, col, align=align)
        if world.mode == "play":
            font.big.draw(s, "SCORE %06d" % world.score, 104, 2, WHITE)
        else:
            font.big.draw(s, "FREE PLAY", 110, 2, (200, 200, 220))
        x = 194
        font.big.draw(s, "AI", x, 2, CYAN)
        for i in range(3):
            icon = self.sprites.compass_icon if i < world.compass.charges else self.sprites.compass_icon_empty
            s.blit(icon, (x + 13 + i * 11, 1))

    def _draw_join_prompts(self, s, world, t):
        if int(t * 2.5) % 2:
            return
        for slot in (0, 1):
            p = world.players[slot]
            if p.active:
                continue
            x, y = config.PLAYER_SPAWN[slot]
            font.small.draw(s, "P%d PRESS START" % (slot + 1), int(x), int(y) - 20, P_COLORS[slot],
                            align="center", outline=INK)

    # =============================================================== attract
    def _draw_attract(self, s, world, t):
        x1, y1, x2, y2 = level.ATTRACT_PANEL
        if getattr(self, "_panel", None) is None:
            self._panel = pygame.Surface((x2 - x1, y2 - y1), pygame.SRCALPHA)
            self._panel.fill((8, 10, 24, 215))
        s.blit(self._panel, (x1, y1))
        pygame.draw.rect(s, ORANGE, (x1, y1, x2 - x1, y2 - y1), 1)
        pygame.draw.rect(s, ORANGE_DK, (x1 + 2, y1 + 2, x2 - x1 - 4, y2 - y1 - 4), 1)
        cx = (x1 + x2) // 2
        page = int(world.attract_time / 4.0) % 4
        sp = self.sprites
        if page == 0:
            ts = self.title_surf_big
            s.blit(ts, (cx - ts.get_width() // 2, y1 + 8))
            font.small.draw(s, "A FACTORY FULL OF MISCHIEVOUS ROBOTS", cx, y1 + 36, (200, 210, 240), align="center")
            font.small.draw(s, "1 OR 2 PLAYERS - TEAM UP!", cx, y1 + 45, CYAN, align="center")
        elif page == 1:
            font.big.draw(s, "JUMP ON BAD BOTS", cx, y1 + 7, YELLOW, align="center")
            font.big.draw(s, "TO FIX THEM!", cx, y1 + 17, YELLOW, align="center")
            kinds = ("gear", "bolt", "box")
            for i, kind in enumerate(kinds):
                bx = cx - 66 + i * 50
                f = int(t * 6) % 2
                bad = sp.robot(kind, False, f, 1)
                good = sp.robot(kind, True, f, 1)
                s.blit(bad, (bx - bad.get_width() // 2, y1 + 50 - bad.get_height()))
                font.small.draw(s, ">", bx + 13, y1 + 40, WHITE, align="center")
                s.blit(good, (bx + 26 - good.get_width() // 2, y1 + 50 - good.get_height()))
            font.small.draw(s, "BAD", cx - 66, y1 + 52, RED, align="center")
            font.small.draw(s, "GOOD", cx - 40, y1 + 52, GREEN, align="center")
        elif page == 2:
            font.big.draw(s, "KINOPTYX CAMERAS", cx, y1 + 7, CYAN, align="center")
            font.big.draw(s, "INSPECT EVERY BOT", cx, y1 + 17, CYAN, align="center")
            f = int(t * 6) % 2
            g = sp.robot("gear", True, f, 1)
            r = sp.robot("box", False, f, 1)
            s.blit(g, (cx - 48 - g.get_width() // 2, y1 + 48 - g.get_height()))
            font.small.draw(s, "GOOD = PASS +100", cx - 48, y1 + 51, GREEN, align="center")
            s.blit(r, (cx + 48 - r.get_width() // 2, y1 + 48 - r.get_height()))
            font.small.draw(s, "BAD = REJECT", cx + 48, y1 + 51, RED, align="center")
        else:
            font.big.draw(s, "HIT THE AI COMPASS", cx, y1 + 7, CYAN, align="center")
            font.big.draw(s, "TO FIX EVERY BOT!", cx, y1 + 17, CYAN, align="center")
            icon = pygame.transform.scale(sp.compass_icon, (18, 18))
            s.blit(icon, (cx - 9, y1 + 30))
            font.small.draw(s, "JUMP UP UNDER THE BLOCK", cx, y1 + 52, (200, 210, 240), align="center")
        if int(t * 2.5) % 2 == 0:
            font.big.draw(s, "PRESS START", cx, y2 - 14, WHITE, align="center", outline=ORANGE_DK)
        font.small.draw(s, config.ATTRACT_FOOTER, W // 2, H - 7, (160, 170, 200), align="center", outline=INK)
