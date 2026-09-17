import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, MIN_SPEED_SCALE, MAX_SPEED_SCALE
from fonts import get_font


def run_settings_screen(screen, settings):
    font_title = get_font(36, bold=True)
    font_item = get_font(28, bold=True)
    font_small = get_font(18)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_TAB):
                    return
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    settings.decrease_speed()
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    settings.increase_speed()

        screen.fill(COLORS["bg_top"])
        title = font_title.render("옵션", True, COLORS["text"])
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 90))

        label = font_item.render(f"노트 속도  {settings.speed_scale:.1f}x", True, COLORS["combo"])
        screen.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, 220))

        bar_w, bar_h = 380, 16
        bar_x = SCREEN_WIDTH // 2 - bar_w // 2
        bar_y = 280
        pygame.draw.rect(screen, COLORS["lane_bg_alt"], (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        ratio = (settings.speed_scale - MIN_SPEED_SCALE) / (MAX_SPEED_SCALE - MIN_SPEED_SCALE)
        pygame.draw.rect(screen, COLORS["combo"], (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=8)
        knob_x = bar_x + int(bar_w * ratio)
        pygame.draw.circle(screen, COLORS["text"], (knob_x, bar_y + bar_h // 2), 12)

        note = font_small.render(
            "속도가 빨라질수록 판정 구간이 넓어져서 타이밍을 조금 놓쳐도 덜 손해봐요",
            True, COLORS["text"],
        )
        screen.blit(note, (SCREEN_WIDTH // 2 - note.get_width() // 2, 330))

        hint = font_small.render("←→ 속도 조절   Enter / Esc / Tab: 뒤로가기", True, COLORS["text"])
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 80))

        pygame.display.flip()
        clock.tick(60)
