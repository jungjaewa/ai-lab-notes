# psd_extractor.py - Standalone PSD Layer Extractor

Photoshop 없이 PSD 파일에서 직접 레이어를 추출하는 CLI 도구.

## 의존성

```
pip install psd-tools Pillow
```

## 사용법

### 레이어 목록 조회
```bash
python psd_extractor.py list ch.psd
```

### 기본 내보내기
```bash
python psd_extractor.py export ch.psd -o ./out
```

### Visible 레이어만 + Even-pad
```bash
python psd_extractor.py export ch.psd -o ./out --visible-only --even-pad 2
```
각 축에 +2px 추가 후 홀수면 +1하여 짝수로 맞춤.
예: 73x58 → +2 → 75x60 → 홀수 보정 → 76x60

### 이름 변경 + 내보내기
```bash
python psd_extractor.py export ch.psd -o ./out --visible-only --even-pad 2 --rename rename_config.json
```

### JPEG 내보내기
```bash
python psd_extractor.py export ch.psd -o ./out --format jpeg --quality 85
```

### 특정 레이어만 내보내기
```bash
python psd_extractor.py export ch.psd -o ./out --layers "오른손,왼손,몸통"
```

### 고정 패딩
```bash
python psd_extractor.py export ch.psd -o ./out --padding-w 20 --padding-h 20
```

## CLI 옵션 (export)

| 옵션 | 축약 | 기본값 | 설명 |
|------|------|--------|------|
| `psd_file` | | (필수) | PSD 파일 경로 |
| `--output` | `-o` | (필수) | 출력 폴더 |
| `--visible-only` | `-v` | false | Visible 레이어만 |
| `--even-pad` | | 0 | 각 축 +N px, 홀수→짝수 |
| `--padding-w` | | 0 | 너비 추가 픽셀 |
| `--padding-h` | | 0 | 높이 추가 픽셀 |
| `--format` | `-f` | png | png 또는 jpeg |
| `--quality` | `-q` | 85 | JPEG 품질 (1-100) |
| `--layers` | `-l` | 전체 | 콤마 구분 레이어 이름 |
| `--rename` | `-r` | 없음 | 이름 변경 JSON 파일 |

## rename_config.json 형식

### 배열 형식 (중복 이름 처리 가능, 권장)
```json
[
  {"old": "오른손", "new": "fxt_ch_hand_01_R"},
  {"old": "오른손", "new": "fxt_ch_hand_02_R"},
  {"old": "왼손", "new": "fxt_ch_hand_L"}
]
```
동일 이름 레이어가 여러 개일 때, 배열 순서대로 매칭됩니다.

### 딕셔너리 형식 (단순 1:1 매핑)
```json
{
  "오른손": "fxt_ch_hand_R",
  "왼손": "fxt_ch_hand_L"
}
```

## 아키텍처

```
PSD 파일
  ↓ psd-tools (PSDImage.open)
PSD 파싱 → 레이어 트리 구조
  ↓ collect_layers()
레이어 목록 (flat list)
  ↓ filter_export_layers()
내보낼 레이어 필터링
  ↓ extract_layer_image()
각 레이어 → PIL Image (RGBA)
  ↓ apply_padding()
패딩 적용 (even-pad / fixed)
  ↓ Pillow save
PNG/JPEG 저장
```

### 주요 함수

| 함수 | 설명 |
|------|------|
| `collect_layers(psd)` | PSD 레이어 트리를 재귀 탐색하여 flat list 반환 |
| `filter_export_layers()` | visible-only, 특정 레이어 필터링 |
| `extract_layer_image(layer)` | `composite()` → RGBA PIL Image 추출, 실패시 `topil()` 폴백 |
| `apply_padding(img, ...)` | 투명 캔버스 생성 + 중앙 배치로 패딩 적용 |
| `even_ceil(value)` | 홀수면 +1하여 짝수로 맞춤 |
| `next_pot(value)` | 값 이상의 가장 가까운 2의 거듭제곱 반환 |
| `apply_pot(img, ..., resize_type)` | POT 캔버스 확장 + Nuke Reformat Resize Type 6종 (none/fit/fill/width/height/distort). 불투명 배경 시 alpha_composite 플래튼 |
| `convert_color_mode(img, mode, bg_rgb)` | RGBA/RGB/L 색상 모드 변환 |
| `save_png_oxipng(img, file_path, level)` | pyoxipng RawImage 직접 인코딩으로 최적화 PNG 저장 |
| `collect_layer_metadata(...)` | Unity UGUI/NGUI용 JSON 메타데이터 수집 (통합 순서 — 그룹+레이어 단일 카운터, pivot 좌표 오프셋 적용, scale_factor/pot 파라미터 지원) |
| `_get_group_path(layer)` | psd-tools Layer의 부모 그룹 경로 반환 (루트→부모 순서) |

### collect_layer_metadata 시그니처

```python
collect_layer_metadata(
    psd, export_layers, rename_map, fmt="png",
    even_pad=0, pad_w=0, pad_h=0,
    psd_filename="",
    group_rename_map=None,
    force_even=True,
    pivot_x=0.0, pivot_y=0.0,
    scale_factor=1.0,
    pot_auto=False, pot_w=0, pot_h=0
)
```

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `pivot_x` | 0.0 | X축 피봇 비율 (0=left, 0.5=center, 1=right) |
| `pivot_y` | 0.0 | Y축 피봇 비율 (0=top, 0.5=center, 1=bottom) |
| `force_even` | True | True면 홀수 크기를 짝수로 올림 |
| `group_rename_map` | None | 그룹 경로→변경명 매핑 dict |
| `scale_factor` | 1.0 | 배율 (canvas, rect, unity 좌표 모두 적용) |
| `pot_auto` | False | True면 padded_size에 POT 자동 적용 |
| `pot_w` | 0 | Manual POT 너비 (0이면 자동) |
| `pot_h` | 0 | Manual POT 높이 (0이면 자동) |

좌표 변환 공식 (pivot 적용):
```
unity.x = layer.left + width/2 - psd.width * pivot_x
unity.y = -(layer.top + height/2) + psd.height * pivot_y
```

반환 JSON 버전: v3 (`"pivot": {"x": pivot_x, "y": pivot_y}` 포함)

## 성능

| 항목 | psd_extractor.py | layer_exporter.py (Photoshop) |
|------|-------------------|-------------------------------|
| 20 레이어 PNG | **3.6초** | 148초 |
| Photoshop 필요 | 아니오 | 예 |
| COM 오버헤드 | 없음 | 있음 |
| 병목 | PIL PNG 압축 | PS saveAs PNG |

## 제한사항

- **레이어 효과** (드롭쉐도우, 스트로크 등): 완벽 재현 불가. PSD 저장 전에 Photoshop에서 Rasterize 권장
- **조정 레이어**: 합성 미지원 (Adjustment Layer는 건너뜀)
- **일부 블렌드 모드**: dissolve 등 미지원
- **색상 프로파일**: Photoshop과 미세한 차이 가능
- **텍스트 레이어**: 텍스트 렌더링 불가 (래스터화된 결과만 추출 가능)

2D 리깅용 캐릭터 파츠는 대부분 단순 픽셀 레이어이므로 위 제한사항의 영향이 거의 없습니다.
