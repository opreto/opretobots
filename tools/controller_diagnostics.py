#!/usr/bin/env python3
"""Controller diagnostics and mapping wizard for Opreto Bots.

    python3 tools/controller_diagnostics.py            # windowed
    python3 tools/controller_diagnostics.py --fullscreen

Shows every connected controller (hot-plug aware) with live buttons, hats
and axes, plus how Opreto Bots currently interprets it (LEFT/RIGHT/JUMP/START).

Press M on the keyboard to start the mapping wizard: the next controller to
press a button is mapped by prompting for A, B, START, SELECT, LEFT, RIGHT.
The result is saved to controller_map.json (keyed by controller name) and
picked up the next time the game starts.  Press Esc to quit.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame  # noqa: E402

import config  # noqa: E402
import font  # noqa: E402
from input_manager import Device, load_mappings  # noqa: E402

W, H = 384, 216
STEPS = ["A", "B", "START", "SELECT", "LEFT", "RIGHT"]


class Wizard:
    def __init__(self):
        self.active = False
        self.device = None
        self.step = 0
        self.result = {}
        self.message = ""

    def start(self):
        self.active = True
        self.device = None
        self.step = 0
        self.result = {"jump": [], "start": [], "select": [], "dpad_left": [], "dpad_right": [],
                        "axis_x": [], "axis_invert": False, "hat": 0}
        self.message = "PRESS A ON THE CONTROLLER TO MAP"

    @property
    def prompt(self):
        return STEPS[self.step] if self.active and self.step < len(STEPS) else ""

    def feed(self, dev, kind, index, value=0):
        """Record one input.  Returns True when finished."""
        if self.device is None:
            self.device = dev
        if dev is not self.device:
            return False
        p = self.prompt
        r = self.result
        if p in ("A", "B") and kind == "button":
            if index not in r["jump"]:
                r["jump"].append(index)
        elif p == "START" and kind == "button":
            r["start"] = [index]
        elif p == "SELECT" and kind == "button":
            r["select"] = [index]
        elif p in ("LEFT", "RIGHT"):
            if kind == "hat":
                r["hat"] = index
            elif kind == "axis":
                if index not in r["axis_x"]:
                    r["axis_x"].append(index)
                if p == "LEFT":
                    r["axis_invert"] = value > 0
            elif kind == "button":
                r["dpad_left" if p == "LEFT" else "dpad_right"].append(index)
            else:
                return False
        else:
            return False
        self.step += 1
        if self.step >= len(STEPS):
            self.active = False
            return True
        return False


def save_profile(name, profile):
    path = config.CONTROLLER_MAP_FILE
    data = {"default": {}, "devices": {}}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    data.setdefault("devices", {})[name] = profile
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fullscreen", action="store_true")
    args = ap.parse_args()
    pygame.init()
    if args.fullscreen:
        screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.FULLSCREEN)
        dest = None
    else:
        screen = pygame.display.set_mode((W * 3, H * 3))
        dest = screen
    pygame.display.set_caption("Opreto Bots - controller diagnostics")
    surf = pygame.Surface((W, H))
    mappings = load_mappings(config.CONTROLLER_MAP_FILE)
    devices = {}
    order = []
    wizard = Wizard()
    clock = pygame.time.Clock()
    status = "PRESS M TO MAP A CONTROLLER - ESC TO QUIT"

    def mapping_for(name):
        m = dict(mappings["default"])
        m.update(mappings["devices"].get(name, {}))
        return m

    def add(index):
        js = pygame.joystick.Joystick(index)
        js.init()
        iid = js.get_instance_id()
        if iid not in devices:
            devices[iid] = Device(js, mapping_for(js.get_name()))
            order.append(iid)
            print("connected: index=%d instance=%d name=%r guid=%s buttons=%d hats=%d axes=%d" % (
                index, iid, js.get_name(), js.get_guid(), js.get_numbuttons(), js.get_numhats(), js.get_numaxes()))

    for i in range(pygame.joystick.get_count()):
        add(i)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_m:
                    wizard.start()
            elif e.type == pygame.JOYDEVICEADDED:
                add(e.device_index)
            elif e.type == pygame.JOYDEVICEREMOVED:
                devices.pop(e.instance_id, None)
                if e.instance_id in order:
                    order.remove(e.instance_id)
                print("disconnected: instance=%d" % e.instance_id)
            else:
                dev = devices.get(getattr(e, "instance_id", None))
                if dev is None:
                    continue
                done = False
                if e.type == pygame.JOYBUTTONDOWN:
                    dev.buttons.add(e.button)
                    print("%s: button %d down" % (dev.name, e.button))
                    if wizard.active:
                        done = wizard.feed(dev, "button", e.button)
                elif e.type == pygame.JOYBUTTONUP:
                    dev.buttons.discard(e.button)
                elif e.type == pygame.JOYHATMOTION:
                    dev.hat_x = int(e.value[0])
                    print("%s: hat %d = %s" % (dev.name, e.hat, e.value))
                    if wizard.active and e.value[0] != 0:
                        done = wizard.feed(dev, "hat", e.hat)
                elif e.type == pygame.JOYAXISMOTION:
                    prev = dev.axis.get(e.axis, 0.0)
                    dev.axis[e.axis] = e.value
                    if abs(e.value) > 0.5 and abs(prev) <= 0.5:
                        print("%s: axis %d = %.2f" % (dev.name, e.axis, e.value))
                        if wizard.active:
                            done = wizard.feed(dev, "axis", e.axis, e.value)
                if done:
                    prof = wizard.result
                    path = save_profile(dev.name, prof)
                    mappings["devices"][dev.name] = prof
                    for d in devices.values():
                        if d.name == dev.name:
                            d.mapping = mapping_for(d.name)
                    status = "SAVED MAPPING FOR %s" % dev.name.upper()[:30]
                    print("saved profile for %r to %s: %s" % (dev.name, path, prof))

        surf.fill((14, 16, 30))
        font.big.draw(surf, "CONTROLLER DIAGNOSTICS", W // 2, 4, (255, 196, 60), align="center")
        font.small.draw(surf, status, W // 2, 14, (150, 200, 255), align="center")
        if wizard.active:
            who = wizard.device.name.upper()[:28] if wizard.device else "ANY CONTROLLER"
            font.big.draw(surf, "PRESS %s" % wizard.prompt, W // 2, 190, (255, 255, 255), align="center",
                          outline=(120, 40, 10))
            font.small.draw(surf, who, W // 2, 202, (200, 200, 200), align="center")
        y = 26
        if not order:
            font.big.draw(surf, "NO CONTROLLERS CONNECTED", W // 2, 90, (255, 120, 120), align="center")
        for slot_guess, iid in enumerate(order[:4]):
            dev = devices[iid]
            js = dev.joystick
            col = (110, 150, 255) if slot_guess == 0 else (255, 110, 110) if slot_guess == 1 else (180, 180, 180)
            label = "P%d" % (slot_guess + 1) if slot_guess < 2 else "WAIT"
            font.small.draw(surf, "%s  ID %d  %s" % (label, iid, dev.name.upper()[:50]), 4, y, col)
            y += 8
            bx = 4
            for b in range(js.get_numbuttons()):
                on = b in dev.buttons
                pygame.draw.rect(surf, (255, 220, 80) if on else (50, 54, 70), (bx, y, 13, 9))
                font.small.draw(surf, str(b), bx + 7, y + 2, (20, 16, 28) if on else (160, 160, 170),
                                align="center")
                bx += 15
            y += 12
            ax_txt = " ".join("A%d:%+.2f" % (a, dev.axis.get(a, 0.0)) for a in range(min(6, js.get_numaxes())))
            hats = " ".join("H%d:%s" % (h, js.get_hat(h)) for h in range(js.get_numhats()))
            font.small.draw(surf, (ax_txt + "  " + hats).upper(), 4, y, (170, 180, 200))
            y += 8
            d = dev.direction()
            roles = ["LEFT" if d < 0 else "RIGHT" if d > 0 else "", "JUMP" if dev.jump_held() else ""]
            roles += [dev.button_role(b).upper() for b in dev.buttons if dev.button_role(b) not in (None, "jump")]
            font.small.draw(surf, "GAME SEES: " + (" ".join(r for r in roles if r) or "-"), 4, y, (120, 255, 140))
            y += 12
        if dest is None:
            screen.blit(surf, (0, 0))
        else:
            pygame.transform.scale(surf, dest.get_size(), dest)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
