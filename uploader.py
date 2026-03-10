"""
AI Lab Notes Manager (PyQt6)
- Left panel: Upload - Project folder -> find .md files -> upload -> auto deploy
- Right panel: Projects - View/manage uploaded projects
"""

import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from datetime import datetime

# Windows taskbar: show app icon instead of python.exe icon
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ai-lab-notes-manager")

from PyQt6.QtCore import QRectF, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QClipboard, QCursor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

# ai-lab-notes repo path
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(REPO_DIR, "docs")
MKDOCS_YML = os.path.join(REPO_DIR, "mkdocs.yml")
SITE_URL = "https://jungjaewa.github.io/ai-lab-notes/"
GITLAB_SITE_URL = "https://jungjaehwa1.gitlab.io/ai-lab-notes/"
REPO_URL = "https://github.com/jungjaewa/ai-lab-notes/tree/main/docs/"
GITLAB_REPO_URL = "https://gitlab.com/jungjaehwa1/ai-lab-notes/-/tree/main/docs/"
GIT_REMOTES = ["origin", "gitlab"]  # push to both GitHub and GitLab


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

UPLOAD_EXTENSIONS = {".md", ".zip", ".7z"}
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
PROJECT_CONFIG = os.path.join(REPO_DIR, ".project_sources.json")

# Global git operation lock — prevents concurrent git operations
_git_busy = False


def _is_git_busy():
    return _git_busy


def _set_git_busy(busy):
    global _git_busy
    _git_busy = busy


def _load_raw_config():
    if os.path.isfile(PROJECT_CONFIG):
        with open(PROJECT_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_raw_config(data):
    # Atomic write: write to temp file first, then rename
    tmp_path = PROJECT_CONFIG + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, PROJECT_CONFIG)


def _normalize_entry(entry):
    """Convert old string format to new dict format."""
    if isinstance(entry, str):
        return {"path": entry, "created_at": None}
    return entry


def load_project_sources():
    """Load project config. Returns {slug: {path, created_at}}."""
    raw = _load_raw_config()
    return {k: _normalize_entry(v) for k, v in raw.items()}


def save_project_source(slug, source_path):
    """Save source folder path for a project (preserves created_at)."""
    data = _load_raw_config()
    existing = _normalize_entry(data.get(slug, {}))
    data[slug] = {
        "path": source_path,
        "created_at": existing.get("created_at") or datetime.now().strftime("%Y-%m-%d"),
    }
    _save_raw_config(data)


def save_project_created_at(slug, date_str):
    """Save or update created_at date for a project."""
    data = _load_raw_config()
    existing = _normalize_entry(data.get(slug, {}))
    existing["created_at"] = date_str
    data[slug] = existing
    _save_raw_config(data)


def remove_project_source(slug):
    """Remove source folder mapping for a project."""
    data = _load_raw_config()
    if slug in data:
        del data[slug]
        _save_raw_config(data)


