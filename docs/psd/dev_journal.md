# PSD Layer Exporter - 개발 일지

이 문서는 PSD Layer Exporter 프로젝트의 개발 의도, 진행 과정, 전환 결정, 개선 사항을 시간순으로 기록한 일지입니다.

---

## 배경: 왜 이 도구를 만들게 되었나

2D 게임 캐릭터 애니메이션(Spine, Live2D, Unity UGUI) 작업에서는 포토샵 PSD 파일의 레이어를 개별 PNG로 추출하는 작업이 반복적으로 필요합니다. 기존에는 포토샵에서 수동으로 레이어를 하나씩 숨기고/보이고/저장하는 방식이었고, 레이어가 20개만 넘어도 상당한 시간이 소요되었습니다.

**핵심 요구사항:**
- 캐릭터 파츠(손, 팔, 다리 등)를 개별 투명 PNG로 추출
- 한글 레이어 이름을 영문 리깅 규칙(`fxt_ch_hand_R` 등)으로 일괄 변환
- 짝수 패딩(텍스처 아틀라스 호환)
- 반복 작업을 최소화하는 자동화

---

## Phase 1: Photoshop 기반 도구 (시작점)

### LayerExporter.jsx — Photoshop 내장 스크립트

가장 먼저 시도한 방법. Photoshop의 ExtendScript(JSX)로 직접 레이어를 순회하며 export.

- **장점**: Photoshop의 모든 효과(드롭쉐도우, 블렌딩 등)를 정확히 재현
- **단점**: ScriptUI 다이얼로그가 단순하고, 20레이어 기준 **~148초** 소요
- **핵심 최적화**: 문서 복제 → `rasterizeAll` → crop 기반 trim 방식으로 개선했지만 근본적 속도 한계

### layer_exporter.py — Python COM 연결

JSX를 Python에서 제어하려는 시도. `photoshop-python-api`로 COM 연결 후 `eval_javascript()`로 JSX 실행.

- Python CLI 인터페이스 (`list`, `rename`, `export` 커맨드)
- 이름 변경 로직을 Python 쪽에서 유연하게 처리 가능
- 하지만 **Photoshop이 반드시 실행 중이어야** 하고, COM 오버헤드로 **~156초** 소요

**이 시점의 판단**: Photoshop에 의존하는 한 속도 개선에 한계가 있다. Photoshop 없이 PSD를 직접 읽을 수 있는 방법이 필요.

---

## Phase 2: Standalone 추출기로 전환

### psd_extractor.py — psd-tools + Pillow

Photoshop 의존성을 완전히 제거한 독립 CLI 도구. `psd-tools` 라이브러리로 PSD를 직접 파싱.

- 20레이어 기준 **~3.6초** (Photoshop 방식 대비 **41배 빠름**)
- `collect_layers()` → `filter_export_layers()` → `extract_layer_image()` → `apply_padding()` 파이프라인
- 3가지 이름 변경 모드: Manual, Sequential, Body Part (한글→영문 자동 매핑)
- `rename_config.json`으로 이름 매핑 외부 설정

**전환 결정 근거**: 2D 리깅용 캐릭터 파츠는 대부분 단순 픽셀 레이어이므로 Photoshop 효과 정확 재현이 불필요. 속도가 압도적으로 중요.

이 파일은 이후 모든 GUI 도구의 **공유 백엔드**가 됨. GUI들은 이 파일의 함수를 import하여 사용.

---

## Phase 3: GUI 개발 — CustomTkinter

### psd_extractor_gui.py — 첫 번째 GUI

CLI만으로는 레이어 선택/프리뷰/이름 변경이 불편해서 GUI를 개발.

- CustomTkinter + Photoshop 스타일 다크 테마 (`photoshop_theme.json`)
- CTkScrollableFrame으로 레이어 목록, CTkLabel로 프리뷰
- 체크박스 선택, Visible 필터, 패딩 옵션 등 기본 기능 완성

**발견된 문제점:**
- **위젯 생성 성능 이슈**: CTkScrollableFrame 안에 레이어마다 개별 위젯(체크박스, 라벨, 엔트리)을 생성하는 구조. 레이어 50개만 넘어도 로딩이 느려짐
- 프리뷰가 CTkLabel 이미지로 단순해서 줌/패닝 불가
- 다중 선택(Shift+Click, Ctrl+Click) 미지원
- 스레딩이 `threading.Thread`로 단순 — Signal/Slot 패턴 없음

**이 시점의 판단**: CustomTkinter의 위젯 기반 리스트는 구조적 한계. Qt의 Model/View 가상화가 필요.

---

## Phase 4: Qt GUI로 포팅 — 대규모 리팩토링

### psd_extractor_gui_qt.py — PySide6 기반 재개발

CustomTkinter 버전의 모든 기능을 유지하면서 아키텍처를 완전히 새로 설계.

#### 핵심 아키텍처 결정

| 항목 | CTk 버전 | Qt 버전 | 전환 이유 |
|------|---------|---------|----------|
| 레이어 리스트 | ScrollableFrame (개별 위젯) | QListView + QAbstractListModel | **가상화**: 200개 레이어도 동일 속도 |
| 행 렌더링 | 위젯 조합 | QStyledItemDelegate.paint() | 위젯 오버헤드 제거 |
| 프리뷰 | CTkLabel 이미지 | QGraphicsView + Scene | 줌, 패닝, 아웃라인 지원 |
| 스레딩 | threading.Thread | QThread + Signal/Slot | UI 스레드 안전 |
| 다중 선택 | 미지원 | ExtendedSelection | Ctrl/Shift+Click 지원 |
| 히스토리 | 미지원 | QComboBox + QSettings | PSD 파일 경로 영속 저장 |

#### 구현 순서

1. **기본 뼈대**: QMainWindow, 패널 레이아웃, 다크 테마 (Fusion + QPalette + QSS)
2. **레이어 리스트**: LayerListModel → LayerDelegate (paint 기반 커스텀 렌더링) → LayerListView
3. **프리뷰**: PreviewView (체커보드 배경, 줌 10%~1600%, 아웃라인 토글)
4. **스레딩**: PreloadTask, ThumbnailTask, ExportWorker 분리
5. **키보드/마우스**: Space 토글, Ctrl+A, Shift 범위 선택, 더블클릭 핸들링
6. **세부 UI 다듬기**: SegmentedButton (Padding 모드), 간격/여백 미세 조정, QSS 스타일링

#### 세부 UI 조정 과정

Qt 포팅 후에도 여러 차례 UI 미세 조정을 거침:
- QGroupBox 패널 간 간격을 50% 축소 (공백이 과도했음)
- 프리뷰 체커보드 밝기 조정
- 레이어 리스트 delegate의 열(column) 배치 미세 조정
- Settings 패널을 한 줄(46px 높이)에 모든 옵션 배치

---

## Phase 5: Unity UGUI Export 기능 추가

### 개발 동기

PSD에서 추출한 이미지를 Unity에서 사용할 때, 각 레이어의 **원본 위치**를 수동으로 맞추는 것이 큰 고통이었음. "포토샵에서의 레이어 위치가 Unity UGUI에서 그대로 재현"되는 기능이 필요.

### 리서치

- psd-tools의 레이어 위치 API 조사: `layer.left`, `layer.top`, `layer.width`, `layer.height`, `layer.opacity`
- PSD 좌표계 (top-left, Y↓) → Unity UGUI 좌표계 (anchor top-left, pivot center, Y↑) 변환 공식 도출
- PhotoshopToSpine.jsx 참고: 기존 PSD→Spine 변환 도구의 메타데이터 구조 분석

### 좌표 변환 공식
```
unity.x = layer.left + layer.width / 2
unity.y = -(layer.top + layer.height / 2)
```

### 구현 내용

**Python 측 (`psd_extractor.py`):**
- `_get_group_path(layer)` — 레이어의 그룹 계층 경로 추출
- `collect_layer_metadata()` — JSON 직렬화 가능한 메타데이터 수집 (위치, 크기, 그룹, opacity, padded_size)

**Qt GUI 측 (`psd_extractor_gui_qt.py`):**
- Settings 패널에 "Unity" 체크박스 추가
- ExportWorker에서 JSON + C# 스크립트 파일 생성

**Unity C# 측 (`FXC_PSDImporter.cs`):**
- Python 파일 내 `_UNITY_IMPORTER_CS` 문자열 상수로 임베드
- Export 시 출력 폴더에 자동 복사
- EditorWindow: JSON 파싱 → Canvas 생성 → RectTransform + Image 자동 배치
- Setup Sprites 유틸리티: 텍스처 타입 일괄 변환
- group_path v2 지원, Undo 지원

### 발견된 이슈
- `psd.name`이 파일명이 아닌 "Root"를 반환 → `psd_filename` 파라미터 별도 전달로 해결
- 패딩 적용 시 `padded_size` 필드를 JSON에 포함하여 Unity 측 sizeDelta 정확도 보장

---

## Phase 6: 프리뷰 시스템 대폭 개선

### 개선 1: 머지 프리뷰 (PSD 로드 시 즉시 표시)

**이전**: PSD 로드 후 "Select a layer to preview" 텍스트만 표시. 레이어를 클릭해야 프리뷰.

**변경**: PSD 로드 시 전체 레이어가 합성된 머지 이미지를 프리뷰에 즉시 표시.

**속도 문제 발견 및 해결:**
- 처음에는 `psd.composite()` (모든 레이어 재합성)를 백그라운드에서 실행 → **~4초 딜레이**
- PSD 파일에는 저장 시 이미 렌더링된 플래트 이미지가 내장되어 있음을 발견
- `psd.topil()` (내장 이미지 읽기)로 교체 → **~44ms** (약 90배 빠름)
- `composite()`는 `topil()` 실패 시 폴백으로만 유지

### 개선 2: 클릭 토글 선택

**이전**: 레이어 클릭 → solo 프리뷰. 다른 레이어를 클릭해야 변경.

**변경**: 같은 레이어를 다시 클릭하면 선택 해제 → 머지 프리뷰로 복귀.

- `LayerListView.mousePressEvent`에서 `currentIndex() == index` 감지 → `clearSelection()` + `setCurrentIndex(QModelIndex())`
- `currentChanged`에서 invalid index → `preview_requested(-1)` emit → `_show_merged_preview()`

### 개선 3: 호버 프리뷰 (Dim)

**요구사항**: 레이어 위에 마우스를 올리면, 해당 레이어가 전체 합성 이미지에서 어디에 위치하는지 시각적으로 확인하고 싶다.

**구현:**
- `setMouseTracking(True)` + `mouseMoveEvent` / `leaveEvent`로 호버 감지
- `hover_changed` Signal로 호버 row 전달
- QPainter 합성: 머지 이미지를 낮은 투명도로 그리고, 호버 레이어만 100%로 그 위에 그림
- 레이어의 PSD 원본 위치(`layer.left`, `layer.top`)에 정확히 배치

**동작 정리:**
| 상태 | 프리뷰 |
|------|--------|
| PSD 로드 직후 | 머지 이미지 (즉시) |
| 레이어 호버 | Dim 머지 + 호버 레이어 100% |
| 레이어 클릭 | 해당 레이어만 solo |
| 같은 레이어 재클릭 | 머지 이미지 복귀 |
| 마우스 리스트 이탈 | 클릭 상태 복원 또는 머지 |

### 개선 4: Dim 사용자 설정

**요구사항**: 호버 시 비활성 레이어의 투명도를 사용자가 조절하고, 단색으로도 볼 수 있게 해달라.

**구현:**
- **Dim 슬라이더** (0~100%): 비활성 레이어 투명도 조절 (기본 30%)
- **Tint 체크박스 + 컬러 버튼**: 비활성 레이어를 단색 실루엣으로 표시 (QColorDialog)

**성능 보장 (캐시 전략):**
- `_hover_bg_qimage` 캐시: Tint on/off, 색상 변경 시에만 재생성
  - Tint OFF → 머지 이미지 그대로 사용
  - Tint ON → `QPainter.CompositionMode_SourceIn`으로 머지 알파 마스크에 단색 적용
- 투명도는 캐시 재생성 없이 draw 시점에 `setOpacity()`만 적용 → 슬라이더 즉시 반응
- 호버 시 합성 = 캐시된 배경 1회 draw + 레이어 1회 draw (2회 draw만으로 완료)

---

## Phase 7: 편의 기능 및 문서화

### Rename Prefix 더블클릭 기본값

Rename Prefix 필드를 더블클릭하면 `fxt_ch_` (프로젝트 기본 접두사)가 자동 입력. `eventFilter` 패턴으로 QLineEdit 더블클릭 감지.

### 문서 작성

- `docs/README.md` — 5개 도구 비교표 + 빠른 시작 가이드
- `docs/psd_extractor_gui_qt.md` — Qt GUI 전체 사용법 (화면 구성, 조작법, 설정, Unity Export)
- `docs/psd_extractor_gui_ctk.md` — CustomTkinter GUI 사용법 + Qt 버전과의 차이
- `docs/psd_extractor.md` — CLI 사용법, 옵션, 아키텍처, 성능
- `CLAUDE.md` — AI 컨텍스트용 프로젝트 개요 (아키텍처, 컬러 팔레트, 네이밍 규칙 등)

---

## Phase 8: 트리 뷰 고도화 — 접기/펼치기, 가이드라인

### 개선 1: Group 버튼 (Tree → Group 리네이밍)

**이전**: "Tree" 버튼으로 플랫/트리 모드를 토글하되, 그룹 헤더는 표시만 될 뿐 인터랙션 없음.

**변경**: 버튼명을 "Group"으로 변경하고, 그룹 헤더를 클릭하면 하위 레이어를 접거나 펼 수 있도록 개선.

**구현:**
- `_collapsed_groups` (set of tuple): 접힌 그룹의 전체 경로 추적
- `toggle_group_collapsed(row)`: 접힌 상태 토글 → `_rebuild_view()`
- delegate에서 접힌 그룹은 ▶, 펼친 그룹은 ▼ 아이콘으로 구분
- 접힌 그룹의 하위 그룹 헤더와 아트 레이어 모두 숨김
- 단일 클릭으로 토글 (delegate의 `editorEvent` 핸들링)

**결정 근거**: PSD에 그룹이 많은 캐릭터(팔, 다리, 얼굴 등)에서 작업 시, 현재 필요없는 그룹을 접어두면 리스트 스크롤이 줄어 작업 효율이 올라감.

### 개선 2: 프리뷰 오버레이 컨트롤 재배치

**이전**: Order/Visible/Deselect/Tree/Restore 버튼과 선택 슬롯/검색란이 프리뷰 **위**에 배치.

**변경**: 프리뷰 **아래**로 이동. 프리뷰 영역을 최대한 크게 확보하는 것이 실제 작업 시 더 유용하다는 판단.

### 개선 3: 프리뷰 상단 바 확장

**이전**: 줌% | ▢(아웃라인) | Fit 3개 컨트롤.

**변경**: 줌% | ✛(십자선) | ▢(아웃라인) | Info | Fit 5개 컨트롤.

- **십자선 (✛)**: 이미지 중심에 가로/세로 보조선을 표시. 캐릭터 리깅 시 좌우 대칭 확인에 유용. `drawForeground()`로 뷰포트 좌표에 그려서 줌에 영향 없음
- **Info**: 레이어 이름과 사이즈를 이미지 아웃라인 바로 아래에 표시. 토글 가능. 이전에는 프리뷰 하단에 별도 QLabel이었으나, 이미지 영역 내부에 직접 그리는 방식으로 변경

