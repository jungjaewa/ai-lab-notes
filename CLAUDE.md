# AI Lab Notes Manager

## Project Overview
Git-backed CMS desktop app (PyQt6) for managing MkDocs documentation.
Abstracts all Git operations so non-Git users can upload, manage, and publish markdown documents to GitHub Pages.

## Architecture
```
Local project folder → [App] → ai-lab-notes git repo → GitHub → MkDocs Pages
```

- **Runtime**: Python 3.12 + PyQt6
- **Backend**: Local git repo, mkdocs.yml nav parsing, shutil file copy
- **Deploy**: GitHub Actions auto-deploy on push to main → gh-pages branch
- **Site**: https://jungjaewa.github.io/ai-lab-notes/

## Key Files
| File | Purpose |
|---|---|
| `uploader.py` | Main app (PyQt6 GUI + all logic) |
| `mkdocs.yml` | MkDocs config + navigation structure |
| `docs/` | All published markdown documents |
| `docs/{project_slug}/` | Per-project document folders |
| `.github/workflows/deploy.yml` | GitHub Actions auto-deploy |

## Constants
- `REPO_DIR` = script directory (ai-lab-notes root)
- `DOCS_DIR` = `REPO_DIR/docs/`
- `MKDOCS_YML` = `REPO_DIR/mkdocs.yml`
- `SITE_URL` = `https://jungjaewa.github.io/ai-lab-notes/`
- `REPO_URL` = `https://github.com/jungjaewa/ai-lab-notes/tree/main/docs/`

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
| `create_app_icon()` | QPainter app icon: purple rounded rect + white "MD" |
| `create_select_icon()` | QPainter left-arrow icon for select button |
| `create_open_icon()` | QPainter external-link icon for open button |
| `create_repo_icon()` | QPainter code-bracket icon for repo button |
| `_icon_pen()` | Shared pen (#848484, 1.2px) for all button icons |

## Classes
| Class | Purpose |
|---|---|
| `UploadWorker(QThread)` | Background upload with progress signals |
| `DeleteWorker(QThread)` | Background project deletion with git push |
| `UploadPanel(QWidget)` | Left panel: browse, scan, upload |
| `ProjectCard(QFrame)` | Project card with Select/Copy/Copy URL/Open/Git/Delete |
| `ProjectsPanel(QWidget)` | Right panel: project list + management |
| `ManagerApp(QMainWindow)` | Main window with side-by-side layout |

## Layout
```
┌─────────────────────────────────────────────────────┐
│ [MD] AI Lab Notes Manager                            │
│ AI Lab Notes                                         │
│ Manage your project documentation                    │
│─────────────────────────────────────────────────────│
│ Upload              │ Projects    Refresh  Open Site  │
│                     │                                │
│ Project Path        │ ┌────────────────────────────┐│
│ [__________] Browse │ │ Eye Pipeline  3d|03-08 14:50││
│                     │ │ ◀ Copy CopyURL ↗ Git    Del││
│ Project Name        │ └────────────────────────────┘│
│ [__________]        │ ┌────────────────────────────┐│
│                     │ │ Teamplay_Gantt  ...        ││
│ Documents Found     │ │ ...                        ││
│ ┌─────────────────┐ │ └────────────────────────────┘│
│ │ ☑ file1.md      │ │                                │
│ │ ☑ file2.md      │ │                                │
│ └─────────────────┘ │                                │
│                     │                                │
│ [ Upload ] [Reset]  │                                │
│ Ready               │ 3 projects                     │
└─────────────────────────────────────────────────────┘
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
- All git operations run with `encoding="utf-8"`
- **Double-click paste**: All QLineEdit fields support double-click to paste clipboard content. Use `_paste_on_double_click()` static method for new fields.
- Scanning feedback: show "Scanning..." with `processEvents()` before blocking scan
- **Windows taskbar icon**: `SetCurrentProcessExplicitAppUserModelID()` before QApplication
- **Icon pattern**: QPainter icons use `_icon_pen()` for consistent color/weight

## Current State
- Phase 0 complete: uploader with progress
- Phase 1 complete: side-by-side layout, project management, delete, copy/copy URL
- Phase 1.5 complete: select button, Git button, icons, reset, refresh, compact cards, app icon, desktop shortcut
- Phase 2 planned: document-level management, drag & drop, change detection
- See PLAN.md for full roadmap
