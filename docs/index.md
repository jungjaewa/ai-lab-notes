---
tags:
  - home
---

# AI Lab Notes

AI R&D 실험 노트 모음. 다양한 AI 프로젝트의 연구 과정과 결과를 기록합니다.

---

## 프로젝트 목록

### Eye Animation Pipeline

AI 영상에서 눈 애니메이션을 자동 추출하여 Unity NGUI 스프라이트 시트로 변환하는 파이프라인.

| 문서 | 설명 |
|---|---|
| [아바타 애니메이션 리서치](eye-pipeline/research.md) | 기법 비교, 아키텍처 결정, 용도별 분리 전략 |
| [R&D 과정 로그](eye-pipeline/rnd-log.md) | 고정크롭 → 템플릿매칭 → Face Mesh → 아핀 정규화까지 6단계 진화 |

**핵심 성과**: MediaPipe Face Mesh + 아핀 정규화로 카메라 줌/회전 영상에서 jitter 0px 달성

---

## 업데이트 이력

| 날짜 | 내용 |
|---|---|
| 2026-03-08 | Eye Pipeline: 아핀 정규화 완성, R&D 로그 작성 |
| 2026-03-08 | 아바타 애니메이션 리서치 문서 정리 |
