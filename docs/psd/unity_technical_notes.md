# Unity 기술 노트 — Shader FX Quad 시스템 개발 중 발견한 사항

이 문서는 UIShaderWidget (NGUI Shader Widget) 개발 과정에서 발견한 Unity 에디터/런타임의 기술적 동작 원리와 해결 방법을 기록합니다.

> **이력**: FXC_MeshQuad (Phase 25~27) → UIShaderWidget (Phase 28)으로 리팩토링됨.

---

## 1. Play 모드 진입 시 Material 텍스처 유실

### 증상

| 시나리오 | 결과 |
|----------|------|
| Setup → Inspector에서 텍스처 할당 → Play | 텍스처 **사라짐** |
| Play 중지 → 텍스처 재할당 → Play | 텍스처 **유지됨** |

동일한 동작(텍스처 할당 후 저장 없이 Play)인데 결과가 다름.

### 근본 원인: Unity 에셋 직렬화 라이프사이클

Unity에서 `.mat` 파일(Material 에셋)은 **디스크 파일**과 **메모리 상태** 두 가지가 존재한다.

```
디스크 (.mat 파일)              메모리 (Inspector에서 보이는 상태)
┌──────────────────────┐       ┌──────────────────────┐
│ shader = fxs_shine   │       │ shader = fxs_shine   │
│ _MainTex = null      │       │ _MainTex = my_tex    │  ← Inspector에서 할당
│ _Color = white       │       │ _Color = white       │
└──────────────────────┘       └──────────────────────┘
    ↑                              ↑
    SaveAssets() 시점의 상태        현재 작업 중인 상태
```

Inspector에서 Material 프로퍼티를 수정하면 **메모리에만** 반영된다. 디스크 파일은 `Ctrl+S` 또는 `AssetDatabase.SaveAssets()`를 호출하기 전까지 **변경 전 상태 그대로**.

### Play 모드 진입 시 Unity 내부 동작

```
Play 버튼 클릭
  → Unity가 도메인 리로드 (C# 재컴파일)
  → 모든 에셋을 디스크에서 다시 읽음
  → 메모리 상태는 디스크 상태로 덮어씌워짐
```

### 시나리오 1: Setup → 텍스처 할당 → Play → 사라짐

```
1. Setup 실행
   → C# 코드에서 new Material(shader) 생성
   → AssetDatabase.CreateAsset(mat, "layer.mat")  ← 디스크에 저장
   → 이 시점의 .mat: _MainTex = null

2. Inspector에서 텍스처 할당
   → 메모리의 Material._MainTex = my_texture
   → 디스크의 .mat 파일은 여전히 _MainTex = null  ← 핵심

3. Play 클릭
   → 도메인 리로드
   → Unity가 .mat 파일을 디스크에서 다시 읽음
   → _MainTex = null (디스크 상태로 복원)
   → 텍스처 사라짐
```

### 시나리오 2: 재할당 → Play → 유지됨

```
4. Play 중지 (도메인 리로드 발생)
   → Unity가 "dirty" 표시된 에셋들을 감지

5. Inspector에서 텍스처 재할당
   → 메모리의 Material._MainTex = my_texture
   → Unity가 이 Material을 "dirty"로 마킹

6. Play 클릭
   → 도메인 리로드 직전, Unity가 dirty 에셋을 자동 직렬화
   → .mat 파일에 _MainTex = my_texture 기록됨
   → 디스크에서 다시 읽어도 텍스처 존재
   → 유지됨
```

### 왜 차이가 나는가

`CreateAsset()` + `SaveAssets()`로 `.mat`이 디스크에 **확정 저장**되면, 이 시점의 상태가 "기준점"이 된다. 이후 Inspector 수정은 메모리만 변경하고 디스크에는 반영되지 않는다.

시나리오 2에서는 Play 중지 → 재할당 경로를 거치면 Unity의 도메인 리로드 과정에서 dirty 에셋 직렬화 타이밍이 달라져서 유지되는 것이다. 이것은 Unity 내부의 에셋 직렬화 최적화 때문이며, 동작이 **비결정적**(때에 따라 다름)이라 더 위험하다.

### 해결: FXC_PlayModeSaver

```csharp
[InitializeOnLoad]
static class FXC_PlayModeSaver
{
    static FXC_PlayModeSaver()
    {
        EditorApplication.playModeStateChanged += OnPlayModeChanged;
    }

    static void OnPlayModeChanged(PlayModeStateChange state)
    {
        if (state == PlayModeStateChange.ExitingEditMode)
            AssetDatabase.SaveAssets();  // Play 직전에 모든 변경사항 디스크에 저장
    }
}
```

