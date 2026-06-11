# fxs_shine_rect — 기능 개요 및 프로퍼티 레퍼런스

## 개요

텍스처 없이 사각형(직사각형)을 프로시쥬얼하게 그리고, 그 위에 빛이 지나가는 Shine 효과를 연출하는 셰이더.

- **셰이더 이름**: `FX Team/fxs_shine_rect`
- **파일 경로**: `Assets/PlatformAsset/Classic/DirectLinkResource/VFX/Shaders/fxs_shine_rect.shader`
- **테스트 프리팹**: `Assets/PlatformAsset/Classic/DirectLinkResource/VFX/_set/_260610_FX_RND_shine_rect/fxs_shine_rect.prefab`
- **테스트 머티리얼**: `Assets/PlatformAsset/Classic/DirectLinkResource/VFX/_set/_260610_FX_RND_shine_rect/_fxt_shine_rect_v2.mat`

## 주요 기능

| 기능 | 설명 |
|---|---|
| Filled / Outline | `_Fill` 0=외곽선만, 1=꽉찬 사각형, 중간값=반투명 내부 |
| Corner Type | Sharp(기본) / Round / Chamfer — 컴파일 variant로 분기 |
| Stroke Align | 테두리를 안쪽(-1), 가운데(0), 바깥쪽(1) 정렬 |
| Shine Sweep | 빛 띠가 진행 방향으로 스윕. Progress 0→1 애니메이션 |
| Padding | UV 공간에서 사각형 경계를 안쪽으로 이동 |
| Scale | 패딩 중심에서 균일 축소 |
| AspectRatio | Border 두께와 Corner 형태 보정. Shine 너비에는 영향 없음 |
| NGUI SoftClip | FXC_NGUISoftClip 연동. 패널 경계 소프트 클리핑 |
| NGUI TexClip | 텍스처 마스크 기반 클리핑 |

## Shader Variants

```
_SOFTCLIP_ON (on/off) × _TEXCLIP_ON (on/off) × _CORNER (Sharp/Round/Chamfer)
= 총 12 variants
```

---

## 프로퍼티 레퍼런스

### [Shine] 섹션

| HLSL명 | 표시명 | 타입 | 기본값 | 설명 |
|---|---|---|---|---|
| `_ShineTex` | Shine Texture | 2D | white | 빛 띠에 적용할 그라디언트 텍스처 (R채널 사용) |
| `_ShineColor` | Shine Color | Color | (1,1,1,1) | 빛 색상 |
| `_ShineAlpha` | Shine Alpha | Range(0,1) | 1.0 | 빛이 알파에 기여하는 강도. 애니메이션용. |
| `_Intensity` | Intensity | Range(0,5) | 1.0 | 빛 밝기 배율 |
| `_ShineWidth` | Shine Width | Range(0.01,2.0) | 0.3 | 빛 띠 너비 (rect 높이 대비 비율) |
| `_ShineAngle` | Shine Angle | Range(-180,180) | 0.0 | 빛 진행 방향 (0=좌→우, 90=아래→위) |
| `_ShineTexScaleX` | Shine Tex Scale X | Range(0.1,5) | 1.0 | 띠 내부 텍스처 UV 수평 확대(>1=확대) |
| `_ShineTexScaleY` | Shine Tex Scale Y | Range(0.1,5) | 1.0 | 띠 내부 텍스처 UV 수직 확대 |
| `_Progress` | Progress | Range(0,1) | 0.0 | 빛 위치. 0=왼쪽 밖, 0.5=중앙, 1=오른쪽 밖. 애니메이션 키. |

### [Shape] 섹션

