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
| `uploader.py` | Main app (PyQt6 GUI + upload logic) |
| `mkdocs.yml` | MkDocs config + navigation structure |
| `docs/` | All published markdown documents |
| `docs/{project_slug}/` | Per-project document folders |
| `.github/workflows/deploy.yml` | GitHub Actions auto-deploy |

## Constants
- `REPO_DIR` = script directory (ai-lab-notes root)
- `DOCS_DIR` = `REPO_DIR/docs/`
- `MKDOCS_YML` = `REPO_DIR/mkdocs.yml`
- `SITE_URL` = `https://jungjaewa.github.io/ai-lab-notes/`

## Core Functions
| Function | Purpose |
|---|---|
| `find_md_files(folder)` | Walk folder (depth ≤ 1), return .md files |
| `slugify(text)` | Project name → URL-safe slug |
| `update_mkdocs_nav()` | Parse mkdocs.yml, insert/update project nav entries |
| `create_project_index()` | Generate index.md with document table |
| `git_push(message)` | Sequential git add → commit → push |

## Classes
| Class | Purpose |
|---|---|
| `UploadWorker(QThread)` | Background upload with progress signals |
| `UploaderApp(QMainWindow)` | Main window (will become `ManagerApp` with tabs) |

## Style
- Windows 11 Explorer aesthetic (accent #0078D4, bg #FFFFFF, borders #E5E5E5)
- Font: Malgun Gothic 10pt (Korean system font)
- UI text: English only
- Custom checkmark icon via QPainter → temp PNG → QSS `image: url()`

## Conventions
- Path normalization: always convert `\` → `/` for display
- Project slug: lowercase, hyphens, preserves Korean characters
- Nav structure: projects inserted before `tags.md` line in mkdocs.yml
- All git operations run with `encoding="utf-8"`

## Current State
- Phase 0 complete: single-tab uploader with progress
- Phase 1 planned: tab structure (Upload | Projects), project management
- See PLAN.md for full roadmap