**동작 흐름 (수정 후):**
```
1. Setup → .mat 디스크 저장 (_MainTex = null)
2. Inspector에서 텍스처 할당 → 메모리만 변경
3. Play 클릭
   → ExitingEditMode 이벤트 발생
   → FXC_PlayModeSaver가 SaveAssets() 호출
   → 메모리 변경사항이 디스크에 기록됨
   → 도메인 리로드
   → 디스크에서 .mat 읽음 → _MainTex = my_texture
   → 텍스처 유지
```

### `[InitializeOnLoad]`를 사용하는 이유

| 방식 | 동작 시점 | 문제 |
|------|----------|------|
| `OnEnable()` | 컴포넌트 활성화 시 | Play 진입 **후** → 이미 늦음 |
| `Awake()` | Play 시작 시 | 도메인 리로드 **후** → 이미 늦음 |
| `[InitializeOnLoad]` | 에디터 로드 즉시 이벤트 구독 | ExitingEditMode = 리로드 **전** |

`ExitingEditMode`는 Unity가 도메인 리로드를 시작하기 **직전**에 발생하는 이벤트. 이 타이밍에 `SaveAssets()`를 호출하면 메모리→디스크 동기화가 리로드 전에 완료된다.

### 교훈

- Unity Inspector에서 수정한 에셋 프로퍼티는 `SaveAssets()`/`Ctrl+S` 전까지 인메모리 상태
- `CreateAsset()` + `SaveAssets()`로 확정 저장된 에셋은 이후 Inspector 수정이 디스크에 자동 반영되지 않음
- Play 모드 진입 = 도메인 리로드 = 디스크에서 에셋 재로드 → 인메모리 변경 유실

---

## 2. [SerializeField] Mesh — 도메인 리로드 시 컴포넌트 간섭 방지

### 증상

Play 모드 진입 시 MeshRenderer의 Material 텍스처가 유실됨 (위 이슈와 별도 원인).

### 원인

```csharp
// 문제 코드
Mesh _mesh;  // 비직렬화 → 도메인 리로드 시 null

void OnEnable()
{
    if (_mesh == null) Rebuild();  // 항상 실행됨
}

public void Rebuild()
{
    if (_mesh == null) { _mesh = new Mesh(); }
    // ... 버텍스 설정 ...
    mf.sharedMesh = _mesh;  // ← MeshFilter에 새 메쉬 할당
}
```

도메인 리로드 순서:
```
1. C# 도메인 리로드 시작
2. 모든 [SerializeField] 필드 직렬화/복원
3. 비직렬화 필드(_mesh) → null
4. OnEnable() 호출 → _mesh == null → Rebuild()
5. Rebuild()가 MeshFilter.sharedMesh 교체
6. 이 시점에서 MeshRenderer가 아직 직렬화 복원 중 → 간섭
7. MeshRenderer의 Material 참조가 깨짐
```

### 해결

```csharp
[HideInInspector]
[SerializeField] Mesh _mesh;  // 직렬화 → 도메인 리로드 시 유지

void OnEnable()
{
    if (_mesh == null)  // 최초 생성 시에만 true
        Rebuild();
    // 도메인 리로드 시: _mesh는 직렬화되어 존재 → Rebuild 스킵
}
```

`[SerializeField]`로 메쉬를 씬에 직렬화하면:
- 도메인 리로드 시 메쉬가 유지됨
- OnEnable에서 Rebuild가 호출되지 않음
- MeshFilter.sharedMesh 교체 없음
- MeshRenderer 직렬화와 간섭 없음

### 교훈

- `[ExecuteAlways]` 컴포넌트에서 OnEnable의 동작 범위를 최소화할 것
- 도메인 리로드 시 OnEnable이 호출되므로, 이 시점에서 다른 컴포넌트를 수정하면 직렬화 충돌 가능
- 런타임에 생성하는 오브젝트(Mesh 등)도 `[SerializeField]`로 보존하면 리로드 안전성 확보

---

## 3. MeshRenderer HideFlags — Animation 키프레임 차단

### 증상

Animation 창에서 MeshRenderer의 Material 프로퍼티에 키프레임을 생성할 수 없음. "Add Property" 목록에 MeshRenderer가 나타나지 않음.

