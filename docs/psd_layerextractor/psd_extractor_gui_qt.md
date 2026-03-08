# psd_extractor_gui_qt.py - PySide6 GUI 사용 가이드

PySide6 기반 고성능 PSD 레이어 추출 GUI. Photoshop 스타일 다크 테마.

## 의존성

```
pip install PySide6 psd-tools Pillow
```

## 실행

```bash
python psd_extractor_gui_qt.py
```

---

## 화면 구성

```
+------------------------------------------------------------------+
| PSD Layer Extractor (Qt)                               [_][O][X]  |
+------------------------------------------------------------------+
| [PSD 경로 QComboBox(히스토리)] [Browse] │ [Refresh] [?]            |
| 정보: ch.psd | 210x283 px | 23 layers (22 art, 1 groups)          |
+------------------------------------------------------------------+
| Rename [mode▼] [옵션 인라인] ... [Rename] [Clear]                 |
| +-- QSplitter(H) -----------------------------------------------+|
| | QListView (가상화)          |                                  ||
| | [01][✓][eye][pot][thumb] name | QGraphicsView 프리뷰            ||
| | [02][✓][eye][pot][thumb] name |  ┌── 100%|✛|◎|▢|POT|Info|Fit ┐||
| | [03][ ][eye][pot][thumb] name |  │                          │  ||
| |  (dim name if eye off)      |  │    [Tab: PSD 정보]       │    ||
| |  ▼ Group Header (접기 가능) |  │                          │    ||
| |  │ [01] layer (들여쓰기)    |  │     layer info text      │    ||
| |                             |  └── Tint|BG|Dim ───────────┘    ||
| |                             | [Order][Visible][Deselect]       ||
| |                             | [Group][Restore]                 ||
| |                             | [1][2][3][4][5] [🔍 검색]       ||
| +----------------------------+----------------------------------+|
+------------------------------------------------------------------+
| Row1: Format [PNG▼] [✓Merge] | Quality | Padding | Color [RGBA▼] | [Reset All] [☐Log] |
| ──────────────────────────── (구분선) ────────────────────────────── |
| Row2: [☐POT] [All][None] [Auto|Manual] [W▼ H▼] | BG [T][B][W][C] |
| Row3: Resize Type [None▼] | Scale [✓1x][☐.75x][☐.5x] | [Ceil|Nearest] | PNG [Fast|Bal|Best] [☐OxiPNG] |
+------------------------------------------------------------------+
| [출력 경로] [●] [Delete] [Output Browse]                          |
| Project [프로젝트▼][✎] │ [프로젝트 경로]                         |
| [☐ Unity] [UGUI|NGUI] │ Pivot [Bottom-Center▼]  진행률 [☐Auto Export] [☐Auto Ver] [☐POT] [EXPORT] [PSD Export] | [Open Folder] |
| [QPlainTextEdit 로그] (기본 숨김, Log 체크 시 표시)               |
+------------------------------------------------------------------+
```

---

## 1. PSD 파일 열기

### 방법 1: Browse 버튼
1. **Browse** 버튼 클릭
2. PSD 파일 선택 → 자동 로드

### 방법 2: 경로 직접 입력
1. 경로란에 PSD 파일 경로 입력 후 **Enter**

### 방법 3: 히스토리에서 선택
- 경로란 드롭다운에서 이전에 열었던 파일 선택

### 방법 4: 더블클릭
- **경로란 더블클릭**: 마지막 열었던 파일 자동 로드
- **레이어 빈 영역 더블클릭**: 파일 열기 다이얼로그

로드 완료 시 정보 표시: `파일명 | 크기 | 레이어 수 (art, groups)`

### PSD 실시간 감시
PSD 파일 로드 후 Photoshop에서 수정하고 저장하면:
- 앱이 파일 변경을 자동 감지 (QFileSystemWatcher)
- 300ms 딜레이 후 자동으로 reload
- Export 중에는 자동 reload 비활성화
- 자동 감지가 안 될 경우 Settings의 **Refresh** 버튼으로 수동 reload

---

## 2. 레이어 선택

### 체크박스
각 레이어의 체크박스를 클릭하여 내보낼 레이어를 선택합니다.

### 도구 버튼 (프리뷰 하단)

상단 행:

