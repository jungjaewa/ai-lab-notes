"""
AI Lab Notes Manager (PyQt6)
- Left panel: Upload - Project folder -> find .md files -> upload -> auto deploy
- Right panel: Projects - View/manage uploaded projects
"""

import ctypes
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
REPO_URL = "https://github.com/jungjaewa/ai-lab-notes/tree/main/docs/"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def find_md_files(folder):
    md_files = []
    for root, dirs, files in os.walk(folder):
        depth = root.replace(folder, "").count(os.sep)
        if depth > 1:
            continue
        for f in files:
            if f.lower().endswith(".md"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, folder)
                md_files.append((rel_path, full_path))
    return sorted(md_files)


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


def create_project_index(project_slug, project_name, md_files_rel):
    index_path = os.path.join(DOCS_DIR, project_slug, "index.md")
    if os.path.exists(index_path):
        return
    lines = [
        f"# {project_name}",
        "",
        "## Documents",
        "",
        "| Document | File |",
        "|---|---|",
    ]
    for rel_name in md_files_rel:
        display = os.path.splitext(rel_name)[0].replace("-", " ").replace("_", " ")
        lines.append(f"| [{display}]({rel_name}) | `{rel_name}` |")

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
        return {"doc_count": 0, "last_updated": None, "total_size": 0}

    md_files = [f for f in os.listdir(folder) if f.lower().endswith(".md")]
    total_size = 0
    latest_mtime = 0

    for f in md_files:
        fpath = os.path.join(folder, f)
        stat = os.stat(fpath)
        total_size += stat.st_size
        if stat.st_mtime > latest_mtime:
            latest_mtime = stat.st_mtime

    last_updated = None
    if latest_mtime > 0:
        last_updated = datetime.fromtimestamp(latest_mtime)

    return {
        "doc_count": len(md_files),
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

    def __init__(self, project_name, selected_files):
        super().__init__()
        self.project_name = project_name
        self.selected_files = selected_files

    def run(self):
        try:
            project_slug = slugify(self.project_name)
            dest_dir = os.path.join(DOCS_DIR, project_slug)
            os.makedirs(dest_dir, exist_ok=True)

            total = len(self.selected_files)
            copied_rel = []
            for i, (rel_path, full_path) in enumerate(self.selected_files):
                dest_path = os.path.join(dest_dir, os.path.basename(rel_path))
                shutil.copy2(full_path, dest_path)
                copied_rel.append(os.path.basename(rel_path))
                pct = int((i + 1) / total * 30)
                self.progress_update.emit(pct, f"Uploading {pct}%")
                self.status_update.emit(f"Copying {rel_path}")

            self.progress_update.emit(40, "Uploading 40%")
            self.status_update.emit("Generating index page...")
            create_project_index(project_slug, self.project_name, copied_rel)
            if "index.md" not in copied_rel:
                copied_rel.insert(0, "index.md")

            self.progress_update.emit(50, "Uploading 50%")
            self.status_update.emit("Updating navigation...")
            update_mkdocs_nav(project_slug, self.project_name, copied_rel)

            self.progress_update.emit(60, "Uploading 60%")
            self.status_update.emit("git add .")
            subprocess.run(["git", "add", "."], cwd=REPO_DIR,
                           capture_output=True, text=True, encoding="utf-8")

            self.progress_update.emit(70, "Uploading 70%")
            self.status_update.emit("git commit")
            subprocess.run(["git", "commit", "-m", f"Add/update {self.project_name} docs"],
                           cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8")

            self.progress_update.emit(80, "Uploading 80%")
            self.status_update.emit("git push origin main...")
            result = subprocess.run(["git", "push", "origin", "main"],
                                    cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8")

            if result.returncode == 0:
                ok, err = True, ""
            else:
                ok, err = False, result.stderr or result.stdout

            self.progress_update.emit(100, "Uploading 100%")

            if ok:
                url = f"{SITE_URL}{project_slug}/"
                self.finished.emit(True, url)
            else:
                self.finished.emit(False, err[:300])

        except Exception as e:
            self.finished.emit(False, str(e))


class DeleteWorker(QThread):
    finished = pyqtSignal(bool, str)
    status_update = pyqtSignal(str)

    def __init__(self, project_name, project_slug):
        super().__init__()
        self.project_name = project_name
        self.project_slug = project_slug

    def run(self):
        try:
            self.status_update.emit("Removing files...")
            folder = os.path.join(DOCS_DIR, self.project_slug)
            if os.path.isdir(folder):
                shutil.rmtree(folder)

            self.status_update.emit("Updating navigation...")
            remove_project_from_nav(self.project_name)

            self.status_update.emit("git add .")
            subprocess.run(["git", "add", "."], cwd=REPO_DIR,
                           capture_output=True, text=True, encoding="utf-8")

            self.status_update.emit("git commit")
            subprocess.run(["git", "commit", "-m", f"Remove {self.project_name} docs"],
                           cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8")

            self.status_update.emit("git push origin main...")
            result = subprocess.run(["git", "push", "origin", "main"],
                                    cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8")

            if result.returncode == 0:
                self.finished.emit(True, "")
            else:
                self.finished.emit(False, (result.stderr or result.stdout)[:300])

        except Exception as e:
            self.finished.emit(False, str(e))


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


# ---------------------------------------------------------------------------
# Upload Panel (left side)
# ---------------------------------------------------------------------------

class UploadPanel(QWidget):
    upload_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.md_files = []
        self.checkboxes = []
        self.worker = None
        self._build_ui()

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

        # Documents Found card
        card_label = QLabel("Documents Found")
        card_label.setObjectName("subtitle")
        layout.addWidget(card_label)
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

        placeholder = QLabel("Select a path to scan for .md files")
        placeholder.setObjectName("placeholder")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list_layout.addWidget(placeholder)

        self.scroll.setWidget(self.file_list_widget)
        card_layout.addWidget(self.scroll)
        layout.addWidget(card, 1)
        layout.addSpacing(12)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.upload_btn = QPushButton("Upload")
        self.upload_btn.setObjectName("upload")
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self._upload)
        btn_row.addWidget(self.upload_btn, 1)

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
        placeholder = QLabel("Select a path to scan for .md files")
        placeholder.setObjectName("placeholder")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list_layout.addWidget(placeholder)
        self.upload_btn.setEnabled(False)
        self.upload_btn.setText("Upload")
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
            self.upload_btn.setText("Update")
        else:
            self.dup_label.setVisible(False)
            self.upload_btn.setText("Upload")

    def _scan_files(self, folder):
        self.checkboxes.clear()
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show scanning state
        self.upload_btn.setEnabled(False)
        self.status_label.setText("Scanning...")
        scanning_label = QLabel("Scanning for .md files...")
        scanning_label.setObjectName("placeholder")
        scanning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list_layout.addWidget(scanning_label)
        QApplication.processEvents()

        self.md_files = find_md_files(folder)

        # Clear scanning label
        scanning_label.deleteLater()

        if not self.md_files:
            err = QLabel("No .md files found")
            err.setObjectName("error")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_list_layout.addWidget(err)
            self.upload_btn.setEnabled(False)
            self.status_label.setText("No documents found")
            return

        for rel_path, full_path in self.md_files:
            cb = QCheckBox(rel_path)
            cb.setChecked(True)
            self.checkboxes.append(cb)
            self.file_list_layout.addWidget(cb)

        self.upload_btn.setEnabled(True)
        self.status_label.setText(f"{len(self.md_files)} documents found")
        self._check_duplicate()

    def _upload(self):
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

        self.upload_btn.setEnabled(False)
        self.status_label.setText("Uploading...")

        self.worker = UploadWorker(project_name, selected)
        self.worker.status_update.connect(self._on_status)
        self.worker.progress_update.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_status(self, text):
        self.status_label.setText(text)

    def _on_progress(self, pct, text):
        self.upload_btn.setText(text)

    def _on_finished(self, success, msg):
        self.upload_btn.setText("Upload")
        self.upload_btn.setEnabled(True)
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

    def __init__(self, name, slug, doc_count, last_updated):
        super().__init__()
        self.setObjectName("project_card")
        self.project_name = name
        self.project_slug = slug
        self.project_url = f"{SITE_URL}{slug}/"
        self.repo_url = f"{REPO_URL}{slug}/"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 8, 14, 8)
        main_layout.setSpacing(4)

        # Top row: name + meta on same line
        top_row = QHBoxLayout()
        top_row.setSpacing(0)
        name_label = QLabel(name)
        name_label.setObjectName("project_name")
        top_row.addWidget(name_label)

        top_row.addStretch()

        meta_parts = [f"{doc_count} docs"]
        if last_updated:
            meta_parts.append(last_updated.strftime('%Y-%m-%d %H:%M'))
        meta_label = QLabel("  |  ".join(meta_parts))
        meta_label.setObjectName("project_meta")
        top_row.addWidget(meta_label)
        main_layout.addLayout(top_row)

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
        copy_url_btn.setToolTip("Copy project URL")
        copy_url_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_url_btn.clicked.connect(lambda: self._copy_to_clipboard(self.project_url, copy_url_btn))
        btn_row.addWidget(copy_url_btn)

        open_btn = QPushButton()
        open_btn.setIcon(create_open_icon())
        open_btn.setObjectName("action_btn")
        open_btn.setToolTip("Open site page")
        open_btn.setFixedWidth(30)
        open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_btn.clicked.connect(self._open_in_browser)
        btn_row.addWidget(open_btn)

        repo_btn = QPushButton("Git")
        repo_btn.setObjectName("action_btn")
        repo_btn.setToolTip("Open GitHub repo")
        repo_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        repo_btn.clicked.connect(lambda: webbrowser.open(self.repo_url))
        btn_row.addWidget(repo_btn)

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

    def _open_in_browser(self):
        webbrowser.open(self.project_url)

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

        open_site_btn = QPushButton("Open Site")
        open_site_btn.setObjectName("open_site")
        open_site_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_site_btn.clicked.connect(lambda: webbrowser.open(SITE_URL))
        header_row.addWidget(open_site_btn)

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
            placeholder = QLabel("No projects uploaded yet")
            placeholder.setObjectName("placeholder")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(placeholder)
            self.status_label.setText("")
            return

        for proj in projects:
            info = get_project_info(proj["slug"])
            card = ProjectCard(
                proj["name"],
                proj["slug"],
                info["doc_count"],
                info["last_updated"],
            )
            card.delete_requested.connect(self._on_delete_requested)
            card.select_requested.connect(self.project_selected)
            self.list_layout.addWidget(card)

        self.status_label.setText(f"{len(projects)} projects")

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
        self._set_buttons_enabled(True)
        if success:
            self.status_label.setText("Project deleted. Site updates in 1-2 min.")
            self.refresh()
        else:
            self.status_label.setText(f"Error: {msg[:80]}")
            QMessageBox.critical(self, "Error", msg)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class ManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Lab Notes Manager")
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(920, 580)

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
