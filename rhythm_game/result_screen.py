import os

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS


def show_result(screen, chart, result):
    font_title = pygame.font.SysFont(None, 56, bold=True)
    font_rank = pygame.font.SysFont(None, 140, bold=True)
    font_mid = pygame.font.SysFont(None, 30)
    font_small = pygame.font.SysFont(None, 22)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                return

        screen.fill(COLORS["bg_top"])
        title = font_title.render(os.path.splitext(chart["source"])[0], True, COLORS["text"])
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        rank_surf = font_rank.render(result.rank, True, COLORS["combo"])
        screen.blit(rank_surf, (SCREEN_WIDTH // 2 - rank_surf.get_width() // 2, 150))

        lines = [
            f"SCORE       {result.score}",
            f"MAX COMBO   {result.max_combo}",
            f"ACCURACY    {result.accuracy:.2f}%",
            "",
            f"PERFECT  {result.counts['PERFECT']}",
            f"GREAT    {result.counts['GREAT']}",
            f"GOOD     {result.counts['GOOD']}",
            f"MISS     {result.counts['MISS']}",
        ]
        y = 340
        for line in lines:
            surf = font_mid.render(line, True, COLORS["text"])
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 36

        hint = font_small.render("아무 키나 눌러 메뉴로 돌아가기", True, COLORS["text"])
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 60))

        pygame.display.flip()
        clock.tick(60)