| 버튼 | 기능 |
|------|------|
| **Group** | 플랫/트리 뷰 토글. 트리 모드에서 그룹 폴더 헤더 + 들여쓰기로 계층 표시. 그룹 헤더 클릭 시 접기/펼치기 |
| **Layer** | 아트 레이어 표시/숨김 토글. 트리 모드에서 그룹 헤더만 남김 |
| **Order** | 레이어 순서 반전 (Photoshop ↔ 역순) |
| **Visible** | Visible(●) 레이어만 체크 |
| **Deselect** | 모든 레이어 선택(하이라이트) 해제 |
| **Restore** | PSD 로드 시점의 체크/가시성/rename 상태로 복원 |

하단 행:

| 요소 | 기능 |
|------|------|
| **1~5 슬롯** | 레이어 선택(하이라이트) 조합 저장/불러오기 (아래 상세 설명) |
| **검색창** | 레이어 이름 검색 필터 (X 버튼으로 초기화) |

### 선택 슬롯 (1~5)
자주 사용하는 레이어 선택 조합을 5개 슬롯에 저장하고 불러올 수 있습니다.

| 조작 | 기능 |
|------|------|
| **빈 슬롯 클릭** | 현재 하이라이트된 레이어를 슬롯에 저장 |
| **채워진 슬롯 클릭** | 저장된 선택 불러오기 (하이라이트 복원) |
| **Ctrl+클릭** | 슬롯 내용 삭제 |

- 저장된 슬롯은 텍스트 색상으로 구분 (활성: 밝은색, 비어있음: 어두운색)
- 마우스 호버 시 툴팁에 저장된 레이어 이름 목록 표시
- 레이어 이름 기준 저장 (정렬/트리 전환에 영향 없음)
- QSettings로 앱 재시작 후에도 유지

### 레이어 검색
프리뷰 상단의 검색창에 텍스트를 입력하면 레이어 이름으로 필터링됩니다.
- 입력 즉시 실시간 필터 적용
- 검색창 오른쪽 X 버튼으로 검색어 초기화
- 플랫 모드, 트리 모드 모두 동작
- 트리 모드에서는 매칭되는 레이어가 속한 그룹 헤더도 함께 표시

### 키보드/마우스
| 조작 | 기능 |
|------|------|
| **클릭** | 레이어 선택 (프리뷰 표시) |
| **Ctrl+클릭** | 다중 선택 추가 |
| **Shift+클릭** | 범위 선택 |
| **Ctrl+A** | 전체 레이어 선택 (하이라이트) |
| **Space** | 선택된 레이어 체크 토글 (다중 시 일괄 처리) |
| **E** | 선택된 레이어 가시성(눈) 토글 (다중 시 일괄 처리) |
| **P** | 선택된 레이어 POT 토글 (다중 시 일괄, Settings POT ON 시) |
| **A** | 레이어 선택 해제 (하이라이트만 해제, 체크 유지) |
| **체크박스 클릭** | 개별 체크 토글 |

