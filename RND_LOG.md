# AI Lab Notes Manager - R&D Log

## 2026-03-09: Phase 2.5 - Empty State UI
- Added guided placeholder messages for first-time users
- UploadPanel: shows instructions when no project folder is selected
- ProjectsPanel: shows onboarding message when no projects exist
- Helps users understand the app flow without external documentation

## 2026-03-09: Phase 2.5 - Image Auto-Copy
- `_find_referenced_images(md_path, source_folder)` parses .md for image references
- Regex patterns: `![alt](path)` and `<img src="path">`
- Resolves relative paths against md file directory or source folder
- UploadWorker automatically copies referenced images during file copy phase
- Moved from Phase 4 roadmap to Phase 2.5 (implemented early)

## 2026-03-09: Phase 2.5 - Async Sync Status
- Created `_SyncStatusWorker(QThread)` for background sync status checking
- `_update_sync_status()` now creates worker thread instead of blocking subprocess
- `_apply_sync_status(sync)` slot receives async results and updates UI icons
- Eliminates UI freeze on app start and Refresh (git ref lookup was blocking)

## 2026-03-09: Phase 2.5 - Git Operation Lock
- Global `_git_busy` flag prevents concurrent git operations
- `_is_git_busy()` / `_set_git_busy(busy)` helper functions
- All git-triggering actions check lock before starting (upload, delete, update, update all)
- Lock acquired on worker start, released on worker finish
- Prevents repo corruption from simultaneous git commands

## 2026-03-09: Phase 2.5 - Atomic JSON Write
- `_save_raw_config(data)` writes to `.tmp` file first, then `os.replace()` to final path
- `os.replace()` is atomic on most filesystems (NTFS included)
- Prevents `.project_sources.json` corruption on crash during write

## 2026-03-09: Phase 2.5 - Friendly Error Messages
- `_friendly_error(msg)` translates raw git errors to user-readable messages
- Covers 7 common scenarios: not a git repo, auth failed, no internet, push rejected, lock exists, timeout, permission denied
- Fallback: first line of raw error, truncated to 120 chars
- Applied to all worker error outputs (UploadWorker, DeleteWorker, _BatchPushWorker)

## 2026-03-09: Custom Calendar Dialog
- Replaced QCalendarWidget with custom QPainter-based calendar
- Single-click date selection (no OK button needed)
- Month navigation (< >) + "Today" button
- Current selection: blue background + white text
- Today: blue bold text
- Used for project start date (`created_at` in config)

## 2026-03-09: Project Start Date Tracking
- Added `created_at` field to `.project_sources.json` config
- Auto-set to today on first upload, preserved on re-uploads
- Displayed on project card as "Started: YYYY-MM-DD" (clickable to edit)
- JSON structure changed from `{slug: path}` to `{slug: {path, created_at}}`
- Backward-compatible: auto-migrates old string format to new dict format

## 2026-03-09: Drag & Drop Upload
- UploadPanel accepts folder drops (`dragEnterEvent` + `dropEvent`)
- Drop auto-fills path + name + scans files
- Only accepts directories (rejects file drops)

## 2026-03-09: Update All Button
- "Update All" button appears in header when any project has changes
- Copies all changed files from all projects → single git commit + push
- `_BatchPushWorker(QThread)` handles git operations (files pre-copied in main thread)

## 2026-03-09: Source Path Management UI
- Each project card shows source path (gray text) or "Set source path..." (blue link)
- Click to change via folder selection dialog
- Path stored in `.project_sources.json`

## 2026-03-09: Change Detection
- `check_project_changes()` compares source .md vs docs/ .md by MD5 hash
- Detects new files (`+`) and modified files (`~`), ignores docs-only files
- Orange "N changed" badge on project card (clickable → auto-update)
- `.project_sources.json` maps project slug → source folder path

## 2026-03-09: Resizable Window
- Changed `setFixedSize(920, 580)` → `setMinimumSize(920, 580)` + `resize(920, 700)`
- Window now freely resizable, more vertical space by default

## 2026-03-09: GitHub/GitLab Sync Status
- `get_sync_status()` compares `origin/main` vs `gitlab/main` commit hashes
- Green circle+checkmark icon = synced with HEAD
- Orange circle+exclamation = behind HEAD
- Icons created via QPainter (16x16): filled circle + white symbol
- Updates on Refresh and after upload/delete

