# Teamplay 업무 자동화 계획서

## 문서 정보
- 작성일: 2026-03-21
- 상태: 기획 중
- 기반: PLAN.md (초기 개발 완료) 이후 자동화 확장

---

## 1. 현재 상태 (As-Is)

### 1.1 주간 업무 사이클

```
월~수                목요일 오전              목요일 오후
┌──────────┐      ┌──────────────┐      ┌──────────────┐
│ 업무 수행 │      │ 팀플레이 작성 │      │ 주간보고     │
│ Work 마크 │ ──→  │ 댓글 양식 작성│ ──→  │ 아트실 주간보고 │
│ dailyNote │      │ (Dooray)     │      │ Wiki 업데이트 │
└──────────┘      └──────────────┘      └──────────────┘
    수동               수동                 반자동(클릭)
```

### 1.2 데이터 흐름과 입력 지점

```
[Dooray 업무 등록] ──→ [팀플레이 댓글] ──→ [Sync] ──→ [Gantt/Planning]
      수동                  수동            버튼         자동 반영

[Plan Excel/Sheets] ──→ [Plan Import] ──→ [Planning 차트]
      외부 작성           버튼+선택          자동 반영

[Gantt 데이터] ──→ [Weekly] ──→ [Dooray 본문 업데이트]
     자동 수집       버튼            버튼

[Gantt 데이터] ──→ [Wiki Panel] ──→ [Dooray Wiki 페이지]
     자동 수집       버튼+선택            버튼
```

### 1.3 사용자 액션 횟수 (주간 기준)

| 작업 | 현재 방식 | 빈도 | 소요 시간 |
|------|----------|------|----------|
| Dooray 업무 등록 | 수동 (양식 직접 작성) | 수시 | 5~10분/건 |
| 팀플레이 댓글 작성 | 수동 (Dooray에서 직접) | 주 1회/인 | 15~30분 |
| Sync 실행 | 버튼 클릭 → 적용 | 주 1~2회 | 2~3분 |
| Work 마크 찍기 | Alt+Click | 매일 | 1~2분 |
| 주간보고 업로드 | 여러 버튼 순차 클릭 | 주 1회 | 5~10분 |
| Wiki 업데이트 | 스캔 → 선택 → 푸시 | 월 1~2회 | 5분 |
| Plan Import 동기화 | 모달 → 파일/URL → 동기화 | 월 1회 | 3분 |

---

## 2. 자동화 목표 (To-Be)

### 2.1 목표 상태

```
월~수                   목요일
┌──────────────┐      ┌──────────────────────────┐
│ 업무 수행     │      │ 앱 시작 → 자동 알림       │
│ Work 마크     │ ──→  │ "목요일 루틴" 원클릭 실행  │
│ dailyNote     │      │ → 모든 보고서 자동 완성   │
└──────────────┘      └──────────────────────────┘
    수동(유지)              자동/원클릭
```

### 2.2 자동화 수준 목표

| 작업 | 현재 | 목표 | 방식 |
|------|------|------|------|
| Dooray 업무 등록 | 수동 | **반자동** | Gantt에서 Task 추가 → Dooray 자동 등록 |
| 팀플레이 댓글 작성 | 수동 | **자동 생성** | Work 마크 + dailyNote → 댓글 초안 자동 생성 |
| Sync 실행 | 버튼 | **자동** | 백그라운드 폴링 또는 앱 시작 시 자동 |
| Work 마크 | Alt+Click | 유지 (수동) | 이것이 핵심 입력 — 자동화 불필요 |
| 주간보고 | 다단계 클릭 | **원클릭** | 목요일 루틴 자동 실행 |
| Wiki 업데이트 | 다단계 클릭 | **자동 감지** | 변경 감지 → 알림 → 원클릭 적용 |
| Plan Import | 다단계 클릭 | **자동 비교** | 앱 시작 시 자동 비교 → 변경 알림 |
| 데이터 불일치 감지 | 수동 확인(U키) | **자동 알림** | Sync 후 자동 검증 → 토스트 알림 |

---

## 3. 자동화 단계

