# Teamplay - Claude Code 개발 가이드

## 프로젝트 개요
FX팀 업무 통합 관리 도구 - Dooray 기반 업무 트래킹 + Gantt 차트 + 보고서 자동화

## MCP 서버

### 1. Sequential Thinking MCP
복잡한 문제를 단계별로 분석하고 해결하는 데 도움

**활용 시나리오**:
- 새로운 기능 설계 시 단계별 분석
- 버그 원인 추적 시 체계적 접근
- 아키텍처 결정 시 장단점 분석

**사용 예시**:
```
"Sequential Thinking을 사용해서 댓글 파싱 로직을 설계해줘"
"단계별로 생각해서 이 버그의 원인을 찾아줘"
```

### 2. Dooray MCP
Dooray API 연동 - 프로젝트, 업무, 댓글 조회/수정

**주요 도구**:
- `dooray_project_list_projects`: 프로젝트 목록 조회
- `dooray_project_list_posts`: 업무 목록 조회
- `dooray_project_get_post`: 업무 상세 조회
- `dooray_project_get_post_comments`: 댓글 조회
- `dooray_project_create_post_comment`: 댓글 작성
- `dooray_wiki_*`: 위키 관련 도구

## 프로젝트 구조

```
D:\_Teamplay\
├── PLAN.md              # 개발 계획서
├── CLAUDE.md            # 이 파일 (Claude Code 가이드)
├── .mcp.json            # MCP 서버 설정
├── package.json         # npm 설정
├── electron-main.js     # Electron 메인 프로세스 (IPC: 파일 읽기/쓰기, 바이너리, 폴더 목록+stat)
├── electron-preload.js  # IPC 브릿지
├── index.html           # 메인 UI
├── styles.css           # 스타일
│
├── js/                  # 프론트엔드 모듈
│   ├── main.js          # 앱 초기화
│   ├── state.js         # 상태 관리 (DEFAULT_COLOR_SETTINGS 2벌 존재, 둘 다 동기화 필수)
│   ├── storage.js       # 데이터 저장
│   ├── plannedImport.js # Excel → Planned 자동 Import 모듈
│   ├── memberHistory.js # 팀원별 업무 이력 조회/복사 모듈
│   ├── commandPalette.js # Command Palette (Ctrl+P) 검색/실행
│   ├── dooray/          # Dooray 연동
│   ├── views/           # 뷰 컴포넌트
│   └── reports/         # 보고서
│
├── config/              # 설정 파일
└── data/                # 로컬 데이터
```

## 업무 플로우

1. **Dooray 댓글 작성** (팀원)
   - 프로젝트 링크 + 표 형식으로 진행사항 기록
   - MM.DD 형식으로 작업 날짜 기록

2. **자동 동기화** (Teamplay)
   - 댓글 조회 → 파싱 → Task/Work 마크 반영
   - "새 업무 등록" 감지 → Gantt에 Task 추가
   - 제목/프로젝트 변경 감지 → 기존 Task 업데이트 + `변경` 배지 (중복 생성 안 함)
   - 중복 Task 발견 시 빈 필드 자동 채움 (releaseMonth, dates, md, planning, assignee, wikiUrl)
   - 완료 처리 → `완료` 배지, Work 마크 적용 → `Work` 배지 (3분 후 자동 해제)

3. **시각화 및 보고**
   - Gantt 차트로 진행 현황 파악
   - 마감 임박/지연 업무 알림
   - 주간/월간 보고서 자동 생성

## 팀 정보
- **팀원**: 정재화, 김보람, 김지인 (3명)
- **특징**: 소규모 팀, 작업량 많음
- **핵심**: 스케줄 놓침 방지

## 개발 원칙

1. **기존 코드 활용**
   - Team Schedule Manager (`E:\_Team Schedule Manager`) 기반
   - DoorayMCP (`E:\_DoorayMCP`) 기능 통합

2. **Electron 우선**
   - 로컬 파일 접근 용이
   - CORS 우회
   - 데스크톱 알림 지원

3. **데이터 무결성**
   - 자동 백업
   - 동기화 충돌 방지
   - 로컬 우선 저장

## !! 절대 보호 데이터 - workLogs / dailyNotes !!

> **workLogs와 dailyNotes는 이 앱에서 가장 중요한 데이터입니다.**
> **절대로 삭제, 초기화, 덮어쓰기, 필터링하여 저장해서는 안 됩니다.**

### 데이터 구조
- `AppState.workLogs[taskId][dateStr]` — Task별 날짜별 작업 마크 (색상값)
- `AppState.dailyNotes["taskId_YYYY-MM-DD"]` — Task별 날짜별 작업 메모

### 사용처
- **Gantt 차트**: 날짜 셀에 워크 마크 dot 표시
- **Team 차트**: 팀 일정 날짜 셀에 워크 마크 dot 표시
- **진행률 계산**: workLogs 날짜 수 / MD로 진행률 산출
- **Work History**: 팀원별 기간별 작업 이력 조회
- **보고서**: 실제 작업일수(Actual MD) 계산
- **Summary Bar**: Plan vs Actual MD 비교

### 절대 금지 사항
1. **workLogs/dailyNotes를 삭제하는 cleanup/정리 함수 작성 금지**
   - 고아 데이터 정리 시 반드시 `AppState.tasks`와 `AppState.teamTasks` 양쪽 모두 확인
   - taskId에 밑줄(`_`)이 포함되므로 `split('_')[0]` 같은 파싱 절대 금지
   - taskId 추출 시 반드시 끝의 `_YYYY-MM-DD` 패턴으로 분리: `noteKey.match(/_(\d{4}-\d{2}-\d{2})$/)`
2. **saveData() 시 빈 객체로 덮어쓰기 금지** — 저장 전 데이터 존재 확인
3. **환경 import/export 시 workLogs/dailyNotes 누락 금지**
4. **Undo/Redo 시 workLogs/dailyNotes 복원 누락 금지**

### 사고 이력 (2026-03-07)
`cleanOrphanedData()` 함수가 앱 시작 시 자동 실행되어:
- dailyNotes 168개 전량 삭제 (`split('_')[0]` → `"task"` 반환 → 전부 고아 판정)
- teamTasks의 workLogs 27개 삭제 (`AppState.tasks`만 체크, `AppState.teamTasks` 미확인)
- **교훈**: workLogs/dailyNotes를 다루는 코드 변경 시 극도의 주의 필요

## 댓글 형식 규칙

```markdown
[프로젝트명/번호 업무제목](dooray://...)

| No | 금주 진행내용 | 다음주 주요 액션 | 이슈 | 팀 공유사항 |
| --- | --- | --- | --- | --- |
| 1 | 01.27 작업내용 | 다음 계획 | 이슈 | 새 업무 등록 |
```

**파싱 규칙**:
- "금주 진행내용" 컬럼이 없는 표는 무시
- MM.DD 패턴으로 날짜 추출
- "새 업무 등록" → Task 자동 생성

## Skills (핵심 로직 문서)

> **활용 가이드**: `.claude/SKILLS_GUIDE.md` 참조

`.claude/skills/` 디렉토리에 핵심 로직이 문서화되어 있습니다:

| Skill | 설명 | 활용 |
|-------|------|------|
| `/sync` | Dooray 동기화 프로세스 | 댓글 → Task/Work 동기화 |
| `/status` | 팀 업무 현황 조회 | 대시보드 데이터 |
| `/parsing` | **핵심 파싱 로직** | 로직 수정 시 참고 |
| `/task-fields` | **Task 필드 정의** | 데이터 구조 확인 |
| `/debug` | **디버깅 가이드** | 문제 해결 |
| `/deadline` | 마감 알림 | D-Day 체크 |
| `/report` | 보고서 생성 | 주간/월간 보고 |

### 핵심 파싱 로직 요약

**1. 제목 파싱** (`commentParser.parseTaskTitle`)
```
𝗙𝗫 [AI] AI 성숙도 4레벨 [작업] 확장자 테스트
     ↓
platform: "AI", project: "AI 성숙도 4레벨", task: "확장자 테스트"
```

**2. 진행률 계산** (`syncManager.calculateProgress`)
```javascript
progress = min(workDays / MD * 100, 95)  // 최대 95%
status = workDays > 0 ? 'Doing' : 'Ready'
// 100%와 Done/Hold는 수동 설정만 가능
```

**4. Work 마크 토글 시 Status 자동 전환** (`tasks.js:toggleWorkLog`)
- Work 마크 추가 시: `Ready → Doing` 자동 전환
- Work 마크 전체 삭제 시: `Doing → Ready` 자동 복원
- `Hold`, `Done`, `Bypass`는 수동 설정이므로 자동 전환하지 않음

**3. 본문 정보 파싱** (`syncManager.parseProjectInfoFromBody`)
- 카테고리, 조직, 일정, 점검월, 위키, 기획 링크 추출
- 위키 링크는 원본 형식 유지 (팝업 동작 필요)
- 기획 링크: `기획: [프로젝트코드/번호 제목](dooray://...)` → 제목만 추출하여 `planningTitle`에 저장

### 중요 규칙

1. **Status vs 상태태그**
   - Task Status: Ready → Doing → Hold → Done → Bypass
   - 제목의 `[작업]`, `[완료]` 등은 상태태그일 뿐, Status와 무관

2. **진행률 최대 95%**
   - Work 마커가 MD보다 많아도 95% 제한
   - 100% 완료는 수동 확인 필요

3. **데이터 일관성**
   - 진행률/상태 계산은 `updateTaskProgress()` 단일 함수 사용
   - Work 마크는 `AppState.workLogs`가 단일 소스

## Gantt 차트 주요 기능

