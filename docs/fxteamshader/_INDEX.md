# FX Team Shader Documentation

AI가 셰이더 작업을 이어받거나 신규 개발할 때 항상 이 파일을 먼저 읽고, 필요한 파일을 추가로 읽는다.

## 문서 구조

| 파일 | 용도 | 언제 읽는가 |
|---|---|---|
| `_INDEX.md` | 이 파일. 전체 지도. | 항상 먼저 |
| `_project_rules.md` | 모든 셰이더에 적용되는 프로젝트 공통 제약 | 모든 작업 전 |
| `fxs_shine_rect_overview.md` | fxs_shine_rect 기능 개요 + 전체 프로퍼티 레퍼런스 | 이 셰이더 작업 전 |
| `fxs_shine_rect_technical.md` | 구현 수학, 설계 결정 근거, 개발 히스토리 | 수정/개선 작업 전 |

## 셰이더 목록

| 셰이더 | 파일 경로 | 상태 |
|---|---|---|
| `FX Team/fxs_shine_rect` | `Assets/PlatformAsset/Classic/DirectLinkResource/VFX/Shaders/fxs_shine_rect.shader` | 개발 완료 |

## 작업 지시 방법

신규 셰이더 작업 시:
1. `_project_rules.md` 읽기
2. 가장 유사한 기존 셰이더의 overview + technical 읽기
3. 일관된 프로퍼티 명명 규칙, 태그, 블렌드 설정 유지

기존 셰이더 개선 시:
1. `_project_rules.md` + 해당 셰이더 두 파일 모두 읽기
2. 개선 후 technical.md의 히스토리 섹션 업데이트
