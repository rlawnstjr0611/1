import os
import sys

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from menu import SongSelectMenu
from chart_generator import generate_chart
from game import PlayScreen
from result_screen import show_result

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SONGS_DIR = os.path.join(BASE_DIR, "songs")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")


def show_message(screen, message):
    font = pygame.font.SysFont(None, 32)
    screen.fill(COLORS["bg_top"])
    surf = font.render(message, True, COLORS["text"])
    screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT // 2))
    pygame.display.flip()
    pygame.event.pump()


def main():
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PyRhythm - DJMAX Style")

    os.makedirs(SONGS_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)

    menu = SongSelectMenu(screen, songs_dir=SONGS_DIR)

    while True:
        selection = menu.run()
        if selection is None:
            break
        audio_path, difficulty = selection

        show_message(screen, "곡을 분석해서 노트를 생성하는 중...")
        try:
            chart = generate_chart(audio_path, difficulty=difficulty, cache_dir=CHARTS_DIR)
        except Exception as exc:
            show_message(screen, f"분석 실패: {exc}")
            pygame.time.wait(2000)
            continue

        play_screen = PlayScreen(screen, audio_path, chart)
        result = play_screen.run()
        if result is None:
            continue
        show_result(screen, chart, result)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