### 필터 시스템
- **프로젝트 필터**: `platform|project` 형식으로 정확한 매칭
- **서비스 필터**: `releaseMonth` 기준
- **플래닝 필터**: `planning` (조직) 기준
- **상태 필터**: Ready/Doing/Hold/Done/Bypass
- **Hide Bypass**: Bypass 상태 Task 숨김 (`AppState.hideBypass`, X키 토글)
- **Hide Planned**: Planned(placeholder) 그룹 숨김 (`AppState.hidePlanned`)
- **Planned 월 필터**: Hide Planned 옆 📅 버튼 → 월별 체크박스로 보고 싶은 월만 선택 (`AppState.plannedVisibleMonths`)
- **Placeholder(Planned) 프로젝트**도 필터 적용됨 (`gantt.js:groupTasksByPlatformProject`)

### Task Selection (Alt+Click)
선택한 Task들의 계획 MD vs 실제 작업 MD를 비교하는 기능

**사용법**:
- `Alt + 클릭`: Task 컬럼에서 Task 선택/해제 토글
- 선택된 Task 앞에 파란 원(●) 표시
- 하단 Summary Bar에 합산 정보 표시

**Summary Bar 구성**:
```
[X] [Excel] [📂] | Selected: N tasks (M done) | Progress: P% | Plan: X MD (Y일) | Actual: X MD (Y일) | Gap: Z MD | Eff: N%
```
- `X` 버튼: 전체 선택 해제 (파란색 Sync 스타일)
- `Excel` 버튼: 선택 Task MD 상세 엑셀 다운로드 (초록색)
- `📂` 버튼: 다운로드 폴더 열기 (초록색)
- `Selected`: 선택 Task 수 + 완료(Done/100%) 개수
- `Progress`: 선택 Task 평균 진행률 (≥100% 초록, ≥50% 기본, <50% 빨강)
- `Plan MD (N일)`: 각 Task의 Plan MD 합산 + 달력일수(중복 제거)
- `Actual MD (N일)`: 각 Task의 Work 마크 합산 + 달력일수(중복 제거)
- `Gap`: Actual - Plan (음수=빨강, 양수=초록)
- `Eff`: Plan / Actual × 100% (>100% 빠르게=초록, <100% 지연=빨강)

**달력일수**: 여러 Task의 일정/Work 마크가 같은 날짜에 겹치면 1일로 카운트

**Excel 파일 구성** (`선택Task_MD_YYYYMMDD.xlsx`):
- 개별 Task 행: No, 프로젝트, Task, Plan MD, Actual MD, Gap
- 합계 행: 볼드, 상단 테두리
- 달력일수 행: Plan/Actual 중복 제거 달력일수
- 효율 행: Plan/Actual 비율 퍼센트

**구현 위치**:
- 상태: `AppState.selectedTasks` (Set, 비영구)
- 핸들러: `GanttView.handleTaskColumnClick()` → `toggleTaskSelection()`
- Summary: `GanttView.updateSelectionSummary()`
- Excel: `GanttView.exportSelectedTasksMD()` (SheetJS xlsx-js-style)
- 폴더: `GanttView.openDownloadsFolder()` → `electronAPI.getDownloadsPath()`
- Summary Bar가 나타나면 플로팅 버튼들이 자동으로 위로 이동
- **하단 여백**: `.gantt-wrapper`, `.planning-overview-table-wrapper`에 `padding-bottom: 60px` — 플로팅 버튼에 콘텐츠가 가려지지 않도록

### Alt+Click 용도 정리
| 위치 | 동작 | 핸들러 |
|------|------|--------|
| Day 셀 | Work 로그 토글 | `App.handleGanttCellClick()` |
| Task 컬럼 | Task 선택 토글 | `GanttView.handleTaskColumnClick()` |
| Alt+Wheel | 수평 스크롤 | `ganttWrapper wheel listener` |

### Sync 미니 배지 시스템
Sync 결과를 Task 컬럼에 미니 배지로 표시. **Task명 뒤쪽**에 위치.

