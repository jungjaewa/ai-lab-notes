# Teamplay Skills 활용 가이드

## Skills란?

Skills는 Claude Code에서 자주 사용하는 작업을 명령어로 정의한 것입니다.
`/명령어` 형태로 호출하면 해당 작업의 컨텍스트와 절차를 자동으로 로드합니다.

---

## 사용 가능한 Skills

### 1. `/sync` - Dooray 동기화
Dooray 댓글을 조회하고 Task/Work 마크를 동기화합니다.

```
/sync                      # 기본 동기화 (설정된 업무 ID 사용)
/sync 4255999526738810112  # 특정 업무 ID로 동기화
```

**결과물**: 새 Task 목록, Work 마크 목록, 동기화 요약

---

### 2. `/status` - 팀 현황 조회
팀의 전체 업무 현황을 분석합니다.

```
/status              # 전체 현황
/status 김보람       # 특정 담당자 현황
/status 로우바둑이   # 특정 프로젝트 현황
```

**결과물**: 담당자별/프로젝트별 진행률, 과부하 경고

---

### 3. `/parsing` - 핵심 로직 레퍼런스
파싱 및 진행률 계산 로직을 확인합니다.

```
/parsing             # 전체 로직 확인
/parsing 제목        # 제목 파싱 로직만
/parsing 진행률      # 진행률 계산 로직만
```

**활용**: 로직 수정 시 참고, 버그 디버깅

---

### 4. `/deadline` - 마감 알림
마감 임박/지연 업무를 확인합니다.

```
/deadline            # 전체 마감 현황
/deadline 오늘       # 오늘 마감 업무
/deadline 이번주     # 이번 주 마감 업무
```

**결과물**: D-Day 목록, 지연 업무 경고

---

### 5. `/report` - 보고서 생성
주간/월간 보고서를 자동 생성합니다.

```
/report weekly       # 주간 보고서
/report monthly      # 월간 보고서
/report 김보람       # 특정 담당자 보고서
```

**결과물**: 마크다운 형식 보고서

---

### 6. `/task-fields` - Task 필드 정의
Task 객체의 모든 필드, 데이터 소스, 매핑 규칙을 확인합니다.

```
/task-fields           # 전체 필드 확인
/task-fields 필수      # 필수 필드만
/task-fields dooray    # Dooray에서 가져오는 필드
```

**활용**: 데이터 구조 확인, 필드 추가/수정 시 참고, Placeholder 필드 확인

---

### 7. `/debug` - 디버깅 가이드
문제 해결을 위한 디버깅 절차와 도구를 안내합니다.

```
/debug               # 전체 디버깅 가이드
/debug sync          # 동기화 문제
/debug gantt         # Gantt 차트 문제
```

**활용**: 버그 리포트 시 원인 추적, 데이터 불일치 해결

---

## 주요 기능 참조

### Plan Import (Excel → Planned 자동 등록)
연간 업무 계획 Excel 파일에서 Planned(placeholder) 항목을 자동 Import합니다.

| 항목 | 설명 |
|------|------|
| 모듈 | `js/plannedImport.js` |
| 진입점 | 사이드 패널 → Plan Import |
| Excel 파싱 | SheetJS (XLSX.read) |
| 플랫폼 매핑 | (공통)→공통, (PC)→PC포커, (클),(모)→포커클래식 |
| 조직 매핑 | 게임기획팀→포커게임기획팀, 서비스기획팀→포커서비스기획팀 |
| 폴더 자동 로드 | 지정 폴더에서 최신 .xlsx 자동 불러오기 (mtime 기준) |
| 중복 감지 | platform+project 기준으로 "기존" 배지 표시 |

### Task Selection Summary (Alt+Click)
Gantt 차트에서 Task를 Alt+Click으로 선택하여 MD 비교 및 진행률을 확인합니다.

| 항목 | 설명 |
|------|------|
| 선택 방법 | Alt + 클릭 (Task 컬럼) |
| Summary Bar | Selected, Progress, Plan MD, Actual MD, Gap, Eff |
| Excel 내보내기 | 선택 Task MD 상세 엑셀 다운로드 |
| 구현 위치 | `js/views/gantt.js` |

