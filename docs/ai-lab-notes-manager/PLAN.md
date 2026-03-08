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

## Phase 2: Document-Level Management

### 2-1. Accordion Document View
Click project card → expand to show individual documents:
- Filename + file size
- Preview button (read-only markdown view)
- Delete individual document
- Open specific document URL in browser

### 2-2. Markdown Preview Dialog
`MarkdownPreviewDialog(QDialog)`:
- Read .md file content
- Display in `QTextEdit` (read-only, monospace)
- Window size: 600×500
- Basic rendering (headers, bold, code blocks) optional — plain text is acceptable

### 2-3. Drag & Drop Upload
- Accept folder drop on Upload panel → auto-fill path
- `dragEnterEvent` + `dropEvent` on the main widget

### 2-4. Change Detection on Upload
Compare source files with existing `docs/{slug}/` files:
- NEW: file doesn't exist in destination
- MODIFIED: file exists but content differs
- UNCHANGED: identical content (skip copy)
- Display status icon next to each checkbox

---

## Phase 3: Advanced Features

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

### 3-5. Image Auto-Copy
When uploading .md files that reference local images:
- Parse `![alt](path)` and `<img src="path">` patterns
- Auto-copy referenced images to `docs/{slug}/`
- Update image paths in copied .md files

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
├── Constants: REPO_DIR, DOCS_DIR, MKDOCS_YML, SITE_URL, REPO_URL, STYLE
├── Utilities: find_md_files, slugify, update_mkdocs_nav, remove_project_from_nav,
│              create_project_index, parse_projects_from_nav, get_project_info,
│              project_exists_in_nav
├── Icons: create_app_icon, create_checkmark_icon, create_select_icon,
│          create_open_icon, create_repo_icon, _icon_pen
│
├── UploadWorker(QThread)       - Upload with progress signals
├── DeleteWorker(QThread)       - Delete project with git push
│
├── UploadPanel(QWidget)        - Left: browse, scan, upload, reset
│   ├── _paste_on_double_click  - Reusable double-click paste for QLineEdit
│   └── set_project_name        - Called when project selected from right panel
├── ProjectCard(QFrame)         - Project card with ◀/Copy/CopyURL/↗/Git/Delete
│   ├── delete_requested        - Signal: name, slug
│   └── select_requested        - Signal: name → fills Upload panel
├── ProjectsPanel(QWidget)      - Right: project list + refresh + management
│   └── project_selected        - Signal: name (relays from ProjectCard)
│
└── ManagerApp(QMainWindow)     - Side-by-side layout container
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
