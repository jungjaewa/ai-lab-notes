---
tags:
  - eye-tracking
  - mediapipe
  - opencv
  - affine-normalization
  - sprite-sheet
date: 2026-03-08
---

# Eye Animation Pipeline - R&D 과정 기록

> 날짜: 2026-03-08
> 목적: AI 영상에서 눈 애니메이션을 자동 추출하여 Unity NGUI 스프라이트 시트로 변환하는 파이프라인 개발
> 테스트 영상: grok_sample.mp4 (애니메 캐릭터, 카메라 줌인+회전, 24fps, 464x688, ~6초)

---

## Phase 1: 기본 파이프라인 구축

### 목표
AI로 생성한 눈 애니메이션 영상에서 눈 영역만 크롭하여 NGUI Atlas용 스프라이트 시트 + Unity Legacy AnimationClip을 자동 생성.

### 구현
- `--crop x,y,w,h` 로 고정 좌표 크롭
- 중복 프레임 자동 제거 (SSIM 유사도 기반)
- POT 스프라이트 시트 생성
- Unity Legacy AnimationClip (.anim YAML) + C# 헬퍼 스크립트 자동 생성
- float curve (frameIndex) + MonoBehaviour에서 UISprite.spriteName 매핑 방식

### 결과
- 정지 카메라 영상에서는 정상 동작
- **문제**: AI 영상은 카메라가 이동/줌하는 경우가 많아 고정 크롭으로는 눈을 못 잡음

---

## Phase 2: 템플릿 매칭 기반 추적 (`--track`)

### 목표
카메라가 이동하는 영상에서도 눈을 자동으로 따라가며 크롭.

### 접근
1. 기준 프레임(눈이 잘 보이는 프레임)에서 눈 영역을 템플릿으로 추출
2. 매 프레임에서 이전 위치 ±search_range 내에서 템플릿 매칭 (TM_CCOEFF_NORMED)
3. 매칭 신뢰도 < threshold 이면 눈 미발견으로 스킵
4. 자동 기준 프레임 탐색: 라플라시안 분산이 가장 높은 프레임 선택

### 추가 기능
- `--ref-frame`: 수동 기준 프레임 지정
- `--track-threshold`: 매칭 신뢰도 임계값 (기본 0.6)
- `--search-range`: 탐색 범위 제한 (기본 ±50px)
- 디버그 이미지 자동 생성 (초/중/후반 프레임에 녹색 박스)

### 테스트 결과 (grok_sample.mp4)
```
Tracked: 45 frames, Skipped: 28
Confidence: min=0.627, max=1.000
X range: 93~202 (delta=109)
Y range: 159~291 (delta=132)
```

### 문제점
- **드리프트 심각**: X delta=109px, Y delta=132px
- 카메라 줌인하면서 눈의 크기/각도가 변하면 초기 템플릿과 매칭이 안 됨
- 후반부에서 코, 입, 머리카락 영역을 눈으로 오인
- 디버그 이미지 확인:
  - Frame 56: 눈 정확 추적
  - Frame 100: 코/입으로 드리프트
  - Frame 144: 머리카락만 포착 (완전 이탈)

### 결론
템플릿 매칭은 **정지 카메라 or 매우 작은 움직임**에서만 유효. AI 영상의 줌/회전에는 부적합.

---

## Phase 3: MediaPipe Face Mesh 도입 (`--face`)

### 목표
프레임마다 독립적으로 얼굴 랜드마크를 검출하여 드리프트 문제 해결.

### 접근
- MediaPipe FaceLandmarker (tasks API, 478 랜드마크, iris 포함)
- 모델: `face_landmarker.task` (float16, 3.6MB)
- 양쪽 눈 윤곽 + 홍채 랜드마크의 중심점을 눈 중심으로 계산
- `--eye-which both|left|right` 로 양쪽/한쪽 선택 가능

### 핵심 랜드마크 인덱스
```
LEFT_EYE  = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
LEFT_IRIS  = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]
```

### MediaPipe 버전 이슈
- mediapipe 0.10.32에서는 `mp.solutions.face_mesh` (legacy API) 제거됨
- 새 API: `mp.tasks.vision.FaceLandmarker`
- `RunningMode.IMAGE` 사용 (프레임별 독립 검출)
- 모델 파일 별도 다운로드 필요

