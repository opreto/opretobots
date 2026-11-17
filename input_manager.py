"""USB controller input and player-slot assignment.

* Devices are tracked by SDL joystick *instance id*, so two identical
  controllers (same name, same GUID) still work independently.
* Hot-plugging: a newly connected controller takes the first free player
  slot; disconnecting one frees its slot and deactivates that player only.
* D-pad may be reported as a hat, as axes, or as buttons - all are supported.
* Button numbers are never assumed: by default every button except the
  configured Select buttons jumps, and any button joins an idle slot.
  ``tools/controller_diagnostics.py`` writes ``controller_map.json`` to pin
  exact mappings per controller name.
"""

import json
import logging
import os

import pygame

import config
from player import Controls

log = logging.getLogger("opretobots.input")

DEFAULT_MAPPING = {
    "jump": None,            # None = every button that is not start/select
    "start": [9, 7],
    "select": [8, 6],
    "dpad_left": [],         # buttons that act as D-pad left/right
    "dpad_right": [],
    "axis_x": [0],           # axes that carry horizontal D-pad
    "axis_invert": False,
    "hat": 0,
}


def load_mappings(path):
    data = {"default": dict(DEFAULT_MAPPING), "devices": {}}
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                user = json.load(fh)
            if isinstance(user.get("default"), dict):
                data["default"].update(user["default"])
            if isinstance(user.get("devices"), dict):
                data["devices"].update(user["devices"])
            log.info("loaded controller map %s (%d device profiles)", path, len(data["devices"]))
        except Exception as exc:
            log.error("could not read controller map %s: %s", path, exc)
    return data


class Device:
    def __init__(self, joystick, mapping):
        self.joystick = joystick
        self.instance_id = joystick.get_instance_id()
        self.name = joystick.get_name()
        self.mapping = mapping
        self.slot = None
        self.buttons = set()
        self.hat_x = 0
        self.axis = {}

    def button_role(self, button):
        m = self.mapping
        if button in m.get("dpad_left", []) or button in m.get("dpad_right", []):
            return "dpad"
        if button in (m.get("start") or []):
            return "start"
        if button in (m.get("select") or []):
            return "select"
        jump = m.get("jump")
        if jump is None or button in jump:
            return "jump"
        return None

    def direction(self):
        m = self.mapping
        d = self.hat_x
        if not d:
            for ax in m.get("axis_x", []):
                v = self.axis.get(ax, 0.0)
                if m.get("axis_invert"):
                    v = -v
                if v <= -config.AXIS_DEADZONE:
                    d = -1
                    break
                if v >= config.AXIS_DEADZONE:
                    d = 1
                    break
        if not d:
            left = any(b in self.buttons for b in m.get("dpad_left", []))
            right = any(b in self.buttons for b in m.get("dpad_right", []))
            d = (1 if right else 0) - (1 if left else 0)
        return d

    def jump_held(self):
        return any(self.button_role(b) == "jump" for b in self.buttons)


class SlotEdges:
    __slots__ = ("jump", "join", "activity")

    def __init__(self):
        self.jump = False
        self.join = False
        self.activity = False


KEYS = [
    {"left": (pygame.K_LEFT,), "right": (pygame.K_RIGHT,), "jump": (pygame.K_z, pygame.K_x, pygame.K_UP),
     "start": (pygame.K_1, pygame.K_RETURN)},
    {"left": (pygame.K_a,), "right": (pygame.K_d,), "jump": (pygame.K_g, pygame.K_h, pygame.K_w),
     "start": (pygame.K_2,)},
]


