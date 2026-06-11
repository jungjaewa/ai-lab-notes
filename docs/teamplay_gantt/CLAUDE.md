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
├── TEAM-WORKFLOW.md     # 팀 업무 워크플로우 (5단계 정의 + 시스템 분석)
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
│   ├── taskCreator.js   # Dooray 새 업무 생성 + 위키 + 팀플레이 댓글
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
- **팀원**: 정재화(팀리더), 김보람(애니메이터)
- **AI 팀원** (이름 앞 `✦`): ✦Jully(두레이·일정·데이터 분석), ✦Lumi(UI 이펙트 연출), ✦Annie(애니메이션)
  - 표시 그룹 `✦FX AI팀` = [✦Lumi, ✦Annie, ✦Jully] (구 이름 `✦Daily`→`✦Jully`, 구 그룹명 `✦AI FX팀`→`✦FX AI팀`)
- **숨김 멤버**: 김지인 (2026-04-04~ 전배, 데이터 보존)
- **특징**: 소규모 팀 + AI 팀원, 작업량 많음
- **핵심**: 스케줄 놓침 방지

### 팀원 숨김 기능
- Settings > 팀원 관리에서 👁 아이콘으로 숨김/해제 토글
- `member.hidden = true`, `member.hiddenAt = 'YYYY-MM-DD'` (숨김 날짜 기록)
- **숨김 시 안 보이는 곳**: Smart Filter, Daily Briefing, Member Dashboard, Work History, Add Task Assignee, Gantt Assignee 필터, Analytics 팀원별 참여 현황
- **보이는 곳**: Gantt Task Assignee 컬럼, 보고서 (기존 데이터 보존)
- Display Group: 숨김 멤버 태그에 취소선 + 반투명 표시
- 구현: `team.js` — `toggleMemberHidden()`, `isMemberVisible()`, `getVisibleMembers()`

#### 팀원 관리 목록 — 숨김 멤버 표시 on/off 토글
Settings > 팀원관리 탭 추가 폼 아래 우측 `👁 숨김 멤버 표시 (N)` 버튼으로, 숨김(전배) 멤버를 **관리 목록 화면에서** 보였다 안 보였다 토글합니다.
- **ON (기본)**: 숨김 멤버를 회색으로 목록에 표시 / **OFF**: 목록에서 완전히 숨김
- `TeamManager._showHiddenInList` (localStorage `teamScheduler_showHiddenInTeamList` 영속), `toggleShowHiddenInList()`, `_syncHiddenToggleBtn()`
- `renderTeamList()`: OFF면 숨김 멤버 `<li>` 렌더 스킵 — **단 색상 `index`는 유지**(다른 멤버 기본색 안 밀림), 순번(rowNo)도 표시 행만 카운트
- 숨김 멤버 0명이면 버튼 자체 숨김. 이 토글은 **팀원관리 목록 표시에만** 영향 (member.hidden 데이터·타 화면 정책 불변)
- 구현: `team.js`, `index.html` `#toggleHiddenMembersBtn`, `styles.css` `.btn-toggle-hidden-members`

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
- 새업무 등록 표기: `isNewTaskMarker()` — 공백 무관 ("새 업무 등록", "새업무등록", "새 업 무 등 록" 모두 감지)

**HTML 테이블 파싱 주의 (`_extractHtmlTable`, `extractTableAfterLink`)**:
- 표 셀 안에 `[@담당자](dooray://...members/...)` 멘션 링크가 있을 경우 테이블 탐색 범위를 잘라선 안 됨
- 탐색 범위 자르기 조건: `/tasks/` 경로를 포함하는 dooray 링크만 (업무 링크)
- `/members/` 경로 링크(멘션)는 무시 → regex: `/\[[^\]]+\]\(dooray:\/\/[^)]*\/tasks\//`
- 구현: `commentParser.js:_extractHtmlTable()`, `extractTableAfterLink()` 두 곳 모두 동일 패턴

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

## Dooray 갱신 (기존 Task 정보 새로고침)

이미 Gantt에 등록된 Task의 Dooray 본문 정보가 변경되었을 때, 최신 정보를 가져와 업데이트하는 기능

### 진입점
| 위치 | 동작 |
|------|------|
| Task 편집 모달 Footer | Dooray 버튼 그룹의 **갱신** 버튼 (`#refreshFromDoorayBtn`) → 개별 Task 갱신 |
| Summary Bar (Alt+Click 선택) | `Dooray` 버튼 → 선택 Task 일괄 갱신 |

### 동작 흐름
```
갱신 클릭 → Dooray API 조회 → 본문 파싱 → 변경 사항 비교 → 미리보기 모달 → 적용/취소
```

### 갱신 대상 필드
| 필드 | 갱신 | 이유 |
|------|------|------|
| releaseMonth, startDate, endDate, md | O | Dooray 본문이 원본 |
| planning, assignee, wikiUrl, planningTitle | O | Dooray 본문이 원본 |
| **status, progress** | **X** | 로컬 수동 관리 |
| **workLogs, dailyNotes** | **X** | 절대 보호 데이터 |
| **id, createdAt** | **X** | 불변 필드 |

### 변경이력 (changeHistory)
Task 객체에 변경이력을 내장하여 백업/Export 시 함께 이동

```javascript
task.changeHistory = [
    {
        date: "2026-03-12T10:30:00Z",
        source: "dooray-refresh",  // dooray-refresh | sync | manual | plan-import
        changes: [
            { field: "startDate", from: "2026-02-23", to: "2026-03-01" },
            { field: "endDate",   from: "2026-02-25", to: "2026-03-05" }
        ]
    }
]
```

- **최대 20건** 유지 (오래된 것 자동 삭제)
- **Edit Task 이력 로그** (왼쪽 패널, Dooray URL 하단 `#taskHistoryLog`)에 최근 5건 표시, 클릭으로 from→to 상세 펼치기
- **source 종류**: `dooray-refresh` (Dooray 갱신), `sync` (댓글 Sync), `manual` (수동 편집), `plan-import` (Plan Import)
- **Undo 지원**: 적용 전 `HistoryManager.saveState()` 호출 → `Ctrl+Z`로 되돌리기 가능

### 미리보기 모달
- 변경된 필드만 하이라이트 (현재값 → Dooray값)
- 변경 없는 Task: "변경 없음" 회색 표시
- 오류 Task: 빨간 오류 메시지 표시
- `적용` 버튼: 변경 있을 때만 활성화

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/dooray/syncManager.js` | `compareTaskWithDooray()`, `applyRefreshChanges()`, `compareManyTasksWithDooray()` |
| `js/main.js` | `refreshTaskFromDooray()`, `refreshSelectedTasksFromDooray()`, `_openDoorayRefreshModal()`, `applyDoorayRefresh()`, `_renderChangeHistory()` |
| `js/views/gantt.js` | Summary Bar에 `Dooray` 버튼 |
| `index.html` | `#refreshFromDoorayBtn`, `#doorayRefreshModal`, `#taskHistoryLog` (왼쪽 패널 이력 로그), `#changeHistoryRow` (숨김 stub 유지) |
| `styles.css` | `.btn-dooray-refresh`, `.dr-*`, `.ch-*`, `.modal-dooray-refresh` |

## Dooray 업로드 (Gantt → Dooray 역방향 Sync)

Gantt 차트에서 변경한 Task 필드를 Dooray 업무 본문에 반영하는 기능

### 진입점
- Task 편집 모달 Footer → Dooray 버튼 그룹 내 "업로드" 버튼 (`#uploadToDoorayBtn`)
- URL이 있고 `isLocal`이 아닌 Task에서만 표시

### Save 미저장 감지
- 업로드 클릭 시 폼의 `name`, `project`, `planning`, `releaseMonth`, `startDate`, `endDate`를 저장된 Task 값과 비교
- 불일치하면 "변경된 내용이 저장되지 않았습니다. Save 버튼을 먼저 클릭한 후 업로드해 주세요." 안내
- **보수적 접근**: 항상 Save → 업로드 순서 (로컬/Dooray 데이터 일관성 보장)

### 동작 흐름
```
업로드 클릭 → 폼 변경 감지 (미저장 시 차단) → Dooray API GET (기존 본문) → buildUpdatedBody() → 변경 비교 → confirm → PUT 업데이트
```

### 업로드 대상 필드

**본문 치환** (`buildUpdatedBody`):
| 필드 | Dooray 본문 행 | 형식 변환 |
|------|--------------|----------|
| 조직 (planning) | `* 조직: 값` | 그대로 |
| 일정 (startDate~endDate) | `* 일정: YY.MM.DD~YY.MM.DD` | YYYY-MM-DD → YY.MM.DD (MD 미포함) |
| 점검월 (releaseMonth) | `* 점검월: YY.MM` | YYYY-MM → YY.MM |

**제목 치환** (`pushTaskToDooray`):
| 필드 | Dooray 제목 위치 | 설명 |
|------|----------------|------|
| 프로젝트명 (project) | `[플랫폼]`과 `[상태태그]` 사이 | 예: `𝗙𝗫 [PC포커] **4월 업데이트** [작업] Task명` |
| Task명 (name) | 마지막 `[상태태그]` 뒤 | 예: `𝗙𝗫 [PC포커] 프로젝트 [작업] **바로입장 연출**` |

**제목 변경 감지 방식**: 모든 `[태그]` 위치를 regex로 찾아 첫 번째(플랫폼)~마지막(상태태그) 사이를 프로젝트명, 마지막 뒤를 Task명으로 분리 비교

### 보호 필드 (절대 수정 안 함)
- `* 위키:` 행 — 링크 포함, 변경 시 깨짐
- `***` 구분선 아래 자유 텍스트 — 사용자 메모

### 기획 URL 업데이트 (buildUpdatedBody)
`task.planningUrl`이 있고 본문의 `dooray://` URL과 다를 때만 `* 기획:` 행을 치환합니다.
- `_toDoorayUrl(url)`: `https://` → `dooray://1387695619080878080/tasks/{postId}` 변환 (`?to=` 파라미터 제거)
- 링크 텍스트: `task.planningTitle` 우선, 없으면 `기획 링크`
- 대괄호 이스케이프 처리: `[` → `&#91;`, `]` → `&#93;`
- 비교 기준: 본문의 `(dooray://...)` 부분만 추출하여 비교 (plain text 형식이면 URL 없음으로 처리 → 항상 업데이트)

### 본문 치환 로직
- `buildUpdatedBody(originalBody, task)`: regex로 해당 행만 치환
- 일정: `/(\*[^\S\r\n]*일정[^\S\r\n]*[:：][^\S\r\n]*)([^\n]*)/` → `YY.MM.DD~YY.MM.DD`
- 점검월: `/(\*[^\S\r\n]*점검월[^\S\r\n]*[:：][^\S\r\n]*)([^\n]*)/` → `YY.MM`
- 조직: `/(\*[^\S\r\n]*조직[^\S\r\n]*[:：][^\S\r\n]*)([^\n]*)/` → planning 값

