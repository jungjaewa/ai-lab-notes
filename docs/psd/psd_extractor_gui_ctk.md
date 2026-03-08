# psd_extractor_gui.py - CustomTkinter GUI 사용 가이드

CustomTkinter 기반 PSD 레이어 추출 GUI. (레거시 — Qt 버전 권장)

> **참고**: 이 버전은 위젯 생성 성능 이슈가 있습니다. `psd_extractor_gui_qt.py` (PySide6) 사용을 권장합니다.

## 의존성

```
pip install customtkinter psd-tools Pillow
```

## 실행

```bash
python psd_extractor_gui.py
```

---

## 화면 구성

Photoshop 스타일 다크 테마. `photoshop_theme.json`으로 컬러 팔레트 적용.

```
+--------------------------------------------------+
| PSD Layer Extractor                    [_][O][X]  |
+--------------------------------------------------+
| PSD File: [경로] [Browse]                         |
| 정보: ch.psd | 210x283 px | 22 layers             |
+--------------------------------------------------+
| Layers                                            |
| [Select Visible] [Deselect All] [↕ Order]         |
| Rename: [mode▼] [옵션] [Apply] [Clear]            |
| +-- CTkScrollableFrame --------------------------+|
| | [✓] ● 오른손    [rename entry]                 ||
| | [✓] ● 왼손      [rename entry]                 ||
| | [ ] ○ 몸통      [rename entry]                 ||
| +------------------------------------------------+|
+--------------------------------------------------+
| Settings                                          |
| Format: [PNG▼]  Quality: [슬라이더] 85             |
| Padding: [None|Even-pad|Fixed]                     |
+--------------------------------------------------+
| Output                                            |
| [출력 경로] [Browse]                               |
| [============= EXPORT =============]              |
| [진행바]                                           |
| [로그 텍스트박스]                                   |
+--------------------------------------------------+
```

---

## 사용법

### 1. PSD 파일 열기
1. **Browse** 버튼 클릭
2. PSD 파일 선택 → 레이어 목록 표시

### 2. 레이어 선택
- **체크박스 클릭**: 개별 레이어 체크/해제
- **Select Visible**: Visible 레이어만 체크
- **Deselect All**: 모든 체크 해제
- **↕ Order**: 순서 반전

### 3. 이름 변경
| 모드 | 설명 |
|------|------|
| **Manual** | rename 필드 직접 편집 |
| **Sequential** | 접두사+순번 자동 생성 |
| **Body Part** | 한글→영문 바디파트 매핑 |

Apply → 체크된 레이어에 rename 적용, Clear → 초기화

### 4. Settings
- **Format**: PNG (기본) / JPEG
- **Quality**: JPEG 품질 (1~100)
- **Padding**: None / Even-pad (+N px, 짝수 맞춤) / Fixed (W/H 지정)

### 5. Export
1. 출력 폴더 선택 (Browse)
2. **EXPORT** 클릭
3. 진행바 + 로그 확인

---

## Qt 버전과의 차이

| 항목 | CTk 버전 | Qt 버전 |
|------|---------|---------|
| 레이어 리스트 | ScrollableFrame (개별 위젯) | QListView (가상화) |
| 프리뷰 | CTkLabel 이미지 | QGraphicsView (줌/패닝) |
| 스레딩 | threading.Thread | QThread + Signal/Slot |
| 선택 모드 | 단일 선택 | ExtendedSelection (다중/범위) |
| 아웃라인 | 미지원 | 지원 (토글) |
| Unity Export | 미지원 | 지원 |
| PSD 히스토리 | 미지원 | QSettings 영속 저장 |
| 성능 | 레이어 수에 비례하여 느려짐 | 레이어 수 무관 (가상화) |