**Info 이동 이유**: 레이어 정보가 프리뷰 이미지와 물리적으로 분리되어 있으면 줌/패닝 시 시선 이동이 불편. 이미지 바로 아래에 붙여서 시각적 연결성 확보.

---

## Phase 9: Ollama LLM 기반 Auto Rename (KR→EN)

### 개발 동기

기존 Body Part 모드는 내장 딕셔너리(~40 단어)에 포함된 인체 파츠만 번역 가능. 하지만 실제 PSD 레이어에는 오브젝트(돌벽, 나무), 자연물(폭포, 바위), 인공물(검, 방패) 등 다양한 한글 이름이 있어, 딕셔너리만으로는 커버 불가.

**검토한 방법:**
1. 대형 딕셔너리 확장 — 끝없이 늘어나는 단어를 수동 관리하기 비현실적
2. Google Translate API — 네트워크 의존, 요금, 속도 느림 (~8초/호출)
3. 로컬 LLM (Ollama) — 오프라인, 무료, snake_case 포맷 직접 제어 가능

### 모델 선정 과정

| 모델 | 크기 | 한글→영문 품질 | 속도 |
|------|------|---------------|------|
| gemma3:4b | 3.3GB | 한글 인식 실패 (garbled) | - |
| qwen2.5:1.5b | 1.3GB | 낮음 (폭포→fallbrook) | ~2.2초 |
| **qwen2.5:3b** | **2.3GB** | **양호** (폭포→waterfall) | **~2.5초** |

- gemma3:4b는 Windows 터미널 인코딩 문제도 있었으나, Python `urllib.request`로 직접 호출해도 한글 해석 자체를 못함
- qwen2.5:3b가 품질-속도 균형 최적. Q4_K_M 양자화 버전 (Ollama 기본)

### 번역 아키텍처

**하이브리드 3단계:**
1. **내장 딕셔너리** (`_KO_BODY_PARTS_SPINE`/`_LIVE2D`) — 인체 파츠 즉시 매핑 (0ms)
2. **세션 캐시** (`_translation_cache`) — 이미 번역한 단어 재사용 (0ms)
3. **Ollama API** — 미스된 단어만 배치로 보내서 번역 (1회 호출로 다수 단어 처리)

### 성능 최적화

**문제 발견**: Ollama 첫 호출 시 모델 로딩에 ~2.5초 (프롬프트 처리), 이후 출력 생성은 ~0.5초.

**해결:**
- **모델 워밍업**: Auto 모드 선택 시 백그라운드에서 `_warmup_ollama()` 실행. 간단한 "hi" 요청으로 모델을 GPU 메모리에 미리 로드
- **비동기 UI**: `QRunnable` + `translate_done` Signal로 번역 중 UI 블로킹 방지. Apply 버튼 "..." + 상태 "Translating..." 표시

### 그룹 컨텍스트 전달 (동음이의어 해결)

**문제**: 같은 한글 단어라도 PSD 그룹에 따라 의미가 다름.
- `팔` 그룹의 `위` → `arm_upper` (팔 위쪽)
- `다리` 그룹의 `위` → `leg_upper` (다리 위쪽)
- `배경` 그룹의 `위` → `background_upper` (배경 위쪽)

**해결:**
- `_apply_auto_rename()`에서 각 레이어의 `group_path`를 수집
- Ollama 프롬프트에 `그룹>레이어` 형식으로 전달 (예: `팔>위`)
- 시스템 프롬프트에 그룹 컨텍스트 활용 규칙 명시 + few-shot 예시 포함
- 캐시 키도 그룹 포함: `팔/위` vs `다리/위`를 별도 캐시

### Windows 인코딩 이슈

curl로 Ollama에 한글을 보내면 Windows 터미널(CP949)에서 인코딩이 깨짐. Python `urllib.request`로 직접 HTTP 호출 + UTF-8 인코딩으로 해결. curl 의존성 제거.

---

## Phase 10: 세션 저장/불러오기

### 개발 동기

PSD를 열고 레이어 체크/가시성/이름 변경 작업을 한 후, 앱을 닫거나 다른 PSD로 전환하면 모든 작업 상태가 사라짐. 반복적으로 같은 설정을 다시 해야 하는 불편.

**요구사항:**
- 수동 저장 (Save 버튼) + 자동 저장 (PSD 전환/앱 종료 시)
- PSD 파일 옆에 저장 (프로젝트와 함께 관리)
- Rename 설정 (모드, Prefix, Preset 등)도 함께 저장

### 세션 파일 설계

- 경로: `{psd_path}.session.json` (예: `ch.psd.session.json`)
- 검증: 레이어 수가 달라지면 (PSD가 수정됨) 세션을 무시하고 새로 시작
- UTF-8, indent=2 (사람이 읽을 수 있는 JSON)

### 저장 항목

```json
{
  "version": 1,
  "psd_file": "ch.psd",
  "layers": {
    "checked": [true, false, ...],
    "visible": [true, true, ...],
    "renamed": ["leg_R", "", ...],
    "order_reversed": false,
    "tree_mode": true,
    "collapsed_groups": [["Group1"], ["Group1", "Sub"]]
  },
  "rename": {
    "mode": "Sequential",
    "seq_prefix": "fxt_ch_",
    "seq_start": "01",
    "seq_direction": "Top → Bottom",
    "bp_preset": "Spine",
    "bp_prefix": "",
    "auto_preset": "Spine",
    "auto_prefix": ""
  }
}
```

### 자동 저장 트리거

1. **PSD 전환 시**: `_load_psd()` 초반에서 이전 PSD 세션 자동 저장 후 새 PSD 로드
2. **앱 종료 시**: `closeEvent()` 오버라이드 → `_save_session()` 호출
3. **수동 저장**: Settings 하단의 Save 버튼 클릭

### 복원 순서

`_load_psd()` 끝에서 `_load_session()` 호출:
1. 레이어 수 검증 (불일치 → 무시)
2. `_art_checked`, layer `visible`, `_art_rename` 복원
3. 레이어 순서 (reversed) 복원
4. 트리 모드, 접힌 그룹 복원
5. Rename 위젯 값 복원
6. `_rebuild_view()` + `_rebuild_merged()` 호출

---

## Phase 11: Rename 중복 감지

### 개발 동기

Sequential이나 Auto 모드로 rename을 적용한 후, 동일한 export 이름이 생기면 파일 내보내기 시 덮어쓰기가 발생할 수 있음. 사전에 시각적으로 경고하여 중복을 인지할 수 있어야 함.

### 구현

