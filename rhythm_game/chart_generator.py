"""mp3(또는 wav/ogg) 파일을 분석해서 리듬게임 노트 차트를 자동 생성한다.

librosa로 타악기(percussive) 성분을 분리한 뒤 온셋(소리가 시작되는 지점)을
검출하고, 각 온셋 시점의 주파수 분포를 4(혹은 6)개 대역으로 나눠 가장 강한
대역을 레인으로 배정한다. 결과는 charts/ 에 JSON으로 캐싱해서 같은 곡을
다시 분석하지 않도록 한다.
"""

import hashlib
import json
import os

import numpy as np
import librosa

from config import DIFFICULTY_PARAMS, LANE_COUNT

CHART_VERSION = 2


def _file_hash(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _lane_for_onset(y, sr, onset_time, lane_count):
    """온셋 주변 오디오의 주파수 분포를 보고 가장 에너지가 큰 대역을 레인으로 반환."""
    frame = int(onset_time * sr)
    window = y[max(0, frame - 1024): frame + 1024]
    if len(window) < 64:
        return 0
    spectrum = np.abs(np.fft.rfft(window))
    freqs = np.fft.rfftfreq(len(window), 1.0 / sr)
    bands = np.linspace(0, freqs[-1], lane_count + 1)
    energies = []
    for i in range(lane_count):
        mask = (freqs >= bands[i]) & (freqs < bands[i + 1])
        energies.append(spectrum[mask].sum() if mask.any() else 0.0)
    return int(np.argmax(energies))


def generate_chart(audio_path, difficulty="NORMAL", lane_count=LANE_COUNT, cache_dir="charts"):
    os.makedirs(cache_dir, exist_ok=True)
    cache_name = f"{_file_hash(audio_path)}_{difficulty}_{lane_count}_v{CHART_VERSION}.json"
    cache_path = os.path.join(cache_dir, cache_name)
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    params = DIFFICULTY_PARAMS[difficulty]
    y, sr = librosa.load(audio_path, sr=44100, mono=True)
    _, y_perc = librosa.effects.hpss(y)

    tempo, _ = librosa.beat.beat_track(y=y_perc, sr=sr)
    tempo = float(tempo) if np.isscalar(tempo) else float(tempo[0])

    onset_frames = librosa.onset.onset_detect(
        y=y_perc, sr=sr, backtrack=True,
        delta=params["onset_delta"], units="frames",
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    min_gap = params["min_gap_ms"] / 1000.0
    rng = np.random.default_rng(int(_file_hash(audio_path)[:8], 16))

    notes = []
    last_time_per_lane = {}
    prev_time = -1.0
    for t in onset_times:
        if t - prev_time < min_gap:
            continue
        prev_time = t

        lane = _lane_for_onset(y, sr, t, lane_count)
        if last_time_per_lane.get(lane, -10.0) > t - 0.08:
            lane = (lane + 1) % lane_count
        last_time_per_lane[lane] = t

        note = {"time": round(float(t), 4), "lane": int(lane), "type": "tap"}
        if rng.random() < params["hold_prob"]:
            note["type"] = "hold"
            note["duration"] = round(float(rng.uniform(0.25, 0.6)), 3)
        notes.append(note)

    notes.sort(key=lambda n: n["time"])
    chart = {
        "source": os.path.basename(audio_path),
        "difficulty": difficulty,
        "lane_count": lane_count,
        "bpm": tempo,
        "duration": float(librosa.get_duration(y=y, sr=sr)),
        "note_count": len(notes),
        "notes": notes,
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(chart, f, ensure_ascii=False, indent=2)
    return chart