### 원인

```csharp
// 문제 코드
void OnEnable()
{
    var mr = GetComponent<MeshRenderer>();
    mr.hideFlags = HideFlags.HideInInspector;  // Inspector에서 숨김
}
```

`HideFlags.HideInInspector`는 Inspector UI에서 컴포넌트를 숨기는 것뿐 아니라, **Animation 창에서도 해당 컴포넌트의 프로퍼티를 탐색 대상에서 제외**한다.

### 해결

MeshRenderer의 HideFlags를 건드리지 않는다. MeshFilter만 숨겨도 Inspector가 깔끔해진다.

```csharp
void OnEnable()
{
    // MeshFilter만 숨김 (MeshRenderer는 건드리지 않음)
    var mf = GetComponent<MeshFilter>();
    if (mf != null)
        mf.hideFlags = HideFlags.HideInInspector;

    // MeshRenderer는 그대로 노출 → Animation 키프레임 생성 가능
}
```

### 교훈

- `HideFlags.HideInInspector`는 Inspector 숨김 + Animation 창 탐색 제외
- Animation으로 제어해야 하는 컴포넌트(MeshRenderer, SpriteRenderer 등)에는 HideFlags를 설정하지 말 것
- 대안: Custom Editor에서 불필요한 섹션만 선택적으로 숨기거나, MeshFilter처럼 사용자가 직접 건드릴 일 없는 컴포넌트만 숨길 것

---

## 4. OnEnable에서 MeshRenderer 프로퍼티 수정 금지

### 증상

Play 모드 진입 시 MeshRenderer의 Material 설정값(텍스처 등)이 리셋됨.

### 원인

```csharp
// 문제 코드
void OnEnable()
{
    var mr = GetComponent<MeshRenderer>();
    mr.shadowCastingMode = ShadowCastingMode.Off;
    mr.receiveShadows = false;
    mr.lightProbeUsage = LightProbeUsage.Off;
    // ... 추가 설정 ...
}
```

`[ExecuteAlways]` 컴포넌트의 OnEnable은 **도메인 리로드 시에도 호출**된다. 이 시점에서 MeshRenderer의 프로퍼티를 수정하면:

```
도메인 리로드 시퀀스:
1. C# 스크립트 재컴파일
2. 모든 컴포넌트의 직렬화된 상태 복원 시작
3. OnEnable() 호출 ← 여기서 MeshRenderer 프로퍼티 수정
4. MeshRenderer의 직렬화 복원이 아직 진행 중일 수 있음
5. 수정과 복원이 충돌 → 예측 불가능한 상태
```

### 해결

MeshRenderer 설정은 **Setup 시 1회만** 적용하고, OnEnable에서는 절대 수정하지 않는다.

```csharp
// Setup 코드 (Editor에서 1회 실행)
void SetupChild(GameObject go, ...)
{
    FXC_MeshQuadChild qc = go.AddComponent<FXC_MeshQuadChild>();

    MeshRenderer mr = go.GetComponent<MeshRenderer>();
    mr.shadowCastingMode = ShadowCastingMode.Off;
    mr.receiveShadows = false;
    mr.lightProbeUsage = LightProbeUsage.Off;
    mr.reflectionProbeUsage = ReflectionProbeUsage.Off;
    mr.motionVectorGenerationMode = MotionVectorGenerationMode.ForceNoMotion;
    mr.allowOcclusionWhenDynamic = false;
    // Setup은 에디터에서 명시적으로 실행 → 도메인 리로드와 무관
}

// OnEnable — MeshRenderer 수정 없음
void OnEnable()
{
    var mf = GetComponent<MeshFilter>();
    if (mf != null && mf.hideFlags != HideFlags.HideInInspector)
        mf.hideFlags = HideFlags.HideInInspector;

    if (_mesh == null)
        Rebuild();
    // MeshRenderer는 건드리지 않음
}
```

### 교훈

- `[ExecuteAlways]` + OnEnable = 도메인 리로드마다 실행됨
- 도메인 리로드 중 다른 컴포넌트 프로퍼티 수정은 직렬화 충돌 위험
- "1회 설정" 성격의 코드는 Setup/Init 함수로 분리하고, OnEnable은 최소한의 자기 자신 초기화만

---

## 5. [RequireComponent] + AddComponent 순서

### 증상

"Can't add component 'MeshRenderer' because it already exists" 에러 + NullReferenceException.

