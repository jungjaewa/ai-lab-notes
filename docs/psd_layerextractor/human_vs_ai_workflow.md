# Human vs AI Workflow — 인간과 AI의 작업 방식 비교

PSD Layer Exporter 프로젝트를 기반으로, 인간 중심 UI/워크플로우와 AI 중심 인터페이스의 근본적 차이를 탐구하는 토론 기록.

---

## 2026-03-02 — 첫 번째 토론: 인간 UI vs AI 인터페이스

### 배경

현재까지 개발된 PSD Layer Exporter는 인간이 반복적인 작업을 더 빠르게 하기 위한 도구. GUI, Unity Inspector, 프리뷰, 단축키 등 모든 것이 인간의 인지-판단-조작 루프를 최적화하는 설계. AI라면 같은 업무를 어떻게 처리하며, 어떤 인터페이스가 필요한가?

### 현재 인간 워크플로우

```
[눈으로 확인] → [손으로 선택] → [하나씩 조정] → [결과 확인] → [반복]
```

PSD 열기 → 레이어 시각적 확인 → 체크/언체크 → 이름 보고 rename →
프리뷰로 검증 → 설정 조정 → Export → Unity 복사 → Setup 클릭 →
Inspector에서 텍스처 확인 → 애니메이션 작업

**인간에게 필요한 것:**
- 썸네일, 프리뷰 — "이게 맞는 레이어인지" 눈으로 확인
- 체크박스, 슬라이더 — 손가락으로 하나씩 토글
- Undo/Redo — 실수를 되돌리기 위해
- 세션 저장 — 어제 하던 작업을 기억 못 하니까
- 중복 경고 (빨간색) — 실수를 눈으로 잡기 위해
- Dim/Tint 프리뷰 — 레이어 간 관계를 시각적으로 파악
- 단축키 — 반복 동작의 물리적 피로 감소

**핵심**: 인간은 **시각적 확인 → 판단 → 물리적 조작**의 루프가 느리기 때문에, UI는 이 루프를 최대한 빠르게 만드는 것이 목표.

### AI가 같은 작업을 한다면

```
[의도 해석] → [전체 분석] → [일괄 실행] → [검증] → [완료]
```

AI에게는 GUI가 필요 없다. 대신:

#### 1. 입력: 선언적 의도 (Intent)

인간이 20번 클릭할 것을 한 문장으로:

```yaml
# 인간: PSD 열고 → 레이어 하나씩 보고 → 체크하고 → rename하고 → POT 설정하고...
# AI: 이것만 받으면 됨

task: export_psd_for_unity
source: "260224_luckyJacpot_text_v2.psd"
target_project: "포커 모바일"
options:
  naming: "fxt_{korean_to_english}"
  pot: { mode: distort, calc: nearest }
  unity: { type: NGUI, pivot: bottom-center }
  shader: fxs_shine
  exclude_layers: ["배경", "가이드"]   # 또는 AI가 자동 판단
```

**차이점**: 인간은 "이 레이어가 뭔지" 썸네일로 확인해야 하지만, AI는 레이어명 + 크기 + 위치 데이터만으로 판단 가능.

#### 2. 처리: 병렬 일괄 실행

```
인간                          AI
─────────────────────────    ─────────────────────────
레이어 1 rename... [2초]      모든 레이어 동시 분석 + rename
레이어 2 rename... [2초]      [0.1초]
...20개 × 2초 = 40초

프리뷰 확인... [3초]          좌표 수치로 검증 [0ms]
POT 설정 조정... [5초]        최적 POT 크기 자동 계산 [0ms]
Export 대기... [10초]         Export [10초] (I/O 동일)
Unity에서 Setup... [30초]     Unity API 직접 호출 [2초]
```

**차이점**: 인간에게 "시각적 확인"이 필요한 단계가 AI에게는 전부 불필요. 반면 디스크 I/O나 이미지 처리 같은 물리적 시간은 동일.

#### 3. 인터페이스: API + 스키마

```
인간용 UI                    AI용 인터페이스
──────────────              ──────────────────
QGraphicsView (프리뷰)       → 불필요 (좌표 데이터로 충분)
체크박스 42개                → JSON 배열: ["layer1", "layer3"]
색상 선택 다이얼로그          → hex string: "#ff0000"
슬라이더 (Dim 0~100%)       → 불필요 (시각적 확인 안 함)
Undo/Redo 30단계            → 불필요 (재생성이 더 빠름)
세션 .json                  → 불필요 (전체 상태를 한 번에 구성)
단축키/마우스 호버            → 불필요 (물리적 입력 없음)
진행률 바                    → 불필요 (비동기 콜백이면 충분)
중복 경고 빨간색 표시         → 사전에 중복 자체를 만들지 않음
```