> **⚠️ 정규식 `\s*` 금지 → `[^\S\r\n]*` (가로 공백만) 사용 필수**
> 콜론 뒤 `\s*`는 **줄바꿈까지 매칭**하므로, 값이 빈 행(예: `* 점검월:`)에서 `([^\n]*)`가 **다음 줄(`* 위키:` 등 보호 필드)을 캡처**한다.
> → 미리보기에 엉뚱한 라인이 표시되고, 적용 시 **보호 필드(위키/기획) 라인이 덮어써지는 데이터 손상** 발생.
> → 가로 공백만 매칭하는 `[^\S\r\n]*`로 같은 줄 안에서만 동작하도록 고정. (사고 이력 2026-06-02, Task #179)

### 미리보기 값 정리 (`_cleanFieldValue`)
변경 비교/confirm 팝업 표시 전에 `from` 값을 정리:
- **마크다운 이스케이프 제거**: `\~` → `~`, `\.` → `.` 등 (한글 Windows에서 `\`가 `₩`로 표시되는 문제)
- **HTML 엔티티 디코드**: `&#91;` → `[`, `&#93;` → `]`, `&lt;`/`&gt;`/`&amp;` 등
- **부수 효과**: 이스케이프만 다른 값(예: `26.05.15\~26.06.18` vs `26.05.15~26.06.18`)은 정리 후 동일해져 **거짓 변경(no-op diff)이 사라짐**

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/dooray/syncManager.js` | `buildUpdatedBody()`, `_cleanFieldValue()`, `pushTaskToDooray()`, `executePushToDooray()`, `_formatDateShort()` |
| `js/main.js` | `uploadTaskToDooray()` (Save 감지 + confirm + 실행), 편집 모달 버튼 표시/숨김 |
| `index.html` | `#uploadToDoorayBtn` (Dooray 버튼 그룹 내) |
| `styles.css` | `.btn-dooray-action` |

## 간트 Done → Dooray 업무 완료 전파

간트 차트에서 Task Status를 **Done**으로 바꾸면, 연결된 Dooray 업무의 **워크플로우 상태도 '완료'로 변경**할지 제안합니다.

### 배경 (해결한 문제)
타인(예: 김보람) 담당 업무는 주간보고 댓글의 "팀 공유사항" 칸을 내가 편집할 수 없어 완료 표시를 못 했고, 그래서 간트에서만 Done 처리해 Dooray와 상태가 어긋났습니다.
- **핵심 구분**: "팀 공유사항 칸 = 댓글 본문 편집(타인 것 불가)" vs **"업무 워크플로우 상태 = 프로젝트 멤버 권한으로 변경 가능할 수 있음(정식 완료 신호)"**.
- 따라서 댓글이 아니라 **업무 워크플로우를 완료로** 바꾸는 방식을 채택.

### 동작 흐름
```
간트 인라인 Status → Done (oldStatus !== 'Done')
→ confirm("Dooray 업무도 '완료'로 변경할까요?")
→ DooraySyncManager.setPostDone(task)  // PUT workflowId
   성공 → 토스트
   실패(403 등) → "완료 댓글 남길까요?" confirm → postCompleteComment() 폴백
```
- **트리거 지점**: `App.updateTaskStatus()` (인라인 간트 Status 드롭다운의 단일 funnel). Sync의 일괄 Done(`matchingTask.status='Done'` 직접 대입)은 이 경로를 안 타므로 **확인창이 뜨지 않음** (안전).
- **완료 워크플로우 ID**: FX 기본 프로젝트(`defaultProjectId` = 클래식FX팀-업무관리)는 알려진 ID `4028352443658351504` 즉시 사용. 그 외 프로젝트는 `/workflows` 조회로 `class === 'closed'` 탐색 (캐시).
- **projectId 결정**: https 링크(`/task/{projectId}/{postId}`)만 실제 projectId를 담음. `dooray://`는 orgId만 있으므로 `defaultProjectId`로 처리.
- `set_post_workflow`는 **모든 담당자 상태를 함께 완료로** 변경 → confirm에 명시. (QA 업무의 경우 CC의 QA팀에게 "FX 수정 완료, 재검증" 신호가 되는 정상 흐름)

### 권한 (검증 필요)
타인 담당 업무에 대해 정재화(CC/팀리더)가 워크플로우를 바꿀 수 있는지는 Dooray 프로젝트 권한 설정에 달림.
- **되면**: 그대로 완료 처리.
- **안 되면(403)**: 완료 알림 댓글(`✅ FX 작업 완료 ({리더명} 확인)`)로 폴백 — 리더명은 `TeamManager.getLeaderName()` 동적 사용(하드코딩 금지).

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/dooray/syncManager.js` | `setPostDone(task)`, `getDoneWorkflowId(projectId)`(closed 워크플로우 캐시), `postCompleteComment(task, content)` |
| `js/main.js` | `App.updateTaskStatus()` hook, `_offerDoorayComplete(taskId)` (confirm + 폴백) |

## Dooray 버튼 그룹 (Edit Task Footer)

Task 편집 모달 Footer에 Dooray 관련 버튼을 그룹으로 묶어 **Footer 좌측**에 배치합니다.

### 구성
```
Footer-Left:  [Delete] [Dooray ?| 가져오기 | 갱신 | 업로드]
Footer-Right: [Generate] [Group] [Save]
```
- **`Dooray ?` 라벨**: 회색 배경 (`var(--hover-color)`) + `?` 도움말 아이콘 내장
- 3개 버튼 `btn-secondary`와 동일한 디자인 (13px, font-weight 500, `var(--text-primary)`)
- 테두리 공유 (`dooray-btn-group`)
- Footer timestamp(Created/Updated)는 제거됨 → 이력은 왼쪽 패널 `#taskHistoryLog`에 표시

### `?` 도움말 아이콘
- **마우스 호버**: 플로팅 툴팁 (`position: fixed` — overflow 클리핑 우회)
- **클릭**: 고정(pinned) 팝업으로 전환 (`dht-pinned` 클래스) → 읽으면서 작업 가능
  - 고정 팝업에 `×` 닫기 버튼 표시
  - 팝업 외부 클릭 시 자동 해제
- **내용**: 데이터 흐름 3가지 시나리오 (가져오기 📥 / 업로드 📤 / 새 업무 등록 🆕)
- **CSS**: `.dooray-help-icon`, `.dooray-help-tooltip`, `.dht-*`, `.dht-pinned`

### 버튼 표시/숨김
| 모드 | 가져오기 | 갱신 | 업로드 |
|------|---------|------|--------|
| 새 Task | O | X | X |
| Edit (URL+!isLocal) | O | O | O |
| Edit (URL 없음/isLocal) | O | X | X |

### 구현 위치
| 파일 | 역할 |
|------|------|
| `index.html` | `footer-left` > `.dooray-btn-group` > `.dooray-btn-label` + `.dooray-help-icon` + `#fetchDoorayBtn` + `#refreshFromDoorayBtn` + `#uploadToDoorayBtn` |
| `styles.css` | `.dooray-btn-group`, `.dooray-btn-label`, `.btn-dooray-action`, `.dooray-help-icon`, `.dooray-help-tooltip`, `.dht-*`, `.dht-pinned`, `.dht-close-btn` |
| `js/main.js` | 새 Task/Edit Task 모드별 display 제어, `positionTooltip()` 뷰포트 경계 체크, `pinned` 상태 관리 |

### Report 패널 자동 갱신
`App.render()` 호출 시 Report 패널이 열려있으면 `ReportView.render()` 자동 호출하여 최신 데이터 반영

## Gantt 차트 주요 기능

### 필터 시스템
- **프로젝트 필터**: `platform|project` 형식으로 정확한 매칭
- **서비스 필터**: `releaseMonth` 기준
- **플래닝 필터**: `planning` (조직) 기준
- **상태 필터**: Ready/Doing/Hold/Done/Bypass
- **Hide Bypass**: Bypass 상태 Task 숨김 (`AppState.hideBypass`, X키 토글)
- **Hide Task Category**: Task 컬럼에서 카테고리(`{cat} | {name}` 중 `{cat} |`) 숨김 (`AppState.hideTaskCategory`)
  - 토글: Task 컬럼 헤더 우측 아이콘 버튼 (`fa-tag` ↔ `fa-eye-slash`)
  - 활성 시 파란색 강조 (`.gantt-task-category-toggle.active`)
  - localStorage `teamScheduler_hideTaskCategory` 영속화
- **Hide Planned**: Planned(placeholder) 그룹 숨김 (`AppState.hidePlanned`)
- **Planned 월 필터**: Hide Planned 옆 📅 버튼 → 월별 체크박스로 보고 싶은 월만 선택 (`AppState.plannedVisibleMonths`)
- **Placeholder(Planned) 프로젝트**도 필터 적용됨 (`gantt.js:groupTasksByPlatformProject`)

### Project Filter 모달

`F` 키 또는 사이드 패널 → Project Filter (`#projectFilterModal`). 왼쪽 프로젝트/플랫폼 리스트 + 오른쪽 연·월 필터.

- **모달 너비**: `.modal-content.modal-project-filter` `max-width: 870px` (기존 580px의 1.5배 — 긴 Task명 표시 여유)
- **연·월 필터**: `renderYearMonthFilter()` — 연도별 그룹 + 1~12월 버튼 (월별 `프로젝트수 (Task수)`)
  - `projectFilterYear`/`projectFilterMonth` (단일 선택, `null`=전체) → 모달의 프로젝트 리스트를 해당 연·월로 좁힘
  - **이번 달 강조**: 현재 월(`YYYY-MM`) 버튼에 `current-month` 클래스 → 파란 1px 아웃라인(`box-shadow: 0 0 0 1px`) + 파란 텍스트(선택 시엔 흰색 유지: `:not(.active)`)
- **All 버튼 (`#allProjectsBtn`)**: 전체 보기 ↔ 이번 달 **토글**
  - 전체 보기 상태에서 클릭 → 이번 달만 보기 (연·월 = 현재 연/월)
  - 이번 달 보기/다른 필터 상태에서 클릭 → 전체 보기 (프로젝트/플랫폼/연·월/검색 모두 해제)
  - **모달을 닫지 않고** 리스트·달력·Gantt 갱신
  - 라벨/상태: `_updateAllProjectsBtnState()` — 전체 보기면 `All`(active), 이번 달 보기면 `이번달`(active), 그 외 필터 중이면 `All`(비활성)
  - 단일 선택 모델이므로 "모든 월 동시 active"는 채택 안 함 (전체=선택 월 없음)
- **Task 목록 표시/숨김 토글 (`#toggleProjectTasksBtn`, "Task")**: 프로젝트 하위 `• Task명` 목록(`.project-filter-tasks`)을 표시/숨김
  - `projectFilterShowTasks` + localStorage `teamScheduler_projectFilterShowTasks` 영속
  - `_applyProjectTasksVisibility()` — `#projectFilterList`에 `hide-tasks` 클래스만 토글 (재렌더 불필요, 컨테이너 클래스라 `innerHTML` 갱신에도 유지)
  - 버튼 텍스트형(아이콘 X — `.project-filter-search i` 회색 강제 회피), active 시 파란 배경 + 흰 글씨

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/main.js` | `renderYearMonthFilter()`, `renderProjectFilterList()`, `selectAllProjects()`(토글), `_updateAllProjectsBtnState()`, `toggleProjectFilterTasks()`, `_applyProjectTasksVisibility()` |
| `index.html` | `#allProjectsBtn`, `#toggleProjectTasksBtn`, `#yearMonthFilter`, `#projectFilterList` |
| `styles.css` | `.modal-project-filter`, `.month-filter-btn.current-month`, `.btn-all-projects.active`, `.btn-toggle-tasks`, `.project-filter-list.hide-tasks` |

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

### 날짜 범위 빠른 버튼 (1M/3M/6M/1Y) + 휠 이동

헤더 오른쪽 `.range-quick-btns` 영역의 `data-months` 버튼(1/3/6/12)으로 표시 기간을 빠르게 설정합니다.

- **클릭**: `setQuickRange(months)` — `AppState.dateRange.start/end` 설정 + `active` 클래스 토글
  - 3M = 전월~익월, 6M = 1~6월, 1Y = 1~12월, 그 외 = 당월~N개월 후
- **버튼 영역 위 휠 스크롤**: `shiftDateRangeByMonth(delta)` — **현재 범위의 월 span을 유지**한 채 달력을 ±1개월 평행 이동
  - 월 span 계산: `(endYear-startYear)*12 + (endMonth-startMonth) + 1`
  - start를 ±1개월 이동 → end = `new Date(startYear, newStartMonth + span, 0)` (span번째 달의 말일)
  - **휠 방향**: 위로 = 미래(+1), 아래로 = 과거(-1) (`deltaY > 0 ? -1 : 1`)
  - `{ passive: false }` + `preventDefault()`로 페이지 스크롤 차단
  - `requestAnimationFrame`으로 빠른 연속 휠을 1프레임당 1회 렌더로 코얼레싱
  - 활성 버튼(1M/3M/6M/1Y) 하이라이트는 유지 (이동 후엔 today 기준 프리셋과 어긋나도 시각적 일관성 우선)
  - start는 항상 1일, end는 항상 말일로 정규화됨

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/main.js` | `setQuickRange()`, `shiftDateRangeByMonth()`, `.range-quick-btns` click + wheel 리스너 |
| `index.html` | `.range-quick-btns` > `.range-btn[data-months]` |

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

### 일별 셀 hover 헤더 강조

Gantt 및 Team Gantt에서 일별 셀(`td.col-day[data-date]`)에 마우스를 올리면 같은 날짜의 헤더 `th`가 subtle 강조됩니다. 행 hover의 가로 강조와 조합하여 십자 좌표 효과로 날짜 식별이 쉬워집니다.

**시각 효과**: 헤더 셀 배경 `#e8eaed` + `font-weight: 600` (본문 셀은 건드리지 않아 작업 바/점 시인성 유지)

**바인딩 방식**: `_hoverBound` 플래그로 1회만 부착되는 delegated mouseover listener
- `GanttView._bindDayHoverHighlight()` — 래퍼 `#ganttView .gantt-wrapper`
- `TeamGanttView._bindDayHoverHighlight()` — 래퍼 `#teamGanttWrapper`
- 각 `render()` 진입 시 호출 (재실행되어도 `_hoverBound` 플래그로 중복 부착 방지)

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/views/gantt.js` | `_bindDayHoverHighlight()`, `render()` 호출 |
| `js/views/teamGantt.js` | `_bindDayHoverHighlight()`, `render()` 호출 |
| `styles.css` | `.gantt-table th.col-day.col-hover-header` (Team Gantt도 `gantt-table` 클래스 공유로 자동 적용) |

### Gantt 컬럼 레이아웃

| 컬럼 | left | width |
|------|------|-------|
| No | 0 | 35px |
| Service | 35px | 70px |
| Platform | 105px | 90px |
| Project | 195px | 200px |
| Task | 395px | 380px |
| Status | 775px | 80px |
| Progress | 855px | 80px |
| Assignee | 935px | 120px |
| Date | 1055px | 90px |
| DateEnd | 1145px | 90px |
| MD | 1235px | 60px |

**주의**: 컬럼 너비 변경 시 `styles.css`에서 2곳 수정 필요 (메인 컬럼 정의 + 그룹 헤더 sticky positions)
**No 컬럼**: 순서 번호가 아닌 Task 고유 seq 번호 표시 (삭제해도 번호 유지, 재사용 안 함)

### Task 컬럼 긴 제목 한 줄 ... 처리 (ellipsis)

긴 Task명이 2줄로 줄바꿈되어 행 높이가 늘어나는 것을 방지하기 위해, 컬럼 너비를 넘는 제목은 한 줄에서 `…`로 잘라 표시합니다.

**구조**: `td.col-task` 안에 `.col-task-inner` flex 래퍼 → `[선택 dot][.gantt-task-name][배지들]`
- **td**: `table-cell` 유지(컬럼 정렬·sticky 보존) + `white-space: nowrap; overflow: hidden`
- **`.col-task-inner`**: `display: flex; width: 100%; min-width: 0`
- **`.gantt-task-name`** (Task명): `flex: 0 1 auto; min-width: 0` + `text-overflow: ellipsis` → 공간 부족 시 줄어들며 `…`
- **배지/선택 dot**: `flex: 0 0 auto` → 줄어들지 않고 **항상 끝에 온전히 표시** (신규/작업/완료/변경/수정/미등록 등이 잘리지 않음)

**전체 제목 확인**: `.gantt-task-name`에 `title="Task명"` 속성 → 잘린 제목은 마우스 호버 툴팁으로 전체 표시

> **주의 — td에 직접 `display: flex` 금지**: `td`를 flex로 바꾸면 table-cell 레이아웃에서 빠져 sticky 컬럼 너비/정렬이 깨짐. 반드시 내부 `.col-task-inner` 래퍼에만 flex 적용.

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/views/gantt.js` | `renderRowCells()` — `.col-task-inner` 래퍼 + `.gantt-task-name`(title 속성) |
| `styles.css` | `td.col-task` nowrap/overflow, `.col-task-inner`(flex), `.gantt-task-name`(ellipsis), 배지 `flex: 0 0 auto` |

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

### 그룹 헤더 바 (H자 형태)
일반 Task 바와 시각적으로 구분하기 위해 그룹 헤더 바는 표준 간트 차트의 **H자 형태**(양 끝 수직 캡 + 얇은 가로선)로 표현합니다.

**구조**:
```
█━━━━━━━━━━━━━━━━█
↑                  ↑
양 끝 수직 캡        가운데 가로선
(width:3px,         (height:4px,
 height:14px)        opacity:0.9)
```

**구현**:
- `.group-bar`: 가운데 가로선 (height 4px, opacity 0.9, border-radius 없음)
- `.group-bar.bar-s::before` + `.bar-se::before`: 시작 셀 또는 단일 셀의 왼쪽 수직 캡
- `.group-bar.bar-e::after` + `.bar-se::after`: 종료 셀 또는 단일 셀의 오른쪽 수직 캡
- 캡 색상: `background: inherit` — 부모 `.group-bar`의 inline `background` 색상 상속
- 중간 셀(클래스 없음): 가로선만 표시 (캡 없음)

**노트 삼각형(▼)과 형태 차이**: 직선 형태 → 삼각형과 혼동 없음 (노트 마커는 우상단 검정 삼각형, z-index 10)

### 보고서 하이라이트
- 보고서 패널에서 Task 항목 hover/클릭 시 Gantt 차트의 해당 행 하이라이트
- **Hide Done/Bypass 자동 해제**: 하이라이트 대상 Task가 Hide Done/Bypass로 숨겨져 있으면 자동으로 해제 후 재렌더하여 하이라이트 표시
- 보고서 패널 닫힐 때 잔존 하이라이트 자동 제거 (`report.js:closePanel()`)
- Gantt → 보고서 역방향 하이라이트도 지원
- 패널 너비: 621px (`styles.css` `.report-panel`)
- **Platform 셀 하이라이트**: 완료 Task의 Platform 셀은 트리 커넥터 배경 + completed 스타일이 높은 specificity를 가짐 → `.group-task.task-completed.task-highlight td.col-platform` 등 고specificity 셀렉터로 오버라이드
- **Flash 효과**: `report.js:_flashRow()` — inline `style.setProperty('background', color, 'important')`로 CSS specificity 무관하게 적용
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

### 보고서 workLogs 기반 Task 포함
완료된 Task라도 해당 기간에 workLogs가 있으면 보고서에 포함합니다.

**배경**: 완료(100%) + 날짜 범위 외 Task가 추가 개선으로 작업했을 때 보고서에 누락되는 문제
**규칙**: 기존 날짜 범위 겹침 / 미완료 조건에 더해, `AppState.workLogs[taskId]`에 해당 기간 작업 기록이 있으면 포함

**적용 위치**:
| 함수 | 용도 |
|------|------|
| `report.js:getTasksInRange()` | 보고서 이번 주/이번 달 Task 목록 |
| `report.js:getTasksForWeeklyReport()` | 주간보고서 금주 작업 내용 |

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

**planningUrl / planningTitle UI 표시**:
- Task 편집 모달의 Project URL 아래에 "기획 URL" 입력 필드 (편집 가능, Project URL과 동일 패턴)
- URL 아래에 `planningTitle` 작은 텍스트로 표시 (있을 때만)
- 열기 버튼: 입력된 URL로 외부 브라우저 열기 (`dooray://` → `https://` 변환)
- Notes는 기획 URL 아래로 이동 (rows="3")
- HTML: `#planningUrlRow`, `#planningUrl`, `#openPlanningUrlBtn`, `#planningTitleDisplay`
- CSS: `.planning-title-display` (11px 서브텍스트)

**Edit Task 기획 URL 자동 조회**:
- Edit Task 열 때 `planningUrl`이 비어있으면 `_fetchPlanningUrlFromDooray(task)` 자동 호출
- Task의 Dooray URL로 API 조회 → 본문에서 `기획:` 파싱 → planningUrl/planningTitle 자동 채움 + 저장
- UI: 배경에서 비동기 실행, 성공 시 input 필드 + title 서브텍스트 자동 갱신

**Edit Task 기획 URL input 변경 시 제목 즉시 갱신**:
- `#planningUrl` input 이벤트 리스너 (debounce 600ms) → `_fetchPlanningTitleByUrl(url)` 호출
- Dooray API로 업무 제목 조회 후 `#planningTitleDisplay` 즉시 갱신
- 캐시: `App._planningTitleInputCache[url]` — 같은 URL 재조회 방지
- 비어있으면 서브텍스트 즉시 숨김
- **구현**: `main.js:init()` 리스너 + `_planningTitleInputCache` + `_fetchPlanningTitleByUrl()`

**구현 위치**:
- 파싱: `syncManager.js:parseProjectInfoFromBody()` — regex + `N월 업데이트 > ` 제거
- 매핑: `syncManager.js:convertToTask()` — `planningTitle`, `planningUrl` 필드
- Sync 갱신: `syncManager.js:addNewTasksWithRemoteInfo()` — `planningTitle`/`planningUrl`은 항상 최신값으로 덮어쓰기
- 보고서 프리페치: `report.js:fetchMissingPlanningTitles()` — 누락 Task를 Dooray API로 개별 조회
- 출력: `report.js:generateTableHtml()` — grouped/individual 모두 지원 + `N월 업데이트 > ` 출력 시 재정리
- UI: `index.html` `#planningUrlRow` + `main.js` `_updatePlanningTitleDisplay()`, `_bindPlanningUrlBtn()`, `_fetchPlanningTitleByUrl()`
- 자동 조회: `main.js:_fetchPlanningUrlFromDooray()` — Edit Task open 시 planningUrl 비어있으면 트리거
- Save: `handleTaskSubmit()` formData에 `planningUrl` 포함

### Planned (Placeholder) 그룹
Task가 없는 예상 프로젝트를 Gantt에 미리 표시하는 기능

**데이터**: `AppState.projectPlaceholders` 배열
```javascript
{
    id: 'ph_xxx',
    platform: 'PC포커',           // 매핑된 플랫폼 (연결 시 Gantt 이름으로 덮어쓰기)
    project: '브로드캐스팅 고도화',  // 프로젝트명 (연결 시 Gantt 이름으로 덮어쓰기)
    releaseMonth: '2026-04',      // YYYY-MM
    planning: '포커게임기획팀',     // 담당 조직
    planner: '홍길동',            // 기획 담당자명
    category: '',
    createdAt: '...',
    linkedProject: 'PC포커|브로드캐스팅',  // 연결된 Gantt 프로젝트 키 (선택)
    importKey: 'PC포커|브로드캐스팅 고도화|포커게임기획팀'  // 연결 전 원본 키 (선택)
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

## Settings 모달 크기

| 모달 | CSS 클래스 | 크기 |
|------|-----------|------|
| Settings (Appearance) | `.modal-content.modal-appearance` | 500px × 750px 고정 |
| 플랫폼/조직 관리 | `.modal-content.modal-org-settings` | 850px × 850px 고정 |

**고정 크기**: `height: 750px !important; max-height: 750px !important;` — 앱 전체 크기(Zoom) 변경 시에도 모달 크기 유지
**외부 스크롤 제거**: `.modal-appearance { overflow-y: hidden }` — 내부 `.settings-tab-content`만 스크롤

### 단일 스크롤 컨텍스트 원칙 (org 모달)
플랫폼/조직 관리 모달은 `.org-settings-body`가 `overflow-y: auto`로 **단일** 스크롤 컨텍스트를 담당합니다. 내부 리스트(`.org-map-list`, `.team-list` 등)에 `max-height` + `overflow-y` 를 추가하면 이중 스크롤이 발생하여 빈 공간에도 스크롤바가 노출되는 버그가 생깁니다.
- `.org-map-list`: 내부 스크롤 제거됨 (max-height/overflow 없음)
- `.modal-org-settings .team-list`: org 모달 한정 오버라이드 (`max-height: none; overflow-y: visible`) — Appearance 모달의 `.team-list`(`#teamGroupColorList`)는 보존
- **새 탭 추가 시 주의**: 리스트에 max-height/overflow 두지 말 것

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

## 조직명 정규화 (효력일 기반 이력 관리)

Dooray 본문에서 파싱된 옛 조직명을 신 조직명으로 자동 변환합니다. 같은 이름이 시점별로 다른 의미를 가질 수 있는 케이스를 지원하기 위해 **효력일(effectiveDate)** 기반 정규화를 사용합니다.

### 데이터 구조

`AppState.organizationRenames`: 사용자 관리 가능한 매핑 배열
```js
[
    { id: 'rn_xxx', from: '포커기획팀', to: '포커게임기획팀', effectiveDate: '', note: '1차 개편' },
    { id: 'rn_yyy', from: '포커운영팀', to: '포커사업팀', effectiveDate: '', note: '2차 개편 (이름 재사용)' }
]
```

- `null`이면 `APP_CONSTANTS.DEFAULT_ORGANIZATION_RENAMES` 사용
- `effectiveDate`가 비어있으면 시점 무관 매핑 (항상 적용)
- `effectiveDate`가 있으면 시점 기반 매핑 (해당 날짜 **이후** 발생한 rename만 적용)

### 정규화 알고리즘 (`normalizeOrganizationName(org, contextDate)`)

```
for each rename (effectiveDate 오름차순):
    if effectiveDate 없음:
        → 항상 적용 (시점 무관)
    else if contextDate 없음:
        → skip (안전 우선 - 잘못된 변환 방지)
    else if rename.effectiveDate <= contextDate:
        → skip (contextDate 시점에 이미 신 이름이었음)
    else:
        → 적용 (forward-roll로 현재 이름까지 변환)
```

### contextDate 전달

`parseProjectInfoFromBody(body, contextDate)` — Dooray API 응답의 `taskDetails.createdAt`/`updatedAt`을 전달
- `syncManager.fetchRemoteTaskInfo()`: 전달함
- `syncManager.compareTaskWithDooray()`: 전달함
- `main.js:_fetchPlanningUrlFromDooray()`: 전달함
- `report.js`: 전달함
- `weeklyReportGenerator.js`: 전달함

### 같은 이름 재사용 케이스 (1차/2차 개편)

조직 이름이 다른 조직에 재사용되는 경우, 효력일을 반드시 명시해야 합니다:

| effectiveDate | from | to | 의미 |
|---|---|---|---|
| 2024-01-15 | 포커사업팀 | 포커서비스기획팀 | 1차 개편 (옛 사업팀 → 서비스기획팀) |
| 2024-06-10 | 포커운영팀 | 포커사업팀 | 2차 개편 (옛 운영팀 → 새 사업팀) |

같은 "포커사업팀" 이름이 두 시점에 다른 조직을 가리키지만, 효력일로 분리되어 안전하게 해석됨.

**예시 트레이스**:
- Dooray 글 2024-01-01 작성, 조직: "포커사업팀" → contextDate=2024-01-01
  - rename 1: 2024-01-15 > contextDate → 적용 → "포커서비스기획팀"
- Dooray 글 2024-12-01 작성, 조직: "포커사업팀" → contextDate=2024-12-01
  - rename 1: 2024-01-15 < contextDate → skip
  - rename 2: 2024-06-10 < contextDate → skip
  - 결과: "포커사업팀" (신 이름 그대로)

### Settings UI (Tab 6: 조직 변경 이력)

`Settings > 플랫폼/조직 관리 > 조직 변경 이력` 탭에서 사용자 관리:

- **추가**: from / to / effectiveDate (선택) / note (선택) 입력
- **삭제**: 항목 우측 × 버튼
- **재사용 감지**: 같은 이름이 from/to에 중복 등장하면 ⚠️ 아이콘 + 경고 배너
- **기본값 복원**: ↩ 버튼 → `DEFAULT_ORGANIZATION_RENAMES`로 초기화
- **기존 Task 일괄 검사**: 🔍 버튼 → `App.checkOrganizationMigration()` 호출 (포커서비스기획팀 Task 일괄 검증)

### 괄호 중복 표기

`(포커게임기획팀)(포커기획팀)` 같은 중복 표기는 신 이름 우선 선택 (rename `from`에 없는 이름을 우선 사용)

### 사고 이력 (2026-05-29) → 효력일 기반으로 전환

이전 `ORGANIZATION_NAME_MAP` (flat Object)이 `'포커사업팀': '포커서비스기획팀'` + `'포커운영팀': '포커사업팀'` 매핑을 가져 모순 발생. Edit Task #200 갱신 시 Dooray의 `조직: 포커사업팀`이 `포커서비스기획팀`으로 잘못 변환됨.

**해결**: 효력일 기반 배열로 전환 + Settings UI에서 사용자 관리. 기본값은 안전한 매핑(`'포커기획팀' → '포커게임기획팀'`, `'포커운영팀' → '포커사업팀'`)만 포함. 옛 `'포커사업팀' → '포커서비스기획팀'` 매핑이 필요한 사용자는 Settings에서 effectiveDate와 함께 직접 추가.

### 구현 위치

| 파일 | 역할 |
|------|------|
| `js/state.js` | `AppState.organizationRenames`, `APP_CONSTANTS.DEFAULT_ORGANIZATION_RENAMES` |
| `js/storage.js` | save/load 5곳 + applyEnvironmentData |
| `js/dooray/syncManager.js` | `_getOrganizationRenames()`, `normalizeOrganizationName(org, contextDate)`, `_applyRenames()`, `parseProjectInfoFromBody(body, contextDate)` |
| `js/main.js` | `renderOrgRenames()`, `addOrgRename()`, `deleteOrgRename()`, `resetOrgRenames()`, `_bindOrgRenamesEvents()`, `checkOrganizationMigration()` |
| `index.html` | `#orgTabRenames` (Tab 6), `.org-renames-*` 입력 폼/테이블 |
| `styles.css` | `.org-renames-*`, `.org-rename-*` |

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

### 미리보기만 (DryRun) 클립보드 복사
`dryRunWeeklyReport()` — 미리보기 갱신 후 클립보드에 복사

**주의**: `setTimeout` 안에서 `navigator.clipboard.writeText()` 호출 시 브라우저가 user gesture 만료로 권한 거부할 수 있음
**해결**: `navigator.clipboard` 실패 시 `textarea.select()` + `document.execCommand('copy')` fallback 적용

**구현 위치**: `main.js:dryRunWeeklyReport()`

### 조직별 프로젝트 순서 변경
미리보기에서 프로젝트 블록을 드래그하여 순서를 변경하고, 본문 업데이트에 반영합니다.

**미리보기 탭**:
| 탭 | 기본 | 설명 |
|---|---|---|
| 조직별 | O | 프로젝트 블록 드래그 순서 변경 + 접기/펼치기 |
| 댓글순 | | 기존 읽기 전용 텍스트 미리보기 |

**프로젝트 블록 드래그**:
- 같은 조직 내에서만 프로젝트 순서 변경 가능
- 프로젝트 블록 = 같은 프로젝트명의 Task 묶음 (1개 이상)
- 드래그 완료 시 `mergedProjects` 배열 즉시 재정렬
- `updateTable()` / `generateTableRows()`는 `mergedProjects` 순서를 그대로 사용

**접기/펼치기**:
- 조직 헤더 클릭 → 해당 조직의 프로젝트 전체 접기/펼치기 (▼/▶ 토글)
- 프로젝트 블록 ▼ 클릭 → 해당 프로젝트 내 Task 목록 접기 (2건 이상일 때만)
- 탭 행 오른쪽에 전체 접기/펼치기 버튼 (`#wrCollapseAllBtn`, `#wrExpandAllBtn`)
- 조직별 탭 활성 시만 표시, 댓글순 탭 전환 시 숨김

**미리보기만 버튼**: URL 행에서 미리보기 헤더 오른쪽으로 이동 (`#weeklyReportDryRunBtn`)

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/main.js` | `_renderOrgDraggablePreview()`, `_initOrgCollapseEvents()`, `_wrCollapseAll()`, `_wrExpandAll()`, `_initOrgProjectDragDrop()`, `_applyOrgProjectOrder()` |
| `index.html` | `#wrPreviewViewToggle` — 조직별(기본) + 댓글순 탭 + 접기/펼치기 버튼 |
| `styles.css` | `.wr-org-preview`, `.wr-org-project-block`, `.wr-org-toggle`, `.wr-org-block-toggle`, `.wr-fold-btn`, `.wr-org-group.collapsed`, `.wr-org-project-block.collapsed` |

### 표 초기화
Dooray 본문의 표 데이터 행을 빈 1행으로 교체하여 표를 비우는 기능입니다.

**동작**: 헤더 + 구분선은 유지, 데이터 행만 빈 행 1개로 교체
**진입**: "본문 업데이트" 옆 "표 초기화" 버튼 (`#weeklyReportResetTableBtn`)

**흐름**:
```
표 초기화 클릭 → confirm → Dooray API GET (기존 본문) → 표 찾기 → 헤더+구분선 유지, 데이터 행 제거 → 빈 1행 삽입 → PUT 업데이트
```

**구현 위치**: `main.js:resetWeeklyReportTable()`

### 보고서 유형 선택 (팀플레이 / 아트실)
URL 입력 행 아래에 라디오 스타일 버튼 2개로 보고서 유형을 선택합니다.

**구조**:
```
[URL 입력] [◀][팀플레이][▶] [본문 업데이트] [표 초기화] [열기]
                                    [✓ 팀플레이 (FX팀)] [✓ 아트실 주간보고]  ← 우측 정렬
```

- 팀플레이 (기본 선택): 본문 업데이트 → `updateWeeklyReportBody()`
- 아트실 선택: 본문 업데이트 → `generateArtTeamReport()`
- 선택 상태: 파란 배경 + 체크 아이콘 (`.wr-type-btn.active`)
- `_weeklyReportType`: `'teamplay'` | `'artteam'` (런타임)

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `index.html` | `.wr-report-type-row` > `#wrTypeTeamplay` + `#wrTypeArtteam` |
| `js/main.js` | 라디오 버튼 이벤트 바인딩, `_weeklyReportType` 상태, 본문 업데이트 분기 |
| `styles.css` | `.wr-report-type-row`, `.wr-type-btn`, `.wr-type-btn.active` |

### 아트실 주간보고 생성
Gantt + Weekly 데이터를 기반으로 아트실 주간보고 업무를 Dooray에 자동 생성합니다.

**전제 조건**: 팀플레이 버튼으로 댓글 조회가 먼저 완료되어야 함

**생성 내용**:
| 항목 | 데이터 소스 | 형식 |
|------|-----------|------|
| 제목 | 날짜 + 보고자명 | `[3월 19일] 정재화` (일자는 zero-padding 없이, `[4월 9일]` not `[4월 09일]`) |
| 주간 요약 | Report Group by Project | `* **[프로젝트] :** Task 완료, Task 진행중 (진척률 N%)` |
| 표 | Weekly generateTableRows | 기존 Weekly 마크다운 표 |
| 담당자 | organizationMemberId | 정재화 (설정 가능) |

**주간 요약 자동 생성**: `ReportView.groupTasksByProject()` + `buildGroupedTaskNamesString()` 재사용
- 이번 주 범위의 Gantt Task를 프로젝트별로 그룹핑
- 완료/진행중/준비 상태별 Task명 나열
- Report "Group by Project" Copy와 동일한 형식

**보고 날짜**: 다음 목요일 (오늘이 목요일이면 오늘)

**설정 (localStorage 자동 저장)**:
| 키 | 기본값 | 설명 |
|---|---|---|
| `teamScheduler_artTeamProjectId` | `2691816469955957947` | 아트실 프로젝트 ID |
| `teamScheduler_artTeamReporter` | `정재화` | 보고자명 (제목에 표시) |
| `teamScheduler_artTeamName` | `클래식FX팀` | 팀명 (본문 상단) |
| `teamScheduler_artTeamMemberId` | `2029850955956616509` | Dooray 담당자 ID |

**미리보기**: 제목, 팀명, 보고일자, 주간 요약, 표 미리보기 + 설정 편집 영역
**버튼**: `Dooray 업무 생성` (POST API) / `본문 복사` (클립보드)

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/main.js` | `generateArtTeamReport()`, `_generateWeeklySummary()`, `_getNextThursday()`, `_createArtTeamPost()` |
| `styles.css` | `.wr-artteam-preview`, `.wr-at-*` |

### 루틴 완료 Dooray 백그라운드 확인 (`_checkRoutineCompletedOnDooray()`)

Automation 패널을 열 때, localStorage에 기록이 없어도 Dooray API로 오늘 루틴 완료 여부를 확인합니다.

**호출 시점**: `openPanel()` → `render()` 완료 후 항상 호출
**확인 우선순위**:
1. `teamScheduler_lastRoutinePostInfo` (저장된 postId) → 직접 GET 조회 → `updatedAt/createdAt`이 오늘이면 완료
2. 아트실 타겟: `GET /project/v1/projects/{artProjectId}/posts?size=20&order=-createdAt` → 오늘 생성된 것 중 제목이 `N월\s*0?N일` 패턴 일치하는 것 탐색
3. 팀플레이 타겟: Weekly 보고 URL 업무의 `updatedAt`이 오늘이면 완료

**완료 감지 시**: `teamScheduler_lastRoutineTime` + `teamScheduler_lastRoutinePostInfo` 저장 → DOM 상태 즉시 업데이트

**중복 방지**: `_doorayRoutineChecking` boolean (failed 호출 후 retry 허용 — date string 비교 방식보다 안전)

**Dooray 날짜 regex**: `new RegExp(\`${month}월\\s*0?${day}일\`)` — `[4월 9일]`과 `[4월 09일]` 모두 매칭

### 아트실 주간보고 댓글 자동화 (Step 5)
아트실 주간보고 본문 생성 후, 개인 작업 내용 + `_Final` 이미지를 댓글로 자동 작성합니다.

**실행 조건**: 루틴 대상 = 아트실 + Step 4(업무 생성) 완료 후 자동 실행

**동작 흐름**:
```
Step 4 완료 (reportPostId 획득)
→ 목~목 기간 계산 (지난주 목요일 ~ 이번주 목요일)
→ workLogs에서 해당 기간 작업 Task 수집
→ 담당자 필터 (reporterName만)
→ 각 Task Dooray API GET → post.files[] → _Final 파일 필터
→ platform → project 2단 그룹핑
→ dailyNotes에서 이번 주 세부 내용 수집
→ 마크다운 생성 → 댓글 POST
```

**`_Final` 파일 규칙**:
- 파일명 패턴: `*_Final.(png|webp|jpg|jpeg)` (대소문자 무시)
- 예시: `260326_FX_Ani_Classic_LobbyIconOfferWall_Final.png`
- Dooray 업무의 첨부파일(본문/댓글 미삽입도 포함)에서 검색
- 파일 참조: `![filename](/files/fileId)` — cross-post 참조 가능 (re-upload 불필요)

**댓글 마크다운 구조**:
```markdown
## PC포커

### [PC포커] 무료 충전소(오퍼월)

* 대기실 아이콘 애니메이션 세부내용1, 세부내용2 **완료**

![260326_FX_Ani_Classic_LobbyIconOfferWall_Final.png](/files/12345)

<br>

### [PC포커] 브로드캐스팅 고도화

* Win, BigWin 연출 세부내용 **진행 중**

<br>
```

**세부 내용**: `AppState.dailyNotes`에서 해당 기간 내 노트를 수집, 중복 제거 후 콤마 구분
**상태 표시**: `_getTaskStatusLabel(task)` — 완료(100%/Done) / 진행 중 (빨간색 볼드)

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/automationPanel.js` | `_routineStepArtComment()`, `_extractPostIdFromUrl()`, `_extractProjectIdFromUrl()`, `_getTaskStatusLabel()` |

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

### 평가 자료 생성 (모달 하단 별도 섹션)

상위 조직장 평가용 자료 출력 — 일반 옵션과 시각적으로 분리된 하단 섹션
- **위치**: `.mh-eval-section` — 점선 구분선(border-top: 2px dashed) + 옅은 배경
- **컨트롤**: 연도 셀렉터(현재 ±2년) + `상반기`(1~6월) / `하반기`(7~12월) 버튼
- **동작**: 클릭 시 자동으로 ① periodType=months + 선택된 6개월 set ② 프로젝트별 그룹 ③ Task명/세부내용 ON ④ 렌더링 ⑤ 평가 형식으로 자동 Copy
- **출력 형식**:
  - 헤더: `[팀원명] YYYY년 상/하반기 평가 자료` + 기간 + 정량 요약 배지
  - 정량 요약: 참여 프로젝트 N개 | 완료 Task M/T개 | 작업일 K일
  - 본문: 프로젝트별 그룹 (진척률 높은 순 → Task 수 많은 순 → 이름순)
    - 각 프로젝트: `[platform] project (진척률 N%, M/T 완료)` + 좌측 컬러 바 (Done 초록 / 진행 파랑 / 0% 빨강)
    - 각 Task: 이름 + 상태 라벨(완료/N%/대기) + 작업일수
    - 세부내용: `dailyNotes` 줄별 분리, 작성자명 라인 자동 제거 (`AppState.teamMembers` 매칭)
- **Copy 결과**: HTML(스타일 포함) + Plain Text(마크다운) 듀얼 클립보드
- **팀원 미선택 시**: 경고 메시지 표시 후 중단
- **데이터 없을 때**: "해당 기간 작업 이력이 없습니다" 메시지

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `index.html` | `#memberHistoryModal` 하단 `.mh-eval-section` |
| `js/memberHistory.js` | `initEvalYearSelect()`, `_bindEvalButtons()`, `runEvaluation(half)`, `_copyEvaluationData()`, `_buildEvalPlainText()`, `_buildEvalHtml()` |
| `styles.css` | `.mh-eval-section`, `.mh-eval-header`, `.mh-eval-controls`, `.mh-eval-year`, `.mh-eval-btn`, `.mh-eval-status` |

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

## 팀원 역할 (업무 담당) 시스템

팀원에게 **업무 담당 역할**(팀리더·이펙트·애니메이션·시스템 등)을 다중 부여하는 시스템. 이름 하드코딩(`'정재화'`)을 제거하고, 역할로 정렬·기본 담당자·필터·담당자 추천을 **동적**으로 구동합니다.

### 데이터 모델
- `AppState.memberRoles`: `string[]` — 사용자 관리 역할 목록. **순서 = 우선순위, 첫 번째 = 대표(팀리더) 역할**. `null`이면 `APP_CONSTANTS.DEFAULT_MEMBER_ROLES`(`['팀리더','이펙트','애니메이션','시스템']`) 사용
- `member.roles`: `string[]` — 멤버별 다중 역할 (N:M — 한 명이 여러 역할, 한 역할에 여러 명). `teamMembers` 배열에 실려 **자동 저장**(order·hidden과 동일)
- `AppState.categoryRoleMap`: `{ '카테고리명': '역할명' }` — 카테고리→역할 매핑(담당자 자동 추천용)
- 영속화: `memberRoles` + `categoryRoleMap`은 storage save 4곳 + load 4곳에 포함 (categoryList 옆)

### 핵심 규칙 — "대표 역할 = 목록 첫 번째" (이름 무관)
`getLeaderRole()`는 `memberRoles[0]`을 반환 → 역할 **이름을 바꿔도(팀리더→대표 등) index 0 기준**이라 안 깨짐. `getLeaderName()`은 그 역할 보유자 중 `order` 최소, 없으면 visible 멤버 중 order 최소.

### team.js 헬퍼
| 함수 | 역할 |
|------|------|
| `getRoleList()` | resolved 역할 목록 (null→기본값) |
| `getLeaderRole()` / `getLeaderName()` | 대표 역할 / 대표 멤버 이름 (동적) |
| `getMemberRoles(name)` / `toggleMemberRole(name, role)` | 멤버 역할 조회/토글 |
| `getMembersByRole(role, visibleOnly)` | 역할 보유 멤버 이름 (order 순) |
| `addRole/renameRole/deleteRole/moveRole` | 역할 CRUD (rename/delete 시 member.roles + categoryRoleMap **cascade**) |

### 구동 기능
| 기능 | 동작 | 구현 |
|------|------|------|
| 팀리더 정렬 | 보고서 담당자 정렬 시 대표 역할 멤버를 맨 앞 (`'정재화'` 하드코딩 제거) | `report.js:_sortAssignees()` |
| 기본 담당자 | 두레이 새 업무/QA 등록 기본 담당자 = 대표 멤버 (없으면 fallback) | `taskCreator.js`, `qaRegister.js` |
| 담당자 자동 추천 | 카테고리↔역할 매핑 → 새 업무 생성 시 그 역할 보유자를 담당자로 | `taskCreator.js:_suggestAssignee()` |
| 역할별 필터 | Smart Filter 역할 칩 / Member Dashboard 역할 바 / Work History 역할 버튼(`role:` 토큰) | `smartFilter.js`, `memberDashboard.js`, `memberHistory.js` |

> **주의 — 아트실 보고자는 제외**: `teamScheduler_artTeamReporter`는 Dooray `memberId`와 쌍을 이루는 설정이라 이름만 리더로 바꾸면 ID와 어긋남(#2 ID-coupling 문제). 그대로 둠.
> **#2 ID↔이름 맵 (HOOK_MEMBER_MAP/syncManager.memberMap/qaRegister.FX_MEMBERS)**: Dooray memberId가 필요해 역할 시스템과 별개. `teamMembers`에 memberId 필드가 없어 동적화 불가 — 멤버 추가/개명 시 수동 유지 필요.

### Settings UI — "역할관리" 탭 (`#orgTabRoles`)
플랫폼/조직 관리 모달의 새 탭. **팀원관리 바로 옆**에 배치(연관 기능 인접). 모달 탭 라벨은 모두 **한 줄**(`.org-tab-label { white-space: nowrap }`) — 플랫폼·팀원관리·역할관리·조직관리·주간보고그룹·카테고리·변경이력. 3개 영역:
1. **역할 목록**: 추가/이름변경(클릭 인라인)/삭제/순서이동(▲▼), 첫 번째에 `대표` 태그
2. **멤버별 역할**: 멤버 × 역할 칩 토글 (다중) — **숨김(전배) 멤버는 제외**(`TeamManager.getVisibleMembers()`)
3. **카테고리 → 역할 매핑**: 카테고리별 드롭다운으로 역할 지정
- 팀원 관리 탭의 멤버 행에는 **역할 뱃지** 표시 (`.member-role-badge`, 대표는 주황 `.leader`)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/state.js` | `AppState.memberRoles`/`categoryRoleMap`, `APP_CONSTANTS.DEFAULT_MEMBER_ROLES`, 기본 멤버 `roles` |
| `js/storage.js` | save 4곳 + load 4곳 (`memberRoles`, `categoryRoleMap`) |
| `js/team.js` | 역할 헬퍼 + CRUD, `renderTeamList()` 역할 뱃지 |
| `js/main.js` | `switchOrgTab('roles')`, `renderRolesTab()`/`_renderRoleList()`/`_renderRoleMemberAssign()`/`_renderCategoryRoleMap()`/`addRoleFromInput()`/`_startEditRoleName()` |
| `js/report.js` | `_sortAssignees()` 동적화 |
| `js/taskCreator.js` | `_suggestAssignee()` + 기본 담당자 |
| `js/qaRegister.js` | 기본 담당자 = 리더 |
| `js/smartFilter.js` | `_activeRole`, `toggleRole()`, `_taskMatchesRole()`, 역할 칩 |
| `js/memberDashboard.js` | `_roleFilter`, 역할 바 |
| `js/memberHistory.js` | `role:` 토큰 선택, `_resolveSelection()`/`_memberLabel()` |
| `index.html` | `#orgTabRoles` 탭 (역할목록/멤버별/카테고리매핑) |
| `styles.css` | `.member-role-badge`, `.role-chip`, `.rma-*`, `.crm-*`, `.sf-role`, `.md-role-*`, `.mh-role-btn` |

## 카테고리 관리 (Settings)

Settings의 "플랫폼/조직 관리" 모달 > "카테고리 관리" 탭에서 두레이 새업무 및 Task 카테고리를 관리합니다.

**데이터**: `AppState.categoryList` — `null`이면 기존 Task에서 동적 추출, `string[]`이면 사용자 관리 목록
**진입점**: 두레이 새업무 모달 > 카테고리 라벨 옆 ⚙ 버튼 → `openOrgSettingsModal('categories')`

### 기능
- **카테고리 추가**: 텍스트 입력 + 추가 버튼 (중복 자동 차단, 알파벳순 정렬)
- **카테고리 이름 변경**: 항목명 클릭 → 인라인 input 전환 (Enter 저장 / Esc 취소) → 관련 Task/TeamTask category 필드 일괄 변경
- **카테고리 삭제**: 각 항목 우측 × 버튼
- **두레이 새업무 연동**: `taskCreator.js:_populateCategoryOptions()` — `AppState.categoryList` 우선 사용

### UI 디자인
팀원 관리 탭과 동일한 `team-form` + `team-list` 패턴:
- 입력창 + `btn-primary` + 아이콘 (팀원 추가와 동일)
- 항목 목록: `fa-tag` 아이콘 + 이름 (`member-name editable`) + 삭제 버튼 (`remove-member`)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/main.js` | `renderCategoryList()`, `addCategory()`, `deleteCategory()`, `renameCategory()`, `_startEditCategoryName()`, `switchOrgTab()` 카테고리 탭 처리 |
| `js/taskCreator.js` | `_populateCategoryOptions()` — categoryList 우선 사용 |
| `js/state.js` | `AppState.categoryList` 필드 |
| `js/storage.js` | save 4곳 + load 3곳 |
| `index.html` | `orgTabCategories` (`team-form` + `team-list` 구조), `#tcCategorySettingsBtn` |

## Planning 차트 팀별 Planned 빠른 추가

Planning 차트 팀 이름 행에 `+` 버튼을 클릭하면 해당 팀의 Planned 프로젝트를 바로 추가할 수 있는 미니 팝오버가 열립니다.

### 팝오버 입력 필드
| 필드 | 설명 |
|------|------|
| 플랫폼 | Gantt 기존 Task에서 자동완성 (datalist) |
| 프로젝트명 | 필수 입력 |
| 점검월 | `YY.MM` 형식, 기본값 다음 달 |
| 기획담당자 | 담당 기획자 이름 |
| URL | `dooray://` 또는 `https://` |

- 입력 후 추가 → `AppState.projectPlaceholders`에 저장 → `App.render()` → **Gantt에도 자동으로 보라색 그룹 헤더로 표시**
- `YY.MM` → `YYYY-MM` 자동 변환 (`releaseMonth` 필드)
- 팝오버 외부 클릭 / ESC로 닫기, 뷰포트 경계 넘침 자동 보정

### Placeholder 클릭 버그 수정
같은 platform+project를 가진 다른 조직의 Placeholder가 여러 개일 때 잘못된 팝오버가 열리는 버그 수정:
- Placeholder HTML에 `data-planning` 속성 추가
- `showPlaceholderDetail()` — `planning` 파라미터 추가, `find()` 조건에 planning 포함

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/views/planningOverview.js` | `_openAddPlannedPopover()`, `_closeAddPlannedPopover()`, `_submitAddPlanned()`, `data-planning` 속성, `showPlaceholderDetail()` planning 매칭 |
| `styles.css` | `.po-add-planned-btn`, `.po-add-planned-popover`, `.po-ap-*` |

## 일정 Gantt (PlanningGanttView) 월별 그룹

일정 Gantt(`js/views/planningGanttView.js`)에서 프로젝트를 `releaseMonth` 기준으로 월별로 묶어 표시합니다.

### 월 그룹 헤더
- `_renderMonthGroupHeader(month)` — `YYYY년 N월` 형태의 회색 헤더 행
- 같은 월의 프로젝트들(Planned P 뱃지 포함)이 헤더 아래 한 묶음으로 표시
- 월 없는 프로젝트("서비스월 미정")는 맨 마지막에 배치
- 월 필터(`_applyMonthFilter`) 적용 시 해당 월 그룹 헤더도 함께 숨김

### 일정 수동 입력 모달 빠른 추가 버튼
- `TEAM_PRESETS`: `'화면 UI'` → `'UI'`, `'연출'` → `'FX'`로 표기 변경
- 범례(legend)도 동일하게 `UI` / `FX`로 변경
- 버튼 크기 통일: `min-width: 36px` + `padding: 3px 0` + `text-align: center`
- `TEAM_NAME_NORMALIZE`: `{ '화면 UI': 'UI', '연출': 'FX' }` — Dooray 원본명 → 표시명 변환 (유지)

### 일정 수동 입력 모달 Task명 입력
수동 입력 모달에서 팀별로 Task명을 입력할 수 있습니다.

**모달 구조 (`pgm-team-group` 그룹)**:
```
.pgm-team-group
  ├── .pgm-main-row       (팀명 | 담당자 | 시작일 ~ 종료일 | 추가 버튼들)
  ├── .pgm-range-row      (추가 날짜 범위, 여러 개 가능)
  └── .pgm-task-section   (Task명 목록)
       └── .pgm-task-row  (불릿 + input + 삭제 버튼)
```

- `_addTaskRow(container, taskName)` — Task 행 동적 추가, 빈 Task명 입력 시 자동 포커스
- `_collectRows()` — `.pgm-team-group` 순회 → `{ team, assignee, tasks, ranges }` 수집
- 저장: `AppState.planningSchedules[projKey][].tasks: string[]`

### 팀 행 인라인 표시
팀 행을 `팀 | 담당자 | 작업기간 | Task내용` 한 줄로 표시합니다.

**레이아웃** (`.pg-team-cell` — `flex-direction: row`):
```
● FX  |  김보람  |  04.28~05.08  |  대기실 캐릭터 애니 9종
```
- `.pg-team-color-dot`: 색상 박스, `margin-right: 5px`
- `.pg-team-name`: 팀명, `width: 68px`
- `.pg-team-col-sep`: `|` 구분자 (회색)
- `.pg-team-assignee`: 담당자, `color: #333`
- `.pg-team-dates`: 작업기간, `color: #333`
- `.pg-team-tasks-inline`: Task 내용, `color: #333`, `flex: 1`, 말줄임표

**구분선**:
- 팀 행 사이: `.pg-team-row td { border-bottom: 1px solid #eee }`
- 달력 세로 그리드: `.pg-cal-td > div { background-image: repeating-linear-gradient(...) }` (16px 간격)

### 팀 색상 커스터마이징
범례(legend) 색상 점을 클릭하면 카테고리별 색상을 변경할 수 있습니다.

**구현**:
- `_userTeamColors`: `{ catKey: hexColor }` (localStorage `teamScheduler_pgTeamColors`)
- `_getTeamColor(name)` — 팀명 → 카테고리 키 → 사용자 정의 색상 → 기본 색상 순으로 결정
- `_getCatColor(catKey)` — 범례 색상 조회
- `_bindLegendColorPickers()` — `<label>` + `<input type="color" opacity:0>` 오버레이 패턴
- `input` 이벤트: 범례 점 즉시 반영, `change` 이벤트: localStorage 저장 + 재렌더

**바 텍스트 색상 자동 적용 (YIQ)**:
```javascript
function _getTextColorForBg(hex) {
    const brightness = (r*299 + g*587 + b*114) / 1000;
    return brightness > 148 ? '#333' : '#fff';  // 밝은 배경 → 검정, 어두운 배경 → 흰색
}
```
- `.pg-bar-label`에 인라인 `color` 적용 (text-shadow 없음)

**백업**: `planningGanttColors` 필드로 `saveData()`, `buildBackupData()`, 복원 3곳 모두 포함
- 복원 시 `localStorage.setItem('teamScheduler_pgTeamColors', ...)` 직접 저장

### 수동 입력 버튼 (단일 펜슬)
프로젝트 타이틀 행 오른쪽 편집 버튼이 데이터 유무에 따라 색상이 변경됩니다.

| 상태 | 스타일 | 설명 |
|------|--------|------|
| 데이터 없음 | 회색 (기본) | `.pg-act-edit` |
| 데이터 있음 | 보라색 | `.pg-act-edit-active` (보라 배경/테두리/아이콘) |

- 기존 수동 입력 보라색 pill(`pg-pill-manual`) 제거 → 버튼 색상으로 통합
- 툴팁: 데이터 있으면 `"수동 입력 (N팀, 편집)"` 표시
- Dooray에서 불러온 데이터(`teams.length > 0 && !isManual`)에는 초록 `N팀` pill 유지

### 프로젝트 타이틀 / 팀 행 시각적 구분
프로젝트 타이틀 행과 팀 행의 배경 대비를 강화하여 계층을 명확히 구분합니다.

- **타이틀 행**: `#EBF0FA`/`#E4ECF7` (파란 톤)
- **팀 행**: `#F8FAFE`/`#F2F6FD` (거의 흰색)
- **프로젝트명**: `font-weight: 600`, `color: #1a237e` (딥 인디고)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/views/planningGanttView.js` | `_renderMonthGroupHeader()`, `render()` 월별 그룹핑, `_applyMonthFilter()` 헤더 동기화, `TEAM_PRESETS`, `_addTaskRow()`, `_addRangeRow()`, `_collectRows()`, `_getTeamColor()`, `_getCatColor()`, `_getTextColorForBg()`, `_bindLegendColorPickers()`, `_renderBar()`, `_renderProjectSection()` |
| `styles.css` | `.pg-month-gh-*`, `.pgm-preset-btn`, `.pgm-team-group`, `.pgm-main-row`, `.pgm-range-row`, `.pgm-task-section`, `.pgm-task-row`, `.pg-team-cell`, `.pg-team-tasks-inline`, `.pg-team-color-dot`, `.pg-act-edit-active`, `.pg-legend-color-btn`, `.pg-legend-color-input` |
| `js/storage.js` | `planningGanttColors` — save/buildBackupData 2곳, loadData/applyEnvironmentData 3곳 |

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

## Planned ↔ Gantt 프로젝트 연결

Planning 차트의 Planned 프로젝트를 Gantt 차트의 실제 프로젝트 그룹과 수동 연결하는 기능입니다.
기획팀 프로젝트명과 Gantt(Dooray) 프로젝트명이 다를 때 사용합니다.

### 동작 흐름
```
Planned 팝오버 → "Gantt 프로젝트 연결" 드롭다운 → 선택
→ importKey 보존 (원본 platform|project|planning)
→ Planned의 platform/project를 Gantt 이름으로 덮어쓰기
→ linkedProject 필드에 연결 키 저장
```

### Placeholder 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| `linkedProject` | string | 연결된 Gantt 프로젝트 키 (`platform\|project`) |
| `importKey` | string | 연결 전 원본 키 (`platform\|project\|planning`) — Plan Import 재매칭용 |

### 연결 시
1. `importKey`가 없으면 현재 `platform|project|planning`을 보존
2. Planned의 `platform`/`project`를 Gantt 프로젝트 값으로 덮어쓰기
3. Planning 차트에서 Gantt 프로젝트명으로 표시 + 원본명 서브텍스트

### 연결 해제 시
1. `importKey`에서 원본 `platform`/`project` 복원
2. `linkedProject` 초기화

### Plan Import 3단계 매칭
`plannedImport.js:compareWithExisting()`:
1. **1순위**: 현재 `platform|project|planning` 키로 매칭
2. **2순위**: `importKey`로 매칭 (연결 후 이름이 변경되어도 Plan Import가 원본을 찾을 수 있음)
3. **3순위**: `importKeyShortMap` — `platform|project`만으로 매칭 (planning 불일치 대비)

**중복 Placeholder 처리**:
- `existingMap`에서 `linkedProject`가 있는 Placeholder 우선 등록
- `matchedPhIds` Set으로 매칭된 Placeholder ID 추적
- 삭제 감지: sibling check — 같은 `platform|project`의 다른 Placeholder가 매칭되면 삭제 제외

### 비주얼 (Planning 차트 셀)
- **연결 뱃지**: 프로젝트명 옆 🔗 아이콘 (`.ph-linked-badge`) — Placeholder + 활성 프로젝트 모두 표시
- **원본명 서브텍스트**: 프로젝트명 아래 작은 회색 텍스트 (`.ph-orig-name`) — Placeholder + 활성 프로젝트 모두 표시
- **기획자명**: 활성 프로젝트에도 Planned의 기획자명 표시 (`.ph-planner-text`)
- **팝오버 원본명**: Planned 팝오버 드롭다운 아래 작은 회색 텍스트 (`.ph-detail-orig`)

### 진행중 프로젝트 팝오버 "Planned 원본" 섹션
연결된 활성 프로젝트 클릭 시 팝오버에 Planned 원본 정보를 별도 섹션으로 표시

- **조건**: `ph.linkedProject`가 있을 때만 표시
- **표시 항목**: 원본 프로젝트명 (importKey), 조직, 점검월, 기획자
- **배경**: 보라색 배경 (`#f8f0ff`) + 보라 구분선 (`#e0d0f0`)
- **CSS**: `.pd-planned-section`

### groupTasksByTeam() 데이터 전달
- `projectData` 객체에 `linkedProject`, `importKey` 포함 필수
- placeholder → 기존 그룹 merge 시에도 `linkedProject`, `importKey` 전달 필수

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/views/planningOverview.js` | `showPlaceholderDetail()` — 드롭다운 UI + 연결/해제 로직, `_getGanttProjectList()` |
| `js/views/planningOverview.js` | `showProjectDetail()` — "Planned 원본" 섹션 표시 |
| `js/views/planningOverview.js` | `groupTasksByTeam()` — `linkedProject`/`importKey` 데이터 전달 (projectData + merge) |
| `js/views/planningOverview.js` | 렌더링 — Placeholder + 활성 프로젝트 모두 연결 뱃지/원본명/기획자 표시 |
| `js/plannedImport.js` | `compareWithExisting()` — importKey 기반 2단계 매칭 |
| `styles.css` | `.ph-detail-link-*`, `.ph-linked-badge`, `.ph-orig-name`, `.ph-detail-orig`, `.pd-planned-section` |

## 프로젝트 상세 → Gantt 이동

Planning 차트에서 프로젝트 클릭 시 프로젝트 정보 + Task 목록을 팝오버로 표시합니다.

### 진행중 프로젝트 팝오버
Planned 프로젝트와 동일한 위치/크기 패턴의 팝오버로 프로젝트 정보와 Task 목록을 함께 표시합니다.

**표시 정보 (2단 그룹)**:
- **FX팀 영역**: 진행률 (프로그레스 바 + 완료/전체 카운트), 점검월, 담당자, 위키 URL
- **기획 영역**: 담당팀(조직), 담당기획자, 기획제목(planningTitle), 기획 URL
- **Planned 원본**: 연결된 Planned가 있으면 원본 프로젝트명/조직/점검월/기획자 표시 (보라색 배경, `.pd-planned-section`)
- **Task 목록**: Task명, 진행률, Status (startDate 정렬, 최대 240px 스크롤)
- Task 클릭 → Gantt 이동 + 하이라이트

**담당자 표시**: 전체 Task의 assignee를 개별 이름으로 분리 → 중복 제거 → `TeamManager.getDisplayAssignee()`로 Display Group 매칭 (3명 전원 → "FX팀")

**기획 담당자 매칭**: Placeholder에서 planner 검색 (5단계 fallback)
1. platform + project 정확 매칭
2. project + planning 매칭
3. project만 매칭
4. planning 일치 + project 부분 매칭 (`_bestPartial()`: platform+project 동시 포함 우선)
5. project 부분 매칭 (`_bestPartial()`: platform+project 동시 포함 우선)

**팝오버 너비**: 432px (Planned 280px보다 넓음 — Task 테이블 포함)

### Planned 프로젝트 팝오버
기존과 동일 — 프로젝트명, 팀, 담당기획자, URL, 점검월 편집

### Gantt 이동 동작
1. Task 행 클릭 → 팝오버 닫힘
2. Hide Done/Bypass로 숨겨진 Task면 자동 해제
3. Gantt 뷰로 전환 (그룹 자동 펼침)
4. Task 행으로 스크롤 + 노란색 깜빡임 하이라이트 (3초)

### Planning 차트 플랫폼 정규화
`groupTasksByTeam()`에서 Task와 Placeholder의 platform을 `App.getPlatformDisplayName()`으로 정규화한 후 그룹핑 키 생성.
예: Task `클래식` + Placeholder `포커클래식` → 정규화 후 동일 키로 합쳐짐.
Settings > 플랫폼 관리에서 별칭 등록 필요.

### 분산 프로젝트 진행률 표시 (Shared Project)

같은 `platform|project` 프로젝트가 여러 planning 팀에 Task가 분산된 경우, 각 팀 셀에 **전체 프로젝트 진행률**을 추가로 표시합니다.

**문제 배경**: Planning 차트의 그룹 키는 `planning|||platform|||project`로 팀별 Task 진행률을 계산함. 한 팀이 모든 Task를 완료해도 다른 팀 셀은 0%로 표시되어 프로젝트 완료 여부 인지가 어려움.

**해결 방식 (두 가지 진행률 병행 표시)**:
- **셀 메인 진행률**: 그 팀이 맡은 Task 기준 (작업량 책임 명확) — 기존 유지
- **🔗 전체 N%**: 모든 팀의 Task를 합산한 전체 프로젝트 진행률 (셀 하단, 회색 작은 글씨)
- 100% 완료 시 초록색 + ✓ 체크 (`.shared-done`) → 사업팀 6/6 + 서비스기획팀 0/0 케이스에서 두 셀 모두 "🔗 전체 100% ✓"로 완료 인지

**데이터 흐름** (`groupTasksByTeam()`):
1. `overallByProject`: `platform|project` 키로 전체 Task 합산 (planning 무관)
2. `projectTeamCount`: 같은 프로젝트가 몇 개 팀에 분산됐는지 Set 카운트
3. 각 `projectData`에 `isShared`, `overallProgress`, `overallDoneCount`, `overallTotalCount` 부여
4. `plannedCount` 로직도 동일 적용 (Gantt와 일관성)

**팀별 분담 섹션** (showProjectDetail 팝오버):
- 2개 이상 팀에 분산된 경우만 표시 (`showTeamBreakdown`)
- 각 팀: 이름 + 진행률 바 + % + (done/total) 형식
- 색상: 100% 초록 / ≥50% 파랑 / >0 노랑 / 0 회색

**적용 대상**: Placeholder 셀 + 활성 프로젝트 셀 모두 적용

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/views/planningOverview.js` | `groupTasksByTeam()` — `overallByProject` + `projectTeamCount` 계산, `renderTeamRows()` — `sharedLine` 렌더링, `showProjectDetail()` — `teamBreakdown` + "팀별 분담" 섹션 |
| `styles.css` | `.project-info-shared-progress`, `.shared-done`, `.pd-team-breakdown-section`, `.pd-tb-row/name/bar/fill/text/count` |

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/views/planningOverview.js` | `showProjectDetail()` — 진행중 프로젝트 팝오버 (정보+Task+Planned원본+팀별분담), `showPlaceholderDetail()` — Planned 팝오버, `_normPlatform()` — 플랫폼 정규화 |
| `js/report.js` | `navigateToGanttTask()` — Gantt 이동 + 하이라이트 |
| `js/commandPalette.js` | `_navigateToTask()` — 동일한 Hide Done/Bypass 자동 해제 적용 |
| `styles.css` | `.pd-project-popover`, `.pd-info-*`, `.pd-info-section`, `.pd-section-label`, `.pd-task-*` (진행중), `.pd-planned-section`, `.ph-detail-*` (Planned) |

## 헤더 ⚙ 바로가기 버튼

주요 차트 헤더에 ⚙ 버튼으로 설정 모달을 빠르게 열 수 있습니다.

| 위치 | 동작 | 구현 |
|------|------|------|
| Gantt Platform 헤더 | `openOrgSettingsModal('platforms')` | `gantt.js` 헤더 HTML, onclick 인라인 |
| Planning Team 헤더 | `openOrgSettingsModal('teams')` | `planningOverview.js` `.planning-team-settings-btn` + `bindEvents()` |
| Task 편집 모달 Platform | `openOrgSettingsModal('platforms')` | `index.html` `#managePlatformFromTaskBtn` |
| Task 편집 모달 Organization | `openOrgSettingsModal('teams')` | `index.html` `#manageOrgFromTaskBtn` |
| Task 편집 모달 Assignee | `openOrgSettingsModal('members')` | `index.html` `#manageTeamFromTaskBtn` |

**패턴**: `btn-icon-inline` CSS 클래스 (10px, opacity 0.6 → hover 1.0)

## Automation Panel (자동화)

자동화 기능의 Feature Flag 관리 + 상태 확인 + 실행 로그를 제공하는 사이드 패널입니다.

### 진입점
- 사이드 메뉴 → "Automation" (`#automationPanelBtn`)
- 단축키: `A`

### Feature Flags (automationFlags)
`AppState.automationFlags` — Settings가 아닌 Automation 패널에서 직접 토글

| 플래그 | 기본값 | 설명 |
|--------|--------|------|
| `autoSyncOnStart` | false | 앱 시작 시 자동 Sync |
| `backgroundPolling` | false | 백그라운드 폴링 |
| `pollingInterval` | 30 | 폴링 간격 (분) |
| `thursdayAlert` | true | 목요일 알림 |
| `planningGanttGapDetect` | false | Planning-Gantt 괴리 감지 |
| `planImportAutoCompare` | false | Plan Import 자동 비교 |
| `routineTarget` | 'teamplay' | 루틴 대상 ('teamplay' \| 'artteam') |
| `scheduledCreateEnabled` | false | 예약 팀플레이 자동 생성 |
| `scheduledCreateDay` | 5 | 요일 (0=일~6=토, 기본 금요일) |
| `scheduledCreateHour` | 9 | 시 (0~23) |
| `scheduledCreateMinute` | 0 | 분 (0~59) |

### 패널 구성
| 섹션 | 내용 |
|------|------|
| Sync | 자동 Sync on/off, 백그라운드 폴링 on/off + 간격 설정, 마지막 Sync 시각, 다음 Sync 카운트다운(초록) |
| 목요일 루틴 | 카운트다운 → 팀플레이 생성+옵션 → 주간보고 작성+대상선택 → 목요일 알림 메시지 안내 |
| 자동 감지 | Planning-Gantt 괴리, Plan Import 자동 비교 on/off + 비교 결과 표시 |
| 자동 백업 | on/off 토글 + pill 형태 시간 설정 + 카운트다운(초록) + 마지막 백업 날짜/시간/GitHub 상태 |
| 실행 로그 | 자동 실행 이력 (최대 50건, 런타임 전용) |

### 목요일 루틴 섹션 구성
```
┌─ 목요일 루틴 ──────────────────────────────────────┐
│ [펄스점] 다음 목요일(MM.DD)까지 N일 N시간 N분 남았습니다  │  ← 초록 배경 카운트다운
│                                                      │
│ [🔥𝗙𝗫 [팀플레이] 생성] [요일/시/분 드롭다운]            │
│ ☐ 예약 자동 생성                                      │
│ ☐ 댓글 정리 (완료 제외, 내용 초기화)                    │
│ ──────────────────── (구분선) ────────────────────── │
│ [주간보고 작성] (상태 힌트) ○ 팀플레이 ○ 아트실         │  ← 목요일 아닌 날 딤 처리
│ (파이프라인 컨테이너)                                  │
│ ☐ 목요일 알림 메시지 안내                              │
└──────────────────────────────────────────────────────┘
```

**목요일 카운트다운**: `_calcThursdayCountdown()` — 다음 목요일 09:00까지 남은 시간 계산, 초록색 배경(`#E6F4EA`), 펄스 점(`.atp-sync-pulse`)
**주간보고 작성 딤 처리**: 목요일 아닌 날 `.atp-routine-dimmed` (opacity 0.45, hover 시 0.8)
**주간보고 작성 상태 힌트**: `_getRoutineStatusHint()` — 목요일 미작성/작성완료/수동실행 표시
- 확인 우선순위: ① `AppState.automationLog` (런타임) → ② `teamScheduler_lastRoutineTime` (localStorage) → ③ `_checkRoutineCompletedOnDooray()` (Dooray API 백그라운드)
- 패널 열 때 `_checkRoutineCompletedOnDooray()` 호출: localStorage에 기록 없어도 Dooray 업무 조회로 완료 여부 확인

**팀플레이 마지막 생성 표시**: `_renderLastTeamplayCreate()` — 마지막 생성 `MM.DD HH:MM 완료(수동)/완료(자동)/이미 존재(스킵)` 표시
**localStorage 키**:
| 키 | 저장 시점 | 내용 |
|---|---|---|
| `teamScheduler_lastRoutineTime` | 루틴 완료 시 | ISO 타임스탬프 |
| `teamScheduler_lastRoutinePostInfo` | 루틴 완료 시 | `{ projectId, postId }` |
| `teamScheduler_lastScheduledCreate` | 팀플레이 생성 시 (수동/자동 공통) | `YYYY-MM-DD` |
| `teamScheduler_lastTeamplayCreateResult` | 팀플레이 생성 시 | `{ time, mode, title, skipped }` |

### Plan Import 자동 비교 (A-5)
앱 시작 시 Google Sheets와 기존 Planned를 자동 비교하여 변경사항을 알려줍니다.

**동작**:
- `planImportAutoCompare` 플래그 활성화 + Sheets URL 설정 시 앱 시작 5초 후 자동 실행
- `PlannedImport.autoCompare()` — UI 없이 백그라운드에서 Sheets fetch → parse → compare
- 결과를 `_autoCompareResult`에 저장 (런타임 전용)

**결과 표시**:
- Automation 패널: 추가(+N)/변경(~N)/삭제(-N) 카운트 + 비교 시각 + "열기" 버튼
- 사이드 패널: Plan Import 버튼에 빨간 뱃지 (변경 총 건수, `.pi-auto-badge`)
- 변경 있을 때 토스트 알림

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/plannedImport.js` | `autoCompare()` (headless 비교), `getAutoCompareResult()` |
| `js/automationPanel.js` | `_runPlanAutoCompare()`, `_renderPlanCompareResult()`, `_updatePlanImportBadge()`, `onAppStart()` 연결 |
| `styles.css` | `.atp-plan-*` (결과 표시), `.pi-auto-badge` (사이드 뱃지) |

### 목요일 알림 (A-3)
- 앱 시작 시 `checkThursdayAlert()` — 오늘이 목요일이면 토스트 알림
- **스킵 조건** (완료 이미 됐으면 토스트 미표시):
  - `lastRoutineTime`이 오늘이면 스킵 (주간보고 작성 완료)
  - `lastScheduledCreate`가 오늘이면 스킵 (팀플레이 생성 완료)
  - 스킵 시에도 `lastThursdayAlert` 저장 (하루 1회 제한 유지)
- **토스트 디자인**: 하단 중앙 라운드 팝업 (초록 계열 `#E6F4EA`, `border-radius: 16px`)
  - 아래에서 위로 슬라이드 인 (cubic-bezier 애니메이션)
  - 벨 아이콘 + 제목 + 3개 액션 버튼(동일 너비 96px) + ✕ 닫기 버튼
  - 버튼: "루틴 실행" / "팀플레이 생성" / "Weekly 열기" (초록 배경, 한 줄 배치)
- 15초 자동 닫힘
- 하루 1회 제한: `localStorage.teamScheduler_lastThursdayAlert`
- CSS: `.atp-thursday-toast` (기존 우측 상단 토스트와 완전히 다른 디자인)

### 팀플레이 자동 생성 (`createTeamplayPost(autoMode)`)
이전주 팀플레이를 기반으로 이번 주 새 문서를 Dooray에 자동 생성합니다.

**흐름**:
```
팀플레이 생성 → 중복 확인 → 이전주 검색 → 정재화 댓글 찾기
→ Dooray POST (새 업무) → 워크플로우 변경 → 댓글 복사 → 완료
```

**autoMode 파라미터**:
| 모드 | confirm | 중복 시 | 완료 후 |
|------|---------|---------|---------|
| `false` (수동 버튼) | 생성 전/후 confirm 표시 | confirm으로 재생성 가능 | Dooray 열기 confirm |
| `true` (예약 자동) | confirm 없음 (완전 자동) | 자동 스킵 + 로그 | 토스트만 표시 |

**생성 내용**:
| 항목 | 값 |
|------|-----|
| 제목 | `🔥𝗙𝗫 [팀플레이] {year}.{month}월 {week}주차 ({monday}~{friday})` |
| 본문 | 이전주 링크(`dooray://`) + 빈 12컬럼 표 |
| 담당자 | 정재화 |
| 댓글 | 이전주 정재화 댓글 복사 |

**워크플로우 자동 변경**:
| 대상 | 변경 | 워크플로우 ID |
|------|------|-------------|
| 새 팀플레이 | 할 일 → **진행 중** | `4028352443602869266` |
| 이전주 팀플레이 | 진행 중 → **완료** | `4028352443658351504` |

- `_setPostWorkflow(projectId, postId, workflowId)` — `PUT /posts/{postId}` + `{ workflowId }`
- 워크플로우 변경 실패해도 나머지 작업(댓글 복사 등)은 계속 진행

**주차 계산**: `Utils.getWeekInfo()` — 금요일 기준 월 판정 (보고서와 동일)

**주요 함수**:
| 함수 | 역할 |
|------|------|
| `createTeamplayPost(autoMode)` | 전체 흐름 오케스트레이션 |
| `_buildTeamplayTitle(wi)` | 제목 생성 |
| `_buildTeamplayBody(...)` | 본문 생성 (이전주 링크 + 빈 표) |
| `_setPostWorkflow(projectId, postId, workflowId)` | Dooray 워크플로우 변경 |
| `_searchTeamplayPosts(projectId, pattern)` | 패턴으로 업무 검색 |
| `_fetchComments(projectId, postId)` | 댓글 목록 조회 |
| `_findCreatorComment(comments, memberId)` | 특정 작성자 댓글 찾기 |

**Dooray 설정**:
| 값 | 상수 |
|-----|------|
| 프로젝트 ID | `4028352443299472148` (클래식FX팀-업무관리) |
| 조직 ID | `1387695619080878080` |
| 정재화 memberId | `2029850955956616509` |

**Dooray 워크플로우 ID** (클래식FX팀-업무관리):
| 상태 | ID |
|------|-----|
| 할 일 | `4028352443545116099` |
| 진행 중 | `4028352443602869266` |
| 완료 | `4028352443658351504` |

### 예약 팀플레이 자동 생성
- `scheduledCreateEnabled` 활성화 시 매분 체크 (`_scheduleTimer`)
- 설정된 요일+시간에 `createTeamplayPost(true)` 자동 실행 (완전 자동, confirm 없음)
- 하루 1회 제한: `localStorage.teamScheduler_lastScheduledCreate`
- UI: 요일/시/분 드롭다운 + "매주 X HH:MM" 라벨
- **`lastScheduledCreate` 저장**: 수동 생성(`autoMode=false`)과 자동 생성 모두 성공/스킵 시 저장 → 앱 재시작 후 팝업 방지
- **`_renderLastTeamplayCreate()`**: `teamScheduler_lastTeamplayCreateResult`에서 생성 시각+모드 읽어 UI에 표시

### 자동 Sync (`_runAutoSync()`)
이번 주 팀플레이를 자동으로 찾아 Sync 실행 + 결과 자동 적용

**흐름**:
```
팀플레이 검색 → syncComments → 제목변경 감지 → Work 마크 적용 → 새 업무 추가 → 완료 처리 → 저장 + 렌더
→ (syncNextWeekAfterThursday ON + 조건 충족 시) 다음주 팀플레이도 동일하게 Sync
```

**적용 항목**: 새 업무(+배지), 완료 처리(+배지), Work 마크(+배지), 제목/프로젝트 변경
**알림**: 변경사항이 있으면 토스트, 실행 로그에 요약 (`댓글 N | 파싱 N | 신규 +N | Work +N`)
**안전성**: 추가 전용(additive) — 기존 데이터 삭제/덮어쓰기 없음, 실패 시 기존 데이터 영향 없음

### 다음주 포함 Sync (`syncNextWeekAfterThursday`)
목요일 오후부터 팀원이 다음주 팀플레이에 업무 댓글을 작성하기 시작하므로, 해당 문서도 Sync하는 기능

**Flag**: `AppState.automationFlags.syncNextWeekAfterThursday` (boolean)
**UI**: Automation 패널 > Sync 섹션 > "다음주 포함 Sync" 토글

**자동 ON 조건** (수동 토글 외):
- `createTeamplayPost()` 성공 완료 시 자동 ON + `Storage.saveAutomationFlags()`
- `_runAutoSync()` 실행 시 목(4) 오후(>=12) / 금(5) / 토(6) / 일(0)이면 OFF여도 자동 ON

**자동 OFF 조건**:
- `_runAutoSync()` 실행 시 월요일(1)이고 flag가 ON이면 자동 OFF + 저장
- 앱 재시작 없이 폴링 주기(최대 30분) 안에 자동 전환됨

**자동 실행 조건** (ON 상태에서 `_runAutoSync()` 실행 시):
| 요일 | 조건 | 결과 |
|------|------|------|
| 월요일 (1) | 항상 | flag 자동 OFF |
| 목요일 (4) + 오후(>=12시) | 조건 충족 | 다음주 Sync 실행 |
| 금(5), 토(6), 일(0) | 조건 충족 | 다음주 Sync 실행 |
| 화(2), 수(3), 목 오전 | 조건 미충족 | 로그만 남기고 스킵 |

**다음주 Sync 흐름**: `Utils.getWeekInfo(new Date(), 1)`로 다음주 패턴 생성 → 이번주와 동일한 syncComments/applyWorkMarks/addNewTasksWithRemoteInfo 수행

### 자동 백업
지정 시간에 데이터 저장 + GitHub Push를 자동 실행합니다.

**UI**: Automation 패널 > 자동 백업 섹션
- on/off 토글 (`teamScheduler_backupEnabled`)
- pill 형태 시간 설정 (클릭 인라인 편집, +/✕)
- 초록 펄스 점 + 카운트다운 (Sync/목요일 루틴과 동일 디자인)
- 마지막 백업: 날짜+시각 + GitHub 상태 (✓/변경없음/실패)

**실행 흐름**:
1. `Storage.saveData()` — 로컬 데이터 저장
2. `githubUpload()` — GitHub API Push
3. 결과 로그 + 토스트

**플로팅**: 하단에 `Backup N시간 N분 후` 초록 pill (Sync 오른쪽 배치)
**스케줄**: `teamScheduler_backupSchedules` (localStorage), 매분 체크, 하루 1회 제한
**상태 저장**: `teamScheduler_lastAutoBackupTime`, `teamScheduler_lastAutoBackupStatus`

**⚠️ `saveAutomationFlags()` 주의**: 자동 백업 스케줄(`backupSchedules`) 저장 시 `Storage.saveData()` 대신 `Storage.saveAutomationFlags()` 사용
- 이유: `saveData()`는 `AppState.tasks`가 비어있으면 저장을 스킵하는 guard가 있음 (데이터 보호 목적)
- 이 guard가 자동화 설정까지 저장을 막아 스케줄이 사라지는 버그 발생
- `saveAutomationFlags()`: 해당 guard를 우회하여 automation 설정만 선택적으로 저장 (`storage.js`)

### 앱 시작 시 자동 실행 (`onAppStart()`)
1. 목요일 알림 체크 (`checkThursdayAlert()`) — 완료 여부 확인 후 스킵 또는 토스트
2. `autoSyncOnStart`면 3초 후 자동 Sync
3. `backgroundPolling`이면 폴링 타이머 시작
4. `scheduledCreateEnabled`면 예약 체커 시작 + 놓친 예약 보완 (`_checkMissedSchedule()` 8초 후 실행)
5. 자동 백업 체커 시작 (`_startBackupChecker`)

### 놓친 예약 팀플레이 생성 확인 (`_checkMissedSchedule()`)
앱 시작 8초 후 실행 — localStorage 기록이 없을 때 Dooray에서 직접 확인 후 팝업 여부 결정

**확인 흐름**:
1. `scheduledCreateEnabled` 플래그 + 오늘 요일 + 예약 시간 경과 여부 체크
2. `lastScheduledCreate`가 오늘이면 스킵
3. localStorage 기록 없으면 → Dooray API로 다음 주 팀플레이 존재 여부 확인
   - `_searchTeamplayPosts(projectId, nextWeekPattern)` 재사용
   - 존재하면: `lastScheduledCreate` + `lastTeamplayCreateResult` 저장 후 스킵
4. 없으면 confirm 팝업 → 사용자가 수락하면 `createTeamplayPost()` 실행

**8초 지연 이유**: Dooray 토큰 준비 + 앱 초기화 완료 대기 (5초 지연으론 간헐적 실패)

### 주간보고 작성 (C-1) — `runThursdayRoutine()`
Sync → 댓글 조회 → 표 생성 → 본문 업데이트/아트실 생성을 원클릭으로 순차 자동 실행합니다.

**루틴 대상 선택**: `AppState.automationFlags.routineTarget` ('teamplay' | 'artteam')
- **팀플레이 (FX팀)**: Step 4 = 본문 업데이트 (`WeeklyReportGenerator.updatePost()`)
- **아트실 주간보고**: Step 4 = Dooray 새 업무 생성 (`_routineStepArtTeam()`)
- UI: `.atp-routine-target-row` 라디오 버튼

**단계별 파이프라인**:
| 단계 | 이름 | 동작 |
|------|------|------|
| 1 | Sync | 팀플레이 검색 → syncComments → 변경 적용 (기존 `_runAutoSync` 로직) |
| 2 | 댓글 조회+파싱 | headless `fetchWeeklyReportComments` — localStorage 설정 사용 |
| 3 | 표 생성 | `WeeklyReportGenerator.updateTable()` |
| 4a | 본문 업데이트 | [팀플레이] `WeeklyReportGenerator.updatePost()` |
| 4b | 아트실 주간보고 생성 | [아트실] Dooray POST (주간 요약 + 표) — `_routineStepArtTeam()` |

**파이프라인 UI**:
- 각 단계: 이름 + 프로그레스바 + 상태 아이콘 + 결과 텍스트
- 상태: pending(회색시계) → running(파랑스핀) → done(초록체크) → error(빨강X)
- 오류 시 해당 단계에서 멈춤 + 오류 메시지 표시
- 완료 시 "Dooray 열기" 버튼 표시

**진입점**:
- Automation 패널 목요일 루틴 섹션 "주간보고 작성" 버튼 (`#atpRunRoutine`, 보라색)
- 목요일 알림 토스트 "주간보고 작성" 버튼 → 패널 열기 + 자동 실행

**headless Weekly 설정**: `localStorage('weeklyReportSettings')`에서 로드 — columns, organizationOrder, platformMap, stripDatePrefix, urlCompact, includeWiki, taskSortOrder

**구현 위치**: `automationPanel.js` — `runThursdayRoutine()`, `_routineStep*()`, `_routineStepArtTeam()`, `_renderRoutineHTML()`, `_renderRoutineUI()`, `_updateRoutineStep()`

### 실행 로그
- `AppState.automationLog` — 런타임 전용 (저장 안 됨)
- `addLog(type, message)` — type: `info`, `sync`, `alert`, `error`
- 최대 50건 유지

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/automationPanel.js` | AutomationPanel 모듈 전체 |
| `index.html` | `#automationPanel` HTML + 사이드 패널 `#automationPanelBtn` |
| `js/state.js` | `AppState.automationFlags`, `AppState.automationLog` |
| `js/storage.js` | automationFlags save/load (4+4곳) |
| `js/main.js` | 이벤트 바인딩, Escape, bringToFront, `A` 단축키, `onAppStart()` 호출 |
| `styles.css` | `.automation-panel`, `.atp-*`, `.atp-thursday-toast`, `.atp-rt-*` (루틴 파이프라인), `.atp-sync-pulse`, `.atp-thursday-countdown`, `.atp-divider`, `.atp-routine-dimmed`, `.atp-routine-status`, `.auto-sync-float` |

### 자동화 계획 문서
- **`PLAN-AUTOMATION.md`**: Phase A~C 전체 계획, 기획 상태 추적, 변경 이력

## Guide Panel (업무 가이드)

프로젝트별 업무 규칙/패턴/관리 방법을 카테고리별로 정리하여 사이드 패널로 표시합니다.

### 진입점
- 사이드 메뉴 → "Guide" (`#guidePanelBtn`)

### 핵심 기능
| 기능 | 설명 |
|------|------|
| 탭 | 포커 > 바둑 > 기타 (우선순위), `+` 버튼으로 커스텀 탭 추가 |
| 섹션 카드 | 제목 + 리치 콘텐츠 + 관리위치(⚙) |
| 편집 | hover → 연필 아이콘 → 인라인 편집 (제목/내용/관리위치) |
| 탭 관리 | 우클릭 → 이름 변경/삭제 |
| 초기화 | ↩ 버튼 → 기본 가이드로 리셋 |

### 리치 렌더링 (`_renderRichContent`)
| 패턴 | 렌더링 | CSS 클래스 |
|------|--------|-----------|
| `[키워드]` | 파란 뱃지 | `.gp-keyword` |
| `from → to` | 2컬럼 매핑 | `.gp-mapping` |
| `예시:` | 파란 좌측 바 블록 | `.gp-example-block` |
| `- 항목` | 파란 불릿 리스트 | `.gp-line-bullet` |
| `1. 항목` | 파란 번호 리스트 | `.gp-line-numbered` |
| `**볼드**` | `<strong>` | |
| `` `코드` `` | 코드 스팬 | `.gp-code` |

### 초기 콘텐츠
| 탭 | 섹션 |
|---|---|
| 포커 | 제목 패턴, 플랫폼 목록, 조직, 보고서 그룹 매핑, 댓글 형식 |
| 바둑 | 제목 패턴, 플랫폼 목록, 플랫폼 약어 규칙, planningTitle 파싱 |
| 기타 | 새 프로젝트 등록 절차, 공통 상태 태그, Plan Import |

### 데이터
- `AppState.guideNotes` — null이면 `DEFAULT_GUIDES` 사용, 편집하면 사용자 데이터로 저장
- storage.js: save 4곳 + load 4곳 (teamAnnualPlans와 동일 패턴)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/guidePanel.js` | GuidePanel 모듈 (렌더링, 편집, 리치 포맷) |
| `index.html` | `#guidePanel` HTML + 사이드 패널 `#guidePanelBtn` |
| `js/main.js` | 이벤트 바인딩 + Escape 핸들러 + bringToFront 위임 |
| `js/state.js` | `AppState.guideNotes` 필드 |
| `js/storage.js` | save/load/backup/restore/import 모든 경로 |
| `styles.css` | `.guide-panel`, `.gp-*` 스타일 |

## Planning 차트 Day Progress Bar

월 헤더 아래에 날짜별 진행 바를 표시하여 한 달 중 현재 위치를 시각화합니다.

**구조**: `<div class="po-day-bar">` 안에 날짜별 `<span class="po-day-seg">` 요소
**색상**:
- 지나간 날: 파랑 (`--google-blue`, opacity 0.5)
- 오늘: 파랑 (opacity 1.0)
- 점검일: 주황 (`--maintenance-bg`, `#FF6B35`)
- 미래: 회색 배경 (`#e8eaed`)

**데이터**: `AppState.maintenanceDays` — `YYYY-MM-DD` 문자열 배열

**좌우 여백**: `margin-left: -6px; margin-right: -6px` — 셀 padding 안쪽까지 확장

**현재월 뱃지**: `.current-month-badge` — 파란 라운드 배경, `padding: 0 12px`, `line-height: inherit` (다른 월과 높이 동일하게 유지)

**Planning 헤더 배경**: `--planning-header-bg` (기본 `#ECEEF0`) — Gantt 헤더(`--header-bg: #F8F9FA`)보다 약간 어둡게 분리

**구현 위치**:
- `planningOverview.js`: `renderMonthHeaders()`, `_renderDayProgressBar()`
- CSS: `.po-day-bar`, `.po-day-seg`, `.po-day-past`, `.po-day-today`, `.po-day-mt`, `.current-month-badge`

## Planning 차트 border-separate

Planning 차트 테이블은 `border-collapse: separate` + `border-spacing: 0`을 사용합니다.

**이유**: `border-collapse: collapse`에서 `thead { position: sticky }`를 사용하면 스크롤 시 border가 사라지는 브라우저 알려진 이슈
**해결**: `border-collapse: separate`로 변경하여 sticky 헤더의 border가 스크롤 시에도 유지
**border 적용**: `border-bottom` + `border-right`를 모든 셀에, `border-left`는 첫 번째 셀에, `border-top`은 첫 번째 헤더 행에 적용

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

## 팀원 순서 관리

Settings > 팀원 관리에서 숫자 입력으로 팀원/그룹 표시 순서를 변경합니다.

**순서 규칙**: `사람+그룹 1~10 · AI+그룹 10~30`
**데이터**: `member.order` (개인), `AppState.teamDisplayGroupOrders` (그룹)
**정렬**: `TeamManager.getOrderedMembersAndGroups()` — 개인+그룹 통합 order 정렬
**적용**: Smart Filter, Daily Briefing, Member Dashboard, Work History

**UI**: No 순번 + 숫자 input (클릭 시 전체선택, 직접 타이핑)
**사용자 값 유지**: 재번호 없음, 입력한 값 그대로 저장

### 그룹 순서(`teamDisplayGroupOrders`) 영속화

그룹(FX팀, ✦FX AI팀 등)의 표시 순서는 `AppState.teamDisplayGroupOrders` (`{ '그룹명': order }`)에 저장됩니다.
개인 순서(`member.order`)는 `teamMembers` 배열에 포함돼 자동 저장되지만, **그룹 순서는 별도 필드**라 save/load 경로에 명시적으로 포함해야 합니다.

- **저장 4곳 + 로드 3곳** 모두에 `teamDisplayGroupOrders` 포함 필수 (`teamDisplayGroupColors` 바로 옆에 위치)
- 누락 시 `updateGroupOrder()`가 메모리엔 반영하지만 **새로고침 시 유실** → 그룹이 기본값 99로 밀려 맨 뒤로 정렬됨

**그룹이 개인보다 앞에 올 수 있음**: `getOrderedMembersAndGroups()`는 개인+그룹을 한 배열에 합쳐 순수 order 오름차순 정렬하므로, FX팀(order 1)을 정재화(order 2)보다 앞에 둘 수 있다. (단 Settings 팀원 관리 목록은 "개인 → 그룹" 섹션으로 분리 표시하는 편집 전용 레이아웃이라 거기선 그룹이 항상 하단)

**사고 이력 (2026-06-06)**: `teamDisplayGroupOrders`가 save/load 어디에도 없어 그룹 순서 변경이 매 새로고침 유실되던 버그. `storage.js` 저장 4곳·로드 3곳에 추가하여 해결.

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/team.js` | `updateGroupOrder()`, `updateMemberOrder()`, `getOrderedMembersAndGroups()` |
| `js/storage.js` | save 4곳 + load 3곳에 `teamDisplayGroupOrders` 포함 |

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

## Analytics 필터 시스템

Analytics 차트는 Gantt와 동일한 필터 바를 공유하며, `getFilteredTasks()`에서 모든 필터를 적용합니다.

**적용 필터**: Status, Project (`platform|project` 형식 지원), Service (`releaseMonth`), Planning, Assignee, Platform
**Overdue/Due 판정**: Done과 Bypass 모두 제외 (Bypass = 더 이상 진행하지 않는 Task)

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
- `js/analytics.js`: `renderMemberParticipation()`, `_bindMpTooltipEvents()`, `_applySliderFilter()`, `_bindTotalSlider()`
- CSS: `.ad-mp-header`, `.ad-mp-row` (5컬럼 그리드), `.ad-mp-task-group`, `.ad-mp-overdue-val`, `.ad-mp-md-val`, `.ad-mp-tooltip-popup`, `.ad-mp-tip-*`, `.ad-total-slider-*`

### FX팀 연간계획

Analytics 차트에서 연간계획을 독립 섹션으로 관리합니다.

**레이아웃**: `ad-mp-wrapper` flex row 안에 5개 독립 영역
```
달력 | Total | Monthly(프로젝트/작업 현황) | 팀원별 참여 현황 | FX팀 연간계획
```

**데이터**: `AppState.teamAnnualPlans` — 배열
```javascript
{ id, year, name, purpose, content, schedule, details: [{ quarter, title, items }] }
```

**연도 정렬**: `_sortedByYear()` — `parseInt(year)` 내림차순, 최신 연도가 위

**계획 편집 모달**: Dooray Sync 스타일, 드래그 지원 (`_setupModalDrag`), 복사 버튼
- 연도/업무명/목적/내용/적용일정/세부계획 입력
- 저장: `Storage.saveData()` + `Analytics.update()` (직접 참조, `this` 바인딩 이슈 방지)

**필드 뱃지**: 목적(파랑 `#E8F0FE`), 내용(초록 `#E6F4EA`), 일정(노랑 `#FEF7E0`)

**백업**: `AppState.teamAnnualPlans` — save/load/backup/restore/export/import/GitHub 7곳 포함

**구현 위치**:
- `js/analytics.js`: `_renderAnnualPlansSection()`, `_renderPlanCard()`, `_openPlanEditModal()`, `_bindAnnualPlansEvents()`, `_sortedByYear()`, `_setupModalDrag()`, `_copyPlanToClipboard()`
- CSS: `.ad-ap-section`, `.ad-ap-card`, `.ad-ap-field-*`, `.ad-ap-modal`

**주의**: `Storage.saveData()` 사용 (`StorageManager`가 아님)

### 월별 프로젝트/작업 현황 (Monthly)

Analytics 차트에서 월별 프로젝트 수와 작업 Task 수를 바 차트로 표시합니다.

**위치**: Total 오른쪽, 팀원별 참여 현황 왼쪽 (350px 고정)

**차트 구성**:
| 차트 | 기준 | 설명 |
|------|------|------|
| 월별 작업 현황 (위) | `workLogs` | 해당 월에 실제 작업 마크가 있는 Task 수 |
| 월별 프로젝트 현황 (아래) | `releaseMonth` | 해당 월의 unique `platform\|project` 프로젝트 수 |

**클릭**: 차트 영역 클릭 시 `App.openProjectFilterModal()` 호출
**현재월 강조**: 파란색 바 + 볼드 라벨

**구현 위치**:
- `js/analytics.js`: `calculateMonthlyStats()`, `renderMonthlyChart()` (Total 섹션 내)
- CSS: `.ad-monthly-section`, `.ad-monthly-chart`

## Task 고유 번호 (seq)

각 Task에 영구적인 고유 번호를 부여하여 식별/검색/검토에 활용합니다.

### 데이터
- `AppState.taskSeqCounter` — 다음 번호 카운터 (증가만, 재사용 안 함)
- `task.seq` — 각 Task의 고유 번호 (1부터 시작, 삭제해도 번호 유지)
- **안전장치**: `_ensureTaskSeq()`에서 counter가 maxTaskSeq + 50 초과 시 자동 리셋 (카운터 폭주 방지)

### 번호 부여 시점
| 위치 | 설명 |
|------|------|
| `tasks.js:createTask()` | 새 Task 생성 |
| `syncManager.js:addNewTasks()` | Sync 신규 Task 추가 시 (createTask 경유 또는 직접 부여) |
| `syncManager.js:addNewTasksWithRemoteInfo()` | 동일 |
| `main.js` bulk import | 일괄 등록 |
| `storage.js:_ensureTaskSeq()` | 기존 Task에 seq 없으면 createdAt 순 자동 부여 |

**주의**: `convertToTask()`는 seq를 부여하지 않음 (seq=0). 실제 AppState.tasks에 추가되는 시점에만 seq가 부여됨.
이유: Sync 시 대부분 Task가 중복이므로, convertToTask() 단계에서 seq를 부여하면 중복 Task가 seq를 소모하여 번호가 급격히 증가하는 문제 발생 (사고 이력 참조).

### seq 압축 (compaction)
`_ensureTaskSeq()`에서 빈 번호가 Task 수의 50% 이상이면 createdAt 순으로 1부터 자동 재정렬.
예: 139개 Task, max seq 686 → 1~139로 압축.

### 사고 이력 (2026-04-14)
`convertToTask()`가 호출될 때마다 `taskSeqCounter++` 실행 → Sync 시 중복 Task도 seq 소모 → 139개 Task인데 seq 686까지 도달 (547개 빈 번호).
추가로 `addNewTasks()`에서 `convertToTask()` + `createTask()` 이중 증가로 1 Task당 seq 2개 소모.
**교훈**: seq 부여는 실제 Task가 추가되는 시점에만 수행해야 함.

### 표시 위치
| 위치 | 형태 | 예시 |
|------|------|------|
| Gantt No 컬럼 | seq 번호 | `127` |
| Edit Task 모달 제목 | `Edit Task #seq` | `Edit Task #127` |
| Command Palette | `#seq 업무명` + 번호 검색 | `#127 로즈 애니메이션` |

### 저장
`taskSeqCounter`는 save/load/backup/restore/import 5곳 모두 포함

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/state.js` | `AppState.taskSeqCounter` |
| `js/tasks.js` | `createTask()` — seq 부여 |
| `js/dooray/syncManager.js` | `convertToTask()` — seq=0 (부여 안 함), `addNewTasks()`/`addNewTasksWithRemoteInfo()` — 실제 추가 시 seq 부여 |
| `js/storage.js` | `_ensureTaskSeq()` — seq 자동 부여 + 압축, save/load 5곳 |
| `js/views/gantt.js` | No 컬럼에 `task.seq` 표시 |
| `js/main.js` | Edit Task 제목, bulk import seq 부여 |
| `js/commandPalette.js` | `#seq` 검색 + 표시 |

## Edit Task 모달 동작

### Save 시 모달 유지
Edit Task에서 Save 클릭 시 모달이 닫히지 않고 저장 완료 안내를 표시합니다.
- Save 버튼이 초록색 "✓ 저장 완료"로 1.5초간 변경 후 원래 상태로 복귀
- Save 후 바로 Dooray 업로드 버튼을 클릭할 수 있음
- 새 Task 추가 시에는 기존처럼 모달이 닫힘
- CSS: `.btn-save-done` (초록 배경 #34a853)

### Project URL 열기 버튼
Project URL 입력 필드 오른쪽에 외부 링크 버튼으로 해당 URL을 브라우저에서 엽니다.
- `#openProjectUrlBtn` — `electronAPI.openExternal(url)` 호출
- CSS: `.url-input-with-btn` (flex), `.btn-open-url`

### Progress 표시
Edit Task 모달에서 `TaskManager.getEffectiveProgress(task)`를 사용하여 Gantt과 동일한 진행률을 표시합니다.
- 기존: `task.progress` (저장된 수동값) → workLogs가 있어도 0% 표시 가능
- 수정: `getEffectiveProgress()` → workLogs 기반 자동 계산값 표시 (Gantt과 일치)

### MD 자동 계산 (읽기 전용)
MD는 Start Date / End Date 기반으로 자동 계산되며 사용자가 직접 수정할 수 없습니다.

**정책**:
- `#manDays` 입력란: `type="text" readonly` — 편집 불가, 회색 배경 표시
- 날짜 변경 시 `calculateMD()` → `calculateWorkingDays()` 결과를 value에 즉시 반영
- Save 시: `calculateWorkingDays()` 우선, 날짜 없을 때만 input value 사용
- 모달 열 때: 저장된 `task.md` 대신 날짜에서 재계산한 값 표시

**로드 시 자동 교정** (`storage.js:_recalcMDFromDates()`):
- `loadData()` / `applyEnvironmentData()` 시 모든 Task의 MD를 날짜 기반으로 재계산
- 과거 버그(날짜 변경 시 MD 미갱신)로 잘못 저장된 값도 앱 시작 시 자동 교정

**사고 이력 (2026-04-20)**:
- #143 등 4개 Task에서 md=1(잘못됨)이 저장된 채 유지 — Edit Task 날짜 변경 시 MD value가 재계산되지 않던 구버그가 원인
- 공휴일(설날·크리스마스+신정)이 반영된 Task(#6, #58)도 있었으나, 시스템이 공휴일 미지원이므로 일관성을 위해 `getWorkingDays`(주말만 제외)로 통일

**CSS**: `#manDays[readonly]` — `background: var(--hover-color)`, `cursor: default`

### Edit Task 이력 로그 패널 (왼쪽 패널)
Task 편집 모달 왼쪽 패널에 Dooray URL 하단에 생성/수정 이력을 표시합니다.

**구조**:
```
[왼쪽 패널]
  Dooray URL
  Project URL
  기획 URL
  ─────────────────────────────
  이력 ▾                        ← #taskHistoryLog (접기/펼치기)
    생성: 2026-04-15 10:30
    수정: 2026-04-24 15:22
    ─────────────────
    2026-04-24 Dooray 갱신 ▶   ← 클릭 시 상세 펼치기
      startDate: 04-01 → 04-10
      endDate:   04-05 → 04-20
```

**기능**:
- **Created/Updated 타임스탬프**: 이전 Footer의 타임스탬프를 대체하여 왼쪽 패널에 표시
- **changeHistory 목록**: 최근 5건 (역순), 각 행 클릭 → from→to 상세 접기/펼치기
- **접기/펼치기**: `.thl-header` 클릭 또는 `▾` 토글로 전체 패널 접기
- **조건부 표시**: Edit Task에서만 표시 (새 Task에서는 숨김)

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `index.html` | `#taskHistoryLog` > `.thl-header` + `.thl-body` > `#thlTimestamps` + `#thlChanges` |
| `js/main.js` | `_renderTaskHistoryLog(task)` — 타임스탬프 + changeHistory 렌더링, `_renderChangeHistory()` — 항상 stub 숨김 유지 |
| `styles.css` | `.task-history-log`, `.thl-*`, `.thl-ch-row` (클릭 가능), `.thl-ch-detail` (펼침 영역, 보라 좌측 바), `.thl-detail-from` (빨강 취소선), `.thl-detail-to` (파랑) |

**주의**: `changeHistoryRow` (우측 패널 Notes/Progress 사이에 위치)는 `display:none` 숨김 stub으로 유지 — `_renderChangeHistory()`에서 절대 `display: ''`로 변경 금지

### Edit Task 모달 입력 필드 클릭 불가 방지
모달을 열었을 때 입력 필드가 즉시 클릭되지 않는 문제를 2가지 원인으로 수정:

1. **CSS `pointer-events` 누락**: `.modal { pointer-events: none }`인데 `.modal.show`에 `auto` 미복원
   - `styles.css`: `.modal.show { pointer-events: auto }` 추가
2. **`_fetchPlanningUrlFromDooray` IPC 즉시 호출**: 모달 열자마자 Dooray API 호출 → Electron 렌더러 마우스 이벤트 블로킹
   - `main.js`: 즉시 호출 → `setTimeout(..., 300)` 지연으로 변경
3. **`setTimeout(focus)` 딜레이 부족**: `50ms` → `150ms` (레이아웃 완료 전 focus 시도 방지)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/main.js` | `_showSaveConfirmation()`, `handleTaskSubmit()` Edit 분기, URL 열기 이벤트, `calculateMD()` value 갱신, `getEffectiveProgress()` 표시, `_fetchPlanningUrlFromDooray()` 자동 조회 (300ms 지연), `_renderTaskHistoryLog()` 이력 로그, `_renderChangeHistory()` stub 숨김 유지 |
| `js/storage.js` | `_recalcMDFromDates()` — 로드 시 날짜 기반 MD 자동 교정, `loadData()` + `applyEnvironmentData()` 두 경로에서 호출 |
| `index.html` | `#manDays`: `type="text" readonly`, `.url-input-with-btn` > `#projectUrl` + `#openProjectUrlBtn`, `#planningUrlRow` > `#planningUrl` + `#openPlanningUrlBtn`, `#taskHistoryLog` (왼쪽 패널 이력 로그), `#changeHistoryRow` (숨김 stub) |
| `styles.css` | `#manDays[readonly]`, `.btn-save-done`, `.url-input-with-btn`, `.btn-open-url`, `.planning-title-display`, `.modal.show { pointer-events: auto }`, `.task-history-log`, `.thl-*` |

## GitHub Backup (Push / Pull)

Backup 모달에서 GitHub 저장소로 데이터를 업로드/다운로드하는 기능입니다.

### UI 구성
```
[GitHub 라벨] [↑ Push] [↓ Pull]
```
- **GitHub 라벨**: 테두리 없는 텍스트 (`backup-github-label`)
- **Push/Pull 버튼**: `backup-btn-compact` 스타일

### 버튼 상태 표시
| 상태 | Push | Pull |
|------|------|------|
| 대기 | `↑ Push` | `↓ Pull` |
| 진행 중 | `<spinner> Push 중...` | `<spinner> Pull 중...` |
| 완료 | `✓ Push 완료` (초록, `.gh-success`) | `✓ Pull 완료` (초록) |
| 변경 없음 | `- 변경 없음` (회색, `.gh-skip`) | — |
| 취소 | — | `- 취소됨` (회색) |

**자동 복귀**: 완료/변경없음/취소 상태 2.5초 후 원래 상태로 복귀 (`_ghBtnReset()`)

### Push (업로드)
- `electronAPI.githubUpload()` → `electron-main.js:github-upload` IPC
- Git blob SHA 비교 → 동일하면 스킵
- GitHub Contents API PUT으로 업로드

### Pull (다운로드)
- `electronAPI.githubDownload()` → `electron-main.js:github-download` IPC
- GitHub Contents API GET → base64 디코딩 → JSON 파싱
- confirm 후 `Storage.applyEnvironmentData(data)` → 데이터 교체

### Backup History 라벨
| type | 라벨 |
|------|------|
| `github` | `GitHub ↑` |
| `github-download` | `GitHub ↓` |

### 설정
`config/github.json` — `{ token, owner, repo, file }` (file 기본값: `Teamplay_latest.json`)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `electron-main.js` | `github-upload`, `github-download` IPC 핸들러 |
| `electron-preload.js` | `githubUpload()`, `githubDownload()` 브릿지 |
| `js/main.js` | `uploadToGithub()`, `downloadFromGithub()`, `_ghBtnReset()` |
| `index.html` | `.backup-github-group` > `#backupGithubBtn` + `#backupGithubDownloadBtn` |
| `styles.css` | `.backup-github-group`, `.gh-success`, `.gh-skip` |

## 데이터 보호

Gantt 차트 데이터 소실 방지를 위한 방어 장치:
- `saveData()`: AppState.tasks가 비어있으면 저장 스킵 + try-catch
- `visibilitychange` 이벤트: 화면 복귀 시 데이터 무결성 체크
- `cleanOrphanedData()`: tasks + teamTasks 양쪽 ID 확인 후 고아 정리 (workLogs/dailyNotes 보호)

> **참고**: workLogs/dailyNotes 보호에 대한 상세 규칙은 상단 "절대 보호 데이터" 섹션 참조

### saveData() guard 우회: saveAutomationFlags()

`saveData()`의 tasks-empty guard는 Gantt 데이터 소실 방지용으로 설계되었으나, automation 설정(자동 백업 스케줄 등)도 함께 저장을 막는 부작용이 있다.

**해결책**: `Storage.saveAutomationFlags()` — tasks 유무와 무관하게 `AppState.automationFlags`만 선택 저장
```javascript
// 이렇게 하면 tasks empty guard에 막힘:
Storage.saveData();

// automation 설정만 저장할 때는 이것을 사용:
Storage.saveAutomationFlags();
```
**적용 위치**: `_saveBackupSchedules()`, backup enabled 토글 핸들러
**`saveData()` 내부**: 이른 반환 전에 `this.saveAutomationFlags()` 호출하여 automation 설정은 항상 보존

## Task 삭제 (Blocklist 방식)

Gantt에서 Task 삭제 시 Dooray 업무는 수동으로 삭제합니다 (Dooray REST API는 업무 DELETE를 지원하지 않음).

### 동작
- Dooray URL이 있는 Task 삭제 시 confirm 다이얼로그
- **확인**: Gantt 삭제 + `AppState.deletedPostIds`에 postId 추가 (Sync 재생성 차단)
- **취소**: Gantt에서만 삭제 (Sync 시 다시 불러올 수 있음)

### Sync 차단
- `AppState.deletedPostIds` — 삭제된 업무의 postId 배열
- `syncManager.js:addNewTasksWithRemoteInfo()`에서 매칭 시 스킵
- save/load/backup/restore/import 모든 경로에 포함

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/main.js` | `handleDeleteTask()` — blocklist 등록 + Gantt 삭제 |
| `js/dooray/syncManager.js` | `addNewTasksWithRemoteInfo()` — deletedPostIds 체크 |
| `js/storage.js` | save/load 경로 |

## Debug Mode (콘솔 로그 제어)

개발 디버깅용 `console.log`/`console.info`를 평소에는 숨기고 필요할 때만 켜는 기능입니다.

- **기본 상태**: 로그 숨김 (앱 시작 시 콘솔 깨끗)
- **켜기**: 브라우저 콘솔에서 `debug(true)` 실행
- **끄기**: `debug(false)` 실행
- `console.warn`과 `console.error`는 항상 표시 (실제 문제 감지)
- 구현: `state.js` 최상단 IIFE — 원본 `console.log`/`console.info`를 저장 후 `_debugMode` 플래그로 제어

## Dooray API 응답 상태 체크

`electron-main.js`의 `dooray-api` IPC 핸들러는 HTTP 4xx/5xx 응답도 `success: true`로 반환합니다.
따라서 모든 Dooray API 호출 후 HTTP 상태 코드를 추가로 체크해야 합니다.

### 체크 패턴
```javascript
if (response?.status && (response.status < 200 || response.status >= 300)) {
    throw new Error(`HTTP ${response.status}`);
}
```

### 적용 위치
| 파일 | 함수 |
|------|------|
| `js/dooray/syncManager.js` | `executePushToDooray()` |
| `js/dooray/weeklyReportGenerator.js` | `updatePost()` |
| `js/automationPanel.js` | `createTeamplayPost()`, `_routineStepArtTeam()`, `_routineStepArtComment()` |

## 키보드 단축키

| 키 | 기능 |
|---|---|
| 1-8 | 뷰 전환 |
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
| Shift+R | Report 프로젝트별 묶기 (Report 패널 열려있을 때) |
| L | Task Log 패널 |
| W | Work Sync 패널 |
| J | Sync 패널 |
| K | Weekly 패널 |
| H | Work History |
| I | QA Register |
| A | Automation 패널 |
| V | 팀 업무 가이드 |
| U | 중복 검사 패널 |
| B | Backup 모달 |
| E | Excel Export |
| S | 환경 저장 |
| Y | Daily Briefing |
| Ctrl+F | 전체화면 토글 |
| Ctrl+P | Command Palette 열기 |
| Ctrl++/= | 앱 확대 |
| Ctrl+- | 앱 축소 |
| Ctrl+0 | 앱 원래 크기 |
| Ctrl+Z | 실행 취소 |
| Ctrl+Y | 다시 실행 |
| ` | 메뉴 열기/닫기 |
| Esc | 모달 닫기 |

## 단축키 도움 버튼 (?)

오른쪽 하단 플로팅 카운트다운 옆에 독립 배치된 `?` 버튼으로, hover 시 단축키 목록 툴팁을 표시합니다.

**위치**: `position: fixed; bottom: 20px; right: 12px` (플로팅창 `right: 46px` 옆)
**크기**: 26px 원형, `z-index: 10000`
**툴팁**: `z-index: 10001`, 아래→위 방향 (`bottom: 100%`), 420px 너비
**구현**: `index.html` (hookPollingStatus 바깥 독립 div), `styles.css` (`.shortcuts-help`, `.btn-shortcuts-help`, `.shortcuts-tooltip`)

## QA 업무 등록 (QA Register)

QA팀 Dooray 업무 URL을 입력하면 FX팀 업무로 자동 변환하여 Dooray에 새 업무를 등록하는 기능입니다.

### 진입점
- 단축키: `I` (modifier 가드: `!e.ctrlKey && !e.shiftKey && !e.altKey`)
- 사이드 패널 → QA 업무 등록

### 동작 흐름 (단건)
```
URL 입력 → 조회 → QA 제목 파싱 (플랫폼/월/담당자 자동 추정) → 미리보기 확인/수정 → Dooray 새 업무 등록
```

### 자동 추정
| 항목 | 추정 방법 |
|------|----------|
| 플랫폼 | QA 제목 태그에서 매칭 (`_getPlatformMap()`) |
| 점검월 | 태그의 `N월` 패턴 추출 |
| 담당자 | CC의 FX 팀원 자동 매칭 |

### FX 업무 형식
- **제목**: `𝗙𝗫 [플랫폼] N월 업데이트 [작업] 내용`
- **본문**: 프로젝트 정보 (카테고리/조직/일정/점검월/위키) + QA 원본 링크

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/qaRegister.js` | QARegister 모듈 (조회/파싱/등록) |
| `index.html` | `#qaRegisterModal` HTML |
| `js/main.js` | 이벤트 바인딩 + I 단축키 + Escape |
| `styles.css` | `.modal-qa-register`, `.qar-*` |

## Wiki Panel (위키 자동 생성/업데이트)

Planning 차트의 활성 프로젝트를 자동 스캔하여 Dooray 위키 페이지를 생성/업데이트하는 사이드 패널입니다.

### 진입점
- 사이드 패널 → "Wiki" 버튼 (`#wikiPanelBtn`)
- Report/Weekly와 동일한 사이드 패널 패턴

### 핵심 기능
| 기능 | 설명 |
|------|------|
| 스캔 | Gantt Task를 `platform\|project`로 그룹핑, wikiUrl 유무로 등록/미등록 판별 |
| 수동 추가 | 플랫폼 + 프로젝트명 입력으로 목록에 추가 |
| 미리보기 | 프로젝트 선택 → Dooray Task 정보 조회 → 마크다운 본문 생성 |
| 복사 | 미리보기 마크다운을 클립보드에 복사 |
| 위키 생성 | 체크된 미등록 프로젝트를 Dooray Wiki API로 페이지 생성 |
| 개별 업데이트 | 등록된 프로젝트 선택 시 미리보기 헤더에 업데이트 버튼 표시 |
| 일괄 업데이트 | 체크된 등록 프로젝트의 제목+본문을 최신 형식으로 PUT 업데이트 |

### 프로젝트 선택/체크
- **기본 선택 해제**: 스캔 시 모든 프로젝트가 체크 해제 상태로 시작
- **모든 프로젝트에 체크박스** 표시 (등록/미등록 모두)
- **전체 선택**: `#wikiSelectAll` 체크박스 (indeterminate 지원)
- **미등록 선택**: `#wikiSelectUnregistered` — 미등록 프로젝트만 선택
- **등록됨 선택**: `#wikiSelectRegistered` — 등록된 프로젝트만 선택
- **전체 해제**: `#wikiDeselectAll` 버튼
- **프로젝트 클릭 토글**: 같은 프로젝트 다시 클릭 시 선택 해제
- **Gantt 하이라이트**: 프로젝트 선택 시 flash 효과 (1초, `--task-log-highlight-bg` 색상, inline style)

### 프로젝트 상태 뱃지
| 뱃지 | 색상 | 의미 |
|------|------|------|
| `등록됨` | 초록 (#188038) | wikiUrl이 있는 프로젝트 |
| `미등록` | 주황 (#E65100) | wikiUrl이 없는 프로젝트 |
| `수동` | 파랑 (#1A73E8) | 수동 추가된 프로젝트 |

### 위키 본문 구조
```markdown
## FX 정재화, 김보람

### 카테고리1
[클래식FX팀-업무관리/575 𝗙𝗫 제목](dooray://orgId/tasks/postId)

### 카테고리2
[클래식FX팀-업무관리/576 𝗙𝗫 제목2](dooray://orgId/tasks/postId2)

## 기획 홍길동

[기획제목](dooray://orgId/tasks/postId)

## UI

## 원화

## 개발
```

**카테고리 그룹핑**: Task의 `category` 필드로 `### 카테고리명` 하위에 정리 (1개뿐이면 헤더 생략)
**URL 없는 Task 제외**: Dooray API 조회 결과가 없는 Task는 위키 본문에서 제외
**섹션 순서**: FX → 기획 → UI → 원화 → 개발
**기획 링크**: `_parsePlanningLink()` — 본문에서 `기획: [text](dooray://...)` regex 추출
**위키 제목**: `[플랫폼] 프로젝트` (월 접미사 없음 — 월 폴더에 이미 포함)
**링크 중복 방지**: `taskNumber`에 `/` 포함 시 projectCode 미접두

### 미리보기
- `&#91;`/`&#93;` → `[`/`]` 디코딩하여 표시 (실제 마크다운 출력은 이스케이프 유지)
- 시스템 폰트 상속 (`font-family: inherit`)

### 월 폴더 자동 생성
- `🔹이펙트 (2026)` 하위에 `└─ N월` 폴더 확인/생성
- 캐싱: `_monthFolders[monthKey]` → 한 번 조회 후 재사용

### 설정 (localStorage)
| 키 | 기본값 | 설명 |
|---|---|---|
| `wikiProjectId` | `4028352443299472148` | Wiki 프로젝트 ID |
| `wikiRootPageId` | `4214714651744127914` | 🔹이펙트 루트 페이지 ID |
| `defaultProjectId` | `1387695619080878080` | 기본 Dooray 조직 ID |

### Wiki REST API 엔드포인트
| 작업 | Method | Endpoint |
|------|--------|----------|
| 하위 페이지 조회 | GET | `/wiki/v1/wikis/{wikiId}/pages?parentPageId=Y` |
| 페이지 생성 | POST | `/wiki/v1/wikis/{wikiId}/pages` body: `{ wikiId, parentPageId, subject, body: { mimeType, content } }` |
| 페이지 업데이트 | PUT | `/wiki/v1/wikis/{wikiId}/pages/{pageId}` body: `{ subject, body: { mimeType, content } }` |

### 기획 담당자 매칭
Placeholder에서 3단계 정확 매칭으로 planner 검색 (부분 매칭은 오매칭 위험이 높아 제거)

1. platform + project 정확 매칭
2. project + planning 매칭
3. project만 매칭

Planning 차트 팝오버(`planningOverview.js`)와 Wiki 패널(`wikiPanel.js`) 동일 로직 적용

### 기획 링크 소스 우선순위
Wiki 생성 시 기획 링크는 다음 순서로 결정:
1. **Placeholder URL** (Planning 차트에서 편집) → `_resolvePlanningLinkTitle()`로 Dooray API 제목 조회 + `dooray://` 변환
2. **Dooray 본문 파싱** (`_parsePlanningLink()`) — `기획: [text](dooray://...)` 패턴
3. **planningTitle** 텍스트만 (링크 없음)

미리보기/위키 생성/일괄 업데이트 3곳 모두에서 resolve 호출

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/wikiPanel.js` | WikiPanel 모듈 전체 (스캔/미리보기/생성/업데이트) |
| `index.html` | `#wikiPanel` HTML + 사이드 패널 `#wikiPanelBtn` |
| `js/main.js` | 이벤트 바인딩 + Escape + mousedown 위임 |
| `styles.css` | `.wiki-panel`, `.wp-*` 스타일 |

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

### 카테고리 그룹 헤더
카테고리가 2개 이상일 때 Gantt 스타일 그룹 헤더 행을 표시합니다.

**헤더 내용**: 카테고리명 + Task 수 + 총 MD + 집약 바 (opacity 0.4)
**접기/펼치기**: 헤더 클릭 → 해당 카테고리 토글, `G` 키 전체 접기/펼치기
**아이콘**: No. 셀에 `fa-chevron-right`/`fa-chevron-down` (Gantt과 동일)
**배경색**: 카테고리 색상의 `Utils.lightenColor(color, 0.85)` (CSS 변수 `--team-gh-bg`)
**상태**: `AppState._teamCollapsedGroups` (런타임 Set, 재시작 시 초기화)

**주의**:
- `currentView`는 `'teamGantt'` (`'team'` 아님) — G키 등 분기 시 주의
- 인라인 `position:relative` 사용 금지 — sticky의 `left` 값을 오버라이드함
- 그룹 헤더 td 배경: sticky `background:#fff`보다 specificity 높아야 함 → `!important`

**우클릭 메뉴**: 그룹 헤더 우클릭 → 이름 변경 + 색상 변경 통합 컨텍스트 메뉴
- 이름 변경: Enter 또는 "적용" 버튼으로 확정, 하위 Task `group` + 색상/접힘 마이그레이션
- 색상 변경: color input 즉시 반영 + 하위 Task `color` 동기화
- "적용" 버튼: 메뉴 하단 파란 버튼, Enter과 동일 동작 (이름+색상 적용 후 메뉴 닫힘)
- 외부 클릭: 메뉴만 닫힘 (변경 미적용 — 명시적 확정 필요)

**자동 색상 배정**: `_autoAssignGroupColors()` — 새 카테고리에 15색 팔레트(`GROUP_COLOR_PALETTE`)에서 미사용 색상 자동 배정

**트리 커넥터**: Gantt Platform 컬럼과 동일한 세로선+가로 가지
- `.team-tree` / `.team-tree-last` — 통일 그레이 `#B0BEC5`
- 그룹 내 Task에서 카테고리 텍스트 숨기고 트리 라인만 표시

**구현 위치**:
- 뷰: `js/views/teamGantt.js` — `renderTasks()` 그룹 헤더 + 트리 커넥터, `showGroupContextMenu()`, `_autoAssignGroupColors()`
- 데이터: `AppState.teamTasks`, `AppState.teamGroupColors`, `AppState._teamCollapsedGroups`
- G키: `main.js:_toggleAllTeamGroups()`
- 색상 관리: `main.js:renderTeamGroupColorList()`, `updateTeamGroupColor()`
- CSS: `.team-group-header-row`, `.team-group-toggle-icon`, `.team-group-header-group`, `.team-group-summary`, `.team-group-context-menu`, `.tgcm-*`, `.team-tree`, `.team-tree-last`

### Add/Edit Team Task 모달

Team Task 추가/편집 모달 (`#teamTaskModal`, `.modal-content.modal-md`)

**모달 너비**: 576px (`modal-md` max-width — 기존 480px에서 +20% 확장)

**폼 필드**:
| 필드 | 설명 |
|------|------|
| Task | 업무명 (필수) |
| Start/End Date | 기간 (필수) |
| 카테고리 | `task.group` — 기존 그룹 datalist 자동완성 |
| Tag | `task.tag` — 기존 태그 datalist 자동완성 |
| Bar Color | `task.color` — 색상 피커 |
| URL | `task.urls[]` — 복수 URL (아래 참조) |
| Notes | `task.note` |

**URL 관리** (`task.urls: {label, url}[]`):
- "URL 추가" 버튼 (`#teamTaskAddUrlBtn`)으로 행 추가 (제한 없음)
- 각 행: **라벨 입력 (110px)** + URL 입력 + 🔗 열기 버튼 + ✕ 삭제 버튼
- 라벨: 링크 설명 (예: `기획서`, `디자인 시안`, `참고 자료`)
- 열기 버튼: URL 입력 시 활성화, `electronAPI.openExternal()` 호출
  - `http`로 시작하지 않으면 `https://` 자동 접두사 추가
- `_addTeamTaskUrlRow(urlOrObj)`: 행 동적 생성 — `string`(구 형식) 또는 `{label, url}` 객체 모두 지원 (하위 호환)
- `_getTeamTaskUrls()`: `{label, url}[]` 반환 (url 비어있는 행 자동 제외)
- 저장: `task.urls` 배열 (`{label, url}` 객체 배열)

**Team Gantt 날짜 셀 더블클릭**:
- 날짜 셀 단일 클릭: Work 마크 토글 (기존 동일)
- 날짜 셀 **더블클릭**: Edit Team Task 팝업 열기 (URL/라벨 포함 Task 전체 편집)
- 구현: `handleTeamGanttCellDblClick()` → `openEditTeamTaskModal(taskId)`

**startDate 변경 시 workLogs/dailyNotes 자동 이동** (`saveTeamTask()`):
- 사용자가 Edit Team Task에서 startDate를 변경하면 `deltaDays = newStart - oldStart` 만큼 이 Task의 workLogs(점)와 dailyNotes를 일괄 shift
- **격리 보장**: `AppState.workLogs[task.id]`와 `${task.id}_` prefix로 필터링 — 다른 Task의 데이터는 절대 건드리지 않음
- 의도: 작업 마크가 Task의 새 날짜 범위로 따라 이동 (점은 작업 진행을 나타내므로 Task가 다른 날로 옮겨가면 함께 이동해야 함)
- `oldStartDate === startDate`면 shift 안 함 (날짜 변경 없을 때 안전)

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `index.html` | `#teamTaskUrlList`, `#teamTaskAddUrlBtn` |
| `js/main.js` | `_addTeamTaskUrlRow()`, `_updateTeamTaskOpenBtn()`, `_getTeamTaskUrls()`, `handleTeamGanttCellDblClick()` |
| `styles.css` | `.tt-url-list`, `.tt-url-row`, `.tt-url-label-input`, `.tt-url-input`, `.tt-url-open-btn`, `.tt-url-remove-btn`, `.tt-url-add-btn` |

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
- 검색 대상: 플랫폼, 프로젝트, Task(`task.task`), Task명(`task.name`), 담당자
- **결과 순서**: Project Group 먼저 (최대 5개) → Task (최대 20개)
- **label**: `task.name` 우선 사용 (`task.task`는 project명과 동일할 수 있음)
- **detail 2단 구성**: 경로(`.cmd-item-path`, #555 진하게) + 부가정보(`.cmd-item-extra`, #aaa 연하게)
- **부가정보**: 담당자 · 진행률 · 날짜범위(MM-DD~MM-DD)
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

### 사이드 패널 메뉴 카테고리 구조

햄버거 메뉴 항목은 6개 기능별 카테고리로 그룹화됩니다. 단순 구분선 대신 작은 회색 대문자 라벨(`.side-panel-category`)이 그룹 위에 표시되어 어떤 카테고리인지 명시적으로 보입니다.

| 카테고리 | 항목 | 의미 |
|---------|------|------|
| **설정** | Project Filter, Settings, Chart Layout, Appearance | 차트와 앱 외형/필터 구성 |
| **Dooray 연동** | Dooray, 두레이 새 업무, QA 등록, Automation | Dooray API와 직접 통신 (Automation은 Dooray Sync 스케줄링) |
| **데이터 입출력** | Bulk Import, Plan Import, Excel Export | 외부 파일 ↔ Gantt 데이터 변환 |
| **보고 · 평가** | Work History, Member Dashboard | 팀원/기간 기준 데이터 추출 |
| **참고** | Wiki, Guide | 읽기 전용 문서 (외부 위키 + 내부 가이드) |
| **데이터 점검** | 중복 검사, Clear All | 데이터 정합성 점검 + 전체 초기화 |

**CSS 스타일** (`.side-panel-category`):
- font-size 10px, font-weight 600, color #9aa0a6, uppercase, letter-spacing 0.6px
- 그룹 위에 `border-top: 1px solid var(--border-color)`로 구분 (첫 카테고리는 border 없음)
- padding-top 6~10px로 항목과 시각 분리

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `index.html` | `.side-panel-body` 내 `.side-panel-category` 6개 + 항목 배치 |
| `styles.css` | `.side-panel-category` 스타일 |

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

## 중복 검사 패널 (DuplicateUrlPanel)

Gantt 차트에서 중복 URL 및 중복 제목 Task를 검출하고 관리하는 패널입니다.

**단축키**: `U` (토글)
**진입점**: 사이드 패널 → "중복 검사" (`#duplicateUrlBtn`)
**모듈**: `js/duplicateUrl.js`

### 탭 구성
| 탭 | 검출 기준 | 설명 |
|---|---|---|
| URL | Post ID 일치 | 동일 Dooray 업무를 가리키는 Task들 |
| 제목 | `task.name` 완전 일치 | 같은 이름이지만 다른 URL을 가진 Task들 (URL 중복은 제외) |

### 제목 중복 확인 완료 (dismiss)
확인 후 문제없는 제목 중복 그룹을 숨길 수 있습니다.

**데이터**: `AppState.dismissedDuplicateTitles` — `[{ title: "...", taskIds: ["id1", "id2"] }]`

**동작**:
- ✓ 버튼: 그룹을 "확인 완료"로 표시 → title + taskIds 저장
- ↩ 버튼: 확인 완료 해제 → 다시 활성 목록으로 복귀
- **새 Task 감지**: 같은 제목으로 새 Task가 추가되면 새 taskId가 dismissed set에 없으므로 다시 표시됨
- **카운트**: 탭 뱃지 숫자에서 dismissed 그룹은 제외

**구현 위치**:
| 파일 | 역할 |
|------|------|
| `js/duplicateUrl.js` | `isDismissedTitleGroup()`, `dismissTitleGroup()`, `restoreTitleGroup()`, `_renderTitleGroup()` |
| `js/state.js` | `AppState.dismissedDuplicateTitles` |
| `js/storage.js` | save/load/backup/restore 모든 경로 |
| `styles.css` | `.dup-dismiss-btn`, `.dup-restore-btn`, `.dup-group-dismissed`, `.dup-dismissed-section` |

### Gantt 네비게이션
패널에서 Task 클릭 시 Gantt 차트에서 해당 Task로 이동 + 하이라이트

- `openTask()` → `ReportView.navigateToGanttTask(taskId)` 재사용
- Hide Done/Bypass 자동 해제, 그룹 자동 펼침, 스크롤 + flash 효과

### 제목 중복 레이아웃
단일 행 flex: Platform → Project → Task(flex:1) → Assignee → Progress → #ID → 삭제

CSS: `.dup-title-item`(flex row), `.dup-title-platform`, `.dup-title-project`, `.dup-title-name`, `.dup-title-assignee`, `.dup-title-progress`, `.dup-title-id`

### Sync 중복 경고 뱃지
Sync 새 업무 목록에서 제목 중복을 뱃지로 표시

| 뱃지 | 색상 | 조건 |
|------|------|------|
| `동일제목 N` | 주황 (`.sync-dup-self`) | Sync 목록 내 같은 제목 N개 |
| `Gantt 중복` | 빨강 (`.sync-dup-gantt`) | 기존 Gantt Task와 같은 제목 |
| `신규` | 초록 (`.sync-badge-new`) | 중복 없는 새 업무 |

**구현 위치**: `main.js:showNewTasks()`

### Sync 완료 업무 상태 뱃지
완료 업무 목록에서 postId(URL) 기반으로 Gantt Task를 매칭하여 현재 상태를 뱃지로 표시

| 뱃지 | 색상 | 조건 |
|------|------|------|
| `이미 완료` | 회색 (`.sync-status-already-done`) | Gantt Task가 이미 Done/100% |
| `완료 대상 N%` | 파랑 (`.sync-status-target`) | Gantt Task 매칭됨, 아직 미완료 (현재 진행률 표시) |
| `미매칭` | 주황 (`.sync-status-nomatch`) | Gantt에 해당 URL의 Task 없음 |

**매칭 방식**: 제목 비교가 아닌 `DooraySyncManager.extractPostId()` 기반 URL 매칭
**구현 위치**: `main.js:showCompletedTasks()`

### Sync Work 마크 상태 뱃지
Work 마크 목록에서 postId(URL) + 날짜 기반으로 기존 workLog 존재 여부를 뱃지로 표시

| 뱃지 | 색상 | 조건 |
|------|------|------|
| `신규` | 초록 (`.sync-wm-new`) | 매칭 Task에 해당 날짜 Work 로그 없음 (새로 추가됨) |
| `적용됨` | 회색 (`.sync-wm-existing`) | 매칭 Task에 해당 날짜 Work 로그 이미 존재 |
| `미매칭` | 주황 (`.sync-status-nomatch`) | Gantt에 해당 URL의 Task 없음 |

**매칭 방식**: `extractPostId()` + `AppState.workLogs[taskId][dateStr]` 존재 여부 체크
**구현 위치**: `main.js:showWorkMarks()`

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
- **배경**: 배경색 없음 (`#fff`) — 라인만 표시 (Team 차트 트리와 동일 패턴)

### 상태별 배경 오버라이드
- **기본/Placeholder**: `background: #fff !important`
- **Hover**: `background: #F5F5F5 !important` (행 hover와 통일)
- **Selected**: `background: #E8F0FE !important` (선택 색과 통일)
- **Completed**: `background: #fff !important; opacity: 0.7`
- **Highlight/Flash**: 기존 유지 (노란색/파란색 inline style)

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

### Daily Notes 툴팁 렌더링

`data-note` 속성 값을 `showNoteTooltip()`에서 파싱하여 HTML로 렌더링합니다.

**노트 저장 형식** (Sync 시 `noteCollector` 패턴):
- 작성자명 + `\n` + 세부 내용 (각 담당자별)
- 담당자 간 구분자: `\u2015` (U+2015 HORIZONTAL BAR)
- 예: `"정재화\nTask 내용1\n\u2015\n김보람\nTask 내용2"`

**Sync 시 처리** (`syncManager.js:applyWorkMarks`, `applyWorkMarksForTask`):
- Dooray 마크다운 이스케이프 제거: `cleanedContent.replace(/\\([_*\`[\]()~>#+=|{}.!\-])/g, '$1')`
  - `fsx\_shine` → `fsx_shine` 변환
- 작성자 접두사: `mark.author + '\n'` 를 cleanedContent 앞에 추가
- 같은 `noteKey` 내용 일괄 수집 후 `\n\u2015\n` 으로 join하여 replace (append 금지)

**툴팁 렌더링** (`main.js:showNoteTooltip`):
- `tooltip.innerHTML` 사용 (개행 + 구분선 표현)
- 각 줄을 `<span>`으로 래핑, `\u2015` 줄은 `<hr class="note-sep">` 로 변환
- `<br>` + `<hr>` 중복 제거 처리

**기존 데이터 마이그레이션** (`storage.js:loadData`):
- 로드 시 모든 `AppState.dailyNotes` 값에 백슬래시 이스케이프 제거 적용
- 조건: `typeof v === 'string' && v.includes('\\')`
- `applyEnvironmentData()` (환경 복원/Import) 경로도 동일하게 적용

**CSS**: `.note-tooltip hr.note-sep { border-top: 1px solid #E0E0E0; margin: 5px 0; }`

### 구현 위치
- `styles.css`: `td.col-day.today::after`, `th.col-day.today::after`, `.group-header-day.today`, `.has-note::before`, `.note-tooltip hr.note-sep`
- `js/dooray/syncManager.js`: `applyWorkMarks()`, `applyWorkMarksForTask()` — noteCollector 패턴
- `js/main.js`: `showNoteTooltip()` — innerHTML + hr 변환
- `js/storage.js`: `loadData()`, `applyEnvironmentData()` — 백슬래시 마이그레이션

## 플로팅 메뉴 (Hook Polling + 시계)

하단 오른쪽 플로팅 메뉴에 Dooray 댓글 감시 타이머와 현재 시각을 표시합니다.

**배치 순서 (왼쪽→오른쪽)**: `[Sync] [Backup] [🔔 Hook 타이머 ⚙ | 날짜 시간] [?]`
- Sync: 가장 왼쪽 (Backup 왼쪽에 동적 배치)
- Backup: Hook 왼쪽에 배치 (초록 pill)
- Hook: 고정 right: 46px

### Hook Polling (Dooray 댓글 감시)

팀플레이 업무의 댓글/본문 변경을 감지하여 **Dooray 메신저에 봇 알림**을 전송합니다.

> **Auto Sync와의 차이**: Hook Polling은 변경 **알림만** 전송하고 Gantt 데이터를 변경하지 않습니다.
> Auto Sync(`automationPanel.js`)는 댓글을 **파싱하여 Gantt에 실제 반영**합니다 (Task/Work 마크 추가).

**동작 흐름**:
```
카운트다운 → 0 → pollForChanges()
→ Dooray API로 팀플레이 업무 댓글/본문 조회
→ 이전 스냅샷과 MD5 해시 비교
→ 변경 감지 시 → analyzeChanges() (새 댓글/수정 댓글/본문 변경 분석)
→ sendDoorayHookNotification() → Dooray Incoming Webhook으로 봇 메시지 전송
```

**비교표**:
| | Hook Polling | Auto Sync (Automation) |
|---|---|---|
| 실행 위치 | `electron-main.js` (메인 프로세스) | `automationPanel.js` (렌더러) |
| 감시 대상 | 팀플레이 댓글/본문 해시 변경 | 팀플레이 댓글 내용 파싱 |
| 결과 | Dooray 메신저 봇 알림 전송 | Gantt Task/Work 마크 실제 반영 |
| Gantt 변경 | 없음 | 있음 |
| 설정 | `config/dooray-hook.json` | `AppState.automationFlags` |

**UI 조작**:
- 🔔 클릭: 폴링 On/Off 토글
- ⚙ 클릭: 간격(분) 변경 (인라인 입력)
- 우클릭: 5초 퀵타이머 (즉시 체크)

**설정 파일**: `config/dooray-hook.json`
```json
{
    "enabled": true,
    "hookUrl": "https://hook.dooray.com/...",
    "botName": "FX Teamplay",
    "polling": {
        "enabled": true,
        "intervalMinutes": 5,
        "projectId": "4028352443299472148",
        "titleKeyword": "팀플레이"
    }
}
```

**상태 저장**: `data/dooray-hook-state.json` — 업무별 해시 + 스냅샷 (변경 감지용)

#### 알림 메시지 형식

봇 이름은 **`FX Teamplay`** (config `botName`). 변경 카드는 **작성자별로 묶어** 작성자마다 메시지 1개씩 순차 전송합니다 (여러 팀원이 같은 주기에 작성 → 사람 수만큼 메시지).

```
[FX Teamplay BOT]
정재화 - 업무 갱신 (2건)            ← 헤더: "{작성자} - 업무 갱신 ({N}건)" (이모지 없음)

1 𝗙𝗫 [공통] 포커리그 개편 [작업] 리그 등급 아이콘 7종   ← 카드 제목 (번호 + 업무명, 이모지 없음, 클릭 시 업무 이동)
[새댓글]                                              ← 변경 종류 텍스트 라벨
- 금주 진행내용: 06.05 클래식 등급 아이콘 7종 완료      ← 변경된 필드만
```

**변경 종류 라벨** (제목 이모지 대신 본문 첫 줄 `[라벨]` + 색상 막대):
| 라벨 | color 막대 | 의미 | 빌드 위치 |
|------|-----------|------|----------|
| `[새댓글]` | green | 새 댓글의 업무 행 | `taskToAttachment(t, '새댓글', ...)` |
| `[본문변경]` | blue | 본문(표) 변경 (작성자 `본문`) | `buildChangeAttachments` 본문 블록 |
| `[댓글수정]` | orange | 기존 댓글 수정 | `buildChangeAttachments` 수정 블록 |

- **카드 구조**: 변경 종류별 **별도 카드** (같은 업무라도 새댓글/본문변경은 각각 카드). 본문변경은 작성자를 알 수 없어 `본문` 그룹 메시지로 분리됨.
- **변경 필드 표시**: `- 금주 진행내용:` / `- 다음주 주요 액션:` / `- 이슈:` / `- 팀 공유사항:` 중 **변경된 항목만**. 삭제 시 `(삭제됨)`.

**이모지 정책**: 알림 메시지에는 **이모지를 쓰지 않음** (헤더 `📝`·카드 `💬/✏️/📄` 모두 제거). 꼭 필요할 때만 사용. (작업 제목의 `𝗙𝗫`는 Dooray 원본 제목 일부라 유지)

**작성자명 해석** (`pollForChanges` 스냅샷):
- Dooray 로그 API는 `createdBy`가 없고 `creator.member.organizationMemberId`(ID)만 반환 → 이름 직접 못 읽음
- `electron-main.js`의 **`HOOK_MEMBER_MAP`** (ID→이름)으로 변환. **`js/dooray/syncManager.js`의 `memberMap`과 동기화 유지 필수** (메인↔렌더러 상호 접근 불가)
- 매핑: 2029850955956616509=정재화, 1601496680004436952=김지인, 3066277838341582318=김보람
- **김지인은 전배(2026-04-04~)했지만 map에서 제거 금지** — 과거 댓글 이름 해석 + 향후 복귀 대비 (숨김 멤버 데이터 보존 정책)
- 새 팀원이 두레이 댓글 작성 시 양쪽 map에 ID 추가 필요. 못 찾으면 `알 수 없음`

**제목 접두사 제거** (`parseCommentTasks`): Dooray 링크 텍스트의 `프로젝트키/번호 ` 접두사 제거
- regex `/^[^\s/]+\/\d+\s*/` — 프로젝트명 무관 (예: `클래식FX팀-업무관리/800 𝗙𝗫...` → `𝗙𝗫...`)

**링크 파싱 — 제목 내 중첩 대괄호 대응** (`parseCommentTasks`, `cleanPreview`):
- 댓글 링크 regex는 `/\[(.*?)\]\(dooray:\/\/[^)]*\)/g` (lazy `.*?`) — 제목에 리터럴 `]`(예: `[팀과제]`, `[작업]`)가 있어도 진짜 `](dooray://`까지 캡처
- `[^\]]*` 금지: 첫 `]`에서 끊겨 링크 매칭 실패 → fallback이 원문(URL 포함) 전체를 덤프함
- 제목 대괄호가 리터럴 `[]`로 오든 HTML 엔티티(`&#91;`/`&#93;`)로 오든 lazy `.*?`면 안전
- `cleanPreview()`의 마크다운 링크 제거 regex도 동일하게 `\[(.*?)\]\([^)]*\)` 사용
- 사고 이력 2026-06-09 (Task 파싱): 한 작성자 댓글만 알림 제목이 `댓글 수정`으로 뜨고 본문에 `dooray://...` URL 노출 → lazy regex로 수정
- ⚠ **작성자=형식 고정 아님**: "정재화=HTML / 김보람=마크다운" 식으로 단정 금지 — 작성 방식에 따라 같은 사람도 형식이 바뀜 (아래 "표 형식 파싱" 참조)

**표 형식 파싱 — HTML `<table>` + 마크다운 `|` 둘 다 지원** (`parseCommentTasks`):
- Dooray 댓글 표는 **마크다운(`| 금주 진행내용 |...`)과 HTML(`<table><th>금주 진행내용</th><td>...</td>`) 두 형식이 혼재** (작성자/작성 방식에 따라 다름)
- `parseCommentTasks`는 링크 구간(`body`)마다 **HTML 표를 먼저 시도**(`parseHtmlTableTasks`) → 없으면 마크다운 `|` 표 파싱으로 fallback
- `parseHtmlTableTasks(body, title)`: `<th>`로 컬럼 인덱스(금주 진행내용/다음주 주요 액션/이슈/팀 공유사항) 매핑, `<th>` 포함 `<tr>`은 헤더로 스킵, `<td>` 셀을 `cleanHtmlCell()`(span/br/태그 제거 + 공백 정규화)로 정리
- **미지원 시 증상**: 표 파싱 0개 → `buildChangeAttachments`의 `allTitles.size===0` fallback → 링크+URL+표 헤더가 한 줄로 뭉친 **raw 텍스트 덤프**로 알림이 옴
- 사고 이력 2026-06-09: 마크다운 `|` 표만 처리하던 `parseCommentTasks`가 HTML `<table>` 댓글을 raw로 덤프 → `parseHtmlTableTasks` 추가. (렌더러 `js/dooray/commentParser.js:_extractHtmlTable()`는 원래부터 둘 다 처리 — 메인 프로세스 파서가 그 기능을 놓쳤던 것)

**마크다운 이스케이프 제거** (`unescapeMarkdown`, `cleanPreview`/`cleanCell`/`cleanHtmlCell`):
- 두레이 본문은 특수문자 앞에 백슬래시를 붙임 (`바둑\&오목`, `26.05\~26.06`, `\[작업\]`, `fsx\_shine`)
- `electron-main.js`의 `decodeHtmlEntities`는 **HTML 엔티티만** 풀고 마크다운 이스케이프는 안 풀어서 `\`가 알림에 그대로 노출됨 (한글 Windows에선 `\`가 `₩`로 보임)
- `unescapeMarkdown(text)` — 특수문자(백슬래시·백틱·`* _ { } [ ] ( ) # + - . ! > < | ~ & =`) 앞의 `\`만 제거, **글자 앞 `\`(`C:\Users`)는 보존**
- `cleanPreview`/`cleanCell`/`cleanHtmlCell` 3곳 모두 `decodeHtmlEntities` 직후 적용
- ⚠ 렌더러 `commentParser.decodeHtml`(`\&`→`&` 등)과 동일 취지지만 **별도 구현** — syncManager의 이스케이프 패턴엔 `&`가 빠져 있으니 주의 (unescapeMarkdown은 `&` 포함)
- 사고 이력 2026-06-09: `바둑\&오목` 알림 노출 → `unescapeMarkdown` 추가

**이중 인코딩 대응 — `decodeHtmlEntities` 2차 패스** (`electron-main.js`, `commentParser.js`):
- Dooray API 응답이 `&amp;#91;` (= HTML로 이중 인코딩된 `&#91;` = `[`) 같은 형태를 반환할 수 있음
- 1차 디코딩: `&amp;#91;` → `&#91;`, 2차 디코딩: `&#91;` → `[`
- `electron-main.js:decodeHtmlEntities()` — `decode()`를 2회 적용 (named 엔티티 먼저 → 숫자 엔티티, 결과에 `&[#a-zA-Z]` 패턴 남으면 재실행)
- `commentParser.js:decodeHtml()` — `textarea.innerHTML` 방식으로 동일하게 2차 패스 추가

**알림 제목 HTML 엔티티 노출 방지** (`buildChangeAttachments`, `taskToAttachment`):
- `parseCommentTasks`에서 `decodeHtmlEntities`를 적용했음에도 특정 엣지케이스에서 `&gt;`가 attachment `title`에 남아 Dooray 메신저에 `&gt;`가 리터럴 텍스트로 노출되는 문제
- **방어적 fix**: attachment `title`을 최종 생성하는 4곳에서 `decodeHtmlEntities` 추가 적용 (idempotent — 이미 디코딩된 값에 재호출해도 안전)
  - `parseCommentTasks` line 1338: 링크 타이틀에 `unescapeMarkdown` 추가 (`>` 등 백슬래시 이스케이프도 처리)
  - `buildChangeAttachments [본문변경]`: `title: decodeHtmlEntities(title)`
  - `buildChangeAttachments [댓글수정]`: `title: decodeHtmlEntities(title)`
  - `taskToAttachment`: `title: decodeHtmlEntities(task.title)`
- 사고 이력 2026-06-10: `𝗙𝗫 [공통] 포커리그개편 &gt; 내 업적에...` 알림 노출 → 방어적 decode 추가

**"알 수 없음 / 변경사항이 감지되었습니다." fallback** (`buildChangeAttachments`):
- `attachments.length === 0`일 때 강제로 들어가는 기본 카드 (작성자 하드코딩 `알 수 없음`, 본문 `변경사항이 감지되었습니다.`)
- **원인**: 해시(`comments + postBody + postUpdatedAt`)는 바뀌었는데 `analyzeChanges`가 구체 변경(새 댓글/수정 댓글/본문 텍스트)을 못 찾음
  - ① **메타데이터만 변경**: 워크플로우 상태·담당자·마감·파일첨부 등 → `postUpdatedAt`만 갱신
  - ② **댓글 삭제**: `analyzeChanges`에 삭제 감지 분기 없음 (ID 기준 신규/수정만 비교)
- 버그 아님 — "업무가 건드려졌다"는 신호. (작성자 ID가 `HOOK_MEMBER_MAP`에 없어서 뜨는 "알 수 없음"과는 별개: 그 경우는 구체 변경 내용이 함께 표시됨)

### 시계

**표시 형식**: `YYYY.MM.DD (요일) HH:MM:SS`
**색상**: 파랑 (`#4285f4`)
**너비**: `white-space: nowrap`으로 텍스트에 맞게 자동 확장

### Auto Sync 플로팅 뱃지

Automation Panel의 백그라운드 폴링 Sync 상태를 독립 플로팅으로 표시합니다.

**위치**: Hook Polling 왼쪽에 동적 배치 (hookPolling 너비에 따라 `right` 계산)
**디자인**: 초록색 테두리/텍스트, `#E6F4EA` 배경, 둥근 뱃지 (`border-radius: 14px`)
**구성**: `Sync` 라벨(볼드) + 카운트다운 (`MM:SS`) 또는 "Sync 중" 스피너
**HTML**: `#autoSyncFloat` > `#autoSyncStatus` (hookPollingStatus 바깥 독립 div)
**CSS**: `.auto-sync-float`, `.auto-sync-label`, `.auto-sync-status`

### 구현 위치
| 파일 | 역할 |
|------|------|
| `electron-main.js` | `pollForChanges()`, `analyzeChanges()`, `buildChangeAttachments()`, `taskToAttachment()`, `parseCommentTasks()`, `parseHtmlTableTasks()`(HTML 표), `cleanCell()`/`cleanHtmlCell()`, `unescapeMarkdown()`(마크다운 이스케이프 제거), `cleanPreview()`, `sendDoorayHookNotification()`, `HOOK_MEMBER_MAP`, IPC 핸들러 |
| `electron-preload.js` | `doorayHookTest()`, `doorayHookConfig()` IPC 브릿지 |
| `js/main.js` | `HookPollingUI` — 카운트다운 타이머, On/Off 토글, 간격 설정, 시계 갱신 |
| `js/automationPanel.js` | `_updateSyncIndicator()`, `_updateSyncCountdown()` — Auto Sync 플로팅 뱃지 위치/내용 갱신 |
| `index.html` | `#hookPollingStatus`, `#hookPollingTimer`, `#hookPollingToggle`, `#hookPollingClock`, `#autoSyncFloat` |
| `styles.css` | `.hook-polling-status`, `.hook-polling-timer`, `.hook-polling-clock`, `.auto-sync-float` |

## 앱 이름 / 타이틀 (FX Team)

앱 이름은 **"FX Team"** 입니다. (구 명칭: Teamplay / FX Team Schedule — 모태인 `Team Schedule Manager`의 잔재)
Task 트래킹뿐 아니라 연중 계획·팀 업무·VFX 어셋 트래킹·보고서 자동화까지 포괄하므로 "Schedule"을 떼고 "FX Team"으로 통일했습니다.

### 이름 표시 위치
| 위치 | 값 | 비고 |
|------|-----|------|
| 윈도우/탭 타이틀 `<title>` | FX Team | `index.html` |
| 메타 앱 타이틀 / 설명 | FX Team | `index.html` |
| 헤더 로고 `#appTitle` | FX Team | **기본 숨김** (`visible: false`) |
| `document.title` (런타임) | `settings.text` | `main.js:applyTitleSettings()` |
| `package.json` productName | **Teamplay** (미변경) | 빌드 결과물(exe) 이름 — 리네이밍 시 빌드/단일인스턴스 잠금 영향 |
| localStorage 접두사 | `teamScheduler_*` (미변경) | 데이터 호환 유지 |

### 주의사항
- **`document.title`에 " Schedule" 자동 추가 금지**: 과거 `applyTitleSettings()`가 `${settings.text} Schedule`로 창 제목을 만들어 "FX Team Schedule"이 표시되던 버그 → `document.title = settings.text`로 수정 (사고 이력 2026-06-06)
- **헤더 로고는 기본 숨김**: `titleSettings.visible: false` (state.js 2벌 + 기본값). 보이게 하려면 Settings > Appearance > Title에서 토글
- **일회성 마이그레이션**: `storage.js:loadData()` — `teamScheduler_titleRenamedFXTeam2` 플래그로 기존 사용자 데이터에도 `text: 'FX Team'` + `visible: false` 1회 강제 적용 (이후 사용자 수정값 유지)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `index.html` | `<title>`, 메타 태그, `#appTitle` 정적 마크업 |
| `js/state.js` | `DEFAULT_TITLE_SETTINGS` + `AppState.titleSettings` (2벌, `text: 'FX Team'`, `visible: false`) |
| `js/main.js` | `applyTitleSettings()` — `document.title = settings.text` |
| `js/storage.js` | `loadData()` — 일회성 리네이밍 마이그레이션 |

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

### 단일 인스턴스 잠금 (Single Instance Lock)
이 앱은 단일 인스턴스로만 실행되어야 합니다. 두 인스턴스가 동시에 실행되면:
- localStorage/JSON 파일 동시 쓰기로 데이터 손실/덮어쓰기 발생
- Auto Sync, Hook Polling, 자동 백업이 중복 실행됨

**2단계 방어**:

1. **배치 파일 레벨** (`Teamplay.bat`): wmic으로 `_Teamplay` 경로의 `electron.exe` 프로세스 존재 확인 → 있으면 즉시 종료 (VS Code 등 다른 Electron 앱과 충돌 없음)

2. **Electron 레벨** (`electron-main.js`): `requestSingleInstanceLock()` + `app.setAppUserModelId('com.teamplay.fx')`
```javascript
app.setAppUserModelId('com.teamplay.fx');  // 앱 ID 고정 — Lock 안정성 보강

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
    app.quit();  // 두 번째 인스턴스 즉시 종료
} else {
    app.on('second-instance', () => {
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.focus();
        }
    });
}
```

**효과**: 앱이 이미 실행 중이면 두 번째 실행 시 기존 창으로 포커스 이동

### 흰 화면 방지 최적화
1. `BrowserWindow` 생성 시 `show: false` — 창을 숨긴 채 시작
2. 앱 초기화 (`main.js:init()`) 완료 후 double `requestAnimationFrame`으로 렌더링 보장
3. `electronAPI.notifyAppReady()` → IPC `app-ready` → `mainWindow.show()`
4. Safety timeout 5초: IPC 실패 시에도 창 표시

### 구현 위치
| 파일 | 역할 |
|------|------|
| `electron-main.js` | `requestSingleInstanceLock()`, `show: false`, `ipcMain.once('app-ready')`, 5초 safety timeout |
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

## Task Creator (두레이 새 업무)

Dooray 새 업무 생성 + 위키 페이지 + 팀플레이 댓글 추가를 통합 처리하는 모듈입니다.

**모듈**: `js/taskCreator.js` (TaskCreator 싱글턴)

### 진입점
- 사이드 패널 → "두레이 새 업무" (`#taskCreatorBtn`)

### 모달 구성
```
+--------------------------------------------------+
| 두레이 새 업무  2026.03.22 (토) 14:30:05    ✕    |
+--------------------------------------------------+
| 플랫폼: [PC포커 ▼]   프로젝트: [_____(자동완성)]  |
| [태그 ▼]  Task명: [_____(자동완성+중복감지)]       |
| 카테고리: [인게임 ▼]  조직: [포커게임기획팀 ▼]    |
| 시작일: [2026-03-22]  종료일: [2026-03-22]        |
| 점검월: [26.04]                                   |
| 기획 URL: [dooray://...]   📄 기획 업무 제목      |
+--------------------------------------------------+
| 옵션:                                            |
| ☑ Gantt 자동 등록  ☑ 위키 자동 생성              |
| ☑ 팀플레이 댓글 추가                              |
|   [◀ 지난주] [이번주] [다음주 ▶]                  |
|   📄 팀플레이 업무 제목                           |
+--------------------------------------------------+
| 상태 로그...                                      |
|                        [불러오기] [생성]           |
+--------------------------------------------------+
```

### 동작 흐름
```
생성 클릭 → ① 위키 페이지 생성 (옵션) → ② 기획 링크 조회 → ③ Dooray 업무 POST → ④ Gantt 등록 (옵션) → ⑤ 팀플레이 댓글 추가 (옵션) → 완료
```

### 상태태그 선택 (`tcStatusTag`)
Dooray 업무 제목에 들어갈 `[상태태그]`를 Task명 앞 드롭다운으로 선택합니다.

| 태그 | 용도 |
|------|------|
| `작업` (기본) | 일반 작업 업무 |
| `일정` | 프로젝트 일정 계획 문서 |
| `QA` | QA 대응 업무 |
| `완료` | 완료 처리 업무 |
| `기획` | 기획 관련 업무 |

- `resetState()` 호출 시 자동으로 `작업`으로 초기화
- HTML: `<select id="tcStatusTag">` (90px 고정, Task명 입력란 앞에 배치)

### 옵션 체크박스
| 옵션 | ID | 기본값 | 설명 |
|------|-----|--------|------|
| Gantt 자동 등록 | `tcAutoGantt` | checked | Gantt에 Task 자동 추가 (테스트 시 해제 가능) |
| 위키 자동 생성 | `tcAutoWiki` | checked | Wiki 페이지 자동 생성 (기존 위키 있으면 스킵) |
| 팀플레이 댓글 추가 | `tcAutoComment` | checked | 팀플레이 업무 댓글에 새 업무 행 추가 |

### 프로젝트 자동완성 (커스텀 드롭다운)
네이티브 `<datalist>` 대신 커스텀 드롭다운(`#tcProjectSuggestions`)을 사용합니다.

**동작**:
- 포커스/입력 시 Gantt의 unique 프로젝트 목록을 드롭다운으로 표시
- 타이핑 시 실시간 필터링 (부분 문자열 매칭)
- **↑/↓ 방향키**: 항목 이동 + 하이라이트, **Enter**: 선택 확정, **Esc**: 닫기
- 마우스 클릭으로도 선택 가능
- 선택 시 `_onProjectChange()` + `_updateTaskSuggestions()` 자동 호출

**배경**: Chromium `<datalist>`는 방향키 탐색 시 `change`/`input` 이벤트가 불안정하게 발생하여 커스텀으로 교체

**구현**: `taskCreator.js` — `_populateProjectSuggestions()`, `_showProjectSuggestions()`, `_hideProjectSuggestions()`, `_onProjectKeydown()`, `_highlightProjectItem()`

### Task명 자동완성 + 중복 감지
선택된 프로젝트의 기존 Task명을 드롭다운으로 제안하고, 중복을 감지합니다.

**동작**:
- 프로젝트 선택 후 Task명 입력란 포커스 시 해당 프로젝트 Task 목록 표시
- 각 항목에 담당자명 표시 (오른쪽, 회색 `.tc-suggest-assignee`)
- **↑/↓ 방향키**: 항목 이동, **Enter**: 선택 확정, **Esc**: 닫기
- 입력 중 실시간 필터링 + 기존 Task명과 완전 일치 시 빨간 "중복" 뱃지 (`#tcTaskDupWarning`)

**데이터**: `_projectTaskItems` — `{ name, assignee }` 배열, `_projectTaskNames` — 이름만 배열

**구현**: `taskCreator.js` — `_showTaskSuggestions()`, `_onTaskNameInput()`, `_onTaskNameKeydown()`, `_checkDuplicate()`
**CSS**: `.tc-task-suggestions`, `.tc-task-suggest-item`, `.tc-suggest-assignee`, `.tc-dup-warning`

### 프로젝트 정보 불러오기
- "불러오기" 버튼 또는 프로젝트 입력 시 자동: 기존 Gantt Task에서 동일 프로젝트 정보 자동 채움
- 채워지는 필드: 플랫폼, 카테고리, 조직, 점검월, 기획 URL
- 기획 URL: 1순위 `task.planningUrl` 직접 참조 → 2순위 Dooray API 본문에서 추출

### 점검월 자동 추론 (`_inferReleaseMonthFromProject`)
프로젝트명에 "N월" 패턴이 있으면 점검월(`releaseMonth`)을 자동 추론합니다.

- **트리거**: `_loadFromExisting()` (불러오기) + `_onProjectChange()` (프로젝트명 입력 시)
- **조건**:
  - N월 패턴이 있으면 **항상 덮어쓰기** (기존 값이 있어도 갱신 — 프로젝트마다 달라야 하므로)
  - N월 패턴이 없으면 **비어있을 때만** 자동 채움 (기존 값 보호)
- **추론 규칙**: `project.match(/(\d{1,2})월/)` → `YY.MM` 형식 (`String(new Date().getFullYear()).slice(2)` + padStart 2)
- **예시**: `6월 업데이트` → `26.06`, `12월 패치` → `26.12`
- **실패 케이스**: "N월" 패턴 없음 또는 월 범위 밖(1~12 외) → null 반환 (점검월 그대로 유지)

### N월 업데이트 패턴 — 자동 채움 스킵
프로젝트명에 "N월" 패턴이 있을 때(`hasMonthPattern = true`) 플랫폼/조직/기획URL 자동 채움을 건너뜁니다.

**스킵 대상 필드**:
| 필드 | 이유 |
|------|------|
| 플랫폼 | "N월 업데이트"는 여러 플랫폼에 공통으로 등록되므로 한 플랫폼으로 고정하면 오선택 |
| 조직 | 같은 프로젝트명이 여러 조직(게임기획/서비스기획/사업)에 걸쳐 있음 |
| 기획 URL | 기획자별로 URL이 달라 프로젝트명만으로 특정 불가 |

**유지되는 자동 채움**: 카테고리 + 점검월(N월 패턴에서 덮어쓰기)

**적용 함수**:
- `_loadFromExisting()` — 불러오기 버튼 클릭 시
- `_onProjectChange()` — 프로젝트명 타이핑 시

**구현**: `const hasMonthPattern = !!this._inferReleaseMonthFromProject(project);` → `if (!hasMonthPattern) { ... }`

### 위키 페이지 재사용 (중복 생성 방지)
새 업무 생성 시 위키 페이지가 이미 존재하면 새로 만들지 않고 기존 페이지를 재사용합니다.

**동작** (`_createWikiPage()`):
1. 월 폴더 획득 (기존과 동일)
2. 월 폴더 내 기존 페이지 목록 조회 (`GET /wiki/.../pages?parentPageId=...`)
3. 같은 `subject`(제목)의 페이지가 있으면 **그 페이지를 반환 + `isNew: false`** (POST 스킵)
4. 없으면 기존대로 새 페이지 POST + **`isNew: true`** 반환

**효과**: 같은 프로젝트로 업무를 두 번 생성해도 위키가 중복 생성되지 않음, 기존 위키 내용 보존

**`isNew` 플래그**: 위키 본문 채움 시 신규 생성된 위키에만 PUT 업데이트 적용 (기존 페이지 내용 보호)

**구현**: `taskCreator.js:_createWikiPage()` — GET 조회 후 `find(p => p.subject === pageTitle)` 매칭

### 위키 본문 자동 생성 (`_buildWikiContent`)
Dooray 업무 생성 후 신규 위키 페이지에 FX 섹션 구조 본문을 자동으로 채웁니다.

**트리거 조건**: 위키 자동 생성 옵션 체크 + 신규 위키(`wikiIsNew === true`) + Dooray 업무 생성 성공

**동작 흐름**:
```
① 위키 페이지 생성 → isNew 판별
② Dooray 업무 POST → newPostId 획득
② -2. wikiIsNew && newPostId → _buildWikiContent() → PUT /wiki/.../pages/{wikiPageId}
```

**생성되는 위키 본문 구조**:
```markdown
## FX 정재화

### (카테고리명)
[클래식FX팀-업무관리/번호 𝗙𝗫 &#91;플랫폼&#93; 프로젝트 &#91;작업&#93; Task명](dooray://orgId/tasks/postId)

## 기획

(기획 링크 — planningLink 있을 때)

## UI

## 원화

## 개발
```

**구현 세부**:
- 카테고리가 `(미분류)` 이면 `### 카테고리` 헤더 생략
- `leaderName` = `TeamManager.getLeaderName()` 동적 (하드코딩 금지)
- 대괄호 이스케이프: `[` → `&#91;`, `]` → `&#93;`
- `taskNumber`에 `/` 포함 시 projectCode 미접두 (위키 패널과 동일 규칙)
- 재사용 위키(`wikiIsNew === false`)는 PUT 스킵 → 기존 내용 보존

### 기획 URL 제목 표시
- URL 입력 시 debounce 400ms → Dooray API로 업무 제목 조회 → `#tcPlanningTitle` 표시
- 캐시: `_planningTitleCache[url]` — 같은 URL 재조회 방지
- URL 형식: `dooray://`, `https://nhnent.dooray.com/task/...`, `/project/tasks/...` 모두 지원

### 주차 선택 (팀플레이)
- 팀플레이 댓글 옵션 활성 시 표시: 지난주(-1) / 이번주(0) / 다음주(+1)
- `Utils.getWeekInfo(date, weekOffset)` 사용하여 주차 검색 패턴 생성
- 캐시: `_teamplayCache` — 같은 주차 재검색 방지

### 생성되는 Dooray 업무
| 항목 | 형식 |
|------|------|
| 제목 | `𝗙𝗫 [플랫폼] 프로젝트 [선택태그] Task명` (기본: `[작업]`) |
| 본문 | 프로젝트 정보 마크다운 (카테고리/조직/일정/점검월/위키/기획) |
| 담당자 | 정재화 (`JAEWHA_MEMBER_ID`) |

### 상수
| 값 | 상수 |
|----|------|
| FX 프로젝트 ID | `4028352443299472148` |
| 조직 ID | `1387695619080878080` |
| 정재화 memberId | `2029850955956616509` |

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/taskCreator.js` | TaskCreator 모듈 전체 (폼/위키/업무생성/댓글/헤더시계) |
| `index.html` | `#taskCreatorModal` HTML + 사이드 패널 `#taskCreatorBtn` |
| `js/main.js` | 이벤트 바인딩 + Escape 핸들러 |
| `styles.css` | `.modal-task-creator`, `.tc-*` 스타일 |

### 헤더 시계
모달 제목 오른쪽에 현재 날짜/시간을 실시간 표시합니다.

**표시 형식**: `2026.03.22 (토) 14:30:05` (1초 간격 갱신)
**생명주기**: 모달 열기 시 `_startHeaderClock()` → 닫기 시 `_stopHeaderClock()`
**HTML**: `#tcHeaderClock` (`.tc-header-clock`, 12px 회색)
**구현**: `taskCreator.js` — `_clockTimer`, `_startHeaderClock()`, `_stopHeaderClock()`, `_updateHeaderClock()`

## Daily Briefing (일일 브리핑)

앱 시작 시 오늘/이번주 팀원별 할일과 업계 소식을 요약하는 모달 팝업입니다.

### 진입점
- 앱 시작 시 자동 표시 (하루 1회, "오늘은 더 이상 보지 않기" 클릭 시 비활성)
- 단축키: `Y`

### 탭 구성
| 탭 | 내용 |
|---|---|
| 팀 업무 (기본) | 팀원별 카드 + 전체 요약 + 지연/이번 주 마감 |
| 업계 소식 | RSS 피드 뉴스 (VFX/Animation, Game Industry, Tech) |

### 팀 업무 탭 레이아웃
```
┌─ FX팀 (1줄, full width 세로로 길게) ─────────────┐
│ ● FX팀                                           │
│ 지연/오늘/금주 ...                                │
├─ 사람 개인 (2줄, 3컬럼 그리드) ──────────────────┤
│ ● 정재화          ● 김보람          + 팀원 추가   │
│ 진행 7 · 지연 7   진행 4 · 지연 4    (빈 슬롯)     │
├─ FX AI팀 (3줄, full width 세로로 길게) ──────────┤
│ ● ✦FX AI팀                                       │
├─ AI 개인 (4줄, 3컬럼 그리드) ────────────────────┤
│ ● ✦Jully         ● ✦Lumi           ● ✦Annie      │
├─ 전체 요약 ─────────────────────────────────────┤
│ 전체 196개 Task 중 178개 완료 (91%) · 지연 10건  │
├─ 지연 ──────────┬─ 이번 주 마감 ────────────────┤
│ Task1 D+60      │ Task1 D-Day                   │
│ Task2 D+46      │ Task2 D-4                     │
└─────────────────┴───────────────────────────────┘
```

- **팀원 카드**: `MemberDashboard._calcStats()`, `_getWeekTasks()` 재사용
- **4줄 분리**: 멤버 이름에 `✦` 포함 시 AI, `isGroup`으로 팀 그룹 구분
  - 1줄: 사람 팀 그룹 (`FX팀`) — `.db-team-row` (full width, 세로로 길게)
  - 2줄: 사람 개인 (`정재화, 김보람`) + 빈 슬롯(`+ 팀원 추가 예정`, `.db-card-empty`) — `.db-cards-grid` 3컬럼
  - 3줄: AI 팀 그룹 (`✦FX AI팀`) — `.db-team-row` (full width)
  - 4줄: AI 개인 (`✦Jully, ✦Lumi, ✦Annie`) — `.db-cards-grid` 3컬럼
  - 각 줄 내부 순서는 `TeamManager.getOrderedMembersAndGroups()` order 유지
  - 구현: `dailyBriefing.js:_render()` — `isAI()`/`isGroup` 분류 + `buildCard()`/`renderRow()`/`renderTeamRow()` 헬퍼
- **카드 너비 균등 + Task명 말줄임**: `.db-member-card { min-width: 0; overflow: hidden }`
  - grid 트랙(`repeat(3, 1fr)`) 아이템의 기본 `min-width: auto` 때문에 `white-space: nowrap`인 긴 Task명이 트랙을 콘텐츠 폭만큼 넓혀 **가로 스크롤(좌우 잘림)이 발생**하던 문제 해결
  - `min-width: 0`으로 카드가 1fr 균등 분할되고, `.db-task-text`의 `text-overflow: ellipsis`가 정상 동작 (긴 Task명 `…` 처리)
- **그룹 중복 제거**: Display Group(FX팀) 전원 배정 Task는 개인 카드에서 제외, 그룹 카드에만 표시
- **전체 요약**: Bypass 제외, Done+100% 완료 카운트
- **하단 2컬럼**: 지연(빨강 배경) + 이번 주 마감(주황 배경), 담당자 표시
- Task 클릭 → Gantt 이동 (모달 유지)

### 업계 소식 탭
- **RSS 피드 16개**, 8개 카테고리:

| 카테고리 | 소스 |
|---------|------|
| Casino / Poker Game | Social Casino Biz, Deconstructor of Fun, GamblingNews |
| Game VFX / Art | Real Time VFX, 80.lv VFX, ArtStation Magazine, Concept Art World |
| UI Motion / Icon Animation | Dribbble Stories, STASH |
| VFX / Motion Design | fxguide, Motionographer, befores & afters |
| Animation / Effects Reference | Sakugabooru Blog, Sakugabooru Effects/Fire/Smoke |
| VFX Tutorials | Gabriel Aguiar (YouTube), CGHOW (YouTube) |
| Game Industry | Game Developer, GamesIndustry.biz |
| Tech / Design | The Verge Gaming |

- **30분 캐시**: `_newsCache` + `_newsCacheTime`
- **자동 백그라운드 로딩**: 모달 열릴 때 자동 시작 (탭 클릭 불필요), 탭 버튼에 스피너→체크 표시
- **IPC**: `electron-main.js:fetch-rss` → Node.js https, 재귀 리다이렉트 (최대 5회), Mozilla UA
- 뉴스 클릭 → 외부 브라우저 열기

### 인터랙션
| 동작 | 트리거 |
|------|--------|
| 자동 표시 | `DailyBriefing.onAppStart()` — localStorage로 하루 1회 제어 |
| 수동 열기 | `Y` 키 |
| 닫기 | Esc / 배경 클릭 / X 버튼 |
| 오늘 비활성 | "오늘은 더 이상 보지 않기" 버튼 클릭 시 localStorage 저장 |
| 모달 드래그 | 헤더 mousedown으로 이동, 닫을 때 위치 리셋 |

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/dailyBriefing.js` | DailyBriefing 모듈 전체 |
| `index.html` | `#dailyBriefingModal` HTML + script 태그 |
| `js/main.js` | init, startup(500ms), Y 단축키, Escape 체인 |
| `electron-main.js` | `fetch-rss` IPC 핸들러 |
| `electron-preload.js` | `fetchRss()` 브릿지 |
| `styles.css` | `.db-*` 스타일 |

## NBSP 주의 (Dooray 본문 파싱)

Dooray API 응답 본문에서 일부 필드 뒤에 Non-Breaking Space (U+00A0)가 사용됩니다.

**영향받는 위치**: `기획:` 필드 뒤 공백
**문제**: `[ \t]*`는 U+00A0을 매칭하지 못함 → 파싱 실패
**해결**: `\s*` 사용 (JavaScript `\s`는 U+00A0 포함)

**적용 위치**:
- `syncManager.js:parseProjectInfoFromBody()` — 위키→기획 크로스라인 regex (1곳)
- `main.js:fillFormFromDooray()` — 기획 URL/제목 파싱 regex (4곳)

## 팀 업무 가이드 뷰어

탭 기반으로 여러 MD 문서를 앱 내 모달에서 열람하는 기능입니다.

**단축키**: `V` (토글)

### 탭 시스템
| 탭 | 파일 | 설명 |
|---|---|---|
| 업무 워크플로우 | `TEAM-WORKFLOW.md` | 5단계 업무 워크플로우 정의 + 시스템 분석 |
| 주간보고 자동화 | `WEEKLY-AUTOMATION.md` | 주간보고 자동화 전체 규칙 |
| 제목 규칙 | `TITLE-RULES.md` | 두레이 업무 제목 규칙 (지속 관리 — 변경 이력 섹션 유지) |

**탭 확장**: `main.js:_twfTabs[]` 배열에 `{ id, label, file }` 추가만으로 새 탭 생성
**파일 캐시**: `_twfCache[file]` — 같은 파일 재로드 방지, 탭 전환 시 즉시 표시
**탭 UI**: `.twf-tab-bar` > `.twf-tab` (active 시 파란 하단 border)

### 동작
- `V` 키 또는 `toggleTeamWorkflowModal()` → 모달 열기
- 탭 클릭 → `_switchTwfTab(tabId)` → 해당 MD 파일 로드 + 렌더
- `electronAPI.readFile()` → MD 파일 로드
- `_renderMarkdown()` → 마크다운 → HTML 변환 (헤딩/표/코드블록/리스트/인용/인라인)
- `Escape` 또는 배경 클릭 → 모달 닫기

### 마크다운 렌더링 지원
| 요소 | 문법 |
|------|------|
| 헤딩 | `# ~ ######` |
| 표 | `\| col \| col \|` |
| 코드블록 | `` ``` `` |
| Flow 다이어그램 | `` ```flow `` |
| 순서 리스트 | `1. item` |
| 비순서 리스트 | `- item` |
| 인용 | `> text` |
| 수평선 | `---` |
| 볼드 | `**text**` |
| 인라인 코드 | `` `code` `` |
| URL + 복사 아이콘 | `https://...` → 클릭 시 클립보드 복사 + 체크 피드백 |

### Flow 다이어그램 DSL
코드블록 언어를 `flow`로 지정하면 `_renderFlowDiagram()`으로 HTML 다이어그램 렌더링

**문법**: `A -> B? -> C` — 노드를 `->` 화살표로 연결, `?` 접미사는 선택 단계(점선 박스)
**예시**: `` ```flow\n기획 -> 자료조사? -> 작업 -> QA? -> 최종\n``` ``

| 노드 타입 | CSS 클래스 | 스타일 |
|----------|-----------|--------|
| 핵심 단계 | `.twf-flow-core` | 파란 배경 (`--google-blue`), 흰 텍스트 |
| 선택 단계 (`?`) | `.twf-flow-optional` | 흰 배경, 점선 테두리, 회색 텍스트 |

**노드 크기**: `width: 72px` 고정 (모든 노드 동일 너비)
**화살표**: `.twf-flow-arrow` — 수평선 + 오른쪽 삼각형 (CSS border trick)

### 목차 (TOC)
문서 최상단에 h2/h3/h4 기반 목차를 자동 생성하고, 헤더에 "목차" 뱃지로 바로가기를 제공합니다.

**목차 생성**: `_renderMarkdown()` — 헤딩에 `id="twf-h-N"` 부여 → 목차 `<nav class="twf-toc">` HTML 자동 생성
**들여쓰기**: h2=0단계, h3=1단계, h4=2단계 (`twf-toc-l0/l1/l2`, padding-left 16px 단위)
**클릭 이동**: 목차 항목 클릭 → `scrollIntoView({ behavior: 'smooth' })`
**헤더 뱃지**: 모달 제목 오른쪽 파란 "목차" 뱃지 (`#twfTocBtn`, `.twf-toc-btn`) — 클릭 시 목차로 스크롤
**CSS**: `.twf-toc`, `.twf-toc-title`, `.twf-toc-btn`

### URL 복사 아이콘
문서 내 bare URL(`https://...`) 옆에 복사 아이콘을 자동 표시합니다.

- **렌더링**: `_inlineMarkdown()` — bare URL 감지 → `<span class="twf-url">` + `<i class="twf-copy-btn">` 삽입
- **클릭**: `navigator.clipboard.writeText(url)` → 체크 아이콘으로 변경 (1.5초 후 복원)
- **CSS**: `.twf-url` (word-break), `.twf-copy-btn` (회색 → hover 파랑), `.twf-copied` (초록 체크)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `TEAM-WORKFLOW.md` | 업무 워크플로우 문서 |
| `WEEKLY-AUTOMATION.md` | 주간보고 자동화 규칙 문서 |
| `TITLE-RULES.md` | 두레이 업무 제목 규칙 문서 (변경 이력 섹션 포함, 지속 관리) |
| `index.html` | `#teamWorkflowModal` HTML + `#twfTabBar` 탭 바 + `#twfTocBtn` 목차 뱃지 |
| `js/main.js` | `_twfTabs[]`, `_switchTwfTab()`, `openTeamWorkflowModal()`, `_renderMarkdown()` |
| `styles.css` | `.modal-team-workflow`, `.twf-tab-bar`, `.twf-tab`, `.twf-*` |

## VFX Asset Dashboard (어셋 데이터 현황)

포커 4개 앱(PC, Classic, Holdem, Baduki)의 VFX 어셋 파일 수/용량을 스캔하고 비교/추이를 시각화하는 뷰입니다.

### 진입점
- 뷰 탭: VFX Assets (8번 키)
- 앱 시작 시 VFX Assets 뷰에서 시작하지 않음 (git fetch 지연 방지)

### 프로젝트 경로 (4개 앱)
| 앱 | Git 저장소 | VFX 경로 |
|---|-----------|---------|
| PC | `PC_VFXAssetSync` | `.../PC/Asset/VFX` |
| Classic | `Classic_VFXAssetSync` | `.../Classic/DirectLinkResource/VFX` |
| Holdem | `Classic_VFXAssetSync` | `.../Classic/SubApp/Holdem/DirectLinkResource/VFX` |
| Baduki | `Classic_VFXAssetSync` | `.../Classic/SubApp/Baduki/DirectLinkResource/VFX` |

### 레이아웃
```
[⋮⋮⋮] (경로 설정)                          [전체 Pull] [전체 스캔]
┌─ PC ──────┐ ┌─ Classic ──┐ ┌─ Holdem ───┐ ┌─ Baduki ───┐  ← 앱 카드
│ 5,063 files│ │ 3,315 files│ │ 319 files  │ │ 196 files  │
│ 936 MB     │ │ 466 MB     │ │ 30 MB      │ │ 32 MB      │
│ png/mat/...│ │ anim/png...│ │ png/prefab.│ │ prefab/anim│
└────────────┘ └────────────┘ └────────────┘ └────────────┘
┌─ 트렌드 (파일 수) ─────┐ ┌─ 트렌드 (용량) ──────────┐  ← 듀얼 SVG 선 차트
│ PC ━━━━━━━ 5,063       │ │ PC ━━━━━━━ 936.0 MB     │
│ Classic ━━━━ 3,328     │ │ Classic ━━━━ 451.1 MB   │
└────────────────────────┘ └──────────────────────────┘
▶ 포맷별 비교 (세로 바 차트, 듀얼: 파일 수 + 용량)
▶ 포맷 상세 (테이블, 접기/펼치기)
```

### 기능
| 기능 | 설명 |
|------|------|
| 스캔 | 로컬 VFX 디렉토리 재귀 스캔 (.meta 제외) |
| Pull | git pull 후 자동 재스캔 (비동기, UI 블로킹 없음) |
| Pull 상태 표시 | 카드에 시각 + 완료/변경없음/실패/스캔 상태 표시 |
| Pull 비교 | pre/post 스캔 비교 + git diff stat → 포맷별 증감 토스트 |
| 전체 Pull/스캔 | Git 저장소 중복 제거하여 일괄 실행 |
| 자동 Pull 스케줄 | 헤더에 pill 형태로 시간 표시, 클릭 편집, 매분 체크, 하루 1회 제한, 카운트다운(초) |
| 트렌드 차트 | SVG 선 차트 듀얼(파일 수 + 용량), 앱 토글(복수 선택), 기간(1주/1개월/3개월/1년/직접지정) |
| 트렌드 포맷 | 전체/png/mat/shader/anim/prefab 클릭 전환 (solo 모드, 재클릭 → 전체 복귀) |
| 트렌드 필터 | 주말 제외 체크박스 + 변화만 체크박스 (포맷 선택 연동), pill 배경 라벨, **기본값 ON** |
| 트렌드 기간 | 프리셋 + 커스텀 날짜 선택, 30일↓ 일별, 90일↓ 주별, 90일↑ 월별 자동 집계 |
| 트렌드 앱 선택 | 클릭=solo(해당 앱만), solo 재클릭=전체(4개) 복귀, Ctrl/Shift/Alt+클릭=다중 토글 (최소 1개 유지) |
| 포맷별 비교 | 세로 바 차트 듀얼(파일 수 + 용량), 앱 토글 + 포맷 뱃지 필터(복수 선택) |
| 포맷 우선순위 | png > mat > shader > anim > prefab > controller > fbx > mesh > asset > bytes > txt |
| 포맷 기본 선택 | png, mat, shader, anim, prefab (5개), 전체 토글로 전체↔기본값 전환 |
| 포맷 선택 | 'all' 토글 유지. 그 외 포맷 클릭=solo, solo 재클릭=기본 5개 복귀, Ctrl/Shift/Alt+클릭=다중 토글 |
| 포맷 상세 | 가로 바 차트 (접기/펼치기), 포맷 뱃지 필터 |
| 차트 캡처 | 트렌드/포맷별 비교 각각 📷 버튼 + 📂 폴더 열기, html2canvas 920px |
| 히스토리 | 스캔 시 `data/vfx-history/YYYY-MM-DD.json` 자동 저장, Git 추적 |
| 백업 정보 | 경로 설정에서 히스토리 경로/일수/최근 저장/Git 커밋 시각 + 차트 캡처 저장 경로 |
| 경로 설정 | 점 9개(⋮⋮⋮) 버튼 → 앱별 VFX/Git/라벨 경로 편집, 설정 상태 유지 (`_settingsOpen`) |
| 내보내기 | 마크다운 리포트 (요약+포맷별 상세) + Dooray 업무 생성 + 차트 이미지 캡처(920px) |
| 다크 스킨 | 앱 카드 다크 블루 테마 (기본값), ☀ 버튼 토글, 차트는 기본 유지 |
| 창 크기 기억 | 앱 종료 시 `data/window-bounds.json`에 저장, 다음 실행 시 복원 |

### IPC 핸들러
| IPC | 역할 |
|-----|------|
| `scan-vfx-assets` | 재귀 디렉토리 스캔 (byExtension, byFolder) |
| `git-pull-vfx` | git pull 실행 (비동기 exec) |
| `git-status-vfx` | git fetch + rev-list 대기 커밋 수 확인 |
| `git-diff-stat` | git diff --stat HEAD@{1} (pull 변경 요약) |
| `vfx-history-save` | 날짜별 스냅샷 JSON 저장 |
| `vfx-history-load` | 전체 히스토리 로드 |
| `vfx-history-info` | 최근 파일/Git 커밋 시각 조회 |

### 앱/포맷 버튼 선택 방식 (2026-05-29 변경)

VFX Assets 차트의 모든 앱·포맷 버튼은 **클릭 = solo (해당 항목만)** 방식으로 통일되었습니다.

| 입력 | 동작 |
|------|------|
| 일반 클릭 | 해당 항목만 선택 (Solo) |
| 일반 클릭 (이미 solo 상태) | 전체 복귀 — 앱은 4개 전체, 포맷은 EXT_DEFAULT(5개) |
| Ctrl / Shift / Alt + 클릭 | 다중 선택 토글 — 이미 선택돼 있으면 제외(최소 1개 유지), 아니면 추가 |

**적용 위치**:
- 트렌드 차트: `[data-app]` 앱 버튼 → `_chartApps` 상태
- 포맷별 비교 차트: `[data-vbar-app]` 앱 버튼 → `_vbarApps` 상태, `[data-vbar-fmt]` 포맷 버튼 → `_vbarFormats` 상태
- 'all' 포맷 버튼은 전체 토글 동작 유지 (전체 ↔ 기본 5개)

**구버전 Alt Solo 모드는 제거됨**: `_trendAltApps`, `_vbarAltMode`는 코드에 남아있지만 항상 비활성. 시각 클래스(`.vad-app-alt-on`, `.vad-app-alt-dim`)도 더 이상 적용되지 않음 (CSS는 잔존).

**선택 이유**: 단일 선택이 95% 사용 시나리오라 클릭이 직관적. 다중 선택은 OS 표준(Ctrl/Shift)을 따라 명시적 의도가 있을 때만 활성.

### 트렌드 차트 꺽인선 방지

동일하게 표시되는 값(예: 모두 "8.8 MB")이 실제 바이트 미세 차이로 인해 꺽인선이 되는 버그 수정.

**원인**: `range = maxVal - minVal` 이 1KB 등 소량이 되면 그 차이가 차트 전체 높이에 매핑됨
**수정**: `range`의 최솟값을 표시 정밀도로 제한
- size 메트릭: `minRange = 104,858 bytes (0.1 MB)` — `_formatSize` 표시 단위
- 파일 수 메트릭: `minRange = 1` (정수, 기존 동작 유지)

```javascript
const minRange = metric === 'totalSize' ? 104858 : 1;
const range = Math.max(maxVal - minVal, minRange) || 1;
```

### 트렌드 차트 타입 토글 (선형 / 막대)

트렌드 헤더 컨트롤 우측에 차트 타입 토글 버튼으로 선형과 막대 차트를 전환할 수 있습니다.

**상태**: `_trendChartType: 'line'` — `'line'` | `'bar'`
**버튼**: `[fa-chart-line]` (선형) / `[fa-chart-bar]` (막대) — `.vad-chart-type-btn`
**위치**: 주말 제외 / 변화만 체크박스 오른쪽, 캡처 버튼 왼쪽

**막대 차트 동작**:
- 날짜별 그룹 막대 (grouped bar) — 앱별 색상, Y축 0 기준 (절대량 비교)
- 슬롯 너비의 72% 묶음, 앱 수로 균등 분할
- 12개 이하 날짜: 막대 위에 값 레이블 표시 (11px, 흰 배경 `rx="2"`, 딱 맞는 패딩)
- 모든 막대(작은 막대 포함)에 레이블 표시 — 기존 `bH > 14` 조건 제거
- 호버 `<title>`: 앱명 + 값 + 날짜
- 기존 앱 토글, 포맷 필터, 기간 선택 모두 연동 (앱/포맷 솔로 동작 포함)

**레이블 스타일**:
```
배경: fill="#fff" fill-opacity="0.88" rx="2"  ← 딱 맞는 패딩, 거의 각진 형태
폰트: font-size="11" font-weight="500"
위치: barY - 8 (항상 막대 위로 고정)
```

**CSS**: `.vad-chart-type-btn` — active 시 파란 배경 (`#E8F0FE`)

### 구현 위치
| 파일 | 역할 |
|------|------|
| `js/vfxAssetDashboard.js` | VfxAssetDashboard 모듈 전체, `_trendChartType` 상태, 막대 SVG 분기 |
| `electron-main.js` | IPC 핸들러 5개, 창 크기 저장/복원 |
| `electron-preload.js` | API 브릿지 |
| `js/state.js` | `vfxAssetData`, VIEW_META/ORDER/VISIBILITY 등록 |
| `index.html` | `#vfxAssetDashboardView` + script 태그 |
| `js/main.js` | switchView, init, 시작 뷰 가드 |
| `styles.css` | `.vad-*`, `.vad-app-alt-on`, `.vad-app-alt-dim`, `.vad-chart-type-btn` 스타일 |
| `data/vfx-history/` | 일별 스냅샷 JSON 파일 |

## 모바일 브리지 (Mobile Bridge) — 폰 PWA → 데스크톱 수신함

모바일(PWA)에서 **새 업무 제안**과 **회의 기록**을 입력해 보내면, 데스크톱 Teamplay 앱이 받아서 **수신함**에 쌓고, 사용자가 확인 후 처리하는 기능. **로컬 내부망(LAN)** 방식 — 외부 서버/클라우드 불필요.

### 아키텍처 (제안 → 확인 게이트 → 생성)
```
폰(같은 Wi-Fi) → http://PC-IP:8829 (Electron 내장 HTTP 서버가 PWA + API 제공)
 → POST /api/draft (새 업무 초안) / POST /api/note (회의 기록)
 → 데스크톱 수신함 → 사용자 확인/수정 → 기존 TaskCreator로 Dooray 업무 생성 + Gantt 등록
```
- **모바일은 Dooray를 직접 건드리지 않음** — 초안만 전달. Dooray 생성/Gantt 적용은 데스크톱에서 사용자가 확인한 뒤에만 발생 (오입력 방지 게이트)
- PWA가 데스크톱 서버에서 제공되므로 **모든 API가 same-origin 상대경로** → CORS·토큰노출 없음. Dooray 호출은 데스크톱(Node)에서만

### 포트 / 설정
- 기본 포트 **8829** (`config/mobile-bridge.json` — `{ enabled, port, pin }`). 사용 중이면 자동으로 +1씩 최대 20회 탐색
- PIN 설정 시 모바일이 `x-mobile-pin` 헤더로 인증 (`/api/ping` 제외)
- 폰 접속: 데스크톱 **모바일 수신함 패널 > 연결 탭**에 접속 URL 표시 (LAN IP 자동 탐지)
- 전제: 같은 Wi-Fi + 데스크톱 앱 켜짐 + 최초 Windows 방화벽 허용

### 데이터 구조 (절대보호 대상 아님, 일반 영속 데이터)
```js
AppState.pendingDrafts[] // { id, createdAt, source:'mobile', platform, project, taskName,
                         //   category, organization, startDate, endDate, releaseMonth,
                         //   planningUrl, note, author, status } status: pending|created|dismissed
AppState.meetingNotes[]  // { id, createdAt, source:'mobile', text, tag:'todo'|'share'|'notify'|'',
                         //   author, status } status: open|converted|archived
```
- save/load/backup/restore/import 전 경로 포함 (storage.js 빌드 4곳 + 로드 4곳, `guideNotes` 옆에 배치)

### 데스크톱 수신함 UI
- 사이드 패널 `모바일 수신함` (`#mobileInboxBtn`, 신규 수신 시 빨간 뱃지)
- 탭 3개: **새 업무 제안** / **회의 기록** / **연결**
- 새 업무 제안: 카드 클릭 `확인·생성` → `TaskCreator.openModalWithDraft(draft)`로 폼 프리필 → 사용자 [생성] → 기존 create() 흐름 (Dooray + Gantt). 생성 성공 시 `MobileInbox.markDraftCreated(id)`로 `created` 표시
- 회의 기록: 태그 필터(할일/공유/알림), `Task로 등록`(→ TaskCreator 프리필, 생성 시 `converted`) / `보관`(archived)

### 이벤트 전달 (메인 → 렌더러)
- 메인이 수신 → `mobileEventBuffer`에 버퍼 + `mainWindow.webContents.send('mobile-event', evt)` + (포커스 아닐 때) OS 알림
- 렌더러 `MobileBridge`: `onMobileEvent`로 실시간 수신 + 앱 로드 시 `mobileBridgeDrain()`으로 버퍼 회수 → payload.id 기준 dedupe 후 AppState에 추가 → `mobile-bridge-ack`로 버퍼 제거 → `mobile-data-changed` 커스텀이벤트 dispatch
- `MobileBridge.pushMeta()`: PWA 폼 드롭다운용 메타(플랫폼/프로젝트/카테고리/조직/팀원)를 `mobile-set-meta`로 메인에 전달 (TaskCreator 옵션 소스와 동일)

### 모바일 PWA (`mobile/` 폴더, 데스크톱 서버가 정적 제공)
- `index.html` / `app.js` / `style.css` — 하단 탭 [새 업무] [회의 기록] [설정]
- `/api/ping` 연결확인 → `/api/meta` 드롭다운 채움 → 제출 시 `/api/draft` / `/api/note` POST
- 설정: 작성자명 + PIN (localStorage 저장)
- `manifest.webmanifest` + `sw.js`(앱셸 캐시, /api는 캐시 우회) + `icon.svg` — 홈화면 설치 지원

### 구현 위치
| 파일 | 역할 |
|------|------|
| `electron-main.js` | Mobile Bridge 섹션 — `startMobileBridge()`, `handleMobileRequest()`, `serveMobileStatic()`, `pushMobileEvent()`, IPC(`mobile-bridge-info`/`-drain`/`-ack`/`mobile-set-meta`) |
| `electron-preload.js` | `mobileBridgeInfo/Drain/Ack`, `mobileSetMeta`, `onMobileEvent` 브릿지 |
| `js/mobileBridge.js` | 렌더러 수신·저장·메타전달·dedupe·접속정보 |
| `js/mobileInbox.js` | 수신함 패널 UI (탭/카드/액션/뱃지/연결안내) |
| `js/taskCreator.js` | `openModalWithDraft()`, `_setSelectEnsure()`, 생성 성공 시 `markDraftCreated` 호출 |
| `js/state.js` | `AppState.pendingDrafts`, `AppState.meetingNotes` |
| `js/storage.js` | save 4곳 + load 4곳 |
| `js/main.js` | 버튼/탭 바인딩, Escape, bringToFront 셀렉터, `MobileBridge.init()`/`MobileInbox.init()` |
| `index.html` | `#mobileInboxBtn`(+뱃지), `#mobileInboxPanel`, script 태그 |
| `styles.css` | `.mobile-inbox-panel`, `.mi-*`, `.mobile-inbox-badge` |
| `config/mobile-bridge.json` | 포트/PIN 설정 |
| `mobile/` | PWA (index.html, app.js, style.css, manifest.webmanifest, sw.js, icon.svg) |

### 클라우드 중계 (외부에서도 전송) — Cloudflare Worker + KV
LAN 방식은 사무실(같은 망)에서만 동작하므로, 외부(집·셀룰러)용으로 **클라우드 중계함**을 추가. **클라우드는 메모/초안만 7일 임시보관하는 사서함 — Dooray 토큰 안 올라감.** 데스크톱이 폴링으로 회수해 같은 모바일 수신함에 합류.
```
폰(어디서든·HTTPS) → Worker /api/draft|note → KV(7일 TTL)
데스크톱 → Worker /api/pull?since= (x-pull-secret) → pushMobileEvent → 모바일 수신함
사용자 확인 → 데스크톱이 Dooray 생성 (토큰은 데스크톱 전용)
```
- **자산 단일소스**: `mobile/`를 수정 → `node cloud/build-worker.js`로 `cloud/worker.js` 재생성(PWA 인라인) → Cloudflare 재배포
- **Worker 엔드포인트**: `/api/draft`·`/api/note`(POST, `x-mobile-pin`=WRITE_PIN), `/api/pull`(GET, `x-pull-secret`=PULL_SECRET), `/api/ping`, `/api/meta`(빈값), 정적 PWA. 항목 key=`item:<pad ts>:<id>`, 7일 TTL
- **데스크톱 폴링**: `electron-main.js` — `startCloudPoll()`/`cloudPollTick()`/`cloudHttpGetJson()`, `config/mobile-bridge.json`의 `cloud:{enabled,baseUrl,pullSecret,pollMinutes}`, 진행상태 `data/mobile-cloud-state.json`(lastTs). 회수 항목은 `pushMobileEvent()`로 LAN과 동일 파이프라인 → renderer가 `payload.id`로 중복 제거 (LAN+클라우드 동시 수신 안전)
- **연결 탭**: 사내망(LAN) + 외부(클라우드 켜짐/꺼짐) 상태 표시 (`mobile-bridge-info`의 `cloud`)
- **배포 가이드**: `cloud/README.md` (KV 바인딩 `INBOX`, Secrets `WRITE_PIN`/`PULL_SECRET`)
- **구현 위치 추가**: `cloud/worker.template.js`(로직), `cloud/build-worker.js`(생성기), `cloud/worker.js`(배포본, 생성됨), `cloud/README.md`

### 수신함 항목 삭제 (`mobileInbox.js`)
- **개별 삭제**: 각 카드 우측 상단 `×` → `_deleteDraft()`/`_deleteNote()`. 미처리(pending/open) 항목은 confirm, 처리된 항목은 즉시
- **처리됨 일괄 삭제**: 툴바 "처리됨 비우기 (N)" → `_clearProcessed()` (현재 탭의 비-pending/비-open 전부 삭제, confirm)
- 삭제는 영구(AppState에서 제거+저장). 재유입 없음 — LAN은 ack 완료, 클라우드는 lastTs 이후만 + 7일 만료

### 모바일 폼 — 프로젝트 자동채움 + 초기화
- **프로젝트 자동채움**: PWA 새 업무 폼에서 기존 프로젝트명 선택/입력 시 플랫폼·카테고리·조직·점검월·기획URL 자동 입력 (데스크톱 `loadFromExisting`과 동일: 플랫폼 일치 우선). 이를 위해 `MobileBridge.buildMeta()`의 `projects`가 `{platform,project,category,organization,releaseMonth,planningUrl}`까지 실어 보냄. 구현: `mobile/app.js:autoFillFromProject()`/`setSelectEnsure()`/`convReleaseMonth()`
  - **프로젝트 필드는 폼 첫 줄** (프로젝트→업무명→플랫폼 순). 클라우드 PWA는 meta가 비어 있어 자동채움 없음(설계상)
- **폼 초기화**: 새 업무/회의 기록 각 폼에 `[초기화]` 버튼 (`resetTaskForm()`/`resetNoteForm()`, 내용 있으면 confirm)

### 모바일 디자인 (DESIGN.md 기반 에디토리얼)
- 프로젝트 루트 **`DESIGN.md`** (= `npx getdesign add cursor` 산출물, Cursor 에디토리얼 시스템)를 기준으로 PWA 디자인 적용 → 향후 UI 작업 참고 기준
- 톤: 따뜻한 크림 캔버스(`#f7f7f4`) + 워밍 잉크(`#26251e`), **단일 강조 오렌지(`#f54e00`)는 주요 버튼/브랜드에만 절제**, 그림자 없이 1px 헤어라인, 디스플레이 400 weight + 음수 자간, 라벨 11px 대문자 트래킹, 라운드 8px(버튼/입력)·12px(카드)
- **폰트는 전부 시스템 폰트로 통일** (외부 Google Fonts 미사용 — `--sans`/`--mono` 모두 시스템 스택). placeholder의 "예:" 예시 텍스트 제거
- 태그 활성=잉크 인버전(파스텔 미사용 — DESIGN.md 규칙 준수)

### 외부 통로 대안 — Firebase (실시간) ★현재 선택
Cloudflare 대신 **Firebase**로도 외부 전송 가능(사용자 선택). **Firestore = 사서함, Dooray 토큰 미저장.** 폰은 익명 로그인 후 생성만, 데스크톱은 `onSnapshot` **실시간** 수신 후 문서 삭제. Cloudflare보다 실시간 + BREAD 친숙.
- **PWA 모드 감지**: `/api/ping` 성공→LAN, 실패+`window.FIREBASE_CONFIG` 존재→firebase 모드 (Firebase Web SDK CDN으로 `fxMobileInbox`에 `addDoc`). 설정 파일 `mobile/firebase-config.js` (템플릿 `mobile/firebase-config.example.js`)
- **데스크톱 수신**: `js/mobileBridge.js:_startFirebaseListener()` — 렌더러에서 Firebase SDK(CDN) `onSnapshot` → `_handleEvent` 동일 파이프라인(payload.id 중복제거) → `deleteDoc`. 설정 `config/mobile-bridge.json`의 `firebase:{enabled,collection,config}`, `mobile-bridge-info` IPC로 렌더러에 config 전달
- **규칙**: `firebase/firestore.rules` (create=폰, read/delete=데스크톱). 배포 `firebase/README.md` (`firebase deploy --only firestore:rules,hosting`, Spark 무료, Functions 미사용)
- **컬렉션명 3곳 일치 필수**: PWA `FX_INBOX_COLLECTION` = 데스크톱 `firebase.collection` = 규칙 `fxMobileInbox`. cloud(Cloudflare)와 **택일**(둘 중 하나만 enabled)
- LAN 서버는 `/firebase-config.js` 없으면 **빈 JS 응답**(콘솔 404 방지). CSP 없음 확인됨(CDN import 가능)
- **메타(드롭다운/자동완성) 발행**: 클라우드 모드엔 `/api/meta`가 없으므로, 데스크톱이 `MobileBridge.writeFirebaseMeta()`로 `fxMeta/current` 문서에 메타(플랫폼/프로젝트/카테고리/조직)를 올리고, PWA가 `loadMetaFirebase()`로 읽어 채움 (데스크톱과 동일한 자동완성). 규칙에 `fxMeta` read/write(인증) 추가. 데스크톱 코드 변경 → **앱 재시작** 필요
- **배포 완료 상태**: 프로젝트 `fxteamplay`, Hosting `https://fxteamplay.web.app` (Spark 무료). 배포는 루트 `firebase.json`(public=`mobile`)로 `npx firebase-tools deploy --only firestore:rules,hosting --project fxteamplay`. ⚠ hosting public이 프로젝트 폴더 밖이면("../mobile") 거부 → **루트 firebase.json 사용**
- 구현 위치 추가: 루트 `firebase.json`, `firebase/firestore.rules`, `firebase/README.md`, `mobile/firebase-config.example.js`, `mobile/firebase-config.js`(실값)

### 모바일 버전 관리 (BREAD 방식)
- **단일 소스 `mobile/version.js`**: `FX_APP_VERSION`(예 `v1.0.0`) + `FX_BUILD_DATE`. window(페이지)와 self(서비스워커) 양쪽에서 로드
- 표시: 설정 탭 하단 `#appVersion`. **새 버전 배너**: `sw.js`가 `version.js`를 importScripts→캐시명=버전이라 버전 올리면 SW 갱신 감지 → `app.js`가 상단 배너("새 버전 …준비됨 · 적용") 표시, '적용' 시 `skipWaiting`+reload
- **버전 올리는 법**: 모바일 기능 변경 시 → `mobile/version.js`의 버전+날짜 수정 + `mobile/CHANGELOG.md` 한 줄 추가 → `npx firebase-tools deploy --only hosting --project fxteamplay` (+ Cloudflare 쓰면 `node cloud/build-worker.js`)
- 규칙: PATCH=수정 / MINOR=기능 추가·개선 / MAJOR=큰 변경
- 구현 위치: `mobile/version.js`, `mobile/CHANGELOG.md`, `mobile/sw.js`(importScripts+캐시명), `mobile/app.js`(renderVersion/showUpdateBanner), `styles`(`.m-version`,`.m-update-bar`)
- **앱 이름**: `FX WORK` (manifest `name`/`short_name`, `<title>`, 헤더 `FX`+`WORK`). 변경 시 manifest + index.html + 헤더 3곳 일치
- **현재 버전 v1.0.3** (2026-06-07~08)

### PWA 캐시 갱신 — no-cache 헤더 필수 (사고 이력 2026-06-08)
앱 이름을 FX WORK로 바꿔 배포했는데 **홈 화면 아이콘 이름이 옛 "FX 수신함"으로 고정**되는 문제 발생. 원인 2가지:
1. **서비스워커가 `manifest.webmanifest`를 캐시** → 재설치해도 옛 매니페스트(이름)를 읽음 → `sw.js`에서 manifest를 SHELL 캐시에서 제외 + fetch 핸들러에서 항상 네트워크 처리
2. **Firebase Hosting 기본 `Cache-Control: max-age=3600`** → 브라우저가 manifest/sw를 1시간 캐시 → `firebase.json`의 `hosting.headers`에 `manifest.webmanifest`/`sw.js`/`version.js`/`index.html`/`firebase-config.js`를 **`no-cache, no-store, must-revalidate`** 로 지정 (⚠ Firebase 헤더 `source`는 glob — `(a|b)` 그룹 대신 **파일별 개별 엔트리**로 지정해야 적용됨)
- **교훈**: PWA 이름/아이콘/버전 변경이 즉시 반영되려면 SW가 manifest를 캐시하지 않고 + Hosting이 no-cache 헤더를 줘야 함. 이미 설치된 폰은 1회 캐시 비우기(앱 삭제만으론 브라우저 SW가 안 지워지므로 브라우저 인터넷기록 삭제 필요) 후 재설치

### 향후(미구현)
- 접속 QR 코드 표시 (현재는 URL 텍스트 + 복사)
- PWA 오프라인 전송 큐(전송 실패 시 IndexedDB 보관 후 재전송)
- (선택) 데스크톱 본체에도 DESIGN.md 톤 점진 적용

## 참고 경로
- 기존 Team Schedule Manager: `E:\_Team Schedule Manager`
- 기존 DoorayMCP: `E:\_DoorayMCP`
- Dooray MCP JAR: `E:\_DoorayMCP\dooray-mcp-server-0.2.1-all.jar`