선택된 레이어는 No 번호가 악센트 색상(#2680EB)으로 표시되어 시각적으로 구분됩니다.

---

## 3. 프리뷰

레이어를 클릭하면 오른쪽 프리뷰 영역에 이미지가 표시됩니다.

| 조작 | 기능 |
|------|------|
| **마우스 휠** | 줌 인/아웃 (10% ~ 1600%) |
| **더블클릭** | 100% 리셋 |
| **드래그** | 패닝 (이미지 이동) |
| **Fit 버튼** | 프리뷰 영역에 맞춤 |
| **✛ Crosshair 버튼** | 이미지 중심 십자선 표시/숨김 |
| **◎ Pivot 마커 버튼** | 피봇 위치를 빨간 십자+원 마커로 표시/숨김 (기본 ON). Pivot 콤보 변경 시 즉시 갱신. 레이어 전환/줌 시 유지 |
| **▢ Outline 버튼** | 이미지 경계선 표시/숨김 (기본 ON) |
| **Info 버튼** | 이미지 하단 레이어 정보(이름/사이즈) 표시/숨김 (기본 ON) |
| **Tab** | PSD 파일 정보 오버레이 토글 (파일명, 크기, 레이어 수) |

### 프리뷰 오버레이
- **상단 오른쪽**: 줌% | ✛(십자선) | ◎(피봇) | ▢(아웃라인) | Info | Fit
- **하단 가운데**: Tint | BG | Dim (배경색, 투명도 조절)
- **이미지 하단 가운데**: 선택된 레이어명 + 사이즈 정보 (drawForeground 기반, 줌 무관)

### 배경색
6종 프리셋 (투명/흰/검/빨/초/파) + 커스텀 컬러 피커. 투명 배경은 체커보드 표시.

### Dim 프리뷰
호버 시 비활성 레이어의 투명도(0~100%) 슬라이더 + Tint 단색 모드 (색상 선택 가능). Dim 라벨 더블클릭 시 기본값 30% 복원.

### 다중 선택 프리뷰
Ctrl+Click / Shift+Click으로 여러 레이어 선택 시 PSD 좌표 기준으로 합성하여 프리뷰 표시 (레이어 뎁스 순서 유지).

---

## 4. 레이어 이름 변경 (Rename)

레이어 리스트 상단의 Rename 도구를 사용합니다.

### 모드

| 모드 | 설명 | 옵션 |
|------|------|------|
| **Manual** | 각 레이어의 rename 필드를 직접 편집 | 없음 |
| **Sequential** | 접두사 + 순번으로 자동 생성 | Prefix, Start 번호, Direction (↓/↑) |
| **Body Part** | 한글 레이어명을 영문 바디파트로 자동 매핑 | Prefix, Spine/Live2D 프리셋 |
| **Auto (KR→EN)** | Ollama(로컬)/Groq(클라우드) LLM으로 한글→영문 자동 번역 | Preset, Prefix, Provider(Ollama/Groq), Model |

### 사용법
1. **모드 선택** (드롭다운)
2. 옵션 설정 (Prefix, Start 번호 등)
3. **Rename** 클릭 → rename 필드 자동 채움
4. **Clear** 클릭 → rename 필드 초기화

### 선택 기반 Rename
레이어를 하이라이트(선택)한 상태에서 Apply를 누르면 **선택된 레이어만** rename이 적용됩니다.
- 하이라이트된 레이어가 있을 때 → 해당 레이어만 대상
- 하이라이트된 레이어가 없을 때 → 전체 아트 레이어 대상 (기존 동작)
- Sequential 모드: 대상 레이어 수 기준으로 01부터 순차 번호 부여
- Body Part 모드: 대상 레이어만 한글→영문 매핑 수행
- Auto (KR→EN) 모드: 대상 레이어만 번역 적용

Body Part 모드는 한글 레이어 이름(예: `오른손`, `왼쪽다리`)을 자동으로 영문 변환합니다.

### Auto (KR→EN) 모드
Ollama 로컬 LLM(qwen2.5:3b)을 사용하여 한글 레이어 이름을 영문 snake_case로 자동 번역합니다.

**사전 준비:**
1. [Ollama](https://ollama.ai) 설치
2. 터미널에서 `ollama pull qwen2.5:3b` 실행 (모델 다운로드)
3. Ollama 서버 실행 상태 확인 (기본 `localhost:11434`)

**번역 우선순위:** 내장 딕셔너리 → 세션 캐시 → Ollama API (배치 호출)

**그룹 컨텍스트:** 레이어가 속한 PSD 그룹명을 함께 전달하여 동음이의어를 구분합니다.
- 예: `팔` 그룹의 `위` → `arm_upper`, `다리` 그룹의 `위` → `leg_upper`

**상태 표시:** Ollama 연결 상태가 Ready(초록) / Error(빨강) / Translating...(노랑) / Done(초록)으로 표시됩니다.

### Rename 열 너비 조절
레이어명과 rename 입력란의 경계를 마우스로 드래그하여 rename 열 너비를 조절할 수 있습니다. 커서가 경계에 닿으면 좌우 리사이즈 커서로 변경됩니다. 변경된 너비는 세션에 저장됩니다.

### Rename 중복 감지
rename 필드에 동일한 이름이 2개 이상 존재하면 해당 이름이 **빨간색(#e05050)**으로 표시됩니다. 이름이 변경되면 실시간으로 중복 상태가 갱신됩니다.

---

## 5. Settings (설정)

### Format
- **PNG**: 투명 배경 지원 (기본값, 권장)
- **JPEG**: 불투명 배경, Quality 슬라이더 활성화 (1~100)

### Merge
- **ON**: 전체 레이어 합성 이미지 `_merged.png/jpg` 함께 내보내기
- **OFF**: 개별 레이어만 내보내기

### Unity (Output 패널)
- **ON**: Unity 메타데이터 `_unity_layout.json` + C# 임포터 스크립트 함께 내보내기
- **OFF**: 이미지만 내보내기
- **UGUI/NGUI**: SegmentedButton으로 UI 타입 선택
  - UGUI: `FXC_PSDImporter_{Stem}.cs` (Canvas + Image + RectTransform)
  - NGUI: `FXC_PSDImporterNGUI_{Stem}.cs` (UISprite + Atlas + depth)
- **C# 고유 클래스명**: PSD 파일명에서 PascalCase 접미사 생성 (멀티 PSD Export 시 충돌 방지)
- **Pivot**: 9방향 피봇 선택 (Top-Left ~ Bottom-Right, 기본 Bottom-Center). 프리뷰에 빨간 십자+원 마커로 피봇 위치 실시간 표시 (◎ 버튼으로 On/Off 토글). 루트 RectTransform에 PSD 캔버스 크기 + pivot 동적 설정
- 레이어 순서가 PSD→Unity 간 정확히 매핑됨 (통합 순서 — 그룹+레이어 단일 카운터로 정확한 sibling 정렬)
- Setup Sprites 시 MeshType=FullRect + GeneratePhysicsShape=off 자동 적용

### Padding
| 모드 | 설명 |
|------|------|
| **None** | 패딩 없음 (원본 크기) |
| **Pad** | 각 축 +N px. Even 체크 ON(기본) 시 홀수→짝수 올림, OFF 시 홀수 유지. 기본값: +2px |
| **Fixed** | Width/Height 별도 고정 패딩 지정 |

### Color Mode
RGBA / RGB / Gray 선택. JPEG 포맷 시 RGBA 비활성화.

### POT (Power of Two)
이미지 캔버스를 2의 거듭제곱 크기로 확장합니다. POT 위젯은 항상 표시됩니다.

- **체크 ON/OFF**: POT 기능 활성화/비활성화
- **All / None**: 전체 레이어 POT ON/OFF 일괄 설정
- **Auto**: 이미지 크기에서 자동으로 가장 가까운 POT 계산 (예: 100→128, 300→512)
- **Manual**: 32/64/128/256/512/1024/2048/4096 중 W/H 수동 선택
- **BG (배경색)**: 16x16 색상 사각형 버튼 — T(투명) / B(블랙) / W(화이트) + C(커스텀 컬러 피커)
- **Ceil / Nearest**: POT 계산 방식 선택
  - **Ceil**: 항상 올림 (71→128)
  - **Nearest**: 가장 가까운 POT (71→64, 가까운 쪽 선택)
- **레이어별 POT 토글**: Settings POT ON 시 레이어 목록에 POT 아이콘 열 표시. 개별 클릭으로 해당 레이어만 POT ON/OFF. POT ON 레이어만 `POT/` 폴더에 Export. P키로 선택 레이어 일괄 토글
- **Resize Type** (Nuke Reformat 기준):

| 타입 | 설명 |
|------|------|
| **None** | 스케일 없이 중앙 배치 (기본) |
| **Fit** | 전체가 보이도록 균일 축소 (빈 영역 발생 가능) |
| **Fill** | 캔버스를 완전히 채우도록 균일 확대 (잘림 발생 가능) |
| **Width** | 너비 맞춤 균일 스케일 |
| **Height** | 높이 맞춤 균일 스케일 |
| **Distort** | 비균일 스케일로 정확히 채움 (비율 무시, 게임 텍스처에 중요) |

- **프리뷰 오버레이**: 프리뷰에 POT 크기 점선 사각형 + 크기 정보 표시. 상단 POT 버튼으로 토글.
- **Export POT**: EXPORT 버튼 왼쪽 POT 체크박스. 체크 시 Settings POT 자동 ON. 레이어별 POT 토글이 ON인 레이어만 `POT/` 서브폴더에 별도 생성 (기본 이미지는 항상 Pad만 적용).

### Scale (다중 배율)
- **1x**: 항상 활성 (기본)
- **.75x**: 0.75배 축소 동시 Export
- **.5x**: 0.5배 축소 동시 Export
- 다중 배율 시 배율별 서브폴더 생성 (`1_00x/`, `0_75x/`, `0_50x/`)

### PNG 옵션
- **Fast/Bal/Best**: PNG 압축 레벨 (1/6/9). 기본 "Bal"
- **OxiPNG**: pyoxipng 라이브러리로 무손실 최적화 (Pillow 대비 15~40% 축소). 설치 시 기본 ON. 미설치 시 자동 비활성화

### Log
- **ON**: 하단 로그 패널 표시
- **OFF**: 로그 패널 숨김 (기본값)

### 세션 자동 저장/복원
PSD 파일 옆에 `.session.json`이 자동으로 저장/복원됩니다 (수동 Save/Load 버튼 없음).

**저장 항목:**
- 레이어 체크 on/off, 가시성(눈) on/off, rename 이름, POT on/off
- 레이어 순서 반전 여부, 트리 모드, 접힌 그룹 상태, 아트 레이어 표시
- Rename 모드, Prefix, Start 번호, Direction, Preset, Provider 등 설정 값
- POT 계산 방식 (Ceil/Nearest), Rename 열 너비
- Format, Merge, Quality, Padding, Color Mode, Unity, UGUI/NGUI, Pivot, Auto Ver, Output 경로
- 프리뷰 BG, Dim 투명도, Tint 설정, Log 표시, 프로젝트명, Auto Export

**자동 저장 트리거:**
- 다른 PSD 파일로 전환할 때 (이전 PSD 세션 자동 저장)
- 앱 종료 시 (`closeEvent`)

**자동 복원:**
- PSD 로드 시 `.session.json` 존재하면 자동 복원 (모든 설정 즉시 적용)
- 레이어 수가 달라진 경우 (PSD 수정됨) 세션 무시
- **Restore** 버튼으로 세션 적용 전 PSD 원본 상태 복원 가능

### Refresh (PSD 경로 행)
현재 PSD 파일을 다시 로드합니다. PSD 경로 행의 Browse 오른쪽에 위치.
- **자동 감지**: QFileSystemWatcher가 파일 변경을 감지하여 300ms 후 자동 reload
- **수동 reload**: 자동 감지가 안 될 경우 Refresh 버튼으로 수동 reload

### Reset All
모든 설정을 기본값으로 초기화합니다. Edit 행의 Find/Replace/Prefix/Suffix/# 필드도 포함하여 초기화.

### ? (단축키 도움말, PSD 경로 행)
Refresh 버튼 오른쪽의 **?** 버튼에 마우스를 올리면 키보드/마우스 단축키 목록이 팝업으로 표시됩니다.

---

## 6. Export (내보내기)

### 기본 내보내기
1. 출력 폴더 설정 (Browse 또는 직접 입력)
2. **EXPORT** 버튼 클릭
3. 진행 상황: `3/22` 형태로 표시
4. 완료 시: 버튼이 "Complete ✓" (초록)으로 2초간 표시 → "EXPORT" 복귀
5. 로그에 각 레이어 결과 출력

### 출력 파일
| 파일 | 조건 |
|------|------|
| `레이어명.png/jpg` | 항상 (체크된 레이어) |
| `_merged.png/jpg` | Merge ON |
| `POT/레이어명.png/jpg` | Export POT ON |
| `POT/_merged.png/jpg` | Export POT ON + Merge ON |
| `POT/_pot_info.json` | Export POT ON (원본/POT 크기 정보) |
| `POT/Materials/mat_*.mat` | FXC_MeshQuad Setup 시 생성 |
| `_unity_layout.json` | Unity ON |
| `FXC_PSDImporter_{Stem}.cs` | Unity ON + UGUI |
| `FXC_PSDImporterNGUI_{Stem}.cs` | Unity ON + NGUI |
| `FXC_MeshQuad_{Suffix}.cs` | Export POT ON + 1x (미존재 시만) |
| `Editor/FXC_MeshQuad_{Suffix}Editor.cs` | Export POT ON + 1x (미존재 시만) |
| `{배율}x/` 서브폴더 | 다중 배율 선택 시 |

### Open Folder
Browse 오른쪽의 **Open Folder** 버튼으로 PSD 파일이 있는 폴더를 탐색기에서 열 수 있습니다.

### Unity 폴더 자동 접미사
Unity ON 시 출력 폴더명에 `_UGUI` 또는 `_NGUI` 접미사가 자동 삽입됩니다.
- 접미사는 버전 앞에 위치: `260225_giftBox_UGUI_v1`
- 이미 접미사가 있으면 중복 삽입 없음
- Unity OFF 시 폴더명 변경 없음 (기존 동작 유지)
- UGUI ↔ NGUI 전환 시 Output 경로가 실시간으로 갱신됨

### Auto Version
Export 행의 **Auto Ver** 체크박스로 제어. 출력 폴더가 이미 존재하면 버전을 자동 증가합니다.
```
260225_giftBox_UGUI_v1  (존재) → 260225_giftBox_UGUI_v2
260225_giftBox_UGUI_v2  (존재) → 260225_giftBox_UGUI_v3
260225_giftBox_UGUI     (존재) → 260225_giftBox_UGUI_v2
```
- Auto Ver OFF 시 기존 폴더에 덮어쓰기 (기존 동작)
- 설정은 QSettings로 앱 전역 저장 (PSD별이 아닌 전역)

---

## 7. Unity Export

PSD 레이어를 Unity에서 원본 위치 그대로 UGUI/NGUI로 재현하는 기능.

### PSD Extractor 측 (공통)
1. Output 패널에서 **Unity 체크 ON**
2. **UGUI** 또는 **NGUI** 선택 (SegmentedButton)
3. **Pivot** 선택 (9방향, 기본 Bottom-Center)
4. Export → 이미지 + `_unity_layout.json` + C# 임포터 스크립트 생성
   - UGUI: `FXC_PSDImporter_{Stem}.cs` (PSD별 고유 클래스명)
   - NGUI: `FXC_PSDImporterNGUI_{Stem}.cs` + `FXC_PSDImporterNGUI_{Stem}Editor.cs`
   - NGUI 모드: 이미지가 PSD 파일명과 동일한 서브폴더에 저장됨
   - 출력 폴더명에 `_UGUI`/`_NGUI` 접미사 자동 삽입 (버전 앞 위치)

### Unity 측 (UGUI)
1. 출력 폴더를 Unity 프로젝트에 통째 복사
2. Unity 메뉴 **Tools > FXC PSD Importer** 실행
3. Browse로 `_unity_layout.json` 선택
4. **Setup Sprites** → 텍스처를 Sprite 타입으로 일괄 변환
5. **Import to Scene** → Canvas + UGUI 계층 자동 생성

### Unity 측 (NGUI)
1. 출력 폴더를 Unity 프로젝트에 통째 복사
2. Unity 메뉴 **Tools > FXC PSD Importer (NGUI)** 실행
3. Browse로 `_unity_layout.json` 선택
4. **Setup Textures** → 이미지 폴더 텍스처 일괄 설정 (Sprite/Readable/Uncompressed)
5. **Make Atlas** → NGUI Atlas 자동 생성 (NGUIAtlas + Material + packed PNG)
6. Base Depth / Depth Step 설정
7. **Import to Scene** → NGUI 하이어라키 자동 생성
- Atlas 업데이트: 이미지 추가/삭제 후 이미지 폴더 우클릭 → Open Atlas Updater → Sync

### 생성되는 Unity 계층 (UGUI)
```
Canvas (ScreenSpaceOverlay)
└── ch (root, PSD 캔버스 크기, pivot 적용)
    └── fxRoot_anim (애니메이션 타겟 컨테이너)
        ├── Group1 (빈 GameObject)
        │   ├── s_body_01 (RectTransform + Image, fxt_→s_ 자동 변환)
        │   └── s_arm_R (RectTransform + Image)
        └── s_leg_01 (RectTransform + Image)
```
- `fxt_` prefix → `s_` 자동 변환 (NGUI와 동일한 텍스처→스프라이트 네이밍 컨벤션)

### 생성되는 Unity 계층 (NGUI)
```
GameObject (FXC_PSDImporterNGUI 스크립트)
└── 260225_giftBox_v1 (PSD 파일명 루트)
    └── fxRoot_anim (애니메이션 타겟 컨테이너)
        ├── Group1 (빈 GameObject)
        │   ├── s_body_01 (UISprite, fxt_→s_ 자동 변환)
        │   └── s_arm_R (UISprite)
        └── s_leg_01 (UISprite)
```
- `fxRoot_anim`: 애니메이션 데이터를 연결하는 빈 오브젝트 (루트 바로 아래)
- `fxt_` prefix → `s_` 자동 변환 (텍스처→스프라이트 네이밍 컨벤션)
- Position은 `Mathf.RoundToInt()`로 정수 반올림 (픽셀 퍼펙트)

각 레이어는 PSD 원본 위치에 정확히 배치되며, opacity/visibility도 반영됩니다.

### Output 경로 및 폴더 관리
- **Unity 연동 경로 전환**: Unity ON → 프로젝트 경로 적용, Unity OFF → PSD 파일 경로로 복원
- Browse 왼쪽 **●** dot 인디케이터로 출력 폴더 존재 여부를 실시간 표시 (초록=존재, 회색=미존재)
- 폴더를 외부에서 삭제/생성해도 자동 갱신 (QFileSystemWatcher)
- **Delete 버튼**: 출력 폴더 삭제 (다크 스킨 확인 팝업). 항상 표시, 폴더 존재 시만 활성화
- **Open Folder**: PSD 파일이 있는 위치의 폴더 열기

### UGUI/NGUI 모드 구분
- 세그먼트 버튼의 활성 텍스트 색상으로 시각 구분
- **UGUI**: 스카이 블루 (#4FC1E9) — Unity 공식 UI 시스템
- **NGUI**: 소프트 그린 (#8CC152) — 서드파티 커뮤니티 플러그인

---

## 8. 키보드/마우스 단축키 종합

### 레이어 리스트
| 조작 | 기능 |
|------|------|
| **클릭** | 레이어 선택 (프리뷰 표시) |
| **그룹 헤더 클릭** | 그룹 접기/펼치기 토글 (트리 모드) |
| **Ctrl+클릭** | 다중 선택 추가/해제 |
| **Shift+클릭** | 범위 선택 |
| **Ctrl+A** | 전체 레이어 선택 (하이라이트) |
| **Space** | 선택된 레이어 체크 토글 (다중 시 일괄) |
| **E** | 선택된 레이어 가시성(눈) 토글 (다중 시 일괄) |
| **P** | 선택된 레이어 POT 토글 (다중 시 일괄, Settings POT ON 시) |
| **A** | 레이어 선택 해제 (하이라이트만 해제) |
| **더블클릭 (빈 영역)** | PSD 파일 열기 다이얼로그 |

### 프리뷰
| 조작 | 기능 |
|------|------|
| **마우스 휠** | 줌 인/아웃 (10% ~ 1600%) |
| **더블클릭** | 줌 100% 리셋 |
| **드래그** | 패닝 |
| **Tab** | PSD 정보 오버레이 토글 |
| **Space** | 포커스 모드 토글 (패널 숨기고 리스트+프리뷰만) |
| **A** | 레이어 선택 해제 (하이라이트만 해제, 체크 유지) |

### 선택 슬롯 (1~5)
| 조작 | 기능 |
|------|------|
| **빈 슬롯 클릭** | 현재 선택 저장 |
| **채워진 슬롯 클릭** | 저장된 선택 불러오기 |
| **Ctrl+클릭** | 슬롯 내용 삭제 |

### Rename/Edit
| 조작 | 기능 |
|------|------|
| **Ctrl+Z** | Undo (Rename/Check/Visible 되돌리기) |
| **Ctrl+Shift+Z** | Redo |
| **Ctrl+Enter** | Edit 행의 입력 필드에서 Apply Edit 실행 |
| **Alt+더블클릭** | Rename/Find/Replace 필드에서 `_` 구분자 단어 선택 |

### 기타
| 조작 | 기능 |
|------|------|
| **경로란 더블클릭** | 마지막 파일 자동 로드 |
| **Prefix/Find/Replace 더블클릭** | 빈 필드에 기본값 "fxt_" 입력 |
| **Dim 라벨 더블클릭** | Dim 값 기본 30% 복원 |

---

## 9. FXC_MeshQuad (Shader FX Quad 워크플로우)

POT(Distort) 텍스처를 Unity Quad에 적용하는 워크플로우를 자동화합니다.

### PSD Exporter 측
POT Export 시 자동으로 생성되는 파일:
- `POT/_pot_info.json` — 원본/POT 크기 정보 (각 레이어별)
- `FXC_MeshQuad_{Suffix}.cs` — Runtime 스크립트 (미존재 시만 생성)
- `Editor/FXC_MeshQuad_{Suffix}Editor.cs` — Editor 스크립트 (미존재 시만 생성)

### Unity 측 워크플로우
1. PSD Exporter에서 **POT + Distort** Export
2. 출력 폴더를 Unity 프로젝트에 복사
3. 빈 GameObject 생성 → `FXC_MeshQuad` 스크립트 드래그
4. **Inspector에서 POT Info JSON 자동 할당** (스크립트 경로 기준 탐색)
5. **Setup** 버튼 → `fxRoot_Anim` + 하위 Mesh 오브젝트 일괄 생성
6. 각 Quad는 **Transform.localScale = (1,1,1)** 유지 (메쉬 버텍스가 실제 픽셀 크기 정의)
7. MeshRenderer의 Material에 텍스처 할당 → 셰이더 애니메이션 작업

### 생성되는 Unity 계층
```
Root (FXC_MeshQuad)
  └─ fxRoot_Anim
       ├─ layer1 (FXC_MeshQuadChild + MeshFilter[hidden] + MeshRenderer)
       ├─ layer2 ...
       └─ ...
```

### 주요 특징
- **Mesh Size**: Inspector에서 Vector3 (X Y Z) 필드로 크기 조절 (Transform Scale 스타일)
- **Material**: MeshRenderer가 Inspector에서 직접 노출 → Animation 키프레임 생성 가능
- **Play 모드 보호**: Inspector에서 수정한 Material 프로퍼티(텍스처 등)가 Play 전 자동 저장 (`FXC_PlayModeSaver`)
- **Shader fallback**: `FX Team/fxs_shine` → `Unlit/Texture` → `Standard`
- **NGUI depth**: `UICustomRendererWidget` 자동 추가 + baseDepth/depthStep으로 depth 제어

### _pot_info.json 구조
```json
{
  "psd_file": "260224_luckyJacpot_text_v2.psd",
  "pot_calc": "nearest",
  "resize_type": "distort",
  "layers": [
    {
      "name": "luckyJacpot_text",
      "file": "luckyJacpot_text.png",
      "original": { "width": 187, "height": 23 },
      "pot": { "width": 128, "height": 32 }
    }
  ]
}
```

---

## 10. 프로젝트 프리셋

프로젝트별 Export 경로와 Unity 타입을 빠르게 전환합니다.

### 사용법
1. Output 패널의 **프로젝트 콤보** 에서 프로젝트 선택
2. Unity 타입(UGUI/NGUI) + Export 경로가 자동 설정됨 (Unity ON 시)
3. `✎` 버튼으로 프로젝트 목록 편집 (추가/삭제/경로 변경)
- **참고:** Output 패널의 UGUI/NGUI 세그먼트를 변경해도 프로젝트 설정에는 반영되지 않습니다. 프로젝트의 UGUI/NGUI 타입은 `✎` Project Manager에서만 변경 가능합니다.

### 기본 프로젝트
- 포커 PC (NGUI), 포커 모바일 (NGUI)
- 바둑 PC (UGUI), 바둑 모바일 (UGUI)

### Auto Export
PSD 파일 변경 감지 시 자동으로 Export 실행 (Export 패널의 **Auto Export** 체크박스).
- Photoshop에서 저장 → 앱이 PSD 변경 감지 → 자동 reload → 자동 Export
- 세션에 상태 저장

---

## 다크 테마 컬러 팔레트

```
#1e1e1e  → 윈도우/캔버스 배경
#2b2b2b  → 패널 배경
#323232  → 레이어 리스트 배경
#535353  → 입력 필드
#3c3c3c  → 테두리, 버튼 배경
#e0e0e0  → 기본 텍스트
#666666  → 비활성 텍스트 (눈 OFF 레이어명)
#b0964a  → 그룹 헤더 (트리 모드 폴더 아이콘/텍스트)
#2680EB  → 악센트 (Export 버튼, 체크박스, 선택된 레이어 No)
#4FC1E9  → UGUI 활성 텍스트 (Unity 스카이 블루)
#8CC152  → NGUI 활성 텍스트 (소프트 그린)
```
