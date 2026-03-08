# layer_exporter.py & LayerExporter.jsx - Photoshop 기반 도구

Photoshop COM 연결 또는 내장 스크립트로 레이어를 내보내는 도구.

## 개요

두 가지 버전이 있습니다:

| 도구 | 실행 방식 | 용도 |
|------|----------|------|
| `layer_exporter.py` | 터미널에서 Python CLI | 배치 자동화, rename + export |
| `LayerExporter.jsx` | Photoshop > File > Scripts > Browse | Photoshop 내부에서 직접 실행, GUI |

## layer_exporter.py (Python CLI)

### 의존성
```
pip install photoshop-python-api
```

### 사용법

```bash
# 레이어 목록
python layer_exporter.py list

# 인터랙티브 이름 변경
python layer_exporter.py rename --interactive

# JSON으로 일괄 이름 변경
python layer_exporter.py rename --config rename_config.json

# 내보내기
python layer_exporter.py export -o ./out --visible-only --even-pad 2

# JPEG 내보내기
python layer_exporter.py export -o ./out --format jpeg --quality 10

# 특정 레이어만
python layer_exporter.py export -o ./out --layers "hand_R,hand_L"
```

### CLI 옵션 (export)

| 옵션 | 축약 | 기본값 | 설명 |
|------|------|--------|------|
| `--output` | `-o` | (필수) | 출력 폴더 |
| `--visible-only` | `-v` | false | Visible 레이어만 |
| `--even-pad` | | 0 | 각 축 +N px, 홀수→짝수 |
| `--padding-w` | | 0 | 너비 추가 픽셀 |
| `--padding-h` | | 0 | 높이 추가 픽셀 |
| `--format` | `-f` | png | png 또는 jpeg |
| `--quality` | `-q` | 10 | JPEG 품질 1-12 (Photoshop 스케일) |
| `--layers` | `-l` | 전체 | 콤마 구분 레이어 이름 |

### 아키텍처

```
Python CLI (argparse)
  ↓ photoshop-python-api (COM)
Photoshop 연결
  ↓ build_batch_export_jsx()
단일 JSX 코드 동적 생성
  ↓ app.eval_javascript(jsx)
Photoshop 내부에서 JSX 실행
  ↓ JSX 내부 동작:
    1. doc.duplicate() (원본 보호)
    2. rasterizeAll() (전처리)
    3. 레이어별: hideAll → show → crop(bounds) → pad → saveAs
    4. doc.close(DONOTSAVECHANGES)
  ↓
결과 문자열 반환 → Python에서 파싱 & 출력
```

### Spine 최적화 적용 사항
- `doc.duplicate()` → 복제본에서 작업, 원본 안전
- `rasterizeAll()` → 스마트오브젝트/텍스트 전처리
- `crop(bounds)` → trim(TRANSPARENT)보다 빠름 (픽셀 스캔 불필요)
- 단일 JSX 호출 → COM 왕복 오버헤드 제거

## LayerExporter.jsx (Photoshop 내장 스크립트)

### 실행 방법
1. Photoshop에서 PSD 파일 열기
2. **File > Scripts > Browse** 선택
3. `LayerExporter.jsx` 선택
4. ScriptUI 다이얼로그에서 설정 후 Export 클릭

### 다이얼로그 설정

- **Document Info**: 파일명, 크기, 레이어 수
- **Export Settings**: Visible 레이어만, PNG/JPEG 선택, JPEG 품질
- **Padding**: Even-pad 모드 또는 고정 W/H 패딩
- **Output**: 출력 폴더 선택
- **Rename**: JSON 설정으로 레이어 이름 일괄 변경 (선택)

### 동작 방식
LayerExporter.jsx는 layer_exporter.py와 동일한 최적화 패턴을 사용합니다:
- 문서 복제 → rasterizeAll → crop(bounds) → 패딩 → saveAs → 히스토리 복원
- 결과를 alert 다이얼로그로 표시

## 성능 비교

| 방식 | 시간 (20 레이어) | 비고 |
|------|------------------|------|
| layer_exporter.py | ~156초 | Python → COM → JSX |
| LayerExporter.jsx | ~148초 | 순수 인프로세스 JSX |
| **psd_extractor.py** | **~3.6초** | **Photoshop 불필요 (권장)** |

병목은 Photoshop의 PNG saveAs 연산 자체이므로, Photoshop을 사용하는 한 추가 최적화 여지가 제한적입니다.

## 제한사항 & 알려진 이슈

- **COM artLayers vs layers**: `doc.artLayers`는 캐싱 문제가 있어 패널 순서와 불일치 가능. `doc.layers`를 사용해야 안정적
- **중복 레이어 이름**: `getByName()`은 항상 첫 번째 매칭. 배열 형식 JSON + 순차 rename으로 해결
- **한글 인코딩**: 터미널에서 `PYTHONIOENCODING=utf-8` 환경변수 필요
- **JPEG 품질 스케일**: Photoshop은 1-12 스케일 (Pillow의 1-100과 다름)

## 이 도구를 사용할 때

- PSD에 레이어 효과(드롭쉐도우 등)가 적용되어 있고 **Photoshop 렌더링 결과 그대로** 내보내야 할 때
- Photoshop 액션/스크립트와 연동해야 할 때
- 내보내기 전 Photoshop에서 실시간 편집이 필요할 때

단순 레이어 추출만 필요하면 `psd_extractor.py`를 사용하세요 (41배 빠름).
