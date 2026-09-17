import os
import sys
import threading

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from menu import SongSelectMenu
from chart_generator import generate_chart
from game import PlayScreen
from result_screen import show_result
from fonts import get_font

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SONGS_DIR = os.path.join(BASE_DIR, "songs")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")


def show_message(screen, message):
    font = get_font(30)
    screen.fill(COLORS["bg_top"])
    surf = font.render(message, True, COLORS["text"])
    screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT // 2))
    pygame.display.flip()
    pygame.event.pump()


def generate_chart_with_loading_screen(screen, audio_path, difficulty):
    """온셋 분석(librosa)은 몇 초~몇십 초가 걸릴 수 있어서, 메인 스레드를 막지 않도록
    별도 스레드에서 돌리고 그동안 창은 계속 이벤트를 처리/그려서 "멈춘 것처럼" 보이지
    않게 한다. Esc/닫기를 누르면 즉시 메뉴로 돌아간다(분석 자체는 백그라운드에서 계속
    끝까지 실행되어 다음에 같은 곡을 고르면 캐시를 바로 쓸 수 있다)."""
    outcome = {}

    def worker():
        try:
            outcome["chart"] = generate_chart(audio_path, difficulty=difficulty, cache_dir=CHARTS_DIR)
        except Exception as exc:  # noqa: BLE001 - surfaced to the loading screen, not swallowed
            outcome["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    font = get_font(30)
    hint_font = get_font(18)
    clock = pygame.time.Clock()
    elapsed = 0.0

    while thread.is_alive():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "cancelled"

        elapsed += clock.tick(30) / 1000.0
        dots = "." * (int(elapsed * 2) % 4)

        screen.fill(COLORS["bg_top"])
        surf = font.render(f"곡을 분석해서 노트를 생성하는 중{dots}", True, COLORS["text"])
        screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        hint = hint_font.render("(처음 재생하는 곡은 시간이 걸릴 수 있어요 — Esc: 취소)", True, COLORS["text"])
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
        pygame.display.flip()

    thread.join()
    if "error" in outcome:
        raise outcome["error"]
    return outcome["chart"]


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

        try:
            chart = generate_chart_with_loading_screen(screen, audio_path, difficulty)
        except Exception as exc:
            show_message(screen, f"분석 실패: {exc}")
            pygame.time.wait(2000)
            continue
        if chart == "cancelled":
            continue

        try:
            play_screen = PlayScreen(screen, audio_path, chart)
            result = play_screen.run()
        except Exception as exc:
            pygame.mixer.music.stop()
            show_message(screen, f"재생 실패: {exc}")
            pygame.time.wait(2000)
            continue

        if result is None:
            continue
        show_result(screen, chart, result)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
