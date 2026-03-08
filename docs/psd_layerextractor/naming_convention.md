# PSD Layer Exporter — Naming Convention

2D 게임 FX/캐릭터 리깅(Spine/Live2D) 파이프라인을 위한 네이밍 규칙 정의.
Auto (KR→EN) Rename, Sequential, Body Part 모드 모두 이 규칙을 따른다.

---

## 1. PSD 파일명

### 형식

```
YYMMDD_FX_{Type}_{Project}_{Title}_v{N}.psd
```

| 필드 | 설명 | 예시 |
|------|------|------|
| `YYMMDD` | 작업 시작일 (6자리) | `260304` |
| `FX` | 팀 고정 접두사 | `FX` |
| `{Type}` | 작업 유형 | `UI` (이펙트), `Ani` (애니메이션) |
| `{Project}` | 프로젝트명 (PascalCase 또는 한글) | `Sahwal`, `Poker` |
| `{Title}` | 에셋 제목 (PascalCase) | `PresentBox`, `CharIdle` |
| `v{N}` | 버전 (정수, Auto Version 대상) | `v1`, `v2` |

### 예시

```
260304_FX_UI_Sahwal_PresentBox_v1.psd      ← UI 이펙트
260115_FX_Ani_Poker_ChipExplosion_v2.psd   ← 애니메이션
260220_FX_UI_Baduk_GiftBox_v1.psd          ← UI 이펙트
```

### Export 시 파일명 활용

| 용도 | 변환 | 결과 |
|------|------|------|
| Unity JSON | 날짜/버전 제거 → 주요 명사 추출 | `fxc_psdImporter_SahwalPresentBox.json` |
| C# 클래스 | 출력 폴더명 → PascalCase | `FXC_PSDImporter_260304FxUiSahwalPresentboxV1` |
| LLM 컨텍스트 | 전체 stem 전달 | `File: 260304_FX_UI_Sahwal_PresentBox_v1` |

---

## 2. PSD 내부 구조 (그룹/레이어 계층)

### 계층 원칙

```
PSD Root
├── {대분류 그룹}              ← depth 0: 메인 파츠 (선물상자, 리본, 배경)
│   ├── {중분류 그룹}          ← depth 1: 상태/변형 (열린상자, 닫힌뚜껑)
│   │   ├── {소분류 그룹}      ← depth 2: 위치/방향 (안쪽아이템, 바깥쪽아이템)
│   │   │   └── 레이어         ← 개별 이미지 (01, 02, 뚜껑장식)
│   │   └── 레이어
│   └── 레이어
└── 레이어                     ← depth 0: 독립 레이어
```

### 입력 언어 모드

PSD에서 그룹/레이어명을 작성하는 세 가지 패턴과 Auto Rename의 처리 방식:

#### 모드 A: 한글+숫자 (권장)

모든 이름을 한글로 작성. Auto Rename이 일괄 번역 + prefix 적용.

```
리본/                    → ribbon_group (번역 + _group)
├── 끝오른쪽             → fxt_ribbon_end_right (번역 + prefix)
├── 끝왼쪽               → fxt_ribbon_end_left
└── 01                   → fxt_ribbon_01 (그룹명 기반 + prefix)
```

**장점**: Auto Rename의 모든 기능 활용 (사전/LLM/noun_modifier 정렬).
**적합**: 초기 작업, 빠른 프로토타이핑, 한글 사용자.

#### 모드 B: 영어+숫자

모든 이름을 영문 snake_case로 직접 작성. Auto Rename은 prefix만 적용.

```
ribbon/                  → ribbon_group (이미 영문 → _group만 추가)
├── ribbon_end_right     → fxt_ribbon_end_right (prefix 추가)
├── ribbon_end_left      → fxt_ribbon_end_left
└── ribbon_01            → fxt_ribbon_01
```

**장점**: 번역 불확실성 없음, 작성자가 정확한 이름 제어.
**적합**: 이미 영문 네이밍에 익숙한 작업자, 정밀한 이름 제어 필요 시.
**규칙**: 본 문서의 noun_modifier 어순과 snake_case 규칙을 직접 따라야 함.

#### 모드 C: 영어+한글+숫자 혼합 (비권장)

하나의 이름 안에 한글과 영어가 섞인 경우. **혼합은 피하는 것을 권장.**

```
❌ 비권장 패턴:
리본end         → 번역 불안정 (한글+영어 경계 파싱 어려움)
arm위           → 번역 불안정
BG뒤            → 번역 불안정

✅ 대신 이렇게:
리본끝          → fxt_ribbon_end (전부 한글)
arm_upper       → fxt_arm_upper (전부 영어)
배경뒤          → fxt_background_back (전부 한글)
```

**혼합이 불가피한 경우의 규칙**:
- 한글 부분이 있으면 전체가 번역 파이프라인으로 진입
- 영어 부분은 LLM이 보존하려 시도하지만 보장되지 않음
- **권장**: 하나의 이름 안에서 언어를 통일할 것 (한글이면 전부 한글, 영어면 전부 영어)

#### 모드 선택 가이드

| 상황 | 권장 모드 | 이유 |
|------|----------|------|
| 첫 작업, 빠른 네이밍 | **A (한글)** | 한글이 자연스럽고 Auto Rename이 처리 |
| 동일 PSD 반복 작업 | **B (영어)** | 이미 확정된 이름 재사용 |
| 팀 내 표준 PSD 제작 | **A 또는 B** (통일) | 혼합 방지 |
| 기존 PSD에 레이어 추가 | **기존 모드 유지** | 일관성 |