| 배지 | 색상 | 의미 | 자동 해제 | 플래그 |
|------|------|------|----------|--------|
| `신규` | 주황 (#ff9800) | Sync 신규 Task 추가 | 1시간 | `isSyncNewTask` |
| `변경` | 보라 (#9b59b6) | 제목/프로젝트 변경 감지 | 1시간 | `isDuplicateWithChanges` |
| `완료` | 초록 (#34a853) | Sync 완료 처리 | 1시간 | `isSyncCompleted` |
| `작업` | 파랑 (#4285f4) | Work 마크 적용 | 1시간 | `isSyncWorkApplied` |
| `미등록` | 빨강 (#E53935) | Dooray 미등록 업무 | 영구 | `isLocal` |
| `수정` | 빨강 (#e53935) | Reopen 수정 재작업 | 수동 (Done 시 해제) | `reopenedAt` |

**배지 위치**: Task명 뒤 (`selectDot + taskName + badges`), `margin-left: 4px`, `vertical-align: middle`
**배지 지속 시간**: `BADGE_DURATION: 1 * 60 * 60 * 1000` (1시간)
**배지 영속성**: 타임스탬프 기반 (`flag + 'ExpiresAt'`), 앱 재시작 시 잔여 시간만큼 타이머 복원
**배지 공통 타이머**: `syncManager.js:_scheduleBadgeClear(taskId, flag, timers, duration)`
**배지 동시 표시**: 신규+작업, 신규+완료 등 여러 배지가 동시에 표시 가능

**구현 위치**:
- 배지 렌더링: `gantt.js` renderRowCells
- 공통 타이머: `syncManager.js:_scheduleBadgeClear()`
- 앱 시작 시 ExpiresAt 검사 → 잔여 타이머 복원: `main.js:init()`
- Reopen 로직: `tasks.js:updateTaskStatus()` (Done → Doing 전환 시)
- CSS: `.sync-new-badge`, `.duplicate-change-badge`, `.sync-completed-badge`, `.sync-work-badge`, `.reopen-badge`, `.local-badge`

### Sync 상태 테이블 변경 열
동기화 상태 테이블에 "변경" 열 추가 - 제목/프로젝트 변경 감지 건수 표시

**동작**:
- Sync 조회 시 `updateExistingTaskTitles(parsedEntries, false)`로 변경 감지 (미리보기)
- 변경 건수 > 0이면 👁 버튼 표시 → 클릭 시 팝오버로 변경 상세 확인
- 팝오버에서 항목 클릭 시 Gantt에서 해당 Task 하이라이트
- Work 마크 적용 / 업무 추가 시 `applyChanges=true`로 실제 반영

**구현 위치**:
- 감지: `syncManager.js:updateExistingTaskTitles(parsedEntries, applyChanges)`
- UI: `main.js:showSyncStatus()`, `main.js:toggleSyncChangesPopover()`

### Sync 새 업무 호버 하이라이트
새 업무 감지 목록(`showNewTasks`)에서 항목에 마우스를 올리면 Gantt 차트의 해당 Task 행이 하이라이트됩니다.

**동작**:
- 각 항목에 `data-dooray-url` 속성 추가
- `mouseenter` → `highlightTaskByDoorayUrl(url, true)` → Gantt 행 하이라이트
- `mouseleave` → `highlightTaskByDoorayUrl(url, false)` → 하이라이트 해제

**구현 위치**: `main.js:showNewTasks()`

### Sync 중복 Task 원격 정보 자동 채움
동기화 시 URL이 일치하는 기존 Task가 있으면 비어있는 필드를 원격 정보로 자동 채웁니다.

**채워지는 필드**: `releaseMonth`, `startDate`, `endDate`, `md`, `planning`, `assignee`, `wikiUrl`, `planningTitle`
**조건**: 기존 Task의 해당 필드가 비어있고 (`!existing.field`) 원격 정보에 값이 있을 때만 (`task.field`)
**구현 위치**: `syncManager.js:addNewTasksWithRemoteInfo()` (duplicate 감지 블록 내)

### Dooray 미등록 업무 (isLocal)

Dooray에 등록되지 않은 자체 업무를 별도로 관리하는 기능입니다.

**Task 필드**: `isLocal` (boolean, 기본값 false)
**뱃지**: Gantt Task 컬럼에 빨간 `미등록` 뱃지 (`.local-badge`, #E53935)

**동작**:
- Add/Edit Task 모달 제목 라인 오른쪽에 "Dooray 미등록 업무" 뱃지 버튼 (`#taskLocalBadgeBtn`)
- 체크 시: ☑ 활성 (빨간 배경) + Dooray URL/Project URL 백업 후 삭제 + 입력 비활성화
- 체크 해제 시: ☐ 비활성 + URL 복원 (`_localUrlBackup` 패턴)
- Sync 보호: `syncManager.js`의 URL 매칭 4곳에 `!t.isLocal` 가드 추가

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/tasks.js` | `createTask()` — `isLocal` 필드 포함 |
| `js/main.js` | `setTaskLocal()`, `getTaskLocal()`, `toggleTaskLocal()`, `_applyTaskLocalState()` |
| `js/dooray/syncManager.js` | `!t.isLocal` 가드 (4곳: addNewTasks×2, updateExistingTaskTitles, applyWorkMarks) |
| `js/views/gantt.js` | `renderRowCells()` — `미등록` 뱃지 렌더링 |
| `styles.css` | `.local-badge`, `.task-local-badge-btn`, `.local-disabled` |

### Gantt 컬럼 레이아웃

| 컬럼 | left | width |
|------|------|-------|
| No | 0 | 35px |
| Service | 35px | 70px |
| Platform | 105px | 90px |
| Project | 195px | 180px |
| Task | 375px | 320px |
| Status | 695px | 80px |
| Progress | 775px | 80px |
| Assignee | 855px | 120px |
| Date | 975px | 90px |
| DateEnd | 1065px | 90px |
| MD | 1155px | 60px |

**주의**: 컬럼 너비 변경 시 `styles.css`에서 2곳 수정 필요 (메인 컬럼 정의 + 그룹 헤더 sticky positions)

### MD 컬럼: Actual | Plan 표시
MD 컬럼에 실제 작업일수(Actual)와 계획일수(Plan)를 `Actual | Plan` 형식으로 표시합니다.

**표시 형식**: `3 | 5` (Actual MD | Plan MD)
**색상 규칙**:
- Actual: 볼드 기본색, Actual >= Plan이면 초록색 (`.md-done`)
- `|` 구분자: 회색 (#ccc)
- Plan: 회색 (#999)

**그룹 헤더**: 그룹 내 전체 Task의 Actual/Plan MD 합산 (allTasks 기준 - Hide Done 필터 무관)

**구현 위치**:
- Task 행: `gantt.js:renderRowCells()` — `AppState.workLogs[task.id]`에서 날짜키 카운트
- 그룹 헤더: `gantt.js:renderGroupHeader()` — `allTasks` 순회 합산
- CSS: `.md-actual`, `.md-sep`, `.md-plan`, `.md-actual.md-done`

### 그룹 헤더
- Platform + Project 기준으로 Task 그룹핑
- 그룹별 Task 수, 진행률, MD(Actual|Plan) 표시
- 접기/펼치기, 잠금 지원
- Planned Task Count 수동 설정 가능 (`type="text" inputmode="numeric"`, `requestAnimationFrame`으로 포커스)
- 정렬: releaseMonth → Placeholder 후배치 → project 이름순

### 그룹 헤더 달력 배경색
그룹 헤더의 달력 영역에 배경색을 적용하여 일반 Task 행과 시각적으로 구분합니다.

**CSS 변수**: `--group-header-day-bg` (기본값 `#f0f5ff`)
**색상 설정**: Settings > Color > Gantt > Group Header > Calendar Background (`groupHeaderDayBg`)
**Specificity 주의**: `.gantt-table td { background: #fff }` (0,1,1)보다 높아야 하므로 `.gantt-table td.group-header-day` (0,2,1) 사용

**z-index 레이어** (뒤→앞):
| z-index | 요소 |
|---------|------|
| 1 | 달력 배경색 (`.group-header-day`) |
| 2 | 기간 바 (`.group-bar`) |
| 3 | Today 세로선 (`::after`) |

- Placeholder 그룹: `--group-placeholder-bg` (보라색) `!important` 오버라이드
- 잠금 그룹: `#FFF3E0` (주황색) 오버라이드
- Today 셀: `--today-cell-bg` `!important` 오버라이드

### 보고서 하이라이트
- 보고서 패널에서 Task 항목 hover/클릭 시 Gantt 차트의 해당 행 하이라이트
- **Hide Done/Bypass 자동 해제**: 하이라이트 대상 Task가 Hide Done/Bypass로 숨겨져 있으면 자동으로 해제 후 재렌더하여 하이라이트 표시
- 보고서 패널 닫힐 때 잔존 하이라이트 자동 제거 (`report.js:closePanel()`)
- Gantt → 보고서 역방향 하이라이트도 지원
- 패널 너비: 621px (`styles.css` `.report-panel`)
- **구현 위치**: `report.js:highlightGanttTask()` — row 미발견 시 `hideCompleted`/`hideBypass` 체크 → 해제 → `App.render()` → row 재탐색

### 보고서 Service 월 표시
보고서 Task 항목에서 `releaseMonth`를 진척률 뒤에 작은 회색 텍스트로 표시합니다.

**표시 형식**: `[PC포커] 브로드캐스팅 고도화 : Task1...  (진척률 75%) 26.04`
- 프로젝트명에서 `(YY.MM)` 괄호 제거 → 진척률 뒤로 이동
- 색상: `#999` (본문보다 약하게)
- Copy / Copy Table에는 미포함 (표시 전용)

**구현 위치**:
- 그룹 항목: `report.js:generateGroupedTaskItem()` — `<span class="report-month">`
- 개별 항목: `report.js:generateTaskItem()` — 동일
- 프로젝트 상세 모달: `report.js:showProjectTasksModal()` — 타이틀에 표시
- CSS: `.report-month-sep` (숨김), `.report-month`

### 보고서 차주 계획 Done 필터
차주/다음달 작업 계획에서 이미 100% 완료된 Task를 제외합니다.

**구현 위치**: `report.js:getNextWeekTasks()` — `getTasksInRange()` 후 `progress < 100` 필터

### Copy Table 기획팀 제목 (planningTitle)
월 업데이트 보고서의 Copy Table 클릭 시, 기획팀 업무 제목을 사용합니다.

**테이블 헤더**: `N월 업데이트 항목 | 내용 | 담당자 | 진척률` (N은 해당 월 숫자)
**별도 제목 행 없음**: 헤더 첫 번째 컬럼에 `N월 업데이트 항목`으로 통합

**담당자 정렬**: `_sortAssignees()` — 정재화가 포함된 경우 맨 앞으로 이동, 나머지 순서 유지

**데이터 흐름**:
1. Dooray 본문의 `위키:` 바로 다음 줄 `기획:` 필드에서 링크 텍스트 파싱 (`syncManager.parseProjectInfoFromBody`)
2. `[프로젝트코드/번호 제목](dooray://...)` → 프로젝트코드/번호 제거 → 제목만 추출
3. `N월 업데이트 > ` 중간 경로 패턴 제거 (바둑 등 프로젝트)
4. `task.planningTitle`에 저장 (Sync 시 항상 최신값으로 갱신)
5. `report.js:generateTableHtml()`에서 `planningTitle`이 있으면 우선 사용, 없으면 기존 `[platform] project` 형식
6. 그룹 모드: 그룹 내 Task 중 하나라도 `planningTitle`이 있으면 그룹 전체에 적용

**파싱 규칙**:
- `위키:` 행 바로 다음 줄의 `기획:`만 허용 (본문 내 다른 `기획:`은 무시)
- `.+?` (lazy match): 링크 텍스트 내 중첩 대괄호 `[PC포커/클래식]` 허용
- `decodedBody` 사용: HTML 엔티티 (`&#91;`→`[`, `&gt;`→`>`) 디코딩 후 매칭
- `N월 업데이트 > ` 패턴 제거: 파싱 시점 + 출력 시점 이중 적용

**예시**:
- 포커: `[한게임포커통합-업데이트관리/2224 [PC포커/클래식/홀덤] CMS 원화 교체](dooray://...)` → `[PC포커/클래식/홀덤] CMS 원화 교체`
- 바둑: `[보드캐쥬얼-업데이트-대시보드/842 [PC바둑오목] 3월 업데이트 > 사활 컨텐츠: 오늘의 사활](dooray://...)` → `[PC바둑오목] 사활 컨텐츠: 오늘의 사활`

**planningTitle UI 표시**:
- Task 편집 모달의 Project URL 아래에 "기획 제목" 읽기 전용 필드
- `planningTitle`이 있는 Task만 표시 (없으면 숨김)
- HTML: `#planningTitleRow`, `#planningTitleDisplay`
- CSS: `.planning-title-display` (읽기 전용 박스)

**구현 위치**:
- 파싱: `syncManager.js:parseProjectInfoFromBody()` — regex + `N월 업데이트 > ` 제거
- 매핑: `syncManager.js:convertToTask()` — `planningTitle` 필드
- Sync 갱신: `syncManager.js:addNewTasksWithRemoteInfo()` — `planningTitle`은 항상 최신값으로 덮어쓰기 (`!existing` 조건 없음)
- 보고서 프리페치: `report.js:fetchMissingPlanningTitles()` — 누락 Task를 Dooray API로 개별 조회
- 출력: `report.js:generateTableHtml()` — grouped/individual 모두 지원 + `N월 업데이트 > ` 출력 시 재정리
- UI: `index.html` `#planningTitleRow` + `main.js` 편집 모달 채우기

### Planned (Placeholder) 그룹
Task가 없는 예상 프로젝트를 Gantt에 미리 표시하는 기능

**데이터**: `AppState.projectPlaceholders` 배열
```javascript
{
    id: 'ph_xxx',
    platform: 'PC포커',           // 매핑된 플랫폼
    project: '브로드캐스팅 고도화',  // 프로젝트명
    releaseMonth: '2026-04',      // YYYY-MM
    planning: '포커게임기획팀',     // 담당 조직
    planner: '홍길동',            // 기획 담당자명
    category: '',
    createdAt: '...'
}
```

**비주얼 스타일**:
- 보라색 테마 (CSS 변수로 사용자 커스터마이징 가능)
- `--group-placeholder-text`: 텍스트 색상 (기본 #7B1FA2)
- `--group-placeholder-bg`: 배경 색상 (기본 #F3E5F5)
- `--group-placeholder-badge-bg`: 뱃지 배경 색상 (기본 #F3E5F5)
- 그룹 헤더의 border-top도 보라색 (일반 그룹의 파란 border-top과 구분)
- hover 시 배경 유지 (일반 그룹처럼 파란색으로 변하지 않음)
- 플랫폼 폰트: font-weight 500 (일반 그룹 600보다 가벼움)

**Planning 차트 기획자 표시**: Planned 프로젝트에 기획 담당자명(`planner`)을 인라인 텍스트로 표시
- "Planned" 뱃지 제거, 기획자명만 표시 (`.ph-planner-text`, 색상 #999, 10px)
- 기획자명이 없어도 `&nbsp;`로 공간 유지 (레이아웃 일관성)
- 데이터: `projectPlaceholders[].planner` 필드

**정렬**: 같은 releaseMonth 내에서 일반 그룹이 위, Planned 그룹이 아래 배치 (`gantt.js` groupOrder.sort)

**구현 위치**:
- 데이터: `state.js` → `AppState.projectPlaceholders`
- 색상: `state.js` → `DEFAULT_COLOR_SETTINGS` (2벌), `storage.js:applyColorSettings()`, `main.js` (load/save/reset/import 7곳)
- 렌더: `gantt.js:groupTasksByPlatformProject()`, `gantt.js:renderGroupHeader()`
- CSS: `styles.css` → `.group-header-row.placeholder`, `.group-placeholder-badge`
- Analytics: `styles.css` → `.ad-placeholder-row` (Planned 배경색 `--group-placeholder-bg` 연동)
- 숨김: `AppState.hidePlanned` → `gantt.js`에서 placeholder forEach 스킵
- 월 필터: `AppState.plannedVisibleMonths` (null=전체, Set=선택된 월만) → `main.js` 드롭다운 UI + `gantt.js` 필터

## Plan Import (Excel/Google Sheets → Planned 자동 등록)

연간 업무 계획 Excel 파일 또는 Google Sheets에서 Planned를 자동 등록하는 기능

**모듈**: `js/plannedImport.js` (PlannedImport 객체)

### 파싱 로직
1. SheetJS로 xlsx 읽기 (CDN 로드됨)
2. 시트에서 "업무명" 헤더 행 찾기 → 열 인덱스 매핑
3. 행 순회하며:
   - Col A에 "N월" 패턴 → 현재 월 업데이트
   - Col B 업무명에서 플랫폼 접두사 추출
   - 담당자 열(게임기획팀/서비스기획팀/사업팀) 확인

### 매핑 테이블

| Excel 접두사 | Teamplay platform |
|---|---|
| (공통) | 공통 |
| (PC) | PC포커 |
| (클), (모), (모바일) | 포커클래식 |
| (PC/클) | PC포커 |

| Excel 담당자 열 | Teamplay planning |
|---|---|
| 게임기획팀 | 포커게임기획팀 |
| 서비스기획팀 | 포커서비스기획팀 |
| 사업팀 | 포커사업팀 (기본 Off) |

### 동기화 (Google Sheets / Excel → 기존 Planned 비교)
- **비교 키**: `platform|project|planning` (조직 포함하여 정확한 매칭)
- **중복 제거**: `deduplicateParsedEntries()` — 같은 키의 엔트리가 여러 월에 있으면 최신 월만 유지
- **상태 분류**: 추가(신규) / 변경(점검월 등 변경) / 삭제(시트에 없음) / 동일
- **적용**: ID 기반 업데이트 (`findIndex(p => p.id)`) — 객체 참조 대신 안정적 매칭

### 상태 필터 버튼
미리보기 헤더 오른쪽에 상태별 필터 버튼 표시 (전체/추가/변경/삭제/동일)
- 0건이어도 항상 표시 (`.zero` 클래스로 opacity 감소)
- 상태 뱃지 색상과 동일 (추가=초록, 변경=파랑, 삭제=빨강, 동일=회색)
- `statusFilterValue` 상태로 필터링, `_origIdx` 추적으로 체크박스 이벤트 연결

### 필터 시스템
- **월 필터**: 범위(시작~끝월) 또는 특정월(개별 체크) 선택
- **팀 필터**: 파싱된 팀별 체크박스 (사업팀은 기본 Off)

### 폴더 자동 로드
- 특정 폴더를 설정하면 모달 열 때 최신 `.xlsx` 파일 자동 탐색 (mtime 기준)
- `electronAPI.listFiles({ withStats: true })` → `electronAPI.readFile({ encoding: 'binary' })`
- 폴더 경로: `localStorage` 저장 (`teamScheduler_plannedImportFolder`)
- `~$` 임시 파일 자동 제외

### IPC (electron-main.js)
- `read-file`: `encoding: 'binary'` → Buffer를 base64로 전달
- `list-files`: `withStats: true` → 파일별 `{ name, mtime, size, isFile }` 반환

### UI 구성
탭 기반 소스 선택 (Google Sheets / Excel 파일)

```
┌────────────────────────────────────────────────┐
│ 📅 Plan Import                             ✕   │
├────────────────────────────────────────────────┤
│ [Google Sheets] [Excel 파일]  ← 탭 전환        │
│ ─────────────────────────────────────────────  │
│ Sheets 탭:                                     │
│   [URL____________________________] [동기화]    │
│   📄 시트 제목                    [열기] [로그]  │
│ Excel 탭:                                      │
│   [📂 파일 선택]  파일명.xlsx                    │
│ ─────────────────────────────────────────────  │
│ 월 필터: ○ 범위 ● 특정월  [4월][5월]... [해제]  │
│ 팀 필터: ☑게임기획 ☑서비스기획 ☐사업            │
├────────────────────────────────────────────────┤
│ 미리보기 | 모두 선택    [전체][추가][변경][삭제][동일]│
│ No ☑ 월  플랫폼  프로젝트  조직  담당자  상태    │
├────────────────────────────────────────────────┤
│                    [취소]  [12개 Planned 추가]   │
└────────────────────────────────────────────────┘
```

**탭 전환**: `PlannedImport.switchSourceTab(tab)` — URL 유무에 따라 자동 선택
**특정월 해제**: 선택된 월 체크박스 전체 해제 (`clearMonthPick()`)
**필터 레이아웃**: 월 필터와 팀 필터는 항상 세로 배치 (`flex-direction: column`)

**구현 위치**:
- 모듈: `js/plannedImport.js`
- 모달: `index.html` (plannedImportModal)
- 리스너: `js/main.js` (plannedImportBtn, file change 등)
- 스타일: `styles.css` → `.modal-planned-import`, `.planned-import-*`, `.pi-source-tabs`, `.pi-tab-panel`, `.pi-sf-btn`
- 사이드 패널: `index.html` → `#plannedImportBtn` ("Plan Import")

### 동기화 버튼 상태 표현
동기화 버튼이 진행 상태를 시각적으로 표현합니다.

| 상태 | 텍스트 | 아이콘 | 색상 |
|------|--------|--------|------|
| 초기 | 동기화 | `fa-sync-alt` | 초록 (#0F9D58) |
| 진행 중 | 동기화 중... | `fa-sync-alt fa-spin` | 초록 (disabled) |
| 완료 | 동기화 완료 | `fa-check` | 초록 (#0F9D58) |
| 실패 | 동기화 | `fa-sync-alt` | 초록 (원래 상태) |

- 열기 버튼: `<a>` → `<button>` 변경, 테두리 있는 보조 버튼 스타일
- 모달 열 때 `resetState()`에서 버튼 초기화
- CSS: `.btn-sheets-sync`, `.btn-sheets-sync.synced`, `.btn-sheets-open`

### Sync 로그 파일 저장
동기화 실행 시 로그를 별도 JSON 파일로 저장합니다.

- **저장 경로**: `{appPath}/data/planned-sync-logs/planned-sync-{timestamp}.json`
- **절대 경로**: `electronAPI.getAppInfo().path`로 앱 경로 획득 + 캐싱 (`_logFolderPath`)
- **UI 버튼 그룹**: 로그 | Export | 폴더열기 (`psl-btn-group`)
- **Export**: 전체 로그를 `planned-sync-logs-export-{date}.json`으로 다운로드 폴더에 저장
- **폴더 열기**: `electronAPI.openFolder(absolutePath)` — 상대 경로 사용 금지

### Planning 차트 Sync 뱃지
Plan Import 동기화 적용 후 Planning 차트의 해당 Planned 프로젝트에 뱃지 표시

| 뱃지 | 색상 | 의미 |
|------|------|------|
| `추가` | 초록 (#188038, 배경 #E6F4EA) | 새로 추가된 Planned |
| `변경` | 파랑 (#1a73e8, 배경 #E8F0FE) | 점검월 등 변경된 Planned |

- **런타임 플래그**: `ph.syncBadge` = `'add'` / `'change'` (placeholder 객체에 직접 설정)
- **자동 소멸**: 런타임 전용 → 앱 재시작 시 제거, `storage.js` save/load에서 제거
- **렌더링**: `planningOverview.js` — 플랫폼 뱃지 옆에 표시 (`project-info-badge-line`)
- CSS: `.ph-sync-badge`, `.ph-sync-add`, `.ph-sync-change`

### 상태 필터 토글
미리보기 상태 필터 버튼 클릭 시 같은 버튼을 다시 클릭하면 '전체'로 복귀합니다.

### 중복 Placeholder 경고
Gantt/Planning 차트에서 동일 `platform|project` 키의 Placeholder가 여러 개 있으면 ⚠ 경고 표시.
- **가시성 필터**: `hidePlanned` 상태를 반영하여 **보이는** Placeholder만 대상으로 중복 검사
- Gantt: `gantt.js` — `hidePlannedGantt` + `hidePlannedGanttForceAll` + `starred` 체크
- Planning: `planningOverview.js` — `hidePlannedPlanning` + `hidePlannedPlanningForceAll` + `starred` 체크

## 색상 설정 시스템

Settings에서 색상을 사용자가 커스터마이징할 수 있음

**데이터 흐름**:
```
state.js (DEFAULT_COLOR_SETTINGS × 2벌)
  → storage.js:applyColorSettings() (CSS 변수 적용)
  → index.html (color picker 입력)
  → main.js (load/save/reset/import - 각 설정별 7곳)
```

**주의**: `state.js`에 `DEFAULT_COLOR_SETTINGS`가 2벌 있으므로 새 색상 설정 추가 시 둘 다 수정 필요

### Color 서브탭
Settings > Appearance > Color 내 서브탭으로 카테고리 분리:
- **Gantt**: 기본 Gantt 차트 색상 (기존)
- **Team**: Team 차트 카테고리 색상
- **Analytics**: Analytics 차트 색상
- **Report**: 보고서/Task Log 색상 (별도 탭으로 분리)

### 보고서 배경색 3단계
업무보고서 Task 항목의 진행률 배경색을 3단계로 구분:

| 상태 | CSS 클래스 | 색상 설정키 | 기본값 |
|------|-----------|------------|--------|
| 완료 (100%) | `progress-complete` | `reportComplete` | `#E8F0FE` |
| 진행중 (1-99%) | `progress-inprogress` | `reportInProgress` | `#ffffff` |
| 준비 (0%) | `progress-zero` | `reportZero` | `#FFF0F0` |

**CSS 변수**: `--report-inprogress-bg`
**구현 위치**: `state.js` 2벌, `storage.js:applyColorSettings()`, `index.html` Color > Report 탭, `main.js` 7곳, `report.js:generateTableHtml()`

## 조직명 정규화

Dooray 본문에서 파싱된 구 조직명을 신 조직명으로 자동 변환합니다.

| 구 이름 | 신 이름 |
|---------|---------|
| 포커기획팀 | 포커게임기획팀 |
| 포커사업팀 | 포커서비스기획팀 |
| 포커운영팀 | 포커사업팀 |

- `(포커게임기획팀)(포커기획팀)` 중복 표기 → 신 이름 우선 선택
- 구현: `syncManager.js:ORGANIZATION_NAME_MAP`, `normalizeOrganizationName()`
- 적용 시점: `parseProjectInfoFromBody()` 내 조직 파싱 직후

## 주간보고 그룹명 (Settings)

Settings의 "주간보고 그룹명" 탭에서 조직을 보고서 그룹으로 매핑합니다.

| 그룹 | 매핑되는 조직 |
|------|-------------|
| 기획팀 | 포커게임기획, 포커게임기획팀 |
| 사업팀 | 사업, 포커서비스기획, 포커서비스기획팀 |
| 운영 | 포커운영, 포커운영팀, 포커사업팀 |

- 구현: `state.js`, `weeklyReportGenerator.js`, `main.js:resetOrgSettings()`
- **Order ↔ 그룹명 동기화**: `syncOrgGroupNamesToOrder()` (저장 시), `syncOrderListWithOrgGroups()` (로드 시)
- **Order 동적 생성**: HTML 하드코딩 금지, localStorage/organizationGroups에서 동적 생성
- **Order 옆 ⚙ 버튼**: 클릭 시 Settings 주간보고 그룹명 탭 열기 (`wrOrderSettingsBtn`)

## Weekly 주간보고 자동화

### 본문 업데이트 후 열기
"본문 업데이트" 버튼 옆에 "열기" 버튼으로 해당 Dooray 업무를 외부 브라우저에서 열 수 있습니다.

**구현 위치**:
- 버튼: `index.html` → `weeklyReportOpenPostBtn` (`btn-secondary`)
- 함수: `main.js:openWeeklyReportPost()` → `electronAPI.openExternal(url)`
- URL: `https://nhnent.dooray.com/task/${projectId}/${postId}` (`_weeklyReportResult`에서 추출)

## 팀원별 업무 이력 (Work History)

팀원이 특정 기간 동안 어떤 업무를 했는지 조회하고 복사하는 전용 모달입니다.

**진입점**: 사이드 패널 → Work History 또는 `H` 키
**모듈**: `js/memberHistory.js` (MemberHistory 싱글턴)

### 핵심 기능
- **팀원 선택**: 버튼 나열 (색상 dot + 이름, 드롭다운 아님), Display Groups 포함
- **기간 선택**: 주간/월간/직접선택/월 버튼(1~12) + 이전/다음 네비게이션
- **월 버튼**: 1~12 복수 선택, 비연속 월 지원, ◀▶로 연도 변경
- **그룹핑**: 프로젝트별 / Task별 / 날짜별 토글
- **표시 옵션**: Task명 on/off, 세부내용 on/off 토글
- **Copy**: HTML + Markdown 듀얼 클립보드 복사 (Dooray 붙여넣기 호환, `##`/`###`/`-` 마크다운 형식)
- **전체 건수**: Summary에 `(전체 N건)` 표시 — Work 마크 있는 Task 외에 배정된 전체 Task 수

### 데이터 소스
- Work 마크: `AppState.workLogs[taskId][dateStr]`
- 작업 내용: `AppState.dailyNotes["taskId_dateStr"]`
- 다중 담당자: `task.assignee.split(',')` → includes 체크
- **그룹 담당자**: Display Group 선택 시 `.every()` 매칭 (그룹 멤버 전원이 assignee에 포함된 Task만)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/memberHistory.js` | 전체 모듈 (데이터 수집, 렌더링, 복사) |
| `index.html` | 모달 HTML (`memberHistoryModal`) + 사이드 패널 버튼 |
| `styles.css` | `.modal-member-history`, `.mh-*` 스타일 |
| `js/main.js` | 이벤트 바인딩 + H 단축키 + Escape 핸들러 |

## 플랫폼 관리 (Settings)

Settings의 "플랫폼 관리" 탭에서 플랫폼을 매핑합니다. 주간보고 그룹명과 동일한 UI 패턴 (대표 이름 ← 별칭들).

**데이터 형식**: `{ "PC포커": ["PC", "FX_PC"], "포커클래식": ["클래식"] }`
**Save 동작**: 별칭 → 대표 이름으로 실제 Task 데이터 변환 + 매핑 저장

### 기능
- **자동 플랫폼 표시**: 저장된 매핑 그룹 + Task에 있지만 미매핑된 플랫폼 모두 표시
- **Add Task/Edit Task 연동**: Platform/Organization 라벨 옆 ⚙ 버튼 → Settings 해당 탭 열기
- **구 형식 자동 마이그레이션**: `{ "PC": "PC포커" }` → `{ "PC포커": ["PC"] }`

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/main.js` | `renderPlatformMapGroups()`, `addPlatformMapGroup()`, `savePlatformMap()`, `getPlatformMappings()`, `getPlatformDisplayName()` |
| `index.html` | `orgTabPlatforms`, `platformMapActions`, `managePlatformFromTaskBtn`, `manageOrgFromTaskBtn` |
| `styles.css` | `.org-map-list`, `.org-map-group`, `.btn-icon-inline` |

## Planned 프로젝트 별표 (Star)

Planning 차트에서 Planned 프로젝트를 Ctrl+클릭하면 별표가 토글됩니다.
별표된 Planned 프로젝트는 Hide Planned가 켜져 있어도 Gantt/Planning 차트에서 계속 표시됩니다.

### 동작
- **Ctrl+클릭**: Planning 차트에서 placeholder 프로젝트 별표 토글
- **별표 표시**: Planning 차트 - 노란색 아웃라인 + ★ 아이콘, Gantt - 프로젝트명 앞 ★
- **Hide Planned 무시**: `AppState.hidePlanned`가 true여도 `ph.starred === true`면 표시
- **월 필터 무시**: starred 프로젝트는 `plannedVisibleMonths` 필터도 무시
- **영속성**: `projectPlaceholders[].starred` 필드에 저장

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/views/planningOverview.js` | Ctrl+click 핸들러, `togglePlaceholderStar()`, ★ 렌더링 |
| `js/views/gantt.js` | `hidePlanned` 가드에서 starred 통과, 그룹 헤더 ★ CSS |
| `styles.css` | `.starred` 아웃라인, `.ph-star-icon`, `.ph-star-badge` |

## 프로젝트 상세 → Gantt 이동

Planning 차트에서 프로젝트 클릭 → 팝업의 Task 클릭 시 Gantt 차트로 이동하고 해당 Task가 하이라이트됩니다.

### 동작
1. Task 행 클릭 → 팝업 닫힘
2. Hide Done/Bypass로 숨겨진 Task면 자동 해제
3. Gantt 뷰로 전환 (그룹 자동 펼침)
4. Task 행으로 스크롤 + 노란색 깜빡임 하이라이트 (3초)

### 구현 위치
- `js/report.js`: `navigateToGanttTask()` — Hide Done/Bypass 자동 해제 + Task 행 `data-task-id` + 클릭 핸들러
- `js/commandPalette.js`: `_navigateToTask()` — 동일한 Hide Done/Bypass 자동 해제 적용
- `styles.css`: `.project-task-row`, `.project-task-highlight`, `@keyframes projectTaskFlash`

## Planning 차트 Team Separator

Planning 차트에서 팀 간 구분선 스타일입니다.

**구현 방식**: inline style이 아닌 CSS 변수 (`--team-border-width`, `--team-border-color`)를 `<tr>` 요소에 설정
**border-collapse 충돌 해결**: `:has(+ tr.planning-team-start)` CSS로 이전 행의 `border-bottom` 제거하여 separator가 항상 표시됨

**구현 위치**:
- `planningOverview.js`: `<tr>` 요소에 CSS 변수 설정 + `planning-team-start` 클래스
- `styles.css`: `.planning-overview-table tbody tr:has(+ tr.planning-team-start) td` + `tr.planning-team-start td`

**Settings 변경 즉시 반영**: `addTeam`, `updateTeamName`, `deleteTeam`, `moveTeam` 등에 `App.render()` 호출

## Reopen (수정 재작업)

완료된 Task에 수정이 필요할 때 상태 추가 없이 플래그로 관리합니다.

### 플래그 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| `reopenedAt` | ISO string \| undefined | 재오픈 시점 (있으면 수정 배지 표시) |
| `reopenCount` | number | 누적 재오픈 횟수 |
| `firstDoneAt` | ISO string | 최초 완료일 (Reopen 후 재완료 시 보존) |

### 동작 흐름
```
Done (100%) → Status를 Doing/Ready로 변경
              → reopenedAt = now, reopenCount += 1, progress = 95%
              → '수정' 배지 표시 (빨강)
              → 작업 후 다시 Done 처리
              → reopenedAt 삭제 (배지 해제), reopenCount/firstDoneAt 보존
```

### 구현 위치
- 상태 전환: `tasks.js:updateTaskStatus()` — Done → Doing/Ready 감지
- 배지 렌더링: `gantt.js:renderRowCells()` — `task.reopenedAt` 체크
- CSS: `.reopen-badge` (빨강 #e53935)

## Smart Filter (할일 알림)

Filter Bar 아래 스트립으로 오늘/금주/지연/수정 카운트를 표시하고, 클릭 시 Gantt를 필터링합니다.

### 필터 항목
| 필터 | 조건 | 색상 |
|------|------|------|
| 지연 | endDate < 오늘 & status != Done/Bypass | 빨강 |
| 오늘 | startDate <= 오늘 <= endDate & Doing/Ready + 지연 + Reopen | 파랑 |
| 금주 | 이번 주(월~일) 범위 내 작업 대상 | 초록 |
| 수정 | reopenedAt 존재 & !Done | 빨강 |
| 이번달 | releaseMonth 또는 날짜 범위가 이번달에 해당 (통계만, 필터 없음) | 보라 |

### 동작
- 클릭: 해당 조건 Task만 Gantt에 표시 (토글)
- `T` 키: 순차 이동 (지연 → 오늘 → 금주 → 수정 → 해제 → 지연 ...) `SmartFilter.cycle()`
- 숫자 0: 비활성 회색 처리
- 지연 > 0: 깜빡임 애니메이션
- 앱 시작 시: 지연/수정 건이 있으면 토스트 알림 (1회)
- 뱃지 스타일: `border-radius: 4px`, `border: 1px` (btn-secondary와 동일)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/smartFilter.js` | SmartFilter 모듈 (calculate, update, toggle, cycle, getFilteredTaskIds, showStartupToast) |
| `index.html` | `.smart-filter-strip` HTML |
| `styles.css` | `.smart-filter-strip`, `.sf-*` 스타일 |
| `js/main.js` | `render()` 내 `SmartFilter.update()`, `init()` 내 `showStartupToast()`, `T` 키 핸들러 |
| `js/views/gantt.js` | `render()` 내 `SmartFilter.getFilteredTaskIds()` 적용 |

### 팀원 필터
Smart Filter Strip 오른쪽에 팀원 버튼을 표시하여 특정 팀원의 Task만 필터링합니다.

**동작**:
- 팀원 클릭: 해당 팀원 Task만 Gantt에 표시 (토글)
- `M` 키: 순차 이동 (팀원1 → 팀원2 → 팀원3 → 해제) `SmartFilter.cycleMember()`
- 할일 필터(T)와 동시 사용 가능 (교집합 필터링)
- 활성 시 요약 스트립 표시: Doing/Ready/Hold/Done 카운트 + Plan/Actual MD + Gap

**버튼 구성**: 팀원별 색상 dot + 이름 + 활성 Task 수 (Done/Bypass 제외)

**구현 위치**:
- `js/smartFilter.js`: `_activeMember`, `toggleMember()`, `cycleMember()`, `renderMemberButtons()`, `updateMemberSummary()`
- `index.html`: `#sfMemberGroup` (동적 생성), `#sfMemberSummary`
- `styles.css`: `.sf-member`, `.sf-member-summary`, `.sfm-*`

## Member Dashboard (팀원 대시보드)

사이드 패널로 팀원별 현황을 한눈에 볼 수 있는 대시보드입니다. Report 패널과 동일한 디자인 패턴을 사용합니다.

### 진입점
- 사이드 패널 → "Member Dashboard"

### 기능
- **팀원 카드**: 멤버별 카드 (접기/펼치기), 멤버 색상 dot + 이름
- **통계 바**: Doing/Ready/Hold/Done/지연 텍스트 뱃지 + Plan/Actual MD + Gap (초과: 초록, 부족: 빨강)
- **Task 분류**: 지연 → 오늘 → 금주 → 기타 순서
- **그룹 라벨 뱃지**: 지연(빨강 배경 #FDECEA), 오늘(파랑 배경 #E8F0FE), 기타(회색 배경 #F1F3F4) — `border-radius: 2px`
- **Task 항목 레이아웃**: 2단 구성 — 왼쪽(점검월+플랫폼+프로젝트+업무명, 줄바꿈 허용) + 오른쪽(진행률+상태+MD+D-Day, 120px 고정폭)
- **D-Day 표시**: D+N (지연, 빨강), D-Day (주황), D-N (파랑), MM.DD (기본)
- **Gantt 연동**: Task 클릭 → `ReportView.navigateToGanttTask()` 재사용, hover → Gantt 행 하이라이트
- **필터 연동**: 카드의 필터 버튼 → SmartFilter 팀원 필터 토글
- **미배정 Task**: 별도 카드로 표시 (색상 #999)
- **실시간 갱신**: `App.render()` 호출 시 자동 업데이트
- **패널 너비**: 600px (Report 패널과 유사)

### 디자인 패턴
Report 패널 스타일 통일:
- CSS 변수 사용: `var(--text-primary)`, `var(--google-blue)`, `var(--google-green)` 등
- 폰트: 13px 기본, 카드 헤더 14px font-weight 600
- Task 항목: `report-list li` 스타일 (6px padding, `::before` 불릿)
- 필터 버튼: `report-copy-btn` 스타일
- 패널 전환: `.show` 클래스 토글 (transition 0.3s)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/memberDashboard.js` | MemberDashboard 모듈 (render, _calcStats, _getWeekTasks, _renderMemberCard, _renderTaskItem, _navigateToTask, _highlightTask) |
| `index.html` | `#memberDashPanel`, `#memberDashboardBtn` |
| `styles.css` | `.member-dash-panel`, `.md-card`, `.md-card-header`, `.md-stats`, `.md-task-item`, `.md-task-text`, `.md-task-info`, `.md-group-*` |
| `js/main.js` | 이벤트 바인딩, Escape 핸들러, `render()` 연동 |

## Display Groups (팀 표시 그룹)

다중 담당자를 하나의 그룹명으로 표시하고 필터링하는 기능입니다.

**데이터**: `AppState.teamDisplayGroups` — `{ "FX팀": ["정재화", "김보람", "김지인"] }`

### 핵심 규칙
- **표시**: `getDisplayAssignee()` (`team.js`) — 콤마 구분 담당자를 그룹명으로 변환 (모든 멤버 일치 시)
- **필터링**: `.every()` 매칭 — 그룹 멤버 **전원**이 Task의 assignee에 포함되어야 함
- **`.some()` 금지**: `.some()`은 멤버 중 한 명이라도 있으면 매칭되어 모든 Task가 걸림

### 적용 위치 (`.every()` 패턴)
| 파일 | 함수 | 용도 |
|------|------|------|
| `js/tasks.js` | `matchesAssigneeFilter()` | Gantt Assignee 필터 |
| `js/report.js` | `matchesAssigneeFilter()` | 보고서 Assignee 필터 |
| `js/smartFilter.js` | `_taskMatchesMember()` | 팀원 필터 |
| `js/memberDashboard.js` | `render()` 내 matchFn | 대시보드 카드 |
| `js/memberHistory.js` | `collectWorkHistory()` | 업무 이력 |
| `js/analytics.js` | `_renderMemberParticipation()` | 팀원별 참여 현황 |
| `js/excel.js` | 필터 로직 | Excel Export |

### 드롭다운/버튼 포함 위치
그룹명을 옵션으로 추가하는 곳:
- `main.js`: Gantt Assignee 필터 드롭다운
- `report.js`: 보고서 Assignee 필터 드롭다운
- `memberHistory.js`: 팀원 버튼 목록
- `excel.js`: Excel Export 체크리스트
- `smartFilter.js`: 팀원 필터 버튼
- `memberDashboard.js`: 팀원 카드

## Analytics 팀원별 참여 현황

Analytics 차트에서 팀원/그룹별 프로젝트, Task 참여 현황을 표시합니다.

### 레이아웃 (5컬럼 그리드)
```
팀원(72px) | 프로젝트(52px) | Task 완료 진행 대기 (1fr) | 지연(36px) | MD(52px)
```
- **Task 그룹**: Task 총수(볼드) + 완료/진행/대기/보류 상태 카운트 (`.ad-mp-task-group`)
- **지연**: 별도 컬럼, 0이면 회색, >0이면 빨강 (`.ad-mp-overdue-val.has-overdue`)
- **MD**: 별도 컬럼, 우측 정렬 (`.ad-mp-md-val`)
- Bypass Task 포함 (프로젝트 수, Task 수에 카운트)

### Total 월 슬라이더
Total 패널 하단에 1~12월 슬라이더를 제공하여 `releaseMonth` 기준 누적 필터링합니다.

- **상태**: `_totalSliderMonth` (기본값: 현재 월)
- **필터 로직**: `_applySliderFilter()` — `releaseMonth`의 월이 1 ~ sliderMonth 범위인 Task만 포함
- **적용 범위**: Total 패널 + 팀원별 참여 현황 동시 적용 (`update()`에서 1회 필터링)
- **12월 선택 시**: 필터 없음 (전체 Task)
- **바인딩**: `_bindTotalSlider()` — DOM 재생성 후 매번 호출

### 상태 판정 로직 (Total + 팀원 통일)
```javascript
if (status === 'Bypass') → bypass
else if (progress >= 100 || status === 'Done') → 완료
else if (status === 'Hold') → 보류
else if (status === 'Doing' || progress > 0) → 진행
else → 대기
```
- `TaskManager.getEffectiveProgress(task)` 사용
- Total과 팀원별 동일 로직 (숫자 불일치 방지)

### 호버 툴팁
팀원/그룹 행에 마우스 호버 시 참여 프로젝트 및 Task 목록 팝업 표시

**특징**:
- JS 관리 fixed position (CSS overflow 클리핑 방지)
- 뷰포트 경계 감지 (화면 밖으로 나가지 않게 위치 조정)
- 마우스를 툴팁으로 이동해도 유지 (delayed hide + hover 체크)
- 상태 아이콘: ✓ (Done, 초록), ● (기타, 상태별 색상), 지연 빨강, Ready 회색
- `max-height: 540px` (스크롤)

**구현 위치**:
- `js/analytics.js`: `_renderMemberParticipation()`, `_bindMpTooltipEvents()`, `_applySliderFilter()`, `_bindTotalSlider()`
- CSS: `.ad-mp-header`, `.ad-mp-row` (5컬럼 그리드), `.ad-mp-task-group`, `.ad-mp-overdue-val`, `.ad-mp-md-val`, `.ad-mp-tooltip-popup`, `.ad-mp-tip-*`, `.ad-total-slider-*`

## 데이터 보호

Gantt 차트 데이터 소실 방지를 위한 방어 장치:
- `saveData()`: AppState.tasks가 비어있으면 저장 스킵 + try-catch
- `visibilitychange` 이벤트: 화면 복귀 시 데이터 무결성 체크
- `cleanOrphanedData()`: tasks + teamTasks 양쪽 ID 확인 후 고아 정리 (workLogs/dailyNotes 보호)

> **참고**: workLogs/dailyNotes 보호에 대한 상세 규칙은 상단 "절대 보호 데이터" 섹션 참조

## 키보드 단축키

| 키 | 기능 |
|---|---|
| 1-7 | 뷰 전환 |
| N | 새 Task 추가 |
| F | Project 필터 |
| Q | 전체 필터 초기화 (Project/Service/Status/Assignee/Planning/SmartFilter) |
| D | Hide Done 토글 |
| X | Hide Bypass 토글 |
| P | Hide Planned 토글 (starred 유지) |
| Shift+P | Hide Planned 강제 (starred 포함 전부 숨김) |
| G | 그룹 전체 접기/펼치기 |
| T | 할일 필터 순환 (지연→오늘→금주→수정→해제) |
| M | 팀원 필터 순환 (팀원1→팀원2→팀원3→해제) |
| R | Report 패널 |
| L | Task Log 패널 |
| W | Work Sync 패널 |
| J | Sync 패널 |
| K | Weekly 패널 |
| H | Work History |
| B | Backup 모달 |
| E | Excel Export |
| S | 환경 저장 |
| Ctrl+F | 전체화면 토글 |
| Ctrl+P | Command Palette 열기 |
| Ctrl++/= | 앱 확대 |
| Ctrl+- | 앱 축소 |
| Ctrl+0 | 앱 원래 크기 |
| Ctrl+Z | 실행 취소 |
| Ctrl+Y | 다시 실행 |
| ` | 메뉴 열기/닫기 |
| Esc | 모달 닫기 |

## FX Collection (연출 모음)

Gantt 차트 그룹 프로젝트의 Task를 카테고리별로 정리하여 Dooray 업무에 댓글 또는 본문으로 작성하는 기능

### 진입점
- Gantt 그룹 헤더 **우클릭** → "연출 모음 생성"

### 모달 구성
```
+--------------------------------------------------+
| 연출 모음 - 서브앱 | 로우바둑이              X    |
+--------------------------------------------------+
| 대상 업무 URL                                     |
| [https://nhnent.dooray.com/task/...]              |
+--------------------------------------------------+
| 카테고리별 Task        | 미리보기  ✓ 27/31 완료  |
| [1] ☑ (미분류)   3/6   | (미분류)                 |
|   ☑ 스페셜판 연출      | | No | URL | 결과 |      |
|   ☑ 커팅 한 카드 수    | ...                      |
| [2] ☑ 대기실    10/10  |                          |
| [3] ☐ 인게임   12/12   |                          |
+--------------------------------------------------+
|          [취소] [복사] [본문 작성] [댓글 작성]     |
+--------------------------------------------------+
```

### 핵심 기능
| 기능 | 설명 |
|------|------|
| 카테고리 순서 | 번호 입력으로 즉시 정렬 (1,2,3...) |
| 카테고리 체크 | 체크 해제 시 해당 카테고리 전체 제외 (반투명 표시) |
| Task 체크 | 개별 Task 포함/제외 |
| URL 없는 Task | 자동 체크 해제 + ⚠ 표시 + 반투명 |
| URL 더블클릭 | 클립보드 자동 붙여넣기 (dooray.com 포함 시) |
| 프로그레시브 바 | Dooray 정보 로딩 진행률 (초록색) + 퍼센트 표시 |
| 모달 드래그 | 헤더 잡고 이동 가능 |

### Dooray 링크 형식
```
[클래식FX팀-업무관리/575 𝗙𝗫 &#91;서브앱&#93; 로우바둑이 &#91;작업&#93; Win, BigWin](dooray://1387695619080878080/tasks/4260398153378615660)
```
- Dooray API로 `taskNumber` + `subject` 조회 → 원본 링크 형식 생성
- `/project/tasks/POSTID` 형식 URL도 지원 (기본 프로젝트 ID fallback)
- fallback: 로컬 데이터로 `[플랫폼] 프로젝트 Task명` 구성

### API 호출
| 작업 | Method | Endpoint |
|------|--------|----------|
| Task 정보 조회 | GET | `/project/v1/projects/{pid}/posts/{postId}` |
| 댓글 작성 | POST | `/project/v1/projects/{pid}/posts/{postId}/logs` |
| 본문 작성 | PUT | `/project/v1/projects/{pid}/posts/{postId}` |

**본문 작성**: 기존 본문 GET → 기존 + `\n\n` + 새 내용 합쳐서 PUT (기존 보존)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/main.js` | `createGroupContextMenu()`, `showGroupContextMenu()`, `openFxCollectionModal()`, `_fetchDoorayInfoForTasks()`, `_renderFxCollectionModal()`, `_generateFxCollectionMarkdown()`, `_postFxCollectionComment()`, `_postFxCollectionBody()` |
| `styles.css` | `.modal-fxc`, `.fxc-*` 스타일 |

### 데이터 구조
```javascript
this._fxCollectionData = {
    groupKey, platform, project, tasks,
    categoryMap,           // { cat: [task, ...] }
    checkedTaskIds,        // Set<taskId>
    checkedCategories,     // Set<categoryName>
    categoryOrder,         // [cat1, cat2, ...]
    doorayInfo: {}         // taskId → { taskNumber, subject, doorayUrl }
};
```

## Team 차트 (Team Gantt)

팀 일정 관리용 별도 Gantt 차트 (`teamGantt.js`)

### 컬럼 구성
| 컬럼 | width | 설명 |
|------|-------|------|
| No. | 35px | 순번 |
| 카테고리 | 120px | 일정 종류 (회의, 교육, 면담 등) — 내부 필드명 `task.group` |
| Task | 250px | 업무명 |
| Tag | 80px | 부가 라벨 |
| Start | 90px | 시작일 |
| End | 90px | 종료일 |
| MD | 60px | 근무일수 |

**카테고리 vs Tag**: 카테고리는 "일정 종류"(회의/교육/면담), Tag는 "부가 라벨". UI에서는 "카테고리"로 표시하지만 내부 데이터 필드는 `task.group` 유지.
**카테고리/Tag 표시**: 일반 텍스트 (뱃지/span 래퍼 없음, Task 컬럼과 동일 폰트 크기)
**카테고리 색상 바**: 셀 왼쪽 4px 컬러 바 (`team-group-color-bar`)

**카테고리 색상**: Settings > Appearance > Color > Team 탭에서 카테고리별 바 색상 설정

**구현 위치**:
- 뷰: `js/views/teamGantt.js`
- 데이터: `AppState.teamTasks`, `AppState.teamGroupColors`
- 색상 관리: `main.js:renderTeamGroupColorList()`, `updateTeamGroupColor()`

## Service 컬럼 이번달 색상 바

Gantt Service 컬럼에 이번달(`releaseMonth === YYYY-MM`) Task를 시각적으로 표시합니다.

**동작**: `task.releaseMonth`가 현재 월과 일치하면 셀 왼쪽에 4px 색상 바 표시
**그룹 헤더**: 그룹 내 Task 중 이번달이 있으면 그룹 헤더 Service 셀에도 바 표시
**색상 설정**: Settings > Appearance > Color > Gantt > Service Column > Current Month Bar

**구현 위치**:
- JS: `gantt.js:renderRowCells()`, `renderGroupHeader()` — `.service-month-bar` span 삽입
- CSS: `.service-month-bar` (absolute, 4px, `var(--service-month-bar-color)`)
- 설정: `state.js` `serviceMonthBar`, `storage.js` `--service-month-bar-color`, `main.js` 7곳

## Command Palette (Ctrl+P)

VS Code 스타일 검색/실행 팔레트. Task 검색, 명령 실행, 팀원 필터, 뷰 전환, 프로젝트 그룹 이동을 지원합니다.

**단축키**: `Ctrl+P` (토글), `Esc` (닫기)
**모듈**: `js/commandPalette.js` (CommandPalette 싱글턴)

### 프리픽스 시스템
| 프리픽스 | 기능 | 예시 |
|---------|------|------|
| (없음) | Task 검색 | `로우바둑이` |
| `/` | 명령 실행 | `/sync`, `/settings` |
| `@` | 팀원 필터 | `@김보람` |
| `.` | 뷰 전환 | `.gantt`, `.planning` |

### 기본 결과 (빈 검색)
프리픽스 없이 빈 상태에서 최근 명령/프로젝트 그룹/뷰 목록 표시

### Task 검색
- 퍼지 매칭 (순차 문자 매칭)
- 플랫폼, 프로젝트, Task명, 담당자 대상
- 클릭 시: SmartFilter 해제 → 프로젝트 필터 적용 → 해당 Task 행 스크롤 + 하이라이트

### 명령 목록
| 명령 | 동작 함수 |
|------|----------|
| Sync | `App.openDooraySyncModal()` |
| Report | `ReportView.openPanel()` / `closePanel()` |
| Work History | `MemberHistory.openModal()` |
| Member Dashboard | `MemberDashboard.toggle()` |
| Settings | `App.openAppearanceModal()` |
| Task Log | `TaskLog.toggle()` |
| Work Sync | `WorkSync.openPanel()` / `closePanel()` |
| Weekly Report | `App.openWeeklyReportModal()` |
| Backup | `App.openBackupModal()` |
| Plan Import | `PlannedImport.openModal()` |

### 네비게이션
- `_clearFiltersAndNavigate(filterValue)`: SmartFilter 해제 → 그룹 펼침 → Gantt 전환 → `App.selectProjectFilterOption(filterValue)`
- `_navigateToTask(taskId)`: Task의 프로젝트 필터 적용 → 행 스크롤 + 하이라이트
- `_navigateToGroup(platform, project)`: `platform|project` 형식으로 프로젝트 필터 적용
- Arrow 키: 위아래 순환 (modulo 연산), Enter: 선택 실행

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/commandPalette.js` | 전체 모듈 (DOM 생성, 검색, 네비게이션, 키보드) |
| `js/main.js` | `CommandPalette.init()` + Ctrl+P 바인딩 + Escape 체인 (최우선) |
| `styles.css` | `.cmd-palette-overlay`, `.cmd-palette`, `.cmd-palette-item`, `.cmd-active` |

## 동적 z-index 모달 스태킹

모달/패널이 열릴 때 가장 최근에 열린 것이 항상 위에 표시됩니다.

### 동작 원리
- `state.js`에 글로벌 카운터 `_modalZCounter` (시작값 1000)
- `bringToFront(element)`: 카운터 증가 → `element.style.zIndex` 설정
- `window.bringToFront`로 전역 접근

### 적용 위치
- **열 때**: 모든 모달/패널의 open 함수에서 `bringToFront()` 호출 (~15곳)
- **클릭 시**: `document.addEventListener('mousedown')` 위임 핸들러로 클릭한 모달을 맨 위로

**클릭 위임 셀렉터**: `.modal, .report-panel, .member-dash-panel, .task-log-panel, .work-sync-panel, .duplicate-url-panel, .side-panel`

### 사이드 패널 z-index
햄버거 메뉴(사이드 패널)도 `bringToFront()` 적용:
- `toggleSidePanel()`: `bringToFront(sidePanel)` + overlay z-index 동기화 (`parseInt(sidePanel.zIndex) - 1`)
- 보고서 패널 등이 열려있어도 사이드 패널이 항상 앞으로 올 수 있음

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/state.js` | `_modalZCounter`, `bringToFront()` 유틸리티 |
| `js/main.js` | 모달 open 함수들 + mousedown 위임 핸들러 |
| `js/report.js` | `openPanel()` |
| `js/memberDashboard.js` | `openPanel()` |
| `js/taskLog.js` | `show()` |
| `js/workSync.js` | `openPanel()` |
| `js/duplicateUrl.js` | `show()` |
| `js/memberHistory.js` | `openModal()` |
| `js/excel.js` | `openModal()` |
| `js/plannedImport.js` | `openModal()` |

## Gantt 트리 커넥터 라인

그룹 내 Task들이 그룹 헤더의 하위 요소임을 시각적으로 표현하는 트리 라인입니다.

### 동작
- **Platform 컬럼**에 세로선(vertical line) + 가로 가지(horizontal branch) 표시
- Platform 컬럼 텍스트는 그룹 내 Task에서 숨김 (트리 라인만 표시)
- Project 컬럼 텍스트는 유지

### 비주얼
- **세로선**: `::before` — 컬럼 중앙(`left: 50%`), 위에서 아래 전체
- **가로 가지**: `::after` — 컬럼 중앙에서 오른쪽 끝까지
- **마지막 Task**: 세로선이 중앙에서 멈춤 (`bottom: 50%`)
- **색상**: 일반 그룹 `#B0BEC5`, Placeholder 그룹 `#CE93D8` (보라)
- **배경**: 그룹 헤더 배경색과 동일 (`--group-header-bg` / `--group-placeholder-bg`)

### 상태별 배경 오버라이드
hover, completed, selected, work-mark 등 상태에서도 Platform 셀 배경이 일관되게 유지되도록 CSS 오버라이드 필요

### 구현 위치
- `gantt.js`: `group-first-task`, `group-last-task`, `group-task-placeholder` 클래스 추가, Platform 텍스트 숨김
- `styles.css`: `.group-task td.col-platform::before/::after`, 상태별 오버라이드

## Today 시각 강화

### Today 세로선
Gantt 달력의 오늘 셀에 중앙 세로선을 표시하여 오늘을 명확히 식별합니다.

- **위치**: 셀 중앙 (`left: 50%`), 위에서 아래 전체
- **두께/색상**: 1px, `var(--today-bg, #4285F4)`, `opacity: 0.45`
- **적용 대상**: `td.col-day.today::after` + `.group-header-day.today::after`
- **z-index**: 3 (group-bar(2) 위, 헤더 삼각형(201) 아래)
- **노트 삼각형과 공존**: 노트 삼각형은 `::before`, Today 세로선은 `::after` 사용 (충돌 방지)

### Today 삼각형 마커
오늘 헤더 셀 하단에 작은 아래쪽 삼각형을 표시합니다.

- **위치**: `th.col-day.today::after`, `bottom: -4px`, `left: 50%`
- **크기**: 4px (border trick: `border-left/right: 4px transparent`, `border-top: 4px solid`)
- **색상**: `var(--today-bg, #4285F4)`
- **z-index**: 201

### 그룹 헤더 Today 배경
그룹 헤더의 오늘 셀에도 today 배경색이 적용됩니다.

- `.group-header-day.today`: `var(--today-cell-bg, #E8F0FE)`
- `.group-header-row.placeholder .group-header-day.today`: 동일
- `.group-header-row[data-locked="true"] .group-header-day.today`: 동일

### Daily Notes 삼각형 (노트 표시)
셀에 노트가 있으면 오른쪽 상단에 검정 삼각형을 표시합니다.

- **pseudo-element**: `::before` (Today 세로선 `::after`와 충돌 방지)
- **클래스**: `.has-note::before` — border trick으로 삼각형 생성
- **z-index**: 10 (Today 세로선(3)보다 위)

### 구현 위치
- `styles.css`: `td.col-day.today::after`, `th.col-day.today::after`, `.group-header-day.today`, `.has-note::before`

## Electron 창 제어 (Zoom / Fullscreen)

### Zoom (확대/축소)
`webFrame` API를 preload에서 노출하여 앱 전체 확대/축소를 지원합니다.

- `Ctrl + =` / `Ctrl + +`: 확대 (줌 레벨 +0.5)
- `Ctrl + -`: 축소 (줌 레벨 -0.5)
- `Ctrl + 0`: 원래 크기 (줌 레벨 0)

### Fullscreen (전체화면)
- `Ctrl + F`: 전체화면 토글

### 구현 위치
| 파일 | 역할 |
|------|------|
| `electron-preload.js` | `zoomIn()`, `zoomOut()`, `zoomReset()`, `getZoomLevel()`, `toggleFullscreen()` |
| `electron-main.js` | `toggle-fullscreen` IPC 핸들러 (`mainWindow.setFullScreen` 토글) |
| `js/main.js` | `handleKeydown()` — Ctrl+=/Ctrl+-/Ctrl+0/Ctrl+F 핸들러 |

## App Startup 최적화

Electron 앱 시작 시 흰 화면(white flash)을 방지하기 위한 최적화입니다.

### 동작 원리
1. `BrowserWindow` 생성 시 `show: false` — 창을 숨긴 채 시작
2. 앱 초기화 (`main.js:init()`) 완료 후 double `requestAnimationFrame`으로 렌더링 보장
3. `electronAPI.notifyAppReady()` → IPC `app-ready` → `mainWindow.show()`
4. Safety timeout 5초: IPC 실패 시에도 창 표시

### 구현 위치
| 파일 | 역할 |
|------|------|
| `electron-main.js` | `show: false`, `ipcMain.once('app-ready')`, 5초 safety timeout |
| `electron-preload.js` | `notifyAppReady: () => ipcRenderer.send('app-ready')` |
| `js/main.js` | init() 끝에서 double rAF 후 `notifyAppReady()` 호출, error handler에서도 호출 |
| `index.html` | 모든 로컬 script에 `defer` 속성 |

### 주의사항
- `defer`: HTML 파싱을 블로킹하지 않고 DOM 준비 후 순서대로 실행
- double rAF: 브라우저가 실제 paint를 완료한 후 IPC 전송 보장
- error handler: init 실패 시에도 빈 화면 방지를 위해 `notifyAppReady()` 호출

## 런타임 전용 필드 보호

Task 객체에 런타임에만 존재해야 하는 필드가 localStorage에 저장되지 않도록 보호합니다.

### 보호 대상 필드
| 필드 | 대상 | 용도 | 위험 |
|------|------|------|------|
| `_planningTitleFetched` | Task | planningTitle API 호출 완료 플래그 | 저장되면 앱 재시작 후 재조회 불가 |
| `syncBadge` | Placeholder | Plan Import 동기화 뱃지 (add/change) | 저장되면 영구 뱃지 잔존 |

### 보호 패턴
- **Task**: `saveData()` / `loadData()`에서 `delete c._planningTitleFetched`
- **Placeholder**: `saveData()`에서 `projectPlaceholders.map(ph => { delete c.syncBadge; })` (2곳), `loadData()`에서도 제거 (3곳)

**구현 위치**: `storage.js:saveData()`, `storage.js:loadData()`, `storage.js:applyEnvironmentData()`

## 참고 경로
- 기존 Team Schedule Manager: `E:\_Team Schedule Manager`
- 기존 DoorayMCP: `E:\_DoorayMCP`
- Dooray MCP JAR: `E:\_DoorayMCP\dooray-mcp-server-0.2.1-all.jar`