### 원인

```csharp
// 문제 코드
[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class FXC_MeshQuadChild : MonoBehaviour { ... }

// Setup에서:
MeshFilter mf = go.AddComponent<MeshFilter>();      // 이미 존재 → 에러
MeshRenderer mr = go.AddComponent<MeshRenderer>();   // 이미 존재 → 에러
FXC_MeshQuadChild qc = go.AddComponent<FXC_MeshQuadChild>();
```

`[RequireComponent]`는 `AddComponent<FXC_MeshQuadChild>()`가 호출되는 순간 MeshFilter와 MeshRenderer를 **자동으로 추가**한다. 그 후에 명시적으로 `AddComponent<MeshFilter>()`를 호출하면 중복 에러.

### 해결

`AddComponent<FXC_MeshQuadChild>()`를 **먼저** 호출하고, MeshFilter/MeshRenderer는 `GetComponent`로 참조한다.

```csharp
// 올바른 순서
FXC_MeshQuadChild qc = go.AddComponent<FXC_MeshQuadChild>();  // MF+MR 자동 추가
qc.meshSize = new Vector3(width, height, 0f);
qc.Rebuild();

MeshRenderer mr = go.GetComponent<MeshRenderer>();  // AddComponent가 아닌 GetComponent
mr.shadowCastingMode = ShadowCastingMode.Off;
// ...
```

### 교훈

- `[RequireComponent]`가 있는 컴포넌트를 AddComponent하면 의존 컴포넌트가 자동 추가됨
- 이미 자동 추가된 컴포넌트에 다시 AddComponent하면 에러
- `[RequireComponent]` 사용 시 Setup 코드에서는 항상 `GetComponent`로 참조

---

## 6. 공유 Mesh .asset vs 인스턴스 메모리 Mesh

### 배경

여러 Quad가 서로 다른 크기를 가질 때, 메쉬를 어떻게 관리할 것인가.

### 방법 1: 공유 .asset (1x1 unit quad)

```csharp
// 공유 메쉬 에셋 (프로젝트에 1개)
// fxg_quad.asset: 1x1 unit quad
Mesh sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>("fxg_quad.asset");
mf.sharedMesh = sharedMesh;
transform.localScale = new Vector3(width, height, 1f);  // 스케일로 크기 제어
```

**문제**: `Transform.localScale ≠ (1,1,1)`
- 파티클 시스템이 부모 스케일의 영향을 받음
- 애니메이션에서 스케일 키프레임이 실제 크기와 혼동됨
- 자식 오브젝트의 좌표/크기가 부모 스케일에 의해 왜곡

### 방법 2: 인스턴스 메모리 Mesh (최종 채택)

```csharp
// 각 Quad마다 개별 메쉬 (메모리에 생성)
Mesh _mesh = new Mesh();
_mesh.vertices = new Vector3[] {
    new Vector3(-width * pvt.x, -height * pvt.y, 0),
    new Vector3(width * (1-pvt.x), -height * pvt.y, 0),
    new Vector3(width * (1-pvt.x), height * (1-pvt.y), 0),
    new Vector3(-width * pvt.x, height * (1-pvt.y), 0)
};
mf.sharedMesh = _mesh;
transform.localScale = Vector3.one;  // 항상 (1,1,1)
```

### 메모리 비용 비교

| 항목 | 공유 .asset | 인스턴스 Mesh |
|------|------------|--------------|
| Mesh 수 | 1개 | N개 |
| Quad 메모리 | ~100 bytes (공유) | ~100 bytes × N |
| 100개 Quad | ~100 bytes | ~10 KB |
| localScale | (width, height, 1) | (1, 1, 1) |

4-vertex quad의 메모리 비용은 무시 가능 (100 bytes). 100개 Quad = ~10KB. 현대 모바일 기기의 메모리(2~8GB)에서 완전히 무시 가능한 수준.

### 결론

`localScale = (1,1,1)` 유지가 애니메이션/파티클 워크플로우에서 필수적이므로, 인스턴스 메모리 메쉬가 올바른 선택. 메모리 비용은 실질적으로 0.

---

## 7. FXC_PlayModeSaver 클래스명과 uniquify 패턴

### 배경

PSD Export 시 C# 클래스명을 PSD별로 고유하게 만들기 위해 `.replace("FXC_MeshQuad", unique_cls)` 패턴을 사용한다.

