# PyRhythm — mp3 자동 채보 리듬게임

pygame으로 만든 DJMAX 스타일 4키 낙하형 리듬게임. `songs/` 폴더에 mp3 파일만
넣으면 `librosa`의 온셋(onset) 검출로 노트 차트를 자동 생성해서 바로 플레이할 수 있다.

## 설치

```bash
cd rhythm_game
pip install -r requirements.txt
```

mp3 디코딩이 실패하면 시스템에 `ffmpeg`가 설치되어 있는지 확인한다.
(`libsndfile`가 최신이면 ffmpeg 없이도 되는 경우가 많지만, 안 되면 ffmpeg를 깔면 대부분 해결된다.)

## 실행

1. `songs/` 폴더에 원하는 mp3 파일을 넣는다.
2. 아래 명령으로 실행:

```bash
python main.py
```

3. 곡 선택 화면에서 위/아래로 곡을, 좌/우로 난이도(EASY / NORMAL / HARD)를 고르고 Enter.
4. 처음 플레이하는 곡은 자동 분석(채보 생성)에 몇 초 걸릴 수 있다. 생성된 채보는
   `charts/` 폴더에 캐싱되어 다음부터는 즉시 시작된다.

## 조작

- 4개 레인: `D` `F` `J` `K`
- `Esc`: 플레이 중 중단하고 메뉴로

## 자동 채보 생성 원리 (`chart_generator.py`)

1. `librosa.effects.hpss`로 타악기(percussive) 성분을 분리한다.
2. `librosa.onset.onset_detect`로 소리가 시작되는 지점(온셋)을 찾는다. 난이도별로
   민감도(`onset_delta`)와 최소 노트 간격(`min_gap_ms`)이 달라서 노트 밀도가 달라진다.
3. 각 온셋 주변 파형을 FFT로 분석해 저음~고음 4개 대역 중 가장 에너지가 큰 대역을
   레인으로 배정한다 (베이스가 강하면 왼쪽 레인, 고음이 강하면 오른쪽 레인 식).
4. 일부 온셋은 확률적으로 롱노트(홀드)로 변환된다.
5. 결과 차트를 `charts/<파일해시>_<난이도>_<레인수>_v<버전>.json` 으로 캐싱한다.

## 파일 구조

```
rhythm_game/
├── main.py            # 진입점: 메뉴 -> 채보 생성 -> 플레이 -> 결과 루프
├── menu.py             # 곡/난이도 선택 화면
├── chart_generator.py  # mp3 -> 노트 차트 자동 생성 (librosa)
├── game.py              # 플레이 화면, 판정, 점수 계산
├── result_screen.py    # 결과(랭크/점수/정확도) 화면
├── hitsound.py          # 타격음 합성 (외부 파일 불필요)
├── config.py            # 화면/레인/판정/색상 등 상수
├── songs/               # 여기에 mp3를 넣는다
└── charts/              # 자동 생성된 채보 캐시 (자동 생성됨)
```

## 커스터마이징

- 레인 수를 6키로 바꾸려면 `chart_generator.generate_chart(..., lane_count=6)` 호출과
  `menu.py`에서 넘기는 값을 맞추면 된다 (`config.KEY_BINDINGS`에 6키 매핑 이미 있음).
- 노트 속도, 판정 타이밍(ms), 난이도별 온셋 민감도는 모두 `config.py`에서 조절 가능하다.
