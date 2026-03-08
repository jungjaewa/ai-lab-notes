# AI Lab Notes Manager - Skills Guide

## Prerequisites

```bash
pip install PyQt6
```

## Launch

**Desktop shortcut**: Double-click "AI Lab Notes Manager" on desktop (no console window).

**Terminal**:
```bash
cd D:\_AI_BMAD\ai-lab-notes
python uploader.py
```

## App Layout

The app has two panels side by side:
- **Left (Upload)**: Upload documents from a local project folder
- **Right (Projects)**: View and manage uploaded projects

## Upload Workflow

### 1. Set Project Path
- **Browse**: Click "Browse" button → select project folder
- **Paste + Enter**: Paste path directly (e.g., `D:\_Teamplay`) → press Enter
- **Double-click**: Double-click the path field to paste from clipboard and auto-scan
- Backslashes are auto-converted to forward slashes

### 2. Set Project Name
- Auto-filled from folder name when path is set
- Editable — change to any display name you want
- **Double-click**: Double-click the name field to paste from clipboard
- This name appears in the MkDocs site navigation
- If the name already exists, a warning shows and the button changes to "Update"

### 3. Select Documents
- All `.md` files found in the folder (up to 1 subfolder deep) are listed
- All checked by default
- Uncheck files you don't want to upload
- "Scanning..." indicator shows while searching for files

### 4. Upload
- Click "Upload" (or "Update" for existing projects)
- Button shows progress percentage (0% → 100%)
- Status line below shows current step:
  - Copying files
  - Generating index page
  - Updating navigation
  - git add / commit / push
- On success: shows published URL
- Projects panel auto-refreshes after upload

## Project Management

### Project Cards
Each uploaded project shows a compact card with:
- Project name (left) + doc count + last updated time (right) — on the same line
- Action buttons below

### Actions
| Button | Action |
|---|---|
| **◀** (icon) | Fill Upload panel's Project Name with this project name |
| **Copy** | Copy project name to clipboard |
| **Copy URL** | Copy project URL to clipboard |
| **↗** (icon) | Open project page in browser |
| **Git** | Open project's GitHub repo page |
| **Delete** | Delete project (2-step confirmation) |
| **Refresh** | Re-scan projects from mkdocs.yml |
| **Open Site** | Open the main documentation site |

### Reset
Click "Reset" button on the Upload panel to clear all fields (path, name, file list).

### Delete Safety
Deleting a project requires two confirmations:
1. Click "Yes" on the warning dialog
2. Type the exact project name to confirm

## What Happens During Upload

1. **File Copy**: Selected .md files → `docs/{project-slug}/`
2. **Index Page**: Auto-generated `index.md` with document table (created once, not overwritten)
3. **Navigation**: `mkdocs.yml` nav section updated with project + documents
4. **Git Push**: `git add .` → `git commit` → `git push origin main`
5. **Deploy**: GitHub Actions builds MkDocs → publishes to GitHub Pages
6. Site available in 1-2 minutes (GitHub Actions build time)

## Published Site

- URL: https://jungjaewa.github.io/ai-lab-notes/
- Each project: `https://jungjaewa.github.io/ai-lab-notes/{project-slug}/`
- Supports: full-text search (Korean + English), dark mode, mobile view

## Re-uploading

Uploading to an existing project name:
- Existing files with the same name are **overwritten**
- New files are **added**
- Previously uploaded files not in the current selection are **kept**
- The index page is **not overwritten** (preserves manual edits)

## Double-Click Paste

All text input fields support double-click to paste:
- **Project Path**: pastes + normalizes path + auto-scans if valid folder
- **Project Name**: pastes clipboard text

## Troubleshooting

| Issue | Solution |
|---|---|
| "No .md files found" | Check folder path. App scans up to 1 subfolder deep. |
| Path paste doesn't work | Press Enter after pasting, or double-click to auto-paste. |
| Upload fails with auth error | Run `git config credential.helper manager` in terminal. |
| Upload fails with network error | Check internet connection. |
| Site not updating | Wait 1-2 minutes. Check GitHub Actions tab for build status. |
| Korean text looks wrong | Ensure Malgun Gothic font is installed (default on Windows 11). |
| Projects not showing | Projects panel refreshes on startup and after upload. Click Refresh to re-scan. |
| App icon not showing | Taskbar icon requires `SetCurrentProcessExplicitAppUserModelID`. Already set in code. |
| Desktop shortcut shows console | Shortcut should use `pythonw.exe`, not `python.exe`. |
