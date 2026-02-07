"""
Enhanced Plugin Manager with Dynamic Discovery
Automatically detects all plugins in plugins/ folder

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import subprocess
import threading
import importlib.util
import ast
from pathlib import Path


class PluginManager(tk.Toplevel):
    """Enhanced plugin manager with dynamic plugin discovery"""

    def __init__(self, parent_app):
        """Initialize the plugin manager"""
        super().__init__(parent_app.root)
        self.app = parent_app
        self.title("Plugin Manager - v10.1 FINAL")
        self.geometry("850x650")
        self.resizable(False, False)

        # Make this window stay on top of main window
        self.transient(parent_app.root)

        # Discover available plugins dynamically
        self.available_plugins = self._discover_plugins()

        # Dictionary to store checkbox variables and UI elements
        self.plugin_vars = {}
        self.status_labels = {}
        self.install_buttons = {}

        # Load current enabled plugins
        self.enabled_plugins = self._load_enabled_plugins()

        # Create UI
        self._create_ui()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (850 // 2)
        y = (self.winfo_screenheight() // 2) - (650 // 2)
        self.geometry(f'+{x}+{y}')

        # Make modal and bring to front
        self.grab_set()
        self.lift()
        self.focus_force()

    def _discover_plugins(self):
        """Dynamically discover all plugins in plugins/ folder"""
        plugin_dir = Path("plugins")
        discovered = {}

        if not plugin_dir.exists():
            return discovered

        for py_file in plugin_dir.glob("*.py"):
            # Skip special files
            if py_file.stem in ["__init__", "plugin_manager"]:
                continue

            try:
                # Import module to read PLUGIN_INFO
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check for PLUGIN_INFO metadata
                if hasattr(module, 'PLUGIN_INFO'):
                    info = module.PLUGIN_INFO
                    discovered[info['id']] = info

            except ImportError as e:
                # Plugin has missing dependencies - try to extract PLUGIN_INFO from file
                print(f"Plugin {py_file.stem} has missing dependencies: {e}")
                try:
                    # Read file and extract PLUGIN_INFO using AST
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Parse with AST to find PLUGIN_INFO
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == 'PLUGIN_INFO':
                                    # Safely evaluate the dictionary
                                    info = ast.literal_eval(node.value)
                                    info['_load_error'] = str(e)
                                    info['_file'] = py_file.stem
                                    discovered[info['id']] = info
                                    break

                    # If AST parsing failed, try string extraction
                    if py_file.stem not in discovered:
                        import re
                        # Look for PLUGIN_INFO = {...}
                        match = re.search(r'PLUGIN_INFO\s*=\s*({.*?})', content, re.DOTALL)
                        if match:
                            try:
                                # Simple eval for dictionary
                                info = eval(match.group(1), {"__builtins__": {}}, {})
                                info['_load_error'] = str(e)
                                info['_file'] = py_file.stem
                                if 'id' not in info:
                                    info['id'] = py_file.stem
                                discovered[info['id']] = info
                            except:
                                pass

                except Exception as parse_error:
                    print(f"Could not parse plugin {py_file.stem}: {parse_error}")
                    # Add as broken plugin placeholder
                    discovered[py_file.stem] = {
                        'id': py_file.stem,
                        'name': py_file.stem.replace('_', ' ').title(),
                        'description': f'Cannot load: {str(e)[:50]}...',
                        'icon': '❌',
                        'version': '1.0',
                        'requires': [],
                        '_load_error': str(e),
                        '_file': py_file.stem,
                        '_broken': True
                    }

            except Exception as e:
                print(f"Warning: Could not load plugin {py_file.stem}: {e}")
                # Add as broken plugin
                discovered[py_file.stem] = {
                    'id': py_file.stem,
                    'name': py_file.stem.replace('_', ' ').title(),
                    'description': f'Error loading: {str(e)[:50]}...',
                    'icon': '❌',
                    'version': '1.0',
                    'requires': [],
                    '_load_error': str(e),
                    '_file': py_file.stem,
                    '_broken': True
                }

        return discovered

    def _create_ui(self):
        """Create the plugin manager interface"""
        # Header
        header_frame = tk.Frame(self, bg="#2196F3")
        header_frame.pack(fill=tk.X)

        tk.Label(header_frame,
                text="🔌 Plugin Manager - v10.1 FINAL",
                font=("Arial", 16, "bold"),
                bg="#2196F3", fg="white",
                pady=15).pack()

        # Info box
        info_frame = tk.Frame(self, bg="#E3F2FD", relief=tk.RIDGE, borderwidth=2)
        info_frame.pack(fill=tk.X, padx=20, pady=15)

        plugin_count = len(self.available_plugins)
        broken_plugins = sum(1 for p in self.available_plugins.values() if '_load_error' in p)
        working_plugins = plugin_count - broken_plugins

        if broken_plugins > 0:
            info_text = (
                f"Found {plugin_count} plugin(s) available ({broken_plugins} need dependencies).\n"
                "Click 'Install' to add missing dependencies. Enable plugins to use them.\n"
                "Enabled plugins appear in the 'Advanced' menu after restart."
            )
        else:
            info_text = (
                f"Found {plugin_count} plugin(s) available.\n"
                "Click 'Install' to add missing dependencies. Enable plugins to use them.\n"
                "Enabled plugins appear in the 'Advanced' menu after restart."
            )

        tk.Label(info_frame, text=info_text,
                fg="#1976D2", bg="#E3F2FD",
                font=("Arial", 9),
                justify=tk.LEFT, pady=10, padx=10).pack()

        if broken_plugins > 0:
            tk.Label(info_frame,
                    text=f"⚠️ {broken_plugins} plugin(s) need dependencies installed.",
                    fg="#F44336", bg="#E3F2FD",
                    font=("Arial", 9, "bold")).pack()

        if not self.available_plugins:
            tk.Label(info_frame,
                    text="⚠️ No plugins found! Place plugin files in plugins/ folder.",
                    fg="#F44336", bg="#E3F2FD",
                    font=("Arial", 9, "bold")).pack()

        # Plugin list with scrollbar
        list_container = tk.Frame(self)
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(list_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add plugins to scrollable frame
        for plugin_id, plugin_info in self.available_plugins.items():
            self._create_plugin_row(scrollable_frame, plugin_id, plugin_info)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="✓ Apply & Save",
                 command=self._apply_changes,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 10, "bold"),
                 width=15, height=2,
                 cursor="hand2").pack(side=tk.LEFT, padx=5)

        if self.available_plugins:
            tk.Button(btn_frame, text="Install All Missing",
                     command=self._install_all_missing,
                     bg="#FF9800", fg="white",
                     font=("Arial", 10),
                     width=18, height=2,
                     cursor="hand2").pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Refresh",
                 command=self._refresh_plugins,
                 bg="#2196F3", fg="white",
                 font=("Arial", 10),
                 width=15, height=2,
                 cursor="hand2").pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Cancel",
                 command=self.destroy,
                 font=("Arial", 10),
                 width=15, height=2,
                 cursor="hand2").pack(side=tk.LEFT, padx=5)

    def _refresh_plugins(self):
        """Refresh plugin list"""
        self.available_plugins = self._discover_plugins()

        # Clear existing widgets
        for widget in self.winfo_children():
            if widget not in [self.children['!frame'], self.children['!frame2']]:
                widget.destroy()

        # Recreate UI
        self._create_ui()

    def _create_plugin_row(self, parent, plugin_id, info):
        """Create a row for a single plugin"""
        # Check if plugin is broken (can't load)
        is_broken = '_load_error' in info
        is_google_earth = plugin_id in ['google_earth_export', 'google_earth']
        is_gis_viewer = plugin_id in ['gis_3d_viewer', '3d_gis_viewer', 'gis_viewer']

        # Special handling for known plugins to ensure proper dependencies
        if is_google_earth and 'requires' not in info:
            info['requires'] = ['simplekml', 'earthengine-api']
        elif is_gis_viewer and 'requires' not in info:
            info['requires'] = ['pyvista', 'folium', 'geopandas', 'matplotlib', 'numpy', 'shapely']

        # Main frame - different color for broken plugins
        frame_bg = "#FFEBEE" if is_broken else "white"

        frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=1, bg=frame_bg)
        frame.pack(fill=tk.X, pady=5, padx=5)

        # Left side: Checkbox + Icon + Info
        left_frame = tk.Frame(frame, bg=frame_bg)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10, padx=10)

        # Checkbox - disabled for broken plugins
        var = tk.BooleanVar(value=self.enabled_plugins.get(plugin_id, False))
        self.plugin_vars[plugin_id] = var

        # Enable checkbox only if plugin can be loaded or has no dependencies missing
        requires = info.get('requires', [])
        requirements_met, missing = self._check_requirements(requires)

        chk_state = tk.NORMAL if (not is_broken and requirements_met) else tk.DISABLED
        chk = tk.Checkbutton(left_frame, variable=var,
                            font=("Arial", 12),
                            bg=frame_bg,
                            activebackground=frame_bg,
                            cursor="hand2" if chk_state == tk.NORMAL else "arrow",
                            state=chk_state)
        chk.pack(side=tk.LEFT, padx=(0, 10))

        # Icon
        icon = info.get("icon", "❌") if is_broken else info.get("icon", "🔌")
        icon_label = tk.Label(left_frame, text=icon,
                             font=("Arial", 24),
                             bg=frame_bg)
        icon_label.pack(side=tk.LEFT, padx=(0, 15))

        # Name and description
        text_frame = tk.Frame(left_frame, bg=frame_bg)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        plugin_name = info.get("name", plugin_id.replace('_', ' ').title())
        if is_broken:
            plugin_name = f"⚠️ {plugin_name}"

        name_label = tk.Label(text_frame, text=plugin_name,
                             font=("Arial", 11, "bold"),
                             bg=frame_bg,
                             anchor=tk.W,
                             fg="#F44336" if is_broken else "black")
        name_label.pack(anchor=tk.W)

        # Description
        if is_broken:
            error_msg = info.get('_load_error', 'Unknown error')
            # Shorten long error messages
            if len(error_msg) > 80:
                error_msg = error_msg[:77] + "..."
            desc_text = f"Cannot load: {error_msg}"
            desc_fg = "#F44336"
        else:
            desc_text = info.get("description", "")
            desc_fg = "gray"

        desc_label = tk.Label(text_frame, text=desc_text,
                             fg=desc_fg, font=("Arial", 9),
                             bg=frame_bg,
                             wraplength=450,
                             anchor=tk.W,
                             justify=tk.LEFT)
        desc_label.pack(anchor=tk.W, pady=(2, 0))

        # Dependencies
        if is_broken:
            deps_text = "Fix dependencies to enable"
            deps_fg = "#F44336"
            deps_font = ("Arial", 8, "italic", "bold")
        elif requires:
            deps_text = f"Requires: {', '.join(requires)}"
            deps_fg = "#666"
            deps_font = ("Arial", 8, "italic")
        else:
            deps_text = "No extra dependencies"
            deps_fg = "green"
            deps_font = ("Arial", 8, "italic")

        deps_label = tk.Label(text_frame, text=deps_text,
                             fg=deps_fg, font=deps_font,
                             bg=frame_bg)
        deps_label.pack(anchor=tk.W, pady=(2, 0))

        # Right side: Status + Install button
        right_frame = tk.Frame(frame, bg=frame_bg)
        right_frame.pack(side=tk.RIGHT, padx=15, pady=10)

        # Check requirements
        requirements_met, missing = self._check_requirements(requires)

        # Status label
        if is_broken:
            status = tk.Label(right_frame, text="❌ Broken",
                            fg="#F44336", font=("Arial", 10, "bold"),
                            bg=frame_bg)
            status.pack()

            # Try to install button for broken plugins
            if requires:
                install_btn = tk.Button(right_frame, text="Fix",
                                       command=lambda pid=plugin_id, pkgs=requires:
                                           self._install_plugin_deps(pid, pkgs),
                                       bg="#F44336", fg="white",
                                       font=("Arial", 9, "bold"),
                                       cursor="hand2",
                                       width=8)
                install_btn.pack(pady=(5, 0))
            else:
                install_btn = tk.Button(right_frame, text="N/A",
                                       state=tk.DISABLED,
                                       bg="#E0E0E0",
                                       font=("Arial", 8))
                install_btn.pack(pady=(5, 0))

        elif requirements_met:
            status = tk.Label(right_frame, text="✓ Ready",
                            fg="green", font=("Arial", 10, "bold"),
                            bg=frame_bg)
            status.pack()

            install_btn = tk.Button(right_frame, text="Installed",
                                   state=tk.DISABLED,
                                   bg="#E0E0E0",
                                   font=("Arial", 8))
            install_btn.pack(pady=(5, 0))
        else:
            status = tk.Label(right_frame, text="⚠ Missing",
                            fg="orange", font=("Arial", 10, "bold"),
                            bg=frame_bg)
            status.pack()

            if missing:
                missing_label = tk.Label(right_frame,
                                       text=f"({', '.join(missing[:2])}{'...' if len(missing) > 2 else ''})",
                                       fg="gray", font=("Arial", 7),
                                       bg=frame_bg)
                missing_label.pack()

            # Install button
            install_btn = tk.Button(right_frame, text="Install",
                                   command=lambda pid=plugin_id, pkgs=requires:
                                       self._install_plugin_deps(pid, pkgs),
                                   bg="#FF9800", fg="white",
                                   font=("Arial", 9, "bold"),
                                   cursor="hand2",
                                   width=10)
            install_btn.pack(pady=(5, 0))

        self.status_labels[plugin_id] = status
        self.install_buttons[plugin_id] = install_btn

    def _check_requirements(self, packages):
        """Check if required packages are installed"""
        missing = []

        # Mapping of package names to import names
        import_mapping = {
            "scikit-learn": "sklearn",
            "python-docx": "docx",
            "earthengine-api": "ee",
            "google-api-python-client": "googleapiclient",
            "simplekml": "simplekml",
            "pyvista": "pyvista",
            "folium": "folium",
            "geopandas": "geopandas",
            "matplotlib": "matplotlib",
            "numpy": "numpy",
            "shapely": "shapely.geometry",
            "scipy": "scipy",
            "pandas": "pandas",
            "openpyxl": "openpyxl",
        }

        for pkg in packages:
            try:
                import_name = import_mapping.get(pkg, pkg)

                # Handle special cases
                if import_name == "shapely.geometry":
                    from shapely.geometry import Point
                elif import_name == "ee":
                    import ee
                else:
                    __import__(import_name)
            except ImportError:
                missing.append(pkg)
            except Exception:
                # Some other error, but likely not installed
                missing.append(pkg)

        return (len(missing) == 0, missing)

    def _install_plugin_deps(self, plugin_id, packages):
        """Install dependencies for a specific plugin"""
        if not packages:
            messagebox.showinfo("No Dependencies",
                              "This plugin has no dependencies to install",
                              parent=self)
            return

        # Get plugin name
        if plugin_id == "all":
            plugin_name = "All Missing Plugins"
        else:
            plugin_info = self.available_plugins.get(plugin_id, {})
            plugin_name = plugin_info.get("name", plugin_id.replace('_', ' ').title())

        # Create installation progress window
        progress_win = tk.Toplevel(self)
        progress_win.title(f"Installing {plugin_name}")
        progress_win.geometry("650x450")
        progress_win.transient(self)
        progress_win.grab_set()

        # Center it
        progress_win.update_idletasks()
        x = (progress_win.winfo_screenwidth() // 2) - (650 // 2)
        y = (progress_win.winfo_screenheight() // 2) - (450 // 2)
        progress_win.geometry(f'+{x}+{y}')

        tk.Label(progress_win,
                text=f"Installing Dependencies for {plugin_name}",
                font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(progress_win,
                text=f"Packages: {', '.join(packages)}",
                font=("Arial", 9), fg="gray").pack()

        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_win,
                                      variable=progress_var,
                                      maximum=100,
                                      mode='indeterminate',
                                      length=550)
        progress_bar.pack(pady=20, padx=20)
        progress_bar.start(10)

        # Output text area
        output_frame = tk.Frame(progress_win)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        output_text = scrolledtext.ScrolledText(output_frame,
                                               height=18,
                                               font=("Courier", 9),
                                               bg="#f5f5f5")
        output_text.pack(fill=tk.BOTH, expand=True)

        def run_installation():
            """Run pip3 install in background thread"""
            try:
                # Use pip instead of pip3 for broader compatibility
                cmd = ["pip3", "install"] + packages
                output_text.insert(tk.END, f"Running: {' '.join(cmd)}\n\n")
                output_text.see(tk.END)

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Stream output
                for line in process.stdout:
                    output_text.insert(tk.END, line)
                    output_text.see(tk.END)
                    progress_win.update()

                process.wait()

                progress_bar.stop()

                if process.returncode == 0:
                    output_text.insert(tk.END, "\n\n✅ Installation completed successfully!\n")
                    output_text.see(tk.END)

                    # Update status for all affected plugins
                    for pid, plugin_info in self.available_plugins.items():
                        plugin_packages = plugin_info.get('requires', [])
                        if any(pkg in packages for pkg in plugin_packages):
                            # Re-check requirements
                            requirements_met, missing = self._check_requirements(plugin_packages)

                            if requirements_met:
                                self.status_labels[pid].config(text="✓ Ready", fg="green")
                                self.install_buttons[pid].config(text="Installed",
                                                              state=tk.DISABLED,
                                                              bg="#E0E0E0")
                                # Enable checkbox
                                if pid in self.plugin_vars:
                                    # Find the checkbox widget and enable it
                                    pass

                    tk.Button(progress_win, text="Close & Refresh",
                             command=lambda: [progress_win.destroy(), self._refresh_plugins()],
                             bg="#4CAF50", fg="white",
                             font=("Arial", 10, "bold"),
                             width=15, height=2).pack(pady=10)
                else:
                    output_text.insert(tk.END,
                                     f"\n\n❌ Installation failed with code {process.returncode}\n")
                    output_text.see(tk.END)

                    tk.Button(progress_win, text="Close",
                             command=progress_win.destroy,
                             bg="#F44336", fg="white",
                             font=("Arial", 10, "bold"),
                             width=15, height=2).pack(pady=10)

            except FileNotFoundError:
                # pip command not found
                progress_bar.stop()
                output_text.insert(tk.END,
                    "\n\n❌ ERROR: pip command not found!\n\n"
                    "Please run these commands manually in your terminal:\n\n"
                    "Option 1 (recommended):\n"
                    f"  python -m pip3 install {' '.join(packages)}\n\n"
                    "Option 2:\n"
                    f"  python3 -m pip3 install {' '.join(packages)}\n\n"
                    "Option 3 (if above don't work):\n"
                    f"  pip3 install {' '.join(packages)}\n"
                )
                output_text.see(tk.END)

                tk.Button(progress_win, text="Close",
                         command=progress_win.destroy,
                         bg="#F44336", fg="white",
                         font=("Arial", 10, "bold"),
                         width=15, height=2).pack(pady=10)

            except Exception as e:
                progress_bar.stop()
                output_text.insert(tk.END,
                    f"\n\n❌ Error: {str(e)}\n\n"
                    "If installation fails, try running manually:\n"
                    f"  python -m pip3 install {' '.join(packages)}\n"
                )
                output_text.see(tk.END)

                tk.Button(progress_win, text="Close",
                         command=progress_win.destroy,
                         bg="#F44336", fg="white",
                         font=("Arial", 10, "bold"),
                         width=15, height=2).pack(pady=10)

        # Start installation in background thread
        install_thread = threading.Thread(target=run_installation, daemon=True)
        install_thread.start()

    def _install_all_missing(self):
        """Install all missing dependencies at once"""
        all_missing = set()
        for plugin_info in self.available_plugins.values():
            requires = plugin_info.get("requires", [])
            if requires:  # Only check if plugin has dependencies
                _, missing = self._check_requirements(requires)
                all_missing.update(missing)

        if not all_missing:
            messagebox.showinfo(
                "All Set!",
                "All plugin dependencies are already installed!\n\n"
                "You can enable any plugin you want.",
                parent=self
            )
            return

        # Group by plugin
        plugin_missing = {}
        for plugin_id, plugin_info in self.available_plugins.items():
            requires = plugin_info.get("requires", [])
            if requires:
                _, missing = self._check_requirements(requires)
                if missing:
                    plugin_name = plugin_info.get("name", plugin_id)
                    plugin_missing[plugin_name] = missing

        # Create message
        missing_text = ""
        for plugin_name, missing_list in plugin_missing.items():
            missing_text += f"\n• {plugin_name}: {', '.join(missing_list)}"

        result = messagebox.askyesno(
            "Install All Missing Dependencies",
            f"This will install {len(all_missing)} package(s):\n\n"
            f"{', '.join(sorted(all_missing))}\n\n"
            f"Affected plugins:{missing_text}\n\n"
            f"This may take a few minutes. Continue?",
            parent=self
        )

        if not result:
            return

        self._install_plugin_deps("all", list(sorted(all_missing)))

    def _load_enabled_plugins(self):
        """Load enabled plugins from config file"""
        config_file = Path("config/enabled_plugins.json")
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading plugin config: {e}")
                return {}
        return {}

    def _save_enabled_plugins(self):
        """Save enabled plugins to config file"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)

        # Only save plugins that can actually be loaded (have no missing deps)
        enabled = {}
        for pid, var in self.plugin_vars.items():
            if var.get():
                # Check if plugin can be loaded
                plugin_info = self.available_plugins.get(pid, {})
                requires = plugin_info.get('requires', [])
                requirements_met, _ = self._check_requirements(requires)

                if requirements_met or not requires:  # Enable if requirements met or no deps
                    enabled[pid] = True
                else:
                    # Don't save plugins with missing deps as enabled
                    messagebox.showwarning(
                        "Plugin Disabled",
                        f"Plugin '{plugin_info.get('name', pid)}' has missing dependencies.\n"
                        "It will remain disabled until dependencies are installed.",
                        parent=self
                    )

        try:
            with open(config_dir / "enabled_plugins.json", "w") as f:
                json.dump(enabled, f, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Save Error",
                               f"Failed to save plugin settings:\n{e}",
                               parent=self)
            return False

    def _apply_changes(self):
        """Apply changes and notify user"""
        if self._save_enabled_plugins():
            enabled_count = sum(1 for var in self.plugin_vars.values() if var.get())

            if enabled_count > 0:
                msg = (
                    f"✓ Plugin settings saved!\n\n"
                    f"{enabled_count} plugin(s) enabled.\n\n"
                    f"Please restart the application for the\n"
                    f"'Advanced' menu to appear with your\n"
                    f"selected features."
                )
            else:
                msg = (
                    "All plugins disabled.\n\n"
                    "The 'Advanced' menu will not appear\n"
                    "until you enable at least one plugin."
                )

            messagebox.showinfo("Plugins Updated", msg, parent=self)
            self.destroy()
