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
- **Drag & Drop**: Drag a folder onto the Upload panel
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
- Click **GitHub** to upload to GitHub only, or **GitLab** for GitLab only
- Button shows progress percentage (0% → 100%)
- Status line below shows current step:
  - Copying files
  - Generating index page
  - Updating navigation
  - git add / commit / push
- On success: shows published URL
- Projects panel auto-refreshes after upload
- Source folder path is automatically saved for change detection

## Project Management

### Project Cards
Each uploaded project shows a compact card with:
- **Row 1**: Project name + change badge (if any) + doc count + last updated time
- **Row 2**: Source path (clickable to change) + start date (clickable to change)
- **Row 3**: Action buttons

### Actions
| Button | Action |
|---|---|
| **◀** (icon) | Fill Upload panel's Project Name with this project name |
| **Copy** | Copy project name to clipboard |
| **Copy URL** | Copy GitLab URL to clipboard (private site) |
| **GitHub** | Open GitHub repo tree page |
| **GitLab** | Open GitLab repo tree page |
| **Delete** | Delete project (2-step confirmation) |
| **N changed** (orange badge) | Click to auto-update changed files from source |

### Header Actions
| Button | Action |
|---|---|
| **Refresh** | Re-scan projects, detect changes, update sync status |
| **GitHub ●** | Open GitHub Pages site (green=synced, orange=behind) |
| **GitLab ●** | Open GitLab Pages site (green=synced, orange=behind) |
| **Update All** | Batch update all changed projects in one commit (appears only when changes exist) |

### Change Detection
- Source folder path is saved when you upload a project
- On Refresh: app compares source .md files vs docs/ files by content hash
- Changed projects show orange "N changed" badge
- Click badge → auto-copies changed files + pushes to both GitHub & GitLab
- "Update All" → updates all changed projects in a single commit

### Source Path & Start Date
- **Source path**: click the gray path text to change via folder dialog
- **Start date**: click "Started: YYYY-MM-DD" to open calendar and change
- Calendar: click a date to select, "Today" button, month navigation (< >)
- Start date is auto-set on first upload

### Reset
Click "Reset" button on the Upload panel to clear all fields (path, name, file list).

### Delete Safety
Deleting a project requires two confirmations:
1. Click "Yes" on the warning dialog
2. Type the exact project name to confirm

## What Happens During Upload

1. **Source Path Saved**: Project folder path recorded in `.project_sources.json`
2. **File Copy**: Selected .md files → `docs/{project-slug}/`
3. **Image Auto-Copy**: Referenced images in .md files (`![](path)`, `<img src="">`) are automatically copied alongside the documents
4. **Index Page**: Auto-generated `index.md` with document table (created once, not overwritten)
5. **Navigation**: `mkdocs.yml` nav section updated with project + documents
6. **Git Push**: `git add .` → `git commit` → `git push` to selected remote(s)
7. **Deploy**: GitHub Actions / GitLab CI builds MkDocs → publishes to Pages
8. Site available in 1-2 minutes (CI build time)

## Published Sites

| Site | URL | Access |
|---|---|---|
| GitHub Pages | https://jungjaewa.github.io/ai-lab-notes/ | Public |
| GitLab Pages | https://jungjaehwa1.gitlab.io/ai-lab-notes/ | Private |

- Each project: `{site-url}/{project-slug}/`
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

## Error Messages

The app translates raw git errors into user-friendly messages:

| Error | Message |
|---|---|
| Not a git repository | "This folder is not set up correctly. Re-clone the repository." |
| Authentication failed | "GitHub/GitLab login required. Check your credentials." |
| Could not resolve host | "No internet connection." |
| Push rejected | "Remote has newer changes. Pull first." |
| Lock file exists | "Git is busy (lock file exists). Wait or delete `.git/index.lock`." |
| Connection timed out | "Connection timed out. Check your network." |
| Permission denied | "Permission denied. Check file/folder permissions." |

## Safety Features

- **Git operation lock**: Only one git operation can run at a time. Prevents repo corruption from concurrent commands.
- **Atomic config save**: Project config is written to a temp file first, then atomically replaced. Prevents data loss on crash.
- **Async sync status**: Sync status check runs in a background thread, keeping the UI responsive.

## Troubleshooting

| Issue | Solution |
|---|---|
| "No .md files found" | Check folder path. App scans up to 1 subfolder deep. |
| Path paste doesn't work | Press Enter after pasting, or double-click to auto-paste. |
| Upload fails with auth error | Run `git config credential.helper manager` in terminal. |
| Upload fails with network error | Check internet connection. |
| GitHub site not updating | Wait 1-2 minutes. Check GitHub Actions tab for build status. |
| GitLab site not updating | Wait 1-2 minutes. Check GitLab Build > Pipelines for status. |
| Sync status shows ⚠ | Push to the behind remote (click the respective upload button). |
| "N changed" badge wrong | Click source path to verify it points to the correct folder. |
| Korean text looks wrong | Ensure Malgun Gothic font is installed (default on Windows 11). |
| Projects not showing | Projects panel refreshes on startup and after upload. Click Refresh to re-scan. |
| App icon not showing | Taskbar icon requires `SetCurrentProcessExplicitAppUserModelID`. Already set in code. |
| Desktop shortcut shows console | Shortcut should use `pythonw.exe`, not `python.exe`. |
| Images not showing on site | Ensure images are in the same folder or subfolder as the .md file. App auto-copies referenced images. |
| Button not responding | A git operation may be in progress. Wait for it to finish (lock auto-releases). |
