# AI Lab Notes Manager - Development Plan

## Vision
Transform the simple uploader into a full **Git-backed CMS GUI** that lets non-Git users completely manage their MkDocs documentation site.

App name change: `AI Lab Notes Uploader` → `AI Lab Notes Manager`

## Layout
```
┌──────────────────────────────────────┐
│  Upload (left)  │  Projects (right)  │
│                 │                    │
│  Side-by-side, single page           │
└──────────────────────────────────────┘
```

---

## Phase 0: Single-Tab Uploader (DONE)

- [x] Browse/paste project path
- [x] Auto-detect project name from folder
- [x] Scan .md files (depth ≤ 1)
- [x] Checkbox selection for documents
- [x] Upload: copy files → generate index → update nav → git push
- [x] Progress percentage on Upload button
- [x] Step-by-step status log below button
- [x] Windows 11 Explorer styling (QSS)
- [x] Custom checkmark icon (QPainter)
- [x] Path normalization (backslash → forward slash)
- [x] Background thread (QThread) for non-blocking upload

---

## Phase 1: Side-by-Side Layout + Project Management (DONE)

### 1-1. Two-Panel Layout
- [x] Rename `UploaderApp` → `ManagerApp`
- [x] Side-by-side: `UploadPanel` (left) + `ProjectsPanel` (right)
- [x] Vertical 1px separator with bottom spacing
- [x] Window title: "AI Lab Notes Manager"
- [x] Window size: 920×580

### 1-2. Projects Panel - Project List
- [x] Parse `mkdocs.yml` nav + scan `docs/` folders
- [x] ProjectCard: name, doc count, last updated date
- [x] Copy button (project name → clipboard)
- [x] Copy URL button (project URL → clipboard)
- [x] Open button (browser)
- [x] Open Site button (main site URL)
- [x] "Copied!" feedback with 1.5s auto-reset

### 1-3. Project Delete
- [x] 2-step confirmation (Yes/No → type project name)
- [x] `DeleteWorker(QThread)` background deletion
- [x] Remove folder + nav entry + git push

### 1-4. Upload Panel - Improvements
- [x] Duplicate detection (warning when project exists)
- [x] Button text: "Upload" → "Update" when duplicate
- [x] Scanning feedback ("Scanning..." with processEvents)
- [x] Double-click paste on Project Path field
- [x] Double-click paste on Project Name field
- [x] Auto-refresh Projects panel after upload

### 1-5. UI Polish
- [x] Separator colors: #C5C5C5 (matches QLineEdit border)
- [x] Transparent scroll area backgrounds
- [x] Horizontal separator under title
- [x] Vertical separator with bottom margin

---

## Phase 1.5: UX Enhancements + Polish (DONE)

### 1.5-1. Upload Panel Additions
- [x] Reset button (clears path, name, file list)
- [x] Upload + Reset button row layout

### 1.5-2. Projects Panel Additions
- [x] Refresh button (re-parse mkdocs.yml + rescan docs/)
- [x] Last updated time display (YYYY-MM-DD HH:MM)
- [x] Select button (◀ icon) → fills Upload panel Project Name field
- [x] Git button → opens GitHub repo page for project
- [x] Open button → external-link icon (QPainter)
- [x] Compact card layout: name + meta on same row (2-line cards)

### 1.5-3. Signal Architecture
- [x] `ProjectCard.select_requested` → `ProjectsPanel.project_selected` → `UploadPanel.set_project_name`