def _file_hash(path):
    """Return MD5 hash of a file for comparison."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def check_project_changes(slug):
    """Compare source files vs docs/ files. Returns list of changed/new/deleted filenames."""
    sources = load_project_sources()
    entry = sources.get(slug)
    source_path = entry.get("path") if entry else None
    if not source_path or not os.path.isdir(source_path):
        return None  # source path unknown or missing

    docs_dir = os.path.join(DOCS_DIR, slug)
    if not os.path.isdir(docs_dir):
        return None

    # Build hash maps for source .md files
    source_files = {}
    for f in os.listdir(source_path):
        if f.lower().endswith(".md"):
            source_files[f] = _file_hash(os.path.join(source_path, f))

    # Build hash maps for docs .md files (exclude index.md which is auto-generated)
    docs_files = {}
    for f in os.listdir(docs_dir):
        if f.lower().endswith(".md") and f != "index.md":
            docs_files[f] = _file_hash(os.path.join(docs_dir, f))

    changes = []
    # Only compare files that exist in source
    for f, h in source_files.items():
        if f not in docs_files:
            changes.append(f"+ {f}")
        elif docs_files[f] != h:
            changes.append(f"~ {f}")

    return changes if changes else []


def get_sync_status():
    """Compare origin/main and gitlab/main commit hashes. Returns dict with sync info."""
    result = {"origin": None, "gitlab": None, "synced": False}
    for remote in ("origin", "gitlab"):
        try:
            r = subprocess.run(
                ["git", "rev-parse", f"{remote}/main"],
                cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8",
                creationflags=_NO_WINDOW,
            )
            if r.returncode == 0:
                result[remote] = r.stdout.strip()
        except Exception:
            pass
    result["synced"] = (
        result["origin"] is not None
        and result["gitlab"] is not None
        and result["origin"] == result["gitlab"]
    )
    return result



def _friendly_error(msg):
    """Translate git/network errors to user-friendly messages."""
    if not msg:
        return "Unknown error occurred."
    m = msg.lower()
    if "not a git repository" in m:
        return "This folder is not set up correctly. Re-clone the repository."
    if "authentication failed" in m or "could not read username" in m:
        return "GitHub/GitLab login required. Check your credentials."
    if "could not resolve host" in m or "unable to access" in m:
        return "No internet connection. Check your network and try again."
    if "rejected" in m and "push" in m:
        return "Remote has newer changes. Click Refresh first, then try again."
    if "lock" in m and "exists" in m:
        return "Git is busy (lock file exists). Wait a moment and try again."
    if "timed out" in m or "timeout" in m:
        return "Connection timed out. Check your network and try again."
    if "permission denied" in m:
        return "Permission denied. Check file/folder access rights."
    # Fallback: show first meaningful line
    first_line = msg.strip().split("\n")[0]
    if len(first_line) > 120:
        first_line = first_line[:120] + "..."
    return first_line


def _find_referenced_images(md_path, source_folder):
    """Parse a .md file and find locally referenced image files."""
    images = []
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return images

    # Match ![alt](path) and <img src="path"> patterns
    patterns = [
        r'!\[.*?\]\(([^)]+)\)',           # ![alt](path)
        r'<img[^>]+src=["\']([^"\']+)',    # <img src="path">
    ]
    for pat in patterns:
        for match in re.finditer(pat, content):
            ref = match.group(1).strip()
            # Skip URLs and absolute paths
            if ref.startswith(("http://", "https://", "data:", "/")):
                continue
            # Resolve relative to md file's directory or source folder
            md_dir = os.path.dirname(md_path)
            candidates = [
                os.path.join(md_dir, ref),
                os.path.join(source_folder, ref),
            ]
            for candidate in candidates:
                if os.path.isfile(candidate):
                    images.append((ref, os.path.abspath(candidate)))
                    break
    return images


def find_project_files(folder):
    found = []
    for root, dirs, files in os.walk(folder):
        depth = root.replace(folder, "").count(os.sep)
        if depth > 1:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in UPLOAD_EXTENSIONS:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, folder)
                found.append((rel_path, full_path))
    return sorted(found)


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\s가-힣-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text


def update_mkdocs_nav(project_slug, project_name, md_files_rel):
    with open(MKDOCS_YML, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    nav_start = None
    for i, line in enumerate(lines):
        if line.strip() == "nav:":
            nav_start = i
            break

    if nav_start is None:
        return

    project_marker = f"  - {project_name}:"
    project_exists = False
    proj_start = None
    proj_end = None

    for i in range(nav_start + 1, len(lines)):
        line = lines[i]
        if line.strip() == "" or (not line.startswith(" ") and line.strip()):
            break
        if line.startswith(project_marker) or line.strip().startswith(f"- {project_name}:"):
            project_exists = True
            proj_start = i
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "" or (
                    lines[j].startswith("  - ") and not lines[j].startswith("    ")
                ):
                    proj_end = j
                    break
            else:
                proj_end = len(lines)
            break

    nav_entries = []
    nav_entries.append(f"  - {project_name}:")
    nav_entries.append(f"    - {project_slug}/index.md")
    for rel_name in md_files_rel:
        if rel_name == "index.md":
            continue
        display = os.path.splitext(rel_name)[0].replace("-", " ").replace("_", " ").title()
        nav_entries.append(f"    - {display}: {project_slug}/{rel_name}")

    if project_exists:
        lines[proj_start:proj_end] = nav_entries
    else:
        tag_line = None
        for i in range(nav_start + 1, len(lines)):
            if "tags.md" in lines[i]:
                tag_line = i
                break
        if tag_line:
            lines[tag_line:tag_line] = nav_entries
        else:
            lines.extend(nav_entries)

    with open(MKDOCS_YML, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def remove_project_from_nav(project_name):
    with open(MKDOCS_YML, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    nav_start = None
    for i, line in enumerate(lines):
        if line.strip() == "nav:":
            nav_start = i
            break

    if nav_start is None:
        return

    proj_start = None
    proj_end = None

    for i in range(nav_start + 1, len(lines)):
        line = lines[i]
        if line.strip() == "" or (not line.startswith(" ") and line.strip()):
            break
        if line.strip().startswith(f"- {project_name}:"):
            proj_start = i
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "" or (
                    lines[j].startswith("  - ") and not lines[j].startswith("    ")
                ):
                    proj_end = j
                    break
            else:
                proj_end = len(lines)
            break

    if proj_start is not None:
        del lines[proj_start:proj_end]
        with open(MKDOCS_YML, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def create_project_index(project_slug, project_name, all_files_rel):
    index_path = os.path.join(DOCS_DIR, project_slug, "index.md")
    if os.path.exists(index_path):
        return

    md_files = [f for f in all_files_rel if f.lower().endswith(".md")]
    attach_files = [f for f in all_files_rel if not f.lower().endswith(".md")]

    lines = [
        f"# {project_name}",
        "",
        "## Documents",
        "",
        "| Document | File |",
        "|---|---|",
    ]
    for rel_name in md_files:
        display = os.path.splitext(rel_name)[0].replace("-", " ").replace("_", " ")
        lines.append(f"| [{display}]({rel_name}) | `{rel_name}` |")

    if attach_files:
        lines.append("")
        lines.append("## Attachments")
        lines.append("")
        lines.append("| File | Size |")
        lines.append("|---|---|")
        for rel_name in attach_files:
            fpath = os.path.join(DOCS_DIR, project_slug, "attach", rel_name)
            size = ""
            if os.path.exists(fpath):
                sz = os.path.getsize(fpath)
                if sz < 1024:
                    size = f"{sz} B"
                elif sz < 1024 * 1024:
                    size = f"{sz / 1024:.1f} KB"
                else:
                    size = f"{sz / (1024 * 1024):.1f} MB"
            lines.append(f"| [{rel_name}](attach/{rel_name}) | {size} |")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def parse_projects_from_nav():
    if not os.path.exists(MKDOCS_YML):
        return []

    with open(MKDOCS_YML, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    nav_start = None
    for i, line in enumerate(lines):
        if line.strip() == "nav:":
            nav_start = i
            break

    if nav_start is None:
        return []

    projects = []
    skip = {"Home", "태그"}

    i = nav_start + 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "" or (not line.startswith(" ") and line.strip()):
            break

        match = re.match(r"^  - (.+):$", line)
        if match:
            name = match.group(1).strip()
            if name not in skip:
                slug = None
                doc_count = 0
                j = i + 1
                while j < len(lines) and lines[j].startswith("    "):
                    child = lines[j].strip()
                    if slug is None:
                        child_match = re.search(r"(\S+)/\S+\.md", child)
                        if child_match:
                            slug = child_match.group(1)
                    doc_count += 1
                    j += 1

                if slug:
                    projects.append({
                        "name": name,
                        "slug": slug,
                        "nav_doc_count": doc_count,
                    })
        i += 1

    return projects


def get_project_info(slug):
    folder = os.path.join(DOCS_DIR, slug)
    if not os.path.isdir(folder):
        return {"doc_count": 0, "attach_count": 0, "last_updated": None, "total_size": 0}

    # Count .md files (excluding index.md)
    md_files = [f for f in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, f))
                and f.lower().endswith(".md") and f != "index.md"]

    # Count attachments in attach/ subfolder
    attach_dir = os.path.join(folder, "attach")
    attach_files = []
    if os.path.isdir(attach_dir):
        attach_files = [f for f in os.listdir(attach_dir)
                        if os.path.isfile(os.path.join(attach_dir, f))]

    total_size = 0
    latest_mtime = 0

    for f in md_files:
        fpath = os.path.join(folder, f)
        stat = os.stat(fpath)
        total_size += stat.st_size
        if stat.st_mtime > latest_mtime:
            latest_mtime = stat.st_mtime

    for f in attach_files:
        fpath = os.path.join(attach_dir, f)
        stat = os.stat(fpath)
        total_size += stat.st_size
        if stat.st_mtime > latest_mtime:
            latest_mtime = stat.st_mtime

    last_updated = None
    if latest_mtime > 0:
        last_updated = datetime.fromtimestamp(latest_mtime)

    return {
        "doc_count": len(md_files) + len(attach_files),
        "attach_count": len(attach_files),
        "last_updated": last_updated,
        "total_size": total_size,
    }


def project_exists_in_nav(project_name):
    projects = parse_projects_from_nav()
    return any(p["name"] == project_name for p in projects)


# ---------------------------------------------------------------------------
# Background workers
# ---------------------------------------------------------------------------

class UploadWorker(QThread):
    finished = pyqtSignal(bool, str)
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int, str)

    def __init__(self, project_name, selected_files, remotes=None, source_path=None):
        super().__init__()
        self.project_name = project_name
        self.selected_files = selected_files
        self.remotes = remotes or GIT_REMOTES
        self.source_path = source_path

    def run(self):
        try:
            project_slug = slugify(self.project_name)
            dest_dir = os.path.join(DOCS_DIR, project_slug)

            if self.source_path:
                save_project_source(project_slug, self.source_path)
            os.makedirs(dest_dir, exist_ok=True)

            attach_dir = os.path.join(dest_dir, "attach")

            total = len(self.selected_files)
            copied_rel = []
            img_count = 0
            for i, (rel_path, full_path) in enumerate(self.selected_files):
                basename = os.path.basename(rel_path)
                if basename.lower().endswith(".md"):
                    dest_path = os.path.join(dest_dir, basename)
                    # Auto-copy referenced images
                    source_dir = os.path.dirname(full_path) or self.source_path or ""
                    for img_ref, img_full in _find_referenced_images(full_path, source_dir):
                        img_dest_dir = os.path.join(dest_dir, os.path.dirname(img_ref))
                        os.makedirs(img_dest_dir, exist_ok=True)
                        img_dest = os.path.join(dest_dir, img_ref)
                        if not os.path.exists(img_dest) or _file_hash(img_full) != _file_hash(img_dest):
                            shutil.copy2(img_full, img_dest)
                            img_count += 1
                else:
                    os.makedirs(attach_dir, exist_ok=True)
                    dest_path = os.path.join(attach_dir, basename)
                shutil.copy2(full_path, dest_path)
                copied_rel.append(basename)
                pct = int((i + 1) / total * 30)
                self.progress_update.emit(pct, f"Uploading {pct}%")
                self.status_update.emit(f"Copying {rel_path}")
            if img_count:
                self.status_update.emit(f"Auto-copied {img_count} referenced images")

            self.progress_update.emit(40, "Uploading 40%")
            self.status_update.emit("Generating index page...")
            create_project_index(project_slug, self.project_name, copied_rel)

            # Only .md files go into nav
            md_rel = [f for f in copied_rel if f.lower().endswith(".md")]
            if "index.md" not in md_rel:
                md_rel.insert(0, "index.md")

            self.progress_update.emit(50, "Uploading 50%")
            self.status_update.emit("Updating navigation...")
            update_mkdocs_nav(project_slug, self.project_name, md_rel)

            self.progress_update.emit(60, "Uploading 60%")
            self.status_update.emit("git add .")
            subprocess.run(["git", "add", "."], cwd=REPO_DIR,
                           capture_output=True, text=True, encoding="utf-8",
                           creationflags=_NO_WINDOW)

            self.progress_update.emit(70, "Uploading 70%")
            self.status_update.emit("git commit")
            subprocess.run(["git", "commit", "-m", f"Add/update {self.project_name} docs"],
                           cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8",
                           creationflags=_NO_WINDOW)

            self.progress_update.emit(80, "Uploading 80%")
            ok, err = True, ""
            for remote in self.remotes:
                self.status_update.emit(f"git push {remote} main...")
                result = subprocess.run(["git", "push", remote, "main"],
                                        cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8",
                                        creationflags=_NO_WINDOW)
                if result.returncode != 0:
                    ok, err = False, _friendly_error(result.stderr or result.stdout)

            self.progress_update.emit(100, "Uploading 100%")

            if ok:
                if self.remotes == ["gitlab"]:
                    url = f"{GITLAB_SITE_URL}{project_slug}/"
                elif self.remotes == ["origin"]:
                    url = f"{SITE_URL}{project_slug}/"
                else:
                    url = f"{SITE_URL}{project_slug}/\n{GITLAB_SITE_URL}{project_slug}/"
                self.finished.emit(True, url)
            else:
                self.finished.emit(False, err)

        except Exception as e:
            self.finished.emit(False, _friendly_error(str(e)))


class DeleteWorker(QThread):
    finished = pyqtSignal(bool, str)
    status_update = pyqtSignal(str)

    def __init__(self, project_name, project_slug, remotes=None):
        super().__init__()
        self.project_name = project_name
        self.project_slug = project_slug
        self.remotes = remotes or GIT_REMOTES

    def run(self):
        try:
            self.status_update.emit("Removing files...")
            folder = os.path.join(DOCS_DIR, self.project_slug)
            if os.path.isdir(folder):
                shutil.rmtree(folder)

            self.status_update.emit("Updating navigation...")
            remove_project_from_nav(self.project_name)
            remove_project_source(self.project_slug)

            self.status_update.emit("git add .")
            subprocess.run(["git", "add", "."], cwd=REPO_DIR,
                           capture_output=True, text=True, encoding="utf-8",
                           creationflags=_NO_WINDOW)

            self.status_update.emit("git commit")
            subprocess.run(["git", "commit", "-m", f"Remove {self.project_name} docs"],
                           cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8",
                           creationflags=_NO_WINDOW)

            ok, err = True, ""
            for remote in self.remotes:
                self.status_update.emit(f"git push {remote} main...")
                result = subprocess.run(["git", "push", remote, "main"],
                                        cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8",
                                        creationflags=_NO_WINDOW)
                if result.returncode != 0:
                    ok, err = False, _friendly_error(result.stderr or result.stdout)

            if ok:
                self.finished.emit(True, "")
            else:
                self.finished.emit(False, err)

        except Exception as e:
            self.finished.emit(False, _friendly_error(str(e)))


# ---------------------------------------------------------------------------
# QSS Style
# ---------------------------------------------------------------------------

STYLE = """
QMainWindow {
    background-color: #FFFFFF;
}
QLabel {
    color: #1A1A1A;
}
QLabel#panel_title {
    font-size: 11pt;
    font-weight: 600;
    color: #1A1A1A;
}
QLabel#title {
    font-size: 16px;
    font-weight: 600;
}
QLabel#subtitle {
    color: #616161;
    font-size: 9pt;
}
QLabel#status {
    color: #616161;
    font-size: 9pt;
}
QLabel#placeholder {
    color: #616161;
    font-size: 9pt;
}
QLabel#error {
    color: #C42B1C;
    font-size: 9pt;
}
QLabel#warning {
    color: #9D5D00;
    font-size: 9pt;
}
QLabel#project_name {
    font-size: 10pt;
    font-weight: 600;
    color: #1A1A1A;
}
QLabel#project_meta {
    font-size: 8pt;
    color: #616161;
}
QLabel#copied_toast {
    color: #0078D4;
    font-size: 8pt;
}
QLineEdit {
    border: 1px solid #C5C5C5;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: #FFFFFF;
    color: #1A1A1A;
    selection-background-color: #0078D4;
}
QLineEdit:focus {
    border: 2px solid #0078D4;
    padding: 5px 9px;
}
QPushButton#browse {
    background-color: #F3F3F3;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
    padding: 6px 16px;
    color: #1A1A1A;
}
QPushButton#browse:hover {
    background-color: #E5E5E5;
}
QPushButton#browse:pressed {
    background-color: #D9D9D9;
}
QPushButton#upload {
    background-color: #0078D4;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    color: #FFFFFF;
    font-weight: 600;
}
QPushButton#upload:hover {
    background-color: #106EBE;
}
QPushButton#upload:pressed {
    background-color: #005A9E;
}
QPushButton#upload:disabled {
    background-color: #C5C5C5;
}
QPushButton#action_btn {
    background-color: transparent;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
    padding: 4px 8px;
    color: #616161;
    font-size: 8pt;
}
QPushButton#action_btn:hover {
    background-color: #F3F3F3;
    color: #1A1A1A;
}
QPushButton#delete_btn {
    background-color: transparent;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
    padding: 4px 8px;
    color: #C42B1C;
    font-size: 8pt;
}
QPushButton#delete_btn:hover {
    background-color: #FDE7E9;
    border-color: #C42B1C;
}
QPushButton#open_site {
    background-color: #F3F3F3;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
    padding: 6px 16px;
    color: #1A1A1A;
}
QPushButton#open_site:hover {
    background-color: #E5E5E5;
}
QFrame#separator {
    background-color: #C5C5C5;
    max-height: 1px;
}
QFrame#v_separator {
    background-color: #C5C5C5;
    max-width: 1px;
}
QFrame#card {
    background-color: #FBFBFB;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
}
QFrame#project_card {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
}
QFrame#project_card:hover {
    border-color: #0078D4;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