### 색상 설정 시스템
Settings에서 Gantt 차트 색상을 커스터마이즈할 수 있습니다.

| 설정 항목 | CSS 변수 | 기본값 |
|-----------|----------|--------|
| Service Month Bar | `--service-month-bar-color` | #4285f4 |
| Planned Text | `--group-placeholder-text` | #7B1FA2 |
| Planned Bg | `--group-placeholder-bg` | #F3E5F5 |
| Planned Badge Bg | `--group-placeholder-badge-bg` | #F3E5F5 |
| Group Header 계열 | `--group-header-*` | 각종 기본값 |

**주의**: `state.js`에 DEFAULT_COLOR_SETTINGS가 2곳에 존재하므로 반드시 둘 다 수정
**색상 추가 시**: `state.js`(2벌) + `storage.js`(applyColorSettings) + `index.html`(input) + `main.js`(7곳: load/save×2/reset/export/import/env)

### Hide 필터
| 필터 | 설명 | 단축키 | localStorage 키 |
|------|------|--------|-----------------|
| Hide Done | Done 상태 Task 숨김 | `D` | `teamScheduler_hideCompleted` |
| Hide Bypass | Bypass 상태 Task 숨김 | `X` | `teamScheduler_hideBypass` |
| Hide Planned | Planned 그룹 숨김 (starred 유지) | `P` | `teamScheduler_hidePlanned` |
| Hide Planned (All) | starred 포함 전부 숨김 | `Shift+P` | `AppState.hidePlannedForceAll` (비영구) |
| Planned 월 필터 | 월별 Planned 선택 표시 | - | `teamScheduler_plannedVisibleMonths` |

### Planned 그룹 정렬
- 같은 releaseMonth 내에서 일반 그룹이 위, Planned 그룹이 아래 배치
- Analytics 차트에서도 Planned 배경색이 Gantt과 동일하게 적용 (`--group-placeholder-bg`)

### Planned 프로젝트 별표 (Star)
Planning 차트에서 Ctrl+Click으로 Planned 프로젝트에 별표를 토글합니다.

| 항목 | 설명 |
|------|------|
| 토글 | Planning 차트에서 Ctrl+Click |
| 저장 | `placeholder.starred` boolean |
| Gantt 표시 | Project 컬럼에 CSS `::before` ★ + `starred` 클래스 |
| Planning 표시 | 노란색 1px outline (`outline: 1px solid #F9A825`) |
| Hide Planned | 별표된 항목은 숨김 제외 (Gantt + Planning 양쪽) |
| Shift+P | starred 포함 전체 숨김 (`hidePlannedForceAll`), 별표 데이터 보존 |
| 구현 | `planningOverview.js:togglePlaceholderStar()`, `gantt.js` |

### 플랫폼 관리
Settings 내 플랫폼 관리 탭에서 플랫폼 매핑을 관리합니다.

| 항목 | 설명 |
|------|------|
| 매핑 형식 | `{ "PC포커": ["PC", "FX_PC"] }` (target → aliases) |
| UI 패턴 | org-map-group (주간보고 그룹명과 동일) |
| 표시 | 저장된 매핑 + 미매핑 Task 플랫폼 모두 표시 |
| 진입점 | Settings → 플랫폼 관리 탭, Add/Edit Task Platform/Organization ⚙ 버튼 |
| 구현 | `main.js:renderPlatformMapGroups()`, `getPlatformMappings()` |

### 프로젝트 상세 → Gantt 이동
Planning 차트의 프로젝트 상세 팝업에서 Task 클릭 시 Gantt 차트로 이동 + 하이라이트합니다.

| 항목 | 설명 |
|------|------|
| 트리거 | 프로젝트 상세 팝업 Task 행 클릭 |
| 동작 | 그룹 펼침 → Gantt 전환 → 300ms 후 하이라이트 + 스크롤 |
| 하이라이트 | 3초간 yellow→blue 애니메이션 후 제거 |
| CSS 주의 | `border-collapse: separate` → `td`에 `!important` 필요 |
| 구현 | `report.js:navigateToGanttTask(taskId)` |

