# Unity UGUI Import — 개발 히스토리

이 문서는 PSD Layer Extractor의 Unity UGUI 내보내기/가져오기 기능의 개발 동기, 설계 결정, 변경 이력을 기록합니다.

---

## 왜 만들었나

### 동기

2D 게임 캐릭터 작업에서 PSD 레이어를 Unity UI(UGUI)로 옮기는 과정은 반복적이고 오류가 발생하기 쉽습니다:
- 포토샵에서 레이어를 개별 PNG로 추출
- Unity에 이미지 임포트 후 Sprite 설정
- 하나씩 Image 컴포넌트를 만들고 위치/크기를 수동 조정
- 그룹 계층 구조를 Unity Hierarchy에 수동 재현

레이어가 20개만 넘어도 이 수작업은 상당한 시간이 소요되며, PSD가 변경될 때마다 처음부터 다시 해야 합니다.

### 참고 자료: PhotoshopToSpine.jsx

[Esoteric Software의 PhotoshopToSpine 스크립트](https://github.com/EsotericSoftware/spine-scripts/tree/master/photoshop)에서 핵심 아이디어를 얻었습니다:
- PSD 레이어 → JSON 메타데이터 + 개별 이미지 내보내기
- 좌표 변환 (PSD top-left 원점 → Spine bottom-up 좌표계)
- 그룹 폴더를 뼈대(bone) 계층으로 매핑
- 태그 시스템 (`[bone]`, `[slot]`, `[skin]`) 으로 레이어에 역할 지정

PhotoshopToSpine이 PSD → Spine 워크플로우를 자동화한 것처럼,
이 도구는 **PSD → Unity UGUI 워크플로우**를 자동화합니다.

### Spine vs Unity UGUI 좌표 비교

| 항목 | PSD | Spine | Unity UGUI |
|------|-----|-------|------------|
| 원점 | top-left | center (bone) | anchor 기반 (top-left 사용) |
| Y축 | ↓ 아래로 증가 | ↑ 위로 증가 | ↑ 위로 증가 |
| 위치 기준 | layer.left, layer.top | 부모 bone 상대좌표 | anchoredPosition (anchor 상대) |
| 크기 | layer.width, height | attachment width/height | sizeDelta |

### 좌표 변환 공식 (PSD → Unity UGUI)

```
// v3 (pivot 적용)
anchor = (pivot_x, 1 - pivot_y)   -- 동적 (pivot 설정에 따라)
pivot  = (0.5, 0.5)               -- center (회전/스케일 친화적)

unity.x = layer.left + layer.width / 2 - canvas_width * pivot_x
unity.y = -(layer.top + layer.height / 2) + canvas_height * pivot_y
sizeDelta = (width, height)

// v2 이하 (pivot 미지원, Top-Left 기준)
anchor = (0, 1)   -- top-left
unity.x = layer.left + layer.width / 2
unity.y = -(layer.top + layer.height / 2)
```

Y축 반전이 핵심: PSD의 top이 작을수록 위쪽이지만, Unity에서는 Y가 클수록 위쪽이므로 부호를 반전합니다. v3부터 pivot 오프셋으로 좌표 원점을 사용자가 선택할 수 있습니다.

---

## 개발 이력

### v1 — EditorWindow 방식 (초기 구현)

**날짜**: 2025년

**구현 내용**:
- `psd_extractor.py`에 `collect_layer_metadata()` 함수 추가
- JSON 포맷 v1: canvas, groups, layers (위치/크기/가시성/투명도)
- `PSDImporter.cs` EditorWindow 스크립트 자동 생성 (v3.0에서 FXC_PSDImporter.cs로 통합됨)
- Unity 메뉴 Tools > PSD Layer Importer로 접근

**워크플로우**:
1. PSD Extractor Qt GUI에서 Unity 체크박스 ON → Export
2. `_unity_layout.json` + `PSDImporter.cs` + 레이어 이미지 생성
3. Unity 프로젝트에 복사
4. Tools > PSD Layer Importer 실행
5. "Setup Sprites in Folder" → 텍스처 임포트 설정 일괄 변환
6. "Import to Scene" → Canvas + 계층 구조 자동 생성

**한계**:
- EditorWindow 방식이라 매번 경로를 수동 지정해야 함
- Canvas를 자동 생성하여 사용자의 기존 UI 계층에 통합하기 어려움
- 동일 그룹명이 다른 깊이에 존재할 때 충돌 가능

### v2 — Component 방식 (2025-02-25)

**변경 동기**:
실제 작업에서 원하는 플로우는 더 단순합니다:
1. Hierarchy에서 빈 오브젝트 생성
2. 컴포넌트 추가 → JSON 드래그 → Build 클릭
3. 끝

EditorWindow는 별도 창을 열고 경로를 매번 입력해야 하는 번거로움이 있었습니다.

**구현 내용**:

1. **JSON 포맷 v2** (`psd_extractor.py`):
   - `blend_mode` 필드 추가 (그룹 + 레이어)
   - 그룹에 `group_path` 배열 추가 (동일 이름 그룹 충돌 방지)
   - `"version": 2`로 범프

2. **PSDLayoutBuilder.cs** (MonoBehaviour) — v3.0에서 제거됨:
   - 아무 GameObject에 붙이는 컴포넌트
   - `TextAsset` 필드로 JSON 드래그 앤 드롭
   - Sprite 폴더 자동 감지 (JSON과 같은 폴더)

3. **PSDLayoutBuilderEditor.cs** (Custom Editor) — v3.0에서 제거됨:
   - Inspector에 Build Layout / Clear Children 버튼
   - Setup Sprite Import Settings 버튼
   - Undo 지원 (Ctrl+Z로 되돌리기)
   - v1/v2 JSON 하위호환

4. **Python 템플릿 업데이트** (`psd_extractor_gui_qt.py`):
   - Export 시 C# 파일 3개 동시 출력 (v3.0에서 1개로 통합됨)

**JSON v2 예시**:
```json
{
  "version": 2,
  "psd_file": "ch.psd",
  "canvas": { "width": 210, "height": 283 },
  "groups": [
    {
      "name": "body",
      "depth": 0,
      "parent": null,
      "group_path": ["body"],
      "blend_mode": "PASS_THROUGH"
    }
  ],
  "layers": [
    {
      "name": "arm_R",
      "file": "arm_R.png",
      "psd_name": "오른팔",
      "group": "body",
      "group_path": ["body"],
      "visible": true,
      "opacity": 255,
      "blend_mode": "NORMAL",
      "rect": { "left": 50, "top": 100, "width": 40, "height": 60 },
      "unity": { "x": 70.0, "y": -130.0, "width": 40, "height": 60 },
      "order": 0
    }
  ]
}
```

---

## Unity 사용 가이드 (v3.0 통합 EditorWindow)

### 준비
1. PSD Extractor Qt GUI에서 **Unity 체크박스 ON** → Export
2. 출력 이미지 + `_unity_layout.json`을 Unity 프로젝트 `Assets/Sprites/캐릭터명/`에 복사
3. `FXC_PSDImporter.cs`를 `Assets/Editor/`에 복사

### 실행
1. Unity 메뉴 **Tools > FXC PSD Importer** 실행
2. **Browse** → `_unity_layout.json` 선택 (Sprite Folder 자동 감지)
3. **Setup Sprites** 클릭 (처음 1회, 텍스처 임포트 설정)
4. **Import to Scene** 클릭

### 결과
- Canvas + root GameObject 하위에 PSD 그룹 구조가 재현됨
- 각 레이어가 Image 컴포넌트를 가진 GameObject로 생성
- 위치/크기/투명도/가시성이 PSD 원본과 일치
- Ctrl+Z로 되돌리기 가능 (Undo 지원)

### 재임포트
PSD가 변경되었을 때:
1. PSD Extractor에서 다시 Export
2. 새 파일들을 Unity에 복사 (덮어쓰기)
3. FXC PSD Importer에서 **Import to Scene** 다시 클릭

### v2.1 — 버그 수정 및 기능 보강 (2025-02-25)

**발견된 문제** (box.psd 테스트 중):
- 동일 레이어명("뚜껑" × 2, "리본끝_우" × 2)이 같은 파일명으로 export → 두 번째 파일이 첫 번째를 덮어쓰기
- 한글 그룹명("보라상자", "열린 뚜껑 복사" 등)이 Unity JSON에 그대로 출력
- 원본 레이어명 중복 시 사전 경고가 없어 사용자가 모르고 export

**수정 내용**:

1. **파일명 충돌 방지 — 자동 접미사 (_1, _2)**
   - `collect_layer_metadata()`, `export_command()`, `ExportWorker.run()` 3곳에 `used_names` dict 추가
   - 동일 파일명 감지 시 `_1`, `_2` 접미사 자동 부여
   - 결과: `뚜껑.png`, `뚜껑_1.png` — 파일 손실 없음

2. **원본 레이어명 중복 경고**
   - `LayerListModel`에 `_orig_name_duplicates` 집합 + `is_orig_name_duplicate()` 메서드
   - `LayerDelegate.paint()`에서 중복 원본명을 주황색(`#e0a050`)으로 표시
   - rename 필드에 "⚠ duplicate name" 플레이스홀더

3. **그룹 리네임 지원**
   - `collect_layer_metadata()`에 `group_rename_map` 파라미터 추가
   - `_rename_group()`, `_rename_group_path()` 헬퍼로 JSON 내 그룹명 일괄 치환
   - GUI 트리 모드에서 그룹 헤더에 rename 입력란 표시 (클릭으로 직접 편집)
   - Auto (KR→EN) 모드에서 한글 그룹명도 Ollama로 자동 번역
   - 세션 저장 시 `group_rename` 필드 보존

4. **Shift+Click 동작 수정**
   - 범위 선택 시 체크박스가 함께 변경되던 버그 수정
   - 이제 하이라이트(선택)만 변경, 체크 상태는 유지

### v2.2 — 성능 최적화 (2025-02-25)

**발견된 문제**: PSD 로딩 속도가 v2.1 변경 후 눈에 띄게 느려짐

**원인 분석**:

1. **트리 가이드라인 O(n²) 스캔** — `paint()` 호출마다 현재 행에서 아래 전체 행을 순회하여 가이드라인 연속 여부 계산. 100개 레이어 × 20행 뷰포트 = 2000+ 번의 `model.data()` 호출
2. **_load_session() 중복 rebuild** — `_load_psd()`가 이미 `set_layers()` → `_rebuild_view()` + `_show_merged_preview()` 호출 후, `_load_session()`에서 `_rebuild_view()` + `_rebuild_merged()` + `_show_merged_preview()` 다시 호출
3. **그룹 번역 시 N회 rebuild** — `_on_translate_done()`에서 그룹마다 `set_group_rename()` → `_rebuild_view()` 반복 호출

**수정 내용**:

1. **트리 가이드 캐시**: `_compute_tree_guides()`에서 역순 1회 순회(O(n))로 모든 행의 `continuing_depths`를 `_tree_guide_cache`에 사전 계산. `paint()`에서는 캐시 조회만 수행(O(1))
2. **세션 로드 최적화**: `_rebuild_merged()` + `_show_merged_preview()` 제거 (이미 `_load_psd()`에서 실행됨). 세션 데이터 반영 후 `_rebuild_view()` 1회만 실행
3. **그룹 번역 일괄 적용**: `_group_rename_map`에 직접 할당 후 `_rebuild_view()` 1회만 호출

### v2.3 — 세션 수동 로드 + Restore 완전 복원 (2026-02-25)

**발견된 문제**:
1. v2.2 최적화 후에도 PSD 로딩이 여전히 느림. `_load_session()`에서 최대 3회 `_rebuild_view()` 호출
2. Restore 버튼이 레이어 순서(reverse)/트리 모드를 복원하지 않아 불완전 복원

**원인 분석**:
1. `_load_session()` 내 `_toggle_layer_order()`, `_tree_btn.setChecked()`, final rebuild가 각각 `_rebuild_view()` + UI 시그널을 발생
2. `_restore_initial_state()`가 체크/가시성/rename만 복원, 순서/트리 상태는 무시

**수정 내용**:

1. **세션 자동 로드 제거**: `_load_psd()` 끝에서 `_load_session()` 호출 제거. 세션 파일 존재 시 로그 알림만 표시. Settings에 Load 버튼 추가하여 수동 복원
2. **`_load_session()` 최적화**: 모든 상태를 시그널 차단 상태에서 먼저 적용한 뒤 `_rebuild_view()` 1회만 실행
   - `_tree_btn.blockSignals(True)` → `setChecked()` → `blockSignals(False)`
   - 레이어 역순: 배열 직접 reverse (`_toggle_layer_order()` 호출 안 함)
3. **Restore 완전 복원**: `_restore_initial_state()`에서 레이어 순서 리셋 + 트리 모드 해제 + `_rebuild_merged()` + `_show_merged_preview()` 호출

### v2.4 — 레이어/그룹 순서 수정 + 패딩 옵션 (2026-02-25)

**발견된 문제**: 포토샵에서 위(front)에 있는 레이어가 Unity UGUI에서 뒤(back)에 렌더링됨. 레이어 순서가 완전히 뒤집힘.

**원인 분석**:

| 시스템 | "앞(front)" 위치 |
|--------|------------------|
| **Photoshop** | 패널 **위** = 앞 |
| **psd-tools** | 이터레이션 순서 = PSD 패널 위→아래 (order 0 = front) |
| **Unity UGUI** | Hierarchy **마지막 sibling** = 앞 |

기존 C# 코드에서 `OrderBy(l => l.order)` (오름차순)으로 레이어를 생성:
- order 0 (PSD front) → 첫 번째 생성 → Unity sibling 0 → 뒤에 렌더링
- order N (PSD back) → 마지막 생성 → Unity 최후 sibling → 앞에 렌더링

**수정 내용**:

1. **레이어 정렬 반전** (C# 스크립트):
   ```csharp
   // Before
   var layersSorted = layout.layers.OrderBy(l => l.order).ToArray();
   // After
   var layersSorted = layout.layers.OrderByDescending(l => l.order).ToArray();
   ```

2. **그룹 order 필드 추가** (`psd_extractor.py`):
   - `collect_layer_metadata()`에서 그룹 수집 시 `"order": grp_order` 필드 추가
   - 이터레이션 순서(PSD front→back) 기반 순번

3. **그룹 정렬 보정** (C# 스크립트):
   ```csharp
   // Before
   var sorted = layout.groups.OrderBy(g => g.depth).ToArray();
   // After
   var sorted = layout.groups
       .OrderBy(g => g.depth)
       .ThenByDescending(g => g.order)
       .ToArray();
   ```
   depth 오름차순 (부모 먼저) + 같은 depth 내 order 내림차순 (PSD back→front 순 생성)

4. **GroupInfo 클래스 업데이트**:
   ```csharp
   public class GroupInfo {
       // ... 기존 필드 ...
       public int order;  // NEW
   }
   ```

5. **패딩 force_even 옵션**:
   - `apply_padding()`에 `force_even=True` 파라미터 추가
   - `collect_layer_metadata()`에도 `force_even` 파라미터 전달
   - UI에 Even 체크박스 추가 (체크 해제 시 홀수 크기 유지)

**결과**: PSD 최상단(front) 레이어가 Unity에서 마지막 sibling(front)으로, PSD 최하단(back) 레이어가 첫 sibling(back)으로 생성되어 포토샵과 동일한 시각적 순서.

**JSON v2 그룹 구조 변경**:
```json
{
  "name": "body",
  "depth": 0,
  "parent": null,
  "group_path": ["body"],
  "blend_mode": "PASS_THROUGH",
  "order": 0
}
```

### v3.0 — C# 스크립트 통합 (FXC_PSDImporter) (2026-02-25)

**변경 동기**:
- 기존 3개 C# 스크립트(PSDImporter, PSDLayoutBuilder, PSDLayoutBuilderEditor)가 중복 기능
- 팀 스크립트 네이밍 규칙 `FXC_` 접두사 적용 필요
- 파일 1개로 단순화하여 배포/관리 용이

**수정 내용**:

1. **C# 스크립트 3개 → 1개 통합**:
   - `FXC_PSDImporter.cs` (EditorWindow) 1개로 통합
   - PSDLayoutBuilderEditor의 group_path v2 로직을 EditorWindow에 병합
   - PSDLayoutBuilder(MonoBehaviour) + PSDLayoutBuilderEditor(Custom Editor) 제거

2. **통합 기능**:
   - `Tools > FXC PSD Importer` 메뉴
   - JSON Browse + Sprite Folder 자동 감지
   - Setup Sprites / Import to Scene 버튼
   - group_path v2 지원 (동일 그룹명 충돌 방지)
   - Undo 지원 (모든 생성 객체)
   - Scale Factor, Create Canvas 옵션

3. **Python 템플릿 업데이트**:
   - `_UNITY_IMPORTER_CS` 1개만 유지
   - `_UNITY_LAYOUT_BUILDER_CS`, `_UNITY_LAYOUT_BUILDER_EDITOR_CS` 제거
   - ExportWorker에서 `FXC_PSDImporter.cs` 1개만 출력

**결과**: Unity 프로젝트에 `FXC_PSDImporter.cs` 파일 1개만 `Assets/Editor/`에 배치하면 모든 PSD 임포트 기능 사용 가능.

### v3.1 — 통합 순서 + Sprite 설정 강화 (2026-02-26)

**발견된 문제 1**: 그룹과 레이어가 같은 부모 아래 혼합되어 있을 때, C# 임포터의 sibling 정렬이 잘못됨.

**원인 분석**:

`collect_layer_metadata()`에서 그룹과 레이어에 **별도 order 카운터** 사용:
- 그룹: `grp_order` = 0, 1, 2, ... (그룹끼리만 순번)
- 레이어: `enumerate(export_layers)` = 0, 1, 2, ... (레이어끼리만 순번)

C# 임포터에서 같은 부모의 자식들(그룹+레이어 혼합)을 order로 정렬할 때, 두 카운터의 값이 비교 불가능:
```
lid_group 자식:
  lid_ribbon_group (그룹 order=6)  ← 그룹 카운터
  fxt_ribbon_end_R (레이어 order=7) ← 레이어 카운터
  → 우연히 맞아 보이지만...

purple_box_group 자식:
  open_lid_group (그룹 order=2)  ← 그룹 카운터
  box_group (그룹 order=4)
  lid_group (그룹 order=5)
  → 레이어 order 0~19와 범위 겹침, 정렬 불안정
```

**수정 내용**:

1. **통합 순서 맵** (`psd_extractor.py`):
   ```python
   # psd.descendants() 1회 순회로 그룹+레이어 공통 순번 부여
   _unified_order = {}
   for uid, desc in enumerate(psd.descendants()):
       _unified_order[id(desc)] = uid

   # 그룹: _unified_order[id(desc)] 사용
   # 레이어: _unified_order.get(id(layer), fallback) 사용
   ```

2. **C# 정렬 방향** — 오름차순 (`a.ord.CompareTo(b.ord)`):
   - psd-tools `descendants()` 순서 = bottom→top (back→front)
   - 낮은 통합 번호 = back → Unity sibling 0 (뒤에 렌더링)
   - 높은 통합 번호 = front → Unity 마지막 sibling (앞에 렌더링)

**발견된 문제 2**: Setup Sprites에서 Sprite 타입 변환 시 Mesh Type이 기본값 Tight로 설정됨. UI/FX 용도에서는 Full Rect가 적절.

**수정 내용**:

Setup Sprites 자동 설정에 추가:
```csharp
TextureImporterSettings settings = new TextureImporterSettings();
imp.ReadTextureSettings(settings);
settings.spriteMeshType = SpriteMeshType.FullRect;
settings.spriteGenerateFallbackPhysicsShape = false;
imp.SetTextureSettings(settings);
```

**Mesh Type 선택 기준**:

| 조건 | 선택 |
|------|------|
| UI Canvas (Image 컴포넌트) | Full Rect |
| FX / 파티클 텍스처 | Full Rect |
| Sliced / Tiled / Filled | Full Rect |
| SpriteRenderer + 큰 투명 영역 | Tight |
| SpriteRenderer + 작은 스프라이트 | Full Rect |

### v3.2 — Pivot 시스템 + C# 고유 클래스명 + NGUI 지원 (2026-02-26)

**발견된 문제 1**: Unity Import 후 루트 오브젝트의 피봇이 항상 PSD top-left 원점에 위치. 캐릭터 하단 중심 등 다른 기준점이 필요한 경우 수동 조정 필요.

**발견된 문제 2**: 여러 PSD를 Export하면 동일한 C# 클래스명(`FXC_PSDImporter`)으로 Unity에서 컴파일 에러.

**수정 내용**:

1. **9방향 Pivot 시스템**:

   | 피봇명 | (px, py) | 설명 |
   |--------|----------|------|
   | Top-Left | (0.0, 0.0) | PSD 원점 (기존 v2 동작) |
   | Top-Center | (0.5, 0.0) | 상단 중심 |
   | Top-Right | (1.0, 0.0) | 상단 우측 |
   | Center-Left | (0.0, 0.5) | 중앙 좌측 |
   | Center | (0.5, 0.5) | 이미지 중심 |
   | Center-Right | (1.0, 0.5) | 중앙 우측 |
   | Bottom-Left | (0.0, 1.0) | 하단 좌측 |
   | **Bottom-Center** | **(0.5, 1.0)** | **하단 중심 (기본값)** |
   | Bottom-Right | (1.0, 1.0) | 하단 우측 |

   - Output 패널에 Pivot 콤보박스 추가 (UGUI/NGUI 세그먼트 옆)
   - 기본값: Bottom-Center (캐릭터 발 밑 기준점, 가장 일반적)

2. **좌표 변환 공식 업데이트** (`psd_extractor.py`):
   ```python
   "unity": {
       "x": round(layer.left + w / 2.0 - psd.width * pivot_x, 2),
       "y": round(-(layer.top + h / 2.0) + psd.height * pivot_y, 2),
   }
   ```

3. **JSON v3 포맷**:
   ```json
   {
     "version": 3,
     "pivot": { "x": 0.5, "y": 1.0 },
     ...
   }
   ```

4. **C# UGUI 동적 anchor** (`FXC_PSDImporter_{Stem}.cs`):
   ```csharp
   public class PivotInfo { public float x; public float y; }
   // PSDLayout에 pivot 필드 추가
   float ax = (layout.pivot != null) ? layout.pivot.x : 0f;
   float ay = (layout.pivot != null) ? 1f - layout.pivot.y : 1f;
   rt.anchorMin = new Vector2(ax, ay);
   rt.anchorMax = new Vector2(ax, ay);
   ```

5. **C# NGUI pivot 오프셋** (`FXC_PSDImporterNGUI_{Stem}.cs`):
   ```csharp
   float offX = layout.canvas.width * (pvtX - 0.5f);
   float offY = layout.canvas.height * (0.5f - pvtY);
   posX = layer.unity.x + offX;
   posY = layer.unity.y + offY;
   ```

6. **C# 고유 클래스명**:
   - PSD 파일명 stem → PascalCase 변환 → 클래스 접미사
   - `ch_01.psd` → `FXC_PSDImporter_Ch01`
   - `gift_box.psd` → `FXC_PSDImporter_GiftBox`
   - UGUI/NGUI 모두 적용

7. **UGUI/NGUI 선택 UI 변경**:
   - QComboBox → SegmentedButton (2개 중 택1)
   - Output 패널 2행 구조: Row 1 (경로), Row 2 (Unity+Pivot+Export)

**JSON v3 예시**:
```json
{
  "version": 3,
  "psd_file": "ch_01.psd",
  "canvas": { "width": 210, "height": 283 },
  "pivot": { "x": 0.5, "y": 1.0 },
  "groups": [...],
  "layers": [
    {
      "name": "arm_R",
      "file": "arm_R.png",
      "unity": { "x": -35.0, "y": 153.0, "width": 40, "height": 60 },
      ...
    }
  ]
}
```

**결과**: 사용자가 9방향 중 원하는 피봇을 선택하면 JSON 좌표가 해당 피봇 기준으로 생성되고, C# 임포터가 anchor를 자동 설정하여 Unity에서 올바른 위치에 배치.

### v3.3 — 루트 RectTransform pivot/sizeDelta 수정 + 피봇 프리뷰 마커 (2026-02-26)

**발견된 문제**: UGUI C# 임포터에서 루트 오브젝트의 RectTransform에 sizeDelta와 pivot을 설정하지 않아 Unity 기본값 `(100, 100)` / `(0.5, 0.5)` 적용. 앱에서 Bottom-Left를 선택해도 Unity에서는 Center로 표시됨.

**수정 내용**:

1. **루트 RectTransform 설정** (`ImportPSD` 함수):
   ```csharp
   RectTransform rootRT = root.GetComponent<RectTransform>();
   rootRT.pivot = new Vector2(pvtX, 1f - pvtY);  // PSD→Unity Y축 반전
   rootRT.sizeDelta = new Vector2(
       canvas.width * scaleFactor,
       canvas.height * scaleFactor);
   ```
   - pivot: JSON의 `(px, py)` → Unity `(px, 1-py)` 변환
   - sizeDelta: PSD 캔버스 크기 × scaleFactor
   - 예) Bottom-Left `(0.0, 1.0)` → Unity pivot `(0.0, 0.0)` = 좌하단

2. **피봇 프리뷰 마커**:
   - 프리뷰 상단 오버레이에 ◎ 토글 버튼 추가 (✛ 십자선 옆, 기본 ON)
   - Pivot 콤보 선택에 따라 이미지 위에 빨간 십자+원 마커로 피봇 위치 표시
   - `QGraphicsLineItem` (arm=10px) + `QGraphicsEllipseItem` (반경 4px)
   - OFF 시 마커 완전 숨김, ON으로 복원 시 현재 Pivot 값 즉시 반영
   - 레이어 전환/호버/줌 시 마커 위치 유지

**결과**: 앱 프리뷰에서 피봇 위치를 시각적으로 확인 가능. Unity Import 시 루트 오브젝트의 피봇이 앱 설정과 정확히 일치.

---

### v3.4 — NGUI 워크플로우 완성 (2026-02-28)

실제 Unity 프로젝트에서 NGUI Import를 반복 테스트하며 전체 파이프라인을 완성. Setup Textures → Make Atlas → Import to Scene 3단계 원클릭 워크플로우 구축.

#### NGUI C# Editor 주요 기능

**1. Setup Textures 버튼**
- JSON에서 이미지 서브폴더를 자동 감지 (`FindImageFolder`)
- 폴더 내 모든 텍스처를 일괄 설정:
  - TextureType = Sprite
  - isReadable = true
  - textureCompression = Uncompressed
  - spriteImportMode = Single
  - meshType = FullRect
  - npotScale = None

**2. Make Atlas 버튼**
- NGUI `UITexturePacker.PackTextures` 기반 Atlas 자동 생성
- 생성 산출물:
  - `{폴더명}.png` — 패킹된 아틀라스 이미지 (RGBA32, 4096 제한)
  - `{폴더명}.mat` — Material (Unlit/Transparent Colored 셰이더)
  - `{폴더명}.asset` — NGUIAtlas ScriptableObject (sprite 목록 + material 참조)
- 설정: padding=2 (프로덕션 NGUI Atlas Maker 일치)
- `NGUIMath.ConvertToPixels`로 UV → 픽셀 좌표 변환 → UISpriteData 생성
- Atlas 생성 후 컴포넌트의 atlasObject 필드에 자동 반영
- Atlas 업데이트: 이미지 폴더 우클릭 → Open Atlas Updater → Sync

**3. Import to Scene 개선**
```
GameObject (FXC_PSDImporterNGUI 스크립트)
└── 260225_giftBox_v1     ← PSD 파일명 루트 (layout.psd_file)
    └── fxRoot_anim        ← 애니메이션 타겟 컨테이너
        ├── Group1         ← PSD 그룹
        │   ├── s_body_01  ← fxt_ → s_ 자동 변환
        │   └── s_arm_R
        └── s_leg_01
```

변경사항:
- **PSD명 루트**: `Path.GetFileNameWithoutExtension(layout.psd_file)`로 생성
- **fxRoot_anim**: 루트 바로 아래 빈 GameObject. 애니메이션 데이터 연결 대상
- **fxt_ → s_**: 텍스처 네이밍(fxt_) → 스프라이트 네이밍(s_) 자동 변환
  ```csharp
  string displayName = layer.name;
  if (displayName.StartsWith("fxt_"))
      displayName = "s_" + displayName.Substring(4);
  ```
- **정수 좌표**: `Mathf.RoundToInt()`로 Position 반올림 (픽셀 퍼펙트)
  ```csharp
  int posX = Mathf.RoundToInt(layer.unity.x + offX);
  int posY = Mathf.RoundToInt(layer.unity.y + offY);
  ```
- **PSD order 정렬**: `layout.layers.OrderBy(l => l.order)`로 depth 정확 할당
- **UIPanel 경고**: Import 후 UIPanel 미존재 시 경고

#### Export 변경사항

- NGUI 모드 시 이미지 서브폴더를 PSD 파일명과 동일하게 생성
  ```python
  # 기존: img_dir = os.path.join(scale_dir, "Images")
  # 변경: PSD 스템(확장자 제외)으로 동적 생성
  _psd_stem = os.path.splitext(os.path.basename(self.psd_filename))[0]
  img_dir = os.path.join(scale_dir, _psd_stem)
  ```
- JSON의 `layer.file`에 서브폴더 경로 포함 (예: `260225_giftBox_v1/layer.png`)

#### 발생한 이슈 및 해결

| 이슈 | 원인 | 해결 |
|------|------|------|
| INGUIAtlas cast error | `t.atlasObject`가 `Object` 타입 | 이미 검증된 `INGUIAtlas atlas` 변수 사용 |
| EncodeToPNG 실패 | `PackTextures`가 compressed format 반환 | `UITexturePacker` + `ARGB32` |
| Atlas Y-flip | `RenderTexture` → `ReadPixels` 플랫폼 차이 | `GetPixels32()` 직접 복사 |
| Material _MainTex null | `CreateAsset` 후 텍스처 참조 유실 | delete → `new Material(tex)` → `CreateAsset` |
| 보라색 아틀라스 배경 | textureType=Default + auto compression | Advanced + RGBA32 platform override |
| 하이어라키 순서 역전 | `fxRoot_anim`이 PSD 루트 위에 생성 | PSD명 루트 → fxRoot_anim → 콘텐츠 3단 구조 |
| fxRoot_anim 소수점 Position | `float offX/offY` (홀수 캔버스 283px → -141.5) | `Mathf.RoundToInt()` 정수화 |
| CS0101 중복 클래스 | 복수 PSD Export 시 글로벌 데이터 클래스 충돌 | Editor 클래스 내부에 nested class로 이동 |
| 그룹 피봇 오프셋 오적용 | offX/offY가 개별 레이어에 적용됨 | fxRoot_anim.localPosition에만 적용, 레이어는 pivot-relative 좌표 |
| 단일 최상위 그룹 중복 | PSD 최상위 그룹이 1개일 때 하이어라키 중복 | mergedTopGroupKey로 감지 → fxRoot_anim에 병합 |

#### NGUI 워크플로우 (최종)

```
[PSD Extractor]                          [Unity]
Export (NGUI) ─→ 폴더 복사 ─→ Tools > FXC PSD Importer (NGUI)
  ├─ JSON                        ├─ JSON Browse
  └─ {psd_stem}/                 ├─ Setup Textures (텍스처 설정)
     ├─ layer1.png               ├─ Make Atlas (아틀라스 자동 생성)
     ├─ layer2.png               ├─ Base Depth / Step 설정
     └─ ...                      └─ Import to Scene
                                      └─ Atlas Updater로 추후 업데이트 가능
```

---

### v3.5 — UIShaderWidget 독립화 (Phase 28, 2026-03-01)

**변경 동기**:
- 기존 UIShaderWidget이 `UICustomRendererWidget` (`External/UIParticleWidget/`)에 의존
- 다른 Unity 프로젝트에 복사 시 외부 패키지까지 함께 복사해야 하는 불편
- UICustomRendererWidget의 클리핑 기능(SoftClip/TextureClip)은 셰이더 FX에 불필요

#### 상속 구조 변경

```
Before: UIWidget → UICustomRendererWidget → UIShaderWidget
After:  UIWidget → UIShaderWidget  (독립)
```

#### UICustomRendererWidget에서 복사한 핵심 기능 (~40줄)

| 기능 | 역할 |
|------|------|
| `m_Renderer` / `m_UseSharedMaterial` | Renderer 참조 + 공유 Material 설정 |
| `material` property override | Renderer의 Material 반환 |
| `Awake()` | `boundless=true`, `fillGeometry=false`, `mWidth=mHeight=2` |
| `OnInit()` / `CacheComponents()` | Renderer 자동 캐싱 |
| `OnDrawCallCreated()` | `dc.SetExternalRenderer(m_Renderer)` — DrawCall↔Renderer 연결 |
| `Invalidate()` override | Panel 영역 무관 가시성 (이펙트 용도) |

#### 복사하지 않은 기능 (~150줄)

- `OnWillRenderObject()` — SoftClip/TextureClip 클리핑
- `MaterialPropertyBlock` — 셰이더 키워드 관리
- 관련 static ID 캐싱 (`_ClipRange0`, `_ClipArgs0`, `_ClipTexID`)

#### Inspector 표준화

```
Before: UIShaderWidgetEditor : UICustomRendererWidgetInspector (NGUI 스타일)
After:  UIShaderWidgetEditor : Editor (표준 Unity UI)
```

`UICustomRendererWidgetInspector`는 `[CustomEditor(typeof(UICustomRendererWidget), true)]`로 서브클래스에도 적용되어 NGUI 스타일(어두운 배경, NGUIEditorTools)이 강제됨. UIWidget 직접 상속으로 이 간섭 자동 해제.

#### Hierarchy Depth 표시

`HierarchyExtend.cs` 추가 — `EditorApplication.hierarchyWindowItemOnGUI`로 UIShaderWidget depth 번호를 연한 초록색으로 표시. VHierarchy의 아이콘 영역(30px)을 오프셋으로 확보하여 겹침 방지.

#### SendMessage 에러 수정

`MeshFilter.sharedMesh` setter → 내부 `SendMessage("OnMeshFilterChanged")` → OnValidate 중 호출 시 Unity 에러. 동일 Mesh 참조 체크(`if (mf.sharedMesh != _mesh)`)로 해결.

#### 복사 필요 파일 (4개)

```
NGUIShaderWidget/
  UIShaderWidget.cs              ← Runtime (Quad Mesh + NGUI Depth)
  Editor/
    UIShaderWidgetEditor.cs      ← Inspector (표준 Unity UI)
    HierarchyExtend.cs           ← Hierarchy depth 번호 표시
    FXC_PlayModeSaver.cs         ← Play 전 SaveAssets
```

의존성: NGUI(UIWidget)만 있으면 동작. UICustomRendererWidget 불필요.

#### Material 네이밍 수정

기존에 Setup 시 생성되는 Material 에셋명에 `mat_` prefix가 붙었으나 제거:
```
Before: POT/Materials/mat_fxt_jackpot_title.mat
After:  POT/Materials/fxt_jackpot_title.mat
```

**수정 위치** (`psd_extractor_gui_qt.py` 템플릿 내 3곳):
1. `matPath = matAssetFolder + "/" + layer.name + ".mat"` (기존: `"/mat_" + layer.name`)
2. `mat.name = layer.name;` × 2곳 (기존: `"mat_" + layer.name`)

**이유**: Material 파일명이 레이어 이미지 파일명과 일치하는 것이 직관적이고 관리 용이.

#### PSD Exporter 템플릿

`_FXC_MESHQUAD_EDITOR_CS` 내 Setup() 코드:
```csharp
UIShaderWidget sw = go.AddComponent<UIShaderWidget>();  // MeshFilter+MeshRenderer 자동 추가
sw.meshSize = new Vector3(width, height, 0f);
sw.Rebuild();
sw.depth = currentDepth;  // NGUI depth 직접 설정 (별도 UICustomRendererWidget 불필요)
```

#### 배포용 스크립트 백업

다른 프로젝트에 복사할 수 있도록 독립 스크립트 4개를 별도 보관:
```
C:\Users\NHN\Desktop\NGUIShaderWidget\
  UIShaderWidget.cs              ← Runtime
  Editor/
    UIShaderWidgetEditor.cs      ← Inspector
    HierarchyExtend.cs           ← Hierarchy depth 표시
    FXC_PlayModeSaver.cs         ← Play 전 SaveAssets
```

---

## 향후 계획

- [ ] Blend mode 실제 렌더링 지원 (커스텀 UI 셰이더)
- [ ] Skin 시스템 (캐릭터 의상/색상 변형)
- [ ] PSD 태그 시스템 (`[bone]`, `[pivot]` 등) 도입 검토
- [x] ~~Sprite Atlas 자동 생성 연동~~ → NGUI Make Atlas 구현 완료 (v3.4)
- [ ] 애니메이션 키프레임 지원 (복수 PSD → AnimationClip)

---

## 참고 링크

- [PhotoshopToSpine.jsx](https://github.com/EsotericSoftware/spine-scripts/tree/master/photoshop) — Esoteric Software, Spine 공식 PSD 내보내기 스크립트
- [E:\PhotoshopToSpine.jsx](file:///E:/PhotoshopToSpine.jsx) — 로컬 참고 사본
- [psd-tools 라이브러리](https://psd-tools.readthedocs.io/) — Python PSD 파싱 라이브러리
