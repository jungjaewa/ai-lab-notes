# AI Lab Notes Manager - Development Plan

## Vision
Transform the simple uploader into a full **Git-backed CMS GUI** that lets non-Git users completely manage their MkDocs documentation site.

App name change: `AI Lab Notes Uploader` → `AI Lab Notes Manager`

## Tab Structure
```
┌──────────┬──────────┐
│  Upload  │ Projects │
└──────────┴──────────┘
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

## Phase 1: Tab Structure + Projects List

### 1-1. Refactor to Tab Layout
- Rename `UploaderApp` → `ManagerApp`
- Add `QTabWidget` with "Upload" and "Projects" tabs
- Extract upload UI into `UploadTab(QWidget)`
- Create `ProjectsTab(QWidget)`
- Window title: "AI Lab Notes Manager"
- Window size: 540×620

### 1-2. Projects Tab - Project List
Data source: parse `mkdocs.yml` nav + scan `docs/` folders

Each project card shows:
| Field | Source |
|---|---|
| Project name | mkdocs.yml nav section header |
| Document count | Count .md files in `docs/{slug}/` |
| Last updated | Most recent mtime in `docs/{slug}/` |
| Open in browser | `SITE_URL + slug` → `webbrowser.open()` |
| Delete project | Remove folder + nav entry + git push |

### 1-3. Project Delete
Safety: 2-step confirmation dialog
1. "Delete {name} and all {n} documents?"
2. Type project name to confirm

Delete flow:
1. `shutil.rmtree(docs/{slug}/)`
2. Remove project section from mkdocs.yml nav
3. git add → commit → push (via `DeleteWorker(QThread)`)

### 1-4. Upload Tab - Duplicate Detection
When user enters a project name that already exists in nav:
- Show warning: "{name} already exists. {n} files will be updated."
- Button text changes: "Upload" → "Update"
- Existing files that match names are overwritten; new files are added

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
- Accept folder drop on Upload tab → auto-fill path
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
- If uncommitted changes exist → show badge on Projects tab
- Per-project: check if any files in `docs/{slug}/` are modified

### 3-2. Recent Upload History
Parse `git log --oneline -10` for recent commits:
- Show in Upload tab or as a dropdown
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

## Class Structure (Target)

```
manager.py
├── Constants: REPO_DIR, DOCS_DIR, MKDOCS_YML, SITE_URL, STYLE
├── Utilities: find_md_files, slugify, update_mkdocs_nav, create_project_index, git_push
├── parse_projects_from_nav() → list of project info dicts
│
├── UploadWorker(QThread)       - Upload with progress
├── DeleteWorker(QThread)       - Delete project with git push
│
├── UploadTab(QWidget)          - Browse, scan, upload
├── ProjectsTab(QWidget)        - List, manage, delete projects
│   ├── ProjectCard(QFrame)     - Single project accordion item
│   └── DocRow(QWidget)         - Individual document row
│
├── MarkdownPreviewDialog(QDialog)  - Read-only .md viewer
│
└── ManagerApp(QMainWindow)     - Tab container + shared state
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