## 2026-03-09: Console Window Fix
- All `subprocess.run` calls now use `creationflags=CREATE_NO_WINDOW`
- `_NO_WINDOW` constant: `subprocess.CREATE_NO_WINDOW` on Windows, `0` otherwise
- Previously: 2 console windows flashed on app start (from `get_sync_status`)

## 2026-03-09: GitLab Dual Deploy
- Added GitLab as second remote alongside GitHub
- `.gitlab-ci.yml` for MkDocs Pages deployment via GitLab CI/CD
- Separate upload buttons: GitHub (origin) / GitLab (gitlab)
- Project card: GitHub / GitLab buttons open respective repo tree URLs
- Header: GitHub / GitLab buttons open respective Pages sites
- GitLab username: `jungjaehwa1`, Pages URL: `jungjaehwa1.gitlab.io`
- Copy URL copies GitLab URL (private site)

## 2026-03-08: Desktop Shortcut
- Created `.ico` file with multiple sizes (16~256px) via Pillow
- Desktop shortcut using `pythonw.exe` (no console window on launch)
- VBScript COM automation to create `.lnk` file with custom icon

## 2026-03-08: App Icon
- Purple (#7B2FBE) rounded rect + white "MD" text via QPainter (64x64)
- `SetCurrentProcessExplicitAppUserModelID("ai-lab-notes-manager")` for Windows taskbar
- Without this, Windows shows python.exe icon instead of app icon

## 2026-03-08: Compact Project Cards
- Moved meta info (doc count, date) to same line as project name (right-aligned)
- Reduced card padding: 10px → 8px vertical, spacing 6px → 4px
- Cards now 2 rows (name+meta / buttons) instead of 3 rows

## 2026-03-08: Git Button & Open Icon
- Added "Git" text button → opens GitHub repo page (`REPO_URL + slug`)
- Added `REPO_URL` constant for GitHub tree URL
- Changed Open button from text to QPainter external-link icon (↗)
- Created `create_open_icon()` with box + arrow design

## 2026-03-08: Select Button (◀) & Icon System
- Added select button (◀ left-arrow icon) on each project card
- Click fills Upload panel's Project Name field
- Signal chain: `ProjectCard.select_requested` → `ProjectsPanel.project_selected` → `UploadPanel.set_project_name`
- Created shared `_icon_pen()` (#848484, 1.2px) for consistent icon styling
- All QPainter icons use same pen for uniform color/weight

## 2026-03-08: Reset & Refresh Buttons
- Reset button on Upload panel: clears path, name, file list, status
- Refresh button on Projects panel: re-parses mkdocs.yml + rescans docs/
- Upload time displayed as `YYYY-MM-DD HH:MM` format on each card

## 2026-03-08: Double-Click Paste & Docs Update
- Added double-click paste for all QLineEdit fields (Project Path, Project Name)
- Reusable `_paste_on_double_click()` static method for future fields
- Path field: double-click pastes clipboard, normalizes path, auto-scans if valid folder
- Name field: double-click pastes clipboard text
- Updated all project docs (CLAUDE.md, PLAN.md, RND_LOG.md, SKILLS_GUIDE.md)

## 2026-03-08: Side-by-Side Layout
- Changed from tab structure to side-by-side two-panel layout (920x580)
- Left panel: Upload (UploadPanel)
- Right panel: Projects (ProjectsPanel)
- Vertical 1px separator with bottom margin
- Removed QTabWidget, UploadTab, ProjectsTab classes
- Added UploadPanel, ProjectsPanel classes

## 2026-03-08: Project Management Features
- Added ProjectCard with Copy, Copy URL, Open, Delete buttons
- Copy: project name → clipboard with "Copied!" feedback (1.5s)
- Copy URL: project URL → clipboard with "Copied!" feedback (1.5s)
- Open: opens project page in browser
- Delete: 2-step confirmation (Yes/No → type name) + DeleteWorker background thread
- Open Site button on Projects panel header
- Auto-refresh Projects panel after upload completes

## 2026-03-08: Upload Improvements
- Duplicate detection: warns when project name exists, button changes to "Update"
- Scanning feedback: "Scanning..." label + processEvents() before blocking scan
- Transparent scroll area backgrounds (removed gray bg on project list)

## 2026-03-08: UI Separator Fixes
- Changed separator colors from #E5E5E5 to #C5C5C5 (matches QLineEdit border)
- Replaced QFrame.Shape.HLine/VLine (thick 2px sunken) with setFixedHeight(1)/setFixedWidth(1) + inline style
- Added horizontal separator under title area
- Vertical separator has 24px bottom spacing

## 2026-03-08: Phase 1 Implementation
- Refactored UploaderApp → ManagerApp
- Initially built with QTabWidget (Upload/Projects tabs)
- User feedback: changed to side-by-side layout for simultaneous view
- Added parse_projects_from_nav(), get_project_info(), remove_project_from_nav()
- Added DeleteWorker(QThread) for background project deletion

## 2026-03-08: Project Docs Created
- Created CLAUDE.md, PLAN.md, RND_LOG.md, SKILLS_GUIDE.md
- Designed Phase 1~3 roadmap for Manager app
- Registered docs in MkDocs site under "AI Lab Notes Manager" section

## 2026-03-08: Upload Progress Feature
- Added `progress_update` signal to `UploadWorker`
- Upload button shows percentage (0% → 30% file copy → 40% index → 50% nav → 60~80% git → 100%)
- Status label shows step-by-step log (e.g., "Copying research.md", "git push origin main...")

## 2026-03-08: PyQt6 Migration
**Problem**: tkinter Korean IME composition font cannot be controlled (OS-level limitation).
During Korean typing, composition characters appeared in a different/larger font than the final text.

**Attempted fixes** (all failed):
- `option_add("*Font", ...)`
- `tkfont.nametofont("TkDefaultFont").configure()`
- Various tkinter font configuration methods

**Root cause**: Windows OS controls IME composition rendering in tkinter. The font used during character composition is determined by the system, not the application.

**Solution**: Migrated entire app from tkinter to PyQt6. PyQt6 handles Korean IME natively — composition font matches the widget font.

**Side effect**: Needed to recreate checkbox styling. Native Qt checkboxes lost their checkmarks when custom QSS was applied. Fixed by generating a white checkmark PNG via QPainter at runtime and referencing it in QSS.

## 2026-03-08: Windows 11 Styling
- Applied Windows 11 Explorer-like design via QSS
- Colors: accent #0078D4, background #FFFFFF, borders #C5C5C5, text #1A1A1A
- Custom checkmark: blue background + white checkmark on checked state
- Font: Malgun Gothic 10pt (Windows Korean system font)
- All UI text in English

## 2026-03-08: Path Normalization Fix
**Problem**: Pasting paths like `D:\_Teamplay` (backslashes) didn't trigger file scanning.
Browse dialog returned forward slashes, but clipboard paste used backslashes.

**Fix**: Added `_normalize_path()` method that strips quotes and converts `\` → `/`.
Connected to `returnPressed` signal on the path input field.

## 2026-03-07: Initial Uploader (tkinter)
- Built first version with tkinter
- Features: browse folder, scan .md files, checkbox selection, git push
- UI: basic tkinter widgets, Korean labels
- Issues discovered: Korean IME font problem, path normalization needed

## 2026-03-07: MkDocs Site Setup
- Created GitHub repo: `jungjaewa/ai-lab-notes`
- Set up MkDocs Material theme with Korean/English search
- GitHub Actions auto-deploy on push to main
- First content: Eye Pipeline project docs (research.md, rnd-log.md)
- Tags plugin enabled for cross-project search

## Design Decisions

### Why MkDocs + GitHub Pages?
- Notion: blocked at work network
- Obsidian Publish: paid service
- MkDocs + GitHub Pages: free, supports PWA for mobile, full control

### Why PyQt6 over tkinter?
- Korean IME font control (primary reason)
- Better styling via QSS (Windows 11 look)
- Qt Designer available for visual UI design
- Native widget rendering on Windows

### Why Git-backed CMS approach?
- User is not familiar with Git commands
- App abstracts git add/commit/push behind a simple Upload button
- Automatic deployment via GitHub Actions
- Version history comes free with Git

### Why side-by-side instead of tabs?
- User requested simultaneous view of Upload and Projects
- No need to switch tabs to see uploaded projects
- Natural workflow: upload on left, verify on right