AI에게 필요한 것:

```
1. Tool 정의 (함수 시그니처 + 설명)
   - extract_layers(psd_path, options) → LayerInfo[]
   - rename_layers(layers, rules) → RenameMap
   - export(layers, format, pot, scale) → FilePaths
   - setup_unity(json, project_path) → GameObjects

2. 스키마 (입출력 구조 정의)
   - PSD 레이어 구조 → JSON
   - 좌표계 변환 규칙 → 문서
   - 셰이더 프로퍼티 목록 → 구조화된 데이터

3. 피드백 (실행 결과)
   - 성공/실패 + 에러 메시지 (텍스트)
   - 생성된 파일 목록 (경로)
   - 수치 검증 결과 (좌표, 크기)
```

#### 4. 검증: 수치 vs 시각

```
인간의 검증                           AI의 검증
──────────────                       ──────────────
프리뷰에서 "이게 맞나?" 눈으로 확인     layer.width == expected_width ✓
"위치가 좀 어긋난 것 같은데..."         abs(unity.x - expected.x) < 0.5 ✓
"이 셰이더 색감이 좀..."              mat.HasProperty("_RShineTex") ✓
"아 fxt_로 시작하는거 하나 빠졌네"      assert all(f.startswith("fxs_")) ✓
```

### 근본적 차이 요약

| 영역 | 인간 | AI |
|------|------|-----|
| **입력** | 시각 인지 → 판단 → 물리 조작 (느림) | 구조화된 데이터 직접 처리 (빠름) |
| **확인** | 눈으로 프리뷰 필수 | 수치 검증으로 충분 |
| **기억** | 세션 저장, Undo가 필수 | 상태를 재구성하면 됨 |
| **실수** | 경고 UI로 사전 방지 | 실수 자체를 안 함 (규칙 100% 적용) |
| **반복** | 단축키로 피로 감소 | 루프 한 번이면 끝 |
| **병렬** | 한 번에 하나씩 | 전체를 동시에 |
| **병목** | 인지 → 판단 → 조작 루프 | I/O (디스크, 네트워크) |

### 현실적 AI 워크플로우 (지금 바로 가능한 것)

지금 진행하는 대화 자체가 이미 AI 워크플로우:

```
인간: "fxt_ → fxs_ 변환해줘"
 AI: 코드 읽기 → 변경 지점 파악 → 수정 → 완료
     (GUI 불필요, 프리뷰 불필요, Undo 불필요)
```

앱에 CLI/API 레이어를 추가한다면:

```bash
# 인간이 GUI에서 5분 걸리는 작업
python psd_extractor.py \
  --psd "jackpot.psd" \
  --rename auto-kr-en \
  --pot distort nearest \
  --unity ngui bottom-center \
  --project "포커 모바일" \
  --export
```

이것이 AI가 호출할 수 있는 **도구(Tool)** 가 됨. GUI는 인간용, CLI/API는 AI용 — 백엔드(`psd_extractor.py`)는 동일.

**결론**: 핵심 로직이 `psd_extractor.py`에 분리되어 있고, GUI는 그 위의 인간용 껍질. AI용 인터페이스를 추가하려면 같은 백엔드 위에 **구조화된 입력(JSON/YAML) → 함수 호출 → 구조화된 출력** 레이어만 얹으면 됨.

---

## 2026-03-02 — 두 번째 토론: AI 인터페이스 프로토타입

### "보여줘"

이론적 비교만으로는 부족하여, 실제 동작하는 AI 인터페이스 프로토타입을 구현.

### 파일: `psd_ai_interface.py`

기존 백엔드(`psd_extractor.py`)를 그대로 import하되, 인간용 GUI 대신 **구조화된 입출력** 레이어를 얹은 형태.

### 인간 GUI vs AI 인터페이스 — 같은 백엔드, 다른 껍질

```
psd_extractor.py (백엔드 — 핵심 로직)
     │
     ├── psd_extractor_gui_qt.py (인간용)
     │   └── 42개 위젯, 프리뷰, Undo, 세션, 단축키...
     │
     └── psd_ai_interface.py (AI용)
         └── ExportTask(dataclass) → PSDAgent.run() → ExportResult(dataclass)
```

