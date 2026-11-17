#!/usr/bin/env python3
"""Opreto Bots - application entry point.

    python3 main.py              # fullscreen kiosk mode
    python3 main.py --windowed   # development window (Esc quits)

Admin exit (kiosk): Ctrl+Shift+Q.  Exit code 0 means "admin quit"; anything
else is treated as a crash by deploy/run_kiosk.sh, which restarts the game.
"""

import argparse
import logging
import logging.handlers
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config  # noqa: E402

log = logging.getLogger("opretobots")


def setup_logging():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fh = logging.handlers.RotatingFileHandler(os.path.join(config.LOG_DIR, "opretobots.log"),
                                              maxBytes=config.LOG_MAX_BYTES, backupCount=config.LOG_BACKUPS)
    fh.setFormatter(fmt)
    root.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)


def parse_args(argv):
    ap = argparse.ArgumentParser(description="Opreto Bots arcade game")
    ap.add_argument("--windowed", action="store_true", help="run in a window instead of fullscreen")
    ap.add_argument("--scale", type=int, default=None, help="window scale factor with --windowed")
    ap.add_argument("--software", action="store_true", help="use software scaling backend")
    ap.add_argument("--no-audio", action="store_true", help="disable sound")
    ap.add_argument("--fps", action="store_true", help="show FPS counter")
    ap.add_argument("--seed", type=int, default=None, help="random seed (testing)")
    return ap.parse_args(argv)


