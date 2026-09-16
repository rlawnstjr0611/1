import numpy as np
import pygame


def make_hit_sound(sample_rate=44100, duration=0.05, freq=1200):
    """외부 사운드 파일 없이 타격음을 합성한다 (감쇠하는 짧은 사인파)."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(freq * t * 2 * np.pi) * np.exp(-t * 40)
    wave = (wave * 32767 * 0.5).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack([wave, wave]))
    return pygame.sndarray.make_sound(stereo)
