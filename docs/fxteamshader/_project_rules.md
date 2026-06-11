# 프로젝트 공통 셰이더 규칙

모든 셰이더 작업 전 반드시 숙지. 이 규칙은 모든 셰이더에 적용된다.

## 프로젝트 개요

- Unity 2022.3.62f2, PC standalone + Android 모바일 확장
- 게임: 포커 (Classic Poker, Holdem, Casino)
- 주 타겟: **저사양 유저** — 성능 우선, 화질 후순위
- 렌더링: NGUI 기반 UI 렌더링

## 플랫폼 제약

```hlsl
#pragma target 2.0          // 필수 — GLES 2.0 / DX9 호환
```

- Windows 7 + DX9 지원 필수
- Android GLES 2.0 지원 필수
- **HDR 사용 안 함** — `[HDR]` 어트리뷰트, HDR 색상 범위 언급 불필요

## 성능 규칙

| 항목 | 규칙 |
|---|---|
| 정밀도 | `float` → `half`/`fixed` 적극 활용. UV, 색상, 간단한 비율값은 `half` 이하 |
| Fragment 연산 | `sin`, `cos`, `length`, `sqrt` 최소화. 가능하면 vertex로 이동 |
| 텍스처 샘플 | 최소화. Pass당 2개 이하 권장 |
| 분기 | GLES 2.0 dynamic branch 지양. `#if defined()` 컴파일타임 분기 사용 |
| LINQ | 사용 금지 (C# 스크립트 작업 시) |

## 타입 선택 기준

```hlsl
fixed   // 0~1 범위 값: 알파, 마스크, 토글 플래그
half    // 일반 UV, 비율, 중간 계산값 (범위 ±60000)
float   // 월드 좌표, 각도(sin/cos 입력), 정밀도 필요한 값
float4  // 유니폼 벡터 (Padding 등)
```

## SubShader 태그 표준

모든 VFX/UI 셰이더는 아래 태그를 기본으로 사용:

```hlsl
Tags
{
    "Queue"="Transparent"
    "IgnoreProjector"="True"
    "RenderType"="Transparent"
    "PreviewType"="Plane"
    "ForceNoShadowCasting"="True"
    "DisableBatching"="True"       // NGUI MaterialPropertyBlock 사용 시 필수
}

Blend [_SrcBlend] [_DstBlend]
Cull Off
Lighting Off
ZWrite Off
Fog { Mode Off }
```

- `DisableBatching="True"`: NGUI SoftClip이 MaterialPropertyBlock으로 `_ClipRange0`/`_ClipArgs0`를 설정하므로 필수. 없으면 Dynamic Batching 시 클리핑 값이 오염됨.

## Blend 기본값

| 용도 | SrcBlend | DstBlend | Unity Enum 값 |
|---|---|---|---|
| 가산 (VFX 기본) | SrcAlpha | One | 5, 1 |
| 일반 반투명 | SrcAlpha | OneMinusSrcAlpha | 5, 10 |

머티리얼 프로퍼티로 노출:
```hlsl
[Enum(UnityEngine.Rendering.BlendMode)] _SrcBlend ("Src Blend", Float) = 5
[Enum(UnityEngine.Rendering.BlendMode)] _DstBlend ("Dst Blend", Float) = 1
```

## 머티리얼 생성 주의사항

**잘못된 방법**: 기본 머티리얼(Standard shader) 생성 → 셰이더 변경
- Standard 셰이더의 SrcBlend=One, DstBlend=Zero가 그대로 남아 불투명하게 렌더링됨

**올바른 방법**: Project 창에서 셰이더 파일 우클릭 → Create → Material
- 또는 기존 fxs_ 계열 머티리얼을 Duplicate해서 사용

## NGUI 연동 규칙

### _MainTex 더미 프로퍼티 필수

NGUI UIWidget이 `material.mainTexture`를 참조 — `_MainTex` 없으면 에러 발생:
```hlsl
[HideInInspector] [NoScaleOffset] _MainTex ("", 2D) = "white" {}
```
CGPROGRAM 내에서 `sampler2D _MainTex` 선언 불필요 (실제로 샘플링 안 함).

### SoftClip 지원

```hlsl
#pragma multi_compile_local _ _SOFTCLIP_ON

// Uniforms (기본값 필수 — FXC_NGUISoftClip이 없을 때 클리핑 없이 안전하게 동작)
float4 _ClipRange0 = float4(0.0, 0.0, 1.0, 1.0);
float2 _ClipArgs0  = float2(1000.0, 1000.0);

// Vertex
float2 worldXY = mul(unity_ObjectToWorld, v.vertex).xy;
o.worldPos = worldXY * _ClipRange0.zw + _ClipRange0.xy;  // [-1,1] 패널 정규화 좌표

// Fragment
#if defined(_SOFTCLIP_ON)
    float2 clipFactor = (float2(1.0, 1.0) - abs(i.worldPos)) * _ClipArgs0;
    alpha *= clamp(min(clipFactor.x, clipFactor.y), 0.0, 1.0);
#endif
```

### TexClip 지원

```hlsl
#pragma multi_compile_local _ _TEXCLIP_ON

// Fragment — worldPos 기반 UV 사용 (i.uv 사용 금지 — 메시 UV와 패널 UV는 다름)
#if defined(_TEXCLIP_ON)
    alpha *= tex2D(_ClipTex, i.worldPos * 0.5 + 0.5).a;
#endif
```

### Depth 관리

별도 컴포넌트(NGUI-Custom Render Widget) 가 renderer.sortingOrder 또는 material.renderQueue를 조정. 셰이더에서 별도 처리 불필요.

## Fallback

```hlsl
FallBack "Mobile/Particles/Additive"
```

## 금지 사항

- 이모지/이모티콘 사용 금지
- 별도 C# 컴포넌트 추가 금지 (셰이더 기능은 셰이더 내에서 해결)
- HDR 관련 기능 추가 금지