QCheckBox {
    spacing: 8px;
    color: #1A1A1A;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #848484;
    border-radius: 3px;
    background-color: #FFFFFF;
}
QCheckBox::indicator:hover {
    border-color: #0078D4;
}
QCheckBox::indicator:checked {
    border: none;
    background-color: #0078D4;
    image: url(CHECKMARK_PATH);
}
"""


def create_app_icon():
    """Create app icon: purple rounded square with white 'MD' text."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Purple rounded background
    painter.setBrush(QBrush(QColor("#7B2FBE")))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(0, 0, size, size), 14, 14)
    # White "MD" text
    font = QFont("Segoe UI", 22, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "MD")
    painter.end()
    return QIcon(pixmap)


def create_checkmark_icon():
    pixmap = QPixmap(18, 18)
    pixmap.fill(QColor("#0078D4"))
    painter = QPainter(pixmap)
    pen = QPen(QColor("#FFFFFF"))
    pen.setWidth(2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.drawLine(4, 9, 7, 13)
    painter.drawLine(7, 13, 14, 5)
    painter.end()
    path = os.path.join(tempfile.gettempdir(), "aln_check.png")
    pixmap.save(path)
    return path.replace("\\", "/")


def _icon_pen():
    """Shared pen for icon drawing — matches action_btn text color #848484, thin line."""
    pen = QPen(QColor("#848484"))
    pen.setWidthF(1.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def create_select_icon():
    """Create a left-arrow icon for the select button (16x16)."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setPen(_icon_pen())
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.drawLine(10, 3, 4, 8)
    painter.drawLine(4, 8, 10, 13)
    painter.end()
    return QIcon(pixmap)


def create_repo_icon():
    """Create a code-bracket icon </> for the repo button (16x16)."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setPen(_icon_pen())
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # < bracket
    painter.drawLine(5, 3, 1, 8)
    painter.drawLine(1, 8, 5, 13)
    # > bracket
    painter.drawLine(11, 3, 15, 8)
    painter.drawLine(15, 8, 11, 13)
    # / slash
    painter.drawLine(10, 2, 6, 14)
    painter.end()
    return QIcon(pixmap)


def create_open_icon():
    """Create an external-link icon for the open button (16x16)."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setPen(_icon_pen())
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Box (bottom-left open rectangle)
    painter.drawLine(3, 6, 3, 13)
    painter.drawLine(3, 13, 10, 13)
    painter.drawLine(10, 13, 10, 9)
    # Arrow (top-right diagonal)
    painter.drawLine(7, 3, 13, 3)
    painter.drawLine(13, 3, 13, 9)
    painter.drawLine(7, 9, 13, 3)
    painter.end()
    return QIcon(pixmap)


def create_sync_icon():
    """Create a green checkmark circle icon for synced state (16x16)."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Green filled circle
    painter.setBrush(QBrush(QColor("#2EA043")))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(1, 1, 14, 14)
    # White checkmark
    pen = QPen(QColor("#FFFFFF"))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.drawLine(4, 8, 7, 11)
    painter.drawLine(7, 11, 12, 5)
    painter.end()
    return QIcon(pixmap)


def create_unsync_icon():
    """Create an orange exclamation circle icon for unsynced state (16x16)."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Orange filled circle
    painter.setBrush(QBrush(QColor("#D83B01")))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(1, 1, 14, 14)
    # White exclamation mark
    pen = QPen(QColor("#FFFFFF"))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(8, 4, 8, 9)
    painter.drawPoint(8, 12)
    painter.end()
    return QIcon(pixmap)


# ---------------------------------------------------------------------------
# Upload Panel (left side)
# ---------------------------------------------------------------------------

class UploadPanel(QWidget):
    upload_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.md_files = []
        self.checkboxes = []
        self.worker = None
        self._build_ui()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and os.path.isdir(urls[0].toLocalFile()):
                event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            folder = urls[0].toLocalFile()
            if os.path.isdir(folder):
                self.path_edit.setText(folder)
                self.name_edit.setText(os.path.basename(folder))
                self._scan_files(folder)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 0, 16, 16)
        layout.setSpacing(0)

        # Panel title
        title = QLabel("Upload")
        title.setObjectName("panel_title")
        layout.addWidget(title)
        layout.addSpacing(12)

        # Project Path
        layout.addWidget(QLabel("Project Path"))
        layout.addSpacing(6)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Paste path or click Browse")
        self.path_edit.returnPressed.connect(self._on_path_entered)
        self.path_edit.mouseDoubleClickEvent = self._on_path_double_click
        path_row.addWidget(self.path_edit)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browse")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)

        layout.addLayout(path_row)
        layout.addSpacing(12)

        # Project Name
        layout.addWidget(QLabel("Project Name"))
        layout.addSpacing(6)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Auto-filled from folder name")
        self.name_edit.textChanged.connect(self._check_duplicate)
        self.name_edit.mouseDoubleClickEvent = self._on_name_double_click
        layout.addWidget(self.name_edit)
        layout.addSpacing(4)

        # Duplicate warning
        self.dup_label = QLabel("")
        self.dup_label.setObjectName("warning")
        self.dup_label.setVisible(False)
        layout.addWidget(self.dup_label)
        layout.addSpacing(10)

        # Documents Found header + Attach button
        doc_header_row = QHBoxLayout()
        card_label = QLabel("Documents Found")
        card_label.setObjectName("subtitle")
        doc_header_row.addWidget(card_label)
        doc_header_row.addStretch()

        attach_btn = QPushButton("Attach")
        attach_btn.setObjectName("browse")
        attach_btn.setToolTip("Attach files from any location")
        attach_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        attach_btn.clicked.connect(self._attach_files)
        doc_header_row.addWidget(attach_btn)

        layout.addLayout(doc_header_row)
        layout.addSpacing(6)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.file_list_widget = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_widget)
        self.file_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.file_list_layout.setContentsMargins(4, 4, 4, 4)
        self.file_list_layout.setSpacing(4)

        placeholder = QLabel("Drop a folder here, paste a path,\nor click Browse to get started")
        placeholder.setObjectName("placeholder")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #999999; font-size: 9pt; padding: 20px;")
        self.file_list_layout.addWidget(placeholder)

        self.scroll.setWidget(self.file_list_widget)
        card_layout.addWidget(self.scroll)
        layout.addWidget(card, 1)
        layout.addSpacing(12)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.gh_upload_btn = QPushButton("GitHub")
        self.gh_upload_btn.setObjectName("upload")
        self.gh_upload_btn.setEnabled(False)
        self.gh_upload_btn.clicked.connect(lambda: self._upload(["origin"], self.gh_upload_btn))
        btn_row.addWidget(self.gh_upload_btn, 1)

        self.gl_upload_btn = QPushButton("GitLab")
        self.gl_upload_btn.setObjectName("upload")
        self.gl_upload_btn.setEnabled(False)
        self.gl_upload_btn.clicked.connect(lambda: self._upload(["gitlab"], self.gl_upload_btn))
        btn_row.addWidget(self.gl_upload_btn, 1)

        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("browse")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(reset_btn)

        layout.addLayout(btn_row)
        layout.addSpacing(8)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

    def set_project_name(self, name):
        self.name_edit.setText(name)
        self.name_edit.setFocus()

    @staticmethod
    def _paste_on_double_click(line_edit, event):
        """Double-click a QLineEdit to paste clipboard text and select all."""
        clipboard = QApplication.clipboard().text()
        if clipboard.strip():
            line_edit.setText(clipboard.strip())
            line_edit.selectAll()
            return True
        return False

    def _normalize_path(self, path):
        path = path.strip().strip('"').strip("'")
        return path.replace("\\", "/")

    def _on_path_double_click(self, event):
        if self._paste_on_double_click(self.path_edit, event):
            folder = self._normalize_path(self.path_edit.text())
            self.path_edit.setText(folder)
            if os.path.isdir(folder):
                if not self.name_edit.text().strip():
                    self.name_edit.setText(os.path.basename(folder))
                self._scan_files(folder)

    def _on_name_double_click(self, event):
        self._paste_on_double_click(self.name_edit, event)

    def _reset(self):
        self.path_edit.clear()
        self.name_edit.clear()
        self.md_files.clear()
        self.checkboxes.clear()
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        placeholder = QLabel("Drop a folder here, paste a path,\nor click Browse to get started")
        placeholder.setObjectName("placeholder")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #999999; font-size: 9pt; padding: 20px;")
        self.file_list_layout.addWidget(placeholder)
        self.gh_upload_btn.setEnabled(False)
        self.gl_upload_btn.setEnabled(False)
        self.gh_upload_btn.setText("GitHub")
        self.gl_upload_btn.setText("GitLab")
        self.dup_label.setVisible(False)
        self.status_label.setText("Ready")

    def _on_path_entered(self):
        raw = self.path_edit.text()
        if not raw.strip():
            return
        folder = self._normalize_path(raw)
        self.path_edit.setText(folder)
        if os.path.isdir(folder):
            if not self.name_edit.text().strip():
                self.name_edit.setText(os.path.basename(folder))
            self._scan_files(folder)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.path_edit.setText(folder)
            self.name_edit.setText(os.path.basename(folder))
            self._scan_files(folder)

    def _check_duplicate(self):
        name = self.name_edit.text().strip()
        if name and project_exists_in_nav(name):
            slug = slugify(name)
            info = get_project_info(slug)
            self.dup_label.setText(
                f'"{name}" already exists ({info["doc_count"]} docs). Files will be updated.'
            )
            self.dup_label.setVisible(True)
        else:
            self.dup_label.setVisible(False)

    def _scan_files(self, folder):
        self.checkboxes.clear()
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show scanning state
        self.gh_upload_btn.setEnabled(False)
        self.gl_upload_btn.setEnabled(False)
        self.status_label.setText("Scanning...")
        scanning_label = QLabel("Scanning for files...")
        scanning_label.setObjectName("placeholder")
        scanning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list_layout.addWidget(scanning_label)
        QApplication.processEvents()

        self.md_files = find_project_files(folder)

        # Clear scanning label
        scanning_label.deleteLater()

        if not self.md_files:
            err = QLabel("No .md or .zip files found")
            err.setObjectName("error")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_list_layout.addWidget(err)
            self.gh_upload_btn.setEnabled(False)
            self.gl_upload_btn.setEnabled(False)
            self.status_label.setText("No files found")
            return

        for rel_path, full_path in self.md_files:
            cb = QCheckBox(rel_path)
            cb.setChecked(True)
            self.checkboxes.append(cb)
            self.file_list_layout.addWidget(cb)

        md_count = sum(1 for r, _ in self.md_files if r.lower().endswith(".md"))
        attach_count = len(self.md_files) - md_count
        parts = []
        if md_count:
            parts.append(f"{md_count} docs")
        if attach_count:
            parts.append(f"{attach_count} attachments")
        self.gh_upload_btn.setEnabled(True)
        self.gl_upload_btn.setEnabled(True)
        self.status_label.setText(f"{' + '.join(parts)} found")
        self._check_duplicate()

    def _attach_files(self):
        """Open file dialog to attach files from any location."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Attach",
            "",
            "Attachments (*.zip *.7z *.pdf *.pptx *.xlsx *.docx);;All Files (*)",
        )
        if not files:
            return

        # Track existing filenames to avoid duplicates
        existing = {os.path.basename(rel) for rel, _ in self.md_files}

        added = 0
        for full_path in files:
            basename = os.path.basename(full_path)
            if basename in existing:
                continue
            existing.add(basename)
            self.md_files.append((basename, full_path))

            cb = QCheckBox(f"{basename}  (attached)")
            cb.setChecked(True)
            self.checkboxes.append(cb)
            self.file_list_layout.addWidget(cb)
            added += 1

        if added == 0:
            return

        # Remove placeholder if present
        for i in range(self.file_list_layout.count()):
            item = self.file_list_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QLabel) and w.objectName() in ("placeholder", "error"):
                    w.deleteLater()
                    break

        # Update status and enable upload
        md_count = sum(1 for r, _ in self.md_files if r.lower().endswith(".md"))
        other_count = len(self.md_files) - md_count
        parts = []
        if md_count:
            parts.append(f"{md_count} docs")
        if other_count:
            parts.append(f"{other_count} attachments")
        self.status_label.setText(f"{' + '.join(parts)} ready")
        self.gh_upload_btn.setEnabled(True)
        self.gl_upload_btn.setEnabled(True)
        self._check_duplicate()

    def _upload(self, remotes, active_btn):
        if _is_git_busy():
            QMessageBox.warning(self, "Busy", "Another operation is in progress. Please wait.")
            return

        project_name = self.name_edit.text().strip()
        if not project_name:
            QMessageBox.warning(self, "Warning", "Please enter a project name")
            return

        selected = [
            (rel, full)
            for (rel, full), cb in zip(self.md_files, self.checkboxes)
            if cb.isChecked()
        ]
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select documents to upload")
            return

        self._active_btn = active_btn
        self.gh_upload_btn.setEnabled(False)
        self.gl_upload_btn.setEnabled(False)
        self.status_label.setText("Uploading...")

        source_path = self.path_edit.text().strip()
        _set_git_busy(True)
        self.worker = UploadWorker(project_name, selected, remotes, source_path=source_path)
        self.worker.status_update.connect(self._on_status)
        self.worker.progress_update.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_status(self, text):
        self.status_label.setText(text)

    def _on_progress(self, pct, text):
        self._active_btn.setText(text)

    def _on_finished(self, success, msg):
        _set_git_busy(False)
        self.gh_upload_btn.setText("GitHub")
        self.gl_upload_btn.setText("GitLab")
        self.gh_upload_btn.setEnabled(True)
        self.gl_upload_btn.setEnabled(True)
        self._check_duplicate()
        if success:
            self.status_label.setText(f"Done! {msg}")
            QMessageBox.information(
                self, "Upload Complete",
                f"Documents uploaded!\n\nAvailable in 1-2 min:\n{msg}"
            )
            self.upload_finished.emit()
        else:
            self.status_label.setText(f"Error: {msg[:80]}")
            QMessageBox.critical(self, "Error", msg)


