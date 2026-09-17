"""한글이 깨지지 않도록 번들된 TTF로만 폰트를 로드한다 (SysFont는 한글 글리프가 없는
시스템 기본 폰트를 골라 네모(□)로 깨지는 경우가 많아서 사용하지 않는다)."""

import os

import pygame

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "Freesentation-3Light.ttf")

_cache = {}


def get_font(size, bold=False):
    key = (size, bold)
    font = _cache.get(key)
    if font is not None:
        return font
    font = pygame.font.Font(FONT_PATH, size)
    font.set_bold(bold)
    _cache[key] = font
    return font