> **핵심 원칙**: 하나의 PSD 파일 내에서 **한 가지 언어 모드**를 일관되게 사용한다.
> 그룹은 한글, 레이어는 영어 — 이런 혼합도 가능하지만, 같은 계층(같은 그룹 내 형제들) 안에서는 통일한다.

---

### 그룹 네이밍 규칙 (한글, PSD 내)

| 패턴 | 형식 | 예시 |
|------|------|------|
| 단일 명사 | `{명사}` | 리본, 상자, 배경 |
| 복합 명사 | `{수식어}{명사}` | 선물상자, 닫힌뚜껑 |
| 방향+명사 | `{방향}{명사}` | 안쪽아이템, 바깥쪽리본 |

**권장**: 그룹명에 공백 사용 가능 (`안쪽 아이템`) — 사전 분해(compound split)가 더 정확히 동작.

### 그룹 네이밍 규칙 (영어, PSD 내)

| 패턴 | 형식 | 예시 |
|------|------|------|
| 단일 명사 | `{noun}` | ribbon, box, background |
| 복합 명사 | `{noun}_{modifier}` | gift_box, lid_closed |
| 방향+명사 | `{noun}_{direction}` | item_inner, item_outer |

**규칙**: noun_modifier 순서. `_group` 접미사는 Auto Rename이 자동 추가하므로 PSD에서는 쓰지 않는다.

### 레이어 네이밍 규칙 (한글, PSD 내)

| 패턴 | 형식 | 예시 |
|------|------|------|
| 숫자만 | `{NN}` | 01, 02, 03 |
| 단일 명사 | `{명사}` | 그림자, 뚜껑, 리본 |
| 방향+명사 | `{방향}{명사}` | 끝오른쪽, 왼쪽날개 |
| 명사+번호 | `{명사}{NN}` | 손가락01, 리본끝02 |
| 명사+좌우 | `{명사}_{좌/우}` | 리본끝_우, 팔_좌 |

**권장**: 레이어명이 숫자만일 경우 부모 그룹명이 base name으로 사용됨. 의미 있는 이름을 쓰면 더 정확한 번역 가능.

### 레이어 네이밍 규칙 (영어, PSD 내)

| 패턴 | 형식 | 예시 |
|------|------|------|
| 숫자만 | `{NN}` | 01, 02, 03 |
| 완전한 이름 | `{noun}_{variant}_{index}` | ribbon_end_right, arm_upper_01 |
| 이름+좌우 | `{name}_{Side}` | arm_01_R, leg_L |

**규칙**: prefix(`fxt_` 등)는 PSD에서 쓰지 않는다 — Auto Rename이 자동 추가. noun_modifier 순서 준수.

### 실제 PSD 구조 예시

#### 한글 모드 (모드 A)
```
선물상자                         ← depth 0
├── 열린상자                     ← depth 1 (상태+명사)
│   ├── 바깥쪽아이템             ← depth 2 (방향+명사)
│   │   ├── 09                   ← 숫자 레이어
│   │   ├── 10
│   │   └── 11
│   ├── 안쪽아이템               ← depth 2
│   │   ├── 01
│   │   └── 02 ... 08
│   └── 뚜껑장식
├── 닫힌뚜껑                     ← depth 1
│   ├── 리본                     ← depth 2
│   │   ├── 끝오른쪽             ← 방향 레이어
│   │   ├── 끝왼쪽
│   │   └── 01 ... 05
│   └── 상자
└── 그림자
```

#### 영어 모드 (모드 B)
```
gift_box                         ← depth 0
├── box_open                     ← depth 1
│   ├── item_outer               ← depth 2
│   │   ├── 09
│   │   ├── 10
│   │   └── 11
│   ├── item_inner               ← depth 2
│   │   ├── 01
│   │   └── 02 ... 08
│   └── lid_decoration
├── lid_closed                   ← depth 1
│   ├── ribbon                   ← depth 2
│   │   ├── ribbon_end_right     ← 완전한 이름
│   │   ├── ribbon_end_left
│   │   └── 01 ... 05
│   └── box
└── shadow
```

---

## 3. 영문 Export 네이밍 — 핵심 규칙

### 3.1 전체 구조

```
{prefix}_{noun}_{variant}_{index}_{Side}
```

| 필드 | 필수 | 설명 | 예시 |
|------|------|------|------|
| `{prefix}` | 레이어만 | 프로젝트 접두사 | `fxt_`, `fxt_ch_` |
| `{noun}` | ✓ | 핵심 명사 (카테고리) | `arm`, `item`, `ribbon` |
| `{variant}` | 선택 | 위치/방향/상태 변형 | `upper`, `inner`, `end_right` |
| `{index}` | 선택 | 동일 파츠 번호 (2자리) | `01`, `02` |
| `{Side}` | 선택 | 좌우 구분 (대문자) | `_R`, `_L` |

### 3.2 단어 순서 규칙 — noun_modifier (명사 우선)

**원칙: 명사(카테고리)가 먼저, 변형(variant)이 뒤에.**

이 규칙을 택하는 이유:
1. **정렬**: 파일 탐색기/Unity 하이어라키에서 같은 카테고리가 모여 보임
2. **일관성**: 기존 바디파츠 사전(`arm_upper`, `hair_front`)과 동일
3. **업계 표준**: 게임 에셋 관리에서 noun-first가 표준 (UE5 `SM_Rock_Small`)

