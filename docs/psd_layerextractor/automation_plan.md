# PSD Layer Exporter — 자동화 기획서

> 작성: 2026-02-28 (Phase 23 기준)
> 상태: 기획 단계 (구현 전)

---

## 1. 현재 워크플로우 (수동)

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Photoshop   │────▶│  PSD Extractor   │────▶│     Unity       │
│              │     │  (Qt GUI)        │     │                 │
│ 1. 레이어 정리│     │ 2. PSD 로드      │     │ 5. Sprite 설정  │
│    그룹 구성  │     │ 3. Rename/설정   │     │ 6. Atlas 생성   │
│    파일 저장  │     │ 4. Export 클릭   │     │ 7. Import Scene │
└─────────────┘     └──────────────────┘     └─────────────────┘
     수동               수동 (5~10분)              수동 (3단계)
```

### 각 단계별 상세

| 단계 | 작업 | 소요 시간 | 반복 빈도 |
|------|------|-----------|-----------|
| PS → PSD 저장 | 레이어 정리, 그룹 구성, 파일 저장 | 10~30분 | 초기 1회 + 수정마다 |
| PSD 로드 | 앱 실행 → Browse → PSD 선택 | 10초 | PSD 변경마다 |
| Rename 설정 | Mode 선택, Auto/Manual rename | 1~5분 | 초기 1회 |
| Export 설정 | Format, Padding, POT, Unity, Pivot 등 | 1~2분 | 초기 1회 |
| Export 실행 | EXPORT 버튼 클릭 | 자동 (수초) | 변경마다 |
| Unity Sprite 설정 | Setup Textures 클릭 | 수초 | Export마다 |
| Unity Atlas 생성 | NGUI Atlas Maker에서 생성 | 수동 | Export마다 |
| Unity Import Scene | Import to Scene 클릭 | 수초 | Export마다 |

**문제점:**
- PSD 수정 → 저장 → 앱 전환 → Export 클릭 → Unity 전환 → 3단계 클릭 반복
- 동일 PSD의 반복 Export에서 매번 동일한 수동 작업
- 4개 프로젝트(포커 PC/모바일, 바둑 PC/모바일) × 다수 PSD 파일 관리

---

## 2. 자동화 목표

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Photoshop   │────▶│  PSD Extractor   │────▶│     Unity       │
│              │     │  (Qt GUI)        │     │                 │
│ 1. 레이어 정리│     │ ✅ 자동 감지      │     │ ✅ 자동 Sprite  │
│    파일 저장  │     │ ✅ 세션 복원      │     │ ✅ Import All   │
│   (Ctrl+S)   │     │ ✅ 자동 Export   │     │    1클릭 완료   │
└─────────────┘     └──────────────────┘     └─────────────────┘
     수동               자동화                    반자동 (1클릭)
```

### 자동화 범위 정의

| 기능 | 자동화 가능 여부 | 비고 |
|------|:---:|------|
| PSD 레이어 정리 | ❌ | 창작 작업, 자동화 불가 |
| PSD 변경 감지 | ✅ | QFileSystemWatcher 이미 구현 |
| 세션 설정 복원 | ✅ | Phase 23에서 자동 로드 구현 완료 |
| Rename (기존 세션) | ✅ | 세션 복원으로 자동 적용 |
| Rename (새 PSD) | ❌ | 사용자 초기 설정 필수 |
| Export 자동 실행 | 🔧 | PSD 변경 감지 → 자동 Export (계획) |
| 프로젝트별 경로 | 🔧 | 프로젝트 프리셋 시스템 (계획) |
| Unity Sprite 설정 | 🔧 | AssetPostprocessor (계획) |
| Unity Atlas 생성 | 🔧 | NGUI API 호출 (계획) |
| Unity Import Scene | 🔧 | Import All 버튼 (계획) |

✅ = 구현 완료, 🔧 = 계획 중, ❌ = 자동화 불가

---

## 3. 자동화 기능 상세 설계

### 3.1 Auto Export (PSD 변경 → 자동 Export)

**개요:** Photoshop에서 PSD를 저장하면 PSD Extractor가 자동으로 감지하여 Export까지 진행