### 팀원별 업무 이력 (Work History)
팀원이 특정 기간 동안 어떤 업무를 했는지 조회하고 클립보드에 복사하는 전용 모달입니다.

| 항목 | 설명 |
|------|------|
| 모듈 | `js/memberHistory.js` |
| 진입점 | 사이드 패널 → Work History 또는 `H` 키 |
| 기간 선택 | 주간/월간/직접선택/월 버튼(1~12) + 이전/다음 네비게이션 |
| 월 버튼 | 1~12 복수 선택, 비연속 월 지원, ◀▶ 연도 변경 |
| 그룹핑 | 프로젝트별 / Task별 / 날짜별 토글 |
| 표시 옵션 | Task명 on/off, 세부내용 on/off 토글 |
| Copy | HTML + Markdown 듀얼 클립보드 (`##`/`###`/`-` 마크다운 형식) |
| 데이터 소스 | `AppState.workLogs` + `AppState.dailyNotes` |

### 조직명 정규화
Dooray 본문에서 파싱된 구 조직명을 신 조직명으로 자동 변환합니다.

| 항목 | 설명 |
|------|------|
| 구현 | `syncManager.js:normalizeOrganizationName()` |
| 매핑 | 포커기획팀→포커게임기획팀, 포커사업팀→포커서비스기획팀, 포커운영팀→포커사업팀 |
| 중복 처리 | `(신명)(구명)` 형태 → 신 이름 우선 |

### 보고서 하이라이트
- 보고서 패널 (621px 너비)에서 Task hover → Gantt 차트 행 하이라이트 (`task-highlight` 클래스)
- 패널 닫힐 때 잔존 하이라이트 자동 제거 (`report.js:closePanel()`)

### MD 컬럼: Actual | Plan 표시
MD 컬럼에 `Actual | Plan` 형식으로 실제 작업일수와 계획일수를 비교 표시합니다.