```
arm_upper       ← "어떤 arm?" → upper arm
arm_lower       ← "어떤 arm?" → lower arm
item_inner      ← "어떤 item?" → inner item
item_outer      ← "어떤 item?" → outer item
hair_front      ← "어떤 hair?" → front hair
lid_closed      ← "어떤 lid?" → closed lid
box_open        ← "어떤 box?" → open box
ribbon_end      ← "어떤 ribbon 부분?" → ribbon end
```

### 3.3 정렬 비교

**noun_modifier (채택)**:
```
fxt_box_open_01
fxt_box_closed_01
fxt_item_inner_01
fxt_item_inner_02
fxt_item_outer_01
fxt_item_outer_02        ← item 계열이 모두 인접
fxt_lid_closed_01
fxt_lid_open_01          ← lid 계열이 모두 인접
fxt_ribbon_end_left
fxt_ribbon_end_right     ← ribbon 계열이 모두 인접
```

**modifier_noun (미채택)**:
```
fxt_closed_box_01
fxt_closed_lid_01        ← closed 끼리 모임 (의미 없는 그룹)
fxt_inner_item_01
fxt_inner_item_02
fxt_open_box_01
fxt_open_lid_01          ← open 끼리 모임 (의미 없는 그룹)
fxt_outer_item_01
```

### 3.4 변형(variant) 체인

변형이 2단계 이상일 때도 noun → variant1 → variant2 순서:

```
ribbon_end_right    ← noun(ribbon) → 위치(end) → 방향(right)
ribbon_end_left
box_lid_inner       ← noun(box) → 부분(lid) → 위치(inner)
arm_upper_front     ← noun(arm) → 위치(upper) → 방향(front)
```

### 3.5 그룹 rename 규칙

| 항목 | 규칙 | 예시 |
|------|------|------|
| 접두사 | 없음 (prefix 미적용) | `arm_group` (~~`fxt_arm_group`~~) |
| 접미사 | `_group` 자동 추가 | `item_inner_group` |
| 단어 순서 | noun_modifier (레이어와 동일) | `item_inner_group` |

그룹 rename은 LLM 번역 시 자동으로 `_group` 접미사가 추가된다.
수동 편집 시에는 `_group` 없이 자유롭게 지정 가능.

---

## 4. 접두사(Prefix) 시스템

### 파이프라인별 접두사

| 접두사 | 의미 | 적용 단계 | 예시 |
|--------|------|----------|------|
| `fxt_` | FX Texture | PSD Export (이미지 파일) | `fxt_arm_upper_01.png` |
| `fxt_ch_` | FX Texture + Character | 캐릭터 전용 Export | `fxt_ch_arm_upper_01_R.png` |
| `fxs_` | FX Shader | Unity MeshQuad 하이어라키 | `fxs_arm_upper_01` |
| `s_` | Sprite | Unity UGUI/NGUI 하이어라키 | `s_arm_upper_01` |
| `fxc_` | FX Component | Unity 스크립트/JSON | `fxc_psdImporter.json` |

### 변환 흐름

```
PSD 레이어: 윗팔 (한글)
     ↓ Auto Rename
Export:     fxt_arm_upper_01.png     (fxt_ 접두사)
     ↓ Unity Import
UGUI:       s_arm_upper_01           (fxt_ → s_ 변환)
NGUI:       s_arm_upper_01           (fxt_ → s_ 변환)
MeshQuad:   fxs_arm_upper_01         (fxt_ → fxs_ 변환)
```

### 그룹에는 접두사 미적용

그룹 rename은 접두사 없이 순수 영문명 + `_group` 접미사만 사용:

```
그룹: arm_group        (접두사 없음)
레이어: fxt_arm_upper_01 (접두사 있음)
```

---

## 5. 접미사(Suffix) 시스템

### 좌우 구분

| 접미사 | 의미 | 예시 |
|--------|------|------|
| `_R` | 오른쪽 (대문자) | `fxt_ch_arm_01_R` |
| `_L` | 왼쪽 (대문자) | `fxt_ch_arm_01_L` |

좌우 접미사는 항상 **마지막**에 위치한다: `{prefix}_{noun}_{variant}_{index}_{Side}`

### 한글 좌우 인식 (자동 추출)

| 한글 패턴 | 추출 결과 | 예시 |
|-----------|----------|------|
| `오른쪽{명사}` (접두) | side=R | 오른쪽다리 → `leg_R` |
| `왼쪽{명사}` (접두) | side=L | 왼쪽팔 → `arm_L` |
| `{명사}_우` (접미) | side=R | 리본끝_우 → `ribbon_end_R` |
| `{명사}_좌` (접미) | side=L | 리본끝_좌 → `ribbon_end_L` |

### 번호 인덱스

| 규칙 | 예시 |
|------|------|
| 최소 2자리 (zero-pad) | `_01`, `_02`, `_10` |
| 번호는 Side 앞에 위치 | `fxt_arm_01_R` |
| 같은 파츠 여럿일 때만 사용 | 손가락 1개 → `finger` (번호 없음) |

### 그룹 접미사

| 접미사 | 적용 | 예시 |
|--------|------|------|
| `_group` | Auto Rename 시 자동 | `ribbon_group`, `item_inner_group` |

---

## 6. 사전 분해 (Dictionary Decomposition)

### 동작 원리