### Phase A: 자동 감지 + 알림 (기반)

> 사람의 클릭을 기다리지 않고, 앱이 먼저 상황을 파악하여 알려준다.

#### A-1. 앱 시작 시 자동 Sync
- **기획 상태**: 구현 완료
- **동작**: `init()` 완료 3초 후 이번 주 팀플레이 자동 검색 → 댓글 조회 → 결과 자동 적용
- **설정**: Automation 패널에서 `autoSyncOnStart` on/off
- **표시**: Automation 패널 "마지막 Sync: YYYY.MM.DD HH:MM"
- **적용 항목**: 새 업무(+배지), 완료 처리(+배지), Work 마크(+배지), 제목/프로젝트 변경
- **안전성**: 추가 전용(additive) — 기존 데이터 삭제/덮어쓰기 없음
- **수정 파일**: `automationPanel.js` (_runAutoSync)

#### A-2. 백그라운드 자동 Sync (폴링)
- **기획 상태**: 구현 완료
- **동작**: 설정된 간격(10~120분)으로 A-1과 동일한 자동 Sync 반복 실행
- **설정**: Automation 패널에서 `backgroundPolling` on/off + `pollingInterval` 간격 선택
- **변경 감지**: 변경사항 있으면 토스트 알림 ("자동 Sync: 신규 N건, Work N건")
- **상태 표시**:
  - 독립 플로팅 뱃지 (`#autoSyncFloat`): Hook Polling 왼쪽, 초록색 테두리/배경, `Sync MM:SS` 카운트다운 / `Sync 중` 스피너
  - Automation 패널: "다음 Sync: N분 N초 후" 초록색 배경(`#E6F4EA`) + 펄스 점(`.atp-sync-pulse`)
