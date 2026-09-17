import os

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from fonts import get_font

AUDIO_EXTENSIONS = (".mp3", ".ogg", ".wav")


class SongSelectMenu:
    def __init__(self, screen, songs_dir):
        self.screen = screen
        self.songs_dir = songs_dir
        self.songs = sorted(
            f for f in os.listdir(songs_dir) if f.lower().endswith(AUDIO_EXTENSIONS)
        ) if os.path.isdir(songs_dir) else []
        self.index = 0
        self.difficulties = ["EASY", "NORMAL", "HARD"]
        self.diff_index = 1

        self.font_title = get_font(44, bold=True)
        self.font_item = get_font(28)
        self.font_hint = get_font(20)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if not self.songs:
                        continue
                    if event.key == pygame.K_UP:
                        self.index = (self.index - 1) % len(self.songs)
                    elif event.key == pygame.K_DOWN:
                        self.index = (self.index + 1) % len(self.songs)
                    elif event.key == pygame.K_LEFT:
                        self.diff_index = (self.diff_index - 1) % len(self.difficulties)
                    elif event.key == pygame.K_RIGHT:
                        self.diff_index = (self.diff_index + 1) % len(self.difficulties)
                    elif event.key == pygame.K_RETURN:
                        return (
                            os.path.join(self.songs_dir, self.songs[self.index]),
                            self.difficulties[self.diff_index],
                        )
            self._draw()
            clock.tick(60)

    def _draw(self):
        self.screen.fill(COLORS["bg_top"])
        title = self.font_title.render("PY RHYTHM", True, COLORS["text"])
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        if not self.songs:
            msg = self.font_item.render("songs/ 폴더에 mp3 파일을 넣어주세요", True, COLORS["MISS"])
            self.screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 220))
            hint = self.font_hint.render("Esc 종료", True, COLORS["text"])
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 60))
            pygame.display.flip()
            return

        start_y = 160
        for i, name in enumerate(self.songs):
            selected = i == self.index
            color = COLORS["combo"] if selected else COLORS["text"]
            label = ("> " if selected else "  ") + os.path.splitext(name)[0]
            surf = self.font_item.render(label, True, color)
            self.screen.blit(surf, (SCREEN_WIDTH // 2 - 260, start_y + i * 34))

        diff = self.difficulties[self.diff_index]
        diff_surf = self.font_item.render(f"난이도: < {diff} >", True, COLORS["GREAT"])
        self.screen.blit(diff_surf, (SCREEN_WIDTH // 2 - diff_surf.get_width() // 2, SCREEN_HEIGHT - 160))

        hint = self.font_hint.render(
            "위/아래: 곡 선택   좌/우: 난이도   Enter: 시작   Esc: 종료", True, COLORS["text"]
        )
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 60))
        pygame.display.flip()
