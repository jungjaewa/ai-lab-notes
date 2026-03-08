# AI Lab Notes Manager - Skills Guide

## Prerequisites

```bash
pip install PyQt6
```

## Launch

```bash
cd D:\_AI_BMAD\ai-lab-notes
python uploader.py
```

## Upload Workflow

### 1. Set Project Path
- **Browse**: Click "Browse" button → select project folder
- **Paste**: Paste path directly (e.g., `D:\_Teamplay`) → press Enter
- Backslashes are auto-converted to forward slashes

### 2. Set Project Name
- Auto-filled from folder name when path is set
- Editable — change to any display name you want
- This name appears in the MkDocs site navigation

### 3. Select Documents
- All `.md` files found in the folder (up to 1 subfolder deep) are listed
- All checked by default
- Uncheck files you don't want to upload

### 4. Upload
- Click "Upload" button
- Button shows progress percentage (0% → 100%)
- Status line below shows current step:
  - Copying files
  - Generating index page
  - Updating navigation
  - git add / commit / push
- On success: shows published URL
- Site available in 1-2 minutes (GitHub Actions build time)

## What Happens During Upload

1. **File Copy**: Selected .md files → `docs/{project-slug}/`
2. **Index Page**: Auto-generated `index.md` with document table (created once, not overwritten)
3. **Navigation**: `mkdocs.yml` nav section updated with project + documents
4. **Git Push**: `git add .` → `git commit` → `git push origin main`
5. **Deploy**: GitHub Actions builds MkDocs → publishes to GitHub Pages

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

## Troubleshooting

| Issue | Solution |
|---|---|
| "No .md files found" | Check folder path. App scans up to 1 subfolder deep. |
| Path paste doesn't work | Press Enter after pasting the path. |
| Upload fails with auth error | Run `git config credential.helper manager` in terminal. |
| Upload fails with network error | Check internet connection. |
| Site not updating | Wait 1-2 minutes. Check GitHub Actions tab for build status. |
| Korean text looks wrong | Ensure Malgun Gothic font is installed (default on Windows 11). |
