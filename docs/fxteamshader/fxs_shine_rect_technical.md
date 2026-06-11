# fxs_shine_rect — 구현 상세 / 설계 결정 / 개발 히스토리

기존 셰이더를 수정하거나 유사 셰이더를 개발할 때 참고.

---

## v2f 구조체

```hlsl
struct v2f
{
    float4 pos      : SV_POSITION;
    fixed4 color    : COLOR;
    float2 uv       : TEXCOORD0;   // 메시 UV [0,1]
    float2 worldPos : TEXCOORD1;   // NGUI 패널 정규화 좌표 [-1,1]
    float3 sinCosA  : TEXCOORD2;   // x=sin, y=cos (_ShineAngle), z=aspect (W/H)
};
```

`sinCosA.z`에 aspect를 패킹한 이유: 별도 TEXCOORD 절약. Quad(평면 메시)에서는 모든 버텍스가 동일한 uniform 값을 가지므로 보간 오차 없음.

---

## Fragment 처리 흐름

### 1단계 — UV 플립 (브랜치 없음)

```hlsl
uv.x = abs(_FlipX - uv.x);   // _FlipX=0: 그대로, _FlipX=1: 1-uv (반전)
uv.y = abs(_FlipY - uv.y);
```

`_FlipX`/`_FlipY`는 Toggle (0 또는 1). 조건 분기 없이 수식으로 처리.

### 2단계 — Padding 및 사각형 경계

```hlsl
float padL = _Padding.x;
float padR = 1.0 - _Padding.y;
float padB = _Padding.z;
float padT = 1.0 - _Padding.w;

float2 rectCenter  = (padL+padR, padB+padT) * 0.5;
float2 rectHalfExt = (padR-padL, padT-padB) * 0.5 * _Scale;
float2 p           = uv - rectCenter;
```

`_Scale`은 `rectHalfExt`에만 곱해짐 → 중심 고정, 크기만 축소.

### 3단계 — Border 계산

```hlsl
half heightUV = (padT - padB) * _Scale;
half bL = _BorderLeft   * heightUV / aspect;   // aspect로 나눠 UV 너비 환산
half bR = _BorderRight  * heightUV / aspect;
half bB = _BorderBottom * heightUV;
half bT = _BorderTop    * heightUV;
```

모든 Border는 높이 기준 정규화. Left/Right를 aspect로 나누는 이유: UV 공간에서 x=0.1은 y=0.1보다 실제 픽셀 너비가 aspect배 더 넓으므로, 같은 값 입력 시 같은 픽셀 두께를 얻기 위함.

### 4단계 — StrokeAlign

```hlsl
half outerFactor = (1.0 + _StrokeAlign) * 0.5;   // -1→0, 0→0.5, +1→1
half innerFactor = (1.0 - _StrokeAlign) * 0.5;   // -1→1, 0→0.5, +1→0

outerHalfExt = rectHalfExt + border * outerFactor
innerHalfExt = max(rectHalfExt - border * innerFactor, 0)
```

- `_StrokeAlign=-1` (Inset): outer=rect 경계, inner=rect 안쪽으로 border만큼 들어옴
- `_StrokeAlign=0` (Center): 양쪽으로 반씩
- `_StrokeAlign=+1` (Outset): inner=rect 경계, outer=rect 바깥쪽으로 border만큼 나감

비대칭 border(L≠R, B≠T)일 때 outer/inner rect의 중심이 rectCenter에서 이동:
```hlsl
p_outer = p - (bR-bL)*outerFactor*0.5, (bT-bB)*outerFactor*0.5
p_inner = p - (bL-bR)*innerFactor*0.5, (bB-bT)*innerFactor*0.5
```

### 5단계 — Corner SDF

**Sharp** (기본): aspect 무관, UV 공간 직접 사용
```hlsl
float SharpRectSDF(float2 p, float2 b)
{
    return max(abs(p.x) - b.x, abs(p.y) - b.y);
}
```

**Round**: aspect-corrected 공간에서 계산 → 스크린에서 원형 코너
```hlsl
float RoundedRectSDF(float2 p, float2 b, float r, float aspect)
{
    float2 pa = float2(p.x * aspect, p.y);
    float2 ba = float2(b.x * aspect, b.y);
    r = min(r, min(ba.x, ba.y));
    float2 d = abs(pa) - ba + r;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r;
}
```

