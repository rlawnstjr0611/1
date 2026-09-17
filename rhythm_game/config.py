import pygame

FPS = 60
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 900

LANE_COUNT = 4
LANE_WIDTH = 120
LANE_GAP = 4
LANES_TOTAL_WIDTH = LANE_COUNT * LANE_WIDTH + (LANE_COUNT - 1) * LANE_GAP
LANES_X_START = (SCREEN_WIDTH - LANES_TOTAL_WIDTH) // 2

JUDGE_LINE_Y = SCREEN_HEIGHT - 140
NOTE_HEIGHT = 28
NOTE_SPEED = 620  # px / sec at NORMAL difficulty

KEY_BINDINGS = {
    4: [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k],
    6: [pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k, pygame.K_l],
}

JUDGMENT_WINDOWS_MS = {
    "PERFECT": 35,
    "GREAT": 70,
    "GOOD": 110,
    "MISS": 160,
}
JUDGMENT_SCORE = {"PERFECT": 100, "GREAT": 70, "GOOD": 30, "MISS": 0}

# 사용자가 옵션 화면에서 조절하는 노트 낙하 속도 배율
DEFAULT_SPEED_SCALE = 1.0
MIN_SPEED_SCALE = 0.5
MAX_SPEED_SCALE = 2.5
SPEED_SCALE_STEP = 0.1

# 노트가 빨라질수록(기준 배속보다 클수록) 판정 구간을 이 배율까지 넓혀서 후하게 준다
JUDGMENT_LENIENCY_CAP = 1.8

# onset_delta: 낮을수록 온셋을 더 민감하게(많이) 잡아 노트가 촘촘해짐
# min_gap_ms: 연속된 노트 사이 최소 시간 간격
# hold_prob: 온셋 하나가 롱노트(홀드)가 될 확률
# speed_mult: 기본 NOTE_SPEED 에 곱해지는 배속
DIFFICULTY_PARAMS = {
    "EASY": dict(onset_delta=0.25, min_gap_ms=260, hold_prob=0.05, speed_mult=0.8),
    "NORMAL": dict(onset_delta=0.15, min_gap_ms=170, hold_prob=0.10, speed_mult=1.0),
    "HARD": dict(onset_delta=0.07, min_gap_ms=110, hold_prob=0.16, speed_mult=1.25),
}

COLORS = {
    "bg_top": (10, 10, 28),
    "lane_bg": (24, 20, 46),
    "lane_bg_alt": (30, 24, 56),
    "lane_line": (90, 70, 160),
    "judge_line": (255, 255, 255),
    "note": [
        (255, 84, 138),
        (84, 200, 255),
        (255, 214, 84),
        (140, 255, 150),
        (200, 130, 255),
        (255, 150, 90),
    ],
    "text": (240, 240, 250),
    "combo": (255, 221, 89),
    "PERFECT": (255, 221, 89),
    "GREAT": (105, 255, 175),
    "GOOD": (105, 190, 255),
    "MISS": (255, 90, 90),
}
