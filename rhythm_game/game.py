import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, LANE_WIDTH, LANE_GAP, LANES_X_START,
    JUDGE_LINE_Y, NOTE_HEIGHT, NOTE_SPEED, KEY_BINDINGS,
    JUDGMENT_WINDOWS_MS, JUDGMENT_SCORE, JUDGMENT_LENIENCY_CAP,
    COLORS, DIFFICULTY_PARAMS,
)
from hitsound import make_hit_sound
from fonts import get_font


class Note:
    __slots__ = ("time", "lane", "type", "duration", "judged", "hold_active")

    def __init__(self, data):
        self.time = data["time"]
        self.lane = data["lane"]
        self.type = data["type"]
        self.duration = data.get("duration", 0.0)
        self.judged = False
        self.hold_active = False

    @property
    def end_time(self):
        return self.time + self.duration if self.type == "hold" else self.time


class PlayResult:
    def __init__(self):
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.counts = {"PERFECT": 0, "GREAT": 0, "GOOD": 0, "MISS": 0}

    def register(self, judgment):
        self.counts[judgment] += 1
        self.score += JUDGMENT_SCORE[judgment]
        if judgment == "MISS":
            self.combo = 0
        else:
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)

    @property
    def total_notes(self):
        return sum(self.counts.values())

    @property
    def accuracy(self):
        if self.total_notes == 0:
            return 0.0
        weighted = (
            self.counts["PERFECT"] * 1.0
            + self.counts["GREAT"] * 0.7
            + self.counts["GOOD"] * 0.3
        )
        return 100.0 * weighted / self.total_notes

    @property
    def rank(self):
        acc = self.accuracy
        if acc >= 97:
            return "S"
        if acc >= 92:
            return "A"
        if acc >= 80:
            return "B"
        if acc >= 60:
            return "C"
        return "F"