inner 반지름 계산:
```hlsl
effectiveOuterR = min(scaledRadius, min(outerHalfExt.x * aspect, outerHalfExt.y));
borderThicknessY = outerHalfExt.y - innerHalfExt.y;
innerR = max(effectiveOuterR - borderThicknessY, 0.0);
```

**Chamfer**: aspect-corrected 45° 사선 모서리
```hlsl
float ChamferedRectSDF(float2 p, float2 b, float c, float aspect)
{
    float2 pa = float2(p.x * aspect, p.y);
    float2 ba = float2(b.x * aspect, b.y);
    c = min(c, min(ba.x, ba.y));
    float2 q = abs(pa);
    return max(max(q.x - ba.x, q.y - ba.y), q.x + q.y - (ba.x + ba.y - c));
}
```

### 6단계 — 마스크

```hlsl
fixed insideOuter = step(sdfOuter, 0.0);
fixed insideInner = step(sdfInner, 0.0);
fixed mask = insideOuter - insideInner * (1.0 - _Fill);
```

`_Fill=0`: 내부=0, 테두리=1 (외곽선)
`_Fill=1`: 전체=1 (꽉찬 사각형)

### 7단계 — Shine 스윕

**중요**: Shine은 UV 공간에서 회전. `_AspectRatio`(aspect)를 사용하지 않음.
→ `_AspectRatio` 변경이 Shine 너비에 영향을 주지 않도록 의도적 분리.

```hlsl
// UV 공간 회전 (aspect 없음)
float2 pr = float2(p_outer.x * cosA - p_outer.y * sinA,
                   p_outer.x * sinA + p_outer.y * cosA);

// Shine이 이동해야 하는 전체 범위
float extentX = abs(outerHalfExt.x * cosA) + abs(outerHalfExt.y * sinA);
float extentY = abs(outerHalfExt.x * sinA) + abs(outerHalfExt.y * cosA);

// 일정한 물리적 띠 너비 (rect 높이 기준)
float bh = max(_ShineWidth * outerHalfExt.y, 0.001);

// Progress 0=완전히 왼쪽 밖, 1=완전히 오른쪽 밖
float center = lerp(-extentX - bh, extentX + bh, _Progress);

float su = (pr.x - center) / (bh * 2.0) + 0.5;   // [0,1] in band
float sv = pr.y / max(extentY, 0.001) * 0.5 + 0.5;

// 텍스처 UV 확대
float2 shineTexUV = float2(
    saturate((su - 0.5) / _ShineTexScaleX + 0.5),
    saturate((sv - 0.5) / _ShineTexScaleY + 0.5)
);

fixed inBand = step(0.0, su) * step(su, 1.0);
fixed shine  = tex2D(_ShineTex, shineTexUV).r * inBand * _Intensity;
```

### 8단계 — 색상 합성

```hlsl
fixed shineAmt = shine * mask;
fixed baseAmt  = mask * _BaseAlpha;

fixed3 col  = _ShineColor.rgb * shineAmt + _Color.rgb * baseAmt;
fixed  alpha = saturate(shineAmt * _ShineAlpha + baseAmt) * _Alpha * i.color.a;
col *= i.color.rgb;
```

**알려진 동작**: `_BaseAlpha`가 col과 alpha 양쪽에 포함되어 실제 기여는 `_BaseAlpha²`.
- 가산 블렌드(기본 SrcAlpha One): VFX 특성상 허용. "펀치감 있는" 비선형 응답.
- 일반 블렌드(SrcAlpha OneMinusSrcAlpha): `_BaseAlpha=0.5`가 25% 불투명도로 나타남. 필요 시 `sqrt(desired_opacity)`로 입력.
- 수정을 원할 경우: `col = _ShineColor.rgb * shineAmt + _Color.rgb * mask`로 변경하면 선형 응답이 되지만, 기존 애니메이션 키프레임 값이 바뀜.

### 9단계 — NGUI 클리핑

