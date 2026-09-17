"""옵션 화면에서 바꾸는 설정을 settings.json 으로 저장/로드한다."""

import json
import os

from config import DEFAULT_SPEED_SCALE, MIN_SPEED_SCALE, MAX_SPEED_SCALE, SPEED_SCALE_STEP

_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")


class Settings:
    def __init__(self):
        self.speed_scale = DEFAULT_SPEED_SCALE
        self._load()

    def _load(self):
        if os.path.exists(_SETTINGS_PATH):
            try:
                with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.speed_scale = float(data.get("speed_scale", DEFAULT_SPEED_SCALE))
            except (OSError, ValueError, json.JSONDecodeError):
                self.speed_scale = DEFAULT_SPEED_SCALE
        self.speed_scale = min(MAX_SPEED_SCALE, max(MIN_SPEED_SCALE, self.speed_scale))

    def save(self):
        try:
            with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump({"speed_scale": self.speed_scale}, f)
        except OSError:
            pass

    def increase_speed(self):
        self.speed_scale = round(min(MAX_SPEED_SCALE, self.speed_scale + SPEED_SCALE_STEP), 2)
        self.save()

    def decrease_speed(self):
        self.speed_scale = round(max(MIN_SPEED_SCALE, self.speed_scale - SPEED_SCALE_STEP), 2)
        self.save()
