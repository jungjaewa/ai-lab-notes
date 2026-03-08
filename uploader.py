"""
AI Lab Notes Uploader (PyQt6)
- Project folder -> find .md files -> upload to ai-lab-notes -> auto deploy
"""

import os
import re
import shutil
import subprocess
import sys
import threading

import tempfile

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

# ai-lab-notes repo path
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(REPO_DIR, "docs")
MKDOCS_YML = os.path.join(REPO_DIR, "mkdocs.yml")
SITE_URL = "https://jungjaewa.github.io/ai-lab-notes/"


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


def git_push(message):
    cmds = [
        ["git", "add", "."],
        ["git", "commit", "-m", message],
        ["git", "push", "origin", "main"],
    ]
    for cmd in cmds:
        result = subprocess.run(
            cmd, cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            return False, result.stderr or result.stdout
    return True, ""


# Background upload worker
class UploadWorker(QThread):
    finished = pyqtSignal(bool, str)
    status_update = pyqtSignal(str)

    def __init__(self, project_name, selected_files):
        super().__init__()
        self.project_name = project_name
        self.selected_files = selected_files

    def run(self):
        try:
            project_slug = slugify(self.project_name)
            dest_dir = os.path.join(DOCS_DIR, project_slug)
            os.makedirs(dest_dir, exist_ok=True)

            copied_rel = []
            for rel_path, full_path in self.selected_files:
                dest_path = os.path.join(dest_dir, os.path.basename(rel_path))
                shutil.copy2(full_path, dest_path)
                copied_rel.append(os.path.basename(rel_path))

            create_project_index(project_slug, self.project_name, copied_rel)
            if "index.md" not in copied_rel:
                copied_rel.insert(0, "index.md")

            update_mkdocs_nav(project_slug, self.project_name, copied_rel)

            self.status_update.emit("Pushing to Git...")
            ok, err = git_push(f"Add/update {self.project_name} docs")

            if ok:
                url = f"{SITE_URL}{project_slug}/"
                self.finished.emit(True, url)
            else:
                self.finished.emit(False, err[:300])

        except Exception as e:
            self.finished.emit(False, str(e))


# Windows 11 style constants
STYLE = """
QMainWindow {
    background-color: #FFFFFF;
}
QLabel {
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
QFrame#separator {
    background-color: #E5E5E5;
    max-height: 1px;
}
QFrame#card {
    background-color: #FBFBFB;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
}
QScrollArea {
    border: none;
    background-color: #FBFBFB;
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


def create_checkmark_icon():
    """Create a white checkmark icon for checked state."""
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


class UploaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Lab Notes Uploader")
        self.setFixedSize(540, 520)

        check_icon_path = create_checkmark_icon()
        self.setStyleSheet(STYLE.replace("CHECKMARK_PATH", check_icon_path))

        self.md_files = []
        self.checkboxes = []
        self.worker = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(0)

        # Title
        title = QLabel("AI Lab Notes")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("Upload project documents to your knowledge base")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(16)

        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)
        layout.addSpacing(16)

        # Project Path
        layout.addWidget(QLabel("Project Path"))
        layout.addSpacing(6)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Paste path or click Browse")
        self.path_edit.returnPressed.connect(self._on_path_entered)
        path_row.addWidget(self.path_edit)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browse")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)

        layout.addLayout(path_row)
        layout.addSpacing(14)

        # Project Name
        layout.addWidget(QLabel("Project Name"))
        layout.addSpacing(6)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Auto-filled from folder name")
        layout.addWidget(self.name_edit)
        layout.addSpacing(16)

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

        self.placeholder = QLabel("Select a path to scan for .md files")
        self.placeholder.setObjectName("placeholder")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list_layout.addWidget(self.placeholder)

        self.scroll.setWidget(self.file_list_widget)
        card_layout.addWidget(self.scroll)
        layout.addWidget(card, 1)
        layout.addSpacing(16)

        # Upload button
        self.upload_btn = QPushButton("Upload")
        self.upload_btn.setObjectName("upload")
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self._upload)
        layout.addWidget(self.upload_btn)
        layout.addSpacing(10)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

    def _normalize_path(self, path):
        path = path.strip().strip('"').strip("'")
        return path.replace("\\", "/")

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

    def _scan_files(self, folder):
        # Clear existing checkboxes
        self.checkboxes.clear()
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.md_files = find_md_files(folder)

        if not self.md_files:
            err = QLabel("No .md files found")
            err.setObjectName("error")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_list_layout.addWidget(err)
            self.upload_btn.setEnabled(False)
            return

        for rel_path, full_path in self.md_files:
            cb = QCheckBox(rel_path)
            cb.setChecked(True)
            self.checkboxes.append(cb)
            self.file_list_layout.addWidget(cb)

        self.upload_btn.setEnabled(True)
        self.status_label.setText(f"{len(self.md_files)} documents found")

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
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_status(self, text):
        self.status_label.setText(text)

    def _on_finished(self, success, msg):
        self.upload_btn.setEnabled(True)
        if success:
            self.status_label.setText(f"Done! {msg}")
            QMessageBox.information(
                self, "Upload Complete",
                f"Documents uploaded!\n\nAvailable in 1-2 min:\n{msg}"
            )
        else:
            self.status_label.setText(f"Error: {msg[:80]}")
            QMessageBox.critical(self, "Error", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Malgun Gothic", 10))
    window = UploaderApp()
    window.show()
    sys.exit(app.exec())