### 테스트 결과 (1-pass, grok_sample.mp4)
```
Tracked: 59/73 frames, Skipped: 14 (no face detected)
Eye center X: 227~244 (delta=17)
Eye center Y: 218~254 (delta=36)
```

### 개선점
- **드리프트 완전 해결**: X delta 109→17, Y delta 132→36
- 검출률 향상: 61% → 81%
- 전 프레임에서 눈 정확 추적 (디버그 이미지 확인)

### 남은 문제
- **프레임간 미세 jitter**: 평균 1.18px, 최대 5.52px
- 58%의 프레임에서 1px 이상 위치 점프
- 재생 시 눈이 약간씩 흔들리는 현상

---

## Phase 4: 가우시안 스무딩

### 목표
프레임간 미세 jitter 감소.

### 접근
- 눈 중심 좌표에 가우시안 가중 이동 평균 적용
- `--smooth N` (윈도우 크기, 홀수)
- 검출 실패 프레임은 선형 보간으로 채움

### 윈도우 크기별 비교 (grok_sample.mp4)
```
Raw (no smooth):   avg=1.18px, max=5.52px, >1px: 58% (42/72)
Smooth w=5:        avg=0.95px, max=3.06px, >1px: 42% (30/72)
Smooth w=7:        avg=0.92px, max=2.76px, >1px: 40% (29/72)
Smooth w=11:       avg=0.88px, max=2.24px, >1px: 43% (31/72)
```

### 결론
- 20~30% 개선되지만 **근본 해결은 아님**
- 이 영상은 카메라가 실제로 줌인하므로 눈 위치가 정당하게 이동
- 가우시안을 세게 하면 실제 이동까지 뭉개짐

---

## Phase 5: 데드존 안정화

### 목표
미세 jitter는 무시하고, 의미 있는 이동만 반영.

### 접근
- 이전 프레임 대비 이동 < deadzone(2px) 이면 위치 고정
- 이동 > deadzone 이면 거리 비례 블렌딩으로 부드럽게 갱신

### 테스트 결과
```
Raw jitter:    avg=1.18px, max=5.52px, >1px: 42/72
Stable jitter: avg=0.81px, max=4.41px, >1px: 25/72
```

### 결론
- 소폭 개선 (>1px 비율: 58% → 35%)
- 여전히 카메라 줌에 의한 실제 이동이 jitter로 남음
- **근본 문제**: 스프라이트 시트 용도에서는 카메라 이동 자체가 불필요. 눈의 "상대적 위치"가 동일해야 함.

---

## Phase 6: 아핀 정규화 (최종 해결)

### 핵심 인사이트
게임 스프라이트에서는 눈의 **절대 위치**가 아닌 **상대 위치(구도)**가 일정해야 함.
카메라 줌/회전/이동과 무관하게 양쪽 눈이 항상 같은 자리에 오도록 정규화하면 jitter가 원리적으로 0이 됨.

### 접근: 2-pass 아핀 정규화
```
Pass 1: 전체 프레임에서 양쪽 눈 중심 좌표 수집 (MediaPipe)
         ↓
가우시안 스무딩 (랜드마크 노이즈 제거)
         ↓
Pass 2: 기준 프레임 대비 아핀 변환 → 정규화된 크롭
```

### 아핀 변환 계산
각 프레임에서 3가지를 보정:

1. **이동 보정 (Translation)**
   - 현재 양쪽 눈 중점 → 출력 이미지 중앙으로 이동

2. **스케일 보정 (Scale)**
   - 현재 눈 간 거리 / 기준 눈 간 거리 → 줌 차이 보정
   - `scale = ref_dist / cur_dist`

3. **회전 보정 (Rotation)**
   - 현재 눈 연결선 각도 vs 기준 각도 차이 → 고개 기울임 보정
   - `rot = ref_angle - cur_angle`

변환 행렬:
```python
cos_r = cos(rot) * scale
sin_r = sin(rot) * scale
M = [[cos_r, -sin_r, out_mid_x - cos_r*cur_mid_x + sin_r*cur_mid_y],
     [sin_r,  cos_r, out_mid_y - sin_r*cur_mid_x - cos_r*cur_mid_y]]

eye = cv2.warpAffine(frame, M, (crop_w, crop_h), flags=INTER_LANCZOS4)
```