class PlayScreen:
    def __init__(self, screen, audio_path, chart, speed_scale=1.0):
        self.screen = screen
        self.audio_path = audio_path
        self.chart = chart
        self.lane_count = chart["lane_count"]

        difficulty_mult = DIFFICULTY_PARAMS[chart["difficulty"]]["speed_mult"]
        effective_mult = difficulty_mult * speed_scale
        self.speed = NOTE_SPEED * effective_mult

        # 기준 배속(1.0x, NORMAL 난이도)보다 노트가 빨라질수록 판정 구간을 넓혀서
        # 후하게 판정한다. 기준보다 느릴 때는 굳이 더 빡빡하게 만들지 않는다.
        leniency = min(max(effective_mult, 1.0), JUDGMENT_LENIENCY_CAP)
        self.judgment_windows_ms = {k: v * leniency for k, v in JUDGMENT_WINDOWS_MS.items()}

        self.notes = [Note(n) for n in chart["notes"]]
        self.notes.sort(key=lambda n: n.time)
        self._lane_notes = {i: [] for i in range(self.lane_count)}
        for n in self.notes:
            self._lane_notes[n.lane].append(n)
        self.next_note_idx_by_lane = {i: 0 for i in range(self.lane_count)}

        self.keys = KEY_BINDINGS[self.lane_count]
        self.key_to_lane = {k: i for i, k in enumerate(self.keys)}
        self.lane_x = [
            LANES_X_START + i * (LANE_WIDTH + LANE_GAP) for i in range(self.lane_count)
        ]

        self.font_big = get_font(64, bold=True)
        self.font_mid = get_font(30, bold=True)
        self.font_small = get_font(20)

        self.result = PlayResult()
        self.lane_press_flash = {i: -1.0 for i in range(self.lane_count)}
        self.center_judgment = None  # (text, expire_time)
        self.hit_sound = make_hit_sound()

        self.start_ticks = None

    def run(self):
        pygame.mixer.music.load(self.audio_path)
        pygame.mixer.music.play()
        self.start_ticks = pygame.time.get_ticks()
        clock = pygame.time.Clock()

        while True:
            now = self._song_time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.mixer.music.stop()
                        return None
                    if event.key in self.key_to_lane:
                        self._on_key_down(self.key_to_lane[event.key], now)
                elif event.type == pygame.KEYUP:
                    if event.key in self.key_to_lane:
                        self._on_key_up(self.key_to_lane[event.key], now)

            self._update_misses(now)

            song_over = not pygame.mixer.music.get_busy() and now > 1.0
            all_judged = all(n.judged for n in self.notes)
            if song_over and all_judged:
                return self.result

            self._draw(now)
            clock.tick(60)

    def _song_time(self):
        return (pygame.time.get_ticks() - self.start_ticks) / 1000.0

    # ---- judging ----

    def _find_target_note(self, lane, now):
        notes = self._lane_notes[lane]
        idx = self.next_note_idx_by_lane[lane]
        while idx < len(notes) and notes[idx].judged:
            idx += 1
        self.next_note_idx_by_lane[lane] = idx
        return notes[idx] if idx < len(notes) else None

    def _judge_from_delta_ms(self, delta_ms):
        d = abs(delta_ms)
        if d <= self.judgment_windows_ms["PERFECT"]:
            return "PERFECT"
        if d <= self.judgment_windows_ms["GREAT"]:
            return "GREAT"
        if d <= self.judgment_windows_ms["GOOD"]:
            return "GOOD"
        return None

    def _on_key_down(self, lane, now):
        self.lane_press_flash[lane] = now
        note = self._find_target_note(lane, now)
        if note is None:
            return
        delta_ms = (now - note.time) * 1000.0
        if abs(delta_ms) > self.judgment_windows_ms["MISS"]:
            return
        judgment = self._judge_from_delta_ms(delta_ms)
        if judgment is None:
            return

        if note.type == "hold":
            note.hold_active = True
            self._show_judgment(judgment, now)
            self.hit_sound.play()
        else:
            note.judged = True
            self._finalize_note(judgment)

    def _on_key_up(self, lane, now):
        note = None
        for n in self._lane_notes[lane]:
            if n.type == "hold" and n.hold_active and not n.judged:
                note = n
                break
        if note is None:
            return
        note.hold_active = False
        note.judged = True
        delta_ms = (note.end_time - now) * 1000.0
        judgment = "GOOD" if delta_ms <= self.judgment_windows_ms["GOOD"] else "MISS"
        self._finalize_note(judgment)

    def _finalize_note(self, judgment):
        self.result.register(judgment)
        self._show_judgment(judgment, self._song_time())
        if judgment != "MISS":
            self.hit_sound.play()

    def _show_judgment(self, judgment, now):
        self.center_judgment = (judgment, now + 0.35)

    def _update_misses(self, now):
        for n in self.notes:
            if n.judged:
                continue
            if n.type == "tap":
                if now - n.time > self.judgment_windows_ms["MISS"] / 1000.0:
                    n.judged = True
                    self._finalize_note("MISS")
            else:
                if n.hold_active:
                    if now >= n.end_time:
                        n.judged = True
                        n.hold_active = False
                        self._finalize_note("PERFECT")
                elif now - n.time > self.judgment_windows_ms["MISS"] / 1000.0:
                    n.judged = True
                    self._finalize_note("MISS")

    # ---- drawing ----

    def _draw(self, now):
        screen = self.screen
        screen.fill(COLORS["bg_top"])

        for i in range(self.lane_count):
            x = self.lane_x[i]
            color = COLORS["lane_bg"] if i % 2 == 0 else COLORS["lane_bg_alt"]
            pygame.draw.rect(screen, color, (x, 0, LANE_WIDTH, SCREEN_HEIGHT))
            if now - self.lane_press_flash[i] < 0.08:
                glow = pygame.Surface((LANE_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                glow.fill((255, 255, 255, 35))
                screen.blit(glow, (x, 0))

        for i in range(self.lane_count + 1):
            x = LANES_X_START + i * (LANE_WIDTH + LANE_GAP) - LANE_GAP // 2
            pygame.draw.line(screen, COLORS["lane_line"], (x, 0), (x, SCREEN_HEIGHT), 2)

        right_edge = LANES_X_START + self.lane_count * (LANE_WIDTH + LANE_GAP) - LANE_GAP
        pygame.draw.line(screen, COLORS["judge_line"], (LANES_X_START, JUDGE_LINE_Y), (right_edge, JUDGE_LINE_Y), 3)

        for i in range(self.lane_count):
            x = self.lane_x[i]
            pressed = now - self.lane_press_flash[i] < 0.08
            color = COLORS["combo"] if pressed else COLORS["lane_line"]
            pygame.draw.rect(screen, color, (x + 6, JUDGE_LINE_Y - 6, LANE_WIDTH - 12, 12), border_radius=4)

        for n in self.notes:
            self._draw_note(n, now)

        self._draw_hud(now)
        pygame.display.flip()

    def _draw_note(self, note, now):
        if note.judged:
            return
        x = self.lane_x[note.lane]
        color = COLORS["note"][note.lane % len(COLORS["note"])]

        if note.type == "tap":
            y = JUDGE_LINE_Y - (note.time - now) * self.speed
            if y < -NOTE_HEIGHT or y > SCREEN_HEIGHT + NOTE_HEIGHT:
                return
            rect = pygame.Rect(x + 6, y - NOTE_HEIGHT // 2, LANE_WIDTH - 12, NOTE_HEIGHT)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, COLORS["text"], rect, width=2, border_radius=8)
            return

        head_y = JUDGE_LINE_Y if note.hold_active else JUDGE_LINE_Y - (note.time - now) * self.speed
        tail_y = JUDGE_LINE_Y - (note.end_time - now) * self.speed
        top, bottom = min(head_y, tail_y), max(head_y, tail_y)
        if bottom < -NOTE_HEIGHT or top > SCREEN_HEIGHT + NOTE_HEIGHT:
            return

        body_color = tuple(min(c + 60, 255) for c in color) if note.hold_active else color
        body_rect = pygame.Rect(x + 16, top, LANE_WIDTH - 32, max(bottom - top, 4))
        pygame.draw.rect(self.screen, body_color, body_rect, border_radius=10)

        head_rect = pygame.Rect(x + 6, head_y - NOTE_HEIGHT // 2, LANE_WIDTH - 12, NOTE_HEIGHT)
        pygame.draw.rect(self.screen, color, head_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLORS["text"], head_rect, width=2, border_radius=8)

    def _draw_hud(self, now):
        screen = self.screen
        score_surf = self.font_big.render(f"{self.result.score:06d}", True, COLORS["text"])
        screen.blit(score_surf, (SCREEN_WIDTH - score_surf.get_width() - 24, 20))

        if self.result.combo > 0:
            combo_surf = self.font_big.render(str(self.result.combo), True, COLORS["combo"])
            screen.blit(combo_surf, (SCREEN_WIDTH // 2 - combo_surf.get_width() // 2, JUDGE_LINE_Y - 220))
            combo_label = self.font_small.render("COMBO", True, COLORS["combo"])
            screen.blit(combo_label, (SCREEN_WIDTH // 2 - combo_label.get_width() // 2, JUDGE_LINE_Y - 160))

        if self.center_judgment and now < self.center_judgment[1]:
            text, _ = self.center_judgment
            surf = self.font_mid.render(text, True, COLORS.get(text, COLORS["text"]))
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, JUDGE_LINE_Y - 100))

        acc_surf = self.font_small.render(f"ACC {self.result.accuracy:5.2f}%", True, COLORS["text"])
        screen.blit(acc_surf, (24, 20))

        duration = max(self.chart["duration"], 0.001)
        progress = max(0.0, min(1.0, now / duration))
        pygame.draw.rect(screen, COLORS["lane_bg_alt"], (0, 0, SCREEN_WIDTH, 6))
        pygame.draw.rect(screen, COLORS["combo"], (0, 0, int(SCREEN_WIDTH * progress), 6))