숫자만 있는 레이어(`01`, `02`, ...)의 이름은 부모 그룹명을 기반으로 생성된다.
이때 한글 그룹명을 영어로 변환하는 과정에서 **사전 분해**를 먼저 시도한다.

```
한글 그룹명: "안쪽아이템"
     ↓ 사전에서 prefix 검색
prefix: "안쪽" → inner
remainder: "아이템" → item
     ↓ noun_modifier 순서로 조합
eng_base: "item_inner"
     ↓ 번호 추가
결과: item_inner_01, item_inner_02, ...
```

### 사전 분해 순서

1. **직접 매칭**: 전체 단어가 사전에 있으면 그대로 사용 (`리본` → `ribbon`)
2. **prefix+remainder 분해**: 사전의 긴 단어부터 prefix 매칭 시도
   - `"안쪽"(inner)` + `"아이템"(item)` → 매칭 성공
3. **LLM 폴백**: 사전 분해 실패 시 LLM에게 번역 요청

### noun_modifier 조합 규칙

사전 분해 결과에서 **어느 것이 명사이고 어느 것이 수식어인지** 판별:

| 분류 | 단어 목록 |
|------|----------|
| **수식어** (modifier) | upper, lower, front, back, left, right, inner, outer, open, closed, big, small, end |
| **명사** (noun) | 그 외 모든 단어 (item, box, lid, ribbon, arm, leg, ...) |

**조합 규칙**: `{noun}_{modifier}` (명사가 앞)

```
"안쪽"(inner=수식어) + "아이템"(item=명사) → item_inner
"열린"(open=수식어) + "뚜껑"(lid=명사) → lid_open
"선물"(gift=명사) + "상자"(box=명사) → gift_box (명사+명사는 순서 유지)
```

### 명사+명사 복합어

두 단어 모두 명사일 경우 **한글 어순 그대로** 유지:

```
"선물"(gift) + "상자"(box) → gift_box (한글 순서 유지)
"뚜껑"(lid) + "장식"(decoration) → lid_decoration
```

---

## 7. LLM 번역 프롬프트 규칙

Auto (KR→EN) 모드에서 LLM에게 전달하는 규칙:

### 의미 있는 한글 레이어

1. `(in: 그룹명)` 앞의 한글 단어를 번역
2. 위치/방향어(위/아래/앞/뒤/끝/왼/오른)나 숫자는 **그룹명을 noun으로 사용**
   - `위 (in: 팔)` → `arm_upper` (noun=arm, modifier=upper)
   - `끝오른쪽 (in: 리본)` → `ribbon_end_right`
   - `3 (in: 리본)` → `ribbon_03`
3. 자기 설명적 단어는 그룹 접두사 불필요
   - `그림자 (in: 상자)` → `shadow` (~~`box_shadow`~~)
   - `머리` → `head`

### 의미 없는 레이어 (숫자, "레이어 N")

1. 부모 그룹명을 영어로 번역 → base name
2. base name + 번호(zero-pad 2자리) → 최종 이름
   - 그룹 "안쪽아이템", 레이어 "01" → `item_inner_01`
   - 그룹 "리본", 레이어 "3" → `ribbon_03`

---

## 8. 전체 변환 예시

### 입력 (PSD)

```
선물상자/                          (depth 0)
├── 열린상자/                      (depth 1)
│   ├── 바깥쪽아이템/              (depth 2)
│   │   ├── 09
│   │   ├── 10
│   │   └── 11
│   ├── 안쪽아이템/                (depth 2)
│   │   ├── 01
│   │   ├── 02
│   │   └── ... 08
│   └── 뚜껑장식
├── 닫힌뚜껑/                      (depth 1)
│   ├── 리본/                      (depth 2)
│   │   ├── 끝오른쪽
│   │   ├── 끝왼쪽
│   │   └── 01 ... 05
│   └── 상자
└── 그림자
```

### 출력 (Auto Rename)

```
그룹 rename:
  선물상자        → gift_box_group
  열린상자        → box_open_group
  바깥쪽아이템    → item_outer_group
  안쪽아이템      → item_inner_group
  닫힌뚜껑        → lid_closed_group
  리본            → ribbon_group

레이어 rename (prefix: fxt_):
  09              → fxt_item_outer_09
  10              → fxt_item_outer_10
  11              → fxt_item_outer_11
  01              → fxt_item_inner_01
  02              → fxt_item_inner_02
  ...08           → fxt_item_inner_08
  뚜껑장식        → fxt_lid_decoration
  끝오른쪽        → fxt_ribbon_end_right
  끝왼쪽          → fxt_ribbon_end_left
  01...05         → fxt_ribbon_01 ... fxt_ribbon_05
  상자            → fxt_box
  그림자          → fxt_shadow
```

### 정렬 결과 (파일 탐색기)

```
fxt_box.png
fxt_item_inner_01.png
fxt_item_inner_02.png
...
fxt_item_inner_08.png
fxt_item_outer_09.png
fxt_item_outer_10.png
fxt_item_outer_11.png        ← item 계열 전부 인접
fxt_lid_decoration.png
fxt_ribbon_01.png
...
fxt_ribbon_05.png
fxt_ribbon_end_left.png
fxt_ribbon_end_right.png     ← ribbon 계열 전부 인접
fxt_shadow.png
```

---

## 9. 캐릭터 아바타 파츠 분리 — 정면 기준

### 9.1 좌우 기준 (L/R Convention)

