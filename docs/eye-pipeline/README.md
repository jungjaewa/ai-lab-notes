# Depth-Based Auto Weight Tool for Spine2D

Depth 이미지를 활용하여 Spine2D 메시의 웨이트를 자동으로 계산하는 도구.

## 핵심 원리

2D 얼굴 원화에서 depth(깊이) 정보를 추출하여, 각 버텍스가 본(bone) 움직임에 얼마나 반응해야 하는지를 자동으로 계산합니다.

```
원화 PNG → Depth 이미지 (AI 생성) → 버텍스별 depth 샘플링 → 웨이트 자동 계산 → Spine JSON 출력
```

- depth가 낮은(앞쪽) 버텍스: 고개 회전 시 더 많이 이동 → 입체감
- depth가 높은(뒤쪽) 버텍스: 고개 회전 시 적게 이동 → 시차 효과

## 프로젝트 구조

```
depth-auto-weight/
├── src/
│   ├── main.py              # 메인 실행 스크립트
│   ├── spine_parser.py      # Spine JSON 파서 (본/메시/슬롯 추출)
│   ├── depth_sampler.py     # Depth 이미지 로더 및 샘플러
│   ├── depth_to_weight.py   # Depth → Weight 변환 엔진
│   └── spine_exporter.py    # 결과를 Spine JSON으로 내보내기
├── samples/
│   └── sample_face.json     # 테스트용 Spine 데이터
├── output/                  # 출력 디렉토리
└── README.md
```

## 설치

```bash
# 필수
pip install Pillow numpy

# Depth 이미지 AI 자동 생성 시 (선택)
pip install torch torchvision transformers
```

## 사용법

### 1. 데모 실행

```bash
cd src
python main.py --demo
```

### 2. 실제 파일 처리

```bash
python main.py --spine avatar.json --depth avatar_depth.png --output avatar_weighted.json
```

### 3. Depth 이미지 준비 방법

**방법 A: AI 모델로 자동 생성 (권장)**
- Depth Anything V2: https://huggingface.co/depth-anything/Depth-Anything-V2-Large
- 원화 PNG를 입력하면 depth 이미지를 자동 생성

**방법 B: 수동 제작**
- 포토샵에서 그레이스케일로 직접 그리기
- 밝을수록 가까움 (코, 이마), 어두울수록 멀음 (귀, 측면)

## 본 역할별 웨이트 전략

| 본 역할 | 전략 | depth 활용 |
|---------|------|-----------|
| head_turn (좌우 회전) | depth 기반 시차 | 앞쪽 = 많이 이동 |
| head_nod (상하 끄덕임) | depth + Y위치 | 앞쪽 = 많이 이동 |
| facial (눈, 입 등) | 거리 + depth 보정 | 앞쪽 = 변형 강하게 |
| body (전신) | 균일 + 미세 depth | 약간의 입체감 |

## 본 설정 파일 (JSON)

커스텀 본 설정을 사용하려면:

```json
{
  "normalize": true,
  "smoothing_iterations": 2,
  "smoothing_factor": 0.25,
  "bones": [
    {
      "name": "head_turn_bone",
      "role": "head_turn",
      "influence_radius": 200,
      "depth_sensitivity": 1.2,
      "falloff_curve": 1.5,
      "use_gradient": true,
      "gradient_sensitivity": 0.4
    },
    {
      "name": "eye_L",
      "role": "eye_left",
      "influence_radius": 40,
      "depth_sensitivity": 0.8
    }
  ]
}
```

```bash
python main.py --spine avatar.json --depth depth.png --bone-config bones.json --output result.json
```

## 파라미터 설명

- `depth_sensitivity`: depth 반영 강도 (0=무시, 1=기본, 2=강하게)
- `influence_radius`: 본의 영향 범위 (Spine 좌표 단위)
- `falloff_curve`: 거리 감쇠 곡선 (1=선형, 2=부드러움, 3=급격)
- `use_gradient`: depth 기울기(표면 방향) 사용 여부
- `gradient_sensitivity`: 기울기 반영 강도
