"""Render every sprite to a PNG sheet for review:  python tools/preview_sprites.py out.png"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))
from sprites import SpriteBank  # noqa: E402

bank = SpriteBank()
sheet = pygame.Surface((230, 100))
sheet.fill((24, 28, 52))
x = 4
for kind in ("gear", "bolt", "box"):
    for good in (False, True):
        for f in (0, 1):
            s = bank.robot(kind, good, f, 1)
            sheet.blit(s, (x, 4))
            x += s.get_width() + 3
x = 4
for slot in (0, 1):
    for name in ("idle", "walk1", "walk2", "jump", "swing", "stun"):
        s = bank.mech(slot, name, 1)
        sheet.blit(s, (x, 34 + slot * 20))
        x += s.get_width() + 2
    x = 4
sheet.blit(bank.compass_icon, (4, 80))
sheet.blit(bank.compass_icon_empty, (14, 80))
sheet.blit(bank.heart, (24, 80))
sheet.blit(bank.star, (32, 80))
out = sys.argv[1] if len(sys.argv) > 1 else "sprites_preview.png"
pygame.image.save(pygame.transform.scale(sheet, (sheet.get_width() * 6, sheet.get_height() * 6)), out)
print("wrote", out)