**전제 조건:**
- PSD Extractor 앱이 실행 중이어야 함
- 해당 PSD의 세션 파일(.session.json)이 존재해야 함 (최소 1회 수동 설정 필요)

**동작 흐름:**
```
PS에서 Ctrl+S
    ↓
QFileSystemWatcher 감지 (이미 구현, 300ms 딜레이)
    ↓
PSD 자동 Reload (이미 구현)
    ↓
세션 자동 복원 (Phase 23 구현 완료)
    ↓
[NEW] 자동 Export 실행
    ↓
Export 완료 → 로그 표시
```

**구현 계획:**
- `_on_file_changed()` 핸들러에 Auto Export 옵션 추가
- Settings 또는 Export 패널에 "Auto Export on Change" 체크박스
- 세션 파일 없는 경우 → 로그 경고 + Export 건너뜀
- Export 진행 중 재변경 → 큐잉 또는 무시 (디바운스)
- 세션에 Auto Export 설정 저장

**예상 UI:**
```
[☐ Auto Export] ← Export 패널 또는 Settings에 배치
```

**우선순위:** ⭐⭐⭐ 높음 (가장 적은 노력으로 가장 큰 효과)

---

### 3.2 프로젝트 프리셋 시스템

**개요:** 여러 프로젝트의 Export 경로와 설정을 미리 저장해두고 콤보박스로 전환

**사용자 프로젝트 예시:**
| 프로젝트 | 타입 | Unity 경로 (예시) |
|----------|------|-------------------|
| 포커 PC | NGUI | `D:\Projects\Poker\PC\Assets\Resources\UI\` |
| 포커 모바일 | UGUI | `D:\Projects\Poker\Mobile\Assets\Resources\UI\` |
| 바둑 PC | NGUI | `D:\Projects\Baduk\PC\Assets\Resources\UI\` |
| 바둑 모바일 | UGUI | `D:\Projects\Baduk\Mobile\Assets\Resources\UI\` |

**프로젝트별 저장 설정:**
```python
{
    "name": "포커 PC",           # 사용자 편집 가능
    "output_path": "D:\\...",    # Browse로 지정, 직접 편집 가능
    "unity_type": "NGUI",       # UGUI / NGUI
    "pivot": "Bottom-Center",   # 9방향
    "scales": [1.0],            # 배율 목록
    # 필요 시 추가: format, padding, pot 등
}
```

**UI 설계:**
```
┌─ Output ──────────────────────────────────────────────────┐
│ Project [포커 PC    ▼] [+] [-] [✎]                       │
│ Path    [D:\Projects\Poker\PC\Assets\...] [Browse] [Open] │
│ [☐ Unity] [UGUI|NGUI] │ Pivot [Bottom-Center▼]  [EXPORT] │
└───────────────────────────────────────────────────────────┘
```

**위젯 설명:**
- `Project` 콤보: 저장된 프로젝트 목록 (편집 불가 콤보)
- `[+]` 버튼: 새 프로젝트 추가 (이름 입력 다이얼로그)
- `[-]` 버튼: 현재 프로젝트 삭제 (확인 다이얼로그)
- `[✎]` 버튼: 프로젝트 이름 변경 (인라인 편집 또는 다이얼로그)
- Project 전환 시 → 경로 + Unity 타입 + Pivot 자동 전환

**저장 위치:** QSettings("PSDExtractor", "Qt") → projects 키
- 세션(per-PSD)이 아닌 앱 전역 설정으로 저장
- PSD마다 마지막 사용한 프로젝트 기억 (세션에 project_name 저장)

**동작 흐름:**
```
프로젝트 콤보 전환
    ↓
output_path 업데이트 → 경로 표시 갱신
Unity 타입 전환 (UGUI/NGUI)
Pivot 전환
    ↓
