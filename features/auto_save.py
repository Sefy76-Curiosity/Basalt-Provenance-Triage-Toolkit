"""
Auto-Save Manager - Automatically saves work in progress
FIXED: Added threading lock to prevent race conditions
"""

import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox

class AutoSaveManager:
    """
    Manages automatic saving of work in progress
    """
    def __init__(self, app, auto_save_interval=300):  # 5 minutes default
        self.app = app
        self.auto_save_dir = Path("auto_save")
        self.auto_save_interval = auto_save_interval  # seconds
        self.last_auto_save = None
        self.is_running = False
        self.auto_save_thread = None
        self.recovery_file = self.auto_save_dir / "recovery.stproj"

        # 🔐 Thread safety locks
        self._save_lock = threading.Lock()
        self._data_lock = threading.Lock()

        # Create auto-save directory
        self.auto_save_dir.mkdir(parents=True, exist_ok=True)

        # Check for recovery on startup
        self._check_for_recovery()

        # Start auto-save thread
        self._start_auto_save()

    def _start_auto_save(self):
        """Start the auto-save background thread"""
        self.is_running = True
        self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self.auto_save_thread.start()

    def _auto_save_loop(self):
        """Background loop that performs auto-saves"""
        while self.is_running:
            time.sleep(self.auto_save_interval)

            # 🔐 Thread-safe check for unsaved changes
            with self._data_lock:
                has_changes = self.app.data_hub.has_unsaved_changes()

            if has_changes:
                self._perform_auto_save()

    def _perform_auto_save(self):
        """Perform an auto-save with thread safety"""
        # 🔐 Use lock to prevent concurrent saves
        with self._save_lock:
            try:
                # Get project data with thread safety
                with self._data_lock:
                    project_data = self.app.project_manager._collect_project_data()

                # Add auto-save metadata
                project_data['metadata']['auto_save'] = True
                project_data['metadata']['auto_save_time'] = datetime.now().isoformat()

                # Write to temporary file first, then rename (atomic operation)
                temp_file = self.recovery_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=2)

                # Atomic rename (POSIX) - on Windows, replace if exists
                if temp_file.exists():
                    if self.recovery_file.exists():
                        self.recovery_file.unlink()
                    temp_file.rename(self.recovery_file)

                with self._data_lock:
                    self.last_auto_save = datetime.now()
                    self.app.data_hub.mark_saved()

                # Update status bar occasionally
                if self.app.root:
                    self.app.root.after(0, lambda: self._show_auto_save_status())

            except Exception as e:
                # Log error silently - don't crash
                print(f"Auto-save error: {e}")
                # Clean up temp file if it exists
                if 'temp_file' in locals() and temp_file.exists():
                    try:
                        temp_file.unlink()
                    except:
                        pass

    def _show_auto_save_status(self):
        """Show auto-save status in the status bar"""
        if self.last_auto_save:
            time_str = self.last_auto_save.strftime("%H:%M:%S")
            self.app.center.set_status(f"💾 Auto-saved at {time_str}", "info")

    def _check_for_recovery(self):
        """Check if there's a recovery file from a previous crash"""
        if self.recovery_file.exists():
            # Check if it's recent (less than 24 hours old)
            mod_time = datetime.fromtimestamp(self.recovery_file.stat().st_mtime)
            age = datetime.now() - mod_time

            if age < timedelta(hours=24):
                # Ask user if they want to recover
                self.app.root.after(1000, lambda: self._ask_recovery(mod_time))

    def _ask_recovery(self, mod_time):
        """Ask user if they want to recover unsaved work"""
        time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")

        response = messagebox.askyesno(
            "Recover Unsaved Work?",
            f"Found unsaved work from {time_str} ({int((datetime.now() - mod_time).total_seconds() / 60)} minutes ago).\n\n"
            "Would you like to recover it?\n\n"
            "Yes: Load the auto-saved work\n"
            "No: Start fresh and delete the recovery file"
        )

        if response:
            # Load recovery file
            success = self.app.project_manager.load_project(str(self.recovery_file))
            if success:
                self.app.center.set_status("✅ Recovered auto-saved work", "success")
        else:
            # Delete recovery file
            self.recovery_file.unlink()

    def manual_save_triggered(self):
        """Called when user manually saves - we can clean up auto-save"""
        with self._data_lock:
            if self.recovery_file.exists():
                self.recovery_file.unlink()
            self.app.data_hub.mark_saved()

    def stop(self):
        """Stop the auto-save thread"""
        self.is_running = False
        if self.auto_save_thread:
            self.auto_save_thread.join(timeout=1)