### AI 인터페이스의 6가지 구성요소

#### 1. ExportTask — 구조화된 입력 (인간의 42개 위젯 → 1개 dataclass)

```python
@dataclass
class ExportTask:
    psd_path: str
    include_layers: list       # 체크박스 42개 → 이름 리스트 1개
    rename_prefix: str         # Rename 패널 전체 → 문자열 1개
    pot_enabled: bool          # POT 섹션 6개 위젯 → bool + 파라미터
    unity_type: str            # UGUI/NGUI 세그먼트 → 문자열 1개
    ...
```

#### 2. 프리셋 — 반복 패턴 (인간의 '프로젝트 프리셋' 대응)

```bash
$ python psd_ai_interface.py presets
Available Presets:
  spine_character          - prefix=fxt_, OxiPNG
  unity_ngui_fx            - prefix=fxt_, POT(nearest+distort), Unity(NGUI), OxiPNG
  unity_ugui               - prefix=fxt_, Unity(UGUI), OxiPNG
  web_assets               - OxiPNG
  quick_check              - default
```

#### 3. inspect — PSD 분석 (인간의 '눈으로 확인' → 구조화된 데이터)

```bash
$ python psd_ai_interface.py inspect ch.psd --format summary
ch.psd: 210x283, 22 art layers, 1 groups

Layers:
  [G] [v] 1
      [v]   왼쪽다리  52x62
      [v]   오른쪽다리  56x62
      [v]   몸통  210x245
      ...
```

```bash
$ python psd_ai_interface.py inspect ch.psd --format json
{
  "file_name": "ch.psd",
  "width": 210, "height": 283,
  "art_layers": 22, "groups": 1,
  "has_korean_names": true,
  "layers": [
    {"name": "왼쪽다리", "size": [52, 62], "position": [46, 221], ...},
    ...
  ]
}
```

**핵심 차이**: 인간은 PSD를 열고 스크롤하며 레이어를 하나씩 확인 (30초~1분). AI는 `inspect` 1회 호출로 전체 구조를 JSON으로 받아 즉시 분석.

#### 4. run --dry-run — 실행 전 검증 (인간의 설정 확인 → 태스크 프리뷰)

```bash
$ python psd_ai_interface.py run ch.psd --preset unity_ngui_fx --dry-run
=== Dry Run: Task Configuration ===
{
  "rename_prefix": "fxt_",
  "pot_enabled": true,
  "pot_calc": "nearest",
  "pot_resize": "distort",
  "unity_enabled": true,
  "unity_type": "NGUI",
  "pivot": "bottom-center",
  ...
}
```

인간은 Export 전에 설정을 눈으로 하나씩 확인. AI는 dry-run으로 태스크 구성을 JSON으로 검증한 후 실행.

#### 5. run — 실행 (인간의 EXPORT 버튼 → 함수 호출)

```bash
$ python psd_ai_interface.py run ch.psd --preset quick_check -o /tmp/test
```

결과:
```json
{
  "success": true,
  "exported": 22,
  "errors": 0,
  "elapsed_seconds": 1.82,
  "validation": {
    "all_files_exist": true,
    "no_empty_files": true,
    "name_conflicts": [],
    "passed": true
  }
}
```

#### 6. ExportResult — 구조화된 출력 (인간의 로그 텍스트 → 파싱 가능한 JSON)

```python
@dataclass
class ExportResult:
    success: bool              # 진행률 바 + "Complete ✓" → bool 1개
    exported: int              # 로그 스크롤 → 숫자 1개
    files: list                # 파일 탐색기 열기 → 경로 리스트
    validation: dict           # 눈으로 확인 → 자동 수치 검증
    ...
```

### 실행 시간 비교 (ch.psd, 22 레이어)

```
인간 (GUI)                             AI (psd_ai_interface.py)
──────────────────────────────         ──────────────────────────
PSD 열기 + 로딩 대기........... 3초     inspect().............. 0.5초
레이어 확인 (스크롤)........... 5초     (불필요 — JSON으로 즉시 파악)
설정 조정 (클릭 × N).......... 10초    preset 1개 선택........ 0초
프리뷰 확인................... 3초     (불필요 — 수치 검증)
EXPORT 클릭 + 대기............ 5초     run().................. 1.8초
결과 확인 (폴더 열기)......... 5초     (불필요 — JSON 결과에 포함)
──────────────────────────────         ──────────────────────────
합계: ~31초                             합계: ~2.3초 (13배 빠름)
```