Export 시 해당 프로젝트 경로로 파일 생성
```

**우선순위:** ⭐⭐⭐ 높음 (다중 프로젝트 운영 시 필수)

---

### 3.3 Unity Import All (1클릭 Import)

**개요:** NGUI의 3단계 수동 작업을 "Import All" 버튼 1클릭으로 자동 실행

**현재 NGUI 워크플로우 (3단계):**
```
1. Setup Textures  → Sprite 설정 (TextureType, MeshType 등)
2. Make Atlas      → NGUI Atlas Maker로 Atlas 생성
3. Import to Scene → 하이어라키에 UISprite + 위치 배치
```

**현재 UGUI 워크플로우 (2단계):**
```
1. Setup Sprites   → Sprite 설정
2. Import to Scene → Canvas + Image + RectTransform 배치
```

**자동화 설계:**

Unity C# EditorWindow에 "Import All" 버튼 추가:

```csharp
// NGUI Import All 흐름
if (GUILayout.Button("Import All"))
{
    // Step 1: Setup Textures
    SetupTextures();
    AssetDatabase.Refresh();

    // Step 2: Make Atlas (NGUI API 호출)
    // NGUIEditorTools.MakeAtlas() 또는 커스텀 래핑
    MakeAtlas();
    AssetDatabase.Refresh();

    // Step 3: Import to Scene
    ImportToScene();
}
```

**고려사항:**
- 각 단계 완료 후 `AssetDatabase.Refresh()` 필요
- Atlas 생성은 NGUI의 내부 API 의존 → 버전별 호환성 확인 필요
- UGUI는 2단계이므로 "Import All" = Setup + Import
- 기존 개별 버튼은 유지 (디버깅/부분 실행용)

**UI 변경:**
```
기존:  [Setup Textures] [Make Atlas] [Import to Scene]
추가:  [Setup Textures] [Make Atlas] [Import to Scene] [Import All]
```

**우선순위:** ⭐⭐ 중간 (편의성 개선, 핵심 기능은 아님)

---

### 3.4 Unity AssetPostprocessor (자동 Sprite 설정)

**개요:** PSD Extractor에서 Export된 PNG가 Unity 프로젝트에 생성되면 자동으로 Sprite 설정 적용

**현재 수동 작업:**
- Setup Textures/Sprites 클릭 → TextureImporter 설정:
  - TextureType = Sprite
  - MeshType = FullRect
  - GeneratePhysicsShape = false
  - mipmapEnabled = false
  - Compression = Uncompressed

**AssetPostprocessor 구현:**
```csharp
public class FXC_PSDSpritePostprocessor : AssetPostprocessor
{
    void OnPreprocessTexture()
    {
        // Export 폴더 내 파일인지 경로로 판별
        if (!assetPath.Contains("Resources/UI/")) return;

        TextureImporter importer = (TextureImporter)assetImporter;
        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Single;
        importer.mipmapEnabled = false;
        // ...
    }
}
```

**장점:**
- Export → Unity 폴더에 파일 생성 → 자동 Sprite 설정 (Setup Textures 단계 제거)
- Import All에서 1단계 생략 가능

**단점:**
- Unity 프로젝트에 스크립트 배치 필요 (Editor 폴더)
- 경로 기반 판별 → 잘못된 폴더의 이미지도 영향받을 수 있음
- 프로젝트별 설정이 다를 수 있음

**우선순위:** ⭐ 낮음 (Import All로 충분히 커버됨)

---

### 3.5 CLI Watch 모드 (헤드리스 자동 Export)

**개요:** GUI 없이 CLI에서 PSD 파일 감시 + 자동 Export

**사용 시나리오:**
- GUI 앱을 실행하지 않고도 PSD 저장 시 자동 Export
- 서버/CI 환경에서 배치 처리
- 여러 PSD를 동시에 감시

**구현 개념:**
```bash
python psd_extractor.py --watch "D:\Art\*.psd" --session auto
```

**동작:**
```
watchdog 라이브러리로 파일 감시
    ↓
PSD 변경 감지
    ↓
.session.json 로드 (설정 복원)
    ↓
Export 실행 (CLI 모드)
    ↓
계속 감시...
```

**필요 라이브러리:** `watchdog` (pip install watchdog)

**우선순위:** ⭐ 낮음 (GUI 기반 Auto Export로 대부분 커버)

---

## 4. 자동화 적용 후 워크플로우

### 4.1 기존 PSD (세션 있음) — 완전 자동

```
Photoshop에서 Ctrl+S
    ↓ (QFileSystemWatcher 자동 감지)
PSD Extractor 자동 Reload
    ↓ (세션 자동 복원)
설정 자동 적용 (Rename, POT, Format 등)
    ↓ (Auto Export ON)
