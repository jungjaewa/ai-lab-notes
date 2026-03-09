# AI Lab Notes Manager

## Project Overview
Git-backed CMS desktop app (PyQt6) for managing MkDocs documentation.
Abstracts all Git operations so non-Git users can upload, manage, and publish markdown documents to GitHub Pages.

## Architecture
```
Local project folder → [App] → ai-lab-notes git repo → GitHub/GitLab → MkDocs Pages
```

- **Runtime**: Python 3.12 + PyQt6
- **Backend**: Local git repo, mkdocs.yml nav parsing, shutil file copy
- **Deploy**: GitHub Actions + GitLab CI/CD auto-deploy on push to main
- **Sites**:
  - GitHub Pages (public): https://jungjaewa.github.io/ai-lab-notes/
  - GitLab Pages (private): https://jungjaehwa1.gitlab.io/ai-lab-notes/

## Key Files
| File | Purpose |
|---|---|
| `uploader.py` | Main app (PyQt6 GUI + all logic) |
| `mkdocs.yml` | MkDocs config + navigation structure |
| `docs/` | All published markdown documents |
| `docs/{project_slug}/` | Per-project document folders |
| `.github/workflows/deploy.yml` | GitHub Actions auto-deploy |
| `.gitlab-ci.yml` | GitLab CI/CD auto-deploy |
| `.project_sources.json` | Local config: project → source path + created_at (gitignored) |

## Constants
- `REPO_DIR` = script directory (ai-lab-notes root)
- `DOCS_DIR` = `REPO_DIR/docs/`
- `MKDOCS_YML` = `REPO_DIR/mkdocs.yml`
- `SITE_URL` = `https://jungjaewa.github.io/ai-lab-notes/`
- `GITLAB_SITE_URL` = `https://jungjaehwa1.gitlab.io/ai-lab-notes/`
- `REPO_URL` = `https://github.com/jungjaewa/ai-lab-notes/tree/main/docs/`
- `GITLAB_REPO_URL` = `https://gitlab.com/jungjaehwa1/ai-lab-notes/-/tree/main/docs/`
- `GIT_REMOTES` = `["origin", "gitlab"]`
- `PROJECT_CONFIG` = `.project_sources.json`

