"""
HTTP Update Checker – GitLab first, then GitHub, with status‑only feedback.
All errors/messages go to status bar; details on click.
"""
import urllib.request
import json
import hashlib
import os
import re
import threading
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

class HTTPUpdateChecker:
    def __init__(self, app, local_version, owner="Sefy76-Curiosity", repo="Basalt-Provenance-Triage-Toolkit", branch="main"):
        self.app = app
        self.local_version = local_version          # store the local version string
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.repo_path = Path(__file__).parent.parent
        self.commit_file = self.repo_path / "config" / ".last_commit"
        self.commit_file.parent.mkdir(exist_ok=True)
        self.active_source = None

    def check(self):
        """Check for updates – no popups, only status bar updates."""
        def run():
            errors = []
            remote_ver = None

            # 1. Try GitLab (your exact working URL)
            gitlab_url = f"https://gitlab.com/sefy76/scientific-toolkit/-/raw/{self.branch}/Scientific-Toolkit.py?ref_type=heads"
            try:
                with urllib.request.urlopen(gitlab_url, timeout=10) as resp:
                    content = resp.read().decode('utf-8')
                    match = re.search(r'APP_INFO\s*=\s*{.*?"version"\s*:\s*"([^"]+)"', content, re.DOTALL)
                    if match:
                        remote_ver = match.group(1)
                        self.active_source = 'gitlab'
            except Exception as e:
                errors.append(f"GitLab ({gitlab_url}): {str(e)}")

            # 2. If GitLab fails, try GitHub
            if remote_ver is None:
                github_url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/refs/heads/{self.branch}/Scientific-Toolkit.py"
                try:
                    with urllib.request.urlopen(github_url, timeout=10) as resp:
                        content = resp.read().decode('utf-8')
                        match = re.search(r'APP_INFO\s*=\s*{.*?"version"\s*:\s*"([^"]+)"', content, re.DOTALL)
                        if match:
                            remote_ver = match.group(1)
                            self.active_source = 'github'
                except Exception as e:
                    errors.append(f"GitHub ({github_url}): {str(e)}")

            # If both failed, show the errors in status bar (clickable)
            if remote_ver is None:
                error_msg = "\n".join(errors)
                self.app.root.after(0, lambda msg=error_msg: self._set_error_status(msg))
                return

            local_ver = self.local_version   # use stored local version

            if remote_ver == local_ver:
                self.app.root.after(0, lambda: self.app.center.set_status("✅ No updates available", "info"))
                return

            # Version differs – proceed with update check using GitHub API
            try:
                latest_sha = self._get_latest_commit()
            except Exception as e:
                self.app.root.after(0, lambda msg=f"Failed to get commit: {e}": self._set_error_status(msg))
                return

            stored_sha = self._get_stored_commit()

            if stored_sha is None:
                self._save_commit(latest_sha)
                self.app.root.after(0, lambda: self._set_update_available_status(remote_ver))
                return

            try:
                changed = self._get_changed_files(stored_sha, latest_sha)
            except Exception as e:
                self.app.root.after(0, lambda msg=f"Failed to get changed files: {e}": self._set_error_status(msg))
                return

            if not changed:
                self._save_commit(latest_sha)
                self.app.root.after(0, lambda: self.app.center.set_status("✅ No file changes", "info"))
                return

            self.app.root.after(0, lambda: self._set_update_ready_status(changed, latest_sha, remote_ver))

        threading.Thread(target=run, daemon=True).start()

    def _set_error_status(self, message):
        """Store full error in last_operation and set status bar text."""
        self.app.center.last_operation = {
            'type': 'update_error',
            'error': message
        }
        self.app.center.set_status("❌ Update check failed – click for details", "error")

    def _set_update_available_status(self, new_version):
        self.app.center.last_operation = {
            'type': 'update_available',
            'new_version': new_version,
            'source': self.active_source
        }
        self.app.center.set_status(f"🔄 Version {new_version} available – click to download", "info")

    def _set_update_ready_status(self, changed_files, new_commit, new_version):
        self.app.center.last_operation = {
            'type': 'app_update',
            'changed': changed_files,
            'new_commit': new_commit,
            'new_version': new_version,
            'count': len(changed_files)
        }
        self.app.center.set_status(f"🔄 {len(changed_files)} file(s) updated – click for details", "info")

    # ------------------------------------------------------------------
    # GitHub API helpers (unchanged)
    # ------------------------------------------------------------------
    def _get_latest_commit(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/branches/{self.branch}"
        req = urllib.request.Request(url, headers={"User-Agent": "Scientific-Toolkit"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['commit']['sha']

    def _get_stored_commit(self):
        if self.commit_file.exists():
            with open(self.commit_file) as f:
                return f.read().strip()
        return None

    def _save_commit(self, sha):
        with open(self.commit_file, 'w') as f:
            f.write(sha)

    def _get_changed_files(self, base_sha, head_sha):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/compare/{base_sha}...{head_sha}"
        req = urllib.request.Request(url, headers={"User-Agent": "Scientific-Toolkit"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return [f['filename'] for f in data['files'] if f['status'] != 'removed']

    # ------------------------------------------------------------------
    # Download logic (same as before)
    # ------------------------------------------------------------------
    def _download_file(self, url, target_path, expected_sha256=None):
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
                    sha256 = hashlib.sha256()
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded = 0
                    chunk_size = 8192
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        tmp.write(chunk)
                        sha256.update(chunk)
                        downloaded += len(chunk)
                    tmp_path = tmp.name

            if expected_sha256:
                file_hash = sha256.hexdigest()
                if file_hash.lower() != expected_sha256.lower():
                    os.unlink(tmp_path)
                    return False

            target_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(tmp_path, target_path)
            return True

        except Exception:
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            return False

    # ------------------------------------------------------------------
    # Update dialog (shown when user clicks status bar)
    # ------------------------------------------------------------------
    def show_update_dialog(self, changed_files, new_commit, new_version):
        win = tk.Toplevel(self.app.root)
        win.title(f"🔄 Update to v{new_version}")
        win.geometry("600x450")
        win.transient(self.app.root)

        main = ttk.Frame(win, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f"The following {len(changed_files)} files will be updated:",
                  font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)

        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        for f in changed_files:
            listbox.insert(tk.END, f)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        progress = ttk.Progressbar(main, mode='determinate')
        progress.pack(fill=tk.X, pady=5)
        status_var = tk.StringVar(value="Ready to download")
        ttk.Label(main, textvariable=status_var).pack()

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)
        download_btn = ttk.Button(btn_frame, text="⬇️ Download Updates",
                                  command=lambda: self._perform_update(win, changed_files, new_commit,
                                                                        new_version, progress, status_var))
        download_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _perform_update(self, win, changed_files, new_commit, new_version, progress, status_var):
        def download():
            total = len(changed_files)
            for i, path in enumerate(changed_files):
                status_var.set(f"Downloading {path}...")
                progress['value'] = (i / total) * 100
                win.update()

                # Use the active source for download
                if self.active_source == 'gitlab':
                    url = f"https://gitlab.com/sefy76/scientific-toolkit/-/raw/{self.branch}/{path}?ref_type=heads"
                else:
                    url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/refs/heads/{self.branch}/{path}"
                target = self.repo_path / path
                success = self._download_file(url, target)
                if not success:
                    failed_path = path
                    win.after(0, lambda p=failed_path: messagebox.showerror("Error", f"Failed to download {p}"))
                    return

            self._save_commit(new_commit)
            win.after(0, lambda: self._update_complete(win, new_version))

        threading.Thread(target=download, daemon=True).start()

    def _update_complete(self, win, new_version):
        messagebox.showinfo("Update Complete", f"Updated to v{new_version}.\nPlease restart the application.")
        win.destroy()
