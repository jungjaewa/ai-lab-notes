# AI Lab Notes Manager - R&D Log

## 2026-03-08: Project Docs Created
- Created CLAUDE.md, PLAN.md, RND_LOG.md, SKILLS_GUIDE.md
- Designed Phase 1~3 roadmap for Manager app (tab structure, project management)
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
- Colors: accent #0078D4, background #FFFFFF, borders #E5E5E5, text #1A1A1A
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