**캐릭터 자신의 왼쪽/오른쪽** (해부학적 관점, Anatomical Convention)

```
        [화면]

   (뷰어 왼쪽)    (뷰어 오른쪽)
         ↓              ↓
       ┌──────────────────┐
       │     ┌────┐       │
       │     │얼굴│       │
       │     └────┘       │
       │   ┌──┐  ┌──┐    │
       │   │R │  │L │    │  ← 캐릭터의 오른팔(R) = 화면 왼쪽
       │   │팔│  │팔│    │  ← 캐릭터의 왼팔(L) = 화면 오른쪽
       │   └──┘  └──┘    │
       │   ┌──┐  ┌──┐    │
       │   │R │  │L │    │
       │   │다│  │다│    │
       │   │리│  │리│    │
       │   └──┘  └──┘    │
       └──────────────────┘
```

| 용어 | 의미 | 화면 위치 |
|------|------|----------|
| `_R` (Right) | 캐릭터의 **오른쪽** | 화면 **왼쪽** |
| `_L` (Left) | 캐릭터의 **왼쪽** | 화면 **오른쪽** |

이 규칙은 **모든 플랫폼에서 동일**:

| 플랫폼 | 형식 | 기준 |
|--------|------|------|
| Spine 2D | `_R` / `_L` (정면) | 캐릭터 기준 |
| Unity 2D | `_L` / `_R` | 캐릭터 기준 |
| Live2D | `_R` / `_L` | 캐릭터 기준 |
| Blender | `.L` / `.R` | 캐릭터 기준 |
| Maya | `L_` / `R_` prefix | 캐릭터 기준 |
| UE5 | `_l` / `_r` (소문자) | 캐릭터 기준 |

> **본 프로젝트**: `_R` / `_L` suffix, 대문자 (Spine/Unity 호환)

### 9.2 캐릭터 파츠 계층 구조

정면(front-facing) 아바타의 전체 파츠 트리:

```
캐릭터 (Root)
├── 머리 (head)
│   ├── 머리카락 (hair)
│   │   ├── 앞머리 (hair_front)
│   │   ├── 옆머리 (hair_side) ─── _R / _L
│   │   └── 뒷머리 (hair_back)
│   ├── 얼굴 (face)
│   │   ├── 눈썹 (eyebrow) ─────── _R / _L
│   │   ├── 눈 (eye) ───────────── _R / _L
│   │   │   ├── 속눈썹 (eyelash)
│   │   │   ├── 눈동자 (pupil)
│   │   │   └── 흰자 (sclera)
│   │   ├── 코 (nose)
│   │   ├── 입 (mouth)
│   │   │   └── 입술 (lip)
│   │   ├── 볼 (cheek) ─────────── _R / _L
│   │   └── 귀 (ear) ──────────── _R / _L
│   └── 목 (neck)
├── 몸통 (body/torso)
│   ├── 어깨 (shoulder) ────────── _R / _L
│   ├── 가슴 (chest)
│   └── 허리 (waist)
├── 팔 (arm) ───────────────────── _R / _L
│   ├── 윗팔 (arm_upper)
│   ├── 아랫팔 (arm_lower)
│   ├── 팔꿈치 (elbow)
│   ├── 손목 (wrist)
│   └── 손 (hand)
│       ├── 엄지 (thumb)
│       ├── 검지 (index_finger)
│       ├── 중지 (middle_finger)
│       ├── 약지 (ring_finger)
│       └── 소지 (pinky)
├── 다리 (leg) ─────────────────── _R / _L
│   ├── 윗다리 (leg_upper/thigh)
│   ├── 무릎 (knee)
│   ├── 아랫다리 (leg_lower/shin)
│   ├── 발목 (ankle)
│   └── 발 (foot)
│       └── 발가락 (toe)
└── 악세서리 (accessories)
    ├── 모자 (hat)
    ├── 안경 (glasses)
    ├── 장갑 (glove) ───────────── _R / _L
    └── 신발 (shoe) ────────────── _R / _L
```

### 9.3 PSD 레이어 순서 (뎁스/Draw Order)

PSD 레이어 스택에서 **위 = 앞에 그려짐 (카메라에 가까움)**:

```
[PSD 레이어 패널 — 위에서 아래로]

=== 가장 앞 (카메라 가까움) ===
앞머리                           ← 얼굴 위를 덮는 머리카락
  눈썹_R / 눈썹_L
  속눈썹_R / 속눈썹_L
  눈동자_R / 눈동자_L
  흰자_R / 흰자_L
  코
  입
  얼굴                           ← 얼굴 베이스
  귀_R / 귀_L
목
앞쪽팔 (화면 앞)                 ← ★ 몸통 앞의 팔
  손
  아랫팔
  윗팔
몸통                             ← 중앙
앞쪽다리 (화면 앞)               ← ★ 몸통 앞의 다리
  발
  아랫다리
  윗다리
뒤쪽다리 (화면 뒤)               ← ★ 몸통 뒤의 다리
  발
  아랫다리
  윗다리
뒤쪽팔 (화면 뒤)                 ← ★ 몸통 뒤의 팔
  손
  아랫팔
  윗팔
뒷머리                           ← 가장 뒤
=== 가장 뒤 (카메라 멀리) ===
```

### 9.4 앞/뒤 팔다리 — front/rear vs L/R

정면 캐릭터에서 팔다리의 앞/뒤 배치에 두 가지 접근법이 있다:

#### 방법 1: 고정 L/R (권장 — Unity/범용)