| 항목 | 설명 |
|------|------|
| 형식 | `3 | 5` (Actual MD &#124; Plan MD) |
| Actual 색상 | 기본 볼드, Actual >= Plan이면 초록 (`.md-done`) |
| Plan 색상 | 회색 (#999) |
| 그룹 헤더 | allTasks 기준 합산 (Hide Done 필터 무관) |
| 구현 | `gantt.js:renderRowCells()`, `renderGroupHeader()` |

### Gantt 컬럼 레이아웃
| 컬럼 | width | 비고 |
|------|-------|------|
| No | 35px | |
| Service | 70px | |
| Platform | 90px | |
| Project | 180px | text-align: left |
| Task | 320px | text-align: left |
| Status | 80px | |
| Progress | 80px | |
| Assignee | 120px | |
| Date | 90px | |
| DateEnd | 90px | |
| MD | 60px | Actual &#124; Plan 형식 |

**주의**: 너비 변경 시 `styles.css` 2곳 수정 (메인 컬럼 + 그룹 헤더 sticky)

### Weekly 주간보고 자동화
| 항목 | 설명 |
|------|------|
| Order 동적 생성 | HTML 하드코딩 금지, localStorage/organizationGroups에서 동적 생성 |
| Order ↔ 그룹명 동기화 | `syncOrgGroupNamesToOrder()` (저장 시), `syncOrderListWithOrgGroups()` (로드 시) |
| 본문 업데이트 후 열기 | `openWeeklyReportPost()` → `electronAPI.openExternal()` |
| Order 옆 ⚙ 버튼 | `wrOrderSettingsBtn` → Settings 주간보고 그룹명 탭 열기 |

### Planning 차트 Team Separator
| 항목 | 설명 |
|------|------|
| 구현 방식 | CSS 변수 (`--team-border-width`, `--team-border-color`) on `<tr>` |
| border-collapse 해결 | `:has(+ tr.planning-team-start)` CSS로 이전 행 border-bottom 제거 |
| Settings 즉시 반영 | `addTeam`, `deleteTeam`, `updateTeamName`, `moveTeam`에 `App.render()` |

### Sync 중복 Task 원격 정보 자동 채움
- Sync 시 URL 중복 Task 발견 → 빈 필드 자동 채움 (releaseMonth, dates, md, planning, assignee, wikiUrl)
- 구현: `syncManager.js:addNewTasksWithRemoteInfo()`

### Sync 새 업무 호버 하이라이트
- 새 업무 감지 목록에서 항목 hover → Gantt 차트 해당 Task 행 하이라이트
- 구현: `main.js:showNewTasks()` → `highlightTaskByDoorayUrl()`

### Reopen (수정 재작업)
완료된 Task를 다시 작업해야 할 때 상태 추가 없이 플래그로 관리합니다.

| 항목 | 설명 |
|------|------|
| 전환 | Status 드롭다운에서 Done → Doing/Ready 변경 시 자동 |
| 플래그 | `reopenedAt` (시점), `reopenCount` (횟수), `firstDoneAt` (최초 완료일) |
| 배지 | `수정` (빨강 #e53935) — Done 완료 시 해제, reopenCount/firstDoneAt 보존 |
| 진행률 | 95%로 리셋 |
| 구현 | `tasks.js:updateTaskStatus()`, `gantt.js:renderRowCells()` |

### Smart Filter (할일 알림)
Filter Bar 아래 스트립으로 할일 카운트를 표시하고, 클릭/T키로 Gantt를 필터링합니다.

| 항목 | 설명 |
|------|------|
| 위치 | Filter Bar 아래 `.smart-filter-strip` |
| 필터 | 지연(빨강), 오늘(파랑), 금주(초록), 수정(빨강), 이번달(보라/통계만) |
| 클릭 | 해당 조건 Task만 Gantt에 표시 (토글) |
| T 키 | 순차 이동: 지연→오늘→금주→수정→해제 (`SmartFilter.cycle()`) |
| 앱 시작 | 지연/수정 건 토스트 알림 (1회) |
| 모듈 | `js/smartFilter.js` |

### 배지 시스템 (5종 한글 통일)
| 배지 | 색상 | 의미 | 해제 |
|------|------|------|------|
| `신규` | 주황 (#ff9800) | Sync 신규 Task | 3시간 |
| `변경` | 보라 (#9b59b6) | 제목/프로젝트 변경 | 3시간 |
| `완료` | 초록 (#34a853) | Sync 완료 처리 | 3시간 |
| `작업` | 파랑 (#4285f4) | Work 마크 적용 | 3시간 |
| `수정` | 빨강 (#e53935) | Reopen 수정 재작업 | Done 시 수동 |

### FX Collection (연출 모음)
Gantt 그룹 헤더 우클릭으로 카테고리별 Task를 정리하여 Dooray에 작성합니다.

| 항목 | 설명 |
|------|------|
| 진입점 | Gantt 그룹 헤더 우클릭 → "연출 모음 생성" |
| 카테고리 순서 | 번호 입력으로 즉시 정렬 |
| 카테고리 제외 | 체크 해제 시 마크다운에서 제외 (반투명, Task 목록 유지) |
| Dooray 링크 | API로 taskNumber + subject 조회 → 원본 형식 링크 |
| URL 프로젝트 타이틀 | URL 입력 시 Dooray API로 제목 조회 → 파란 배경 표시 (syncProjectTitle 패턴) |
| URL 자동 감지 | 같은 그룹 내 "연출 모음" 포함 Task URL 자동 입력 |
| 댓글 작성 | POST `/posts/{id}/logs` |
| 본문 작성 | GET 기존 본문 → 합쳐서 PUT (기존 보존) |
| URL 더블클릭 | 클립보드 자동 붙여넣기 |
| URL 열기 버튼 | 우측 버튼 클릭 → 외부 브라우저 열기 |
| 프로그레시브 바 | 초록색, 퍼센트 + (n/total) 표시 |
| 모달 드래그 | 헤더로 이동 가능 (동적 생성 모달) |
| 구현 | `main.js` (openFxCollectionModal 등), `styles.css` (.fxc-*) |

### Service 컬럼 이번달 색상 바
Service 컬럼에 이번달 releaseMonth인 Task를 색상 바로 표시합니다.

| 항목 | 설명 |
|------|------|
| 조건 | `task.releaseMonth === currentMonth` (YYYY-MM) |
| 표시 | 셀 왼쪽 4px 색상 바 (`.service-month-bar`) |
| 그룹 헤더 | 그룹 내 Task 중 이번달이 있으면 바 표시 |
| 설정 | Settings > Gantt > Service Column > Current Month Bar |
| CSS 변수 | `--service-month-bar-color` (기본 #4285f4) |
| 구현 | `gantt.js:renderRowCells()`, `renderGroupHeader()` |

### Gantt 테이블 배경색
- `.gantt-table th, .gantt-table td` 기본: `background: #fff`
- sticky 컬럼과 day 셀 간 GPU compositing 차이 방지를 위해 모든 td에 명시적 #fff
- 특수 상태 (hover, completed, selected, weekend, holiday 등)는 더 구체적 selector에서 덮어씀

### Planned 예상 수 입력
- `type="text" inputmode="numeric"` 사용 (Electron에서 `type="number"` IME 이슈)
- `requestAnimationFrame`으로 포커스/선택 처리
- 구현: `gantt.js` plannedCountInput

---

## 새로운 Skill 추가 방법

### 1. Skill 파일 생성
`.claude/skills/` 디렉토리에 마크다운 파일 생성:

```markdown
# /명령어 - 설명

간단한 설명

## 사용법
\`\`\`
/명령어 인자
\`\`\`

## 동작
1. 단계 1
2. 단계 2

## 실행 절차

<command-name>

### 상세 절차
실제 수행할 작업 설명

</command-name>
```

### 2. 중요 로직 문서화 시 포함할 내용

| 항목 | 설명 |
|------|------|
| 정규식 패턴 | 파싱에 사용되는 정규식 |
| 데이터 흐름 | 입력 → 처리 → 출력 |
| 예외 처리 | 엣지 케이스 및 처리 방법 |
| 관련 파일 | 소스 코드 위치 |
| 변경 이력 | 수정 날짜 및 내용 |

---

## 개발 시 Skill 활용 패턴

### 패턴 1: 로직 확인 후 수정
```
1. /parsing 확인해줘
2. (로직 이해)
3. 제목 파싱에서 [완료] 태그도 처리하도록 수정해줘
```

### 패턴 2: 새 기능 추가
```
1. /parsing 참고해서 새로운 파싱 로직 추가해줘
2. (구현)
3. /parsing Skill에도 문서화해줘
```

### 패턴 3: 버그 디버깅
```
1. 진행률이 이상하게 계산돼
2. /parsing 진행률 로직 확인해줘
3. (원인 파악 및 수정)
```

### 패턴 4: 새 Skill 요청
```
1. 담당자 변경 기능을 Skill로 만들어줘
2. (Skill 파일 생성)
3. /assignee 테스트해줘
```

---

## Skill 유지보수

### 로직 변경 시
1. 코드 수정
2. 해당 Skill 문서 업데이트
3. 변경 이력 추가

### 새 규칙 추가 시
1. CLAUDE.md의 "중요 규칙" 섹션 업데이트
2. 관련 Skill 문서에 반영

---

## 자주 묻는 질문

**Q: Skill을 호출하면 자동으로 실행되나요?**
A: 아니요. Skill은 컨텍스트와 절차를 제공하며, 실제 실행은 사용자 확인 후 진행됩니다.

**Q: Skill 문서는 코드와 동기화되나요?**
A: 수동으로 동기화해야 합니다. 코드 변경 시 Skill 문서도 함께 업데이트하세요.

**Q: 새 Skill은 언제 만들어야 하나요?**
A: 반복적으로 사용되는 작업, 복잡한 로직, 팀원과 공유해야 하는 절차가 있을 때 만듭니다.
