"""
Settings Manager - Centralized user preferences and feature toggles
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

class SettingsManager:
    """
    Manages user settings and feature toggles
    """
    def __init__(self, app):
        self.app = app
        self.config_dir = Path("config")
        self.settings_file = self.config_dir / "user_settings.json"
        self.settings = self._load_settings()

    def _load_settings(self):
        """Load settings from file or create defaults"""
        default_settings = {
            # Auto-save settings
            "auto_save": {
                "enabled": True,
                "interval": 300,  # 5 minutes
                "notify_on_save": True
            },
            # Macro recorder settings
            "macro_recorder": {
                "enabled": True,
                "max_macros": 50,
                "confirm_delete": True
            },
            # Project manager settings
            "project_manager": {
                "enabled": True,
                "auto_load_recent": True,
                "max_recent_projects": 10
            },
            # Script exporter settings
            "script_exporter": {
                "enabled": True,
                "default_language": "python",
                "include_comments": True
            },
            # Recent files settings
            "recent_files": {
                "enabled": True,
                "max_files": 10,
                "show_in_menu": True
            },
            # Tooltip settings
            "tooltips": {
                "enabled": True,
                "delay": 500
            },
            # UI settings
            "ui": {
                "show_unsaved_indicator": True,
                "auto_size_columns": True,
                "confirm_deletes": True
            },
            # Last session
            "last_session": {
                "last_project": None,
                "window_geometry": None,
                "last_accessed": None
            }
        }

        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults (keep any new settings)
                    for category, values in default_settings.items():
                        if category not in loaded:
                            loaded[category] = values
                        else:
                            for key, val in values.items():
                                if key not in loaded[category]:
                                    loaded[category][key] = val
                    return loaded
            except Exception as e:
                print(f"⚠️ Error loading settings: {e}")
                return default_settings
        else:
            return default_settings

    def _save_settings(self):
        """Save settings to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            print(f"✅ Settings saved")
        except Exception as e:
            print(f"⚠️ Error saving settings: {e}")

    def get(self, category, key=None):
        """Get a setting value"""
        if category not in self.settings:
            return None

        if key is None:
            return self.settings[category]

        return self.settings[category].get(key)

    def set(self, category, key, value):
        """Set a setting value"""
        if category not in self.settings:
            self.settings[category] = {}

        self.settings[category][key] = value
        self._save_settings()

        # Apply setting immediately if needed
        self._apply_setting(category, key, value)

    def _apply_setting(self, category, key, value):
        """Apply a setting immediately"""
        try:
            # Auto-save settings
            if category == "auto_save" and key == "enabled" and hasattr(self.app, 'auto_save'):
                if value:
                    # Restart auto-save if disabled
                    if not self.app.auto_save.is_running:
                        self.app.auto_save._start_auto_save()
                else:
                    # Stop auto-save
                    if self.app.auto_save.is_running:
                        self.app.auto_save.stop()

            elif category == "auto_save" and key == "interval" and hasattr(self.app, 'auto_save'):
                self.app.auto_save.auto_save_interval = value

            # Macro recorder settings
            elif category == "macro_recorder" and key == "enabled" and hasattr(self.app, 'macro_recorder'):
                # Just update the setting, recorder can still be used but we'll grey out menu
                self._update_menu_states()

            # UI settings
            elif category == "ui" and key == "show_unsaved_indicator":
                if hasattr(self.app, 'unsaved_indicator'):
                    if value:
                        self.app.unsaved_indicator.config(text="●" if self.app.data_hub.has_unsaved_changes() else "○")
                    else:
                        self.app.unsaved_indicator.config(text="")

            elif category == "tooltips" and key == "enabled" and hasattr(self.app, 'tooltip_manager'):
                if not value:
                    self.app.tooltip_manager.clear_all()

        except Exception as e:
            print(f"⚠️ Error applying setting {category}.{key}: {e}")

    def _update_menu_states(self):
        """Update menu item states based on settings"""
        if not hasattr(self.app, 'workflow_menu'):
            return

        # Enable/disable macro menu items
        macro_enabled = self.get('macro_recorder', 'enabled')
        state = tk.NORMAL if macro_enabled else tk.DISABLED

        try:
            self.app.workflow_menu.entryconfig(0, state=state)  # Start Recording
            self.app.workflow_menu.entryconfig(1, state=state)  # Stop Recording
            self.app.workflow_menu.entryconfig(3, state=state)  # Manage Macros
        except:
            pass

    def update_last_session(self, **kwargs):
        """Update last session information"""
        for key, value in kwargs.items():
            self.settings['last_session'][key] = value
        self.settings['last_session']['last_accessed'] = datetime.now().isoformat()
        self._save_settings()