### 테스트 결과 (grok_sample.mp4)
```
Reference: eye dist=38.6px, angle=-6.6deg
Reference midpoint: (244, 224)
Raw position jitter: avg=1.47px, max=5.52px
Affine output: all frames normalized to same eye position (0px jitter)
Result: 73 frames → dedup → 35 unique
```

### 핵심 성과
| 지표 | 템플릿 매칭 | Face Mesh 1-pass | 아핀 정규화 |
|---|---|---|---|
| 위치 안정성 | 드리프트 | avg 1.18px | **0px** |
| 줌 대응 | 불가 | 대응 (크기 변함) | **정규화 (크기 고정)** |
| 회전 대응 | 불가 | 대응 (각도 변함) | **정규화 (각도 고정)** |
| 프레임 흔들림 | 심각 | 약간 | **없음** |

### 부가 효과
- 검출 실패 프레임(14/73)도 선형 보간으로 복원 → 73프레임 전부 사용 가능
- 눈이 안 보이는 초반(뒤돌아본 상태)은 보간된 좌표로 크롭되므로 콘텐츠는 의미 없음 → 실사용 시 해당 구간 제외 필요
- `INTER_LANCZOS4` 보간으로 서브픽셀 품질 유지

---

## 전체 진화 경로 요약

```
고정 크롭 ──→ 템플릿 매칭 ──→ Face Mesh ──→ 가우시안 스무딩 ──→ 아핀 정규화
(Phase 1)     (Phase 2)       (Phase 3)     (Phase 4-5)        (Phase 6)

정지 카메라만   드리프트 심각    jitter 1.18px   jitter 0.81px     jitter 0px
                                                                  스케일/회전 정규화
```

---

## 최종 파이프라인 사용법

```bash
# 권장 (Face Mesh + 아핀 정규화)
python eye_anim_pipeline.py \
  --video eye_blink.mp4 \
  --face \
  --eye-size 200,80 \
  --smooth 5 \
  --name char01_eye \
  --fps 10 \
  --output ./output/eye_anim \
  --dedup 0.95 \
  --save-frames
```

### 출력물
| 파일 | 설명 |
|---|---|
| `{name}_sheet.png` | 스프라이트 시트 (POT, RGBA) |
| `{name}_sprites.json` | 스프라이트 좌표 메타데이터 |
| `{name}.anim` | Unity Legacy AnimationClip |
| `{ClassName}.cs` | C# 헬퍼 (frameIndex → spriteName) |
| `facemesh_debug_*.png` | 추적 디버그 이미지 |
| `frames/` | 개별 프레임 (--save-frames) |

### 주요 파라미터 가이드
| 파라미터 | 권장값 | 설명 |
|---|---|---|
| `--eye-size` | 200,80 (양쪽) / 100,60 (한쪽) | 크롭 크기. 게임 해상도에 맞게 조절 |
| `--smooth` | 5~7 | 스무딩 강도. 클수록 안정적 but 반응 느림 |
| `--fps` | 8~12 | 스프라이트 수에 직접 영향 |
| `--dedup` | 0.93~0.97 | 낮을수록 공격적 제거 |
| `--eye-which` | both | 양쪽 눈 한 번에 / left,right 개별 |

---

## 기술 의존성

| 패키지 | 버전 | 용도 |
|---|---|---|
| opencv-python | 4.x | 영상 처리, warpAffine |
| opencv-contrib-python | 4.x | guidedFilter (differential matting용) |
| mediapipe | 0.10.32+ | FaceLandmarker (tasks API) |
| numpy | 1.x | 수치 연산 |

### 모델 파일
- `models/face_landmarker.task` (3.6MB)
- 출처: Google MediaPipe (float16)
- 자동 다운로드 아님 → 수동 배치 또는 스크립트 필요

---

## 향후 과제

- [ ] 생성된 스프라이트 시트를 실제 NGUI Atlas에 등록하여 Unity에서 확인
- [ ] 눈이 안 보이는 프레임 자동 필터링 (현재는 보간으로 무의미한 프레임 생성)
- [ ] 입/표정 영역으로 확장 가능성 검토
- [ ] 다양한 AI 영상 생성 모델(Grok, Runway, Kling 등) 호환성 테스트
- [ ] 배치 처리 (여러 캐릭터 한번에)