- `_rename_duplicates` (set): `_art_rename`에서 2개 이상 등장하는 이름 집합
- `_refresh_rename_duplicates()`: rename 변경 시 호출, 중복 셋 재계산
- `setData(RenameRole)` 시 자동 갱신: 중복 상태 변경 시 전체 행 repaint
- delegate paint: `is_rename_duplicate(name)` → 빨간색(#e05050) 텍스트

**성능 고려**: 전체 행 repaint는 중복 상태가 실제로 변경된 경우에만 수행 (`old_dups != new_dups` 비교).

---

## 도구 진화 요약

```
Photoshop 의존                          Photoshop 불필요
(정확하지만 느림)                        (빠르고 자동화 가능)

LayerExporter.jsx ──┐
    (~148초)        │
                    ├──→ psd_extractor.py ──→ psd_extractor_gui.py (CTk, 레거시)
layer_exporter.py ──┘        (~3.6초)     │
    (~156초)                              └──→ psd_extractor_gui_qt.py (Qt, 권장)
                                                       │
                                                       ├── 가상화 리스트 (성능)
                                                       ├── 프리뷰 (줌/패닝/호버/십자선)
                                                       ├── Dim 설정 (투명도/틴트)
                                                       ├── 그룹 접기/펼치기
                                                       ├── Unity UGUI Export
                                                       ├── Ollama LLM 자동 번역
                                                       ├── 세션 저장/불러오기
                                                       ├── Rename 중복 감지
                                                       ├── 원본명 중복 경고
                                                       ├── 그룹 리네임 (UI + Auto 번역 + _group 서픽스)
                                                       ├── Rename Post-Edit (Find/Replace, +Prefix/Suffix, +#)
                                                       ├── Undo/Redo (Rename+Check+Visible, 30단계)
                                                       ├── Ollama 모델 프리로드 + 상태 애니메이션
                                                       ├── 번역 품질 개선 (복합어/딕셔너리/컨텍스트)
                                                       ├── 파일명 충돌 방지
                                                       ├── 트리 가이드 캐시 (O(n²)→O(n))
                                                       └── 다중 선택, 히스토리 등
```

## Phase 12: Unity Component 방식 + 실전 버그 수정 (2025-02-25)

### Unity v2 — Component 방식 전환

**개발 동기**: EditorWindow 방식(Tools > PSD Layer Importer)은 별도 창을 열고 경로를 매번 지정해야 하는 번거로움. 원하는 워크플로우는: 빈 GameObject 생성 → Add Component → JSON 드래그 → Build 클릭 → 끝.

**참고 자료**: [PhotoshopToSpine.jsx](https://github.com/EsotericSoftware/spine-scripts/tree/master/photoshop)의 PSD → JSON + 이미지 내보내기 구조를 Unity UGUI에 적용.

**구현:**
1. **JSON v2 포맷**: `blend_mode` (그룹+레이어), `group_path` (고유 그룹 경로), `version: 2`
2. **PSDLayoutBuilder.cs** (MonoBehaviour): TextAsset 드래그 앤 드롭, scaleFactor, matchCanvasSize, useTopLeftAnchor 옵션 — v3.0에서 FXC_PSDImporter.cs로 통합됨
3. **PSDLayoutBuilderEditor.cs** (Custom Editor): Build Layout / Clear Children / Setup Sprite 버튼, Undo 지원 — v3.0에서 FXC_PSDImporter.cs로 통합됨
4. **Python 템플릿 업데이트**: Export 시 C# 파일 출력 (v3.0에서 FXC_PSDImporter.cs 1개로 통합)

**설계 결정:**
- Canvas를 생성하지 않음 → 사용자가 배치 위치 결정
- Blend mode는 JSON 메타데이터에만 기록 → 실제 렌더링은 수동 설정 (셰이더 미구현)
- group_path로 동일 이름 그룹 충돌 방지 (v1은 name-only로 충돌 가능)

### 실전 테스트에서 발견된 문제들

box.psd (28레이어, 7그룹)로 테스트 중 3가지 문제 발견:

#### 1. 파일명 충돌 — 무음 덮어쓰기

**문제**: 동일 레이어명("뚜껑" × 2, "리본끝_우" × 2)이 같은 파일명으로 export → 두 번째가 첫 번째를 덮어씀. 사용자에게 경고 없음.

**해결**: `used_names` dict로 파일명 추적, 중복 시 `_1`, `_2` 접미사 자동 부여.
- 3곳 동시 수정: `collect_layer_metadata()`, `export_command()`, `ExportWorker.run()`

#### 2. 원본 레이어명 중복 사전 경고

**문제**: rename 하기 전에는 원본 이름이 중복인지 시각적으로 알 수 없음.

**해결**: `_orig_name_duplicates` 집합으로 PSD 로드 시 중복 계산. delegate에서 주황색(`#e0a050`) 표시 + "⚠ duplicate name" 플레이스홀더.

#### 3. 그룹 리네임 지원

**문제**: 한글 그룹명("보라상자" 등)이 Unity JSON에 그대로 출력. 그룹명을 변경할 수 있는 UI가 없음.

**해결**:
- `_group_rename_map` dict + `set_group_rename()` / `get_group_rename_map()` 메서드
- 트리 모드 그룹 헤더에 rename 입력란 추가 (클릭으로 편집)
- Auto (KR→EN) 모드에서 한글 그룹명도 Ollama로 자동 번역
- `collect_layer_metadata()`에 `group_rename_map` 파라미터로 JSON에 반영
- 세션 저장/복원에 `group_rename` 필드 추가

### Shift+Click 동작 수정

**문제**: Shift+Click 범위 선택 시 체크박스까지 변경됨. 선택(하이라이트)만 바뀌어야 함.

**해결**: mousePressEvent의 Shift 핸들러에서 `setData(CheckedRole)` 루프 제거, `super().mousePressEvent()` 만 호출.

### 성능 회귀 및 최적화

v2.1 변경 후 PSD 로딩 속도가 체감될 정도로 느려짐. 원인 분석 결과 3가지:

#### 1. 트리 가이드라인 O(n²) 문제

**원인**: `LayerDelegate.paint()`에서 매 행마다 아래 전체 행을 forward scan하여 가이드라인 연속 여부 계산. 100레이어 × 20행 뷰포트 = 2000+ data() 호출.

**해결**: `_compute_tree_guides()` 메서드 추가. `_rebuild_view()` 후 역순 1회 순회(O(n))로 `_tree_guide_cache` (frozenset per row)에 사전 계산. paint()에서는 캐시 조회만 수행.

#### 2. _load_session() 중복 rebuild

**원인**: `_load_psd()`가 이미 `set_layers()` → `_rebuild_view()` + `psd.topil()` → 프리뷰를 실행한 직후, `_load_session()`이 `_rebuild_view()` + `_rebuild_merged()` (PIL 전체 합성) + `_show_merged_preview()`를 다시 호출. `_rebuild_merged()`는 이 시점에 `_cached_img`가 없어서 빈 이미지만 만드는 무의미한 작업.

**해결**: `_rebuild_merged()` + `_show_merged_preview()` 제거. 세션 데이터 반영 후 `_rebuild_view()` 1회만 실행.

#### 3. 그룹 번역 N회 rebuild

**원인**: `_on_translate_done()`에서 그룹마다 `set_group_rename()` 호출 → 매번 `_rebuild_view()` 트리거.

**해결**: `_group_rename_map`에 일괄 할당 후 `_rebuild_view()` 1회만 호출.

---

## Phase 13: 세션 로드 최적화 + Restore 완전 복원 (2026-02-25)

### 세션 자동 로드 → 수동 로드 전환

**문제**: Phase 12의 최적화 이후에도 PSD 로딩이 여전히 느림. `_load_session()`이 `_load_psd()` 끝에서 자동 실행되면서:
1. `_toggle_layer_order()` → `reverse_order()` → `_rebuild_view()` (조건적)
2. `_tree_btn.setChecked()` → `_toggle_tree_mode()` → `set_tree_mode()` → `_rebuild_view()` (조건적)
3. 무조건 final `beginResetModel/endResetModel` + `_rebuild_view()` (항상)

**원인 분석**: 최대 3회의 중복 `_rebuild_view()` + 각 호출마다 `_compute_tree_guides()` + `beginResetModel/endResetModel` UI 리페인트. 23레이어 기준 불필요한 오버헤드.

**해결**:
1. **자동 로드 제거**: `_load_psd()`에서 `_load_session()` 호출 제거. 세션 파일 존재 시 로그 알림만 표시
2. **수동 Load 버튼 추가**: Settings 패널에 Save 옆에 Load 버튼 추가
3. **`_load_session()` 최적화**: 모든 상태를 먼저 적용 (시그널 차단, 직접 배열 reverse) 후 `_rebuild_view()` 1회만 실행
   - `_tree_btn.blockSignals(True)` → `setChecked()` → `blockSignals(False)` → `_tree_mode` 직접 설정
   - 레이어 순서 역순: `_toggle_layer_order()` 대신 배열 직접 reverse (rebuild 없이)
4. **머지 프리뷰 갱신**: 세션 복원 후 가시성 변경 반영을 위해 `_rebuild_merged()` + `_show_merged_preview()` 추가

### Restore 버튼 완전 복원

**문제**: Restore 버튼이 체크/가시성/rename만 복원하고 레이어 순서(reverse)와 트리 모드는 복원하지 않음. 세션에서 역순+트리 상태로 작업 후 Restore 누르면 불완전 복원.

**해결**: `_restore_initial_state()`에서:
1. `_layer_order_reversed == True`이면 배열 직접 reverse 후 플래그 리셋
2. `_tree_btn.blockSignals(True)` → `setChecked(False)` → `_tree_mode = False` → `_collapsed_groups.clear()`
3. `restore_initial_state()` 호출 (체크/가시성/rename/그룹rename 복원)
4. `_rebuild_merged()` + `_show_merged_preview()`로 머지 프리뷰 갱신

---

## Phase 14: Rename Post-Edit + Undo/Redo + 번역 품질 개선 (2026-02-25)

### Rename Post-Edit 도구

**개발 동기**: 1차 Rename(Auto/Sequential/Body Part) 후 결과를 미세 조정하는 기능이 필요. 프리픽스 추가(`lid` → `fxt_lid`), 서픽스 추가(`ribbon` → `ribbon_01`), 특정 단어 찾아 바꾸기(`box_inside` → `box_inner`) 등.

**구현:**
- Rename 바 아래에 인라인 후처리 도구 행 추가 (항상 표시)
- Find & Replace: 검색 텍스트를 대체 텍스트로 치환 (선택 레이어 또는 전체)
- +Prefix / +Suffix: 현재 rename 값 앞/뒤에 텍스트 추가
- +# 넘버링: 01 또는 001 형식으로 순번 서픽스 추가
- 넘버링 방향: ↓ (Top→Bottom) / ↑ (Bottom→Top) 선택
- Reset 버튼: 모든 Edit 필드 초기화
- Apply Edit 버튼: Prefix + Suffix + # 를 한번에 적용

### Rename 패널 분리

**결정**: Rename 관련 모든 UI를 레이어 목록 패널과 Settings 패널 사이에 독립 QGroupBox로 분리. `_build_rename_panel()`이 `_build_rename_tools()`와 `_build_post_edit_row()`를 래핑.

### Undo/Redo 시스템

**개발 동기**: Post-Edit로 rename을 수정한 후 결과가 마음에 안 들 때 되돌리기 기능이 필요. 초기에는 Rename 전용으로 구현, 이후 사용자 요청으로 Check + Visible까지 확장.

**구현:**
- `_undo_stack` / `_redo_stack`: 최대 30단계 스냅샷 스택
- 스냅샷 구조: `(art_rename[], group_rename_map{}, art_checked[], art_visible[])`
- 스냅샷 저장 시점: 모든 배치 작업(Auto/Sequential/Body Part/Find&Replace/Post-Edit/Clear) + 개별 체크/가시성 변경(checkbox 클릭, Space, E 키) + Restore/Deselect/Visible 버튼
- `state_will_change` Signal: `LayerListView`에서 체크/가시성/rename 변경 직전에 emit → 메인 윈도우에서 스냅샷 저장
- `_undo_batch` 플래그: 배치 작업 중 개별 스냅샷 방지 (중복 저장 방지)
- 복원 시 `_rebuild_merged()` + `_show_merged_preview()` 호출 (가시성 변경 반영)
- PSD 전환 시 스택 초기화
- UI: Edit 행의 `←` / `→` 버튼 + `Ctrl+Z` / `Ctrl+Shift+Z` 단축키

### Ollama 모델 프리로드

**문제**: Auto 모드 첫 사용 시 모델 로딩에 ~2.5초 딜레이 (콜드 스타트).

**해결**: `QTimer.singleShot(3000, window._preload_ollama)` — 앱 UI 표시 3초 후 백그라운드에서 Ollama에 "hi" 요청. 모델이 GPU 메모리에 미리 로드됨.

**주의**: HTTP 요청만 발생, Python 프로세스에 부하 없음. Ollama 서버 측에서 VRAM/RAM ~2-3GB 사용. 5분 미사용 시 자동 해제.

**시행착오**: 처음에 `__init__`의 `QTimer.singleShot(2000)`에 배치 → 앱 시작이 느려짐. lazy import도 시도했으나 PSD 로딩이 느려지기만 함 (import cost가 이동만 됨). 최종적으로 `window.show()` 후 `main()`에서 타이머 배치.

### 상태 애니메이션

**구현**: `_ollama_dot_timer` (QTimer, 400ms) — `·` → `··` → `···` 순환. `_on_ollama_status()` 중앙 핸들러에서 시작/중지. "…" 접미사가 있는 상태 텍스트에서 자동 활성화.

### 번역 품질 개선

**문제 1**: "fxt_tougal_tougal" — 그룹명=레이어명(뚜껑>뚜껑)일 때 모델이 두 단어를 합성.

**해결**: `_call_ollama()`에서 `ctx_g == part`이면 컨텍스트 생략 (레이어명만 전달).

**문제 2**: "tougal"은 "뚜껑"의 정확한 번역이 아님. qwen2.5:3b가 불안정하게 번역 (dome, doughnut, tougal 등 랜덤).

**해결**:
1. 딕셔너리에 일반 오브젝트/수식어 ~40개 추가 (뚜껑→lid, 상자→box, 리본→ribbon, 열린→open, 닫힌→closed, 큰→big, 작은→small 등)
2. 복합어 분리: "열린 뚜껑" → 공백으로 split → 각 단어 딕셔너리 조회 → "open_lid"

### 그룹 `_group` 서픽스

**결정**: AI가 그룹과 일반 레이어를 구분할 수 있도록 그룹 rename에 `_group` 서픽스 자동 추가. `_grp` vs `_group` 비교 후 AI 친화적인 전체 단어 선택.

### Alt+더블클릭 단어 선택

**구현**: `_RenameLineEdit(QLineEdit)` 서브클래스. Alt+더블클릭 시 커서 위치에서 `_` 구분자 기준 단어 경계를 찾아 해당 단어만 선택. 일반 더블클릭은 전체 선택 (기본 동작).

---

### 핵심 전환점들

1. **Photoshop → Standalone**: 41배 속도 향상. 2D 리깅 파츠는 효과 정확 재현이 불필요하다는 판단
2. **CustomTkinter → PySide6**: 위젯 기반 리스트의 구조적 한계. Model/View 가상화로 해결
3. **이미지 추출만 → 위치 메타데이터 포함**: Unity UGUI에서 원본 위치 재현 요구
4. **정적 프리뷰 → 인터랙티브 프리뷰**: 머지 즉시 표시, 호버 Dim, 클릭 solo, 토글 해제
5. **composite() → topil()**: 머지 프리뷰 속도 90배 개선 (PSD 내장 플래트 이미지 활용)
6. **딕셔너리 → LLM 번역**: 제한된 인체 파츠 매핑에서 범용 한글→영문 자동 번역으로 확장 (Ollama qwen2.5:3b)
7. **휘발성 작업 → 세션 영속화**: 체크/가시성/rename/설정을 JSON으로 보존, PSD 전환/앱 종료 시 자동 저장
8. **EditorWindow → Component 방식**: Unity Import를 별도 창 → Inspector 컴포넌트로 전환. JSON v2 포맷 (blend_mode, group_path)
9. **실전 테스트 → 견고화**: 파일명 충돌 방지, 원본명 중복 경고, 그룹 리네임 등 실제 PSD에서 발견된 엣지케이스 해결
10. **O(n²) → O(n) 최적화**: 트리 가이드라인 forward scan을 사전 계산 캐시로 교체, 중복 rebuild 제거
11. **자동 세션 로드 → 수동 로드**: PSD 열기 시 세션 자동 복원을 제거하여 로딩 속도 개선. 사용자가 필요 시 Load 버튼으로 수동 복원
12. **단일 Rename → Post-Edit 파이프라인**: 1차 Rename 후 Find/Replace, Prefix/Suffix, 넘버링으로 미세 조정하는 후처리 워크플로우 확립
13. **Rename 전용 Undo → 전체 상태 Undo/Redo**: Rename만 되돌리기에서 Check+Visible까지 확장. 30단계 스냅샷 스택 + Ctrl+Z/Shift+Z 단축키
14. **딕셔너리 + LLM 하이브리드 번역 고도화**: 복합어 분리, 동일명 컨텍스트 스킵, 일반 오브젝트 딕셔너리 확장으로 번역 정확도 향상
15. **Ollama 단일 → 멀티 Provider (Ollama/Groq)**: 로컬 Ollama 외에 Groq 클라우드 API 선택 가능. Groq는 32B 모델을 무료로 사용하며 속도 우수

---

## Phase 15: 번역 품질 개선 + Groq 클라우드 통합

### 프롬프트 컨텍스트 강화

기존 프롬프트는 직속 부모 그룹 1개만 전달 (`팔>위`). 개선 후:
- **PSD 파일명**: 이미지의 정체성(캐릭터/배경/UI)을 모델에 알려줌
- **전체 그룹 경로**: `캐릭터>팔>위` — 깊은 계층에서도 컨텍스트 유지
- **형제 레이어명**: 같은 그룹의 다른 레이어를 최대 6개 전달하여 맥락 파악

### Groq 클라우드 Provider 추가

Ollama(로컬) 외에 Groq(클라우드) 선택 가능한 Provider 체계 도입.

**Groq 장점:**
- Ollama 없이도 번역 가능 (인터넷만 있으면 됨)
- 무료 tier: 일일 1,000 요청 (qwen3-32b 등)
- 32B 모델 → 로컬 3b보다 한국어 이해력 현저히 우수
- LPU 기반 초고속 추론 (1,000+ tok/s)

**구현:**
- `_call_llm()` 통합 함수 → provider에 따라 Ollama/Groq 분기
- `_call_ollama_raw()` / `_call_groq_raw()` — 각 Provider별 HTTP 호출
- API 키: `.groq_api_key` 파일 → QSettings 순으로 로드, 앱 전역 저장
- Provider 변경 시 모델 목록 자동 교체 + 상태 확인
- 세션에 `auto_provider` 저장/복원

### API 키 메모

- **서비스**: Groq (https://console.groq.com)
- **키 이름**: PSD Layer
- **키 파일**: `.groq_api_key` (프로젝트 루트)
- **무료 한도**: 1,000 요청/일 (qwen/qwen3-32b 기준)

---

## Phase 16: UI/UX 개선 + Groq 고도화 + 패딩 옵션 + Unity 순서 수정 (2026-02-25)

### UI/UX 개선

#### 선택 하이라이트 색상 변경

**문제**: 선택된 레이어(`#3a3a3a`)와 비선택 레이어의 배경색 차이가 미미하여 구분 어려움.

**해결**: 선택 배경색을 `#2d3748` (다크 네이비)로 변경. 눈에 크게 띄지 않으면서도 여러 레이어 선택 시 눈이 아프지 않은 색상.

#### Space 포커스 모드

**요구사항**: 프리뷰 영역에서 Space 키를 누르면 레이어 리스트+프리뷰만 보이고 나머지 패널(PSD 경로, Rename, Settings, Export)은 모두 숨김.

**구현**:
- `PreviewView`에 `focus_mode_requested` Signal 추가
- `keyPressEvent`에서 Space 키 감지 → Signal emit
- `_toggle_focus_mode()`에서 `_file_panel`, `_rename_panel`, `_settings_panel`, `_output_panel` 4개 QGroupBox 토글
- 각 `_build_*_panel()` 메서드에서 QGroupBox 참조 저장

#### Ctrl+Enter Edit 단축키

Edit 행의 Find/Replace/Prefix/Suffix 4개 입력 필드에서 Ctrl+Enter → `_do_post_edit()` 실행. `QShortcut(WidgetShortcut)` 컨텍스트로 해당 필드 포커스 시에만 동작.

#### Save/Load 버튼 위치 이동

Settings 패널에서 프리뷰 하단 버튼 행으로 이동. Deselect 오른쪽에 `|` 구분선 + Save + Load 배치. 버튼 너비: 기존 72px, Save/Load 54px.

### Groq 클라우드 Provider 고도화

#### 동적 모델 목록

**문제**: Groq 모델이 4개만 하드코딩되어 있었음.

**해결**: `groq_models` Signal 추가. `_check_groq_status`에서 API 응답의 전체 모델 목록을 emit. `_on_groq_models()` 핸들러에서 동적 populate. 추천 모델(`qwen/qwen3-32b`, `llama-3.3-70b-versatile`)은 초록색(`#4ec94e`)으로 표시.

#### 추천 모델 색상 (QSS 오버라이드 문제)

**문제**: `setItemData(ForegroundRole)` 색상이 글로벌 QSS `QComboBox QAbstractItemView { color: #e0e0e0; }`에 의해 덮어써짐.

**해결**: `_ColorItemDelegate(QStyledItemDelegate)` 추가. `initStyleOption()`에서 `ForegroundRole` 색상을 palette에 직접 적용.

#### Groq 콘솔 링크 버튼

Key 버튼 오른쪽에 "→" 버튼 추가. 클릭 시 `https://console.groq.com/keys` 브라우저 열기. `QDesktopServices.openUrl()` 사용.

#### Groq 토큰 사용량 표시

`_groq_tokens_used` 카운터. `_call_groq_raw()`에서 `usage.total_tokens` 누적. 번역 완료 후 `_update_groq_usage_label()`으로 K/M 포맷 갱신.

#### Ollama/Groq 모델 레이스 컨디션 수정

**문제**: Auto 모드에서 Groq 선택 시, 비동기 `_preload_ollama()` 완료 콜백이 Ollama 모델로 콤보박스를 덮어씀.

**해결**: `_on_ollama_models()`에 `if self._auto_provider.currentText() == "Groq": return` 가드 추가.

#### Ollama 버튼 레이아웃 정렬

Row 2의 Ollama 버튼 시작 위치를 Row 1의 Auto 드롭다운 시작 위치에 맞춤. 투명 "Rename" QLabel을 동일 너비 인덴트로 사용하는 기법.

#### Load 세션 시 Provider 재초기화 방지

**문제**: `_load_session()` 호출 시 `_set_provider()` 무조건 실행되어 모델 API 재호출 발생.

**해결**: `saved_provider != current_provider` 비교 후 변경된 경우에만 `_set_provider()` 호출.

### Auto Rename 개선

#### 그룹명 prefix 제외

**문제**: Auto 번역 시 그룹 폴더명에도 `fxt_` prefix가 붙음. 사용자가 수동 추가하지 않는 한 prefix는 이미지에만 적용되어야 함.

**해결**: `_TranslateTask.run()`의 그룹 번역 호출에서 `prefix=""` 전달.

#### Auto Apply 재실행 문제

**문제**: Auto Apply 후 Prefix 변경 → 다시 Apply → 동작 안 함. 상태 라벨이 "Done"인데 코드가 "Ready"만 체크.

**해결**: `_apply_auto_rename()`에서 "Done" 상태도 허용. 2초 후 자동으로 "Ready" 복원.

### 패딩 옵션 리팩토링

#### "Even" → "Pad" 리네이밍

SegmentedButton 라벨 "Even"이 기능과 맞지 않음 (원래 이미지에 패딩 추가하는 것). "Pad"로 변경.

#### Even 체크박스 추가

**요구사항**: 패딩 후 홀수 크기를 짝수로 올리는 동작을 선택적으로 만들기.

**구현**:
- Pad 옵션 행에 `self.even_check = QCheckBox("Even")` 추가 (기본 ON)
- `apply_padding()`에 `force_even=True` 파라미터 추가 — `False`면 `even_ceil()` 호출 안 함
- `collect_layer_metadata()`에도 `force_even` 파라미터 전달
- `ExportWorker.__init__`에 `force_even` 파라미터 추가
- Export 시 `self.even_check.isChecked()` 값을 전달

### Unity UGUI 레이어 순서 수정

**문제**: 포토샵에서 위(front)에 있는 레이어가 Unity UGUI에서 뒤(back)에 렌더링됨. 순서 역전.

**원인 분석**:
- Photoshop: 패널 위 = 앞(front), 아래 = 뒤(back)
- psd-tools: 이터레이션 순서 = PSD 패널 위→아래 (top-to-bottom), order 0 = front
- Unity UGUI: Hierarchy 마지막 sibling = 앞(front), 첫 sibling = 뒤(back)
- 기존 코드: `OrderBy(l => l.order)` (오름차순) → front가 첫 sibling(Unity 뒤)이 됨

**해결**:
- C# 스크립트(`FXC_PSDImporter.cs`): `OrderBy(l => l.order)` → `OrderByDescending(l => l.order)`
- 그룹: `collect_layer_metadata()`에 그룹 `order` 필드 추가. C# 스크립트에서 `OrderBy(depth).ThenByDescending(order)`로 같은 depth 내 역순 생성
- `GroupInfo` 클래스에 `public int order;` 필드 추가

---

## Phase 17: 그룹 rename 경로 리팩토링 + Unity 통합 순서 + UX 개선 (2026-02-26)

### _group_rename_map 경로 기반 리팩토링

**문제**: `_group_rename_map`이 `{원본그룹명: 변경명}` dict로, 동일 이름 그룹이 2개 이상일 때 1개 엔트리만 존재. 한 그룹의 rename을 수동 변경해도 다른 동일명 그룹과 공유되어 독립 편집 불가.

**해결**: `_group_rename_map`을 `{group_path_tuple: 변경명}`으로 리팩토링.

**영향 범위** (~15곳):
- `_build_tree_view()`: `_group_rename_map.get(full_path, ...)` 조회
- `setData()`: `grp_path = self._layers[row].get("_group_path")` 키로 저장
- `_refresh_rename_duplicates()`: `.values()` 순회로 중복 카운팅
- `set_group_rename()` / `get_group_rename()`: path tuple 파라미터
- `get_group_rename_map_by_name()`: Export용 `{name: rename}` 변환 헬퍼 추가
- 세션 저장: `group_rename_v2` (path→join("/")) + v1 하위호환
- Undo 스냅샷/복원: path 기반 조회
- Auto rename: 모든 그룹 경로에 매핑

### 그룹 rename 중복 감지 수정

**문제**: 같은 이름의 그룹 2개가 동일한 rename을 가져도 빨간색 표시 안 됨.

**원인**:
1. `_refresh_rename_duplicates()`가 `_group_rename_map`의 항목 수로 카운팅 → 동일 이름 그룹이 1개 엔트리만 존재하여 항상 count=1
2. Auto rename 완료 후 `_refresh_rename_duplicates()` 미호출

**해결**: 경로 리팩토링으로 자연스럽게 해결 + `_on_translate_done()`에서 호출 추가

### 그룹 접기 하위 그룹 숨김 수정

**문제**: 상위 그룹 접힌 상태에서 하위 그룹 헤더가 여전히 표시됨.

**원인**: `_build_tree_view()`에서 선조 접힘 검사가 그룹 헤더 삽입 루프 **뒤**에 위치 → `common > 0`일 때 하위 헤더가 먼저 삽입됨.

**해결**: 선조 접힘 검사를 그룹 헤더 삽입 루프 **앞**으로 이동.

### 호버 프리뷰 영역 제한

**요구사항**: 레이어명 입력란(rename 필드) 위에서는 호버 프리뷰가 트리거되지 않도록.

**구현**: `mouseMoveEvent`에서 마우스 X 좌표가 `rename_start` 이상이면 `row = -1`로 설정하여 호버 비활성화.

### 프리뷰 패널 백틱(`) 키 지원

**요구사항**: 프리뷰 패널에서도 `` ` `` 키로 레이어 선택 해제.

**구현**:
- `PreviewView`에 `deselect_requested` Signal 추가
- `keyPressEvent`에서 `` Key_QuoteLeft `` 감지 → Signal emit
- `_clear_layer_selection()` 메서드 추가 (clearSelection + setCurrentIndex 리셋 + 빈 preview_requested emit)

**시행착오**: 처음에 `_deselect_all()` (체크박스 해제)에 연결하여 모든 레이어의 체크가 해제되는 버그 발생. `_clear_layer_selection()` (선택 하이라이트만 해제)으로 수정.

### DeprecationWarning 수정

`_RenameLineEdit.mouseDoubleClickEvent`의 `event.pos()` → `event.position().toPoint()` 변경 (PySide6 deprecation).

### Unity UGUI 통합 순서 (Unified Ordering)

**문제**: 그룹과 레이어가 별도의 order 카운터를 사용 (그룹: 0~6, 레이어: 0~19). C# 임포터에서 같은 부모의 자식(그룹+레이어 혼합)을 정렬할 때 두 카운터의 값이 비교 불가능하여 잘못된 순서 생성.

**예시**: `lid_group` 안에서 `lid_ribbon_group`(그룹 order=6)과 `fxt_lid`(레이어 order=9)는 우연히 맞지만, `purple_box_group` 안의 하위 그룹들(order 2,4,5)이 레이어 order 범위와 겹치면서 엉킴.

**해결**:
1. `psd_extractor.py` `collect_layer_metadata()`: `psd.descendants()` 1회 순회로 `_unified_order` 맵 생성. 그룹과 레이어 모두 이 맵에서 order 값 사용
2. C# 임포터 정렬: 오름차순 (`a.ord.CompareTo(b.ord)`) — psd-tools bottom→top 순서에서 낮은 번호=back, 높은 번호=front → Unity sibling 0=back, N=front

### Unity Sprite 자동 설정 개선

**추가 설정**: Setup Sprites에서 TextureType=Sprite 변환 시 추가 설정 자동 적용:
- `SpriteMeshType = FullRect` (UI/FX용, Tight 대신)
- `spriteGenerateFallbackPhysicsShape = false`
- `TextureImporterSettings` API 사용

---

### 핵심 전환점 (Phase 16 추가분)

16. **선택 UX 강화**: 하이라이트 색상, 포커스 모드, Ctrl+Enter 단축키로 작업 흐름 최적화
17. **Groq 고도화**: 동적 모델 목록, 추천 모델 색상, 토큰 추적, 레이스 컨디션 수정으로 클라우드 Provider 안정화
18. **패딩 유연화**: Even 체크박스로 짝수 올림을 선택적으로. force_even 파라미터로 전체 체인 관통
19. **Unity 스크립트 통합**: C# 3개(PSDImporter + PSDLayoutBuilder + Editor) → `FXC_PSDImporter.cs` 1개로 통합. 팀 네이밍 규칙 `FXC_` 접두사 적용
19. **Unity 순서 수정**: PSD front→back ↔ Unity sibling 순서 정확히 매핑. 그룹에도 order 필드 추가

### 핵심 전환점 (Phase 17 추가분)

20. **그룹 rename 경로 리팩토링**: `{name: rename}` → `{path_tuple: rename}`으로 동일 이름 그룹의 독립 편집 지원. 세션 v2 포맷 + v1 하위호환
21. **Unity 통합 순서**: 그룹/레이어 별도 카운터 → `psd.descendants()` 기반 단일 통합 순번. 혼합 자식 정렬 문제 근본 해결
22. **Sprite 자동 설정 강화**: FullRect + PhysicsShape off 자동 적용. UI/FX 워크플로우 최적화

---

## Phase 18: UI 개선 + Pivot 시스템 + C# 고유 클래스명 (2026-02-26)

### Paint 크래시 수정

**문제**: `ch_01.psd` (그룹 없는 PSD) 열 때 `UnboundLocalError: cannot access local variable 'model'` → `paint()` 내에서 무한 재귀 (`paint` → `sizeHint` → `flags` → `paint`).

**원인**: `model = index.model()`이 `if tree_depth > 0` 및 `if is_group` 조건 분기 내부에서만 할당. 플랫 모드(tree_depth=0) 아트 레이어에서 `model` 미정의.

**해결**: 아트 레이어 섹션 시작부에 `model = index.model()` 무조건 할당 추가.

### 눈-썸네일 간격 추가

**문제**: 그룹 없는 PSD에서 눈 아이콘과 썸네일 사이 공백 부족.

**해결**: `_COL_THUMB_X` 56→62, `_COL_NAME_X` 92→98 (6px 간격 추가).

### 버튼 라벨 정리

- **Apply → Rename**: 적용 버튼명을 기능에 맞게 변경. 버튼 폭 56→66px
- **Edit 버튼 색상**: 악센트(#2680EB) → 회색(#3c3c3c, Reset과 동일)
- **Find/Replace 입력란**: 200→180px (10% 축소)
- **Reset All**: Edit 행 필드(Find/Replace/Prefix/Suffix/#)도 포함하여 초기화

### Refresh/? 버튼 이동

**이전**: Settings 패널 하단에 위치.
**변경**: PSD 경로 행의 Browse 오른쪽으로 이동. `|` 구분선으로 분리. 도움말 팝업도 함께 이동.

### Output 패널 2행 구조 리팩토링

**이전**: 1행에 출력 경로 + Browse + Open Folder + 진행률 + EXPORT.
**변경**:
- **Row 1**: 출력 경로 + Browse + Open Folder
- **Row 2**: Unity 체크 + UGUI/NGUI SegmentedButton + `|` 구분선 + Pivot 콤보 + 진행률 + EXPORT

**UGUI/NGUI 선택**: QComboBox → SegmentedButton으로 변경 (2개 중 택1 UI).

### C# 고유 클래스명

**문제**: 여러 PSD를 Export하면 C# 스크립트 클래스명이 동일하여 Unity에서 네임스페이스 충돌.

**해결**: PSD 파일명에서 PascalCase 접미사 생성:
```
ch_01.psd → FXC_PSDImporter_Ch01
gift_box.psd → FXC_PSDImporter_GiftBox
```
- UGUI: `FXC_PSDImporter_{Stem}.cs`
- NGUI: `FXC_PSDImporterNGUI_{Stem}.cs`

### Pivot 시스템 (9방향)

**개발 동기**: Unity에서 Import한 오브젝트의 루트 피봇이 항상 PSD top-left 원점에 위치. 캐릭터 하단 중심, 이미지 중심 등 다양한 피봇 위치가 필요.

**구현:**

1. **UI**: 9방향 Pivot 콤보박스 (Output 패널 Row 2)
   ```
   _PIVOT_MAP = {
     "Top-Left": (0.0, 0.0), "Top-Center": (0.5, 0.0), "Top-Right": (1.0, 0.0),
     "Center-Left": (0.0, 0.5), "Center": (0.5, 0.5), "Center-Right": (1.0, 0.5),
     "Bottom-Left": (0.0, 1.0), "Bottom-Center": (0.5, 1.0), "Bottom-Right": (1.0, 1.0),
   }
   ```

2. **좌표 공식** (pivot 오프셋):
   ```
   unity.x = layer.left + w/2 - canvas_width * pivot_x
   unity.y = -(layer.top + h/2) + canvas_height * pivot_y
   ```

3. **JSON v3**: `"pivot": {"x": px, "y": py}` 필드 추가

4. **C# UGUI**: `PivotInfo` 클래스 추가. anchor 동적: `anchorMin = anchorMax = (px, 1-py)`

5. **C# NGUI**: pivot 오프셋:
   ```
   offX = canvas.width * (pvtX - 0.5)
   offY = canvas.height * (0.5 - pvtY)
   posX = layer.unity.x + offX
   posY = layer.unity.y + offY
   ```

### 피봇 프리뷰 마커

**개발 동기**: Pivot을 설정해도 프리뷰에서 실제 피봇 위치를 확인할 수 없어 직관성이 부족.

**구현:**
- PreviewView에 `_pivot_items` / `_pivot_pos` 상태 변수 추가
- `set_pivot((px, py))` → `_update_pivot_marker()`: 이미지 크기 × 비율로 픽셀 좌표 계산
- 빨간색 십자선 (arm=10px, cosmetic pen) + 중심 원 (반경 4px, 반투명 fill) — `QGraphicsLineItem` + `QGraphicsEllipseItem`
- `_pivot_combo.currentTextChanged` → `_on_pivot_changed()` → `preview_view.set_pivot()` 즉시 갱신
- `set_image()` 양쪽 경로(keep_zoom=True/False)에서 `_update_pivot_marker()` 호출 — 레이어 전환/호버 시 마커 유지
- `clear_preview()` / `show_text()`에서 `_pivot_items.clear()` — 이미지 없을 때 정리
- PSD 로드 시 `_show_merged_preview()` 직후 초기 피봇 설정
- **On/Off 토글 버튼**: 상단 오버레이에 빨간 십자+원 아이콘 토글 버튼 추가 (✛ 버튼 오른쪽, 기본 ON). `_pivot_btn.toggled` → `_on_pivot_btn_toggled()`. OFF 시 `set_pivot(None)`으로 마커 완전 숨김

### 루트 RectTransform pivot + sizeDelta 수정

**문제**: UGUI C# 임포터에서 루트 오브젝트의 RectTransform에 sizeDelta와 pivot을 설정하지 않아 Unity 기본값 `(100, 100)` / `(0.5, 0.5)` 적용. 피봇 위치가 PSD 캔버스와 불일치.

**해결**: `ImportPSD()` 함수에서 루트 RT 설정 추가:
```csharp
rootRT.pivot = new Vector2(pvtX, 1f - pvtY);  // PSD→Unity Y축 반전
rootRT.sizeDelta = new Vector2(canvas.width * scaleFactor, canvas.height * scaleFactor);
```

### 핵심 전환점 (Phase 18 추가분)

23. **Paint 크래시 수정**: 플랫 모드에서 `model` 변수 스코핑 버그 → 무조건 할당으로 해결
24. **UI 패널 재구조화**: Output 패널 2행 + Refresh/? 상단 이동 + 버튼 라벨 정리
25. **C# 고유 클래스명**: PSD별 PascalCase 접미사로 멀티 PSD Export 시 네임스페이스 충돌 방지
26. **Pivot 시스템**: 9방향 사용자 설정 피봇 → JSON v3 + C# 동적 anchor/오프셋. UGUI/NGUI 모두 지원
27. **UGUI/NGUI 통합 UI**: ComboBox → SegmentedButton으로 전환. Output 패널에 통합 배치
28. **피봇 프리뷰 마커**: Pivot 콤보 변경 시 프리뷰에 빨간 십자+원 마커로 피봇 위치 시각화. 토글 버튼으로 On/Off. 이미지 전환/줌 시 유지
29. **루트 RT 피봇 수정**: UGUI C# 임포터에서 루트 RectTransform에 PSD 캔버스 크기 + pivot 동적 설정 추가

---

## Phase 19: POT Export + Multi-Scale + OxiPNG + Nuke Resize Type

### 배경
게임 텍스처 워크플로우에서 POT(Power of Two) 캔버스, 다중 배율, 무손실 PNG 최적화가 필수적. Spine/Unity 2D 제작 파이프라인 강화를 위해 고급 Export 기능 추가.

### Export 파이프라인 구조
```
Extract(RGBA) → Scale → Pad → POT → ColorMode → Save/OxiPNG
```
- Scale 먼저 (패딩/POT는 최종 픽셀 기준)
- POT 마지막 (패딩 적용 후 가장 가까운 2의 거듭제곱으로 확장)

### 백엔드 함수 추가 (psd_extractor.py)
- `next_pot()`: 값 이상의 가장 가까운 2의 거듭제곱 반환 (`1 << (value-1).bit_length()`)
- `apply_pot()`: POT 캔버스 확장 + Nuke Reformat Resize Type 6종
  - **none**: 스케일 없이 중앙 배치 (기본)
  - **fit**: 전체가 보이도록 균일 축소 (min ratio)
  - **fill**: 캔버스를 완전히 채우도록 균일 확대 (max ratio, 잘림)
  - **width/height**: 축 맞춤 균일 스케일
  - **distort**: 비균일 스케일로 정확히 채움 (비율 무시, 게임 텍스처에 중요)
  - 불투명 배경 시 `Image.alpha_composite()`로 완전 플래튼 (반투명 영역도 불투명화)
- `convert_color_mode()`: RGBA/RGB/L 변환
- `save_png_oxipng()`: pyoxipng RawImage 직접 인코딩 (Pillow 대비 15~40% 축소)

### Settings Row 2 UI (2행 구조)
```
Row1: Format [PNG▼] [✓Merge] | Quality | Padding | Color [RGBA▼] | [Reset All] [☐Log]
Row2: [☐POT] [Auto|Manual] [W▼ H▼] BG[T|B|W|C] [Resize▼] | Scale [✓1x][☐.75x][☐.5x] | PNG [Fast|Bal|Best] [☐OxiPNG]
```
- POT 체크 OFF → 관련 위젯 모두 숨김 (기본 상태 = 기존과 동일)
- POT Auto: `next_pot()` 자동 계산 / Manual: 32~4096 수동 선택
- POT BG: Transparent/Black/White/Custom 4종
- Resize Type: Nuke Reformat 기준 6종 (None/Fit/Fill/Width/Height/Distort)

### Export POT 분리 설계
- Settings POT = **프리뷰 설정용** (프리뷰 오버레이에 POT 크기 점선 표시)
- Export 버튼 왼쪽 POT 체크박스 = **실제 내보내기 제어**
- Export POT 체크 시 Settings POT 자동 ON (역방향 연동)
- Settings POT OFF 시 Export POT도 자동 OFF
- 기본 이미지는 항상 메인 폴더에 Pad만 적용하여 저장
- POT 이미지는 `POT/` 서브폴더에 별도 생성 (Merged 포함)

### POT 프리뷰 오버레이
- 프리뷰 이미지 위에 POT 크기 점선 사각형 (`QGraphicsRectItem`, cosmetic pen, #64B4FF)
- 크기 정보 텍스트 표시 (예: "512 x 256 px")
- 레이어 선택/전환/설정 변경 시 자동 갱신
- 상단 오버레이에 POT 토글 버튼 (Settings POT 연동)

### POT 배경색 불투명 플래튼
- 초기 구현: `canvas.paste(img, (ox, oy), img)` — 반투명 영역이 완전히 불투명화되지 않는 문제
- 최종 해결: `canvas.alpha_composite(img, (ox, oy))` — 표준 알파 합성으로 완전 플래튼
- 조건: `bg_color[3] == 255`일 때만 적용, 투명 배경은 기존 `paste()` 유지

### 다중 배율 Export
- 1x (기본, 항상), 0.75x, 0.5x 체크박스
- 다중 배율 시 서브폴더 구조: `1_00x/`, `0_75x/`, `0_50x/`
- Unity JSON도 배율별 생성 (좌표 스케일 적용)
- C# 임포터는 1x 폴더에만 1회 생성

### LLM 번역 안정성 강화
- Groq qwen3-32b 모델이 thinking 블록을 반환하는 문제 발견
- 수정: 시스템 프롬프트에 `/no_think` 추가
- 코드 블록(``` ``` ```) 제거: `re.sub(r"```[a-z]*\n?", "", content)`
- 추론 텍스트(`_is_reasoning_text`) 감지 시 `continue`로 완전 스킵 (빈 문자열 대신)
- `_strip_think_tags`에 `<|think|>` 변형 태그 지원 추가
- `_on_translate_done`에 진단 로그 (성공/스킵 카운트)

### PSD 정보 바 HTML 리치 텍스트
- `info_label`을 plain text에서 HTML로 전환
- 텍스트: `#e0e0e0`, 구분선(`|`): `#555555`
- Hidden 레이어 개수: `#e0a050`, Rename 중복 개수: `#e05050`
- `LayerListModel.duplicates_changed` 시그널 → `_update_info_label()` 자동 갱신

### Rename Edit Find/Replace 개선
- `QLineEdit` → `_RenameLineEdit`로 변경 (Alt+더블클릭 `_` 기준 단어 선택)
- 빈 필드 더블클릭 시 `"fxt_"` 자동 입력 (Prefix 필드와 동일 동작)
- eventFilter에서 텍스트가 있을 때 `return False`로 이벤트 통과 (Alt+더블클릭 미동작 버그 수정)

### 핵심 전환점 (Phase 19)

30. **POT Export**: Settings POT(프리뷰) + Export POT(내보내기) 이중 구조. 기본 이미지와 POT 이미지 분리 저장
31. **Nuke Reformat Resize Type**: distort(비균일 스케일)가 게임 텍스처에서 가장 중요. 6종 모두 구현
32. **alpha_composite 플래튼**: POT 불투명 배경에서 반투명 영역까지 완전히 불투명화
33. **다중 배율**: 배율별 서브폴더 + Unity JSON 배율 좌표 + C# 1x 전용
34. **OxiPNG**: Pillow 우회 RawImage 직접 인코딩으로 15~40% 파일 크기 절감
35. **LLM /no_think**: Qwen3 thinking 블록 문제 근본 해결
36. **정보 바 HTML**: 중복/숨김 개수를 색상별로 실시간 표시

---

---

## Phase 20: 레이어별 POT 토글 + nearest POT + UI 개선 (2026-02-27)

### 레이어별 POT 토글

**개발 동기**: POT Export가 전체 체크된 레이어에 일괄 적용되어, 특정 레이어만 POT로 내보내려면 체크를 해제→Export→다시 체크하는 번거로움. 체크박스/눈 아이콘과 동일한 패턴으로 개별 레이어에 POT on/off를 토글할 수 있어야 함.

**구현:**
- `PotRole = Qt.ItemDataRole.UserRole + 9` — 레이어별 POT 상태 Role
- `_art_pot` / `_pot` 병렬 배열 (소스/뷰, 체크박스/가시성과 동일 패턴)
- `_initial_pot` — PSD 로드 시점 스냅샷 (Restore용, 기본 `[False]*N`)
- delegate `paint()`에서 POT 아이콘 렌더링 (파란 사각형 `#2680EB` on, 회색 `#505050` off)
- `_pot_column_visible` delegate 플래그: Settings POT ON일 때만 아이콘 열 표시
- Thumbnail/Name X 좌표를 POT 열 유무에 따라 동적 분기 (`_COL_POT_X`, `_COL_THUMB_X_POT`, `_COL_NAME_X_POT`)
- `mousePressEvent`에서 POT 영역 히트 테스트 → 클릭 토글
- **P 키**: 선택된 레이어 일괄 POT 토글 (Space/E와 동일 패턴)

**시행착오:**
1. `_eff_thumb_g` UnboundLocalError: 변수가 `if tree_depth > 0:` 블록 내에서만 정의되어 최상위 그룹(depth=0)에서 미정의. `if is_group:` 블록 시작부에 무조건 할당으로 해결
2. `self.layer_delegate` AttributeError: delegate를 로컬 변수로 저장하고 인스턴스 속성으로 저장하지 않음. `self.layer_delegate = LayerDelegate(...)` 로 수정
3. `self.layer_list` AttributeError: `self.layer_view`가 정확한 속성명. 2곳 수정

### POT All/None 버튼

**개발 동기**: Settings POT ON 시 전체 레이어가 POT ON 상태에서 시작하므로, 전체 OFF 후 필요한 레이어만 선택적으로 ON하는 워크플로우 지원.

**구현:**
- All/None을 일반 QPushButton으로 추가 (SegmentedButton 아닌 1회성 동작)
- `_set_all_pot(enabled)`: `model._art_pot` 전체 설정 + 뷰 배열 동기화
- SegmentedButton과 동일한 스타일 (높이/색상/border-radius)
- `:pressed` pseudo-class로 클릭 피드백 (`#2680EB`)
- None 오른쪽에 `|` 세로 구분선

### nearest_pot() 함수 — Nearest POT 계산

**개발 동기**: 기존 `next_pot()`은 항상 올림 (71→128). 하지만 71px는 64에 가깝고 128에 멀어서, 리소스 낭비. "가장 가까운 POT" 옵션 필요.

**구현 (`psd_extractor.py`):**
```python
def nearest_pot(value):
    if value <= 1:
        return 1
    ceil = 1 << (value - 1).bit_length()
    floor = ceil >> 1
    return floor if (value - floor) <= (ceil - value) else ceil
```

**UI:**
- `_pot_calc_seg = SegmentedButton(["Ceil", "Nearest"])` — Auto 모드에서만 표시
- `apply_pot()`에 `pot_calc` 파라미터 추가, `_pot_fn = nearest_pot if pot_calc == "nearest" else next_pot`
- ExportWorker에 `pot_calc` 전달
- 세션 저장/복원에 `pot_calc` 포함

### POT BG 색상 사각형 버튼

**변경**: `SegmentedButton(["T","B","W","C"])` → 프리뷰 BG와 동일한 16x16 색상 사각형 버튼 스타일.

**구현:**
- `_pot_bg_buttons` dict: T(체커보드)/B(#000)/W(#fff) 각각 `QPushButton(fixedSize=22x22)`
- `_pot_bg_custom_btn`: C(커스텀) 버튼 + QColorDialog
- `_pot_bg_value` 변수로 현재 선택 추적 (기존 `.value()` 대체)
- 선택 버튼에 `border: 2px solid #2680EB` 강조

### Settings 패널 3행 레이아웃

**변경**: POT 설정을 2행으로 분리 + Format행과 POT행 사이에 가로 구분선 추가.

**레이아웃:**
```
Row1: Format | Merge | Quality | Padding | Color | Reset All | Log
────────────────────── (1px #3c3c3c 구분선) ──────────────────────
Row2: POT | All | None | Auto/Manual | W/H | BG T B W C
Row3: Resize Type [combo] | Scale 1x/.75x/.5x | Ceil/Nearest | PNG Fast/Bal/Best | OxiPNG
```

- POT 위젯 항상 표시 (POT OFF 시에도 숨기지 않음, W/H 콤보만 조건 표시)
- BG/Resize Type 라벨을 Scale 라벨과 동일 스타일로 통일

### Rename 열 너비 드래그

**개발 동기**: 레이어명이 길거나 짧을 때 rename 입력란의 적절한 너비가 달라짐. 사용자가 경계를 드래그하여 조절 가능하게.

**구현:**
- `_rename_col_w` delegate 인스턴스 변수 (기본값 `_COL_RENAME_W`)
- `_is_on_rename_edge(pos)`: 마우스 X가 rename 영역 왼쪽 경계 ±3px 이내 판단
- `mousePressEvent`: 경계 위 → `_rename_dragging = True`, `_rename_drag_start_x/w` 저장
- `mouseMoveEvent`: 드래그 중 너비 실시간 갱신 + `SplitHCursor` 커서
- `mouseReleaseEvent`: 드래그 종료
- 세션 저장/복원에 `rename_col_w` 포함

### OxiPNG 기본 ON

pyoxipng 설치 시 OxiPNG 체크박스를 기본 ON으로 설정. 미설치 시 비활성화 유지.

### Undo/Redo 5-tuple 확장

**변경**: 스냅샷 구조를 4-tuple → 5-tuple로 확장하여 POT 상태 포함.

```python
# 기존: (art_rename, group_map, art_checked, art_visible)
# 변경: (art_rename, group_map, art_checked, art_visible, art_pot)
```

하위호환: `len(snapshot) == 5` 검사로 기존 4-tuple 스냅샷과 호환.

### 핵심 전환점 (Phase 20)

37. **레이어별 POT 토글**: 전체 일괄 POT → 개별 레이어 선택적 POT. 체크/눈과 동일 패턴 (배열+아이콘+클릭+키보드)
38. **nearest_pot()**: 올림 전용 → Ceil/Nearest 선택. 리소스 낭비 방지 (71→64 vs 71→128)
39. **POT BG 색상 사각형**: SegmentedButton 텍스트 → 프리뷰 BG와 동일한 시각적 색상 버튼
40. **Settings 3행 레이아웃**: 1행 압축 → 3행 분리로 가독성 향상. 구분선 추가
41. **Rename 열 너비 드래그**: 고정 너비 → 사용자 조절 가능. 세션 저장
42. **Undo 5-tuple**: POT 상태도 Undo/Redo 대상에 포함

---

## Phase 21: NGUI 워크플로우 완성 + UX 개선

### 배경
Phase 18에서 NGUI 기본 지원(피봇 오프셋, C# 고유 클래스명)을 추가했으나, 실제 Unity 테스트를 거치며 Atlas 생성, 하이어라키 구조, 좌표 정밀도 등 실무 워크플로우에 필요한 기능들이 부족함을 확인. 유니티 실제 환경에서 반복 테스트하며 NGUI 파이프라인을 완성.

### NGUI C# Editor 기능 추가

**Setup Textures 버튼**
- 이미지 폴더 내 모든 텍스처를 자동 설정: Sprite/Readable/Uncompressed/FullRect/npotScale=None
- Atlas 생성 전 필수 단계 (텍스처가 Readable이어야 PackTextures 가능)

**Make Atlas 버튼**
- NGUI UITexturePacker 기반 자동 Atlas 생성
- 생성물: NGUIAtlas ScriptableObject + Material (Unlit/Transparent Colored) + packed PNG
- 설정: padding=2, RGBA32, maxTextureSize=4096 (프로덕션 NGUI Atlas 설정과 일치)
- 처음에 Unity `PackTextures` 사용 → compressed format으로 `EncodeToPNG` 실패 → `UITexturePacker.PackTextures`로 전환
- RenderTexture Y-flip 문제 → `GetPixels32()` 직접 복사로 해결
- Material 텍스처 null 참조 문제 → delete-and-recreate 패턴으로 해결
- Atlas 생성 후 스크립트 컴포넌트의 atlasObject에 자동 반영

**Import to Scene 개선**
- **PSD명 루트 오브젝트**: 스크립트 오브젝트 → PSD 파일명 루트 → fxRoot_anim → 콘텐츠 (3단 구조)
- **fxRoot_anim**: 애니메이션 타겟 컨테이너. 루트 바로 아래에 빈 GameObject로 삽입, 모든 그룹/레이어가 이 하위에 배치
- **fxt_ → s_ prefix 변환**: 하이어라키에서 텍스처 네이밍(fxt_)을 스프라이트 네이밍(s_)으로 자동 변환
- **정수 좌표**: `Mathf.RoundToInt()`로 Position 반올림 (NGUI 픽셀 퍼펙트 + 애니메이션 편의)
- **PSD order 기반 depth 정렬**: `OrderBy(l => l.order)`로 back→front 정확한 depth 할당
- **UIPanel 경고**: Import 후 UIPanel 미존재 시 경고 메시지 표시

### Export 개선
- **NGUI 이미지 서브폴더**: PSD 파일명과 동일한 서브폴더에 이미지 저장 (기존 hardcoded "Images/" → 동적)
- **JSON layer.file 경로**: 서브폴더명 포함 (예: `260225_giftBox_v1/layer.png`)
- Atlas Updater 호환: 이미지 폴더 우클릭 → Open Atlas Updater → Sync으로 아틀라스 업데이트 가능

### Output 패널 UX 개선
- **폴더 존재 인디케이터**: Browse 왼쪽 QCheckBox(disabled)로 출력 폴더 존재 여부 실시간 표시
- **QFileSystemWatcher**: 부모 디렉토리 감시하여 외부 생성/삭제 즉시 반영 (폴더 지워도 체크 즉시 해제)
- **Open Folder 폴백**: 출력 폴더가 없을 때 PSD 파일이 있는 폴더 열기

### Phase 21 후속 개선
- **UGUI/NGUI 색상 구분**: 세그먼트 버튼 활성 텍스트 색상 분리 — UGUI: 스카이 블루(#4FC1E9), NGUI: 소프트 그린(#8CC152). 비활성 상태(#808080)는 공통
- **삭제 확인 다크 스킨**: Output 폴더 Delete 버튼의 QMessageBox를 다크 테마로 (#2b2b2b 배경, #e0e0e0 텍스트, #2680EB 기본 버튼 테두리)
- **fxRoot_anim 정수 좌표**: NGUI pivot offset(offX/offY)을 `float` → `int` (`Mathf.RoundToInt`)로 변경. 캔버스 홀수 크기에서 소수점 Position 방지
- **Orig dup 정보 개선**: rename이 완료된(unresolved=0) 원본 중복은 info bar에 미표시
- **Open Folder 동작 변경**: 항상 PSD 파일이 있는 위치의 폴더만 열기 (출력 폴더 무관)

### 발생한 이슈 및 해결
| 이슈 | 원인 | 해결 |
|------|------|------|
| fxRoot_anim 소수점 Position | `float offX/offY` 계산 (홀수 캔버스) | `Mathf.RoundToInt()`로 정수화 |
| 삭제 팝업 라이트 테마 | `QMessageBox.question()` 정적 메서드 | 인스턴스 생성 + `setStyleSheet()` |
| UGUI/NGUI 구분 어려움 | 동일한 흰색 텍스트(#e0e0e0) | 개별 활성 텍스트 색상 분리 |
| Orig dup 표시 잔존 | rename 완료 후에도 카운트 표시 | unresolved(미rename) 기준으로 필터링 |
| INGUIAtlas cast error | `t.atlasObject`가 Object 타입 | 이미 검증된 `atlas` 변수 사용 |
| EncodeToPNG 실패 | PackTextures가 compressed format 반환 | UITexturePacker + ARGB32 |
| Atlas 이미지 Y-flip | RenderTexture → ReadPixels 플랫폼 차이 | GetPixels32() 직접 복사 |
| Material _MainTex null | CreateAsset 후 텍스처 참조 유실 | delete → new Material(tex) → CreateAsset |
| 보라색 아틀라스 배경 | textureType=Default + auto compression | Advanced + RGBA32 platform override |
| 하이어라키 순서 역전 | fxRoot_anim이 root 바로 아래 생성 | PSD명 루트 → fxRoot_anim → 콘텐츠 3단 |
| 소수점 Position | float 좌표 그대로 사용 | Mathf.RoundToInt() 적용 |

### Key Turning Points (Phase 21)
43. **NGUI Atlas 자동 생성**: 수동 Atlas Maker → 버튼 1클릭 자동 생성 (Setup Textures → Make Atlas)
44. **fxRoot_anim 구조**: 플랫 하이어라키 → 애니메이션 컨테이너 삽입으로 Spine/Unity 애니메이션 워크플로우 지원
45. **fxt_ → s_ 네이밍**: 텍스처/스프라이트 네이밍 컨벤션 자동 적용
46. **Output 폴더 실시간 감시**: 텍스트 변경 시만 → QFileSystemWatcher로 외부 변경도 감지
47. **UGUI/NGUI 시각 구분**: 세그먼트 버튼에 모드별 고유 색상 부여로 직관성 향상
48. **다크 스킨 통일**: 삭제 확인 팝업까지 다크 테마 적용, 앱 전체 일관된 UX

---

## Phase 22: 코드 리뷰 & Unity Export 폴더 자동 접미사 + Auto Version

### 코드 리뷰 (60+ 항목 분석, 19개 수정)

대규모 코드 리뷰를 수행하여 Critical~Low 우선순위로 분류 후 체계적 수정.

#### Critical (1건)
- **`_start_export()` 가시성 필터 버그**: 체크 ON이지만 가시성 OFF인 레이어도 export되던 문제 → `if not visible: continue` 가드 추가

#### High (6건)
- **`_start_export()` 레이어 이름 취득 잘못된 인덱스**: `_art_layers[art_idx]` 대신 `_layers[i]` 사용하던 버그 수정
- **UGUI C# 임포터 pivotInfo null 참조**: PSD 파일 경로에서 pivot 정보를 읽지 못할 때 발생하는 NullReferenceException 방어 코드 추가
- **Backend `pot_calc` 파라미터 누락**: `collect_layer_metadata()` 호출에 `pot_calc=self.pot_calc` 추가
- **Backend Grayscale 변환 버그**: 비RGBA 이미지의 "L" 모드 변환 경로 추가 (`if img.mode == "RGBA"` → `else img.convert("L")`)
- **NGUI Editor C# JSON 역직렬화 오류**: `layout.canvas` 접근 시 JsonConvert 파싱 실패 방어
- **`_reset_all()` 불완전한 상태 초기화**: Undo/Redo 스택, 번역 캐시(Lock), Groq 토큰(Lock), 머지/호버 이미지 초기화 추가

#### Medium (7건)
- **`show_text()` zoom_changed 미발신**: 텍스트 프리뷰 후 줌 시그널 emit 추가
- **그룹 rename 충돌 경고 누락**: `get_group_rename_map_by_name()`에 collision logging 추가
- **호버 QImage 반복 변환**: `layer_info["_cached_qimg"]`로 pil_to_qimage 결과 캐싱
- **QFontMetrics 반복 생성**: Delegate `__init__`에서 `_fm_rename`, `_font_fx`, `_fm_fx` 사전 생성, paint()에서 재사용
- **`flags()` 불필요 조건 분기**: 동일 반환값의 if/else → 단일 return으로 단순화
- **Signal disconnect RuntimeWarning**: PySide6의 `disconnect()` 경고를 `warnings.catch_warnings()` + `simplefilter("ignore", RuntimeWarning)` + `except (RuntimeError, SystemError)`로 안전 처리 (6곳)
- **Dead code 제거**: `if False and ...` 블록(~23줄) 삭제 + 들여쓰기 수정

#### Low (5건)
- `_reset_all()` 추가 상태 초기화 (위 참조)
- Dead code 제거 (위 참조)
- `flags()` 단순화 (위 참조)
- QFontMetrics 캐싱 (위 참조)
- `import warnings` 추가

### Unity Export 폴더 자동 접미사

Unity UGUI/NGUI 모드로 내보낼 때 출력 폴더명에 `_UGUI` 또는 `_NGUI` 접미사를 자동 삽입.

**경로 변환 규칙:**
```
260225_giftBox_v1  + UGUI → 260225_giftBox_UGUI_v1
260225_giftBox_v1  + NGUI → 260225_giftBox_NGUI_v1
260225_giftBox     + UGUI → 260225_giftBox_UGUI
Unity OFF                 → 변경 없음
```

**구현 핵심:**
- `_compute_export_dir(base_dir, unity_mode, auto_version)` 메서드 추가
- regex로 기존 `_UGUI/_NGUI` 접미사 제거 (중복 방지) → `_v\d+` 버전 분리 → 접미사 삽입 → 버전 복원
- 7개 테스트 케이스 통과 확인

### Auto Version 체크박스

출력 폴더가 이미 존재할 때 버전을 자동 증가하여 새 폴더 생성.

- Export 행에 **Auto Ver** 체크박스 추가 (POT 왼쪽)
- `os.path.exists()` 확인 후 `_v2`, `_v3` 등 순차 증가 (최대 100번 탐색)
- QSettings 전역 저장 (`auto_version`)
- 버전 없는 폴더명도 지원: `260225_giftBox_UGUI` → `260225_giftBox_UGUI_v2`

### Output 경로 실시간 프리뷰

Unity ON/OFF, UGUI/NGUI 전환 시 `output_entry`가 즉시 반영되어 사용자가 최종 경로 확인 가능.

- `_output_base_dir`: 원본 경로 보존 (Unity 접미사 미적용 상태)
- `_updating_output_display`: textChanged 무한 루프 방지 플래그
- `unity_check.toggled` / `_unity_type_seg.valueChanged` → `_update_output_display()` 연결
- PSD 로드/Browse/Reset All 시 `_output_base_dir` 설정 → `_update_output_display()` 호출

### Signal Disconnect RuntimeWarning 수정

PySide6의 `Signal.disconnect()`가 연결되지 않은 슬롯에 대해 `RuntimeWarning`을 발생시키는 문제.

| 시도 | 결과 |
|------|------|
| `try/except RuntimeError` | RuntimeWarning 미포착 |
| `simplefilter("error", RuntimeWarning)` | C++ 내부에서 SystemError 발생 |
| `simplefilter("ignore", RuntimeWarning)` | 경고 무시 + `except (RuntimeError, SystemError)` 안전망 ✓ |

6개 disconnect 위치에 동일한 `with warnings.catch_warnings()` 패턴 적용.

### 발생한 이슈 및 해결
| 이슈 | 원인 | 해결 |
|------|------|------|
| 가시성 OFF 레이어 Export | visible 필터 누락 | `if not visible: continue` |
| pot_calc 미전달 | collect_layer_metadata 호출 시 누락 | 파라미터 명시 추가 |
| Grayscale 변환 실패 | 비RGBA→L 경로 없음 | else 분기 추가 |
| RuntimeWarning → SystemError 크래시 | simplefilter("error") + C++ 내부 | simplefilter("ignore") |
| output_entry 무한 루프 | textChanged → 갱신 → textChanged | `_updating_output_display` 플래그 |

### Key Turning Points (Phase 22)
49. **코드 리뷰 체계화**: 60+ 항목 분석 → Critical/High/Medium/Low 4단계 우선순위 분류 → 19개 수정
50. **Export 경로 자동 변환**: regex 기반 폴더명 파싱으로 UGUI/NGUI 접미사 + 버전 관리 자동화
51. **Output 경로 실시간 동기화**: Unity 모드 변경이 즉시 경로에 반영되는 라이브 프리뷰
52. **PySide6 경고 안전 처리**: C++ 내부 RuntimeWarning에 대한 방어적 프로그래밍 패턴 확립

---

## Phase 23: UX 개선 — 세션 자동화, UI 정리, 슬롯 단순화

### 목표
- 세션 자동 저장/복원으로 수동 Save/Load 제거
- 누락된 16개 설정 항목을 세션에 추가
- UI 버튼 배치 최적화 및 슬롯 단축키 단순화

### 주요 변경 사항

#### 1. 세션 자동 저장/복원
- **Save/Load 버튼 제거**: 자동 저장(PSD 전환/앱 종료)으로 대체
- **PSD 로드 시 자동 복원**: `_load_session()` 자동 호출. 기존: 로그 알림 → 수동 Load 클릭
- **초기 스냅샷 순서**: `set_layers()` → 초기 스냅샷 → `_load_session()`. Restore는 세션 적용 전 상태로 복원
- **settings_v2 확장** (16개 항목 추가):
  - Settings Row 1: format, merge, quality, padding(5항목), log
  - Export: unity, unity_type, pivot, auto_ver, output_base_dir
  - 프리뷰: hover_opacity, hover_tint, hover_tint_color, preview_bg
- **프리뷰 BG 복원**: 프리셋 6종(T/#000/#fff/#f00/#0f0/#00f) 매칭 → 해당 버튼 체크 + `set_bg_color()`. 매칭 실패 시 커스텀 색상
- **closeEvent QSettings 정리**: auto_version을 QSettings에서 제거 (세션으로 이관)

#### 2. UI 배치 변경
- **Restore 버튼 이동**: slot_search_row → Settings Row 1의 Reset All 왼쪽. 아이콘(24x24) → 텍스트 "Restore"(70px)
- **Open Folder 이동**: Output Row 1 → Export 행의 PSD Export 오른쪽 (`|` 구분선)
- **Browse → Output Browse**: 텍스트 변경, 너비 80→110px
- **Output 폴더 인디케이터**: QCheckBox → QLabel("●") 8px dot. 초록(#4ec94e, 존재) / 회색(#666666, 미존재)
- **Delete 버튼**: 숨김/표시 → 항상 표시 + 활성/비활성. 너비 80→60px. 구분선 제거

#### 3. Layer 토글 버튼
- **위치**: Group 버튼 오른쪽, `|` 구분선으로 Order와 분리
- **동작**: 아트 레이어 표시/숨김 토글. 트리 모드에서는 그룹 헤더만 남음
- **모델**: `_show_art_layers` 플래그 + `set_show_art_layers()`. `_rebuild_view()`/`_build_tree_view()`에서 필터링
- **세션 저장**: `show_art_layers` 항목 추가

#### 4. Auto Ver 경로 표시 개선
- **버전 없는 PSD + Auto Ver ON**: `_v1` 자동 추가 (예: `ch_01` → `ch_01_v1`)
- **`_update_output_display()`**: `auto_version=False` 고정 → `_auto_ver_check.isChecked()` 반영
- **Auto Ver 시그널 연결**: `toggled` → `_update_output_display()`. 체크 변경 시 경로 즉시 갱신

#### 5. 선택 슬롯 단축키 변경
- **기존**: Click=로드, Shift+Click=저장, Ctrl+Click=삭제
- **변경**: 빈 슬롯 Click=저장, 채워진 슬롯 Click=로드, Ctrl+Click=삭제
- **장점**: Shift 불필요, 슬롯 상태에 따라 자동 판단

#### 6. POT Nearest 프리뷰 수정
- **문제**: Nearest 모드에서 POT < 이미지 크기일 때 사각형 미표시
- **원인**: `pot_w <= img_w and pot_h <= img_h: return` 가드
- **수정**: `pot_w == img_w and pot_h == img_h` (동일할 때만 스킵)
- **색상 구분**: POT > 이미지 = 파란 점선, POT < 이미지 = 빨간 점선

### 발생한 이슈 및 해결
| 이슈 | 원인 | 해결 |
|------|------|------|
| Tint 설정 복원 후 프리뷰 미반영 | `_rebuild_hover_bg()` 미호출 | 세션 로드 최종 rebuild 섹션에 추가 |
| POT Nearest 사각형 미표시 | `<=` 비교로 작은 POT 차단 | `==` 동일 비교로 변경 |
| Auto Ver OFF→ON 시 경로 미갱신 | 시그널 미연결 | `toggled` → `_update_output_display` 연결 |

### Key Turning Points (Phase 23)
53. **세션 완전 자동화**: 수동 Save/Load 제거 → PSD 로드 시 모든 설정 자동 복원. 사용자 동선 1단계 제거
54. **설정 무손실 보존**: 16개 누락 항목 추가로 PSD 재오픈 시 100% 동일 작업 환경 복원
55. **슬롯 UX 단순화**: 3단계(Click/Shift/Ctrl) → 2단계(Click/Ctrl) + 상태 기반 자동 판단

---

## Phase 24: 프로젝트 프리셋 + Auto Export + NGUI Import All + 그룹 BBox 피봇 (2026-02-28)

### 배경
실무에서 여러 프로젝트(포커 PC/모바일, 바둑 PC/모바일)를 오가며 작업할 때 Export 경로와 Unity 타입(UGUI/NGUI)을 매번 수동 전환하는 비효율 해결. 또한 NGUI 임포터의 3단계(Setup Textures → Make Atlas → Import to Scene)를 1클릭으로 통합.

### 프로젝트 프리셋 시스템

**구현:**
- `_project_combo` (QComboBox, 150px) + `✎` 매니저 버튼
- QSettings → "projects" JSON + "last_project" 영속화
- 4개 기본 프로젝트: 포커 PC/모바일(NGUI), 바둑 PC/모바일(UGUI)
- 프로젝트 선택 시 Unity 타입 자동 전환 + Export 경로 자동 결정
- Project Manager 다이얼로그: UGUI/NGUI 드롭다운 색상 구분 (UGUI=#4FC1E9, NGUI=#8CC152)
- 세션 저장에 `project_name` 포함

### Auto Export

PSD 파일 변경 감지 시 자동으로 Export 실행.

- `_auto_export_check` (QCheckBox) — Export 패널에 배치
- `_do_refresh()` 완료 후 500ms 딜레이 → `_auto_export_trigger()` 호출
- 세션에 `auto_export` 상태 저장/복원
- 조건 검증: PSD 로드 완료 + 출력 경로 설정 + Export 진행 중 아닐 때만 실행

### NGUI Import All 버튼

Setup Textures + Make Atlas + Import to Scene 3단계를 1클릭 순차 실행.
- 보라색 버튼으로 시각 구분
- 각 단계 완료 후 다음 단계 자동 진행
- Undo 지원

### UGUI/NGUI 그룹 BBox 피봇

**개발 동기:** 기존에는 그룹이 빈 GameObject로 위치 (0,0,0)에 생성되어, 회전/스케일 시 콘텐츠가 예상치 못한 중심점 기준으로 변환됨.

**해결:**
- Phase 1: 모든 레이어 rect를 순회하여 직속/상위 그룹에 bbox 누적 (Vector4: minX, minY, maxX, maxY)
- Phase 2: 그룹 생성 — bbox 있으면 실제 크기/위치 설정. 하위 그룹은 부모 중심 기준 상대좌표
- Phase 3: 레이어 생성 — bbox 그룹 내 레이어는 anchor(0.5,0.5)로 그룹 중심 기준 상대좌표
- UGUI: RectTransform sizeDelta + anchoredPosition
- NGUI: localPosition (부모 중심 기준 상대좌표)

### Snap to Pixel

위치/크기를 정수로 반올림하는 `snapToPixel` bool + `Sn` 헬퍼 함수. 기본 ON. Inspector에서 토글 가능.

**시행착오:** C# `System.Func<float, float>` 지역 변수 `Sn`이 사용 지점보다 아래에 선언되어 CS0841 에러. 선언 위치를 위로 이동하여 해결.

### Key Turning Points (Phase 24)

56. **프로젝트 프리셋**: 수동 경로/타입 전환 → 콤보 1클릭으로 프로젝트 컨텍스트 전환
57. **Auto Export**: PSD 저장 → 자동 Export → Unity 즉시 반영. 수동 EXPORT 클릭 제거
58. **NGUI Import All**: 3단계 수동 → 1클릭 자동. 반복 작업 대폭 감소
59. **그룹 BBox 피봇**: 빈 오브젝트 (0,0,0) → 콘텐츠 바운딩박스 기반 중심점. 애니메이션/트랜스폼 정확도 향상

---

## Phase 25: FXC_MeshQuad + POT Info JSON (2026-03-01)

### 배경
Shine FX 워크플로우에서 POT(Distort) 텍스처를 Unity Quad에 적용할 때:
1. 원본 이미지 크기를 매번 수동으로 기록/입력해야 함
2. `Transform.localScale`로 Quad 크기를 제어하면 Scale ≠ (1,1,1) — 애니메이션/파티클 간섭

**목표:** PSD Exporter에서 이미지 + 크기 정보 JSON + Unity C# 스크립트를 자동 생성하고, Unity에서 1클릭으로 Quad 오브젝트를 일괄 생성. Quad는 메쉬 버텍스 기반으로 실제 픽셀 크기를 정의하여 `localScale = (1,1,1)` 유지.

### _pot_info.json 자동 생성

ExportWorker에서 POT export 시 원본/POT 크기 정보 수집 및 JSON 출력.

**구현:**
- `pot_info_entries = []` — 레이어 루프에서 POT 처리 시마다 append
- `pre_pot_w, pre_pot_h = img.size` — Pad 후 POT 전 크기 캡처 (= Unity Quad 메쉬 크기)
- 레이어 루프 종료 후 `POT/_pot_info.json` 작성
- 로그: `[pot] _pot_info.json (N layers)`

### C# 템플릿 상수 — Runtime (`_FXC_MESHQUAD_CS`)

**`FXC_MeshQuad`** — 루트 컴포넌트:
- `[ExecuteAlways]`, `[AddComponentMenu("FXC/Mesh Quad")]`
- `TextAsset potInfoJson` — JSON 참조
- `int baseDepth, depthStep` — NGUI depth 제어
- `Vector2 pivot` — 메쉬 피봇 좌표

**`FXC_MeshQuadChild`** — 자식 Quad 컴포넌트:
- `[ExecuteAlways]`, `[RequireComponent(MeshFilter, MeshRenderer)]`
- `Vector3 meshSize` — X=Width, Y=Height, Z=Depth (Inspector에서 Transform Scale 스타일 표시)
- `[HideInInspector][SerializeField] Mesh _mesh` — 씬에 직렬화 → 도메인 리로드 시 유지
- `Rebuild()` — 4-vertex quad, 피봇 오프셋 적용, `localScale = Vector3.one` 강제
- `OnEnable()` — MeshFilter HideFlags 설정 + `_mesh == null`일 때만 Rebuild
- `LateUpdate()` — `_dirty` 플래그 기반 조건부 Rebuild
- OnDestroy 없음 — Unity가 직렬화된 메쉬 수명 관리

### C# 템플릿 상수 — Editor (`_FXC_MESHQUAD_EDITOR_CS`)

**`FXC_PlayModeSaver`** — Play 모드 에셋 자동 저장:
- `[InitializeOnLoad]` static class
- `EditorApplication.playModeStateChanged` 구독
- `PlayModeStateChange.ExitingEditMode` 시 `AssetDatabase.SaveAssets()` 호출
- Setup으로 생성된 .mat 에셋을 Inspector에서 수정 후 저장 없이 Play해도 텍스처 유실 방지

**`FXC_MeshQuadEditor`** — Custom Inspector + Setup:
- JSON auto-discovery: `MonoScript.FromMonoBehaviour()` → 스크립트 경로 기준 `POT/_pot_info.json` 자동 할당
- Setup: JSON 파싱 → fxRoot_Anim 생성 → 각 layer에 Child 오브젝트 생성
- MeshRenderer 경량 2D 설정 (Setup 시 1회만): Shadow/Probes/MotionVector/Occlusion Off
- Material .mat 에셋 → `POT/Materials/mat_{name}.mat` (재Setup 시 기존 .mat 재사용)
- `SetupTextureImport()`: POT 텍스처 → Default, sRGB, NPOT=None, Mipmap=OFF, Clamp, Bilinear, Uncompressed
- Shader fallback: `FX Team/fxs_shine` → `Unlit/Texture` → `Standard`
- UICustomRendererWidget depth 자동 할당 (baseDepth + depthStep × N)
- Hierarchy 표시: 자식 오브젝트 목록 + Size + Depth 정보

**`FXC_MeshQuadChildEditor`** — Mesh Size만 표시:
- `EditorGUILayout.PropertyField(meshSize)` — Vector3 필드 (X Y Z)
- Material은 MeshRenderer가 Inspector에서 직접 노출 (Animation 키프레임 지원)

### 공유 메쉬 vs 인스턴스 메쉬 설계 결정

**시도 1: 공유 `.asset` (fxg_quad.asset)**
- 1x1 unit quad 에셋을 공유하고 `localScale = (width, height, 1)`로 크기 제어
- 문제: Scale ≠ (1,1,1) → 애니메이션/파티클 시스템 간섭

**시도 2: 인스턴스 메모리 메쉬 (최종 채택)**
- 각 Child가 `Rebuild()`로 실제 픽셀 크기의 4-vertex quad 생성
- `localScale = Vector3.one` 유지
- 메모리: Quad 4 vertices ≈ 100 bytes, 100개 = ~10KB — 무시 가능

### Play 모드 머티리얼 텍스처 유실 해결 과정

**증상**: Setup → 텍스처 할당 → Play → 텍스처 사라짐. 재할당 후 Play → 유지됨.

**진단 과정:**
1. `_mesh`가 비직렬화 → OnEnable → Rebuild → `mf.sharedMesh` 교체 → 도메인 리로드 중 MeshRenderer 직렬화 간섭
   - 해결: `[SerializeField] Mesh _mesh`, OnEnable에서 `_mesh == null`일 때만 Rebuild
2. OnEnable에서 MeshRenderer 프로퍼티(shadowCastingMode 등) 수정 → 직렬화 간섭
   - 해결: MeshRenderer 설정을 Setup 시 1회만 적용, OnEnable에서 제거
3. Setup의 `AssetDatabase.SaveAssets()`가 .mat 초기 상태만 디스크에 저장 → Inspector 수정은 인메모리 → Play 시 디스크 버전 리로드
   - 해결: `FXC_PlayModeSaver` — Play 진입 직전 SaveAssets() 자동 호출

**핵심 교훈:**
- `[ExecuteAlways]` + OnEnable에서 컴포넌트 프로퍼티 수정은 도메인 리로드 시 다른 컴포넌트의 직렬화를 방해할 수 있음
- Unity Inspector에서 수정한 에셋 프로퍼티는 `SaveAssets()`/`Ctrl+S` 전까지 인메모리 상태
- MeshRenderer에 `HideFlags.HideInInspector` 설정 시 Animation 창에서 머티리얼 키프레임 생성 불가

### PSD Exporter C# 파일 출력

- POT export ON + scale 1x일 때, 파일 미존재 시에만 생성
- `FXC_MeshQuad.cs` → `scale_dir` (메인 폴더)
- `FXC_MeshQuadEditor.cs` → `scale_dir/Editor/`
- PSD별 고유 클래스명: `.replace("FXC_MeshQuad", unique_cls)` 패턴
- `FXC_PlayModeSaver`는 "FXC_MeshQuad" 미포함 → uniquify 안 됨 (전역 동작이므로 무해)

### 발생한 이슈 및 해결
| 이슈 | 원인 | 해결 |
|------|------|------|
| "Can't add component MeshRenderer" | `[RequireComponent]` 자동 추가 + 명시적 AddComponent 중복 | AddComponent<Child> 먼저 → GetComponent<MeshRenderer> |
| Transform Scale ≠ (1,1,1) | 공유 mesh + localScale 방식 | 인스턴스 메쉬 + 버텍스 기반 크기 |
| Material Inspector 이중 표시 | ObjectField + MaterialEditor.DrawHeader() 동시 | 커스텀 에디터에서 Material 섹션 제거, MeshRenderer 직접 노출 |
| Animation 키프레임 불가 | MeshRenderer HideFlags.HideInInspector | MeshRenderer hideFlags 제거 |
| Play 모드 텍스처 유실 (1차) | 비직렬화 _mesh → OnEnable Rebuild | [SerializeField] Mesh _mesh |
| Play 모드 텍스처 유실 (2차) | OnEnable MeshRenderer 프로퍼티 수정 | Setup 시 1회만 설정 |
| Play 모드 텍스처 유실 (3차) | Inspector 수정 = 인메모리, Play = 디스크 리로드 | FXC_PlayModeSaver (SaveAssets on ExitingEditMode) |

### Key Turning Points (Phase 25)

60. **POT Info JSON**: 원본/POT 크기 수동 기록 → `_pot_info.json` 자동 생성. Unity에서 1클릭 Quad 일괄 생성
61. **메쉬 버텍스 기반 Quad**: localScale 방식 → 인스턴스 메쉬 버텍스 기반. Scale (1,1,1) 유지하며 정확한 픽셀 크기
62. **[SerializeField] Mesh**: 도메인 리로드 시 OnEnable 컴포넌트 수정 방지 → 머티리얼 직렬화 보호
63. **PlayModeSaver**: Inspector 인메모리 수정 → Play 전 자동 SaveAssets. Unity 에셋 직렬화 라이프사이클 이해 심화
64. **C# 템플릿 자동 출력**: PSD Export → Unity C# 스크립트 자동 생성 + PSD별 고유 클래스명

---

## Phase 26: Output 경로 개선 + Unity 임포터 통일 (2026-03-01)

### 배경
Phase 25까지의 기능이 안정화되면서 워크플로우 품질 개선에 집중. 5가지 독립적 개선 사항.

### 1. Unity OFF → PSD 경로 출력 전환

**문제:** Unity ON에서 프로젝트 경로가 설정된 후 Unity OFF로 전환해도 출력 경로가 프로젝트 경로에 머물러 있음. PSD 파일 위치에 이미지가 생성되어야 하는 일반 Export에서도 프로젝트 경로로 내보내짐.

**분석:** `_output_base_dir`이 프로젝트 경로로 덮어쓰여진 후 Unity OFF 시 원래 PSD 경로로 복원되지 않음. 6개의 코드 경로(`_on_psd_loaded`, `_load_session`, `_on_project_changed`, `_apply_project_path`, `output_entry.textChanged`, `_on_unity_type_changed`)가 `_output_base_dir`을 수정하지만, Unity OFF 시 원본 경로로 돌아가는 로직이 없었음.

**해결:**
- `_psd_default_dir` 변수 추가 — PSD 로드 시 기본 출력 경로 보존
- `_on_unity_toggled()` 메서드 추가 — Unity ON→`_apply_project_path()`, OFF→`_psd_default_dir` 복원
- `unity_check.toggled` 연결 대상을 `_update_output_display`에서 `_on_unity_toggled`으로 변경
- `_load_session()`에서 Unity ON 시만 `_apply_project_path()` 호출 (조건부)
- `_on_project_changed()`에서도 Unity ON 시만 프로젝트 경로 적용

### 2. Output 패널 행 순서 변경

**변경 전:** Row 0=Project preset, Row 1=Output path, Row 2=Export controls
**변경 후:** Row 0=Output path, Row 1=Project preset, Row 2=Export controls

**이유:** 사용자가 가장 먼저 확인하는 것은 출력 대상(어디에 내보낼지)이므로 Destination→Configuration→Action 순서가 직관적.

### 3. UGUI fxt_ → s_ prefix 변환

**문제:** NGUI 임포터에서는 `fxt_`로 시작하는 레이어명을 하이어라키에서 `s_`로 변환하는데, UGUI 임포터에는 이 변환이 없었음. 두 모드 간 동작 불일치.

**해결:** UGUI C# 템플릿에 동일한 `displayName` 변환 로직 추가:
```csharp
string displayName = layer.name;
if (displayName.StartsWith("fxt_"))
    displayName = "s_" + displayName.Substring(4);
GameObject go = new GameObject(displayName);
```

### 4. Project Manager unity_type 데이터 격리

**문제:** 작업 중 프로젝트의 UGUI/NGUI 설정이 의도치 않게 변경됨. Output 패널의 UGUI/NGUI 세그먼트를 변경하면 프로젝트 데이터가 오염됨.

**원인 분석:**
1. `_on_unity_type_changed()`가 매번 `_projects[idx]["unity_type"] = val` + `_save_projects()` 호출 — UI 세그먼트의 임시 변경이 영구적으로 프로젝트에 기록
2. `_load_session()`에서 `_unity_type_seg.setValue()` 호출 시 `blockSignals` 없이 실행 → `_on_unity_type_changed` 트리거 → 프로젝트 데이터 변경

**해결:**
- `_on_unity_type_changed()`에서 프로젝트 데이터 write-back 완전 제거 — `_update_output_display()`만 호출
- `_load_session()`에서 `_unity_type_seg.setValue()` 앞뒤로 `blockSignals(True/False)` 추가
- **설계 원칙:** 프로젝트의 unity_type은 Project Manager 다이얼로그에서만 변경 가능

### 5. POT/Preview BG 투명 버튼 아웃라인 수정

**문제:** POT BG의 투명(체커보드) 버튼 선택 시 파란색 아웃라인이 보이지 않음. B/W 버튼은 정상.

**원인:** 16x16 버튼에 16x16 아이콘 + `padding: 0` → 아이콘이 2px border 영역까지 완전히 덮어서 checked 상태의 border가 보이지 않음.

**해결:** 체커보드 아이콘 크기를 16x16 → 12x12로 축소. Preview BG와 POT BG 두 곳 모두 적용.

### Key Turning Points (Phase 26)

65. **Output 경로 Unity 연동**: 수동 경로 전환 → Unity ON/OFF에 따라 자동 전환. `_psd_default_dir`로 원본 경로 보존
66. **UGUI/NGUI 동작 통일**: UGUI에도 `fxt_→s_` 변환 적용하여 두 모드 간 일관성 확보
67. **프로젝트 데이터 격리**: UI 임시 상태와 프로젝트 영구 데이터를 분리. 의도치 않은 설정 변경 원천 차단

---

## Phase 27 — FXC_QuadMesh 공용 스크립트 분리 (2026-03-01)

Phase 25에서 PSD별 중복 생성되던 FXC_MeshQuadChild + FXC_MeshQuadChildEditor + FXC_PlayModeSaver를 공용 스크립트로 분리.

### 1. 공용 스크립트 분리

**동기:** 여러 PSD를 Export할 때 동일한 Child/Editor/PlayModeSaver 코드가 매번 생성됨. 이미 존재하는 파일은 스킵하지만, 프로젝트 내 중복 코드 관리가 비효율적.

**변경:**
- `FXC_QuadMesh.cs` → `Script/FX/` — 공용 Runtime 컴포넌트 (meshSize + Rebuild, pivot center 하드코딩)
- `FXC_QuadMeshEditor.cs` → `Script/FX/Editor/` — 공용 Custom Inspector (meshSize 표시)
- `FXC_PlayModeSaver.cs` → `Script/FX/Editor/` — 공용 Play 모드 에셋 저장

### 2. 템플릿 경량화

- `_FXC_MESHQUAD_CS`에서 Child 클래스 제거 (Root MonoBehaviour만 남김)
- `_FXC_MESHQUAD_EDITOR_CS`에서 PlayModeSaver + ChildEditor 제거 (Root Editor만)
- pivot 필드 제거 (center 하드코딩)

### 3. `.replace()` 안전성 확인

`FXC_QuadMesh`는 `FXC_MeshQuad`의 부분문자열이 아님 → `.replace("FXC_MeshQuad", unique)` 호출 시 공용 스크립트 클래스명이 치환되지 않아 안전.

### Key Turning Points (Phase 27)

68. **PSD별 중복 코드 제거**: Child/Editor/PlayModeSaver를 공용 스크립트로 분리하여 프로젝트당 1벌만 유지
69. **템플릿 경량화**: 생성되는 C# 파일이 Root 클래스만 포함 → 파일 크기 축소 + 관리 용이

---

## Phase 28 — UIShaderWidget 독립화 + Material 네이밍 (2026-03-01~02)

Phase 27의 FXC_QuadMesh를 UIWidget 직접 상속 방식으로 전면 리팩토링. UICustomRendererWidget 의존을 완전히 제거하고, Material 네이밍 개선.

### 1. UIShaderWidget — UIWidget 직접 상속

**동기:** 기존 UIShaderWidget이 `UICustomRendererWidget` (`External/UIParticleWidget/`)에 의존. 다른 Unity 프로젝트에 복사 시 외부 패키지까지 함께 복사해야 하는 불편.

**상속 구조 변경:**
```
Before: UIWidget → UICustomRendererWidget → UIShaderWidget
After:  UIWidget → UIShaderWidget  (독립)
```

**UICustomRendererWidget에서 복사한 핵심 기능 (~40줄):**
- `m_Renderer` / `m_UseSharedMaterial` — Renderer 참조 + 공유 Material 설정
- `material` property override — Renderer의 Material 반환
- `Awake()` — `boundless=true`, `fillGeometry=false`, `mWidth=mHeight=2`
- `OnDrawCallCreated()` — `dc.SetExternalRenderer(m_Renderer)`
- `Invalidate()` override — Panel 영역 무관 가시성 (이펙트 용도)

**복사하지 않은 기능 (~150줄):** SoftClip/TextureClip 클리핑 전체 (셰이더 FX에 불필요)

### 2. Inspector 표준화

```
Before: UIShaderWidgetEditor : UICustomRendererWidgetInspector (NGUI 스타일)
After:  UIShaderWidgetEditor : Editor (표준 Unity UI)
```

`UICustomRendererWidgetInspector`의 `[CustomEditor(typeof(UICustomRendererWidget), true)]`가 서브클래스에도 적용되어 NGUI 스타일(어두운 배경, NGUIEditorTools)이 강제됨. UIWidget 직접 상속으로 간섭 자동 해제.

### 3. HierarchyExtend — Depth 번호 표시

`EditorApplication.hierarchyWindowItemOnGUI`로 UIShaderWidget depth 번호를 연한 초록색으로 표시. VHierarchy 아이콘 영역(30px) 오프셋으로 겹침 방지.

### 4. SendMessage 에러 수정

`MeshFilter.sharedMesh` setter → 내부 `SendMessage("OnMeshFilterChanged")` → OnValidate 중 호출 시 에러. `if (mf.sharedMesh != _mesh)` 동일 참조 체크로 해결.

### 5. Material 네이밍 수정

**변경:** `mat_` prefix 제거:
```
Before: POT/Materials/mat_fxt_jackpot_title.mat
After:  POT/Materials/fxt_jackpot_title.mat
```

`psd_extractor_gui_qt.py` 템플릿 내 3곳에서 `"mat_" +` 삭제:
- `matPath` — 파일 경로
- `mat.name` × 2곳 — Material 에셋 이름 (생성 경로 + 폴백)

### 6. PSD Exporter 템플릿 업데이트

Setup()에서 `go.AddComponent<UIShaderWidget>()` 1회만 호출, `sw.depth = currentDepth` 직접 설정. FXC_MeshQuadChild → UIShaderWidget으로 교체.

### 8. fxt_ → fxs_ 하이어라키 이름 변환

FXC_MeshQuad Setup 시 자식 오브젝트 이름에 `fxt_` → `fxs_` 변환 추가. 셰이더 FX 전용 prefix로 UGUI/NGUI의 `fxt_` → `s_` 변환과 유사하되, MeshQuad 쪽은 `fxs_`(FX Shader)로 구분.

```
Before: fxt_shine → fxt_shine (하이어라키명 = 레이어명 그대로)
After:  fxt_shine → fxs_shine (하이어라키에서 shader prefix로 변환)
```

`psd_extractor_gui_qt.py` 템플릿의 Setup() 내 `new GameObject(layer.name)` → `displayName` 변수로 변환 후 `new GameObject(displayName)` 패턴 적용.

### 7. 배포용 스크립트 백업

다른 프로젝트 복사용으로 `C:\Users\NHN\Desktop\NGUIShaderWidget\`에 4파일 보관:
- `UIShaderWidget.cs` — Runtime (Quad Mesh + NGUI Depth)
- `Editor/UIShaderWidgetEditor.cs` — Inspector (표준 Unity UI)
- `Editor/HierarchyExtend.cs` — Hierarchy depth 번호 표시
- `Editor/FXC_PlayModeSaver.cs` — Play 전 SaveAssets

### 9. R Shine 기본 텍스처 자동 할당

Setup 시 `_RShineTex` 슬롯에 `fxt_grad_50.png` 기본 텍스처 자동 할당. fxs_shine 셰이더의 R 채널 그라디언트 텍스처로, 매번 수동 할당하는 반복 작업 제거.

```
경로: Assets/PlatformAsset/Classic/DirectLinkResource/VFX/Images/Textures/Common/Gradient/fxt_grad_50.png
셰이더 프로퍼티: _RShineTex ("R Shine Texture (R)")
```

**조건부 할당**: `mat.GetTexture("_RShineTex")` == null 또는 name == "white" 일 때만. 이미 다른 텍스처가 수동 할당된 경우 덮어쓰지 않음 (재Setup 안전).

### Key Turning Points (Phase 28)

70. **UICustomRendererWidget 의존 제거**: 외부 패키지 없이 NGUI UIWidget만으로 동작하는 독립 컴포넌트
71. **Inspector 표준화**: NGUI 스타일 간섭 해제 → 표준 Unity Editor UI
72. **Hierarchy depth 표시**: 작업 중 렌더링 순서를 한눈에 파악 가능
73. **SendMessage 안전성**: 동일 참조 체크로 OnValidate 중 MeshFilter 에러 방지
74. **Material 네이밍 직관화**: `mat_` prefix 제거하여 레이어 파일명과 일치
75. **fxt_→fxs_ 하이어라키 변환**: MeshQuad 셰이더 FX 전용 prefix로 UGUI/NGUI(`s_`)와 구분
76. **R Shine 기본 텍스처 자동화**: `fxt_grad_50.png` 자동 할당으로 Setup 후 즉시 셰이더 프리뷰 가능

---

## Phase 29 — AI Agent 인터페이스 + 워크플로우 토론 (2026-03-02)

인간 GUI 워크플로우와 AI 구조화 데이터 워크플로우의 근본적 차이를 분석하고, 실제 작동하는 AI 전용 인터페이스 프로토타입을 구현.

### 1. Human vs AI 워크플로우 토론

**동기:** PSD Exporter가 인간을 위한 GUI 도구로 성숙해지면서, "같은 백엔드 기능을 AI가 사용한다면 인터페이스가 어떻게 달라야 하는가?"라는 질문이 대두.

**핵심 비교:**
| 관점 | 인간 (GUI) | AI (구조화 데이터) |
|------|-----------|-------------------|
| 입력 | 마우스 클릭, 체크박스, 드래그 | JSON/dataclass, 선언적 설정 |
| 처리 | 시각적 확인 → 수동 조정 반복 | 규칙 기반 일괄 처리 |
| 검증 | 눈으로 보고 판단 | 프로그래밍 체크 (파일 존재, 크기 이상, 이름 충돌) |
| 피드백 | 프리뷰 이미지, 진행률 바 | 구조화된 결과 dict/JSON |

토론 문서: `docs/human_vs_ai_workflow.md` (날짜 기반 히스토리 형식으로 계속 확장 가능)

### 2. psd_ai_interface.py — AI Agent 인터페이스 프로토타입

**설계 원칙:** 기존 `psd_extractor.py` 백엔드 함수를 그대로 import하여 래핑 — 새 백엔드 코드 0줄.

**핵심 클래스:**
```
ExportTask (dataclass)     ← 입력: 30개 필드, 모두 선언적
  ↓
PSDAgent.run(task)         ← 실행: 백엔드 함수 호출 + 파일 저장
  ↓
ExportResult (dataclass)   ← 출력: 파일 목록 + 검증 결과
```

- `ExportTask`: psd_path, layers, rename_map, format, padding, pot, color_mode, unity 등 30개 필드
- `PSDAgent`: `run()` 메서드 하나로 전체 export 파이프라인 실행
- `ExportResult`: exported_files, skipped, duration_sec, validation(검증 결과)
- `PSDInfo`: inspect_psd()로 PSD 분석 결과 반환

**5개 프리셋:**
- `spine_character` — Spine 리깅용 (RGBA, even padding, 0.5x 포함)
- `unity_ngui_fx` — NGUI FX용 (POT distort, single scale)
- `unity_ugui` — UGUI용 (패딩 + merge)
- `web_assets` — 웹용 (JPEG, RGB, no padding)
- `quick_check` — 빠른 확인 (모든 레이어, 기본값)

**CLI 인터페이스:**
```bash
python psd_ai_interface.py inspect sample.psd          # PSD 분석
python psd_ai_interface.py run sample.psd --preset spine  # 프리셋 실행
python psd_ai_interface.py presets                       # 프리셋 목록
python psd_ai_interface.py run sample.psd --dry-run     # 설정만 확인
```

**테스트 결과:** ch.psd (22레이어) 기준 1.82초, 전체 검증 통과.

### 3. 아키텍처 인사이트

```
psd_extractor.py (백엔드 함수)
  ├── psd_extractor_gui_qt.py (인간 GUI — PySide6)
  ├── psd_extractor.py __main__ (인간 CLI — argparse)
  └── psd_ai_interface.py (AI Agent — dataclass/JSON)
```

하나의 백엔드에 3개의 인터페이스가 공존하는 구조. 각 인터페이스는 같은 핵심 함수(`collect_layers`, `extract_layer_image`, `apply_padding`, `apply_pot` 등)를 사용하되, 입출력 형태만 다름.

**Windows cp949 이슈:** CLI 출력에서 이모지(📁🖼👁) + em-dash(—) 인코딩 에러 발생 → ASCII 문자로 대체하여 해결.

### Key Turning Points (Phase 29)

77. **AI 인터페이스 구현**: 기존 백엔드 코드 변경 없이 dataclass + JSON 래핑만으로 AI 전용 인터페이스 완성
78. **3-인터페이스 아키텍처**: 동일 백엔드 위에 GUI/CLI/AI API 3개 프론트엔드 공존 확인
79. **구조화된 검증**: AI는 시각 검증 대신 프로그래밍 체크 (빈 파일, 이름 충돌, 크기 이상)으로 품질 보장
80. **워크플로우 토론 문서화**: 인간 vs AI 인터페이스 비교를 날짜 기반 히스토리로 기록하여 지속 발전 가능한 토론 프레임워크 구축

---

## 개발 환경

- Windows 11, Python 3.13+
- Unity 2022.3.67f2 (UGUI 임포트 시)
- Photoshop v27.4 (COM 기반 도구 사용 시만)
- Ollama (로컬 LLM 서버, Auto KR→EN Rename 시 사용)
- Groq (클라우드 LLM API, Auto KR→EN Rename 대체/보조)
- 주요 의존성: PySide6, psd-tools 1.12.1, Pillow 12.1.1, pyoxipng >= 9.1.0
