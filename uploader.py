"""
AI Lab Notes Uploader
- 프로젝트 폴더에서 .md 파일을 찾아 ai-lab-notes에 업로드
- git push 하면 GitHub Actions가 자동 배포
"""

import os
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ai-lab-notes 레포 경로
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(REPO_DIR, "docs")
MKDOCS_YML = os.path.join(REPO_DIR, "mkdocs.yml")
SITE_URL = "https://jungjaewa.github.io/ai-lab-notes/"


def find_md_files(folder):
    """폴더에서 .md 파일 탐색 (1단계 하위 폴더까지)"""
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
    """한글/영문 프로젝트 이름을 URL 친화적 슬러그로 변환"""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s가-힣-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text


def read_mkdocs_yml():
    with open(MKDOCS_YML, "r", encoding="utf-8") as f:
        return f.read()


def update_mkdocs_nav(project_slug, project_name, md_files_rel):
    """mkdocs.yml의 nav 섹션에 프로젝트 추가/갱신"""
    content = read_mkdocs_yml()

    # nav 섹션 파싱
    lines = content.split("\n")
    nav_start = None
    for i, line in enumerate(lines):
        if line.strip() == "nav:":
            nav_start = i
            break

    if nav_start is None:
        return

    # 기존 nav에서 이 프로젝트 항목이 있는지 확인
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
            # 다음 최상위 항목까지 찾기
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "" or (
                    lines[j].startswith("  - ") and not lines[j].startswith("    ")
                ):
                    proj_end = j
                    break
            else:
                proj_end = len(lines)
            break

    # 새 nav 항목 생성
    nav_entries = []
    nav_entries.append(f"  - {project_name}:")
    nav_entries.append(f"    - {project_slug}/index.md")
    for rel_name in md_files_rel:
        if rel_name == "index.md":
            continue
        # 파일명에서 표시 이름 생성
        display = os.path.splitext(rel_name)[0].replace("-", " ").replace("_", " ").title()
        nav_entries.append(f"    - {display}: {project_slug}/{rel_name}")

    if project_exists:
        # 기존 항목 교체
        lines[proj_start:proj_end] = nav_entries
    else:
        # 태그 항목 앞에 삽입
        tag_line = None
        for i in range(nav_start + 1, len(lines)):
            if "태그:" in lines[i] or "tags.md" in lines[i]:
                tag_line = i
                break

        if tag_line:
            lines[tag_line:tag_line] = nav_entries
        else:
            lines.extend(nav_entries)

    with open(MKDOCS_YML, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def create_project_index(project_slug, project_name, md_files_rel):
    """프로젝트 index.md 생성"""
    index_path = os.path.join(DOCS_DIR, project_slug, "index.md")
    if os.path.exists(index_path):
        return

    lines = [
        f"# {project_name}",
        "",
        "## 문서 목록",
        "",
        "| 문서 | 파일 |",
        "|---|---|",
    ]
    for rel_name in md_files_rel:
        display = os.path.splitext(rel_name)[0].replace("-", " ").replace("_", " ")
        lines.append(f"| [{display}]({rel_name}) | `{rel_name}` |")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def git_push(message):
    """git add + commit + push"""
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


class UploaderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Lab Notes Uploader")
        self.root.geometry("520x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        self.md_files = []
        self.check_vars = []

        self._build_ui()

    def _build_ui(self):
        # 스타일
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), background="#f5f5f5")
        style.configure("TLabel", font=("Segoe UI", 10), background="#f5f5f5")
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Upload.TButton", font=("Segoe UI", 11, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 9), background="#f5f5f5")

        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        # 타이틀
        ttk.Label(main, text="AI Lab Notes Uploader", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(8, 12))

        # 프로젝트 경로
        path_frame = ttk.Frame(main)
        path_frame.pack(fill=tk.X)
        ttk.Label(path_frame, text="프로젝트 경로:").pack(anchor=tk.W)

        entry_frame = ttk.Frame(main)
        entry_frame.pack(fill=tk.X, pady=(4, 0))
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(entry_frame, textvariable=self.path_var, font=("Segoe UI", 10))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(entry_frame, text="찾아보기", command=self._browse).pack(side=tk.RIGHT)

        # 프로젝트 이름
        name_frame = ttk.Frame(main)
        name_frame.pack(fill=tk.X, pady=(12, 0))
        ttk.Label(name_frame, text="프로젝트 이름:").pack(anchor=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var, font=("Segoe UI", 10)).pack(
            fill=tk.X, pady=(4, 0)
        )

        # 발견된 문서 목록
        list_frame = ttk.LabelFrame(main, text="발견된 문서", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        self.file_list_frame = ttk.Frame(list_frame)
        self.file_list_frame.pack(fill=tk.BOTH, expand=True)

        self.no_files_label = ttk.Label(
            self.file_list_frame, text="경로를 선택하면 .md 파일을 탐색합니다", foreground="gray"
        )
        self.no_files_label.pack(pady=20)

        # 업로드 버튼
        self.upload_btn = ttk.Button(
            main, text="업로드", style="Upload.TButton", command=self._upload, state=tk.DISABLED
        )
        self.upload_btn.pack(fill=tk.X, pady=(12, 0), ipady=4)

        # 상태 표시
        self.status_var = tk.StringVar(value="준비")
        ttk.Label(main, textvariable=self.status_var, style="Status.TLabel", foreground="gray").pack(
            anchor=tk.W, pady=(8, 0)
        )

    def _browse(self):
        folder = filedialog.askdirectory(title="프로젝트 폴더 선택")
        if folder:
            self.path_var.set(folder)
            folder_name = os.path.basename(folder)
            self.name_var.set(folder_name)
            self._scan_files(folder)

    def _scan_files(self, folder):
        # 기존 체크박스 제거
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        self.md_files = find_md_files(folder)
        self.check_vars = []

        if not self.md_files:
            ttk.Label(self.file_list_frame, text=".md 파일이 없습니다", foreground="red").pack(pady=20)
            self.upload_btn.configure(state=tk.DISABLED)
            return

        # 스크롤 가능한 프레임
        canvas = tk.Canvas(self.file_list_frame, bg="white", highlightthickness=0, height=140)
        scrollbar = ttk.Scrollbar(self.file_list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        for rel_path, full_path in self.md_files:
            var = tk.BooleanVar(value=True)
            self.check_vars.append(var)
            cb = ttk.Checkbutton(scroll_frame, text=rel_path, variable=var)
            cb.pack(anchor=tk.W, padx=4, pady=2)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.upload_btn.configure(state=tk.NORMAL)
        self.status_var.set(f"{len(self.md_files)}개 문서 발견")

    def _upload(self):
        project_name = self.name_var.get().strip()
        if not project_name:
            messagebox.showwarning("경고", "프로젝트 이름을 입력해주세요")
            return

        selected = [
            (rel, full)
            for (rel, full), var in zip(self.md_files, self.check_vars)
            if var.get()
        ]
        if not selected:
            messagebox.showwarning("경고", "업로드할 문서를 선택해주세요")
            return

        self.upload_btn.configure(state=tk.DISABLED)
        self.status_var.set("업로드 중...")
        self.root.update()

        # 백그라운드에서 실행
        threading.Thread(
            target=self._do_upload, args=(project_name, selected), daemon=True
        ).start()

    def _do_upload(self, project_name, selected):
        try:
            project_slug = slugify(project_name)
            dest_dir = os.path.join(DOCS_DIR, project_slug)
            os.makedirs(dest_dir, exist_ok=True)

            # 파일 복사
            copied_rel = []
            for rel_path, full_path in selected:
                # 하위 폴더 구조 유지
                dest_path = os.path.join(dest_dir, os.path.basename(rel_path))
                shutil.copy2(full_path, dest_path)
                copied_rel.append(os.path.basename(rel_path))

            # index.md 생성
            create_project_index(project_slug, project_name, copied_rel)
            if "index.md" not in copied_rel:
                copied_rel.insert(0, "index.md")

            # mkdocs.yml nav 업데이트
            update_mkdocs_nav(project_slug, project_name, copied_rel)

            # git push
            self._update_status("Git push 중...")
            ok, err = git_push(f"Add/update {project_name} docs")

            if ok:
                url = f"{SITE_URL}{project_slug}/"
                self._update_status(f"완료! {url}")
                self.root.after(0, lambda: messagebox.showinfo(
                    "업로드 완료",
                    f"문서 {len(selected)}개 업로드 완료!\n\n"
                    f"1~2분 후 확인 가능:\n{url}"
                ))
            else:
                self._update_status(f"Git 오류: {err[:100]}")
                self.root.after(0, lambda: messagebox.showerror("Git 오류", err[:300]))

        except Exception as e:
            self._update_status(f"오류: {e}")
            self.root.after(0, lambda: messagebox.showerror("오류", str(e)))

        finally:
            self.root.after(0, lambda: self.upload_btn.configure(state=tk.NORMAL))

    def _update_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = UploaderApp()
    app.run()