단, I/O 시간(이미지 저장)은 동일. 차이는 전부 **인간의 인지-판단-조작 루프**에서 발생.

### 아키텍처 교훈

```
                    ┌─────────────────────┐
                    │  psd_extractor.py   │  ← 핵심 로직 (불변)
                    │  (백엔드)            │
                    └────────┬────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐ ┌───▼────────┐ ┌──▼──────────┐
     │ GUI (Qt)       │ │ AI API     │ │ CLI (기존)   │
     │ 인간용 42위젯   │ │ dataclass  │ │ argparse     │
     │ 프리뷰/Undo    │ │ JSON I/O   │ │ 텍스트 출력   │
     └────────────────┘ └────────────┘ └─────────────┘
```

좋은 분리 설계가 이미 되어 있었기 때문에, AI 인터페이스를 추가하는 데 **새로운 백엔드 코드 0줄** — 기존 함수를 import하여 감싸기만 하면 됨.

---

## 2026-03-02 — 세 번째 토론: 자동화가 만든 역할 전환

### 배경

AI 인터페이스 프로토타입(`psd_ai_interface.py`)을 구현하고 실제 테스트하면서, 동시에 진행된 GUI 기능 개선(fxt_→fxs_ 변환, R Shine 기본 텍스처)이 흥미로운 대조를 만들었다.

### 인간이 요청하고 AI가 구현하는 역전된 구조

전통적 도구 개발:
```
프로그래머가 코드를 쓰고 → 사용자가 GUI를 사용
```

현재 워크플로우:
```
사용자(인간)가 의도를 말하고 → AI가 코드를 작성하고 → 인간이 결과를 확인
```

**fxt_→fxs_ 변환 사례:**
```
인간: "하이어라키에 fxs_로 변환해줘"
 AI:  1. C# 템플릿에서 `new GameObject(layer.name)` 찾기         [0.5초]
      2. `displayName` 변수 패턴 파악 (UGUI/NGUI 선례 참조)      [1초]
      3. fxt_→fxs_ 조건 분기 코드 작성                           [2초]
      4. 편집 적용                                              [즉시]
인간: Unity에서 확인 → "OK"                                      [30초]
```

인간이 하는 일: 의도 전달(10초) + 결과 검증(30초) = 40초
AI가 하는 일: 코드 분석 + 수정 = ~4초

**R Shine 텍스처 사례:**
```
인간: [스크린샷 첨부] "이 슬롯에 이 텍스처를 기본 할당해줘"
 AI:  1. 셰이더 파일 읽기 → _RShineTex 프로퍼티명 확인           [1초]
      2. 텍스처 프리로드 코드 추가                               [2초]
      3. 조건부 할당 (null/white 체크) 코드 추가                  [2초]
      4. 편집 적용                                              [즉시]
인간: Unity에서 확인 → "OK"                                      [30초]
```

### 인간-AI 역할 분담 패턴

```
┌──────────────────────────────────────────────────────┐
│                   현재 워크플로우                       │
├──────────────────┬───────────────────────────────────┤
│  인간의 역할      │  AI의 역할                         │
├──────────────────┼───────────────────────────────────┤
│  의도 정의        │  코드베이스 탐색                    │
│  (무엇을 원하는지)│  (어디를 수정해야 하는지 자동 파악)   │
│                  │                                   │
│  도메인 지식 제공  │  패턴 인식 + 적용                   │
│  (fxs_ prefix,   │  (displayName 패턴 재사용,          │
│   셰이더 프로퍼티) │   조건부 할당 안전 패턴 적용)        │
│                  │                                   │
│  시각적 검증      │  구조적 검증                        │
│  (Unity에서 확인) │  (코드 일관성, 컴파일 가능성)        │
│                  │                                   │
│  최종 승인        │  문서화 (MD 자동 업데이트)           │
└──────────────────┴───────────────────────────────────┘
```

### GUI 개선 vs AI 인터페이스 — 같은 날, 다른 방향

같은 2026-03-02에 두 가지가 동시에 진행:

