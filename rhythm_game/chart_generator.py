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

CHART_VERSION = 4

LANE_PICK_TEMPERATURE = 1.1  # 낮을수록 스펙트럼상 가장 강한 레인으로 더 확정적으로 쏠림
MAX_SAME_LANE_REPEAT = 2  # 같은 레인이 이 횟수 연속으로 나오면 다음엔 강하게 회피


def _file_hash(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _band_energies(y, sr, onset_time, lane_count):
    """온셋 주변 오디오를 lane_count개 주파수 대역으로 나눠 대역별 세기를 반환.

    음악 스펙트럼은 저음/중음에 에너지가 압도적으로 몰려있어서(1/f에 가까운 분포),
    대역을 선형으로 나누면 거의 항상 같은 한두 대역만 이긴다. 그래서 대역 경계를
    로그 스케일(멜 스케일과 비슷하게 저음은 좁게, 고음은 넓게)로 나누고, 세기도
    합이 아닌 로그 압축된 평균으로 비교해 대역별 빈(bin) 개수 차이의 영향을 줄인다.
    """
    frame = int(onset_time * sr)
    window = y[max(0, frame - 1024): frame + 1024]
    if len(window) < 64:
        return np.ones(lane_count)
    windowed = window * np.hanning(len(window))
    spectrum = np.log1p(np.abs(np.fft.rfft(windowed)))
    freqs = np.fft.rfftfreq(len(window), 1.0 / sr)

    edges = np.concatenate(([0.0], np.geomspace(60.0, freqs[-1], lane_count)))
    energies = np.zeros(lane_count)
    for i in range(lane_count):
        mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
        energies[i] = spectrum[mask].mean() if mask.any() else 0.0
    return energies


def _pick_lane(energies, rng, recent_lanes):
    """대역 세기가 가장 큰 레인에 확률적으로 쏠리게(소프트맥스) 레인을 뽑는다.

    argmax로 고정하면 곡 전체의 음색이 비슷할 때 항상 같은 한두 레인만 나와서
    "두 레일에서만 노트가 나온다"는 문제가 생긴다. 에너지를 곡 상대적인
    z-score로 정규화한 뒤 온도(temperature)를 적용한 소프트맥스로 확률적으로
    샘플링하면, 가장 강한 레인 쪽으로 여전히 치우치면서도 다른 레인에도 노트가
    분산된다. 같은 레인이 너무 자주 연속되면 그 레인 확률을 추가로 깎는다.
    """
    lane_count = len(energies)
    std = float(energies.std())
    z = (energies - energies.mean()) / std if std > 1e-6 else np.zeros(lane_count)
    weights = np.exp(z / LANE_PICK_TEMPERATURE)

    if len(recent_lanes) >= MAX_SAME_LANE_REPEAT and len(set(recent_lanes[-MAX_SAME_LANE_REPEAT:])) == 1:
        weights[recent_lanes[-1]] *= 0.08

    total = weights.sum()
    if not np.isfinite(total) or total <= 0:
        weights = np.ones(lane_count)
        total = float(lane_count)
    weights = weights / total
    return int(rng.choice(lane_count, p=weights))


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
    recent_lanes = []
    last_time_per_lane = {}
    prev_time = -1.0
    for t in onset_times:
        if t - prev_time < min_gap:
            continue
        prev_time = t

        energies = _band_energies(y, sr, t, lane_count)
        lane = _pick_lane(energies, rng, recent_lanes)
        if last_time_per_lane.get(lane, -10.0) > t - 0.08:
            lane = (lane + 1) % lane_count
        last_time_per_lane[lane] = t
        recent_lanes.append(lane)

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