class InputManager:
    def __init__(self, mapping_path=None, num_slots=2):
        self.mappings = load_mappings(mapping_path or config.CONTROLLER_MAP_FILE)
        self.devices = {}               # instance_id -> Device
        self.slots = [None] * num_slots  # instance_id per slot
        self.waiting = []                # connected devices without a slot
        self.edges = [SlotEdges() for _ in range(num_slots)]
        self.disconnected = []           # slots that lost their controller
        self.keys_down = set()
        self.keyboard_enabled = config.KEYBOARD_PLAYERS
        self.admin_exit = False

    # ------------------------------------------------------------ devices
    def mapping_for(self, name):
        m = dict(self.mappings["default"])
        m.update(self.mappings["devices"].get(name, {}))
        return m

    def scan_existing(self):
        for i in range(pygame.joystick.get_count()):
            self._add_device(i)

    def _add_device(self, device_index):
        try:
            js = pygame.joystick.Joystick(device_index)
            js.init()
        except pygame.error as exc:
            log.warning("could not open joystick %s: %s", device_index, exc)
            return
        iid = js.get_instance_id()
        if iid in self.devices:
            return
        dev = Device(js, self.mapping_for(js.get_name()))
        self.devices[iid] = dev
        log.info("controller connected: %r instance=%s buttons=%d hats=%d axes=%d", dev.name, iid,
                 js.get_numbuttons(), js.get_numhats(), js.get_numaxes())
        self._assign(dev)

    def _assign(self, dev):
        for slot, owner in enumerate(self.slots):
            if owner is None:
                self.slots[slot] = dev.instance_id
                dev.slot = slot
                log.info("controller %s -> player %d", dev.instance_id, slot + 1)
                return
        self.waiting.append(dev.instance_id)

    def _remove_device(self, instance_id):
        dev = self.devices.pop(instance_id, None)
        if dev is None:
            return
        log.info("controller disconnected: %r instance=%s", dev.name, instance_id)
        if instance_id in self.waiting:
            self.waiting.remove(instance_id)
        if dev.slot is not None:
            slot = dev.slot
            self.slots[slot] = None
            self.disconnected.append(slot)
            # hand the free slot to a controller that was waiting for one
            while self.waiting:
                nxt = self.devices.get(self.waiting.pop(0))
                if nxt is not None:
                    self.slots[slot] = nxt.instance_id
                    nxt.slot = slot
                    break

    def slot_connected(self, slot):
        return self.slots[slot] is not None

    def slot_name(self, slot):
        iid = self.slots[slot]
        return self.devices[iid].name if iid is not None and iid in self.devices else None

    # ------------------------------------------------------------- events
    def handle_event(self, e):
        t = e.type
        if t == pygame.JOYDEVICEADDED:
            self._add_device(e.device_index)
        elif t == pygame.JOYDEVICEREMOVED:
            self._remove_device(e.instance_id)
        elif t in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
            dev = self.devices.get(getattr(e, "instance_id", None))
            if dev is None:
                return
            if t == pygame.JOYBUTTONDOWN:
                dev.buttons.add(e.button)
                self._button_edge(dev, dev.button_role(e.button))
            else:
                dev.buttons.discard(e.button)
        elif t == pygame.JOYHATMOTION:
            dev = self.devices.get(getattr(e, "instance_id", None))
            if dev is not None and e.hat == dev.mapping.get("hat", 0):
                dev.hat_x = int(e.value[0])
                if dev.hat_x and dev.slot is not None:
                    self.edges[dev.slot].activity = True
        elif t == pygame.JOYAXISMOTION:
            dev = self.devices.get(getattr(e, "instance_id", None))
            if dev is not None:
                old = dev.direction()
                dev.axis[e.axis] = e.value
                if dev.direction() != old and dev.direction() and dev.slot is not None:
                    self.edges[dev.slot].activity = True
        elif t == pygame.KEYDOWN:
            self.keys_down.add(e.key)
            mods = pygame.key.get_mods()
            if e.key == pygame.K_q and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
                self.admin_exit = True
            if self.keyboard_enabled:
                for slot, km in enumerate(KEYS):
                    if e.key in km["jump"]:
                        self._slot_edge(slot, "jump")
                    elif e.key in km["start"]:
                        self._slot_edge(slot, "start")
                    elif e.key in km["left"] or e.key in km["right"]:
                        self.edges[slot].activity = True
        elif t == pygame.KEYUP:
            self.keys_down.discard(e.key)

    def _button_edge(self, dev, role):
        if dev.slot is None:
            return
        if role in ("dpad",):
            self.edges[dev.slot].activity = True
            return
        self._slot_edge(dev.slot, role)

    def _slot_edge(self, slot, role):
        ed = self.edges[slot]
        ed.activity = True
        if role == "jump":
            ed.jump = True
            if config.JOIN_WITH_ANY_BUTTON:
                ed.join = True
        elif role == "start":
            ed.join = True
        elif role is not None and config.JOIN_WITH_ANY_BUTTON:
            ed.join = True

    # ------------------------------------------------------------- polling
    def poll(self):
        """Controls for every slot since the last poll (edge flags are consumed)."""
        out = []
        for slot in range(len(self.slots)):
            d = 0
            held = False
            iid = self.slots[slot]
            dev = self.devices.get(iid) if iid is not None else None
            if dev is not None:
                d = dev.direction()
                held = dev.jump_held()
            if self.keyboard_enabled:
                km = KEYS[slot]
                kl = any(k in self.keys_down for k in km["left"])
                kr = any(k in self.keys_down for k in km["right"])
                if kl or kr:
                    d = d or ((1 if kr else 0) - (1 if kl else 0))
                held = held or any(k in self.keys_down for k in km["jump"])
            ed = self.edges[slot]
            out.append(Controls(dir=d, jump_held=held, jump_pressed=ed.jump, join_pressed=ed.join,
                                activity=ed.activity or d != 0))
            self.edges[slot] = SlotEdges()
        return out

    def take_disconnected(self):
        d, self.disconnected = self.disconnected, []
        return d