```hlsl
#if defined(_SOFTCLIP_ON)
    float2 clipFactor = (float2(1.0, 1.0) - abs(i.worldPos)) * _ClipArgs0;
    alpha *= clamp(min(clipFactor.x, clipFactor.y), 0.0, 1.0);
#endif
#if defined(_TEXCLIP_ON)
    // i.worldPos는 [-1,1] 패널 정규화 좌표 → [0,1] UV로 변환
    alpha *= tex2D(_ClipTex, i.worldPos * 0.5 + 0.5).a;
#endif
```

---

## 주요 설계 결정

### 결정 1: `_AspectRatio` 수동 입력 (자동 계산 제거)

**이유**: NGUI UIWidget은 `transform.localScale`이 실제 픽셀 크기(예: 600×166)이지만 버텍스 좌표계는 [-0.5, 0.5] 정규화 공간. 월드 변환 행렬에서 aspect를 계산하면 비율이 아닌 픽셀값이 나와 잘못된 결과 발생.

**Trade-off**: 사용자가 직접 W/H 비율을 입력해야 하나, 신뢰할 수 있는 값 보장.

### 결정 2: Shine이 UV 공간에서 회전 (aspect 미적용)

**이유**: `_AspectRatio` 변경이 Shine 너비에 영향을 주어서는 안 된다는 사용자 요구. aspect를 shine 회전에 적용하면 aspect 조정 시 band width가 변하는 문제 발생.

**Trade-off**: `_ShineAngle=45°`가 비정사각형 rect에서 시각적으로 45° 각도로 보이지 않음. Shine은 UV 공간 기준의 각도.

### 결정 3: bh = _ShineWidth × outerHalfExt.y (일정한 물리 너비)

**이유**: 이전 구현에서 `bh = _BandWidth × extentX` 사용 시 extentX가 각도에 따라 최대 3.9배 변함 (aspect 3.6:1 rect에서 0°→90° 회전). Progress 이동 속도와 band width가 각도에 따라 비선형적으로 변하는 문제.

**Fix**: `outerHalfExt.y`(rect 높이 절반) 기준으로 고정 → 각도와 무관하게 일정한 물리 너비.

### 결정 4: _ShineAlpha, _BaseAlpha를 별도 프로퍼티로 분리

**이유**: `_ShineColor.a`, `_Color.a`의 개별 채널은 Unity Legacy Animation에서 키프레임 설정이 불편함. 단일 float Range 슬라이더가 훨씬 효율적.

### 결정 5: DisableBatching="True"

**이유**: FXC_NGUISoftClip 컴포넌트가 MaterialPropertyBlock으로 `_ClipRange0`/`_ClipArgs0`를 매 프레임 세팅. Dynamic Batching 적용 시 다른 오브젝트의 값과 섞여 클리핑 좌표가 오염됨.

### 결정 6: _TEXCLIP_ON에서 i.worldPos * 0.5 + 0.5 사용

**이유**: `i.uv`는 메시 자체 UV(0~1)이며 패널 공간과 무관. NGUI TexClip은 패널 공간 기준 UV가 필요. `i.worldPos`는 이미 `_ClipRange0`로 패널 정규화 좌표([-1,1])로 변환된 값이므로 +0.5 오프셋으로 [0,1] UV 공간으로 변환.

---

## 개발 히스토리

### [Fix] bh 계산 — 비선형 orbit 속도

- **증상**: ShineAngle 변경 시 band width와 이동 속도가 비선형적으로 변함
- **원인**: `bh = _BandWidth * extentX`. extentX가 회전 각도에 따라 최대 3.9× 변함
- **수정**: `bh = _ShineWidth * outerHalfExt.y` (rect 높이 고정 기준)

### [Fix] NGUI _MainTex 에러

- **증상**: `Material doesn't have a texture property '_MainTex'` 콘솔 에러
- **원인**: NGUI UIWidget.mainTexture 접근 시 _MainTex 프로퍼티 필요
- **수정**: `[HideInInspector] [NoScaleOffset] _MainTex ("", 2D) = "white" {}` 추가

### [Fix] 새 머티리얼 SrcBlend=One/DstBlend=Zero