- **수정 파일**: `automationPanel.js` (_startPolling, _startStatusRefresh, _updateSyncIndicator, _updateSyncCountdown), `index.html` (#autoSyncFloat), `styles.css` (.auto-sync-float)

#### A-3. 목요일 자동 알림 + 팀플레이 자동 생성
- **기획 상태**: 구현 완료
- **동작**: 앱 시작 시 오늘이 목요일이면
  - "주간보고 준비" 토스트 알림 표시 (팀플레이 생성 + Weekly 열기 버튼)
  - Automation Panel의 목요일 루틴 섹션에 "🔥𝗙𝗫 [팀플레이] 생성" 버튼
- **목요일 카운트다운**: 다음 목요일 09:00까지 남은 시간 표시 (초록색 배경 + 펄스 점)
  - `_calcThursdayCountdown()` — 남은 일/시간/분 계산
  - 매분 자동 갱신 (`_startStatusRefresh` 타이머)
- **팀플레이 자동 생성 흐름**:
  1. 다음 주 팀플레이가 이미 있는지 확인 (중복 방지)
  2. 이번주 팀플레이 검색 → dooray:// 링크 생성
  3. 새 업무 생성 (제목 + 본문 + 담당자)
  4. 이번주 정재화 댓글을 새 업무에 자동 복사
- **댓글 정리 옵션** (`cleanPrevComment`):
  - 팀 공유사항에 "완료" 텍스트 → 해당 프로젝트 블록 제외
  - Dooray API `workflowClass === 'closed'` → 해당 프로젝트 블록 제외
  - 나머지 블록: 금주 진행내용/다음주 액션/이슈/팀 공유사항 초기화
  - `"closed"` 링크 힌트로 빠른 판별 + API fallback
- **예약 자동 생성**:
  - `scheduledCreateEnabled/Day/Hour/Minute` 4개 플래그
  - `_scheduleTimer` 매분 체크, 하루 1회 제한 (localStorage)
  - 놓친 예약 보완: 앱 시작 시 예약 시간 지났으면 confirm 알림
- **제목 형식**: `🔥𝗙𝗫 [팀플레이] {year}.{month}월 {week}주차 ({monday}~{friday})`
- **주차 계산**: `Utils.getWeekInfo()` 공통 함수 사용 (금요일 기준 월 판정)
- **선행 조건**: 없음
- **수정 파일**: `automationPanel.js` (createTeamplayPost, _processCommentForNewWeek, _checkScheduledCreation), `state.js`, `styles.css`

#### A-4. Planning vs Gantt 괴리 감지
- **기획 상태**: 미착수
- **동작**: Planning Planned가 있는데 Gantt에 실제 Task가 없는 프로젝트 / 그 반대 자동 감지
- **표시**: Planning 차트에 "미매칭" 뱃지 또는 Analytics에 괴리 리포트
- **주기**: `App.render()` 시 자동 계산
- **선행 조건**: 없음
- **수정 파일**: `planningOverview.js` 또는 `analytics.js`, 새 감지 함수

#### A-5. Plan Import 자동 비교
- **기획 상태**: 구현 완료
- **동작**: Google Sheets URL이 설정되어 있으면 앱 시작 5초 후 자동 비교 (데이터 변경만 확인, 적용 안 함)
- **설정**: Automation 패널에서 `planImportAutoCompare` on/off
- **비교 결과 표시**:
  - Automation 패널: 추가(+N)/변경(~N)/삭제(-N) 카운트 + 시각 + "열기" 버튼
  - 사이드 패널: Plan Import 버튼에 빨간 뱃지 (변경 총 건수)
  - 변경 있을 때 토스트 알림
- **구현**: `PlannedImport.autoCompare()` (headless), `AutomationPanel._runPlanAutoCompare()`, `_updatePlanImportBadge()`
- **선행 조건**: 없음 (기존 PlannedImport 모듈 활용)
- **수정 파일**: `plannedImport.js` (autoCompare), `automationPanel.js` (_runPlanAutoCompare, UI), `styles.css`

---

### Phase B: 입력 자동화 (핵심)

> 사람이 직접 타이핑/작성하는 부분을 줄인다. 가장 큰 시간 절약.

#### B-1. Work 마크 → 팀플레이 댓글 자동 생성 (역방향 Sync)
- **기획 상태**: 미착수
- **현재 흐름**: 팀원이 Dooray 댓글 작성 → Sync로 가져옴
- **목표 흐름**: Work 마크 + dailyNote → 댓글 양식 자동 생성 → Dooray POST
- **데이터 소스**:
  - `AppState.workLogs[taskId][dateStr]` — 어떤 날에 작업했는지
  - `AppState.dailyNotes["taskId_YYYY-MM-DD"]` — 작업 내용 메모
  - `task.platform`, `task.project`, `task.name` — 업무 식별
  - `task.url` — Dooray 링크
- **생성 양식**:
  ```markdown
  [프로젝트코드/번호 𝗙𝗫 [플랫폼] 프로젝트 [작업] Task명](dooray://...)

  | No | 금주 진행내용 | 다음주 주요 액션 | 이슈 | 팀 공유사항 |
  | --- | --- | --- | --- | --- |
  | 1 | MM.DD 작업내용 | | | |
  | 2 | MM.DD 작업내용 | | | |
  ```
- **미리보기**: 생성된 댓글 미리보기 → 수정 가능 → "다음주 액션", "이슈" 직접 입력 → POST
- **장점**: 팀원이 15~30분 걸리는 댓글 작성이 2~3분으로 단축
- **주의**: dailyNote 미입력 시 날짜만 표시 (내용 빈칸)
- **선행 조건**: 없음 (기존 데이터 활용)
- **수정 파일**: 새 모듈 `js/commentGenerator.js`, UI 모달, `syncManager.js` (POST)

#### B-2. Gantt → Dooray 업무 자동 등록
- **기획 상태**: 미착수
- **현재**: Dooray에서 수동으로 업무 생성 → 양식 본문 작성 → Teamplay에서 Sync
- **목표**: Gantt에서 Task 추가(isLocal) → "Dooray 등록" 버튼 → 자동 업무 생성
- **자동 채움 필드**:
  - 제목: `𝗙𝗫 [platform] project [작업] task`
  - 본문: 카테고리/조직/일정/점검월 양식 자동 생성
  - 담당자: `task.assignee` → Dooray memberId 매칭
- **결과**: Dooray 업무 URL 자동 반영 → `isLocal` 해제
- **선행 조건**: 업무 등록 양식(본문 템플릿) 표준화
- **수정 파일**: `syncManager.js` (POST), `main.js` (UI), Task 편집 모달
- **참고**: QA 등록(`qaRegister.js`)이 유사 패턴의 프로토타입

#### B-3. 본문 양식 자동 생성 강화
- **기획 상태**: 미착수
- **현재**: Dooray 업로드(Upload) 시 조직/일정/점검월만 치환
- **목표**: 업무 등록 시 전체 본문 양식을 자동 생성
  ```
  * 카테고리: {category}
  * 조직: {planning}
  * 일정: {startDate}~{endDate} ({md}MD)
  * 점검월: {releaseMonth}
  * 위키: [위키 링크](...)
  * 기획: [기획 링크](...)
  ```
- **선행 조건**: B-2와 함께 진행
- **수정 파일**: `syncManager.js` (buildNewBody 함수)

---

### Phase C: 워크플로우 통합 (최종)

> 여러 단계를 하나의 흐름으로 묶어 원클릭으로 실행한다.

#### C-1. 주간보고 작성 (원클릭 자동화)
- **기획 상태**: ~~미착수~~ **구현 완료** (2026-03-22)
- **동작**: "주간보고 작성" 버튼 하나로 아래 단계를 순차 자동 실행
- **루틴 대상 선택**: `routineTarget` ('teamplay' | 'artteam') 라디오로 선택
  - **팀플레이 (FX팀)**: Step 4 = `WeeklyReportGenerator.updatePost()` — 기존 업무 본문 PUT
  - **아트실 주간보고**: Step 4 = `_routineStepArtTeam()` — Dooray 새 업무 POST (주간 요약 + 표)
  ```
  Step 1. Sync (팀플레이 동기화)     — 팀플레이 검색 → syncComments → 변경 적용
       ↓
  Step 2. 댓글 조회 + 파싱          — headless fetchWeeklyReportComments
       ↓
  Step 3. 표 생성 (Weekly)          — WeeklyReportGenerator.updateTable()
       ↓
  Step 4a. 본문 업데이트 (Dooray)    — [팀플레이] WeeklyReportGenerator.updatePost()
  Step 4b. 아트실 주간보고 생성      — [아트실] Dooray POST (주간 요약 + 표)
  ```
- **대상 선택 UI**: `.atp-routine-target-row` 라디오 버튼 (배경 제거, 목요일 아닌 날 딤 처리)
- **파이프라인 UI**: 각 단계별 프로그레스바 + 상태 아이콘(대기/진행/완료/오류) + 결과 텍스트
- **진입점**: Automation 패널 "주간보고 작성" 버튼(보라색) + 목요일 토스트 "주간보고 작성" 버튼
- **딤 처리**: 목요일 아닌 날 `.atp-routine-dimmed` (opacity 0.45, hover 시 0.8)
- **상태 힌트**: `_getRoutineStatusHint()` — 목요일 미작성/작성완료(시각)/수동실행 표시
- **headless Weekly**: localStorage('weeklyReportSettings')에서 설정 로드 — UI 조작 불필요
- **오류 처리**: 해당 단계에서 멈춤 + 오류 메시지 표시 (이전 단계 결과 보존)
- **완료 시**: "Dooray 열기" 버튼으로 업데이트된 업무 확인
- **수정 파일**: `js/automationPanel.js` (`runThursdayRoutine()`, `_routineStep*()`, `_routineStepArtTeam()`, `_calcThursdayCountdown()`, `_getRoutineStatusHint()`)
- **CSS**: `styles.css` `.atp-rt-*`, `.atp-btn-routine`, `.atp-routine-target-row`, `.atp-routine-radio`, `.atp-routine-dimmed`, `.atp-routine-status`, `.atp-thursday-countdown`, `.atp-divider`

#### C-2. 변경 감지 통합 대시보드
- **기획 상태**: 미착수
- **동작**: 앱 시작 시 한 화면에 모든 변경사항/해야 할 일을 표시
  - Sync 후 변경사항 (새 업무, 완료, Work 마크)
  - Planning vs Gantt 괴리
  - 지연/오늘/금주 Task 요약
  - Plan Import 변경사항
  - 주간보고 상태 (미작성/작성완료)
- **기존 연동**: Smart Filter + Member Dashboard + Analytics 데이터 통합
- **선행 조건**: Phase A 전체 완료
- **수정 파일**: 새 모듈 또는 기존 Analytics 확장

---

## 4. 기반 정리 작업

> 자동화 개발 전에 정리해야 하는 사항들

### 4.1 바둑 프로젝트 지원

| 항목 | 현재 상태 | 필요 작업 |
|------|----------|----------|
| 플랫폼 등록 | 미등록 | Settings > 플랫폼 관리에 바둑 플랫폼 6종 추가 |
| 조직 매핑 | 미등록 | 바둑 조직 → 보고서 그룹 매핑 추가 |
| 제목 파싱 | 포커 패턴 중심 | `[게임명] N월 > 제목` 패턴 파싱 검증 |
| planningTitle | `N월 업데이트 > ` 제거 | 바둑 패턴도 동일 동작 확인 |
| Guide Panel | 초기 콘텐츠 작성 완료 | 실제 사용하며 내용 보완 |

### 4.2 API 호출 관리

| 항목 | 현재 상태 | 필요 작업 |
|------|----------|----------|
| API 호출 | 개별 fetch 산재 | 공통 API 레이어 정리 (에러 핸들링 통일) |
| 쓰로틀링 | 없음 | 자동 Sync 도입 시 호출 빈도 제한 필요 |
| 오프라인 대응 | 없음 | API 실패 시 재시도 큐 또는 오프라인 모드 |

### 4.3 데이터 표준화

| 항목 | 현재 상태 | 필요 작업 |
|------|----------|----------|
| 본문 양식 | 파싱으로 추출 | 생성용 양식 템플릿 정의 (B-2, B-3용) |
| 댓글 양식 | 팀원별 상이 (MD/HTML) | 자동 생성 시 통일된 양식 사용 (B-1용) |
| memberId 매핑 | Dooray CC에서 추출 | Task assignee → Dooray memberId 매핑 테이블 |

---

## 5. 우선순위 및 의존성

```
[기반 정리] ─────────────────────────────────────────────
  4.1 바둑 플랫폼/조직 등록 .............. 즉시 가능
  4.2 API 호출 관리 ...................... Phase A 전에
  4.3 데이터 표준화 ...................... Phase B 전에

[Phase A: 자동 감지] ────────────────────────────────────
  A-1 앱 시작 시 자동 Sync ←─── 4.2 API 관리
  A-2 백그라운드 폴링 ←────────── A-1
  A-3 목요일 알림 ...................... 독립
  A-4 Planning-Gantt 괴리 감지 ........ 독립
  A-5 Plan Import 자동 비교 ........... 독립

[Phase B: 입력 자동화] ──────────────────────────────────
  B-1 댓글 자동 생성 ←───── 4.3 데이터 표준화
  B-2 Dooray 업무 등록 ←──── 4.3, B-3
  B-3 본문 양식 자동 생성 ←── 4.3

[Phase C: 워크플로우 통합] ──────────────────────────────
  C-1 목요일 루틴 ←──── A-1, B-1 (선택)
  C-2 통합 대시보드 ←──── Phase A 전체
```

---

## 6. 기대 효과

### 6.1 시간 절약 (주간 기준)

| 작업 | 현재 | 목표 | 절약 |
|------|------|------|------|
| 팀플레이 댓글 작성 (3명) | 60~90분 | 10분 | **50~80분** |
| Sync + 검증 | 5~10분 | 0분 (자동) | **5~10분** |
| 주간보고 + 아트실 + Wiki | 15~20분 | 2분 (원클릭) | **13~18분** |
| Plan Import 확인 | 5분/월 | 0분 (자동 알림) | **5분/월** |
| **주간 합계** | **~120분** | **~12분** | **~108분** |

### 6.2 품질 향상

| 항목 | 개선 |
|------|------|
| 데이터 정확도 | Work 마크가 단일 소스 → 댓글과 Gantt 일치 |
| 누락 방지 | 자동 감지가 빠진 항목을 미리 알려줌 |
| 양식 통일 | 자동 생성으로 포맷 불일치 제거 |
| 실시간성 | 자동 Sync로 항상 최신 상태 유지 |

---

## 7. 위험 요소

| 위험 | 영향 | 대응 |
|------|------|------|
| Dooray API 호출 제한 | 자동 Sync 차단 | 쓰로틀링 + 최소 간격 설정 |
| 자동 생성 댓글 품질 | 팀원 신뢰 저하 | 반드시 미리보기 + 수동 보완 단계 유지 |
| 자동 등록 오류 | Dooray에 잘못된 데이터 | 되돌리기(Undo) 지원 + 미리보기 필수 |
| 양식 변경 | 파싱/생성 로직 깨짐 | Guide Panel에 양식 문서화 + 테스트 케이스 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-21 | 최초 작성 — 현재 상태 분석 + 3단계 자동화 계획 |
| 2026-03-21 | Automation Panel 구현 — Feature Flag 시스템 + 사이드 패널 + 목요일 알림 |
| 2026-03-21 | 팀플레이 자동 생성 — 이전주 검색 + 새 업무 POST + 정재화 댓글 복사 |
| 2026-03-21 | 주차 계산 통합 — Utils.getWeekInfo() 공통 함수, report.js/main.js 2곳 통합 |
| 2026-03-22 | 댓글 정리 옵션 — 완료 프로젝트 제외(텍스트+API), 데이터 컬럼 초기화 |
| 2026-03-22 | 예약 팀플레이 자동 생성 — 요일/시간 설정, 놓친 예약 보완 |
| 2026-03-22 | A-1/A-2 구현 완료 — 자동 Sync 실제 연결, 새 업무/완료/Work 마크/변경 자동 적용 |
| 2026-03-22 | Sync 상태 표시 — 시계 옆 카운트다운 + Automation 패널 실시간 갱신 |
| 2026-03-22 | A-4 구현 완료 — Planned ↔ Gantt 프로젝트 수동 연결 (importKey 보존 + Plan Import 2단계 매칭) |
| 2026-03-22 | A-5 구현 완료 — Plan Import 자동 비교 (headless Sheets 비교 + 사이드 뱃지 + Automation 패널 결과) |
| 2026-03-22 | C-1 루틴 대상 선택 — 팀플레이(FX팀) vs 아트실 주간보고 라디오 선택 + `_routineStepArtTeam()` |
| 2026-03-22 | "아트실 보고서" → "아트실 주간보고" 전체 rename (index.html, main.js, styles.css, CLAUDE.md 등) |
| 2026-03-22 | 목요일 루틴 UI 재정리 — 흐름별 그룹핑, 구분선, 카운트다운 통합 |
| 2026-03-22 | "루틴 실행" → "주간보고 작성" rename + 상태 힌트 + 딤 처리 (목요일 외) |
| 2026-03-22 | 팀플레이 생성 텍스트 → "🔥𝗙𝗫 [팀플레이] 생성" |
| 2026-03-22 | 목요일 카운트다운 추가 — 다음 목요일까지 남은 시간, 초록 배경 + 펄스 점 |
| 2026-03-22 | 다음 Sync 카운트다운 초록색 + 펄스 점 + 배경 (#E6F4EA) |
| 2026-03-22 | Auto Sync 플로팅 독립 배치 — `#autoSyncFloat` (hookPolling 왼쪽, 동적 위치) |
| 2026-03-22 | Plan Import 삭제 감지 버그 수정 — 연결된/중복 Placeholder 오판정 (importKeyShortMap + sibling check) |
| 2026-03-22 | "목요일 알림" → "목요일 알림 메시지 안내" rename, 섹션 맨 아래로 이동 |