**GUI 쪽 (인간을 위한 자동화):**
- fxt_→fxs_ 변환: 인간이 하이어라키에서 수동 rename → 자동 변환
- R Shine 텍스처: 인간이 Material Inspector에서 수동 드래그 → 자동 할당
- 목표: "인간이 반복하던 클릭 N번을 0번으로"

**AI 쪽 (AI를 위한 인터페이스):**
- `psd_ai_interface.py`: 42개 위젯 → 1개 dataclass
- inspect/run/presets: GUI 전체 → CLI 3개 명령
- 목표: "AI가 이해할 수 없는 GUI 위젯을 구조화된 데이터로"

```
두 방향 모두 같은 본질:
  "반복적인 인지-판단-조작 루프를 제거"

GUI 자동화: 인간의 루프를 줄임 (10클릭 → 0클릭)
AI 인터페이스: 인간의 루프 자체를 우회 (GUI → API 직접 호출)
```

### 자동화의 계층

```
Level 0: 수동          포토샵에서 레이어 하나씩 저장
Level 1: 도구          PSD Extractor GUI — 배치 처리, 프리뷰
Level 2: 도구 내 자동화  fxt_→fxs_ 자동 변환, R Shine 자동 할당
Level 3: AI 보조       "이 기능 추가해줘" → AI가 코드 수정
Level 4: AI 직접 실행   psd_ai_interface.py — AI가 도구를 직접 호출
Level 5: ???          AI가 PSD 내용을 이해하고 스스로 판단?
```

현재 Level 2~4 사이를 오가는 중. Level 5는 멀티모달 AI가 레이어 이미지 자체를 분석하는 단계.

### 각 레벨의 구체적 예시

#### Level 2: 도구 내 자동화 — "코드에 내장된 규칙이 반복 작업을 대신"

인간이 GUI를 사용할 때, 코드가 알아서 처리해주는 부분:

| 기능 | 인간이 안 해도 되는 것 |
|------|---------------------|
| `fxt_` → `fxs_` 변환 | Setup 클릭만 하면 하이어라키명 자동 변환. 예전엔 20개 오브젝트를 하나씩 rename |
| `_RShineTex` 자동 할당 | Material 생성 시 그라디언트 텍스처가 이미 들어가 있음. 예전엔 Inspector에서 드래그 × N회 |
| POT 자동 계산 | 187×23 → 128×32 (nearest). 인간이 "2의 거듭제곱 중 가장 가까운 게 뭐지?" 계산할 필요 없음 |
| `_pot_info.json` 생성 | Export 시 원본/POT 크기 자동 기록. 예전엔 메모장에 수동 기록 |
| Rename 중복 감지 | 빨간색으로 실시간 경고. 인간이 22개 이름을 눈으로 비교할 필요 없음 |
| Auto Ver (`_v1` → `_v2`) | 폴더 존재하면 버전 자동 증가. 예전엔 수동으로 v1 확인하고 v2로 변경 |

**핵심**: 인간은 여전히 **GUI를 직접 조작**하지만, 규칙 기반 반복 작업은 코드가 처리.

#### Level 3: AI 보조 — "인간이 의도를 말하면 AI가 코드를 수정"

지금 이 대화에서 일어나고 있는 것:

| 요청 | AI가 한 일 |
|------|-----------|
| "fxs_로 변환해줘" | C# 템플릿 찾기 → displayName 패턴 파악 → 코드 5줄 추가 |
| "R Shine에 이 텍스처 할당해줘" | 셰이더 파일 읽기 → 프로퍼티명 확인 → 프리로드 + 조건부 할당 코드 추가 |
| "MD 업데이트해줘" | 5개 파일 읽기 → 변경사항 파악 → 각각에 맞는 형식으로 갱신 |
| "mat_ prefix 제거해줘" | 템플릿 내 3곳 찾기 → `"mat_" +` 삭제 |

**핵심**: 인간이 **도구 자체를 수정하는 것**을 AI가 대행. Level 2의 자동화 규칙을 **만드는** 행위.

#### Level 4: AI 직접 실행 — "AI가 GUI를 거치지 않고 도구를 직접 호출"

`psd_ai_interface.py`가 이 레벨:

```python
# AI가 직접 실행 (인간의 GUI 조작 0회)
task = ExportTask(
    psd_path="jackpot.psd",
    rename_prefix="fxt_",
    pot_enabled=True, pot_calc="nearest", pot_resize="distort",
    unity_type="NGUI",
)
result = PSDAgent().run(task)
# → 22개 레이어 export, 1.82초, 검증 통과
```