```
260225_giftBox.psd → FXC_MeshQuad_260225Giftbox
ch_01.psd         → FXC_MeshQuad_Ch01
```

이 패턴은 `FXC_MeshQuad`라는 문자열이 포함된 모든 클래스명을 치환한다:
- `FXC_MeshQuad` → `FXC_MeshQuad_260225Giftbox`
- `FXC_MeshQuadChild` → `FXC_MeshQuad_260225GiftboxChild`
- `FXC_MeshQuadEditor` → `FXC_MeshQuad_260225GiftboxEditor`
- `FXC_MeshQuadChildEditor` → `FXC_MeshQuad_260225GiftboxChildEditor`

### 문제

`FXC_PlayModeSaver`는 "FXC_MeshQuad" 문자열이 포함되어 있지 않으므로 **치환되지 않는다**.

```
FXC_PlayModeSaver  → FXC_PlayModeSaver (변경 없음)
```

여러 PSD를 Export하면 동일한 `FXC_PlayModeSaver` 클래스가 여러 파일에 존재하게 된다.

### 왜 문제가 되지 않는가

1. **기능이 동일**: `SaveAssets()`는 전역 동작이므로 어떤 인스턴스가 호출해도 결과 동일
2. **C# 파일 미존재 시에만 생성**: Export 코드에서 `if not os.path.exists(_mq_ed_path)` 가드로 중복 파일 생성 방지
3. **동일 클래스 정의가 2개 이상 있으면**: Unity가 CS0101 에러를 발생시키지만, 파일 미존재 가드로 실제 중복 파일은 생성되지 않음

### 만약 문제가 된다면

클래스명에 "FXC_MeshQuad"를 포함시키면 자동으로 uniquify 된다:
```csharp
// 예: FXC_MeshQuadPlayModeSaver → 자동 치환됨
static class FXC_MeshQuadPlayModeSaver { ... }
```

현재는 파일 존재 가드로 충분하므로 변경하지 않음.

---

---

## 8. SendMessage cannot be called during OnValidate

### 증상

Inspector에서 UIShaderWidget의 Mesh Size를 변경하면 콘솔에 에러:
```
SendMessage cannot be called during Awake, CheckConsistency, or OnValidate
  (fxt_jackpot_title: OnMeshFilterChanged)
```

### 원인

```
UIShaderWidgetEditor.OnInspectorGUI()
  → serializedObject.ApplyModifiedProperties()
  → OnValidate() 트리거
  → Rebuild()
  → mf.sharedMesh = _mesh    ← MeshFilter 내부에서 SendMessage("OnMeshFilterChanged") 호출
```

Unity의 `MeshFilter.sharedMesh` setter는 내부적으로 `SendMessage("OnMeshFilterChanged")`를 호출한다. 이것이 `OnValidate` 콜백 내에서 실행되면 Unity가 에러를 발생시킨다.

### 해결

```csharp
public void Rebuild()
{
    // ... 메쉬 버텍스/UV/삼각형 수정 ...
    _mesh.RecalculateBounds();

    // 동일한 Mesh 참조면 재할당 스킵 → SendMessage 방지
    if (mf.sharedMesh != _mesh)
        mf.sharedMesh = _mesh;
}
```

핵심: `new Mesh()`는 최초 1회만 실행되고, 이후 `Rebuild()`는 **동일 Mesh 인스턴스**의 vertices/uv/triangles를 in-place로 수정한다. `mf.sharedMesh`는 이미 같은 참조를 가리키므로 `!= _mesh`가 false → 재할당 스킵 → SendMessage 미발생.

### 교훈

- `MeshFilter.sharedMesh` 할당은 내부적으로 `SendMessage`를 호출한다
- `OnValidate`에서 다른 컴포넌트의 프로퍼티를 수정하면 Unity 제약에 걸릴 수 있다
- 동일 참조 체크(`!=`)로 불필요한 할당을 건너뛰면 안전하게 회피 가능

---

## 9. UIShaderWidget — UIWidget 직접 상속으로 독립화

### 배경

UIShaderWidget은 원래 `UICustomRendererWidget`을 상속하여 NGUI depth + MeshRenderer DrawCall 통합 기능을 사용했다.

```
UIWidget → UICustomRendererWidget → UIShaderWidget
             (External/UIParticleWidget/)
```