프로젝트 경로로 자동 Export
    ↓ (AssetPostprocessor 또는 Import All)
Unity에서 Import All 1클릭
```

**사용자 개입:** PS에서 Ctrl+S + Unity에서 Import All 클릭 (2 액션)

### 4.2 새 PSD (세션 없음) — 초기 설정 필요

```
PSD Extractor에서 Browse → PSD 선택
    ↓
Rename 모드 선택 + 이름 설정 (수동)
    ↓
Export 설정 (Format, Padding, POT 등) (수동)
    ↓
프로젝트 선택 (콤보) → 경로 자동 설정
    ↓
EXPORT 클릭 (수동)
    ↓
세션 자동 저장 (.session.json)
    ↓
이후부터는 4.1 자동 흐름 적용
```

**핵심:** 새 PSD는 1회 수동 설정이 필수. 이후 동일 PSD의 반복 Export는 완전 자동.

---

## 5. 구현 우선순위 및 로드맵

| 순서 | 기능 | 난이도 | 효과 | 의존성 |
|:---:|------|:---:|:---:|--------|
| 1 | Auto Export on PSD Change | 낮음 | ⭐⭐⭐ | 세션 자동 로드 (완료) |
| 2 | 프로젝트 프리셋 시스템 | 중간 | ⭐⭐⭐ | 없음 |
| 3 | Unity Import All 버튼 | 낮음 | ⭐⭐ | C# 템플릿 수정 |
| 4 | AssetPostprocessor | 낮음 | ⭐ | 프로젝트 프리셋 |
| 5 | CLI Watch 모드 | 중간 | ⭐ | psd_extractor.py 확장 |

### Phase 24 (자동화 1차) — 완료 ✅

**목표:** Auto Export + 프로젝트 프리셋 + NGUI Import All

| # | 작업 | 설명 | 상태 |
|---|------|------|:---:|
| 1 | Auto Export 체크박스 | Export 패널에 배치, 세션 저장 | ✅ |
| 2 | Auto Export 로직 | `_do_refresh()` → 세션 복원 후 자동 Export | ✅ |
| 3 | 프로젝트 프리셋 UI | 콤보(150px) + ✎ 매니저 다이얼로그 | ✅ |
| 4 | 프로젝트 프리셋 저장 | QSettings 영속화 (name + path) | ✅ |
| 5 | 프로젝트 전환 로직 | 경로 자동 전환 (프로젝트경로/PSD명) | ✅ |
| 6 | 세션에 프로젝트 연결 | PSD별 project_name + auto_export 저장 | ✅ |
| 7 | NGUI Import All | Setup + Atlas + Import 3단계 1클릭 | ✅ |
| 8 | 다크 테마 다이얼로그 | _DARK_DIALOG_SS 재사용 스타일시트 | ✅ |
| 9 | C# 클래스명 충돌 수정 | output dir 기반 _cls_suffix | ✅ |
| 10 | Auto Export 경로 버그 | _apply_project_path() 항상 호출 | ✅ |

### Phase 25 (자동화 2차) — 예정

**목표:** UGUI Import All + AssetPostprocessor

| # | 작업 | 설명 |
|---|------|------|
| 1 | UGUI Import All | Setup Sprites + Import to Scene 통합 |
| 2 | AssetPostprocessor 템플릿 | Export 시 함께 생성 (선택) |

---

## 6. 기술 검토 노트

### 6.1 QFileSystemWatcher 동작

현재 구현 (`psd_extractor_gui_qt.py`):
- `QFileSystemWatcher.fileChanged` 시그널로 PSD 변경 감지
- 300ms `QTimer.singleShot` 딜레이 (Photoshop의 원자적 쓰기 대응)
- 자동 reload: `_reload_psd()` → `set_layers()` → 세션 자동 복원

Auto Export 추가 시:
- `_on_file_changed()` 끝에 Auto Export 조건부 실행
- `_load_psd()` 완료 후 Export 트리거 (세션 복원 후)
- Export 진행 중 재변경 방지: `_exporting` 플래그 체크

### 6.2 프로젝트 프리셋 저장 구조

```python
# QSettings 저장 형태
{
    "projects": [
        {
            "name": "포커 PC",
            "path": "D:\\Projects\\Poker\\PC\\Assets\\Resources\\UI",
            "unity_type": "NGUI",
            "pivot": "Bottom-Center",
            "scales": [1.0]
        },
        {
            "name": "포커 모바일",
            "path": "D:\\Projects\\Poker\\Mobile\\Assets\\Resources\\UI",
            "unity_type": "UGUI",
            "pivot": "Bottom-Center",
            "scales": [1.0, 0.75]
        }
    ],
    "last_project": "포커 PC"
}
```

### 6.3 NGUI Atlas API 호환성

NGUI의 Atlas Maker API는 버전별로 다를 수 있음:
- `NGUIEditorTools` 클래스 존재 여부 확인 필요
- Atlas Maker 윈도우를 프로그래밍적으로 호출하는 방법 조사 필요
- 대안: `UIAtlasMaker.UpdateAtlas()` 직접 호출

### 6.4 세션 없는 PSD의 자동화 한계

세션 파일 없이 자동 Export가 불가능한 이유:
- Rename 규칙을 AI가 자동으로 결정할 수 없음 (프로젝트별 네이밍 컨벤션)
- POT 크기, Padding, Format 등은 용도에 따라 다름
- Export 경로 (프로젝트)를 모름

→ **결론:** 새 PSD는 반드시 1회 수동 설정이 필요. 프리셋 시스템으로 설정 시간을 최소화할 수 있음.

---

## 7. 개발 히스토리

### Phase 23 (완료) — 세션 자동화 기반

| 날짜 | 작업 | 상태 |
|------|------|:---:|
| 2026-02-28 | 세션 자동 저장/로드 (16개 설정 추가) | ✅ |
| 2026-02-28 | Save/Load 버튼 제거, Restore 유지 | ✅ |
| 2026-02-28 | PSD 로드 시 자동 세션 복원 | ✅ |
| 2026-02-28 | Layer 토글 버튼 (그룹만 표시) | ✅ |
| 2026-02-28 | Auto Ver 버전 없는 PSD 경로 처리 | ✅ |
| 2026-02-28 | 선택 슬롯 단축키 간소화 | ✅ |

### Phase 24 (완료) — 자동화 1차

| 작업 | 상태 |
|------|:---:|
| Auto Export on PSD Change | ✅ |
| 프로젝트 프리셋 시스템 (UI + 저장) | ✅ |
| 프로젝트별 경로 Export | ✅ |
| 세션-프로젝트 연결 | ✅ |
| NGUI Import All 버튼 | ✅ |
| 다크 테마 프로젝트 매니저 다이얼로그 | ✅ |
| Auto Export 경로 버그 수정 | ✅ |
| C# 클래스명 충돌 수정 (output dir 기반) | ✅ |

### Phase 25 (예정) — 자동화 2차

| 작업 | 상태 |
|------|:---:|
| UGUI Import All 버튼 | 📋 |
| AssetPostprocessor 자동 생성 | 📋 |

---

## 8. 참고: 검토했으나 채택하지 않은 방안

### Photoshop UXP 플러그인으로 직접 Export
- Photoshop 안에서 레이어를 직접 내보내는 UXP 플러그인
- **미채택 사유:**
  - PSD Extractor의 기존 기능(Rename, POT, 세션 등)을 모두 재구현해야 함
  - UXP API 제약 (QGraphicsView 수준의 프리뷰 불가)
  - 이미 psd-tools 기반으로 충분히 빠름 (PS COM 대비 41배)

### Unity에서 PSD 직접 Import
- Unity가 PSD를 직접 읽어서 레이어를 Sprite로 변환
- **미채택 사유:**
  - Unity 내장 PSD Import는 머지 이미지만 지원
  - 써드파티 에셋(2D PSD Importer 등)은 기능 제한적
  - Rename/POT/다중배율 등 커스텀 파이프라인 불가

### 전체 무인 자동화 (새 PSD 포함)
- AI가 레이어명을 분석하여 자동으로 Rename + 설정
- **미채택 사유:**
  - 프로젝트별 네이밍 컨벤션이 다름
  - 오류 시 수동 수정 비용이 초기 설정보다 큼
  - 세션 시스템으로 "1회 설정 → 이후 자동" 패턴이 충분
