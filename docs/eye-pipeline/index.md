---
tags:
  - eye-tracking
  - unity
  - mediapipe
  - pipeline
---

# Eye Animation Pipeline

AI 영상에서 눈 애니메이션을 자동 추출하여 Unity NGUI 스프라이트 시트로 변환하는 파이프라인.

## 문서 목록

| 문서 | 설명 |
|---|---|
| [아바타 애니메이션 리서치](research.md) | 전체 기법 비교 및 아키텍처 결정 과정 |
| [R&D 과정 로그](rnd-log.md) | 6단계 진화 과정 상세 기록 |

## 기술 스택

- Python, OpenCV, MediaPipe FaceLandmarker
- Unity Legacy Animation, NGUI Atlas
- 아핀 정규화 (2-pass)

## 핵심 결과

```
고정 크롭 → 템플릿 매칭 → Face Mesh → 가우시안 스무딩 → 아핀 정규화
(정지만)     (드리프트)     (1.18px)    (0.81px)          (0px)
```