좌우를 L/R로 고정. 어느 팔이 앞인지는 **PSD 레이어 순서**로 결정.

```
PSD 그룹 구조:                    Export 이름:
팔_R/                             (그룹) arm_R_group
├── 손_R                          fxt_ch_hand_R
├── 아랫팔_R                      fxt_ch_arm_lower_R
└── 윗팔_R                        fxt_ch_arm_upper_R
...
팔_L/                             (그룹) arm_L_group
├── 손_L                          fxt_ch_hand_L
├── 아랫팔_L                      fxt_ch_arm_lower_L
└── 윗팔_L                        fxt_ch_arm_upper_L
```

**장점**: Unity에서 L/R 팔을 독립적으로 애니메이션 가능. 좌우 대칭 본 매핑 용이.
**적합**: Unity 2D Animation, 정면 UI 아바타, L/R 팔이 교차하지 않는 캐릭터.

#### 방법 2: front/rear (Spine 전통 방식)

앞/뒤 기준으로 네이밍. 3/4 뷰나 측면 뷰에서 유용.

```
PSD 그룹 구조:                    Export 이름:
앞쪽팔/                           (그룹) arm_front_group
├── 손_앞                         fxt_ch_hand_front
├── 아랫팔_앞                     fxt_ch_arm_lower_front
└── 윗팔_앞                       fxt_ch_arm_upper_front
...
뒤쪽팔/                           (그룹) arm_rear_group
├── 손_뒤                         fxt_ch_hand_rear
├── 아랫팔_뒤                     fxt_ch_arm_lower_rear
└── 윗팔_뒤                       fxt_ch_arm_upper_rear
```

**장점**: Spine 공식 예제(Spineboy)와 동일. 캐릭터 방향 전환 시 front/rear 유지.
**적합**: Spine 리깅, 측면/3-4뷰 캐릭터, 팔다리가 앞뒤로 교차하는 액션.

#### 선택 기준

| 상황 | 권장 | 이유 |
|------|------|------|
| Unity 정면 아바타 | **L/R** | 좌우 대칭, 본 미러링 |
| Spine 정면 아바타 | **L/R** | Spine도 정면에서는 L/R 사용 |
| Spine 측면 캐릭터 | **front/rear** | 공식 Spineboy 예제 패턴 |
| 방향 전환 있는 캐릭터 | **front/rear** | 방향 바뀌어도 앞/뒤 의미 유지 |

### 9.5 남성/여성 차이

#### 공통 파츠 (남녀 동일)

머리, 눈, 코, 입, 귀, 목, 어깨, 팔, 손, 다리, 발 — 계층 구조 동일.

#### 여성 추가 파츠

| 파츠 | 한글 | 영문 | L/R | 비고 |
|------|------|------|-----|------|
| 가슴 | 가슴 | breast | _R / _L | 피직스 애니메이션용 분리 |
| 치마 | 치마 | skirt | — | 앞/뒤/좌/우 4분할 가능 |
| 치마 앞 | 치마앞 | skirt_front | — | 스프링 본/피직스용 |
| 치마 뒤 | 치마뒤 | skirt_back | — | |
| 치마 좌 | 치마좌 | skirt_L | _L | |
| 치마 우 | 치마우 | skirt_R | _R | |
| 리본/장식 | 리본 | ribbon | — | 머리/의상 장식 |
| 긴 머리카락 | 긴머리 | hair_long | — | 피직스 다수 레이어 필요 |
| 포니테일 | 포니테일 | ponytail | — | 별도 스프링 본 |
| 카라 | 카라 | collar | — | 의상 목 장식 |

#### 남성 추가 파츠

| 파츠 | 한글 | 영문 | 비고 |
|------|------|------|------|
| 수염 | 수염 | beard | 얼굴 그룹 내 |
| 콧수염 | 콧수염 | mustache | 얼굴 그룹 내 |
| 넥타이 | 넥타이 | necktie | 몸통 앞 |

### 9.6 PSD 구조 예시 — 정면 여성 아바타 (한글 모드)

```
260305_FX_Ani_Baduk_GirlAvatar_v1.psd

[PSD 레이어 순서: 위→앞, 아래→뒤]

앞머리
  앞머리01
  앞머리02
옆머리_R                         ← 캐릭터 오른쪽 (화면 왼쪽)
옆머리_L                         ← 캐릭터 왼쪽 (화면 오른쪽)
눈_R/
  속눈썹_R
  눈동자_R
  흰자_R
눈_L/
  속눈썹_L
  눈동자_L
  흰자_L
눈썹_R
눈썹_L
코
입/
  윗입술
  아랫입술
  이
얼굴
귀_R
귀_L
목
팔_R/                            ← 화면 앞 팔 (레이어 순서로 앞)
  손_R
  아랫팔_R
  윗팔_R
  어깨_R
가슴                             ← 또는 가슴_R / 가슴_L (피직스 시)
몸통
팔_L/                            ← 화면 뒤 팔 (레이어 순서로 뒤)
  손_L
  아랫팔_L
  윗팔_L
  어깨_L
치마/
  치마앞
  치마_R
  치마_L
  치마뒤
다리_R/
  발_R
  아랫다리_R
  윗다리_R
다리_L/
  발_L
  아랫다리_L
  윗다리_L
뒷머리
  뒷머리01
  포니테일
```

### 9.7 Export 결과 예시 (Auto Rename)

위 PSD에 Auto Rename (prefix: `fxt_ch_`) 적용 시:

