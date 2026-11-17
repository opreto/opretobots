"""Controller handling with fake joystick objects (no hardware needed)."""
import pygame
import pytest

import input_manager
from input_manager import InputManager


class FakeJoy:
    _next = 100

    def __init__(self, name="USB Gamepad"):
        FakeJoy._next += 1
        self.iid = FakeJoy._next
        self.name = name

    def init(self):
        pass

    def get_instance_id(self):
        return self.iid

    def get_name(self):
        return self.name

    def get_numbuttons(self):
        return 10

    def get_numhats(self):
        return 0

    def get_numaxes(self):
        return 2


@pytest.fixture
def im(monkeypatch, tmp_path):
    pygame.init()
    joys = {}

    def fake_joystick(index):
        return joys[index]

    monkeypatch.setattr(input_manager.pygame.joystick, "Joystick", fake_joystick)
    m = InputManager(mapping_path=str(tmp_path / "none.json"))
    m.keyboard_enabled = False
    m._joys = joys
    return m


def plug(im, index, name="USB Gamepad"):
    j = FakeJoy(name)
    im._joys[index] = j
    im.handle_event(pygame.event.Event(pygame.JOYDEVICEADDED, device_index=index))
    return j


def ev(t, **kw):
    return pygame.event.Event(t, **kw)


def test_identical_controllers_are_independent(im):
    a = plug(im, 0)
    b = plug(im, 1)
    assert im.slots == [a.iid, b.iid]
    im.handle_event(ev(pygame.JOYAXISMOTION, instance_id=b.iid, axis=0, value=1.0))
    im.handle_event(ev(pygame.JOYBUTTONDOWN, instance_id=a.iid, button=1))
    c = im.poll()
    assert c[0].jump_pressed and c[0].dir == 0
    assert c[1].dir == 1 and not c[1].jump_pressed


def test_any_button_joins_and_start_joins(im):
    a = plug(im, 0)
    im.handle_event(ev(pygame.JOYBUTTONDOWN, instance_id=a.iid, button=9))
    assert im.poll()[0].join_pressed
    im.handle_event(ev(pygame.JOYBUTTONDOWN, instance_id=a.iid, button=2))
    c = im.poll()[0]
    assert c.join_pressed and c.jump_pressed


def test_hat_dpad(im):
    a = plug(im, 0)
    im.handle_event(ev(pygame.JOYHATMOTION, instance_id=a.iid, hat=0, value=(-1, 0)))
    c = im.poll()[0]
    assert c.dir == -1 and c.activity


def test_axis_noise_is_ignored(im):
    a = plug(im, 0)
    im.handle_event(ev(pygame.JOYAXISMOTION, instance_id=a.iid, axis=0, value=0.08))
    c = im.poll()[0]
    assert c.dir == 0 and not c.activity


def test_hotplug_frees_and_reassigns_slot(im):
    a = plug(im, 0)
    b = plug(im, 1)
    c = plug(im, 2)                 # third controller waits
    im.handle_event(ev(pygame.JOYDEVICEREMOVED, instance_id=a.iid))
    assert im.take_disconnected() == [0]
    assert im.slots == [c.iid, b.iid]
    im.handle_event(ev(pygame.JOYDEVICEREMOVED, instance_id=c.iid))
    d = plug(im, 3)                 # reconnect takes the free slot
    assert im.slots[0] == d.iid


def test_device_profile_mapping(im, tmp_path):
    im.mappings["devices"]["Weird Pad"] = {"jump": [0, 3], "start": [5], "dpad_left": [10], "dpad_right": [11]}
    w = plug(im, 0, "Weird Pad")
    im.handle_event(ev(pygame.JOYBUTTONDOWN, instance_id=w.iid, button=11))
    c = im.poll()[0]
    assert c.dir == 1 and not c.jump_pressed
    im.handle_event(ev(pygame.JOYBUTTONDOWN, instance_id=w.iid, button=3))
    assert im.poll()[0].jump_pressed
