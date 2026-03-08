# PSD Layer Exporter - 도구 가이드 총 목차

PSD 파일의 레이어를 개별 이미지로 추출하는 도구 모음.
2D 게임 캐릭터 리깅/애니메이션(Spine, Unity UGUI 등) 워크플로우에 최적화.

---

## 도구 비교표

| 도구 | Photoshop 필요 | 속도 (20레이어) | Unity Export | 추천 용도 |
|------|:-:|:-:|:-:|------|
| **Qt GUI** (`psd_extractor_gui_qt.py`) | X | ~3.6초 | O | **일반 사용 (권장)** |
| **CTk GUI** (`psd_extractor_gui.py`) | X | ~3.6초 | X | 레거시 유지 |
| **CLI** (`psd_extractor.py`) | X | ~3.6초 | X | 배치/자동화 |
| **Python COM** (`layer_exporter.py`) | O | ~156초 | X | PS 효과 정확 재현 |
| **JSX Script** (`LayerExporter.jsx`) | O | ~148초 | X | PS 내부 직접 실행 |

---

## 빠른 시작

### 설치
```bash
pip install PySide6 psd-tools Pillow
```

### Qt GUI 실행 (권장)
```bash
python psd_extractor_gui_qt.py
```
1. Browse → PSD 파일 선택
2. 내보낼 레이어 체크
3. 출력 폴더 설정 → **EXPORT**

### CLI 실행
```bash
# 레이어 목록
python psd_extractor.py list ch.psd

# 내보내기
python psd_extractor.py export ch.psd -o ./out --visible-only --even-pad 2
```

---

## 상세 문서

| 문서 | 내용 |
|------|------|
| [psd_extractor_gui_qt.md](psd_extractor_gui_qt.md) | Qt GUI 전체 사용법 (화면 구성, 조작법, 설정, Unity Export) |
| [psd_extractor_gui_ctk.md](psd_extractor_gui_ctk.md) | CustomTkinter GUI 사용법 (레거시) |
| [psd_extractor.md](psd_extractor.md) | CLI 사용법, 옵션, 아키텍처, 성능 |
| [layer_exporter.md](layer_exporter.md) | Photoshop COM/JSX 도구 사용법 |

---

## 공통 기능

### 레이어 이름 변경 (3가지 모드)

| 모드 | 설명 | 예시 |
|------|------|------|
| **Manual** | 직접 입력 | `fxt_ch_hand_R` |
| **Sequential** | 접두사+순번 | `fxt_ch_01`, `fxt_ch_02`, ... |
| **Body Part** | 한글→영문 자동 | `오른손` → `fxt_ch_hand_R` |

### 패딩 모드

| 모드 | 설명 | 예시 (원본 73x58) |
|------|------|-----|
| **None** | 패딩 없음 | 73x58 |
| **Even** | +N px 후 짝수 맞춤 | +2 → 76x60 |
| **Fixed** | W/H 별도 지정 | +20/+20 → 93x78 |

### 출력 포맷

| 포맷 | 배경 | 용도 |
|------|------|------|
| **PNG** | 투명 (RGBA) | 게임 에셋, UI (기본/권장) |
| **JPEG** | 흰색 | 참고용, 웹 |

---

## Unity UGUI Export (Qt GUI 전용)

PSD 레이어를 Unity에서 원본 위치 그대로 UGUI로 재현.

### 사용법
1. Qt GUI에서 Settings의 **Unity** 체크 ON
2. **EXPORT** → 이미지 + `_unity_layout.json` + `PSDImporter.cs` 생성
3. Unity 프로젝트 `Assets/Sprites/`에 복사
4. `PSDImporter.cs`를 `Assets/Editor/`에 복사
5. Unity 메뉴 **Tools > PSD Layer Importer** → Setup Sprites → Import

### 생성되는 Unity 계층
```
Canvas (ScreenSpaceOverlay)
└── 캐릭터명 (root, PSD 캔버스 크기)
    └── Group (빈 GameObject)
        ├── layer_01 (RectTransform + Image)
        ├── layer_02 (RectTransform + Image)
        └── ...
```

상세: [psd_extractor_gui_qt.md](psd_extractor_gui_qt.md#7-unity-ugui-export)

---

## 어떤 도구를 선택해야 할까?

| 상황 | 추천 도구 |
|------|----------|
| 일반적인 레이어 추출 | **Qt GUI** |
| Unity UGUI에 레이어 배치 | **Qt GUI** (Unity 체크 ON) |
| CI/CD, 배치 자동화 | **CLI** (`psd_extractor.py`) |
| 드롭쉐도우 등 PS 효과 정확 재현 | **Photoshop COM** (`layer_exporter.py`) |
| Photoshop 내부에서 직접 실행 | **JSX** (`LayerExporter.jsx`) |

---

## 프로젝트 구조

```
d:\_AI Tool\PSD\
  psd_extractor_gui_qt.py   # GUI (PySide6, 권장)
  psd_extractor_gui.py      # GUI (CustomTkinter, 레거시)
  psd_extractor.py          # Standalone CLI (백엔드 공유)
  layer_exporter.py          # Photoshop COM 기반 CLI
  LayerExporter.jsx          # Photoshop 내장 스크립트
  photoshop_theme.json       # CTk GUI 테마
  rename_config.json         # 레이어 이름 변경 설정
  requirements.txt           # Python 의존성
  CLAUDE.md                  # 프로젝트 개요 (AI 컨텍스트)
  docs/
    README.md                # 이 파일 (도구 가이드 총 목차)
    psd_extractor_gui_qt.md  # Qt GUI 상세
    psd_extractor_gui_ctk.md # CTk GUI 상세
    psd_extractor.md         # CLI 상세
    layer_exporter.md        # Photoshop 도구 상세
  _sample/
    ch.psd                   # 테스트용 PSD
```
