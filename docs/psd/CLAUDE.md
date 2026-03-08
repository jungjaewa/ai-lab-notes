# PSD Layer Exporter - Project Overview

이 프로젝트는 Photoshop PSD 파일의 레이어를 개별 이미지로 추출하고 이름을 변경하는 도구 모음입니다.
2D 게임 캐릭터 리깅/애니메이션(Spine 등) 워크플로우에 최적화되어 있습니다.

## 도구 구성

### 1. psd_extractor_gui_qt.py (Qt GUI - 권장)
- **PySide6 기반 고성능 GUI** (CustomTkinter 대비 대폭 성능 개선)
- Photoshop 스타일 다크 테마 (Fusion + QPalette + QSS)
- psd_extractor.py의 핵심 로직을 import하여 사용
- 실행: `python psd_extractor_gui_qt.py`

#### 주요 특징
- **가상화 레이어 리스트**: QListView + QAbstractListModel + QStyledItemDelegate (paint 기반, 수백 행도 동일 속도)
- **트리 뷰 모드**: Group 버튼으로 플랫/트리 토글. 그룹 폴더 헤더(20px) + 들여쓰기로 계층 구조 표시. 그룹 헤더 폰트는 레이어명과 동일 (Segoe UI 9pt, 색상 #b0964a). 플랫 모드에서는 그룹 경로 숨김 (1줄 표시)
- **레이어 표시 토글**: Layer 버튼으로 아트 레이어 표시/숨김. 트리 모드에서는 그룹 헤더만 남고, 플랫 모드에서는 빈 목록. 기본값 ON. 세션 저장에 포함
- **그룹 접기/펼치기**: 트리 모드에서 그룹 헤더 클릭 시 하위 레이어 접기/펼치기 토글. 접힌 그룹은 ▶ 아이콘, 펼친 그룹은 ▼ 아이콘. 세션 저장 시 접힌 상태 보존
- **PSD 실시간 감시**: QFileSystemWatcher로 PSD 파일 변경 자동 감지 → 300ms 딜레이 후 자동 reload. Refresh 버튼으로 수동 reload 가능
- **프로젝트 프리셋**: 프로젝트별 Export 경로 + Unity 타입(UGUI/NGUI) 저장/전환 (콤보+✎ 매니저). QSettings 영속화. 4개 기본 프로젝트 (포커 PC/모바일=NGUI, 바둑 PC/모바일=UGUI). 프로젝트 선택 시 Unity 타입 자동 전환. 프로젝트 경로 + PSD명 조합으로 output 경로 자동 결정. 세션에 project_name 저장. Project Manager 다이얼로그에서 UGUI/NGUI 드롭다운 색상 구분 (UGUI=#4FC1E9, NGUI=#8CC152). **unity_type 데이터 격리**: Output 패널의 UGUI/NGUI 세그먼트 변경은 프로젝트 데이터에 반영하지 않음 — Project Manager 다이얼로그만이 프로젝트의 unity_type 변경 가능 (의도치 않은 데이터 변경 방지)
- **Auto Export**: PSD 변경 감지 시 자동 Export (세션 복원 후 500ms 딜레이). Export 패널 체크박스로 ON/OFF. 세션에 auto_export 상태 저장
- **가시성 연동**: 눈 아이콘 OFF 레이어는 이름이 dim 처리 (#666666), 머지 프리뷰에서 즉시 제외
- **프리뷰**: QGraphicsView + QGraphicsScene (1:1 기본 표시, 휠 줌 10%~1600%, 더블클릭 100% 리셋, Fit 버튼)
- **다중 선택 프리뷰**: Ctrl+Click / Shift+Click으로 여러 레이어 선택 시 PSD 좌표 기준으로 합성하여 프리뷰 표시 (레이어 뎁스 순서 유지)
- **머지 프리뷰**: PSD 로드 시 `psd.topil()` (내장 플래트 이미지)로 즉시 표시 → `composite()` 대비 ~90배 빠름
- **호버 프리뷰**: 레이어 위에 마우스 호버 → 머지 이미지를 Dim 처리 + 호버 레이어만 100% 표시. 클릭 시 solo 프리뷰. 호버 감지 범위는 레이어명 영역까지만 (rename 입력란 제외)
- **줌 유지**: 레이어 전환/호버 시 현재 줌 레벨 유지 (QGraphicsPixmapItem.setPixmap으로 in-place 교체)
- **프리뷰 오버레이 UI**: 프리뷰 영역 내부에 떠있는 반투명 오버레이로 컨트롤 배치
  - **하단 가운데**: Tint | BG | Dim (배경색, 투명도 조절)
  - **상단 오른쪽**: 줌% | ✛(십자선) | ◎(피봇) | ▢(아웃라인) | Info | Fit
- **배경색 선택**: 6종 프리셋 (투명/흰/검/빨/초/파) + 커스텀 컬러 피커. 투명 배경은 체커보드 표시
- **Dim 설정**: 호버 시 비활성 레이어의 투명도(0~100%) 슬라이더 + Tint 단색 모드 (색상 선택 가능). Dim 라벨 더블클릭 시 기본값 30% 복원
- **PSD 정보 오버레이**: 프리뷰에서 Tab 키 → 파일명, 크기, 레이어 정보를 좌상단에 토글 표시
- **레이어 정보 오버레이**: 프리뷰 이미지 아웃라인 하단 가운데에 레이어명/사이즈 표시 (drawForeground). Info 버튼으로 토글
- **십자선 오버레이**: 프리뷰 이미지 중심에 십자선 표시. ✛ 버튼으로 토글
- **피봇 마커 오버레이**: Pivot 콤보 선택 시 프리뷰 이미지 위에 피봇 위치를 빨간 십자+원 마커로 표시. QGraphicsLineItem + QGraphicsEllipseItem (cosmetic pen). PSD 로드/레이어 전환/줌 시 유지. Pivot 변경 시 즉시 갱신. 상단 오버레이의 피봇 토글 버튼(기본 ON)으로 표시/숨김
- **아웃라인 토글**: 프리뷰 이미지 경계선 표시/숨김 (기본 ON, #515151, cosmetic pen)
- **다크 컬러 다이얼로그**: Tint/BG 커스텀 색상 선택 시 QColorDialog에 다크 테마 적용
- **로그 패널 접기**: 기본 숨김, Row3 오른쪽 Log 체크박스로 토글 + × 버튼으로 로그 내용 삭제
- **스레딩**: QThread + Worker (export), QRunnable + QThreadPool (썸네일/프리로드/머지 생성/Ollama 번역)
- **PSD 파일 히스토리**: 편집 가능 QComboBox + QSettings 영속 저장
- **세션 자동 저장/복원**: PSD 파일 옆에 `.session.json` 저장. PSD 로드 시 세션 자동 복원. PSD 전환/앱 종료 시 자동 저장. 체크/가시성/rename/트리모드/접힌그룹/Rename설정/Format/Merge/Quality/Padding/Unity/UGUI·NGUI/Pivot/Auto Ver/Output경로/프리뷰BG/Dim/Tint/Log/Layer표시 보존. Restore 버튼으로 세션 적용 전 원본 PSD 상태 복원
- **Rename Prefix/Find/Replace 더블클릭**: 빈 필드 더블클릭 시 기본값 "fxt_" 자동 입력 (Prefix, Find, Replace 공통)
- **Rename 중복 감지**: 동일한 rename 이름이 2개 이상이면 빨간색(#e05050)으로 표시. 실시간 갱신
- **원본 레이어명 중복 경고**: PSD에서 동일한 레이어명이 2개 이상이면 주황색(#e0a050)으로 표시 + rename 필드에 "⚠ duplicate name" 플레이스홀더
- **Auto (KR→EN) Rename**: Ollama/Groq LLM으로 한글 레이어명을 영문 snake_case로 자동 번역. 딕셔너리 우선 + 복합어 분리 + 혼합 이름 분해 + 캐시 + LLM 폴백. 그룹명 컨텍스트(즉시 부모만) 전달로 동음이의어 구분 (예: 팔/위→arm_upper). 그룹명=레이어명일 때 컨텍스트 생략 (중복 방지). 그룹명에는 prefix 미적용 (fxt_ 제외). noun_modifier 어순 (명사 우선: arm_upper, item_inner). 영어 이름은 prefix만 적용 (ribbon_01→fxt_ribbon_01). 혼합 이름(리본end)은 세그먼트 분리 후 사전 변환. 네이밍 규칙: [docs/naming_convention.md](docs/naming_convention.md)
- **Ollama/Groq Provider 선택**: Ollama(로컬) 또는 Groq(클라우드) 선택 가능. Groq는 무료 tier로 32B 모델 사용, 동적 모델 목록 API 조회, 추천 모델 초록색 표시, 토큰 사용량 실시간 표시
- **Ollama 모델 프리로드**: 앱 UI 표시 3초 후 백그라운드에서 모델을 GPU에 미리 로드 (콜드 스타트 방지). 앱 부하 없음, Ollama 서버 측에서만 메모리 사용
- **Ollama 상태 애니메이션**: 모델 로딩/번역 중 `·` → `··` → `···` 순환 애니메이션 표시 (400ms 간격). 상태 라벨에 모델명 항상 표시 ("Ready (qwen2.5:3b)")
- **그룹 리네임**: 트리 모드에서 그룹 헤더에 rename 입력란 표시. 클릭으로 직접 편집 가능. Auto (KR→EN) 모드에서 한글 그룹명도 자동 번역 + `_group` 서픽스 자동 추가 (AI 구분용). 세션 저장 시 보존. 동일 이름 그룹도 경로(path-tuple) 기반으로 독립 rename 가능
- **그룹 rename 중복 감지**: 동일 rename 이름의 그룹이 2개 이상이면 빨간색(#e05050)으로 표시 + Export 시 경고. 경로 기반 카운팅으로 정확한 중복 판정
- **그룹 접기 하위 그룹 숨김**: 상위 그룹이 접힌 상태에서 하위 그룹 헤더도 완전히 숨김 (선조 접힘 검사 우선 적용)
- **Rename Post-Edit**: 1차 Rename 후 후처리 도구 행. Find/Replace(전체 또는 선택), +Prefix, +Suffix, +# 넘버링(01/001), 넘버링 방향(↓/↑), Reset, Apply Edit. Rename 패널 내 항상 표시
- **Rename 패널 분리**: Rename 도구 전체(Rename 행 + Edit 행)를 레이어 패널과 설정 패널 사이에 독립 QGroupBox로 분리
- **Undo/Redo**: Rename + Check + Visible + POT + Lock + Pivot + Crop 상태를 최대 30단계 스냅샷 저장 (9-tuple). Ctrl+Z/Ctrl+Shift+Z 또는 Edit 행 ←/→ 버튼. 모든 배치 작업(Auto/Sequential/Body Part/Find&Replace/Post-Edit/Clear) + 개별 체크/가시성/잠금 변경 + Restore/Deselect/Visible 버튼 모두 Undo 가능. PSD 전환 시 스택 초기화
- **Alt+더블클릭 단어 선택**: Rename/Find/Replace 편집 필드에서 Alt+더블클릭 시 `_` 구분자 기준 개별 단어만 선택 (_RenameLineEdit 서브클래스)
- **선택 기반 Rename**: 하이라이트된 레이어가 있으면 그것만 rename 적용, 없으면 전체 (Sequential/Body Part/Auto 모두)
- **Sequential Rename 그룹 헤더 제외**: 트리 모드에서 그룹 헤더가 시퀀스 번호를 소비하지 않음 (01부터 정상 시작)
- **선택 슬롯 (S1~S5)**: 레이어 선택 조합을 5개 슬롯에 저장/불러오기. QSettings 영속화. 빈 슬롯 Click=저장, 채워진 슬롯 Click=로드, Ctrl+Click=삭제
- **레이어 검색**: 프리뷰 하단 검색란으로 레이어명 실시간 필터링 (대소문자 무시, X 버튼으로 초기화). 플랫/트리 모드 모두 지원
- **Restore 버튼**: PSD 경로 행의 Refresh 왼쪽에 배치. PSD 로드 시점의 체크/가시성/rename 상태를 스냅샷으로 저장, 클릭 시 초기 상태 완전 복원 (레이어 순서/트리 모드/그룹 rename도 리셋)
- **QPainter 커스텀 아이콘**: 툴바 버튼(Order/Visible/Deselect/Group/Restore)에 QPainter로 직접 그린 14x14 벡터 아이콘 적용
- **선택 하이라이트 강화**: 선택된 레이어의 No 번호를 악센트 컬러(#2680EB)로 표시
- **단축키 도움말 팝업**: PSD 경로 행의 ? 버튼 호버 시 테두리 없는 단축키 설명 팝업 표시
- **Space 포커스 모드**: 프리뷰 영역에서 Space 키 → PSD 경로/Rename/Settings/Export 패널 모두 숨김 (레이어 리스트+프리뷰만 표시). 다시 Space 누르면 복원
- **Ctrl+Enter Edit 단축키**: Edit 행의 Find/Replace/Prefix/Suffix 필드에서 Ctrl+Enter → Apply Edit 실행
- **선택 하이라이트 색상**: 선택된 레이어 배경을 다크 네이비(#2d3748)로 표시하여 비선택과 확실히 구분
- **POT (Power of Two) Export**: 이미지 캔버스를 2의 거듭제곱 크기로 확장. Auto(자동 계산)/Manual(수동 지정) 모드. 배경색 4종(T/B/W/C, 16x16 색상 사각형 버튼). Nuke Reformat Resize Type 6종 (None/Fit/Fill/Width/Height/Distort) 지원. POT 계산: Ceil(항상 올림) / Nearest(가장 가까운 POT) 선택 가능. Settings POT는 프리뷰 설정, Export POT 체크박스로 실제 내보내기 제어. POT 이미지는 별도 `POT/` 서브폴더에 생성
- **레이어별 POT 토글**: Settings POT ON 시 레이어 목록에 POT 아이콘 열 표시. 개별 레이어 클릭으로 POT ON/OFF 토글. POT ON 레이어만 `POT/` 서브폴더에 Export. All/None 버튼으로 전체 일괄 설정. P키로 선택 레이어 일괄 토글. 세션 저장/Undo/Redo에 포함
- **POT 프리뷰 오버레이**: 프리뷰 이미지 위에 POT 크기 점선 사각형 + 크기 정보 표시. 레이어 선택/전환 시 자동 갱신. 상단 오버레이의 POT 토글 버튼으로 표시/숨김
- **POT Resize Type**: Nuke Reformat 노드 기준 — None(스케일 없이 중앙 배치), Fit(전체 보이도록 균일 축소), Fill(캔버스 완전 채우기), Width/Height(축 맞춤), Distort(비균일 스케일로 정확히 채움, 비율 무시)
- **다중 배율 동시 Export**: 1x, 0.75x, 0.5x 배율 체크박스. 다중 배율 시 배율별 서브폴더 (`1_00x/`, `0_75x/`, `0_50x/`) 생성
- **PNG 압축 레벨**: Fast(1) / Bal(6) / Best(9) 세그먼트 선택
- **OxiPNG 무손실 최적화**: pyoxipng 라이브러리로 Pillow 대비 15~40% 파일 크기 축소. 미설치 시 자동 비활성화 + Pillow 폴백. 설치 시 기본 ON
- **색상 모드 선택**: RGBA / RGB / Gray 콤보. JPEG 시 RGBA 비활성화
- **Rename 중복 정보 표시**: PSD 정보 바에 hidden/duplicate 개수를 색상별로 표시 (HTML 리치 텍스트, 구분선 #555555)
- **LLM 번역 안정성 강화**: Qwen3 `/no_think` 프롬프트, 코드 블록 제거, 추론 텍스트 필터링, `<|think|>` 태그 지원
- **Rename 열 너비 드래그**: 레이어명과 rename 입력란 경계를 마우스로 드래그하여 rename 열 너비 조절. 세션 저장에 포함
- **Unity Export 폴더 자동 접미사**: Unity ON 시 출력 폴더명에 `_UGUI` 또는 `_NGUI` 접미사 자동 삽입 (버전 앞에 위치). 예: `260225_giftBox_UGUI_v1`. Output 경로가 Unity 모드에 따라 실시간 갱신
- **Auto Version**: 출력 폴더가 이미 존재하면 버전을 자동 증가하여 새 폴더 생성 (`_v1` → `_v2`). Export 행의 Auto Ver 체크박스로 제어. QSettings 전역 저장
- **Output 경로 Unity 연동**: Unity ON → 프로젝트 경로 적용 (`_apply_project_path()`), Unity OFF → PSD 파일 경로로 복원 (`_psd_default_dir`). `_on_unity_toggled()` 메서드로 전환. `_output_base_dir`에 원본 경로 보존, `_compute_export_dir()`로 변환 표시
- **Output 폴더 존재 인디케이터**: Browse 왼쪽 QCheckBox(disabled)로 출력 폴더 존재 여부 실시간 표시. QFileSystemWatcher로 부모 디렉토리 감시하여 외부 생성/삭제 즉시 반영
- **Output 폴더 삭제**: Delete 버튼으로 출력 폴더 삭제 (다크 스킨 확인 팝업). 폴더 존재 시만 표시
- **Open Folder**: PSD 파일이 있는 위치의 폴더 열기
- **UGUI/NGUI 색상 구분**: UGUI 활성 시 스카이 블루(#4FC1E9), NGUI 활성 시 그린(#8CC152)으로 텍스트 색상 분리
- **다크 스킨 다이얼로그**: 삭제 확인 팝업에 다크 테마 적용 (#2b2b2b 배경, #e0e0e0 텍스트)
- **Rename Lock (잠금)**: 레이어/그룹별 rename 잠금. 잠금된 항목은 모든 배치 rename 작업(Auto/Sequential/Body Part/Find&Replace/Post-Edit/Clear)에서 제외. 개별 수동 편집도 차단. L 키로 선택 레이어/그룹 일괄 토글 (하나라도 미잠금→전부 잠금, 전부 잠금→전부 해제). rename 필드에 자물쇠 아이콘(#2680EB) + dim 텍스트(#909090). 레이어: `_art_locked` 배열, 그룹: `_group_locked` dict(경로tuple→bool). Undo/Redo(7-tuple)/세션 저장에 포함. Restore 시 초기화
- **Per-Layer Pivot (레이어별 피봇)**: 각 레이어마다 독립적인 피봇 포인트(정수 좌표) 설정. 프리뷰에서 드래그/Alt+Click으로 위치 지정, 9-point 스냅(3×3 그리드), 더블클릭으로 리셋. `_art_pivot` 배열 (POT/Lock과 동일한 듀얼 배열 패턴). Unity RectTransform.pivot에 per-layer 값 반영. JSON에 `pivot_local` 필드 추가. Undo/Redo(9-tuple)/세션 저장에 포함. Restore 시 초기화
- **Per-Layer Crop (레이어별 자동 크롭)**: 레이어별 투명 영역 자동 크롭 ON/OFF. Settings Row1 `Crop` 체크박스(전체 ON/OFF) + Threshold 스핀박스(0~254, 기본 10). `_art_crop` 배열 (듀얼 배열 패턴). C 키로 선택 레이어 개별 토글. 프리뷰에 크롭 오버레이 표시 (dim 영역 + 주황색 점선 경계 + 크기 정보). Export 시 `crop_transparent()` 함수로 실제 크롭 적용, Unity 좌표 보정 (`crop_offsets`). Undo/Redo(9-tuple)/세션 저장에 포함. Restore 시 초기화
- **PSD Export (바이너리)**: rename된 레이어명으로 PSD 파일 직접 저장. psd-tools `psd.save()` 대신 바이너리 레벨 수정 (Pascal string + luni Unicode 블록만 변경, 나머지 원본 바이트 보존) — Photoshop 호환성 보장

#### GUI 레이아웃 (타이틀 없는 패널 구조)
```
+------------------------------------------------------------------+
| PSD Layer Extractor (Qt)                               [_][O][X]  |
+------------------------------------------------------------------+
| [경로 QComboBox(히스토리)] [Browse] │ [Restore] [Refresh] [?]       |
| 정보: ch.psd | 210x283 px | 23 layers                            |
+------------------------------------------------------------------+
| +-- QSplitter(H) -----------------------------------------------+|
| | QListView (가상화)          |                                  ||
| | [01][✓][eye][thumb] name    | QGraphicsView 프리뷰             ||
| | [02][✓][eye][thumb] name    |  ┌── 100%|✛|◎|▢|Info|Fit ─┐    ||
| | [03][ ][eye][thumb] name    |  │                          │    ||
| |  (dim name if eye off)      |  │    [Tab: PSD 정보]       │    ||
| |  ▼ Group Header (접기 가능) |  │                          │    ||
| |  │ [01] layer (들여쓰기)    |  │     layer info text      │    ||
| |                             |  └── Tint|BG|Dim ───────────┘    ||
| |                             | [Group][Layer]│[Order][Visible][Deselect]||
| |                             | [S1][S2][S3][S4][S5][검색란    ] ||
| +----------------------------+----------------------------------+|
+------------------------------------------------------------------+
| Rename [mode▼] [옵션 인라인] ... [Rename] [Clear]                 |
| [Ollama|Groq] [model▼] [Key][→][tokens] (Auto 모드)              |
| Edit [←][→]│[Find___]→[Replace___][All]│[+Prefix][+Suffix][+# ↓][Apply Edit][Reset]|
+------------------------------------------------------------------+
| Row1: Format [PNG▼] [✓Merge] | Quality | Padding | Color [RGBA▼] | [☐Crop][threshold] |
| ──────────────────────────── (구분선) ────────────────────────────── |
| Row2: [☐POT] [All][None] [Auto|Manual] [W▼ H▼] | BG [T][B][W][C] | [Reset All] |
| Row3: Resize Type [None▼] | Scale [✓1x][☐.75x][☐.5x] | [Ceil|Nearest] | PNG [Fast|Bal|Best] [☐OxiPNG] ── [☐Log][×] |
+------------------------------------------------------------------+
| [출력 경로] [●] [Delete] [Output Browse]                           |
| Project [포커 모바일▼][✎] │ [D:\02_GIT\...\Assets\_FX]              |
| [☐ Unity] [UGUI|NGUI] │ Pivot [Bottom-Center▼]  진행률 [☐Auto Export] [☐Auto Ver] [☐POT] [EXPORT] [PSD Export] | [Open Folder] |
| [QPlainTextEdit 로그] (기본 숨김, Log 체크 시 표시)               |
+------------------------------------------------------------------+
```

#### 프리뷰 동작
- **PSD 로드**: `psd.topil()`로 머지 이미지 즉시 표시 (딜레이 없음)
- **레이어 호버**: Dim 처리된 머지 배경 + 호버 레이어 100% 합성 (QPainter compositing)
- **단일 레이어 클릭**: 해당 레이어만 solo 프리뷰
- **다중 레이어 선택**: 선택된 레이어들을 PSD 좌표 기준으로 합성 프리뷰 (bottom→top 뎁스 순서 유지)
- **같은 레이어 재클릭**: 선택 해제 → 머지 프리뷰로 복귀
- **선택 없음**: 전체 머지 이미지 표시
- **줌 유지**: 레이어 전환/호버 시 현재 줌/스크롤 위치 완전 유지 (setPixmap in-place 교체)
- **Dim 슬라이더**: 호버 시 비활성 레이어 투명도 조절 (0~100%, 기본 30%, 라벨 더블클릭으로 리셋)
- **Tint 모드**: 비활성 레이어를 단색 실루엣으로 표시 (색상 선택 가능, QPainter CompositionMode_SourceIn)
- **BG 색상**: 프리뷰 배경을 투명(체커보드)/흰/검/빨/초/파/커스텀으로 변경

#### 키보드/마우스 동작
- **Ctrl+Z**: Undo (Rename/Check/Visible 상태 되돌리기)
- **Ctrl+Shift+Z**: Redo (Undo 되돌리기)
- **Ctrl+A**: 전체 레이어 선택 (하이라이트)
- **Ctrl+Click**: 다중 선택 추가/해제
- **Shift+Click**: 범위 선택 (하이라이트만, 체크 변경 없음)
- **Space**: 선택된 레이어 체크 토글 (다중 선택 시 일괄 처리)
- **E**: 선택된 레이어 가시성(눈) 토글 (다중 선택 시 일괄 처리)
- **P**: 선택된 레이어 POT 토글 (다중 선택 시 일괄 처리, Settings POT ON 시)
- **L**: 선택된 레이어 rename 잠금/해제 토글 (다중 선택 시 일괄 처리)
- **C**: 선택된 레이어 Crop 토글 (다중 선택 시 일괄 처리, Settings Crop ON 시)
- **A**: 레이어 선택 해제 (하이라이트만 해제, 체크 유지). 프리뷰 패널에서도 동일 동작
- **Tab (프리뷰 포커스)**: PSD 파일 정보 오버레이 토글 (파일명, 크기, 레이어 수)
- **Space (프리뷰 포커스)**: 포커스 모드 토글 (패널 숨김/표시)
- **Ctrl+Enter (Edit 필드)**: Apply Edit 실행
- **Alt+더블클릭 (Rename/Find/Replace 필드)**: `_` 구분자 기준 개별 단어 선택
- **체크박스 클릭**: 개별 체크 토글
- **휠 (프리뷰)**: 줌 (10%~1600%, 단계별)
- **더블클릭 (프리뷰)**: 100% 리셋
- **더블클릭 (레이어 빈 영역)**: PSD 파일 열기 다이얼로그
- **더블클릭 (PSD 경로란)**: 마지막 열었던 파일 자동 로드
- **더블클릭 (Rename Prefix/Find/Replace)**: 빈 필드에 기본값 "fxt_" 자동 입력
- **더블클릭 (Dim 라벨)**: Dim 값을 기본 30%로 복원

#### Export 동작
- EXPORT 클릭 → "Exporting..." (비활성) → 진행률 표시 → "Complete ✓" (초록, 2초) → "EXPORT" 복귀
- Merge 체크박스 ON 시 `_merged.png/jpg` 함께 내보내기
- Unity 체크박스 ON + UGUI/NGUI 모드 선택 + Pivot(9방향) 설정:
  - **UGUI**: `fxc_psdImporter_{name}.json` + `Editor/FXC_PSDImporter_{Stem}.cs` (Canvas+Image, PSD별 고유 클래스명)
  - **NGUI**: `fxc_psdImporter_{name}.json` + `Editor/FXC_PSDImporterNGUI_{Stem}.cs` (UISprite+Atlas+depth)
- **C# 고유 클래스명**: 출력 폴더명에서 PascalCase 접미사 생성 (예: `260225_giftBox_UGUI_v1` → `FXC_PSDImporter_260225GiftboxUguiV1`). 여러 PSD Export 시 네임스페이스 충돌 방지. 데이터 클래스(PSDLayout 등)는 Editor 클래스 내부에 중첩하여 전역 네임스페이스 충돌 방지
- **Pivot 시스템**: 9방향 피봇 콤보 (Top-Left ~ Bottom-Right, 기본 Bottom-Center). JSON v3에 pivot 좌표 포함, C# 임포터에서 동적 anchor 적용
- **파일명 충돌 방지**: 동일 레이어명이 있을 때 자동 접미사(_1, _2) 추가하여 파일 덮어쓰기 방지
- **Export 파이프라인**: Extract(RGBA) → Crop → Scale → Pad → POT → ColorMode → Save/OxiPNG
- **Export POT 분리**: Settings POT는 프리뷰 설정용, Export 버튼 왼쪽 POT 체크박스로 실제 내보내기 제어. POT 이미지는 `POT/` 서브폴더에 별도 생성 (기본 이미지는 항상 Pad만 적용)
- **다중 배율**: 배율별 서브폴더 구조, Unity JSON도 배율별 생성 (좌표 스케일 적용). C# 임포터는 1x에서만 1회 생성
- **Unity 폴더 접미사**: Unity ON 시 출력 폴더명에 `_UGUI`/`_NGUI` 자동 삽입 (기존 접미사 중복 방지, 버전 앞 위치). regex로 `_v\d+` 분리 후 삽입
- **Auto Version**: Export 시 폴더 존재하면 자동으로 `_v2`, `_v3` 등 증가. 버전 없는 PSD 파일에 Auto Ver ON 시 `_v1` 자동 추가. `_compute_export_dir()` 메서드로 경로 변환. 출력 경로에 실시간 반영
- **POT Info JSON**: POT Export 시 `POT/_pot_info.json` 자동 생성 (psd_file, pot_calc, resize_type, layers[{name,file,original{w,h},pot{w,h}}]). original = Pad 후 POT 전 크기 (Unity Quad 메쉬 크기)
- **FXC_MeshQuad C# 자동 생성**: POT Export + 1x 배율 시 `FXC_MeshQuad.cs` + `Editor/FXC_MeshQuadEditor.cs` 자동 출력 (미존재 시만). PSD별 고유 클래스명 (`.replace("FXC_MeshQuad", unique_cls)` 패턴)
- QThread Worker로 백그라운드 실행, UI 블로킹 없음

#### 다크 테마 컬러
```
#1e1e1e  → 윈도우/캔버스 배경
#2b2b2b  → 패널 배경
#323232  → 레이어 리스트 배경
#535353  → 입력 필드
#3c3c3c  → 테두리, 버튼 배경
#e0e0e0  → 기본 텍스트
#666666  → 비활성 텍스트 (눈 OFF 레이어명)
#b0964a  → 그룹 헤더 (트리 모드 폴더 아이콘/텍스트)
#e0a050  → 경고-약 (원본 레이어명 중복)
#e05050  → 경고-강 (Rename 중복 이름, 오류)
#6a8a3a  → 그룹 rename 텍스트
#2d3748  → 선택된 레이어 배경 (다크 네이비)
#2680EB  → 악센트 (Export 버튼, 체크박스)
#4FC1E9  → UGUI 활성 텍스트 (Unity 스카이 블루)
#8CC152  → NGUI 활성 텍스트 (소프트 그린)
#4ec94e  → 추천 모델 텍스트 (Groq 모델 드롭다운)
rgba(30,30,30,200) → 프리뷰 오버레이 배경
Segoe UI 9pt (시스템 폰트 통일)
```

### 2. psd_extractor_gui.py (GUI - 레거시 CustomTkinter)
- CustomTkinter 기반 GUI (기존 버전, 유지만 함)
- 위젯 생성 성능 이슈 있음 (Qt 버전 권장)
- 실행: `python psd_extractor_gui.py`

### 3. psd_extractor.py (CLI - 개발자/자동화 권장)
- **Photoshop 불필요**. psd-tools + Pillow로 PSD를 직접 파싱
- 20개 레이어 기준 **~3.6초** (Photoshop 방식 대비 41배 빠름)
- Qt GUI와 CLI 모두 이 파일의 핵심 함수를 공유: `collect_layers`, `extract_layer_image`, `apply_padding`, `apply_pot`, `next_pot`, `nearest_pot`, `convert_color_mode`, `save_png_oxipng`, `sanitize_filename`, `_get_group_path`, `collect_layer_metadata`, `crop_transparent`
- 자세한 내용: [docs/psd_extractor.md](docs/psd_extractor.md)

### 4. psd_ai_interface.py (AI Agent 인터페이스)
- psd_extractor.py 백엔드를 그대로 import하여 AI가 호출하기 최적화된 구조화된 입출력 제공
- **ExportTask** (dataclass) — 인간 GUI의 42개 위젯을 1개 구조체로 통합
- **PSDAgent.run()** — 태스크 실행 → ExportResult(dataclass) 반환 (JSON 직렬화 가능)
- **inspect_psd()** — PSD 구조 분석 → PSDInfo(dataclass) 반환 (레이어명/크기/위치/그룹/이펙트)
- **프리셋**: spine_character, unity_ngui_fx, unity_ugui, web_assets, quick_check
- **CLI**: `python psd_ai_interface.py inspect ch.psd`, `run ch.psd --preset unity_ngui_fx`, `--dry-run`
- **YAML/JSON 설정 파일** 지원: `run ch.psd --config task.yaml`
- **수치 기반 검증**: ExportResult.validation (파일 존재, 빈 파일, 이름 충돌, 크기 이상 자동 검사)
- 프리뷰/Undo/세션/슬라이더 없음 — AI에게 불필요한 시각적 요소 제거
- 실행: `python psd_ai_interface.py run ch.psd --preset quick_check`
- 상세 비교: [docs/human_vs_ai_workflow.md](docs/human_vs_ai_workflow.md)

### 5. layer_exporter.py (Photoshop COM)
- Photoshop이 실행 중이어야 함 (COM 연결)
- Python에서 eval_javascript()로 JSX 실행
- 20개 레이어 기준 ~148초
- 자세한 내용: [docs/layer_exporter.md](docs/layer_exporter.md)

### 5. LayerExporter.jsx (Photoshop 내장 스크립트)
- Photoshop File > Scripts > Browse로 실행
- ScriptUI 다이얼로그 제공
- 자세한 내용: [docs/layer_exporter.md](docs/layer_exporter.md)

## 프로젝트 구조

```
d:\_AI Tool\PSD\
  psd_extractor_gui_qt.py # GUI (PySide6, 권장)
  psd_extractor_gui.py    # GUI (CustomTkinter, 레거시)
  psd_extractor.py        # Standalone CLI (psd-tools, 백엔드 공유)
  psd_ai_interface.py     # AI Agent용 인터페이스 (구조화된 입출력)
  photoshop_theme.json    # CTk GUI 테마 (Photoshop 컬러 팔레트)
  layer_exporter.py       # Photoshop COM 기반 CLI
  LayerExporter.jsx       # Photoshop 내장 스크립트 (ScriptUI)
  rename_config.json      # 레이어 이름 변경 설정 (배열 형식)
  requirements.txt        # Python 의존성
  CLAUDE.md               # 프로젝트 개요 (AI 컨텍스트)
  docs/
    README.md             # 도구 가이드 총 목차
    psd_extractor_gui_qt.md  # Qt GUI 상세 사용법
    psd_extractor_gui_ctk.md # CTk GUI 상세 사용법
    psd_extractor.md      # Standalone CLI 상세 문서
    layer_exporter.md     # Photoshop 기반 도구 상세 문서
    dev_journal.md        # 개발 일지 (Phase별 의사결정 기록)
    unity_dev_history.md  # Unity UGUI Import 개발 히스토리
    human_vs_ai_workflow.md # 인간 vs AI 워크플로우 비교 토론 기록
  _sample/
    ch.psd                # 테스트용 캐릭터 PSD (23레이어)
    ch_01.psd             # 테스트용 PSD 변형본
```

## 핵심 기능

- **레이어 목록 조회**: PSD 내 모든 레이어의 이름, 가시성, 계층 구조 출력
- **트리 뷰**: 그룹 폴더 헤더 + 들여쓰기로 계층 표시, 플랫 모드에서는 그룹 경로 2줄 표시
- **가시성 연동**: 눈 OFF → 레이어명 dim 처리 + 머지 프리뷰에서 즉시 제외
- **레이어 이름 변경**: 4가지 모드 (Manual/Sequential/Body Part/Auto KR→EN), 한글 바디파트 자동 매핑 + Ollama LLM 번역
- **Rename 중복 감지**: 동일 export name이 2개 이상이면 빨간색으로 실시간 표시
- **개별 레이어 PNG/JPEG 내보내기**: 체크 선택, Visible 필터, 다중 선택 지원
- **다중 선택 합성 프리뷰**: Ctrl/Shift 클릭으로 여러 레이어 선택 시 PSD 원본 뎁스 순서로 합성 프리뷰
- **Merge 이미지**: 전체 레이어 합성 이미지 내보내기 (옵션)
- **Unity UGUI Export**: 레이어 위치/크기/계층 메타데이터 JSON + Unity C# 임포터 스크립트 내보내기
- **Pad 패딩**: 각 축 +N px 추가. Even 체크 ON(기본) 시 홀수면 +1로 짝수 맞춤, OFF 시 홀수 유지
- **고정 패딩**: Width/Height 별도 지정
- **레이어별 자동 크롭**: 투명 영역 자동 제거 (threshold 조절 가능). 프리뷰 오버레이로 크롭 결과 확인. Unity 좌표 자동 보정
- **POT 캔버스 확장**: Power of Two 크기로 확장 + Nuke Reformat Resize Type 6종
- **다중 배율 Export**: 1x/0.75x/0.5x 동시 내보내기
- **OxiPNG 최적화**: 무손실 PNG 압축 (pyoxipng)
- **색상 모드**: RGBA/RGB/Grayscale 선택
- **프리뷰**: 머지 즉시 표시 (topil), 호버 Dim 프리뷰, solo/다중 합성 프리뷰, 줌/패닝, 체커보드/단색 배경, 아웃라인 토글
- **프리뷰 오버레이**: 하단(Tint|BG|Dim), 상단(줌%|영역|Fit), Tab(PSD 정보)이 프리뷰 내부에 떠있는 형태
- **Dim 프리뷰**: 호버 시 비활성 레이어 투명도 슬라이더 (0~100%) + Tint 단색 모드 (QColorDialog)
- **배경색 프리셋**: 투명(체커보드)/흰/검/빨/초/파 + 커스텀 컬러 피커
- **로그 패널 접기**: 기본 숨김, Row3 오른쪽 Log 체크로 토글 + × 버튼으로 로그 클리어
- **PSD 실시간 감시**: Photoshop에서 저장 시 자동 reload (QFileSystemWatcher)
- **세션 자동 저장/복원**: PSD 옆에 `.session.json` 자동 저장/복원 (체크, 가시성, rename, 트리 상태, Rename 설정, Format/Padding/Unity/Pivot/프리뷰BG/Dim/Tint 등 전체 설정). PSD 로드 시 자동 복원, PSD 전환/앱 종료 시 자동 저장
- **Refresh 버튼**: PSD 경로 행의 Browse 오른쪽, 수동 PSD reload
- **경로 정규화**: QFileDialog 경로를 Windows 표준 백슬래시(\)로 변환

## Qt GUI 아키텍처 (psd_extractor_gui_qt.py)

```
PSDExtractorQt (QMainWindow)
├── LayerListModel (QAbstractListModel)
│   ├── _art_layers / _art_checked / _art_thumbnails / _art_rename (소스 배열)
│   ├── _layers / _checked / _thumbnails / _rename (뷰 배열, 트리 모드 시 그룹 헤더 포함)
│   ├── _initial_checked / _initial_visible — PSD 로드 시점 스냅샷 (Restore용)
│   ├── _search_text — 검색 필터 문자열 (빈 문자열이면 전체 표시)
│   ├── _collapsed_groups — 접힌 그룹 경로 집합 (set of tuple)
│   ├── _rename_duplicates — 중복된 rename 이름 집합 (실시간 갱신)
│   ├── _orig_name_duplicates — 원본 레이어명 중복 집합 (주황색 경고용)
│   ├── _group_rename_map — 그룹경로tuple→변경명 매핑 (dict, 동일명 그룹 독립 rename)
│   ├── _tree_guide_cache — 트리 가이드라인 사전 계산 캐시 (frozenset per row)
│   ├── set_tree_mode() → _rebuild_view() → _build_tree_view() (그룹 헤더 삽입)
│   ├── set_search_text() → _rebuild_view() (검색 필터 적용)
│   ├── toggle_group_collapsed(row) — 그룹 헤더 접기/펼치기 토글
│   ├── duplicates_changed (Signal) — 중복 개수 변경 시 발신 → info bar 갱신
│   ├── _refresh_rename_duplicates() — _art_rename 중복 검사 + _rename_duplicates 갱신
│   ├── _refresh_orig_name_duplicates() — 원본 레이어명 중복 검사
│   ├── is_rename_duplicate(name) / is_orig_name_duplicate(name) — 중복 확인
│   ├── set_group_rename() / get_group_rename() / get_group_rename_map() — 그룹 rename 관리
│   ├── set_show_art_layers() — 아트 레이어 표시/숨김 토글 (Layer 버튼)
│   ├── restore_initial_state() — 초기 체크/가시성/rename 복원
│   ├── is_group(row) — 해당 행이 그룹 헤더인지 확인
│   ├── set_thumbnail_by_art_idx() — 아트 인덱스 기준 썸네일 설정 (트리 모드 안전)
│   ├── _art_pot / _pot — 레이어별 POT 토글 상태 (소스/뷰 배열)
│   ├── _initial_pot — PSD 로드 시점 POT 스냅샷 (Restore용)
│   ├── _art_locked / _locked — 레이어별 rename 잠금 상태 (소스/뷰 배열)
│   ├── _initial_locked — PSD 로드 시점 잠금 스냅샷 (Restore용)
│   ├── _art_pivot / _pivot — 레이어별 피봇 좌표 ((int,int) or None) (소스/뷰 배열)
│   ├── _initial_pivot — PSD 로드 시점 피봇 스냅샷 (Restore용)
│   ├── _art_crop / _crop — 레이어별 자동 크롭 ON/OFF (소스/뷰 배열)
│   ├── _initial_crop — PSD 로드 시점 크롭 스냅샷 (Restore용)
│   └── Roles: Checked, Visible, Thumbnail, Rename, LayerInfo, OrigNo, IsGroup, TreeDepth, Pot, Lock, Pivot, Crop
├── LayerDelegate (QStyledItemDelegate)
│   ├── 그룹 헤더 행: ▼/▶ 아이콘 (#b0964a) + 원본 그룹명 + rename 입력란 (클릭 편집)
│   ├── 아트 레이어 행: No + 체크박스 + 눈 + [POT] + 썸네일 + 이름 (1줄 표시, 그룹 경로 숨김)
│   ├── _pot_column_visible — POT 아이콘 열 표시 플래그 (Settings POT 연동)
│   ├── _crop_column_visible — Crop 인디케이터 표시 플래그 (Settings Crop 연동)
│   ├── _rename_col_w — rename 열 너비 (드래그 조절 가능, 세션 저장)
│   ├── 선택 하이라이트: No 번호를 악센트 컬러(#2680EB)로 표시
│   ├── Rename 중복: rename 텍스트가 중복이면 빨간색(#e05050) 표시
│   ├── 원본명 중복: 원본 레이어명이 중복이면 주황색(#e0a050) 표시
│   └── 가시성 OFF → 이름 색상 dim (#666666)
├── _RenameLineEdit (QLineEdit) — Alt+더블클릭 시 _ 구분자 기준 단어 선택
├── LayerListView (QListView) — ExtendedSelection, 키보드/마우스/호버 핸들링
│   ├── preview_requested (Signal(list)) — 선택 변경 시 행 리스트 전달
│   ├── hover_changed (Signal(int)) — 마우스 호버/떠남 → Dim 프리뷰
│   ├── state_will_change (Signal()) — Check/Visible/Rename 변경 직전 → Undo 스냅샷
│   ├── selectionChanged() — 단일/다중 선택 감지 → preview_requested 발신
│   └── setMouseTracking(True) — mouseMoveEvent/leaveEvent로 호버 감지
├── PreviewView (QGraphicsView) — 체커보드/단색 배경, 줌, 아웃라인, 오버레이
│   ├── _info_overlay (QLabel) — Tab 토글 PSD 정보 (좌상단)
│   ├── _bottom_bar (QWidget) — Tint | BG | Dim 오버레이 (하단 가운데)
│   ├── _top_bar (QWidget) — 줌% | ✛ | ◎ | ▢ | Info | Fit 오버레이 (상단 오른쪽)
│   ├── _layer_info_text / _layer_info_visible — 레이어 정보 오버레이 (이미지 하단)
│   ├── _crosshair_visible — 십자선 토글 상태
│   ├── _pivot_items / _pivot_pos — 글로벌 피봇 마커 아이템 + 위치 비율 (px, py)
│   ├── _layer_pivot_items / _layer_snap_items — 레이어별 피봇 마커 + 9-point 스냅 인디케이터
│   ├── _dragging_pivot — 레이어 피봇 드래그 중 플래그
│   ├── layer_pivot_changed (Signal(object)) — 레이어 피봇 변경 시그널 ((lpx, lpy) or None)
│   ├── set_layer_pivot() — 레이어별 피봇 마커 설정 (9-point 스냅 + 좌표 텍스트)
│   ├── _crop_bbox / _crop_overlay_visible — 크롭 영역 바운딩박스 + 오버레이 표시 플래그
│   ├── set_crop_bbox() — 크롭 오버레이 설정 (dim 영역 + 주황 점선 경계 + 크기 텍스트)
│   ├── drawForeground() — 레이어 정보 + 십자선 + 크롭 오버레이를 뷰포트/씬 좌표로 그림
│   ├── set_bg_color() — 투명(None)/단색(QColor) 배경 전환
│   ├── set_psd_info() — Tab 오버레이 텍스트 설정
│   ├── set_layer_info() — 레이어 정보 텍스트 설정 (이미지 하단 가운데)
│   ├── set_pivot() / _update_pivot_marker() — 피봇 마커 위치 설정/갱신
│   ├── set_pot_rect() / set_pot_info() — POT 크기 점선 사각형 + 정보 텍스트
│   ├── _pot_item (QGraphicsRectItem) — POT 프리뷰 오버레이 (점선, cosmetic pen)
│   ├── toggle_layer_info() / toggle_crosshair() — Info/십자선 토글
│   ├── deselect_requested (Signal()) — ` 키 → 레이어 선택 해제
│   ├── event() 오버라이드 — Tab 키 가로채기 (Qt 포커스 전환 방지)
│   └── _reposition_overlays() — resizeEvent 시 오버레이 위치 재계산
├── SegmentedButton (QWidget) — QButtonGroup + checkable QPushButton
├── PreloadTask (QRunnable) — 백그라운드 레이어 이미지 캐시 (_cached_img)
├── ThumbnailTask (QRunnable) — 썸네일 생성 (art index 기준)
├── MergedTask (QRunnable) — 백그라운드 머지 이미지 생성 (폴백)
├── ExportWorker (QObject) — QThread에서 export 실행
├── QFileSystemWatcher — PSD 파일 변경 감시, 자동 reload
├── _sel_slots [None]*5 — 선택 슬롯 (레이어 이름 리스트, QSettings 영속화)
├── _translation_cache — Ollama 번역 캐시 (그룹 컨텍스트 포함 키)
├── _undo_stack / _redo_stack — Undo/Redo 스냅샷 스택 (rename+checked+visible+pot+locked+group_locked+pivot+crop, 9-tuple, 최대 30단계)
├── _undo_batch — 배치 작업 중 개별 스냅샷 방지 플래그
├── _ollama_dot_timer (QTimer) — 상태 라벨 순환 애니메이션 (400ms)
├── _auto_provider (SegmentedButton) — Ollama/Groq Provider 선택
├── _groq_key_btn / _groq_link_btn — Groq API 키 관리 + 콘솔 링크
├── _groq_usage_label / _groq_tokens_used — Groq 토큰 사용량 표시
├── _ColorItemDelegate — QComboBox 모델 항목별 색상 (추천 모델 초록색)
├── _help_popup (QLabel) — ? 버튼 호버 시 단축키 설명 팝업
├── _make_btn_icon() — QPainter로 커스텀 아이콘 생성 헬퍼
├── _icon_order / _icon_visible / _icon_deselect / _icon_tree / _icon_restore — 아이콘 드로잉 함수
├── _session_path() / _save_session() / _load_session() — 세션 JSON 저장/복원
├── _translate_korean_names() / _call_ollama() — Ollama 한글→영문 번역
├── _unity_type_seg (SegmentedButton) — UGUI/NGUI UI 타입 선택
├── _pivot_combo (QComboBox) — 9방향 피봇 선택 (Top-Left ~ Bottom-Right, 기본 Bottom-Center)
├── _on_pivot_changed() — Pivot 콤보 변경 → preview_view.set_pivot() 갱신 (버튼 ON 시만)
├── _pivot_btn (QPushButton) — 피봇 마커 표시/숨김 토글 (기본 ON)
├── _on_pivot_btn_toggled() — 피봇 마커 토글 → set_pivot()/set_pivot(None)
├── _PIVOT_MAP (dict) — 피봇명→(px,py) 매핑
├── _UNITY_IMPORTER_CS (str) — UGUI EditorWindow 스크립트 템플릿 (FXC_PSDImporter, PivotInfo 클래스 포함)
├── _UNITY_IMPORTER_NGUI_CS (str) — NGUI MonoBehaviour 스크립트 템플릿 (FXC_PSDImporterNGUI)
├── _UNITY_IMPORTER_NGUI_EDITOR_CS (str) — NGUI Editor 스크립트 템플릿 (Setup Textures/Make Atlas/Import to Scene/Import All, fxRoot_anim, bbox 그룹 피봇, fxt_→s_ 변환, Snap to Pixel)
├── _FXC_MESHQUAD_CS (str) — FXC_MeshQuad Root 전용 Runtime 템플릿 (potInfoJson, baseDepth, depthStep)
├── _FXC_MESHQUAD_EDITOR_CS (str) — FXC_MeshQuadEditor 템플릿 (Setup→UIShaderWidget, JSON auto-discovery, MeshRenderer 직접 노출, fxt_→fxs_ 변환)
├── _pot_check / _pot_mode_seg / _pot_w_combo / _pot_h_combo — POT 설정 위젯
├── _pot_bg_buttons / _pot_bg_custom_btn / _pot_bg_value — POT BG 색상 사각형 버튼 (T/B/W + Custom)
├── _pot_calc_seg (SegmentedButton) — POT 계산 방식 (Ceil/Nearest)
├── _pot_all_btn / _pot_none_btn — POT 레이어 일괄 설정 버튼
├── _pot_resize_combo (QComboBox) — Nuke Reformat Resize Type (None/Fit/Fill/Width/Height/Distort)
├── _pot_preview_btn (QPushButton) — 프리뷰 POT 오버레이 토글
├── _export_pot_check (QCheckBox) — Export 버튼 옆 POT 내보내기 토글
├── _update_pot_preview() — POT 프리뷰 오버레이 갱신 (레이어 선택/설정 변경 시)
├── _scale_075_check / _scale_050_check — 다중 배율 체크박스
├── _png_compress_seg (SegmentedButton) — PNG 압축 레벨 (Fast/Bal/Best)
├── _oxipng_check (QCheckBox) — OxiPNG 토글
├── _color_mode_combo (QComboBox) — 색상 모드 (RGBA/RGB/Gray)
├── _crop_check (QCheckBox) — 레이어별 자동 크롭 ON/OFF (전체 일괄 토글)
├── _crop_threshold_spin (QSpinBox) — 크롭 Alpha threshold (0~254, 기본 10)
├── _on_crop_toggled() — Crop 체크 변경 → delegate/view 동기화 + 전체 레이어 ON/OFF
├── _update_crop_preview() — PIL getbbox()로 크롭 영역 계산 → preview_view.set_crop_bbox()
├── _refresh_crop_overlay() — CropRole dataChanged/threshold 변경 시 오버레이 갱신
├── _update_info_label() — PSD 정보 바 HTML 갱신 (hidden/duplicate 카운트 포함)
├── _layer_btn (QPushButton, checkable) — 아트 레이어 표시/숨김 토글 (기본 ON)
├── _output_exists_dot (QLabel "●") — 출력 폴더 존재 dot 인디케이터 (초록#4ec94e/회색#666666)
├── _output_delete_btn (QPushButton) — 출력 폴더 삭제 (항상 표시, 폴더 존재 시만 활성)
├── _output_dir_watcher (QFileSystemWatcher) — 출력 폴더 부모 디렉토리 감시 (생성/삭제 실시간 감지)
├── _output_base_dir (str) — 원본 출력 경로 (Unity 접미사 적용 전 기본 경로)
├── _psd_default_dir (str) — PSD 파일 경로 기반 기본 출력 폴더 (Unity OFF 시 복원용)
├── _updating_output_display (bool) — output_entry textChanged 무한 루프 방지 플래그
├── _auto_ver_check (QCheckBox) — Auto Version 체크박스 (세션 저장, 경로 실시간 반영)
├── _auto_export_check (QCheckBox) — Auto Export 체크박스 (PSD 변경 감지 시 자동 Export)
├── _project_combo (QComboBox) — 프로젝트 프리셋 콤보 (포커 PC/모바일, 바둑 PC/모바일)
├── _project_path_label (QLineEdit, readOnly) — 현재 프로젝트 경로 표시
├── _projects (list[dict]) — 프로젝트 목록 [{"name": str, "path": str}], QSettings 영속화
├── _DARK_DIALOG_SS (str) — 다크 테마 다이얼로그 스타일시트 (재사용)
├── _open_project_manager() — 프로젝트 편집 다이얼로그 (전체 프로젝트 목록 표시/편집/추가/삭제)
├── _load_projects() / _save_projects() — QSettings 프로젝트 데이터 로드/저장
├── _apply_project_path() — 프로젝트 경로 + PSD명 조합으로 _output_base_dir 설정 (Unity ON 시만 호출)
├── _on_unity_toggled() — Unity 체크 ON→프로젝트 경로 적용, OFF→PSD 경로 복원
├── _auto_export_trigger() — Auto Export 조건 검증 후 _start_export() 호출
├── _log_clear_btn (QLabel "×") — 로그 클리어 버튼 (14x14 정사각형, Row3 오른쪽)
├── _clear_log() — 로그 텍스트 삭제
├── closeEvent() — try-except RuntimeError로 C++ 객체 삭제 시 안전 처리
├── _compute_export_dir() — Unity 접미사 + Auto Version 적용한 최종 export 경로 계산
├── _update_output_display() — Unity 모드 / Auto Ver 변경 시 output_entry 실시간 갱신
└── WorkerSignals (QObject) — thumbnail_ready, preview_ready, merged_ready, preload_one, translate_done
```

### 호버/Dim 프리뷰 구조
```
PSD 로드 → psd.topil() → _merged_qimage (캐시)
                            ↓
Tint/설정 변경 → _rebuild_hover_bg() → _hover_bg_qimage (캐시)
                                         ↓
마우스 호버 → _show_hover_preview(row):
  QPainter(result)
    .setOpacity(slider값) → draw _hover_bg_qimage (머지 또는 틴트)
    .setOpacity(1.0)      → draw 호버 레이어 at (layer.left, layer.top)
```
- **캐시 전략**: _hover_bg_qimage는 Tint on/off, 색상 변경 시에만 재생성. 투명도는 draw 시점에 적용 → 슬라이더 즉시 반응

### 다중 선택 프리뷰 구조
```
selectionChanged → _on_preview_requested(rows: list)
  rows 비어있음 → _show_merged_preview()
  rows 1개     → solo 프리뷰 (기존 동작)
  rows 2개+    → PSD 캔버스 크기로 빈 이미지 생성
                  reversed(rows) 순서로 (bottom→top) Image.paste 합성
                  → set_image(keep_zoom=True)
```

### 세션 자동 저장/복원 구조
```
PSD 로드 → set_layers() (초기 스냅샷 생성)
        → 썸네일/프리로드 시작
        → _load_session() (세션 자동 복원)
PSD 전환 → _save_session() (이전 PSD 세션 자동 저장)
앱 종료  → closeEvent() → _save_session()
Restore  → 초기 스냅샷으로 복원 (세션 적용 전 상태)
```
- 세션 파일 경로: `{psd_path}.session.json` (예: `ch.psd.session.json`)
- PSD 로드 시 세션 자동 복원 (Save/Load 버튼 없음)
- `_load_session()` 내부에서 모든 상태를 먼저 적용 후 `_rebuild_view()` 1회만 실행 (시그널 차단으로 중복 rebuild 방지)
- 레이어 수 불일치 시 (PSD가 변경됨) 세션 무시
- 저장 항목: checked, visible, renamed, pot, locked, pivot, crop, order_reversed, tree_mode, show_art_layers, collapsed_groups, group_rename, group_locked, rename 설정 전체, pot_calc, rename_col_w, project_name, auto_export
- settings_v2: format, merge, quality, padding(5항목), log, unity, unity_type, pivot, auto_ver, output_base_dir, hover_opacity, hover_tint, hover_tint_color, preview_bg, crop, crop_threshold

### Auto (KR→EN) 번역 구조
```
_apply_auto_rename()
  ├── group_path 수집 (각 레이어의 PSD 그룹 경로)
  └── QRunnable → _translate_korean_names(names, group_paths)
      ├── 의미 없는 이름 ("01", "레이어 1") → _call_ollama_context() (그룹 기반 추론)
      ├── 영어 이름 (한글 미포함) → prefix만 적용 후 반환 (번역 스킵)
      ├── 딕셔너리 히트 (_KO_BODY_PARTS) → 즉시 반환
      ├── 복합어 분리 ("열린 뚜껑" → split → ["열린","뚜껑"] → "lid_open")
      ├── 혼합 이름 분해 ("리본end" → ["리본","end"] → "ribbon_end")
      ├── 캐시 히트 (_translation_cache, 그룹 컨텍스트 포함 키) → 즉시 반환
      └── _call_llm(parts, contexts) → Provider 분기 (즉시 부모 그룹만 전달)
          ├── Ollama: POST http://localhost:11434/api/chat
          └── Groq: POST https://api.groq.com/openai/v1/chat/completions
              └── 번역 결과 캐시 저장 + translate_done Signal + 토큰 사용량 누적
_on_translate_done()
  ├── 레이어 rename 적용 (setData RenameRole)
  └── 그룹 rename 적용 (_group_rename_map, _group 서픽스 추가, prefix 미적용)
```
- noun_modifier 어순: 명사 우선 (arm_upper, item_inner, lid_open)
- 캐시 키: `그룹경로/파츠명` (예: `팔/위` → `arm_upper`, `다리/위` → `leg_upper`)
- 그룹명=레이어명일 때 컨텍스트 생략 (중복 단어 방지: 뚜껑>뚜껑 → tougal_tougal 문제 해결)
- 딕셔너리에 ~90개 바디파츠/오브젝트/수식어 포함 (뚜껑→lid, 상자→box, 열린→open 등)
- 입력 언어 모드: 한글(번역+prefix), 영어(prefix만), 혼합(세그먼트 분리). 상세: [docs/naming_convention.md](docs/naming_convention.md)
- 앱 UI 표시 3초 후 `_preload_ollama()` 실행 (GPU에 모델 미리 로드)
- 모드 선택 시 `_warmup_ollama()` 백그라운드 실행 (추가 콜드 스타트 방지)
- 그룹 번역 시 prefix="" (fxt_ 접두사 제외 — 사용자가 수동 추가하지 않는 한 prefix는 이미지에만)
- Groq Provider: 동적 모델 목록 API 조회, 추천 모델(qwen3-32b, llama-3.3-70b) 초록색 표시, 토큰 사용량 누적 표시(K/M 포맷)

## 네이밍 컨벤션

2D 게임 리깅용 레이어 이름 규칙 (UE5/Blender 표준 기반):
```
fxt_ch_{part}_{index}_{Side}
```
- prefix: `fxt_ch_` (프로젝트별 접두사)
- part: `hand`, `finger`, `arm`, `eye`, `ear`, `body`, `leg`, `screen` 등
- index: `01`, `02` (같은 파츠가 여러 개일 때)
- Side: `_R` (오른쪽), `_L` (왼쪽)

## Unity Export 기능

PSD 레이어를 Unity에서 원본 위치 그대로 재현하는 기능. UGUI/NGUI 두 가지 모드 지원.

### 개요
Output 패널의 **Unity 체크박스** ON + **UGUI/NGUI 세그먼트** 선택 + **Pivot** 설정 후 Export:
- `fxc_psdImporter_{name}.json` — 레이어 위치/크기/계층/opacity/blend_mode/pivot 메타데이터 (v3)
- `Editor/FXC_PSDImporter_{Stem}.cs` — UGUI 모드 (Canvas + Image + RectTransform, PSD별 고유 클래스명)
- `Editor/FXC_PSDImporterNGUI_{Stem}.cs` — NGUI 모드 (UISprite + Atlas + Widget depth, PSD별 고유 클래스명)

JSON 파일명은 PSD 파일명에서 날짜(YYMMDD_)/버전(_v1, _01) 제거 후 주요 명사만 추출.

### UGUI 워크플로우
1. PSD Extractor에서 **Unity 체크 ON, UGUI** → Export
2. 출력 폴더를 Unity 프로젝트에 통째 복사
3. Unity 메뉴 **Tools > FXC PSD Importer** 실행
4. JSON Browse → Setup Sprites → Import to Scene

### NGUI 워크플로우
1. PSD Extractor에서 **Unity 체크 ON, NGUI** → Export
2. 출력 폴더를 Unity 프로젝트에 통째 복사
3. Unity 메뉴 **Tools > FXC PSD Importer (NGUI)** 실행
4. JSON Browse → **Setup Textures** → **Make Atlas** → Base Depth/Step 설정 → **Import to Scene**
5. 또는 **Import All** 버튼으로 Setup → Atlas → Import 3단계를 1클릭 실행
- **Setup Textures**: 이미지 폴더 내 텍스처를 Sprite/Readable/Uncompressed/FullRect/npotScale=None으로 일괄 설정
- **Make Atlas**: NGUI UITexturePacker로 Atlas 자동 생성 (NGUIAtlas + Material + packed PNG, padding=2, RGBA32, 4096). 스크립트 atlasObject에 자동 반영
- **Import All**: Setup Textures + Make Atlas + Import to Scene 순차 실행 (보라색 버튼)
- **Atlas 업데이트**: 이미지 추가/삭제 후 이미지 폴더 우클릭 → Open Atlas Updater → Sync
- Depth는 PSD order 기반 back→front 자동 할당 (사용자가 나중에 수동 조정)
- UISprite의 spriteName = 파일명(확장자 제외)으로 Atlas에서 매칭
- **이미지 서브폴더**: PSD 파일명과 동일한 서브폴더에 이미지 저장 (예: `260225_giftBox_v1/`)

### 좌표 변환
- **PSD**: 원점 top-left, Y축 ↓ (`layer.left`, `layer.top`, `layer.width`, `layer.height`)
- **UGUI**: anchor=(px, 1-py) 동적, pivot=(0.5,0.5) center, Y축 ↑
- **NGUI**: 원점 center, Y축 ↑. pivot 오프셋 적용: `offX = canvas.width * (pvtX - 0.5)`, `offY = canvas.height * (0.5 - pvtY)`
- **공통 변환 공식** (pivot 적용):
  - `unity.x = layer.left + layer.width / 2 - canvas_width * pivot_x`
  - `unity.y = -(layer.top + layer.height / 2) + canvas_height * pivot_y`
  - `sizeDelta/width/height = (width, height)` (패딩 적용 시 padded_size 사용)
- **Pivot 값**: (px, py) — px=0 left, 0.5 center, 1 right; py=0 top, 0.5 center, 1 bottom

### JSON 구조 (_unity_layout.json, v3)
```json
{
  "version": 3,
  "psd_file": "ch.psd",
  "canvas": { "width": 210, "height": 283 },
  "pivot": { "x": 0.5, "y": 1.0 },
  "groups": [
    {
      "name": "Group1", "depth": 0, "parent": null,
      "group_path": ["Group1"], "blend_mode": "PASS_THROUGH", "order": 0
    }
  ],
  "layers": [
    {
      "name": "leg_R",
      "file": "leg_R.png",
      "psd_name": "오른쪽다리",
      "group": "Group1",
      "group_path": ["Group1"],
      "visible": true,
      "opacity": 255,
      "blend_mode": "NORMAL",
      "rect": { "left": 110, "top": 221, "width": 56, "height": 62 },
      "unity": { "x": 33.0, "y": 31.0, "width": 56, "height": 62 },
      "padded_size": { "width": 58, "height": 64 },
      "order": 0
    }
  ]
}
```

### UGUI 임포터 생성 구조
```
GameObject (FXC_PSDImporter 컴포넌트)
└── 260225_giftBox_v1 (PSD 파일명 루트, pivot=(px, 1-py))
    └── fxRoot_anim (애니메이션 타겟, bbox 기반 RectTransform)
        ├── Group1 (bbox 기반 RectTransform, anchor=0.5/0.5)
        │   ├── leg_R (RectTransform + Image, 그룹 중심 기준 상대좌표)
        │   ├── leg_L (RectTransform + Image)
        │   └── ...
        └── s_leg_01 (RectTransform + Image)
```
- **PSD명 루트**: PSD 파일명에서 추출한 이름의 RectTransform (캔버스 크기 × scaleFactor)
- **fxRoot_anim**: 단일 최상위 그룹이면 fxRoot_anim에 머지 (불필요한 중첩 방지)
- **그룹 바운딩박스 피봇**: 각 그룹의 RectTransform을 하위 레이어 바운딩박스 기반으로 설정. 그룹마다 독립된 중심점 → 회전/스케일 시 콘텐츠 중심 기준 동작
  - Phase 1: 모든 레이어 rect를 순회하여 직속/상위 그룹에 bbox 누적 (Vector4: minX, minY, maxX, maxY)
  - Phase 2: 그룹 생성 — bbox 있으면 실제 크기/위치, 하위 그룹은 부모 중심 기준 상대좌표
  - Phase 3: 레이어 생성 — bbox 그룹 내 레이어는 anchor(0.5,0.5)로 그룹 중심 기준 상대좌표
- **Snap to Pixel**: 위치/크기를 정수로 반올림 (기본 ON). Inspector에서 토글 가능
- **fxt_ → s_ prefix 변환**: 레이어명이 `fxt_`로 시작하면 하이어라키에서 `s_`로 변환 (텍스처→스프라이트 네이밍, NGUI와 동일)
- opacity < 255 → Image.color.a 반영
- visible=false → SetActive(false)
- Scale Factor 지원 (기본 1.0)
- Undo 지원 (Ctrl+Z로 되돌리기)
- group_path 기반 고유 그룹 매칭 (동일 이름 그룹 충돌 방지)
- v1/v2/v3 JSON 하위호환
- **통합 순서 (Unified Ordering)**: `psd.descendants()` 1회 순회로 그룹과 레이어에 단일 통합 순번 부여. C# 임포터에서 오름차순 정렬하여 PSD back→front = Unity sibling 0→N (UGUI 렌더 순서 일치)
- **Sprite 자동 설정**: Setup Sprites 시 TextureType=Sprite + MeshType=FullRect + GeneratePhysicsShape=off + mipmapEnabled=false + Uncompressed 일괄 적용

### NGUI 임포터 생성 구조
```
GameObject (FXC_PSDImporterNGUI 컴포넌트)
└── 260225_giftBox_v1 (PSD 파일명 루트)
    └── fxRoot_anim (애니메이션 타겟, bbox 기반 localPosition)
        ├── Group1 (bbox 기반 localPosition, 부모 중심 기준 상대좌표)
        │   ├── s_body_01 (UISprite, 그룹 중심 기준 상대좌표)
        │   └── s_arm_R (UISprite)
        └── s_leg_01 (UISprite)
```
- **PSD명 루트**: PSD 파일명에서 추출한 이름의 빈 GameObject (스크립트 오브젝트 하위)
- **fxRoot_anim**: 단일 최상위 그룹이면 fxRoot_anim에 머지 (불필요한 중첩 방지)
- **그룹 바운딩박스 피봇**: UGUI와 동일한 Phase 1/2/3 bbox 로직. localPosition으로 그룹 중심 배치
  - Phase 1: 모든 레이어 rect를 순회하여 직속/상위 그룹에 bbox 누적 (Vector4: minX, minY, maxX, maxY)
  - Phase 2: 그룹 생성 — bbox 있으면 localPosition으로 배치. 머지 최상위 그룹은 NGUI 중심좌표 기준 (`bcx - canvasW*0.5`), 하위 그룹은 부모 중심 기준 상대좌표 (`bcx - pcx`)
  - Phase 3: 레이어 생성 — bbox 그룹 내 레이어는 그룹 중심 기준 상대좌표 (`lcx - pcx`)
- **Snap to Pixel**: 위치/크기를 정수로 반올림 (기본 ON). Inspector에서 토글 가능
- **fxt_ → s_ prefix 변환**: 레이어명이 `fxt_`로 시작하면 하이어라키에서 `s_`로 변환 (텍스처→스프라이트 네이밍)
- Depth: PSD order 기준 back→front 자동 할당 (baseDepth + depthStep × N)
- UISprite: atlas + spriteName(파일명) + width/height(padded_size 우선)
- opacity < 255 → UISprite.color.a 반영
- visible=false → SetActive(false)
- UIPanel 미존재 시 경고 메시지 표시
- Undo 지원 (Ctrl+Z로 되돌리기)

### FXC_MeshQuad (Shader FX Quad 워크플로우)

POT(Distort) 텍스처를 Unity Quad에 적용하는 워크플로우를 자동화. PSD Exporter에서 이미지 + JSON + C# 스크립트를 생성하고, Unity에서 1클릭으로 Quad 오브젝트를 일괄 생성.

#### 출력 파일 구조
```
export_dir/
  layer1.png
  FXC_MeshQuad_{Suffix}.cs              ← Runtime (미존재 시만 생성)
  POT/
    layer1.png                           ← POT 텍스처
    _pot_info.json                       ← 원본/POT 크기 정보
    Materials/
      layer1.mat                         ← 머티리얼 에셋 (레이어명과 동일)
  Editor/
    FXC_MeshQuad_{Suffix}Editor.cs       ← Editor (미존재 시만 생성)
```

#### C# 클래스 구조
- **`FXC_MeshQuad`** — 루트 컴포넌트 (`[ExecuteAlways]`, `[AddComponentMenu("FXC/Mesh Quad")]`)
  - `TextAsset potInfoJson` — `_pot_info.json` 참조 (Editor OnEnable에서 자동 탐색)
  - `int baseDepth, depthStep` — NGUI depth 제어
- **`UIShaderWidget`** — 공용 자식 Quad 컴포넌트 (별도 스크립트, `Script/FX/UIShaderWidget.cs`)
  - UIWidget 직접 상속 (UICustomRendererWidget 의존 없음)
  - `Vector3 meshSize` — X=Width, Y=Height (픽셀 단위)
  - `[SerializeField] Mesh _mesh` — 씬에 직렬화되어 도메인 리로드 시 유지
  - `Rebuild()` — 메쉬 버텍스가 실제 픽셀 크기 정의 → `Transform.localScale = (1,1,1)` 유지
  - MeshFilter만 `HideFlags.HideInInspector` (MeshRenderer는 숨기지 않음 — Animation 키프레임 지원)
  - OnEnable 시 `_mesh == null`일 때만 Rebuild (컴포넌트 수정 최소화 → 머티리얼 직렬화 보호)
  - Renderer↔DrawCall 연결, NGUI depth, Invalidate override 자체 구현
- **`FXC_PlayModeSaver`** — 공용 `[InitializeOnLoad]` static class (`Script/FX/Editor/`). Play 전 `AssetDatabase.SaveAssets()` 자동 호출
- **`FXC_MeshQuadEditor`** — Custom Inspector + Setup 메뉴
  - JSON auto-discovery: `MonoScript.FromMonoBehaviour()` → 스크립트 경로 기준 `POT/_pot_info.json` 자동 할당
  - Setup: fxRoot_Anim + 하위 Mesh 오브젝트 일괄 생성 (`AddComponent<UIShaderWidget>()`, `fxt_` → `fxs_` 이름 변환)
  - MeshRenderer 경량 2D 설정 (Setup 시 1회만): Shadow Off, Probes Off, MotionVector Off, Occlusion Off
  - Material .mat 에셋 → `POT/Materials/{name}.mat` (레이어명과 동일, 재Setup 시 기존 .mat 재사용)
  - `SetupTextureImport()`: POT 텍스처 → Default, sRGB, NPOT=None, Mipmap=OFF, Clamp, Bilinear, Uncompressed
  - Shader fallback: `FX Team/fxs_shine` → `Unlit/Texture` → `Standard`
  - `_RShineTex` 기본 텍스처 자동 할당: `fxt_grad_50.png` (미설정 시만, 재Setup 시 기존 텍스처 보존)
  - UIShaderWidget.depth 자동 할당 (baseDepth + depthStep × N)
  - Hierarchy 표시: 자식 오브젝트 목록 + Size + Depth 정보

#### Unity 계층 구조
```
Root (FXC_MeshQuad)
  └─ fxRoot_Anim
       ├─ fxs_layer1 (UIShaderWidget + MeshFilter[hidden] + MeshRenderer)  ← fxt_→fxs_ 변환
       ├─ fxs_layer2 ...
       └─ ...
```

#### 워크플로우
```
PS → PSD Exporter (POT+Distort Export)
  → 이미지 + _pot_info.json + FXC_MeshQuad.cs 자동 생성
  → Unity 프로젝트에 복사
  → 빈 GameObject 생성 → FXC_MeshQuad 스크립트 드래그 (JSON 자동 할당)
  → Setup 버튼 → fxRoot_Anim + 하위 UIShaderWidget 오브젝트 일괄 생성
  → Transform.localScale = (1,1,1) 유지, 바로 셰이더 애니메이션 작업
```

#### 설계 결정 사항
- **메쉬 버텍스 기반 크기** (localScale 아님): Scale (1,1,1) 필수 — 애니메이션/파티클 간섭 방지
- **공유 mesh .asset 불가**: 서로 다른 크기의 Quad는 버텍스가 달라야 하므로 공유 불가. 인스턴스별 메모리 메쉬 사용 (Quad 4 vertices ≈ 100 bytes, 100개 = ~10KB — 무시 가능)
- **`[SerializeField] Mesh _mesh`**: 씬에 직렬화하여 도메인 리로드 시 OnEnable에서 컴포넌트 수정 방지 → MeshRenderer 머티리얼 직렬화와 간섭 없음
- **MeshRenderer 숨기지 않음**: `HideFlags.HideInInspector` 설정 시 Animation 창에서 머티리얼 키프레임 생성 불가
- **MeshRenderer 설정은 Setup 시 1회만**: OnEnable에서 MeshRenderer 프로퍼티 수정 시 도메인 리로드 중 직렬화 간섭 → 머티리얼 텍스처 유실
- **PlayModeSaver**: Setup으로 생성된 .mat 에셋을 Inspector에서 수정 후 저장 없이 Play하면 디스크 버전으로 리로드되어 텍스처 유실. `[InitializeOnLoad]`로 Play 진입 직전 `SaveAssets()` 자동 호출하여 해결
- **`fxc_` prefix**: FX Component 약자 (팀 네이밍 규칙). 인스턴스 메쉬명 `fxc_quad`
- **`fxt_` → `fxs_` prefix 변환**: Setup 시 레이어명이 `fxt_`로 시작하면 하이어라키에서 `fxs_`로 변환 (texture→shader FX 네이밍). UGUI/NGUI의 `fxt_`→`s_` 변환과 유사 패턴
- **UIShaderWidget 독립성**: UIWidget 직접 상속 (UICustomRendererWidget 의존 없음). 복사 시 필요 파일: UIShaderWidget.cs, UIShaderWidgetEditor.cs, HierarchyExtend.cs, FXC_PlayModeSaver.cs (+ NGUI UIWidget 필요)
- **Material 네이밍**: `POT/Materials/{레이어명}.mat` (mat_ prefix 없음, 레이어 파일명과 동일)
- **R Shine 기본 텍스처**: Setup 시 `_RShineTex` 슬롯에 `fxt_grad_50.png` 자동 할당 (fxs_shine 셰이더 전용). 이미 다른 텍스처가 할당된 경우 덮어쓰지 않음

### 백엔드 함수 (psd_extractor.py)
- `_get_group_path(layer)` — psd-tools Layer의 부모 그룹 경로 반환
- `next_pot(value)` — 값 이상의 가장 가까운 2의 거듭제곱 반환 (올림)
- `nearest_pot(value)` — 가장 가까운 2의 거듭제곱 반환 (올림/내림 중 거리가 가까운 쪽)
- `apply_pot(img, pot_w, pot_h, pot_auto, bg_color, resize_type, pot_calc)` — POT 캔버스 확장. pot_calc="ceil"(올림)/"nearest"(근접). Nuke Reformat Resize Type 6종 (none/fit/fill/width/height/distort). 불투명 배경 시 `alpha_composite`로 완전 플래튼
- `convert_color_mode(img, mode, bg_rgb)` — RGBA/RGB/L 색상 모드 변환
- `save_png_oxipng(img, file_path, level)` — pyoxipng 라이브러리로 최적화된 PNG 저장
- `collect_layer_metadata(psd, ..., per_layer_pivot=None, crop_offsets=None)` — JSON 직렬화 가능한 메타데이터 dict 반환. 파일명 충돌 자동 방지(_1, _2 접미사). 그룹 리네임 적용. 통합 순서(unified order). pivot_x/pivot_y로 글로벌 좌표 원점 오프셋 적용. per_layer_pivot으로 레이어별 피봇 반영. crop_offsets로 크롭 후 좌표 보정 (dx, dy, crop_w, crop_h)
- `crop_transparent(img, threshold=0)` — 투명 영역 자동 크롭. Alpha threshold 기반 getbbox(). 반환: `(cropped_img, dx, dy)` — dx, dy는 왼쪽/위 잘림 오프셋 (Unity 좌표 보정용)
- `save_psd_with_renames(psd, rename_pairs, output_path, psd_path)` — 바이너리 레벨 PSD 수정으로 레이어명 변경 후 저장. Pascal string + luni Unicode 블록만 수정, 원본 바이트 보존. PSB(대용량) 호환. Photoshop에서 정상 인식

## 개발 환경

- Windows 11, Python 3.13+
- Unity 2022.3.67f2 (Unity UGUI 임포트 시)
- Photoshop v27.4 (COM 기반 도구 사용시만 필요)
- psd-tools 1.12.1, Pillow 12.1.1, PySide6, customtkinter 5.2.2
- pyoxipng >= 9.1.0 (선택, OxiPNG 무손실 PNG 최적화)
- Ollama (로컬 LLM 서버, Auto KR→EN Rename 시 사용, qwen2.5:3b 모델)
- Groq (클라우드 LLM API, Auto KR→EN Rename 대체/보조, qwen3-32b 등)