인간이 GUI에서 하는 일 전체(PSD 열기 → 스크롤 → 체크 → rename 설정 → POT 설정 → Unity 설정 → EXPORT)가 **함수 호출 1회**로 대체. 단, 현재는 프로토타입 수준 — "어떤 레이어를 뺄지", "rename을 어떻게 할지" 같은 판단은 아직 인간이 결정해야 함.

#### 레벨 간 관계

```
Level 2                    Level 3                    Level 4
(도구가 알아서)             (AI가 도구를 고쳐줌)         (AI가 도구를 직접 씀)
─────────────────         ─────────────────          ─────────────────
fxt_→fxs_ 작동   ←────── fxt_→fxs_ 규칙 생성
R Shine 자동 할당  ←────── R Shine 코드 작성
POT 자동 계산               MD 자동 갱신
중복 경고                                            psd_ai_interface.py
                                                     inspect / run
```

Level 3이 Level 2를 **만들고**, Level 4는 Level 2를 **우회**하는 관계.

현재 가장 많이 쓰이는 건 **Level 3** — "이거 추가해줘" → AI가 코드 수정 → 인간이 확인하는 루프가 이 프로젝트의 주된 개발 방식.

### Level 4의 실제 장벽: "AI가 맥락을 모른다"

Level 4로 가려면 AI가 직접 도구를 실행해야 하는데, 현재 가장 큰 장벽은 **인간의 머릿속에만 있는 암묵지**:

```
인간의 머릿속 (암묵지)              GUI에서 클릭으로 전달
──────────────────────            ──────────────────────
"이건 포커 모바일 이펙트야"    →    프로젝트: 포커 모바일 (NGUI)
"셰이더 FX용이야"              →    POT ON + Distort + fxs_shine
"이 3개 레이어는 가이드니까 빼"  →    체크 해제
"이름은 fxt_로 시작해야 해"     →    Rename prefix: fxt_
"피봇은 아래 중앙"             →    Pivot: Bottom-Center
```

이 5가지 판단을 AI가 스스로 할 수 없는 게 현재 Level 4의 한계.

#### Level 4로 가는 3가지 현실적 방법

**방법 1: 워크스페이스 규칙 파일 (가장 실용적)**

PSD 파일 옆에 `.fxc_workspace.json`을 한 번만 만들어 두면:

```json
{
  "project": "포커 모바일",
  "workflow": "shader_fx",
  "defaults": {
    "rename_prefix": "fxt_",
    "pot": { "calc": "nearest", "resize": "distort" },
    "unity": { "type": "NGUI", "pivot": "bottom-center" },
    "shader": "fxs_shine",
    "exclude_patterns": ["가이드", "배경", "guide", "bg_"]
  }
}
```

그러면 AI한테 이렇게만 말하면 됨:
```
"jackpot.psd export 해줘"
```

AI가 하는 일:
```
1. PSD 옆에 .fxc_workspace.json 발견
2. workflow: shader_fx → POT+Distort+fxs_shine 자동 적용
3. exclude_patterns으로 가이드 레이어 자동 제외
4. project: 포커 모바일 → 출력 경로 자동 결정
5. 실행 → 결과 반환
```

인간이 할 일: 처음에 워크스페이스 파일 한 번 만들기 (또는 AI한테 "포커 모바일 이펙트 워크스페이스 만들어줘"라고 하면 됨).

**방법 2: 폴더 구조가 곧 규칙 (제로 설정)**

```
D:\02_GIT\Classic\hangame-poker-unity\
  Poker\Assets\_FX\
    260224_luckyJacpot_text_v2\     ← _FX 폴더 안 = 이펙트
      260224_luckyJacpot_text_v2.psd

  Poker\Assets\_UI\
    login_popup\                     ← _UI 폴더 안 = UI
      login_popup.psd
```

폴더 경로 자체가 맥락:
```
_FX/ 하위  → shader_fx 워크플로우 (POT, NGUI, fxs_shine)
_UI/ 하위  → ui 워크플로우 (UGUI 또는 NGUI, 스프라이트)
_Anim/ 하위 → animation 워크플로우 (Spine, 다중 배율)
```

AI가 PSD 경로만 보면 어떤 워크플로우인지 판단 가능. 이미 프로젝트 프리셋 시스템이 하는 것과 비슷 — 프로젝트 경로가 Unity 타입을 결정하듯.