## Core Functions
| Function | Purpose |
|---|---|
| `find_md_files(folder)` | Walk folder (depth ≤ 1), return .md files |
| `slugify(text)` | Project name → URL-safe slug |
| `update_mkdocs_nav()` | Parse mkdocs.yml, insert/update project nav entries |
| `remove_project_from_nav()` | Remove project section from mkdocs.yml nav |
| `create_project_index()` | Generate index.md with document table |
| `parse_projects_from_nav()` | Parse nav → list of {name, slug, nav_doc_count} |
| `get_project_info(slug)` | Scan docs folder → {doc_count, last_updated, total_size} |
| `project_exists_in_nav()` | Check if project name already in nav |
| `load_project_sources()` | Load project config (path + created_at) from JSON |
| `save_project_source()` | Save source path + auto-set created_at on first upload |
| `save_project_created_at()` | Save/update project start date |
| `check_project_changes()` | Compare source vs docs files by MD5 hash |
| `get_sync_status()` | Compare origin/main vs gitlab/main commit hashes |
| `create_app_icon()` | QPainter app icon: purple rounded rect + white "MD" |
| `create_select_icon()` | QPainter left-arrow icon for select button |
| `create_open_icon()` | QPainter external-link icon for open button |
| `create_repo_icon()` | QPainter code-bracket icon for repo button |
| `create_sync_icon()` | Green circle + white checkmark (synced) |
| `create_unsync_icon()` | Orange circle + white exclamation (unsynced) |
| `_icon_pen()` | Shared pen (#848484, 1.2px) for all button icons |
| `_friendly_error(msg)` | Translate raw git errors → user-friendly messages |
| `_is_git_busy()` | Check global git operation lock |
| `_set_git_busy(busy)` | Set/release global git operation lock |
| `_save_raw_config(data)` | Atomic JSON write (`.tmp` → `os.replace()`) |
| `_find_referenced_images(md_path, source_folder)` | Parse `![](path)` and `<img src="">` in .md, return referenced image paths |

## Classes
| Class | Purpose |
|---|---|
| `UploadWorker(QThread)` | Background upload with progress signals (supports remote selection) |
| `DeleteWorker(QThread)` | Background project deletion with git push |
| `_BatchPushWorker(QThread)` | Git add/commit/push for Update All (files already copied) |
| `_SyncStatusWorker(QThread)` | Background thread for sync status check (prevents UI freeze) |
| `UploadPanel(QWidget)` | Left panel: browse, scan, upload, drag & drop |
| `ProjectCard(QFrame)` | Project card with source path, start date, change badge, actions |
| `ProjectsPanel(QWidget)` | Right panel: project list + sync status + Update All |
| `ManagerApp(QMainWindow)` | Main window with side-by-side layout (resizable) |

## Layout
```
┌───────────────────────────────────────────────────────────┐
│ [MD] AI Lab Notes Manager                                  │
│ AI Lab Notes                                               │
│ Manage your project documentation                          │
│───────────────────────────────────────────────────────────│
│ Upload              │ Projects  Refresh ●GitHub ●GitLab    │
│                     │                         [Update All] │
│ Project Path        │ ┌──────────────────────────────────┐│
│ [__________] Browse │ │ PSD          [3 changed]  13files││
│                     │ │ D:/_AI Tool/PSD    Started:02-21 ││
│ Project Name        │ │ ◀ Copy CopyURL GitHub GitLab  Del││
│ [__________]        │ └──────────────────────────────────┘│
│                     │ ┌──────────────────────────────────┐│
│ Documents Found     │ │ Eye Pipeline           2 files   ││
│ ┌─────────────────┐ │ │ Set source path...  Set start... ││
│ │ ☑ file1.md      │ │ │ ◀ Copy CopyURL GitHub GitLab Del││
│ │ ☑ file2.md      │ │ └──────────────────────────────────┘│
│ └─────────────────┘ │                                      │
│                     │                                      │
│ [GitHub][GitLab]    │                                      │
│ [Reset]             │                                      │
│ Ready               │ 4 projects                           │
└───────────────────────────────────────────────────────────┘
```

## Style
- Windows 11 Explorer aesthetic (accent #0078D4, bg #FFFFFF, borders #C5C5C5)
- Font: Malgun Gothic 10pt (Korean system font)
- UI text: English only
- Custom checkmark icon via QPainter → temp PNG → QSS `image: url()`
- Separators: 1px solid #C5C5C5 (matches QLineEdit border)
- App icon: purple (#7B2FBE) rounded rect + white "MD" text (QPainter, 64x64)
- Button icons: QPainter-drawn, #848484 color, 1.2px line width
- Desktop shortcut: `pythonw.exe` (no console window)

## Conventions
- Path normalization: always convert `\` → `/` for display
- Project slug: lowercase, hyphens, preserves Korean characters
- Nav structure: projects inserted before `tags.md` line in mkdocs.yml
- All git operations run with `encoding="utf-8"` and `creationflags=CREATE_NO_WINDOW`
- **Double-click paste**: All QLineEdit fields support double-click to paste clipboard content
- **Drag & drop**: Folder drop on Upload panel auto-fills path + name + scans
- **Windows taskbar icon**: `SetCurrentProcessExplicitAppUserModelID()` before QApplication
- **Icon pattern**: QPainter icons use `_icon_pen()` for consistent color/weight
- **Sync icons**: green circle+checkmark (synced), orange circle+exclamation (unsynced)
- **Project config**: `.project_sources.json` stores `{slug: {path, created_at}}`, gitignored
- **Atomic JSON write**: `_save_raw_config()` writes to `.tmp` then `os.replace()` to prevent corruption
- **Git operation lock**: `_is_git_busy()` / `_set_git_busy()` prevents concurrent git operations
- **Friendly errors**: `_friendly_error()` translates git errors to user-friendly messages
- **Image auto-copy**: `_find_referenced_images()` parses .md for image refs, auto-copies during upload
- **Empty state UI**: Guided placeholder messages shown when panels have no content
- **Async sync status**: `_SyncStatusWorker(QThread)` checks sync status without blocking UI

## Current State
- Phase 0 complete: uploader with progress
- Phase 1 complete: side-by-side layout, project management, delete, copy/copy URL
- Phase 1.5 complete: select button, Git button, icons, reset, refresh, compact cards, app icon, desktop shortcut
- Phase 2 complete: GitLab dual deploy, sync status, change detection, Update All, drag & drop, source path management, project start date with calendar
- Phase 2.5 complete: Robustness & polish (friendly errors, atomic write, git lock, async sync, image auto-copy, empty state UI)
- See PLAN.md for full roadmap