### 1.5-4. App Icon & Desktop Shortcut
- [x] App icon: purple (#7B2FBE) rounded rect + white "MD" (QPainter, 64x64)
- [x] `SetCurrentProcessExplicitAppUserModelID()` for Windows taskbar icon
- [x] `.ico` file with multiple sizes (16~256px, via Pillow)
- [x] Desktop shortcut: `pythonw.exe` (no console window)

### 1.5-5. Icon System
- [x] `_icon_pen()` shared pen (#848484, 1.2px) for consistent button icons
- [x] `create_select_icon()` — left arrow ◀
- [x] `create_open_icon()` — external link ↗
- [x] `create_repo_icon()` — code brackets </>

---

## Phase 2: Dual Deploy + Change Detection + UX (DONE)

### 2-1. GitLab Dual Deploy
- [x] Added GitLab as second remote (`gitlab` → `gitlab.com/jungjaehwa1/ai-lab-notes`)
- [x] `.gitlab-ci.yml` for GitLab Pages deployment
- [x] Separate upload buttons: GitHub / GitLab (push to selected remote only)
- [x] Project card: GitHub / GitLab buttons open respective repo tree pages
- [x] Header: GitHub / GitLab buttons open respective Pages sites

### 2-2. Sync Status
- [x] Compare `origin/main` vs `gitlab/main` commit hashes (local refs, no network)
- [x] Green circle+checkmark icon = synced, orange circle+exclamation = behind
- [x] Status updates on Refresh and after upload/delete
- [x] All subprocess calls use `CREATE_NO_WINDOW` (no console flash)

### 2-3. Change Detection
- [x] `.project_sources.json` stores project → source folder mapping + created_at date
- [x] On Refresh: compare source .md files vs docs/ files by MD5 hash
- [x] Orange "N changed" badge on project card when files differ
- [x] Badge is clickable → auto-copies changed files + git push (single project)
- [x] "Update All" button in header → batch update all changed projects in one commit

### 2-4. Drag & Drop Upload
- [x] Accept folder drop on Upload panel → auto-fill path + name + scan files
- [x] `dragEnterEvent` + `dropEvent` on UploadPanel

### 2-5. Source Path Management
- [x] Source path shown on project card (gray text, clickable to change)
- [x] "Set source path..." link for projects without source path
- [x] Folder selection dialog to set/change path

### 2-6. Project Start Date
- [x] `created_at` field in project config (auto-set on first upload)
- [x] "Started: YYYY-MM-DD" shown on project card (clickable to change)
- [x] Custom calendar dialog (QPainter, not QCalendarWidget)
  - Single-click date selection (no OK button needed)
  - Month navigation (< >)
  - "Today" button to jump to current month
  - Current selection highlighted in blue, today in bold blue

### 2-7. Resizable Window
- [x] Changed from fixed 920x580 to resizable with minimum 920x580
- [x] Default size 920x700 for more vertical space

---

## Phase 2.5: Robustness & Polish (DONE)

### 2.5-1. Friendly Error Messages
- [x] `_friendly_error(msg)` translates raw git errors to user-friendly messages
- [x] Covers: not a git repo, auth failed, no internet, push rejected, lock exists, timeout, permission denied
- [x] Fallback: first line of error, truncated to 120 chars
- [x] Applied to all worker error outputs (UploadWorker, DeleteWorker, _BatchPushWorker)

### 2.5-2. Atomic JSON Write
- [x] `_save_raw_config(data)` writes to `.tmp` file first, then `os.replace()` to final path
- [x] Prevents config corruption on crash or power loss during write

### 2.5-3. Git Operation Lock
- [x] Global `_git_busy` flag with `_is_git_busy()` / `_set_git_busy()` helpers
- [x] All git-triggering actions (upload, delete, update, update all) check lock before starting
- [x] Lock set on worker start, released on worker finish
- [x] Prevents concurrent git operations that could corrupt the repo

### 2.5-4. Async Sync Status
- [x] `_SyncStatusWorker(QThread)` runs sync status check in background thread
- [x] `_update_sync_status()` creates worker instead of blocking subprocess calls
- [x] `_apply_sync_status(sync)` slot receives results and updates UI
- [x] Prevents UI freeze during git ref lookups on app start and refresh

### 2.5-5. Image Auto-Copy
- [x] `_find_referenced_images(md_path, source_folder)` parses .md files for image references
- [x] Detects `![alt](path)` and `<img src="path">` patterns
- [x] Resolves paths relative to .md file directory or source folder
- [x] Auto-copies referenced images during file copy phase in UploadWorker

### 2.5-6. Empty State UI
- [x] UploadPanel shows guided placeholder message when no project is loaded
- [x] ProjectsPanel shows guided placeholder message when no projects exist
- [x] Helps first-time users understand what to do

---

## Phase 3: Document-Level Management

### 3-1. Accordion Document View
Click project card → expand to show individual documents:
- Filename + file size
- Preview button (read-only markdown view)
- Delete individual document
- Open specific document URL in browser

### 3-2. Markdown Preview Dialog
`MarkdownPreviewDialog(QDialog)`:
- Read .md file content
- Display in `QTextEdit` (read-only, monospace)
- Window size: 600×500
- Basic rendering (headers, bold, code blocks) optional — plain text is acceptable

---

## Phase 4: Advanced Features

### 3-1. Unpublished Changes Indicator
Run `git status --porcelain` on REPO_DIR:
- If uncommitted changes exist → show badge on Projects panel
- Per-project: check if any files in `docs/{slug}/` are modified

### 3-2. Recent Upload History
Parse `git log --oneline -10` for recent commits:
- Show in Upload panel or as a dropdown
- Format: "2026-03-08 Add/update Eye Pipeline docs"

### 3-3. Deploy Status
GitHub API: `GET /repos/{owner}/{repo}/actions/runs?per_page=1`
- Show deploy status: queued / in_progress / success / failure
- Requires GitHub token (store in config or env var)
- Optional: auto-refresh every 30 seconds after push

### 3-4. Quick Edit
In-app markdown editing for small fixes:
- `QPlainTextEdit` with monospace font
- Save → overwrite file in `docs/{slug}/`
- Separate "Publish" button to git push changes
- Not a full editor — for typo fixes only

### 3-5. Image Auto-Copy (DONE — moved to Phase 2.5)

### 3-6. Tags Management
Visual interface for MkDocs tags:
- Read `tags:` metadata from each .md file frontmatter
- Display tag cloud or list
- Add/remove tags with UI (edit YAML frontmatter)

### 3-7. Project Reorder
Drag to reorder projects in nav:
- Update mkdocs.yml nav section order
- git push to apply

---

## Class Structure (Current)

```
uploader.py
├── Constants: REPO_DIR, DOCS_DIR, MKDOCS_YML, SITE_URL, GITLAB_SITE_URL,
│              REPO_URL, GITLAB_REPO_URL, GIT_REMOTES, PROJECT_CONFIG, STYLE
├── Config: load_project_sources, save_project_source, save_project_created_at,
│           remove_project_source, _load_raw_config, _save_raw_config (atomic write)
├── Utilities: find_md_files, slugify, update_mkdocs_nav, remove_project_from_nav,
│              create_project_index, parse_projects_from_nav, get_project_info,
│              project_exists_in_nav, check_project_changes, get_sync_status,
│              _friendly_error, _find_referenced_images
├── Git Lock: _git_busy, _is_git_busy, _set_git_busy
├── Icons: create_app_icon, create_checkmark_icon, create_select_icon,
│          create_open_icon, create_repo_icon, create_sync_icon,
│          create_unsync_icon, _icon_pen
│
├── UploadWorker(QThread)       - Upload with progress (supports remote selection + source_path)
├── DeleteWorker(QThread)       - Delete project with git push
├── _BatchPushWorker(QThread)   - Git push only for Update All (files pre-copied)
├── _SyncStatusWorker(QThread)  - Background sync status check (async UI)
│
├── UploadPanel(QWidget)        - Left: browse, scan, upload, drag & drop
│   ├── dragEnterEvent/dropEvent - Folder drag & drop support
│   ├── _paste_on_double_click   - Reusable double-click paste for QLineEdit
│   └── set_project_name         - Called when project selected from right panel
├── ProjectCard(QFrame)          - Project card with source path, date, change badge
│   ├── delete_requested         - Signal: name, slug
│   ├── select_requested         - Signal: name → fills Upload panel
│   ├── update_requested         - Signal: name, slug → auto-update changed files
│   ├── _change_source_path      - Folder dialog to set/change source path
│   └── _change_created_date     - Custom calendar dialog for start date
├── ProjectsPanel(QWidget)       - Right: project list + sync status + Update All
│   ├── _update_sync_status      - Check origin/gitlab commit refs + update icons
│   ├── _on_update_requested     - Single project auto-update from source
│   └── _on_update_all           - Batch update all changed projects
│
└── ManagerApp(QMainWindow)      - Resizable side-by-side layout container
```

---

## Error Message Translation
Git errors → user-friendly messages:

| Git Error | Display |
|---|---|
| `fatal: not a git repository` | "This folder is not set up correctly. Re-clone the repository." |
| `Authentication failed` | "GitHub login required. Check your credentials." |
| `Could not resolve host` | "No internet connection." |
| `nothing to commit` | (Silently skip, not an error) |
| `rejected` (push) | "Remote has newer changes. Pull first." |