**방법 3: 대화로 한 번만 알려주기 (가장 자연스러움)**

```
인간: "앞으로 이 폴더의 PSD는 전부 포커 모바일 이펙트야.
       POT distort, NGUI, fxs_shine, 가이드 레이어는 빼줘."

 AI: (이 컨텍스트를 MEMORY.md에 저장)
     "알겠습니다. 이 경로의 PSD는 shader_fx 워크플로우로 처리하겠습니다."

--- 다음 세션 ---

인간: "jackpot.psd export 해줘"
 AI: (MEMORY.md 참조 → 이전에 알려준 규칙 적용 → 실행)
```

Level 3과 가장 가까운데, 차이는 **코드 수정 없이 실행만** 한다는 점.

#### 현실적으로 부족한 것

```
지금 있는 것                          없는 것
─────────────────                   ─────────────────
psd_ai_interface.py (실행 엔진)      맥락 자동 감지 (어떤 워크플로우?)
프리셋 5종 (실행 옵션 묶음)            레이어 자동 판단 (뭘 빼야 하는지?)
inspect (PSD 분석)                   Unity 프로젝트 연결 (어디로 복사?)
ExportTask (구조화된 입력)            워크스페이스 규칙 시스템
```

가장 큰 빈 칸은 **"이 레이어를 빼야 하는지"** 판단:
```
Level 4 (규칙 기반):  이름에 "가이드/guide/bg_" 포함 → 제외  (지금 가능)
Level 5 (이해 기반):  레이어 이미지를 보고 "이건 보조선이다" 판단  (아직 불가)
```

#### Level 4 핵심 요약

**맥락을 한 번만 설정하면 반복 불필요**하게 만드는 것이 Level 4의 본질.

워크스페이스 규칙 파일이 가장 실용적인 첫 걸음:
```bash
# 1회: 워크스페이스 생성 (AI한테 말하거나 직접 작성)
python psd_ai_interface.py init --preset unity_ngui_fx --path "D:\..\_FX\"

# 매번: PSD 넣고 실행만
python psd_ai_interface.py run jackpot.psd
# → 워크스페이스 규칙 자동 적용 → export → Unity 폴더에 복사까지
```

또는 이 대화에서:
```
인간: "jackpot.psd 포커 모바일 이펙트로 export"
 AI:  psd_ai_interface.py 호출 → 결과 반환 → "22개 완료, 검증 통과"
```

### 관찰: 문서화도 워크플로우의 일부

이 토론 자체가 보여주는 패턴:
```
기능 구현 → MD 업데이트 요청 → AI가 CLAUDE.md + MEMORY.md + dev_journal.md + 이 파일 동시 갱신
```

인간이 5개 MD 파일을 직접 업데이트했다면 30분+. AI는 ~2분. 그런데 "어떤 내용을 기록해야 하는지"의 판단은 인간과 AI의 대화에서 나온다. 문서화 자체가 인간-AI 협업의 산물.

---

## 열린 질문 (다음 토론을 위해)

- AI가 "시각적 판단"이 필요한 경우는? (셰이더 결과물의 미적 평가 등)
- 인간-AI 협업 워크플로우에서 각자의 최적 역할 분담은?
- AI가 Unity Editor 안에서 직접 작업하려면 어떤 브릿지가 필요한가?
- YAML 태스크 파일로 파이프라인 자동화를 어디까지 확장할 수 있는가?
- AI가 PSD 내용을 "이해"하려면 (레이어 이미지 자체를 분석) 어떤 추가 인터페이스가 필요한가?
- Level 5 자동화에 도달하려면 어떤 멀티모달 능력이 필요한가? (이미지 인식 + 도메인 지식 + 실행 능력)
- "인간이 의도를 말하고 AI가 구현"하는 현재 패턴에서, 의도 전달의 효율을 높이는 방법은?
- 자동화 수준이 올라갈수록 인간의 역할은 어떻게 변화하는가? (실행자 → 감독자 → 의사결정자)
- ~~워크스페이스 규칙 파일 vs 폴더 규칙 vs 대화 기억 — 어떤 맥락 전달 방식이 가장 실용적인가?~~ → 세 번째 토론에서 분석 완료
- 워크스페이스 규칙 파일을 실제 구현한다면, GUI의 세션/프로젝트 프리셋 시스템과 어떻게 공존해야 하는가?