class SettingsDialog:
    """
    Settings dialog with tabs for different feature categories
    """
    def __init__(self, parent, settings_manager):
        self.settings = settings_manager
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ Settings")
        self.window.geometry("700x600")
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        """Build the settings UI with tabs"""
        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main, text="Application Settings",
                 font=("TkDefaultFont", 14, "bold")).pack(pady=(0, 10))

        # Create notebook for tabs
        notebook = ttk.Notebook(main)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Feature Toggles Tab
        self._build_features_tab(notebook)

        # Auto-Save Tab
        self._build_autosave_tab(notebook)

        # Macro Recorder Tab
        self._build_macro_tab(notebook)

        # Project Manager Tab
        self._build_project_tab(notebook)

        # Script Exporter Tab
        self._build_script_tab(notebook)

        # UI Settings Tab
        self._build_ui_tab(notebook)

        # Classification Schemes Tab
        self._build_schemes_tab(notebook)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Save", command=self._save_settings, width=10).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy, width=10).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Reset to Defaults", command=self._reset_defaults, width=15).pack(side=tk.LEFT, padx=2)

    def _build_features_tab(self, notebook):
        """Build the main features toggle tab"""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="🔌 Features")

        ttk.Label(tab, text="Enable/Disable Features",
                 font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Feature toggles
        features_frame = ttk.LabelFrame(tab, text="Feature Toggles", padding=10)
        features_frame.pack(fill=tk.X, pady=5)

        self.feature_vars = {}
        features = [
            ("auto_save", "💾 Auto-Save", "Automatically save work every few minutes"),
            ("macro_recorder", "🎬 Macro Recorder", "Record and replay user workflows"),
            ("project_manager", "📁 Project Manager", "Save and load entire projects"),
            ("script_exporter", "🐍 Script Exporter", "Export workflows as Python/R scripts"),
            ("recent_files", "📜 Recent Files", "Track recently opened files"),
            ("tooltips", "💬 Tooltips", "Show helpful tooltips on hover")
        ]

        for feature_id, label, desc in features:
            frame = ttk.Frame(features_frame)
            frame.pack(fill=tk.X, pady=5)

            var = tk.BooleanVar(value=self.settings.get(feature_id, 'enabled'))
            self.feature_vars[feature_id] = var

            cb = ttk.Checkbutton(frame, text=label, variable=var)
            cb.pack(anchor=tk.W)

            ttk.Label(frame, text=desc, font=("TkDefaultFont", 8),
                     foreground="gray").pack(anchor=tk.W, padx=(20, 0))

    def _build_autosave_tab(self, notebook):
        """Build auto-save settings tab"""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="💾 Auto-Save")

        ttk.Label(tab, text="Auto-Save Settings",
                 font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Main enable
        self.autosave_enabled = tk.BooleanVar(value=self.settings.get('auto_save', 'enabled'))
        ttk.Checkbutton(tab, text="Enable Auto-Save",
                       variable=self.autosave_enabled).pack(anchor=tk.W, pady=5)

        # Interval
        interval_frame = ttk.Frame(tab)
        interval_frame.pack(fill=tk.X, pady=10, padx=20)

        ttk.Label(interval_frame, text="Auto-save interval (seconds):").pack(side=tk.LEFT)
        self.autosave_interval = tk.IntVar(value=self.settings.get('auto_save', 'interval'))
        ttk.Spinbox(interval_frame, from_=30, to=3600, textvariable=self.autosave_interval,
                   width=10).pack(side=tk.LEFT, padx=10)

        # Notify on save
        self.autosave_notify = tk.BooleanVar(value=self.settings.get('auto_save', 'notify_on_save'))
        ttk.Checkbutton(tab, text="Show notification when auto-save completes",
                       variable=self.autosave_notify).pack(anchor=tk.W, padx=20, pady=5)

        # Info
        info_text = """
        Auto-save automatically saves your work every X seconds.
        If the application crashes, you'll be prompted to recover
        your work on the next startup.
        """
        ttk.Label(tab, text=info_text, justify=tk.LEFT,
                 foreground="gray", wraplength=500).pack(pady=20)

    def _build_macro_tab(self, notebook):
        """Build macro recorder settings tab"""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="🎬 Macros")

        ttk.Label(tab, text="Macro Recorder Settings",
                 font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Main enable
        self.macro_enabled = tk.BooleanVar(value=self.settings.get('macro_recorder', 'enabled'))
        ttk.Checkbutton(tab, text="Enable Macro Recorder",
                       variable=self.macro_enabled).pack(anchor=tk.W, pady=5)

        # Max macros
        max_frame = ttk.Frame(tab)
        max_frame.pack(fill=tk.X, pady=10, padx=20)

        ttk.Label(max_frame, text="Maximum saved macros:").pack(side=tk.LEFT)
        self.macro_max = tk.IntVar(value=self.settings.get('macro_recorder', 'max_macros'))
        ttk.Spinbox(max_frame, from_=5, to=200, textvariable=self.macro_max,
                   width=10).pack(side=tk.LEFT, padx=10)

        # Confirm delete
        self.macro_confirm = tk.BooleanVar(value=self.settings.get('macro_recorder', 'confirm_delete'))
        ttk.Checkbutton(tab, text="Confirm before deleting macros",
                       variable=self.macro_confirm).pack(anchor=tk.W, padx=20, pady=5)

    def _build_project_tab(self, notebook):
        """Build project manager settings tab"""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="📁 Projects")

        ttk.Label(tab, text="Project Manager Settings",
                 font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Main enable
        self.project_enabled = tk.BooleanVar(value=self.settings.get('project_manager', 'enabled'))
        ttk.Checkbutton(tab, text="Enable Project Manager",
                       variable=self.project_enabled).pack(anchor=tk.W, pady=5)

        # Auto-load recent
        self.project_autoload = tk.BooleanVar(value=self.settings.get('project_manager', 'auto_load_recent'))
        ttk.Checkbutton(tab, text="Automatically load most recent project on startup",
                       variable=self.project_autoload).pack(anchor=tk.W, padx=20, pady=5)

        # Max recent projects
        recent_frame = ttk.Frame(tab)
        recent_frame.pack(fill=tk.X, pady=10, padx=20)

        ttk.Label(recent_frame, text="Maximum recent projects:").pack(side=tk.LEFT)
        self.project_max = tk.IntVar(value=self.settings.get('project_manager', 'max_recent_projects'))
        ttk.Spinbox(recent_frame, from_=3, to=30, textvariable=self.project_max,
                   width=10).pack(side=tk.LEFT, padx=10)

    def _build_script_tab(self, notebook):
        """Build script exporter settings tab"""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="🐍 Scripts")

        ttk.Label(tab, text="Script Exporter Settings",
                 font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Main enable
        self.script_enabled = tk.BooleanVar(value=self.settings.get('script_exporter', 'enabled'))
        ttk.Checkbutton(tab, text="Enable Script Exporter",
                       variable=self.script_enabled).pack(anchor=tk.W, pady=5)

        # Default language
        lang_frame = ttk.Frame(tab)
        lang_frame.pack(fill=tk.X, pady=10, padx=20)

        ttk.Label(lang_frame, text="Default script language:").pack(side=tk.LEFT)
        self.script_lang = tk.StringVar(value=self.settings.get('script_exporter', 'default_language'))
        ttk.Combobox(lang_frame, textvariable=self.script_lang,
                    values=["python", "r"], state="readonly", width=10).pack(side=tk.LEFT, padx=10)

        # Include comments
        self.script_comments = tk.BooleanVar(value=self.settings.get('script_exporter', 'include_comments'))
        ttk.Checkbutton(tab, text="Include explanatory comments in generated scripts",
                       variable=self.script_comments).pack(anchor=tk.W, padx=20, pady=5)

    def _build_ui_tab(self, notebook):
        """Build UI settings tab"""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="🎨 UI")

        ttk.Label(tab, text="User Interface Settings",
                 font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Show unsaved indicator
        self.ui_unsaved = tk.BooleanVar(value=self.settings.get('ui', 'show_unsaved_indicator'))
        ttk.Checkbutton(tab, text="Show unsaved changes indicator (●)",
                       variable=self.ui_unsaved).pack(anchor=tk.W, pady=5)

        # Auto-size columns
        self.ui_autosize = tk.BooleanVar(value=self.settings.get('ui', 'auto_size_columns'))
        ttk.Checkbutton(tab, text="Auto-size columns on refresh",
                       variable=self.ui_autosize).pack(anchor=tk.W, pady=5)

        # Confirm deletes
        self.ui_confirm = tk.BooleanVar(value=self.settings.get('ui', 'confirm_deletes'))
        ttk.Checkbutton(tab, text="Confirm before deleting rows",
                       variable=self.ui_confirm).pack(anchor=tk.W, pady=5)

        # Tooltip delay
        delay_frame = ttk.Frame(tab)
        delay_frame.pack(fill=tk.X, pady=10, padx=20)

        ttk.Label(delay_frame, text="Tooltip delay (ms):").pack(side=tk.LEFT)
        self.tooltip_delay = tk.IntVar(value=self.settings.get('tooltips', 'delay'))
        ttk.Spinbox(delay_frame, from_=0, to=2000, textvariable=self.tooltip_delay,
                   width=10).pack(side=tk.LEFT, padx=10)

    def _build_schemes_tab(self, notebook):
        """Build classification schemes enable/disable tab."""
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="🔬 Schemes")

        ttk.Label(tab, text="Classification Schemes",
                  font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W, pady=(0, 4))
        ttk.Label(tab, text="Uncheck schemes to hide them from the dropdown and exclude from Run All.",
                  foreground="gray", font=("TkDefaultFont", 8)).pack(anchor=tk.W, pady=(0, 8))

        self._scheme_vars = {}

        # Load current disabled set
        disabled = self._load_disabled_schemes()

        # Get schemes from engine via app reference in settings_manager
        app = self.settings.app
        schemes = []
        if hasattr(app, 'classification_engine') and app.classification_engine:
            try:
                schemes = app.classification_engine.get_available_schemes()
            except Exception:
                pass

        if not schemes:
            ttk.Label(tab, text="No classification engine loaded.",
                      foreground="gray").pack(pady=20)
            return

        # Summary label
        self._schemes_summary_var = tk.StringVar()
        ttk.Label(tab, textvariable=self._schemes_summary_var,
                  font=("TkDefaultFont", 8)).pack(anchor=tk.E, pady=(0, 4))

        # Scrollable area
        outer = ttk.Frame(tab)
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = ttk.Frame(canvas)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Group by field
        from collections import defaultdict
        by_field = defaultdict(list)
        for s in schemes:
            by_field[s.get('field', 'General')].append(s)

        for field in sorted(by_field.keys()):
            ttk.Label(inner, text=field,
                      font=("TkDefaultFont", 9, "bold"),
                      foreground="#555").pack(anchor=tk.W, padx=6, pady=(8, 2))
            ttk.Separator(inner, orient='horizontal').pack(fill=tk.X, padx=6, pady=(0, 4))

            for s in sorted(by_field[field], key=lambda x: x['name']):
                sid = s['id']
                var = tk.BooleanVar(value=sid not in disabled)
                var.trace_add('write', lambda *a: self._update_schemes_summary())
                self._scheme_vars[sid] = var

                row = ttk.Frame(inner)
                row.pack(fill=tk.X, padx=14, pady=1)
                ttk.Checkbutton(row, variable=var).pack(side=tk.LEFT)
                ttk.Label(row, text=f"{s.get('icon','📊')} {s['name']}").pack(side=tk.LEFT, padx=4)
                desc = s.get('description', s.get('category', ''))
                if desc:
                    ttk.Label(row, text=desc, foreground="gray",
                              font=("TkDefaultFont", 7)).pack(side=tk.LEFT, padx=4)

        self._update_schemes_summary()

        # Enable All / Disable All buttons
        btn_row = ttk.Frame(tab)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row, text="Enable All",
                   command=lambda: [v.set(True) for v in self._scheme_vars.values()]).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="Disable All",
                   command=lambda: [v.set(False) for v in self._scheme_vars.values()]).pack(side=tk.LEFT, padx=2)

    def _update_schemes_summary(self):
        if not hasattr(self, '_scheme_vars') or not self._scheme_vars:
            return
        total = len(self._scheme_vars)
        enabled = sum(1 for v in self._scheme_vars.values() if v.get())
        if hasattr(self, '_schemes_summary_var'):
            self._schemes_summary_var.set(f"{enabled} / {total} enabled")

    def _load_disabled_schemes(self):
        """Return set of disabled scheme ids from config/disabled_schemes.json."""
        config = Path("config/disabled_schemes.json")
        if config.exists():
            try:
                with open(config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data) if isinstance(data, list) else set()
            except Exception:
                pass
        return set()

    def _save_disabled_schemes(self):
        """Write disabled scheme ids to config/disabled_schemes.json."""
        if not hasattr(self, '_scheme_vars'):
            return
        try:
            config = Path("config/disabled_schemes.json")
            config.parent.mkdir(parents=True, exist_ok=True)
            disabled = [sid for sid, var in self._scheme_vars.items() if not var.get()]
            with open(config, 'w', encoding='utf-8') as f:
                json.dump(disabled, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save scheme settings: {e}")

    def _save_settings(self):
        """Save all settings"""
        # Feature toggles
        for feature_id, var in self.feature_vars.items():
            self.settings.set(feature_id, 'enabled', var.get())

        # Auto-save settings
        self.settings.set('auto_save', 'enabled', self.autosave_enabled.get())
        self.settings.set('auto_save', 'interval', self.autosave_interval.get())
        self.settings.set('auto_save', 'notify_on_save', self.autosave_notify.get())

        # Macro settings
        self.settings.set('macro_recorder', 'enabled', self.macro_enabled.get())
        self.settings.set('macro_recorder', 'max_macros', self.macro_max.get())
        self.settings.set('macro_recorder', 'confirm_delete', self.macro_confirm.get())

        # Project settings
        self.settings.set('project_manager', 'enabled', self.project_enabled.get())
        self.settings.set('project_manager', 'auto_load_recent', self.project_autoload.get())
        self.settings.set('project_manager', 'max_recent_projects', self.project_max.get())

        # Script settings
        self.settings.set('script_exporter', 'enabled', self.script_enabled.get())
        self.settings.set('script_exporter', 'default_language', self.script_lang.get())
        self.settings.set('script_exporter', 'include_comments', self.script_comments.get())

        # UI settings
        self.settings.set('ui', 'show_unsaved_indicator', self.ui_unsaved.get())
        self.settings.set('ui', 'auto_size_columns', self.ui_autosize.get())
        self.settings.set('ui', 'confirm_deletes', self.ui_confirm.get())
        self.settings.set('tooltips', 'delay', self.tooltip_delay.get())

        # Scheme settings
        self._save_disabled_schemes()

        # Force save
        self.settings._save_settings()

        # Refresh right panel dropdown to reflect scheme changes
        app = self.settings.app
        if hasattr(app, 'right'):
            app.right._refresh_schemes()

        messagebox.showinfo("Settings", "Settings saved successfully")
        self.window.destroy()

    def _reset_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Reset all settings to default values?"):
            # Delete settings file
            if self.settings.settings_file.exists():
                self.settings.settings_file.unlink()
            # Reload defaults
            self.settings.settings = self.settings._load_settings()
            self.window.destroy()
            # Reopen settings dialog
            SettingsDialog(self.window.master, self.settings)