```
그룹 rename:
  눈_R            → eye_R_group
  눈_L            → eye_L_group
  입              → mouth_group
  팔_R            → arm_R_group
  팔_L            → arm_L_group
  치마            → skirt_group
  다리_R          → leg_R_group
  다리_L          → leg_L_group

레이어 rename:
  앞머리01        → fxt_ch_hair_front_01
  앞머리02        → fxt_ch_hair_front_02
  옆머리_R        → fxt_ch_hair_side_R
  옆머리_L        → fxt_ch_hair_side_L
  속눈썹_R        → fxt_ch_eyelash_R
  눈동자_R        → fxt_ch_pupil_R
  흰자_R          → fxt_ch_sclera_R
  속눈썹_L        → fxt_ch_eyelash_L
  눈동자_L        → fxt_ch_pupil_L
  흰자_L          → fxt_ch_sclera_L
  눈썹_R          → fxt_ch_eyebrow_R
  눈썹_L          → fxt_ch_eyebrow_L
  코              → fxt_ch_nose
  윗입술          → fxt_ch_lip_upper
  아랫입술        → fxt_ch_lip_lower
  이              → fxt_ch_teeth
  얼굴            → fxt_ch_face
  귀_R            → fxt_ch_ear_R
  귀_L            → fxt_ch_ear_L
  목              → fxt_ch_neck
  손_R            → fxt_ch_hand_R
  아랫팔_R        → fxt_ch_arm_lower_R
  윗팔_R          → fxt_ch_arm_upper_R
  어깨_R          → fxt_ch_shoulder_R
  가슴            → fxt_ch_chest
  몸통            → fxt_ch_body
  손_L            → fxt_ch_hand_L
  아랫팔_L        → fxt_ch_arm_lower_L
  윗팔_L          → fxt_ch_arm_upper_L
  어깨_L          → fxt_ch_shoulder_L
  치마앞          → fxt_ch_skirt_front
  치마_R          → fxt_ch_skirt_R
  치마_L          → fxt_ch_skirt_L
  치마뒤          → fxt_ch_skirt_back
  발_R            → fxt_ch_foot_R
  아랫다리_R      → fxt_ch_leg_lower_R
  윗다리_R        → fxt_ch_leg_upper_R
  발_L            → fxt_ch_foot_L
  아랫다리_L      → fxt_ch_leg_lower_L
  윗다리_L        → fxt_ch_leg_upper_L
  뒷머리01        → fxt_ch_hair_back_01
  포니테일        → fxt_ch_ponytail

파일 정렬 (탐색기):
  fxt_ch_arm_lower_L.png
  fxt_ch_arm_lower_R.png
  fxt_ch_arm_upper_L.png
  fxt_ch_arm_upper_R.png     ← arm 계열 인접
  fxt_ch_body.png
  fxt_ch_chest.png
  fxt_ch_ear_L.png
  fxt_ch_ear_R.png           ← ear 계열 인접
  fxt_ch_eyelash_L.png
  fxt_ch_eyelash_R.png       ← eye 계열 인접
  fxt_ch_eyebrow_L.png
  fxt_ch_eyebrow_R.png
  ...
  fxt_ch_hair_back_01.png
  fxt_ch_hair_front_01.png
  fxt_ch_hair_front_02.png
  fxt_ch_hair_side_L.png
  fxt_ch_hair_side_R.png     ← hair 계열 인접
  ...
```

### 9.8 네이밍 형식 — 최종 구조

```
{prefix}_{noun}_{segment}_{index}_{Side}
```

| 필드 | 필수 | 설명 | 예시 |
|------|------|------|------|
| `{prefix}` | ✓ | 프로젝트 접두사 | `fxt_ch_` |
| `{noun}` | ✓ | 파츠 명사 | `arm`, `leg`, `hair`, `eye` |
| `{segment}` | 선택 | 부위/상태 | `upper`, `lower`, `front`, `side` |
| `{index}` | 선택 | 번호 (2자리) | `_01`, `_02` |
| `{Side}` | 선택 | 좌우 (대문자) | `_R`, `_L` |

**순서 규칙**: noun → segment → index → Side (항상 Side가 마지막)

```
fxt_ch_arm_upper_01_R
       │    │      │  │
       │    │      │  └── Side (캐릭터 오른쪽)
       │    │      └───── Index (번호)
       │    └──────────── Segment (윗팔)
       └───────────────── Noun (팔)
```

### 9.9 사전에 추가 필요한 단어

Auto Rename이 정확히 동작하려면 아래 한글이 사전에 등록되어야 한다:

| 한글 | 영문 | 분류 |
|------|------|------|
| 이 | teeth | 명사 |
| 윗입술 | lip_upper | 복합명사 |
| 아랫입술 | lip_lower | 복합명사 |
| 포니테일 | ponytail | 명사 |
| 치마 | skirt | 명사 |
| 수염 | beard | 명사 |
| 콧수염 | mustache | 명사 |
| 넥타이 | necktie | 명사 |
| 카라 | collar | 명사 |
| 가슴 (여성) | breast | 명사 |

---

## 10. 판별 매트릭스 (Quick Reference)

### 단어 순서 판별

