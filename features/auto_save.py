"""
Auto-Save Manager - Automatically saves work in progress
FIXED: Added proper cleanup of after callbacks and thread safety
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

        # 🔹 Track after callbacks to cancel them on shutdown
        self._after_ids = []
        self._recovery_after_id = None

        # 🔐 Thread safety locks
        self._save_lock = threading.Lock()
        self._data_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._shutdown_flag = False

        # Create auto-save directory
        self.auto_save_dir.mkdir(parents=True, exist_ok=True)

        # Check for recovery on startup
        self._check_for_recovery()

        # Start auto-save thread
        self._start_auto_save()

    def _start_auto_save(self):
        """Start the auto-save background thread"""
        self.is_running = True
        self._stop_event.clear()
        self._shutdown_flag = False
        self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self.auto_save_thread.start()

    def _auto_save_loop(self):
        """Background loop that performs auto-saves"""
        while self.is_running and not self._stop_event.is_set() and not self._shutdown_flag:
            # Use event wait with timeout instead of sleep (more responsive to stop)
            if self._stop_event.wait(timeout=self.auto_save_interval):
                # If stop event was set, exit immediately
                break

            # 🔐 Thread-safe check for unsaved changes
            try:
                with self._data_lock:
                    # Check if app still exists and has data_hub
                    if not hasattr(self.app, 'data_hub') or self.app.data_hub is None:
                        break
                    has_changes = self.app.data_hub.has_unsaved_changes()

                if has_changes and not self._shutdown_flag:
                    self._perform_auto_save()
            except Exception:
                # If any error occurs (like app shutting down), exit gracefully
                break

    def _perform_auto_save(self):
        """Perform an auto-save with thread safety"""
        # 🔐 Use lock to prevent concurrent saves
        with self._save_lock:
            try:
                # Check if app still exists
                if not hasattr(self.app, 'project_manager') or self.app.project_manager is None:
                    return

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

                # 🔹 FIX: Schedule UI update with proper error handling and tracking
                self._safe_after_call(self._show_auto_save_status)

            except (AttributeError, RuntimeError, tk.TclError):
                # App is shutting down - exit silently
                pass
            except Exception as e:
                # Log error silently - don't crash
                print(f"Auto-save error: {e}")
                # Clean up temp file if it exists
                if 'temp_file' in locals() and temp_file.exists():
                    try:
                        temp_file.unlink()
                    except:
                        pass

    def _safe_after_call(self, callback, *args, **kwargs):
        """Safely schedule a callback with proper cleanup"""
        try:
            if self._shutdown_flag:
                return

            if self.app.root and self.app.root.winfo_exists():
                # Create a wrapper that will remove the ID when executed
                def wrapped_callback():
                    try:
                        if not self._shutdown_flag:
                            callback(*args, **kwargs)
                    except (tk.TclError, RuntimeError, AttributeError):
                        # Window destroyed during callback - ignore
                        pass
                    finally:
                        # Remove this after_id from the list
                        if after_id in self._after_ids:
                            self._after_ids.remove(after_id)

                after_id = self.app.root.after(0, wrapped_callback)
                self._after_ids.append(after_id)
            else:
                # Window doesn't exist, execute directly if safe
                if not self._shutdown_flag:
                    try:
                        callback(*args, **kwargs)
                    except (tk.TclError, RuntimeError):
                        pass
        except (tk.TclError, RuntimeError, AttributeError):
            # Window has been destroyed - ignore
            pass

    def _execute_callback(self, callback, *args, **kwargs):
        """Execute a callback and remove its after ID"""
        try:
            # Remove this after_id from the list
            if hasattr(self, '_after_ids'):
                # Find and remove the current callback's ID
                import inspect
                frame = inspect.currentframe()
                # This is tricky - we're in the callback, so we don't have the ID easily
                # Alternative: clear all after_ids periodically or just let them be
                pass

            if not self._shutdown_flag:
                callback(*args, **kwargs)
        except (tk.TclError, RuntimeError, AttributeError):
            # Window destroyed during callback
            pass

    def _show_auto_save_status(self):
        """Show auto-save status in the status bar - MUST be called from main thread"""
        try:
            # Check if app and center still exist
            if self._shutdown_flag:
                return

            if not hasattr(self.app, 'center') or self.app.center is None:
                return

            if self.last_auto_save:
                time_str = self.last_auto_save.strftime("%H:%M:%S")
                self.app.center.set_status(f"💾 Auto-saved at {time_str}", "info")
        except (tk.TclError, RuntimeError, AttributeError):
            # Window has been destroyed - ignore
            pass

    def _check_for_recovery(self):
        """Check if there's a recovery file from a previous crash"""
        if self.recovery_file.exists():
            # Check if it's recent (less than 24 hours old)
            mod_time = datetime.fromtimestamp(self.recovery_file.stat().st_mtime)
            age = datetime.now() - mod_time

            if age < timedelta(hours=24):
                # Ask user if they want to recover - store the after ID
                self._recovery_after_id = self.app.root.after(1000, lambda: self._ask_recovery(mod_time))

    def _ask_recovery(self, mod_time):
        """Ask user if they want to recover unsaved work"""
        try:
            if self._shutdown_flag:
                return

            time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")

            response = messagebox.askyesno(
                "Recover Unsaved Work?",
                f"Found unsaved work from {time_str} ({int((datetime.now() - mod_time).total_seconds() / 60)} minutes ago).\n\n"
                "Would you like to recover it?\n\n"
                "Yes: Load the auto-saved work\n"
                "No: Start fresh and delete the recovery file"
            )

            if not self._shutdown_flag:
                if response:
                    # Load recovery file
                    success = self.app.project_manager.load_project(str(self.recovery_file))
                    if success:
                        self.app.center.set_status("✅ Recovered auto-saved work", "success")
                else:
                    # Delete recovery file
                    self.recovery_file.unlink()
        except (tk.TclError, RuntimeError, AttributeError):
            # Window has been destroyed - ignore
            pass

    def manual_save_triggered(self):
        """Called when user manually saves - we can clean up auto-save"""
        try:
            with self._data_lock:
                if self.recovery_file.exists():
                    self.recovery_file.unlink()
                self.app.data_hub.mark_saved()
        except (AttributeError, RuntimeError):
            # App is shutting down - ignore
            pass

    def stop(self):
        """Stop the auto-save thread and cancel all pending callbacks"""
        print("🛑 Stopping auto-save manager...")
        self._shutdown_flag = True
        self.is_running = False
        self._stop_event.set()  # Signal thread to stop

        # 🔹 Cancel all pending after callbacks FIRST
        self._cancel_all_after_callbacks()

        # Then stop the thread
        if self.auto_save_thread and self.auto_save_thread.is_alive():
            self.auto_save_thread.join(timeout=2)  # Wait up to 2 seconds

        print("✅ Auto-save manager stopped")

    def _cancel_all_after_callbacks(self):
        """Cancel all pending after callbacks"""
        # Cancel recovery after callback
        if self._recovery_after_id:
            try:
                # Check if root still exists before cancelling
                if self.app.root and self.app.root.winfo_exists():
                    self.app.root.after_cancel(self._recovery_after_id)
                    print(f"✅ Cancelled recovery callback: {self._recovery_after_id}")
            except (tk.TclError, RuntimeError, AttributeError) as e:
                print(f"⚠️ Could not cancel recovery callback: {e}")
            self._recovery_after_id = None

        # Cancel all tracked after callbacks
        cancelled_count = 0
        for after_id in self._after_ids[:]:  # Use a copy of the list
            try:
                if self.app.root and self.app.root.winfo_exists():
                    self.app.root.after_cancel(after_id)
                    cancelled_count += 1
            except (tk.TclError, RuntimeError, AttributeError) as e:
                print(f"⚠️ Could not cancel callback {after_id}: {e}")

        if cancelled_count > 0:
            print(f"✅ Cancelled {cancelled_count} pending callbacks")

        self._after_ids.clear()

    def __del__(self):
        """Cleanup when object is deleted"""
        self.stop()