# ---------------------------------------------------------------------------
# Project Card Widget
# ---------------------------------------------------------------------------

class ProjectCard(QFrame):
    delete_requested = pyqtSignal(str, str)  # name, slug
    select_requested = pyqtSignal(str)  # name
    update_requested = pyqtSignal(str, str)  # name, slug

    def __init__(self, name, slug, doc_count, attach_count, last_updated, changes=None, source_path=None, created_at=None):
        super().__init__()
        self.setObjectName("project_card")
        self.project_name = name
        self.project_slug = slug
        self.gh_url = f"{SITE_URL}{slug}/"
        self.gl_url = f"{GITLAB_SITE_URL}{slug}/"
        self.gh_repo_url = f"{REPO_URL}{slug}/"
        self.gl_repo_url = f"{GITLAB_REPO_URL}{slug}/"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 8, 14, 8)
        main_layout.setSpacing(4)

        # Top row: name + meta on same line
        top_row = QHBoxLayout()
        top_row.setSpacing(0)
        name_label = QLabel(name)
        name_label.setObjectName("project_name")
        top_row.addWidget(name_label)

        # Updated badge (clickable)
        if changes:
            badge = QPushButton(f"  {len(changes)} changed")
            badge.setStyleSheet(
                "color: #FFFFFF; background: #D83B01; border-radius: 3px;"
                "padding: 1px 6px; font-size: 9pt; border: none;"
            )
            badge.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            badge.setToolTip("Click to update\n" + "\n".join(changes))
            badge.clicked.connect(lambda: self.update_requested.emit(self.project_name, self.project_slug))
            top_row.addSpacing(8)
            top_row.addWidget(badge)

        top_row.addStretch()

        count_parts = [f"{doc_count} files"]
        if attach_count:
            count_parts.append(f"{attach_count} attached")
        meta_parts = [" · ".join(count_parts)]
        if last_updated:
            meta_parts.append(last_updated.strftime('%Y-%m-%d %H:%M'))
        meta_label = QLabel("  |  ".join(meta_parts))
        meta_label.setObjectName("project_meta")
        top_row.addWidget(meta_label)
        main_layout.addLayout(top_row)

        # Source path + created date row
        info_row = QHBoxLayout()
        info_row.setSpacing(0)

        path_text = source_path.replace("\\", "/") if source_path else "Set source path..."
        path_style = "color: #999999; font-size: 8pt;" if source_path else "color: #0078D4; font-size: 8pt;"
        self._path_btn = QPushButton(path_text)
        self._path_btn.setStyleSheet(
            f"QPushButton {{ {path_style} border: none; text-align: left; padding: 0; }}"
            f"QPushButton:hover {{ color: #0078D4; }}"
        )
        self._path_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._path_btn.clicked.connect(self._change_source_path)
        info_row.addWidget(self._path_btn)

        info_row.addStretch()

        date_text = f"Started: {created_at}" if created_at else "Set start date..."
        date_style = "color: #999999; font-size: 8pt;" if created_at else "color: #0078D4; font-size: 8pt;"
        self._date_btn = QPushButton(date_text)
        self._date_btn.setStyleSheet(
            f"QPushButton {{ {date_style} border: none; padding: 0; }}"
            f"QPushButton:hover {{ color: #0078D4; }}"
        )
        self._date_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._date_btn.clicked.connect(self._change_created_date)
        info_row.addWidget(self._date_btn)

        main_layout.addLayout(info_row)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        select_btn = QPushButton()
        select_btn.setIcon(create_select_icon())
        select_btn.setObjectName("action_btn")
        select_btn.setToolTip("Use this name for upload")
        select_btn.setFixedWidth(30)
        select_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        select_btn.clicked.connect(lambda: self.select_requested.emit(self.project_name))
        btn_row.addWidget(select_btn)

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("action_btn")
        copy_btn.setToolTip("Copy project name")
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(self.project_name, copy_btn))
        btn_row.addWidget(copy_btn)

        copy_url_btn = QPushButton("Copy URL")
        copy_url_btn.setObjectName("action_btn")
        copy_url_btn.setToolTip("Copy GitLab URL (private)")
        copy_url_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_url_btn.clicked.connect(lambda: self._copy_to_clipboard(self.gl_url, copy_url_btn))
        btn_row.addWidget(copy_url_btn)

        gh_open_btn = QPushButton("GitHub")
        gh_open_btn.setObjectName("action_btn")
        gh_open_btn.setToolTip("Open GitHub repo tree")
        gh_open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        gh_open_btn.clicked.connect(lambda: webbrowser.open(self.gh_repo_url))
        btn_row.addWidget(gh_open_btn)

        gl_open_btn = QPushButton("GitLab")
        gl_open_btn.setObjectName("action_btn")
        gl_open_btn.setToolTip("Open GitLab repo tree")
        gl_open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        gl_open_btn.clicked.connect(lambda: webbrowser.open(self.gl_repo_url))
        btn_row.addWidget(gl_open_btn)

        btn_row.addStretch()

        del_btn = QPushButton("Delete")
        del_btn.setObjectName("delete_btn")
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.clicked.connect(self._request_delete)
        btn_row.addWidget(del_btn)

        main_layout.addLayout(btn_row)

    def _copy_to_clipboard(self, text, btn):
        QApplication.clipboard().setText(text)
        original = btn.text()
        btn.setText("Copied!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: btn.setText(original))

    def _change_source_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            save_project_source(self.project_slug, folder)
            self._path_btn.setText(folder.replace("\\", "/"))
            self._path_btn.setStyleSheet(
                "QPushButton { color: #999999; font-size: 8pt; border: none; text-align: left; padding: 0; }"
                "QPushButton:hover { color: #0078D4; }"
            )

    def _change_created_date(self):
        from PyQt6.QtWidgets import QDialog, QGridLayout
        from PyQt6.QtCore import QDate

        sources = load_project_sources()
        entry = sources.get(self.project_slug, {})
        if entry.get("created_at"):
            parts = entry["created_at"].split("-")
            cur = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            cur = QDate.currentDate()

        dlg = QDialog(self)
        dlg.setWindowTitle("Start Date")
        dlg.setFixedSize(280, 320)
        dlg.setStyleSheet("""
            QDialog { background: #FFFFFF; }
            QPushButton { border: none; font-size: 10pt; padding: 4px; }
            QPushButton:hover { background: #E8E8E8; border-radius: 4px; }
        """)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(12, 12, 12, 12)
        dlg_layout.setSpacing(8)

        view_date = [cur]  # mutable reference for month navigation
        selected_result = [None]

        # Header: < Month Year >
        nav_row = QHBoxLayout()
        prev_btn = QPushButton("<")
        prev_btn.setFixedWidth(30)
        prev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        month_label = QLabel()
        month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        month_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        next_btn = QPushButton(">")
        next_btn.setFixedWidth(30)
        next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        nav_row.addWidget(prev_btn)
        nav_row.addWidget(month_label, 1)
        nav_row.addWidget(next_btn)
        dlg_layout.addLayout(nav_row)

        # Day-of-week headers
        dow_row = QHBoxLayout()
        dow_row.setSpacing(0)
        for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #888888; font-size: 8pt;")
            lbl.setFixedSize(36, 20)
            dow_row.addWidget(lbl)
        dlg_layout.addLayout(dow_row)

        # Day grid
        grid = QGridLayout()
        grid.setSpacing(0)
        day_buttons = []
        for r in range(6):
            for c in range(7):
                btn = QPushButton("")
                btn.setFixedSize(36, 32)
                btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                grid.addWidget(btn, r, c)
                day_buttons.append(btn)
        dlg_layout.addLayout(grid)

        def fill_grid():
            d = view_date[0]
            month_label.setText(f"{d.year()}.{d.month():02d}")
            first = QDate(d.year(), d.month(), 1)
            start_dow = first.dayOfWeek()  # 1=Mon
            days_in_month = first.daysInMonth()
            today = QDate.currentDate()

            for i, btn in enumerate(day_buttons):
                day_num = i - (start_dow - 1) + 1
                if 1 <= day_num <= days_in_month:
                    btn.setText(str(day_num))
                    btn.setEnabled(True)
                    this_date = QDate(d.year(), d.month(), day_num)
                    # Style
                    if this_date == cur:
                        btn.setStyleSheet("background: #0078D4; color: white; border-radius: 4px; font-size: 10pt;")
                    elif this_date == today:
                        btn.setStyleSheet("color: #0078D4; font-weight: bold; font-size: 10pt;")
                    else:
                        btn.setStyleSheet("font-size: 10pt;")
                    # Click = select, double-click = select & close
                    btn.clicked.disconnect() if btn.receivers(btn.clicked) else None
                    date_str = this_date.toString("yyyy-MM-dd")
                    btn.clicked.connect(lambda checked, ds=date_str: _on_select(ds))
                else:
                    btn.setText("")
                    btn.setEnabled(False)
                    btn.setStyleSheet("font-size: 10pt;")

        def _on_select(date_str):
            selected_result[0] = date_str
            dlg.accept()

        def go_prev():
            d = view_date[0]
            view_date[0] = d.addMonths(-1)
            fill_grid()

        def go_next():
            d = view_date[0]
            view_date[0] = d.addMonths(1)
            fill_grid()

        def go_today():
            view_date[0] = QDate.currentDate()
            fill_grid()

        prev_btn.clicked.connect(go_prev)
        next_btn.clicked.connect(go_next)

        # Bottom: Today + Cancel
        bottom_row = QHBoxLayout()
        today_btn = QPushButton("Today")
        today_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        today_btn.setStyleSheet("color: #0078D4; font-size: 9pt;")
        today_btn.clicked.connect(go_today)
        bottom_row.addWidget(today_btn)
        bottom_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setStyleSheet("color: #888888; font-size: 9pt;")
        cancel_btn.clicked.connect(dlg.reject)
        bottom_row.addWidget(cancel_btn)
        dlg_layout.addLayout(bottom_row)

        fill_grid()

        if dlg.exec() == QDialog.DialogCode.Accepted and selected_result[0]:
            save_project_created_at(self.project_slug, selected_result[0])
            self._date_btn.setText(f"Started: {selected_result[0]}")
            self._date_btn.setStyleSheet(
                "QPushButton { color: #999999; font-size: 8pt; border: none; padding: 0; }"
                "QPushButton:hover { color: #0078D4; }"
            )

    def _request_delete(self):
        self.delete_requested.emit(self.project_name, self.project_slug)


# ---------------------------------------------------------------------------
# Projects Panel (right side)
# ---------------------------------------------------------------------------

class ProjectsPanel(QWidget):
    project_selected = pyqtSignal(str)  # name

    def __init__(self):
        super().__init__()
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 0, 24, 16)
        layout.setSpacing(0)

        # Header row
        header_row = QHBoxLayout()

        title = QLabel("Projects")
        title.setObjectName("panel_title")
        header_row.addWidget(title)

        header_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("browse")
        refresh_btn.setToolTip("Refresh project list")
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(refresh_btn)
        header_row.addSpacing(6)

        self.gh_site_btn = QPushButton("GitHub")
        self.gh_site_btn.setObjectName("open_site")
        self.gh_site_btn.setToolTip("Open GitHub Pages (public)")
        self.gh_site_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.gh_site_btn.clicked.connect(lambda: webbrowser.open(SITE_URL))
        header_row.addWidget(self.gh_site_btn)
        header_row.addSpacing(6)

        self.gl_site_btn = QPushButton("GitLab")
        self.gl_site_btn.setObjectName("open_site")
        self.gl_site_btn.setToolTip("Open GitLab Pages (private)")
        self.gl_site_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.gl_site_btn.clicked.connect(lambda: webbrowser.open(GITLAB_SITE_URL))
        header_row.addWidget(self.gl_site_btn)
        header_row.addSpacing(6)

        self.update_all_btn = QPushButton("Update All")
        self.update_all_btn.setObjectName("upload")
        self.update_all_btn.setToolTip("Update all changed projects")
        self.update_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.update_all_btn.clicked.connect(self._on_update_all)
        self.update_all_btn.setVisible(False)
        header_row.addWidget(self.update_all_btn)

        layout.addLayout(header_row)
        layout.addSpacing(12)

        # Scrollable project list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        self.scroll.setWidget(self.list_widget)
        layout.addWidget(self.scroll, 1)
        layout.addSpacing(8)

        # Status
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

    def refresh(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = parse_projects_from_nav()

        if not projects:
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setSpacing(8)

            icon_label = QLabel("📂")
            icon_label.setStyleSheet("font-size: 32pt;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(icon_label)

            title_label = QLabel("No projects yet")
            title_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #616161;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(title_label)

            guide_label = QLabel(
                "Upload your first project:\n"
                "1. Set a project folder path on the left\n"
                "2. Select documents to upload\n"
                "3. Click GitHub or GitLab"
            )
            guide_label.setStyleSheet("color: #999999; font-size: 9pt;")
            guide_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(guide_label)

            self.list_layout.addWidget(empty_widget)
            self.status_label.setText("")
            return

        sources = load_project_sources()
        self._changed_projects = []
        for proj in projects:
            info = get_project_info(proj["slug"])
            changes = check_project_changes(proj["slug"])
            entry = sources.get(proj["slug"], {})
            source_path = entry.get("path")
            created_at = entry.get("created_at")
            if changes:
                self._changed_projects.append((proj["name"], proj["slug"]))
            card = ProjectCard(
                proj["name"],
                proj["slug"],
                info["doc_count"],
                info["attach_count"],
                info["last_updated"],
                changes=changes,
                source_path=source_path,
                created_at=created_at,
            )
            card.delete_requested.connect(self._on_delete_requested)
            card.select_requested.connect(self.project_selected)
            card.update_requested.connect(self._on_update_requested)
            self.list_layout.addWidget(card)

        self.update_all_btn.setVisible(len(self._changed_projects) > 0)
        self.status_label.setText(f"{len(projects)} projects")
        self._update_sync_status()

    def _update_sync_status(self):
        self._sync_worker = _SyncStatusWorker()
        self._sync_worker.result_ready.connect(self._apply_sync_status)
        self._sync_worker.start()

    def _apply_sync_status(self, sync):
        sync_icon = create_sync_icon()
        unsync_icon = create_unsync_icon()
        head = sync.get("head")
        if sync["synced"]:
            self.gh_site_btn.setIcon(sync_icon)
            self.gl_site_btn.setIcon(sync_icon)
        else:
            self.gh_site_btn.setIcon(sync_icon if sync["origin"] == head else unsync_icon)
            self.gl_site_btn.setIcon(sync_icon if sync["gitlab"] == head else unsync_icon)

    def _on_delete_requested(self, name, slug):
        info = get_project_info(slug)
        reply = QMessageBox.warning(
            self,
            "Delete Project",
            f'Delete "{name}" and all {info["doc_count"]} documents?\n\n'
            f"This will remove the project from the site.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self,
            "Confirm Delete",
            f'Type "{name}" to confirm deletion:',
        )
        if not ok or text.strip() != name:
            self.status_label.setText("Delete cancelled")
            return

        if _is_git_busy():
            QMessageBox.warning(self, "Busy", "Another operation is in progress. Please wait.")
            return

        _set_git_busy(True)
        self._set_buttons_enabled(False)
        self.status_label.setText("Deleting...")

        self.worker = DeleteWorker(name, slug)
        self.worker.status_update.connect(self._on_status)
        self.worker.finished.connect(self._on_delete_finished)
        self.worker.start()

    def _set_buttons_enabled(self, enabled):
        for i in range(self.list_layout.count()):
            item = self.list_layout.itemAt(i)
            if item and item.widget():
                item.widget().setEnabled(enabled)

    def _on_status(self, text):
        self.status_label.setText(text)

    def _on_delete_finished(self, success, msg):
        _set_git_busy(False)
        self._set_buttons_enabled(True)
        if success:
            self.status_label.setText("Project deleted. Site updates in 1-2 min.")
            self.refresh()
        else:
            self.status_label.setText(f"Error: {msg[:80]}")
            QMessageBox.critical(self, "Error", msg)

    def _on_update_requested(self, name, slug):
        if _is_git_busy():
            QMessageBox.warning(self, "Busy", "Another operation is in progress. Please wait.")
            return

        sources = load_project_sources()
        entry = sources.get(slug, {})
        source_path = entry.get("path")
        if not source_path or not os.path.isdir(source_path):
            QMessageBox.warning(self, "Error", "Source folder not found")
            return

        # Collect changed .md files from source
        changes = check_project_changes(slug)
        if not changes:
            self.status_label.setText("No changes detected")
            return

        # Build file list from source folder (only changed/new files)
        selected = []
        for change in changes:
            fname = change[2:]  # remove "+ " or "~ " prefix
            full = os.path.join(source_path, fname)
            if os.path.isfile(full):
                selected.append((fname, full))

        if not selected:
            self.status_label.setText("No files to update")
            return

        _set_git_busy(True)
        self._set_buttons_enabled(False)
        self.status_label.setText("Updating...")

        self.worker = UploadWorker(name, selected, GIT_REMOTES, source_path=source_path)
        self.worker.status_update.connect(self._on_status)
        self.worker.progress_update.connect(lambda pct, text: self.status_label.setText(text))
        self.worker.finished.connect(self._on_update_finished)
        self.worker.start()

    def _on_batch_progress(self, pct, desc):
        self.update_all_btn.setText(f"Pushing... {pct}%")
        self.status_label.setText(desc)

    def _on_update_finished(self, success, msg):
        _set_git_busy(False)
        self._set_buttons_enabled(True)
        self.update_all_btn.setText("Update All")
        if success:
            self.status_label.setText("Updated. Site updates in 1-2 min.")
            self.refresh()
        else:
            self.status_label.setText(f"Error: {msg[:80]}")
            QMessageBox.critical(self, "Error", msg)

    def _on_update_all(self):
        if not self._changed_projects:
            return
        if _is_git_busy():
            QMessageBox.warning(self, "Busy", "Another operation is in progress. Please wait.")
            return

        sources = load_project_sources()
        all_selected = []
        names = []
        total = len(self._changed_projects)
        for idx, (name, slug) in enumerate(self._changed_projects):
            pct = int(100 * idx / total) if total else 0
            self.update_all_btn.setText(f"Copying... {pct}%")
            QApplication.processEvents()

            entry = sources.get(slug, {})
            source_path = entry.get("path")
            if not source_path or not os.path.isdir(source_path):
                continue
            changes = check_project_changes(slug)
            if not changes:
                continue
            # Copy changed files to docs
            dest_dir = os.path.join(DOCS_DIR, slug)
            os.makedirs(dest_dir, exist_ok=True)
            for change in changes:
                fname = change[2:]
                full = os.path.join(source_path, fname)
                if os.path.isfile(full):
                    shutil.copy2(full, os.path.join(dest_dir, fname))
            # Regenerate index and nav
            md_files = [f for f in os.listdir(dest_dir) if f.lower().endswith(".md") and f != "index.md"]
            create_project_index(slug, name, md_files)
            md_files.insert(0, "index.md")
            update_mkdocs_nav(slug, name, md_files)
            names.append(name)

        if not names:
            self.update_all_btn.setText("Update All")
            self.status_label.setText("No changes to update")
            return

        _set_git_busy(True)
        self._set_buttons_enabled(False)
        self.update_all_btn.setEnabled(True)  # keep visible for progress
        self.update_all_btn.setText("Pushing... 0%")

        commit_msg = f"Update {', '.join(names)} docs"
        self._batch_worker = _BatchPushWorker(commit_msg)
        self._batch_worker.status_update.connect(self._on_status)
        self._batch_worker.progress_update.connect(self._on_batch_progress)
        self._batch_worker.finished.connect(self._on_update_finished)
        self._batch_worker.start()


class _SyncStatusWorker(QThread):
    """Check git sync status in background thread."""
    result_ready = pyqtSignal(dict)

    def run(self):
        sync = get_sync_status()
        # Also get HEAD
        try:
            r = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8",
                creationflags=_NO_WINDOW,
            )
            sync["head"] = r.stdout.strip() if r.returncode == 0 else None
        except Exception:
            sync["head"] = None
        self.result_ready.emit(sync)


class _BatchPushWorker(QThread):
    """Git add + commit + push only (files already copied)."""
    finished = pyqtSignal(bool, str)
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int, str)  # percent, description

    def __init__(self, commit_msg):
        super().__init__()
        self.commit_msg = commit_msg

    def run(self):
        try:
            total_remotes = len(GIT_REMOTES)
            self.progress_update.emit(10, "git add ...")
            subprocess.run(["git", "add", "."], cwd=REPO_DIR,
                           capture_output=True, text=True, encoding="utf-8",
                           creationflags=_NO_WINDOW)

            self.progress_update.emit(25, "git commit ...")
            subprocess.run(["git", "commit", "-m", self.commit_msg],
                           cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8",
                           creationflags=_NO_WINDOW)

            ok, err = True, ""
            for i, remote in enumerate(GIT_REMOTES):
                pct = 40 + int(55 * i / total_remotes)
                self.progress_update.emit(pct, f"git push {remote} ...")
                result = subprocess.run(["git", "push", remote, "main"],
                                        cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8",
                                        creationflags=_NO_WINDOW)
                if result.returncode != 0:
                    ok, err = False, _friendly_error(result.stderr or result.stdout)

            if ok:
                self.progress_update.emit(100, "Done")
                self.finished.emit(True, "All projects updated")
            else:
                self.finished.emit(False, err)
        except Exception as e:
            self.finished.emit(False, _friendly_error(str(e)))


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class ManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Lab Notes Manager")
        self.setWindowIcon(create_app_icon())
        self.setMinimumSize(920, 580)
        self.resize(920, 700)

        check_icon_path = create_checkmark_icon()
        self.setStyleSheet(STYLE.replace("CHECKMARK_PATH", check_icon_path))

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title area
        title_area = QWidget()
        title_layout = QVBoxLayout(title_area)
        title_layout.setContentsMargins(24, 16, 24, 0)
        title_layout.setSpacing(0)

        title = QLabel("AI Lab Notes")
        title.setObjectName("title")
        title_layout.addWidget(title)

        subtitle = QLabel("Manage your project documentation")
        subtitle.setObjectName("subtitle")
        title_layout.addWidget(subtitle)
        title_layout.addSpacing(12)

        # Horizontal separator
        h_sep = QFrame()
        h_sep.setFixedHeight(1)
        h_sep.setStyleSheet("background-color: #C5C5C5;")
        title_layout.addWidget(h_sep)
        title_layout.addSpacing(12)

        layout.addWidget(title_area)

        # Two-panel layout
        panels = QHBoxLayout()
        panels.setSpacing(0)

        # Left: Upload
        self.upload_panel = UploadPanel()
        panels.addWidget(self.upload_panel, 1)

        # Vertical separator (with bottom spacing)
        sep_container = QVBoxLayout()
        sep_container.setContentsMargins(0, 0, 0, 24)
        v_sep = QFrame()
        v_sep.setFixedWidth(1)
        v_sep.setStyleSheet("background-color: #C5C5C5;")
        sep_container.addWidget(v_sep)
        panels.addLayout(sep_container)

        # Right: Projects
        self.projects_panel = ProjectsPanel()
        panels.addWidget(self.projects_panel, 1)

        layout.addLayout(panels, 1)

        # Connect signals
        self.upload_panel.upload_finished.connect(self.projects_panel.refresh)
        self.projects_panel.project_selected.connect(self.upload_panel.set_project_name)
        self.projects_panel.refresh()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Malgun Gothic", 10))
    window = ManagerApp()
    window.show()
    sys.exit(app.exec())