| 질문 | 답변 | 순서 | 예시 |
|------|------|------|------|
| 명사 + 위치/방향? | "어떤 것의 어디?" | `noun_modifier` | `arm_upper`, `ribbon_end` |
| 명사 + 상태? | "어떤 상태의 것?" | `noun_modifier` | `lid_closed`, `box_open` |
| 명사 + 크기/속성? | "어떤 종류의 것?" | `noun_modifier` | `stone_big`, `box_small` |
| 명사 + 명사? | 복합 명사 | 한글 순서 유지 | `gift_box`, `lid_decoration` |

### 접두사 판별

| 대상 | 접두사 | 접미사 |
|------|--------|--------|
| 아트 레이어 | `fxt_` (사용자 설정) | `_01`, `_R` |
| 그룹 헤더 | 없음 | `_group` |
| Unity UGUI/NGUI | `s_` (자동 변환) | — |
| Unity MeshQuad | `fxs_` (자동 변환) | — |

### Auto Rename 변환 흐름

```
레이어명 입력
  ↓
0. 의미 없는 이름? ("01", "레이어 1") → 그룹 컨텍스트 기반 추론
  ↓
1. 한글 포함? → NO → 영어 이름 → prefix 추가 후 반환
  ↓ YES
2. 사전 직접 매칭? → 영문 반환
3. 복합어 분리 (공백)? → 사전 개별 매칭 → noun_modifier 조합
4. 사전 분해 (prefix+remainder)? → noun_modifier 조합
5. LLM 번역 (그룹 컨텍스트 포함) → noun_modifier 반환
  ↓
prefix + eng + index + Side
```

### 입력 언어별 처리 상세

| 입력 | 한글 감지 | 처리 경로 | prefix 적용 | 결과 |
|------|----------|----------|------------|------|
| `머리` | ✓ | 사전 → "head" | ✓ | `fxt_head` |
| `끝오른쪽` | ✓ | 파싱 → LLM → "ribbon_end" + side=R | ✓ | `fxt_ribbon_end_R` |
| `열린 뚜껑` | ✓ | 복합어 분리 → "lid_open" | ✓ | `fxt_lid_open` |
| `ribbon_01` | ✗ | 영어 → 원본 유지 | ✓ | `fxt_ribbon_01` |
| `shadow` | ✗ | 영어 → 원본 유지 | ✓ | `fxt_shadow` |
| `01` (in 리본) | - | 의미없음 → 그룹 추론 | ✓ | `fxt_ribbon_01` |
| `리본end` | ✓ | LLM 번역 (불안정) | ✓ | `fxt_ribbon_end` (불보장) |

---

## 부록: 사전 등록 단어 목록

### 바디파츠 (55개)
```
머리=head, 머리카락=hair, 앞머리=hair_front, 옆머리=hair_side, 뒷머리=hair_back,
얼굴=face, 눈=eye, 눈썹=eyebrow, 속눈썹=eyelash, 눈동자=pupil, 흰자=sclera,
코=nose, 입=mouth, 입술=lip, 이=teeth, 윗입술=lip_upper, 아랫입술=lip_lower,
턱=jaw, 귀=ear, 볼=cheek, 이마=forehead, 다크써클=eye_shadow, 귀그림자=ear_shadow,
몸통=torso, 몸=body, 상체=torso_upper, 하체=torso_lower, 가슴=chest, 배=belly,
등=back, 어깨=shoulder, 목=neck, 엉덩이=hip, 허리=waist,
팔=arm, 윗팔=arm_upper, 아랫팔=arm_lower, 팔꿈치=elbow,
손=hand, 손가락=finger, 손목=wrist, 엄지=thumb, 검지=index, 중지=middle,
약지=ring, 소지=pinky, 주먹=fist, 손그림자=hand_shadow,
다리=leg, 윗다리=leg_upper, 허벅지=thigh, 아랫다리=leg_lower, 종아리=shin, 무릎=knee,
발=foot, 발가락=toe, 발목=ankle, 꼬리=tail, 날개=wing, 뿔=horn
```

### 의상/악세서리 (10개)
```
치마=skirt, 포니테일=ponytail, 수염=beard, 콧수염=mustache,
넥타이=necktie, 카라=collar,
앞쪽팔=arm_front, 뒤쪽팔=arm_rear, 앞쪽다리=leg_front, 뒤쪽다리=leg_rear
```

### 일반 오브젝트 (31개)
```
그림자=shadow, 스크린=screen, 이펙트=effect, 무기=weapon, 방패=shield,
망토=cape, 모자=hat, 안경=glasses, 장갑=glove, 신발=shoe, 벨트=belt, 갑옷=armor,
뚜껑=lid, 상자=box, 리본=ribbon, 열쇠=key, 자물쇠=lock, 문=door,
창문=window, 기둥=pillar, 바닥=floor, 천장=ceiling, 지붕=roof, 벽=wall,
배경=background, 구름=cloud, 나무=tree, 꽃=flower, 풀=grass, 돌=stone,
물=water, 불=fire, 빛=light, 연기=smoke, 먼지=dust, 폭발=explosion,
별=star, 달=moon, 해=sun,
아이템=item, 선물=gift, 포장=wrapping, 장식=decoration, 보석=gem, 조각=piece
```

### 수식어 (21개)
```
열린=open, 닫힌=closed, 큰=big, 작은=small,
위=upper, 아래=lower, 앞=front, 뒤=back, 왼=left, 오른=right, 안=inner, 밖=outer,
안쪽=inner, 바깥쪽=outer, 위쪽=upper, 아래쪽=lower,
왼쪽=left, 오른쪽=right, 앞쪽=front, 뒤쪽=back,
끝=end
```