문제: UICustomRendererWidget은 `External/UIParticleWidget/` 경로에 있는 외부 패키지 파일. 다른 프로젝트에 UIShaderWidget을 복사할 때 이 의존성까지 복사해야 함. 또한 UICustomRendererWidget은 SoftClip/TextureClip 등 UIShaderWidget에 불필요한 클리핑 기능을 포함.

### 해결: UIWidget 직접 상속

```
UIWidget → UIShaderWidget  (UICustomRendererWidget 의존 제거)
```

UICustomRendererWidget에서 **필수 기능만** 복사:

```csharp
public class UIShaderWidget : UIWidget  // ← 직접 상속
{
    // --- UICustomRendererWidget에서 복사한 핵심 기능 ---

    [SerializeField] protected Renderer m_Renderer;
    [SerializeField] protected bool m_UseSharedMaterial = false;

    public override bool hasVertices { get { return true; } }

    // Material — Renderer에서 가져옴
    public override Material material { get { ... } }

    // NGUI 초기화 — boundless=true, fillGeometry=false
    protected override void Awake()
    {
        base.Awake();
        mWidth = mHeight = 2;
        boundless = true;       // Panel 영역 제한 없음
        fillGeometry = false;   // NGUI 자체 geometry 생성 안 함
    }

    // Renderer 캐싱
    protected override void OnInit() { base.OnInit(); CacheComponents(); }

    // DrawCall ↔ 외부 Renderer 연결
    public override void OnDrawCallCreated(UIDrawCall dc)
    {
        CacheComponents();
        dc.SetExternalRenderer(m_Renderer);
    }

    // 가시성 — Panel 영역 무관하게 항상 표시
    public override void Invalidate(bool includeChildren)
    {
        if (panel != null)
        {
            UpdateVisibility(CalculateCumulativeAlpha(Time.frameCount) > 0.001f, true);
            UpdateFinalAlpha(Time.frameCount);
            if (includeChildren) base.Invalidate(true);
        }
    }

    // --- UIShaderWidget 고유 기능 (Quad Mesh) ---
    public Vector3 meshSize = ...;
    [SerializeField] Mesh _mesh;
    void OnValidate() { ... Rebuild(); }
    public void Rebuild() { ... }
}
```

### 복사하지 않은 기능 (클리핑)

UICustomRendererWidget의 ~150줄 클리핑 코드를 제외:
- `OnWillRenderObject()` — SoftClip/TextureClip 영역 계산
- `MaterialPropertyBlock` — 셰이더 프로퍼티 블록
- `ClearClipping()`, `ApplySoftClip()`, `SetSoftClipKeyword()`, `SetTexClipKeyword()`
- 관련 static 변수 (`_ClipRange0`, `_ClipArgs0`, `_ClipTexID`)

**이유**: UIShaderWidget은 셰이더 FX(Shine 등) 전용. Panel 클리핑이 필요한 UI 요소에는 사용하지 않음.

### 복사 시 필요 파일

| 파일 | 위치 | 역할 |
|------|------|------|
| `UIShaderWidget.cs` | `Script/FX/` | Runtime — Quad Mesh + NGUI Depth |
| `UIShaderWidgetEditor.cs` | `Script/FX/Editor/` | Inspector (표준 Unity UI) |
| `HierarchyExtend.cs` | `Script/Editor/` | Hierarchy depth 번호 표시 |
| `FXC_PlayModeSaver.cs` | `Script/FX/Editor/` | Play 전 SaveAssets |

의존성: **NGUI(UIWidget)만 있으면** 동작. UICustomRendererWidget 불필요.

### Inspector 스타일

UIShaderWidgetEditor는 `Editor`를 직접 상속 (표준 Unity UI):
```csharp
[CustomEditor(typeof(UIShaderWidget))]
public class UIShaderWidgetEditor : Editor  // ← Editor 직접 상속
{
    // EditorGUILayout.PropertyField() 사용 (표준 스타일)
}
```

기존에는 `UICustomRendererWidgetInspector` (`[CustomEditor(typeof(UICustomRendererWidget), true)]`)가 서브클래스에도 적용되어 NGUI 스타일(어두운 배경, NGUIEditorTools)이 강제되었음. UIWidget 직접 상속으로 이 간섭도 자동 해제.

### SerializedProperty 이름 매핑

| Inspector 표시 | SerializedProperty | 선언 위치 |
|---------------|-------------------|----------|
| Mesh Size | `meshSize` | UIShaderWidget |
| Depth | `mDepth` | UIWidget (상속) |
| Renderer | `m_Renderer` | UIShaderWidget (자체 선언) |
| Use Shared Material | `m_UseSharedMaterial` | UIShaderWidget (자체 선언) |