class Display:
    """Owns the window and the integer nearest-neighbour upscale."""

    def __init__(self, windowed, scale):
        import pygame
        self.pg = pygame
        W, H = config.LOGICAL_W, config.LOGICAL_H
        self.windowed = windowed
        self.backend = config.RENDER_BACKEND if not windowed else "software"
        vs = 1 if config.VSYNC else 0
        if self.backend == "scaled":
            flags = pygame.SCALED | pygame.FULLSCREEN
            try:
                self.screen = pygame.display.set_mode((W, H), flags, vsync=vs)
            except pygame.error as exc:
                log.warning("vsync scaled mode failed (%s); retrying without vsync", exc)
                self.screen = pygame.display.set_mode((W, H), flags)
            self.dest = None
        else:
            if windowed:
                k = scale or config.WINDOW_SCALE
                size = (W * k, H * k)
                flags = 0
            else:
                size = (config.DISPLAY_W, config.DISPLAY_H)
                flags = pygame.FULLSCREEN
            try:
                self.screen = pygame.display.set_mode(size, flags, vsync=vs)
            except pygame.error:
                self.screen = pygame.display.set_mode(size, flags)
            sw, sh = self.screen.get_size()
            k = max(1, min(sw // W, sh // H))
            self.k = k
            self.rect = pygame.Rect((sw - W * k) // 2, (sh - H * k) // 2, W * k, H * k)
            self.dest = self.screen.subsurface(self.rect)
        pygame.display.set_caption("Opreto Bots")
        log.info("display backend=%s size=%s driver=%s", self.backend, self.screen.get_size(),
                 pygame.display.get_driver())

    def present(self, logical, offset=(0, 0)):
        if self.dest is None:
            if offset != (0, 0):
                self.screen.fill((0, 0, 0))
            self.screen.blit(logical, offset)
        else:
            if offset != (0, 0):
                self.dest.fill((0, 0, 0))
                tmp = logical.copy()
                tmp.fill((0, 0, 0))
                tmp.blit(logical, offset)
                logical = tmp
            self.pg.transform.scale(logical, self.rect.size, self.dest)
        self.pg.display.flip()


def merge_controls(pending, fresh):
    from player import Controls
    if pending is None:
        return fresh
    out = []
    for a, b in zip(pending, fresh):
        out.append(Controls(dir=b.dir, jump_held=b.jump_held,
                            jump_pressed=a.jump_pressed or b.jump_pressed,
                            join_pressed=a.join_pressed or b.join_pressed,
                            activity=a.activity or b.activity))
    return out


def run(args):
    os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "nearest")
    os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    if args.no_audio:
        config.AUDIO_ENABLED = False
    if args.software:
        config.RENDER_BACKEND = "software"
    if args.fps:
        config.SHOW_FPS = True

    import pygame
    from audio import Audio
    from game import World
    from input_manager import InputManager
    from player import Controls

    if config.AUDIO_ENABLED:
        try:
            pygame.mixer.pre_init(config.AUDIO_FREQUENCY, -16, 1, config.AUDIO_BUFFER)
        except Exception:
            pass
    pygame.init()
    log.info("pygame %s, SDL %s", pygame.version.ver, ".".join(map(str, pygame.get_sdl_version())))

    # Clean shutdown on SIGTERM/SIGINT (systemd stop, OS shutdown, Ctrl+C).
    # Installed after pygame.init() so it replaces SDL's own handlers.
    import signal
    stop = {"flag": False}

    def _on_signal(signum, _frame):
        log.info("signal %s received, exiting", signum)
        stop["flag"] = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _on_signal)
        except (ValueError, OSError):
            pass

    display = Display(args.windowed, args.scale)
    pygame.mouse.set_visible(False)
    try:
        pygame.event.set_grab(False)
    except Exception:
        pass

    from renderer import Renderer
    audio = Audio()
    renderer = Renderer()
    world = World(seed=args.seed)
    inputs = InputManager()
    inputs.scan_existing()

    clock = pygame.time.Clock()
    dt = 1.0 / config.PHYSICS_HZ
    acc = 0.0
    last = time.perf_counter()
    pending = None
    heartbeat = time.monotonic()
    frames = 0

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT and args.windowed:
                return 0
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE and args.windowed:
                    return 0
                if e.key == pygame.K_F2:
                    renderer.show_fps = not renderer.show_fps
            inputs.handle_event(e)
        if stop["flag"]:
            return 0
        if inputs.admin_exit:
            log.info("admin exit requested")
            return 0

        pending = merge_controls(pending, inputs.poll())
        disconnected = inputs.take_disconnected()

        now = time.perf_counter()
        acc += min(0.25, now - last)
        last = now
        steps = 0
        while acc >= dt and steps < config.MAX_PHYSICS_STEPS_PER_FRAME:
            ctl = pending
            world.step(dt, ctl, disconnected)
            disconnected = []
            pending = [Controls(dir=c.dir, jump_held=c.jump_held) for c in ctl]
            acc -= dt
            steps += 1
        if steps == config.MAX_PHYSICS_STEPS_PER_FRAME:
            acc = 0.0
        if disconnected:  # no step ran this frame - apply next frame
            for slot in disconnected:
                world.leave(slot)

        audio.play_events(world.drain_events(), world.time, attract=(world.mode == "attract"))
        renderer.fps = clock.get_fps()
        logical = renderer.draw(world)
        display.present(logical, renderer.shake_offset(world))
        clock.tick(config.TARGET_FPS)

        frames += 1
        if time.monotonic() - heartbeat > 600:
            heartbeat = time.monotonic()
            rss = 0
            try:
                import resource
                rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
            except Exception:
                pass
            log.info("heartbeat fps=%.1f mode=%s score=%d bots=%d particles=%d maxrss=%dMB controllers=%d",
                     clock.get_fps(), world.mode, world.score, len(world.robots),
                     len(world.effects.particles), rss, len(inputs.devices))


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    applied = config.load_overrides()
    setup_logging()
    if applied:
        log.info("config overrides: %s", ", ".join(applied))
    try:
        code = run(args)
    except KeyboardInterrupt:
        code = 0
    except Exception:
        log.exception("fatal error")
        code = 1
    finally:
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass
    return code


if __name__ == "__main__":
    sys.exit(main())
