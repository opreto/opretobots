"""Original 8-bit style sound effects, synthesised at start-up (no asset files).

Audio is optional: if the mixer cannot be initialised (no sound device) or
AUDIO_ENABLED is False, every call becomes a silent no-op.
"""

import logging
import math
import random
from array import array

import pygame

import config

log = logging.getLogger("opretobots.audio")


def _square(freq, t, duty=0.5):
    return 1.0 if (freq * t) % 1.0 < duty else -1.0


def _tri(freq, t):
    p = (freq * t) % 1.0
    return 4 * p - 1 if p < 0.5 else 3 - 4 * p


class Synth:
    def __init__(self, rate):
        self.rate = rate
        self.rng = random.Random(42)

    def tone(self, f0, f1, dur, wave="square", vol=0.5, duty=0.5, attack=0.004, release=0.04, vibrato=0.0):
        n = int(self.rate * dur)
        out = []
        phase = 0.0
        noise_val = 0.0
        for i in range(n):
            t = i / self.rate
            k = i / max(1, n - 1)
            f = f0 + (f1 - f0) * k
            if vibrato:
                f *= 1.0 + vibrato * math.sin(t * 40)
            phase += f / self.rate
            if wave == "square":
                v = 1.0 if phase % 1.0 < duty else -1.0
            elif wave == "tri":
                p = phase % 1.0
                v = 4 * p - 1 if p < 0.5 else 3 - 4 * p
            else:  # noise, re-sampled at the "frequency" rate like the NES
                if int(phase) != int(phase - f / self.rate):
                    noise_val = self.rng.uniform(-1, 1)
                v = noise_val
            env = 1.0
            if t < attack:
                env = t / attack
            rem = dur - t
            if rem < release:
                env *= max(0.0, rem / release)
            out.append(v * vol * env)
        return out

    @staticmethod
    def seq(*parts):
        out = []
        for p in parts:
            out.extend(p)
        return out

    def silence(self, dur):
        return [0.0] * int(self.rate * dur)

    @staticmethod
    def mix(a, b):
        n = max(len(a), len(b))
        return [(a[i] if i < len(a) else 0.0) + (b[i] if i < len(b) else 0.0) for i in range(n)]

    def arp(self, notes, step, wave="square", vol=0.45, duty=0.5):
        return self.seq(*[self.tone(f, f, step, wave, vol, duty, release=0.015) for f in notes])


def _note(n):
    """MIDI note number to Hz."""
    return 440.0 * 2 ** ((n - 69) / 12.0)


def build_sounds(rate):
    s = Synth(rate)
    N = _note
    sounds = {
        "jump": s.tone(N(60), N(79), 0.13, "square", 0.32, 0.25),
        "step": s.tone(180, 120, 0.025, "noise", 0.10),
        "land": s.tone(140, 90, 0.04, "noise", 0.16),
        "bounce": s.tone(N(72), N(84), 0.07, "square", 0.3, 0.5),
        "fix": s.seq(s.tone(300, 900, 0.05, "noise", 0.15),
                     s.arp([N(72), N(76), N(79), N(84), N(88)], 0.045, "square", 0.36, 0.25)),
        "break": s.seq(s.tone(N(70), N(46), 0.18, "square", 0.34, 0.5, vibrato=0.06),
                       s.tone(220, 120, 0.06, "noise", 0.2)),
        "pass": s.arp([N(84), N(91), N(96)], 0.07, "tri", 0.6),
        "reject": s.seq(s.tone(N(43), N(40), 0.12, "square", 0.32, 0.5), s.silence(0.03),
                        s.tone(N(40), N(36), 0.18, "square", 0.32, 0.5), s.tone(400, 80, 0.12, "noise", 0.25)),
        "scan": s.tone(N(96), N(100), 0.08, "square", 0.12, 0.125),
        "compass": s.mix(s.seq(s.tone(N(48), N(84), 0.30, "square", 0.32, 0.5),
                               s.arp([N(84), N(88), N(91), N(96), N(91), N(96), N(100)], 0.06, "square", 0.32,
                                     0.25)),
                         s.seq(s.tone(1200, 60, 0.45, "noise", 0.28), s.tone(N(36), N(48), 0.3, "tri", 0.5))),
        "bonk": s.tone(N(48), N(43), 0.08, "square", 0.3, 0.5),
        "arm_warn": s.seq(s.tone(N(81), N(81), 0.06, "square", 0.12), s.silence(0.06),
                          s.tone(N(81), N(81), 0.06, "square", 0.12)),
        "arm_move": s.mix(s.tone(80, 160, 0.9, "noise", 0.08, release=0.3),
                          s.tone(N(40), N(45), 0.9, "tri", 0.18, release=0.3)),
        "join": s.arp([N(60), N(64), N(67), N(72), N(76), N(79), N(84)], 0.05, "square", 0.32, 0.5),
        "leave": s.arp([N(79), N(72), N(67), N(60), N(55)], 0.06, "tri", 0.45),
        "hurt": s.seq(s.tone(900, 200, 0.1, "noise", 0.3), s.tone(N(55), N(43), 0.15, "square", 0.3, 0.25)),
        "spawn": s.tone(N(67), N(60), 0.05, "square", 0.12, 0.125),
        "recharge": s.arp([N(72), N(79), N(84), N(91), N(96), N(103)], 0.05, "tri", 0.6),
        "game_start": s.arp([N(72), N(72), N(79), N(84)], 0.08, "square", 0.32, 0.5),
    }
    return sounds


class Audio:
    # minimum seconds between repeats of the same sound
    THROTTLE = {"step": 0.12, "spawn": 0.2, "scan": 0.15, "land": 0.08, "fix": 0.04, "break": 0.04}

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        self.last_played = {}
        self.muted_attract = not config.ATTRACT_AUDIO
        if not config.AUDIO_ENABLED:
            log.info("audio disabled by config")
            return
        try:
            pygame.mixer.pre_init(config.AUDIO_FREQUENCY, -16, 1, config.AUDIO_BUFFER)
            pygame.mixer.init()
            init = pygame.mixer.get_init()
            if not init:
                raise RuntimeError("mixer did not initialise")
            rate, fmt, channels = init
            pygame.mixer.set_num_channels(16)
            raw = build_sounds(rate)
            for name, samples in raw.items():
                arr = array("h")
                for v in samples:
                    iv = int(max(-1.0, min(1.0, v * config.MASTER_VOLUME)) * 32000)
                    for _ in range(channels):
                        arr.append(iv)
                if fmt not in (-16, 16):
                    log.warning("unexpected mixer format %s; sounds may be distorted", fmt)
                self.sounds[name] = pygame.mixer.Sound(buffer=arr.tobytes())
            self.enabled = True
            log.info("audio ready (%d Hz, %d ch, %d sounds)", rate, channels, len(self.sounds))
        except Exception as exc:  # no sound device etc. - the game runs silently
            log.warning("audio unavailable: %s", exc)
            self.enabled = False

    def play_events(self, events, now, attract=False):
        if not self.enabled:
            return
        if attract and self.muted_attract:
            return
        for name in events:
            snd = self.sounds.get(name)
            if snd is None:
                continue
            gap = self.THROTTLE.get(name, 0.0)
            if gap and now - self.last_played.get(name, -10.0) < gap:
                continue
            if name == "step" and not config.FOOTSTEP_SOUNDS:
                continue
            self.last_played[name] = now
            try:
                snd.play()
            except Exception:  # pragma: no cover - device vanished mid-show
                pass
