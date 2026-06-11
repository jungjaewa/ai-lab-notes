# Teamplay

FX팀 업무 통합 관리 도구 — Dooray 기반 업무 트래킹 + Gantt 차트 + 보고서 자동화

## 개요

소규모 팀(3명)의 업무 진행사항을 실시간으로 추적하고, 주간/월간 보고서를 자동 생성하는 Electron 데스크톱 애플리케이션입니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| **Gantt 차트** | Task 일정 관리, 진행률 추적, 기간 바 시각화 |
| **Dooray 동기화** | 댓글 파싱 → Task/Work 마크 자동 반영 |
| **Planning 차트** | 월별 프로젝트 배치 현황, Planned 프로젝트 관리 |
| **보고서 자동화** | 주간/월간 보고서 생성, 아트실 주간보고 자동 작성 |
| **Team 차트** | 팀 공통 일정 (회의, 교육, 면담 등) 관리 |
| **Analytics** | 팀원별 참여 현황, 월별 프로젝트/작업 통계 |
| **Smart Filter** | 지연/오늘/금주/수정 업무 알림 및 필터링 |
| **Work History** | 팀원별 기간별 작업 이력 조회 및 복사 |
| **Wiki 자동 생성** | Dooray 위키 페이지 자동 생성/업데이트 |
| **Plan Import** | Excel/Google Sheets → Planned 프로젝트 자동 등록 |

## 기술 스택

- **Electron** — 데스크톱 앱 프레임워크
- **Vanilla JS** — 프레임워크 없는 순수 JavaScript
- **Dooray MCP** — Dooray API 연동 (업무/댓글/위키)
- **SheetJS** — Excel 읽기/쓰기

## 설치 및 실행

```bash
git clone https://github.com/jungjaewa/teamplay.git
cd teamplay
npm install
npm start
```

## 데이터 복원

앱 데이터(Task, 작업기록 등)는 별도 저장소에서 관리됩니다.

1. `teamplay-data` 저장소에서 `Teamplay_latest.json` 다운로드
2. 앱 실행 → Backup 모달(B) → Import

## 프로젝트 구조

```
├── electron-main.js       # Electron 메인 프로세스
├── electron-preload.js    # IPC 브릿지
├── index.html             # 메인 UI
├── styles.css             # 스타일
├── js/
│   ├── main.js            # 앱 초기화 + 이벤트
│   ├── state.js           # 상태 관리
│   ├── storage.js         # 데이터 저장/로드
│   ├── dooray/            # Dooray 연동 (파싱, 동기화)
│   ├── views/             # 뷰 (Gantt, Planning, Team 등)
│   └── reports/           # 보고서 생성
├── config/                # 설정 (Git 제외)
└── data/                  # 로컬 데이터 (Git 제외)
```

## 문서

| 파일 | 내용 |
|------|------|
| [PLAN.md](PLAN.md) | 프로젝트 계획서 + 백업 체계 |
| [PLAN-AUTOMATION.md](PLAN-AUTOMATION.md) | 업무 자동화 계획 |
| [CLAUDE.md](CLAUDE.md) | Claude Code 개발 가이드 |