| HLSL명 | 표시명 | 타입 | 기본값 | 설명 |
|---|---|---|---|---|
| `_Color` | Base Color | Color | (1,1,1,1) | 사각형 기본 색상 |
| `_BaseAlpha` | Base Alpha | Range(0,1) | 0.0 | 사각형 기본 불투명도. 0=투명(Shine만), 1=꽉 참. 애니메이션용. |
| `_Fill` | Fill | Range(0,1) | 0.0 | 0=외곽선만, 1=꽉찬 사각형 |
| `_Corner` | Corner Type | KeywordEnum | 0(Sharp) | Sharp / Round / Chamfer |
| `_CornerRadius` | Corner Radius | Range(0,0.5) | 0.0 | Round/Chamfer 코너 반지름 (UV 단위) |
| `_Padding` | Padding (L R B T) | Vector | (0,0,0,0) | 메시 UV 경계에서 사각형을 안쪽으로 이동. xyzw = Left Right Bottom Top |
| `_FlipX` | Flip X | Toggle | 0 | 수평 미러 |
| `_FlipY` | Flip Y | Toggle | 0 | 수직 미러 |
| `_Scale` | Scale | Range(0.01,1) | 1.0 | 패딩 중심 기준 균일 축소 |
| `_AspectRatio` | Aspect Ratio | Range(0.1,20) | 1.0 | 가로/세로 비율 (W/H). Border 두께 균일화 및 Corner 형태 보정에만 사용. Shine 너비에 영향 없음. |

### [Border] 섹션

모든 Border 값은 **높이(padT-padB) 기준 정규화 단위**.
Left/Right는 내부적으로 `_AspectRatio`로 나눠 UV 너비로 환산 → 같은 값 = 같은 픽셀 두께.

| HLSL명 | 표시명 | 타입 | 기본값 | 설명 |
|---|---|---|---|---|
| `_BorderLeft` | Border Left | Range(0,0.5) | 0.05 | 왼쪽 테두리 두께 |
| `_BorderRight` | Border Right | Range(0,0.5) | 0.05 | 오른쪽 테두리 두께 |
| `_BorderTop` | Border Top | Range(0,0.5) | 0.05 | 위쪽 테두리 두께 |
| `_BorderBottom` | Border Bottom | Range(0,0.5) | 0.05 | 아래쪽 테두리 두께 |
| `_StrokeAlign` | Stroke Align | Range(-1,1) | -1.0 | -1=Inset(안쪽), 0=Center, +1=Outset(바깥쪽) |

### [Global] 섹션

| HLSL명 | 표시명 | 타입 | 기본값 | 설명 |
|---|---|---|---|---|
| `_Alpha` | Final Alpha | Range(0,1) | 1.0 | 최종 전체 알파 배율 |
| `_SrcBlend` | Src Blend | Enum | 5 (SrcAlpha) | 블렌드 소스. 가산=5, 일반=5 |
| `_DstBlend` | Dst Blend | Enum | 1 (One) | 블렌드 대상. 가산=1, 일반=10 |

### [Hidden] 프로퍼티

| HLSL명 | 용도 |
|---|---|
| `_MainTex` | NGUI UIWidget.mainTexture 에러 방지용 더미. 셰이더에서 샘플링 안 함. |
| `_ClipTex` | NGUI TexClip 마스크 텍스처 |

---

## 일반적인 사용 시나리오

### 시나리오 1: Shine 애니메이션만 (테두리 위)

```
_Fill = 0          // 외곽선만
_BaseAlpha = 0     // 배경 투명
_ShineAlpha = 1    // Shine 불투명
_Progress: 0→1 애니메이션
Blend: SrcAlpha One (가산)
```

### 시나리오 2: 배경 박스 + Shine

```
_Fill = 1
_BaseAlpha = 0.8   // 반투명 배경
_ShineAlpha = 1
Blend: SrcAlpha OneMinusSrcAlpha (일반 반투명)
```

### 시나리오 3: 라운드 외곽선

```
_Fill = 0
_Corner = Round
_CornerRadius = 0.15
_BaseAlpha = 0     // Shine만
_AspectRatio = (실제 W/H 비율 입력)
```

---

## 애니메이션 키프레임 가이드

Legacy Animation 시스템 사용. `Mesh Renderer.Material_` 접두사는 Unity 에디터 고정 표시 형식.

주요 애니메이션 대상 프로퍼티:
- `_Progress`: Shine 스윕 위치
- `_ShineAlpha`: Shine 페이드 인/아웃
- `_BaseAlpha`: 배경 페이드 인/아웃
- `_Alpha`: 전체 페이드

`_ShineColor.a`, `_Color.a` 대신 `_ShineAlpha`, `_BaseAlpha`를 쓰는 이유: 단일 float 슬라이더가 Color 채널보다 키프레임 설정이 용이.