UICustomRendererWidget 시절과 동일한 필드명 유지 → Editor 코드 변경 불필요.

---

## 10. Hierarchy에 NGUI Depth 번호 표시

### 배경

UIShaderWidget은 NGUI depth로 렌더링 순서를 제어한다. Hierarchy 창에서 각 오브젝트의 depth를 한눈에 확인할 수 있으면 작업 효율이 크게 향상된다.

### 구현: HierarchyExtend.cs

```csharp
[InitializeOnLoad]
public class HierarchyExtend
{
    static GUIStyle _depthStyle;

    static HierarchyExtend()
    {
        EditorApplication.hierarchyWindowItemOnGUI += HierarchyWindowItemOnGUI;
    }

    public static void HierarchyWindowItemOnGUI(int instanceID, Rect selectionRect)
    {
        var go = EditorUtility.InstanceIDToObject(instanceID) as GameObject;
        if (go == null) return;

        var sw = go.GetComponent<UIShaderWidget>();
        if (sw == null) return;

        if (_depthStyle == null)
        {
            _depthStyle = new GUIStyle(EditorStyles.label);
            _depthStyle.alignment = TextAnchor.MiddleRight;
            _depthStyle.normal.textColor = new Color(0.55f, 0.72f, 0.45f, 0.9f);
        }

        string text = sw.depth.ToString();
        float textWidth = _depthStyle.CalcSize(new GUIContent(text)).x;
        float iconOffset = 30f;  // VHierarchy 아이콘 영역 (MeshFilter + MeshRenderer = 2 × 13px + 여백)

        Rect rect = new Rect(
            selectionRect.xMax - iconOffset - textWidth - 2f,
            selectionRect.y,
            textWidth + 2f,
            selectionRect.height);

        GUI.Label(rect, text, _depthStyle);
    }
}
```

### VHierarchy 아이콘 숨김

VHierarchy 플러그인의 componentMinimap 기능이 MeshFilter/MeshRenderer 아이콘을 표시하면 depth 번호와 겹칠 수 있다. VHierarchy.cs에서 UIShaderWidget 타입의 아이콘을 null로 반환하여 숨김:

```csharp
// VHierarchy.cs L1039
else if (strType == "UIShaderWidget")
    componentIcons_byType[component.GetType()] = null;
```

### 디자인 결정

- **폰트**: `EditorStyles.label` (Unity 기본 라벨 폰트 — 일관된 크기). `miniLabel`은 너무 작아 가독성 저하
- **색상**: 연한 초록 `(0.55, 0.72, 0.45, 0.9)` — 일반 라벨과 구분되면서 눈에 띄지 않는 보조 정보
- **위치**: 오른쪽 정렬, VHierarchy 아이콘 영역(30px)을 오프셋으로 확보
- **+/− 버튼 없음**: depth 조정은 Inspector에서 하므로 Hierarchy에는 읽기 전용 표시만

---

## 요약: 핵심 원칙

| # | 원칙 | 근거 |
|---|------|------|
| 1 | Inspector 수정 ≠ 디스크 저장 | `SaveAssets()` 전까지 인메모리 |
| 2 | Play 모드 = 디스크에서 리로드 | 인메모리 변경 유실 가능 |
| 3 | `[ExecuteAlways]` OnEnable은 최소화 | 도메인 리로드 시 실행 → 간섭 위험 |
| 4 | 다른 컴포넌트 수정은 Setup에서만 | OnEnable에서 수정 시 직렬화 충돌 |
| 5 | Animation용 컴포넌트에 HideFlags 금지 | Animation 창에서 프로퍼티 탐색 불가 |
| 6 | `[RequireComponent]` → `GetComponent` | 자동 추가된 컴포넌트에 AddComponent 중복 에러 |
| 7 | 런타임 생성 오브젝트도 `[SerializeField]` 고려 | 도메인 리로드 시 null → 불필요한 재생성 방지 |
| 8 | `MeshFilter.sharedMesh` 할당 전 참조 체크 | OnValidate 중 SendMessage 방지 |
| 9 | 외부 패키지 의존 최소화 | 필수 기능만 복사하여 독립 컴포넌트 구성 |
| 10 | Hierarchy 보조 정보는 읽기 전용 | depth 번호 표시만, 수정은 Inspector에서 |