- **증상**: 새로 생성한 머티리얼이 불투명하게 렌더링
- **원인**: 기본 머티리얼(Standard shader) 생성 후 셰이더 변경 → Standard의 One/Zero 블렌드값 유지
- **수정**: 셰이더에서 직접 머티리얼 생성하거나 .mat 파일에서 SrcBlend=5, DstBlend=1로 직접 설정

### [Fix] _AspectRatio 자동 계산 제거

- **증상**: 월드 행렬에서 계산한 aspect 값이 NGUI UIWidget에서 잘못된 결과
- **원인**: UIWidget 버텍스는 픽셀 좌표, transform.localScale은 픽셀 크기 → 행렬 기반 계산 불가
- **수정**: `_AspectRatio` 수동 입력 프로퍼티로 전환

### [Fix] _AspectRatio가 Shine 너비에 영향

- **증상**: _AspectRatio 조정 시 Shine band width도 변함
- **원인**: `p_corr = float2(p_outer.x * aspect, p_outer.y)` 형태의 aspect-corrected 회전 사용
- **수정**: Shine 섹션에서 aspect 제거. `p_outer` 직접 회전. `extentX/Y`에서도 aspect 제거

### [Fix] DisableBatching 누락

- **증상**: 잠재적 — SoftClip 클리핑 좌표 오염 가능성
- **원인**: 태그 미설정
- **수정**: `"DisableBatching"="True"` 추가

### [Fix] _TEXCLIP_ON UV 오류

- **증상**: TexClip 활성화 시 잘못된 클리핑 영역
- **원인**: `tex2D(_ClipTex, i.uv)` — 메시 UV 사용
- **수정**: `tex2D(_ClipTex, i.worldPos * 0.5 + 0.5)` — 패널 정규화 좌표 사용

### [Rename] 프로퍼티명 변경

| 이전 | 이후 | 이유 |
|---|---|---|
| `_BandWidth` | `_ShineWidth` | Shine 계열 프로퍼티와 접두사 통일 |
| `_ShineScaleX/Y` | `_ShineTexScaleX/Y` | "텍스처 UV 스케일"임을 명확히 표현 |

**주의**: 이전 이름으로 설정된 애니메이션 클립이 있다면 바인딩이 끊어짐. 해당 프로퍼티를 제거하고 새 이름으로 재설정 필요.

---

## 현재 셰이더 Uniform 선언 전체

```hlsl
fixed4 _ShineColor;
fixed4 _Color;
half   _ShineAlpha;
half   _BaseAlpha;
half   _Intensity;
half   _ShineWidth;
half   _Progress;
float  _ShineAngle;
half   _ShineTexScaleX;
half   _ShineTexScaleY;
half   _BorderLeft;
half   _BorderRight;
half   _BorderBottom;
half   _BorderTop;
half   _StrokeAlign;
half   _Fill;
float4 _Padding;
fixed  _FlipX;
fixed  _FlipY;
half   _CornerRadius;
half   _Scale;
half   _AspectRatio;
fixed  _Alpha;

float4 _ClipRange0 = float4(0.0, 0.0, 1.0, 1.0);  // 기본값: 클리핑 없음
float2 _ClipArgs0  = float2(1000.0, 1000.0);         // 기본값: 클리핑 없음

sampler2D _ShineTex;
sampler2D _ClipTex;
// _MainTex: sampler 선언 불필요 (더미 프로퍼티, 실제 샘플링 안 함)
```

---

## 개선 후보 (미구현)

| 항목 | 내용 | 우선순위 |
|---|---|---|
| `_BaseAlpha` 선형 응답 | 현재 _BaseAlpha² 응답. `col`에서 _BaseAlpha 분리 시 선형화 가능. 기존 키프레임 값 변경 필요. | 낮음 |
| Shine 텍스처 V-대칭 | orbit(360° 순환) 효과를 위해 아래쪽이 위쪽의 수직 반전인 그라디언트 텍스처 제작. 셰이더 변경 불필요. | 필요 시 |
| `_ShineAngle` 스크린 공간 일치 | 현재 UV 공간 기준 → 비정사각형 rect에서 시각적 각도 왜곡. 수정 시 _AspectRatio가 Shine에 다시 영향. | Trade-off 존재 |
