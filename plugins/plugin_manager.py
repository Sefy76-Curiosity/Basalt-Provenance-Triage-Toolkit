"""
Plugin Manager v10.2 - Compact Covenant
Author: Sefy Levy

3 TABS · 3 CATEGORIES · SMART TOGGLE · REAL REMOVAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ CHECK → Enable + Add to menu
✗ UNCHECK → Disable + REMOVE FROM MENU instantly
⚡ Smart button: ENABLE N / DISABLE N
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_MANAGER_INFO = {
    "id": "plugin_manager_v10_2",
    "name": "🔌 Plugin Manager",
    "version": "10.2",
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import threading
import importlib.util
import ast
import sys
from pathlib import Path

class PluginManager(tk.Toplevel):
    # Import name → pip package name
    IMPORT_MAPPING = {
        # Scientific stack - CORRECT import names
        "numpy": "numpy",
        "pandas": "pandas",
        "matplotlib": "matplotlib",
        "scipy": "scipy",
        "scikit-learn": "sklearn",
        "scikit-image": "skimage",
        "opencv-python": "cv2",
        "opencv-contrib-python": "cv2",

        # Serial
        "pyserial": "serial",

        # Imaging
        "pillow": "PIL",

        # Built-in - map to itself
        "ctypes": "ctypes",  # ← ADD THIS LINE

        # Everything else
        "umap-learn": "umap",
        "python-docx": "docx",
        "simplekml": "simplekml",
        "pyvista": "pyvista",
        "geopandas": "geopandas",
        "pynmea2": "pynmea2",
        "watchdog": "watchdog",
        "pythonnet": "clr",
        "earthengine-api": "ee",
        "pybaselines": "pybaselines",
        "lmfit": "lmfit",
    }

    def __init__(self, parent_app):
        super().__init__(parent_app.root)
        self.app = parent_app

        # ─── COMPACT: 620x500, NO WASTE ──────────────────
        self.title("🔌 Plugin Manager v10.2")
        self.geometry("620x500")
        self.minsize(580, 450)
        self.transient(parent_app.root)

        # Plugin registry
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.enabled_file = self.config_dir / "enabled_plugins.json"

        # Discover and load state
        self.plugins_by_category = self._discover_all()
        self.enabled_plugins = self._load_enabled()
        self.plugin_vars = {}
        self.plugin_rows = {}

        self._build_ui()
        self._update_button_state()
        self._center_window()
        self.grab_set()

    # ────────────────────────────────────────────────────────────
    # DISCOVERY · READ ONLY · NO MENU CREATION
    # ────────────────────────────────────────────────────────────
    def _discover_all(self):
        """Scan folders, extract PLUGIN_INFO, sort by category."""
        categories = {
            "add-on": [],
            "software": [],
            "hardware": []
        }

        folder_map = {
            "add-on": Path("plugins/add-ons"),
            "software": Path("plugins/software"),
            "hardware": Path("plugins/hardware")
        }

        for category, folder in folder_map.items():
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
                continue

            for py_file in folder.glob("*.py"):
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue

                info = self._extract_info(py_file, category)
                if info:
                    categories[category].append(info)

        # Sort each category by name
        for cat in categories:
            categories[cat].sort(key=lambda x: x.get('name', x['id']))

        return categories

    def _extract_info(self, py_file, default_category):
        """Extract PLUGIN_INFO via import (preferred) or AST fallback."""
        # Method 1: Import
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'PLUGIN_INFO'):
                info = module.PLUGIN_INFO.copy()
                info['category'] = default_category
                info['path'] = str(py_file)
                info['module'] = py_file.stem
                return info
        except:
            pass

        # Method 2: AST fallback
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'PLUGIN_INFO':
                            info = ast.literal_eval(node.value)
                            info['category'] = default_category
                            info['path'] = str(py_file)
                            info['module'] = py_file.stem
                            return info
        except:
            pass

        return None

    # ────────────────────────────────────────────────────────────
    # STATE MANAGEMENT · SINGLE SOURCE OF TRUTH
    # ────────────────────────────────────────────────────────────
    def _load_enabled(self):
        """Load enabled_plugins.json."""
        if self.enabled_file.exists():
            try:
                with open(self.enabled_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_enabled(self):
        """Save enabled_plugins.json."""
        enabled = {pid: var.get() for pid, var in self.plugin_vars.items()}
        with open(self.enabled_file, 'w') as f:
            json.dump(enabled, f, indent=2)
        return enabled

    # ────────────────────────────────────────────────────────────
    # DEPENDENCY CHECK · FIXED: ACTUAL IMPORT TEST
    # ────────────────────────────────────────────────────────────
    def _check_deps(self, requires):
        """Return (met: bool, missing: list)"""
        if not requires:
            return True, []

        missing = []
        for pkg in requires:
            # ─── SKIP ctypes - it's built-in, always available ───
            if pkg == 'ctypes':
                continue

            import_name = self.IMPORT_MAPPING.get(pkg, pkg)
            try:
                if importlib.util.find_spec(import_name) is None:
                    missing.append(pkg)
            except:
                missing.append(pkg)
        return len(missing) == 0, missing

    def _install_deps(self, plugin_name, packages):
        """Spawn pip install in a non-blocking window."""
        win = tk.Toplevel(self)
        win.title(f"📦 Installing: {plugin_name}")
        win.geometry("600x400")
        win.transient(self)

        header = tk.Frame(win, bg="#2196F3", height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"pip install {' '.join(packages)}",
                font=("Consolas", 9), bg="#2196F3", fg="white").pack(pady=6)

        text = tk.Text(win, wrap=tk.WORD, font=("Consolas", 9),
                      bg="#1e1e1e", fg="#d4d4d4")
        scroll = tk.Scrollbar(win, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        def run():
            text.insert(tk.END, f"$ pip install {' '.join(packages)}\n\n")
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install"] + packages,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in proc.stdout:
                text.insert(tk.END, line)
                text.see(tk.END)
                win.update()
            proc.wait()

            if proc.returncode == 0:
                text.insert(tk.END, "\n✅ SUCCESS! Dependencies installed.\n")
                text.insert(tk.END, "🔁 Restart recommended.\n")
            else:
                text.insert(tk.END, f"\n❌ FAILED (code {proc.returncode})\n")

        threading.Thread(target=run, daemon=True).start()

    # ────────────────────────────────────────────────────────────
    # UI · 3 BIG TABS · FULL WIDTH · SMART BUTTON
    # ────────────────────────────────────────────────────────────
    def _build_ui(self):
        """620x500, 3 big text tabs, full-width list, smart button."""

        # ─── HEADER ──────────────────────────────────
        header = tk.Frame(self, bg="#2c3e50", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🔌", font=("Arial", 16),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="PLUGIN MANAGER v10.2", font=("Arial", 12, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)

        # ─── 3 BIG CATEGORY TABS - FULL ROW ──────────
        tab_frame = tk.Frame(self, bg="#34495e", height=45)
        tab_frame.pack(fill=tk.X)
        tab_frame.pack_propagate(False)

        # Configure grid - 3 equal columns
        tab_frame.columnconfigure(0, weight=1)
        tab_frame.columnconfigure(1, weight=1)
        tab_frame.columnconfigure(2, weight=1)

        self.category_var = tk.StringVar(value="add-on")

        self.btn_addons = tk.Button(tab_frame, text="🎨 ADD-ONS",
                                   font=("Arial", 11, "bold"),
                                   bg="#2c3e50", fg="white",
                                   relief=tk.FLAT,
                                   command=lambda: self._switch_category("add-on"))
        self.btn_addons.grid(row=0, column=0, sticky="nsew", padx=1, pady=2)

        self.btn_software = tk.Button(tab_frame, text="📦 SOFTWARE",
                                     font=("Arial", 11, "bold"),
                                     bg="#34495e", fg="#bdc3c7",
                                     relief=tk.FLAT,
                                     command=lambda: self._switch_category("software"))
        self.btn_software.grid(row=0, column=1, sticky="nsew", padx=1, pady=2)

        self.btn_hardware = tk.Button(tab_frame, text="🔌 HARDWARE",
                                     font=("Arial", 11, "bold"),
                                     bg="#34495e", fg="#bdc3c7",
                                     relief=tk.FLAT,
                                     command=lambda: self._switch_category("hardware"))
        self.btn_hardware.grid(row=0, column=2, sticky="nsew", padx=1, pady=2)

        # ─── CONTENT AREA - FILLS ALL REMAINING SPACE ──────────
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create category frames
        self.frames = {
            "add-on": tk.Frame(self.content_frame, bg="white"),
            "software": tk.Frame(self.content_frame, bg="white"),
            "hardware": tk.Frame(self.content_frame, bg="white")
        }

        # Populate each frame
        for category, frame in self.frames.items():
            self._populate_category(frame, self.plugins_by_category[category])

        # Show default category (add-ons)
        self._switch_category("add-on")

        # ─── SMART BUTTON ────────────────────────────
        footer = tk.Frame(self, bg="#ecf0f1", height=55)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        # Left side - status
        self.status_var = tk.StringVar(value="⚡ Ready")
        status = tk.Label(footer, textvariable=self.status_var,
                         font=("Arial", 9), bg="#ecf0f1", fg="#7f8c8d")
        status.pack(side=tk.LEFT, padx=15)

        # Right side - smart button
        self.action_btn = tk.Button(footer, text="✅ APPLY CHANGES",
                                   font=("Arial", 11, "bold"),
                                   bg="#27ae60", fg="white",
                                   padx=25, pady=8,
                                   command=self._apply)
        self.action_btn.pack(side=tk.RIGHT, padx=15, pady=8)

    def _switch_category(self, category):
        """Switch between ADD-ONS, SOFTWARE, HARDWARE - FIXED: FULL WIDTH & HEIGHT."""
        self.category_var.set(category)

        # Update button colors
        self.btn_addons.config(bg="#2c3e50" if category == "add-on" else "#34495e",
                              fg="white" if category == "add-on" else "#bdc3c7")
        self.btn_software.config(bg="#2c3e50" if category == "software" else "#34495e",
                                fg="white" if category == "software" else "#bdc3c7")
        self.btn_hardware.config(bg="#2c3e50" if category == "hardware" else "#34495e",
                                fg="white" if category == "hardware" else "#bdc3c7")

        # Show selected frame, hide others - FIXED: fill=BOTH, expand=True
        for cat, frame in self.frames.items():
            if cat == category:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()

    def _populate_category(self, parent, plugins):
        """Fill a category with plugin rows - FIXED: FULL WIDTH + MOUSE WHEEL."""
        if not plugins:
            empty = tk.Frame(parent, bg="white")
            empty.pack(fill=tk.BOTH, expand=True)
            tk.Label(empty, text="✨ No plugins found",
                    font=("Arial", 11), bg="white", fg="#95a5a6").pack(expand=True)
            return

        # Canvas + Scrollbar - FIXED: FULL WIDTH
        canvas = tk.Canvas(parent, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")

        # Configure scroll frame
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))

        # Create window that fills canvas width
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=canvas.winfo_width())

        # FIXED: Resize window when canvas resizes
        def _on_canvas_configure(event):
            canvas.itemconfig(1, width=event.width)  # item 1 is the window

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        # ============ MOUSE WHEEL SUPPORT ============
        def _on_mousewheel(event):
            """Handle mouse wheel scrolling - works on all platforms"""
            if event.delta:  # Windows/macOS
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:  # Linux
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")

        def _on_enter(event):
            """Bind mouse wheel when mouse enters canvas"""
            canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/macOS
            canvas.bind_all("<Button-4>", _on_mousewheel)   # Linux up
            canvas.bind_all("<Button-5>", _on_mousewheel)   # Linux down

        def _on_leave(event):
            """Unbind mouse wheel when mouse leaves canvas"""
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        # Bind mouse enter/leave events
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        # ===============================================

        # FIXED: Pack with expand=True to fill remaining space
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add each plugin row
        for info in plugins:
            self._create_plugin_row(scroll_frame, info)

    def _create_plugin_row(self, parent, info):
        """Single plugin row - clean, compact, with checkbox."""
        pid = info['id']
        name = info.get('name', pid)
        icon = info.get('icon', '📦')
        version = info.get('version', '')
        author = info.get('author', 'Unknown')
        description = info.get('description', '')
        requires = info.get('requires', [])

        # Row container - FULL WIDTH
        row = tk.Frame(parent, bg="white", relief=tk.GROOVE, borderwidth=1)
        row.pack(fill=tk.X, padx=3, pady=2)
        self.plugin_rows[pid] = row

        # Checkbox + Icon + Name (left side)
        left = tk.Frame(row, bg="white")
        left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=6)

        var = tk.BooleanVar(value=self.enabled_plugins.get(pid, False))
        var.trace('w', lambda *args: self._update_button_state())
        self.plugin_vars[pid] = var

        cb = tk.Checkbutton(left, text=f"{icon} {name}", variable=var,
                           font=("Arial", 10, "bold"),
                           bg="white", anchor="w")
        cb.pack(anchor=tk.W)

        # Description line
        if description:
            desc = tk.Label(left, text=f"  {description}",
                           font=("Arial", 8), fg="#5e6c84",
                           bg="white", anchor="w")
            desc.pack(anchor=tk.W)

        # Author + version
        meta = tk.Label(left, text=f"  by {author} · v{version}",
                       font=("Arial", 7), fg="#7f8c8d",
                       bg="white", anchor="w")
        meta.pack(anchor=tk.W)

        # Dependencies (right side)
        if requires:
            deps_frame = tk.Frame(row, bg="white")
            deps_frame.pack(side=tk.RIGHT, padx=10)

            met, missing = self._check_deps(requires)

            if met:
                tk.Label(deps_frame, text="✓✓", font=("Arial", 9),
                        fg="#27ae60", bg="white").pack(side=tk.LEFT, padx=2)
                deps_text = ", ".join(requires[:2])
                if len(requires) > 2:
                    deps_text += f" +{len(requires)-2}"
                tk.Label(deps_frame, text=deps_text,
                        font=("Arial", 7), fg="#27ae60",
                        bg="white").pack(side=tk.LEFT)
            else:
                tk.Label(deps_frame, text="⚠️", font=("Arial", 9),
                        fg="#e67e22", bg="white").pack(side=tk.LEFT, padx=2)
                tk.Label(deps_frame, text=f"missing: {missing[0]}",
                        font=("Arial", 7), fg="#e67e22",
                        bg="white").pack(side=tk.LEFT)

                btn = tk.Button(deps_frame, text="INSTALL",
                               font=("Arial", 7, "bold"),
                               bg="#f39c12", fg="white",
                               padx=6, pady=0,
                               command=lambda: self._install_deps(name, missing))
                btn.pack(side=tk.LEFT, padx=5)

    # ────────────────────────────────────────────────────────────
    # SMART BUTTON · REAL MENU REMOVAL · INSTANT FEEDBACK
    # ────────────────────────────────────────────────────────────
    def _update_button_state(self):
        """Update smart button text based on selections."""
        to_enable = 0
        to_disable = 0

        for pid, var in self.plugin_vars.items():
            was_enabled = self.enabled_plugins.get(pid, False)
            is_enabled = var.get()

            if is_enabled and not was_enabled:
                to_enable += 1
            elif not is_enabled and was_enabled:
                to_disable += 1

        if to_enable > 0 and to_disable > 0:
            self.action_btn.config(text=f"⚡ APPLY ({to_enable} ENABLE / {to_disable} DISABLE)",
                                  bg="#e67e22")
        elif to_enable > 0:
            self.action_btn.config(text=f"✅ ENABLE {to_enable}", bg="#27ae60")
        elif to_disable > 0:
            self.action_btn.config(text=f"🔥 DISABLE {to_disable}", bg="#e74c3c")
        else:
            self.action_btn.config(text="✅ APPLY CHANGES", bg="#27ae60")

    def _remove_from_menu(self, plugin_id: str, info: dict):
        """REAL REMOVAL - Delete plugin from menu system."""
        category = info.get('category', '')
        name = info.get('name', plugin_id)

        print(f"🗑️ Removing: {name}")

        # Software → Advanced menu
        if category == 'software' and hasattr(self.app, 'advanced_menu'):
            try:
                last = self.app.advanced_menu.index('end')
                for i in range(last + 1):
                    try:
                        label = self.app.advanced_menu.entrycget(i, 'label')
                        if name in label or plugin_id in label:
                            self.app.advanced_menu.delete(i)
                            print(f"  ✓ Removed from Advanced menu")
                            break
                    except:
                        continue
            except:
                pass

        # Hardware → XRF/Chemistry/Mineralogy menus
        elif category == 'hardware':
            # XRF menu
            if hasattr(self.app, 'xrf_menu'):
                try:
                    last = self.app.xrf_menu.index('end')
                    for i in range(last + 1):
                        try:
                            label = self.app.xrf_menu.entrycget(i, 'label')
                            if name in label or plugin_id in label:
                                self.app.xrf_menu.delete(i)
                                print(f"  ✓ Removed from XRF menu")
                                break
                        except:
                            continue
                except:
                    pass

            # Chemistry menu
            if hasattr(self.app, 'chemistry_menu'):
                try:
                    last = self.app.chemistry_menu.index('end')
                    for i in range(last + 1):
                        try:
                            label = self.app.chemistry_menu.entrycget(i, 'label')
                            if name in label or plugin_id in label:
                                self.app.chemistry_menu.delete(i)
                                print(f"  ✓ Removed from Chemistry menu")
                                break
                        except:
                            continue
                except:
                    pass

            # Mineralogy menu
            if hasattr(self.app, 'mineralogy_menu'):
                try:
                    last = self.app.mineralogy_menu.index('end')
                    for i in range(last + 1):
                        try:
                            label = self.app.mineralogy_menu.entrycget(i, 'label')
                            if name in label or plugin_id in label:
                                self.app.mineralogy_menu.delete(i)
                                print(f"  ✓ Removed from Mineralogy menu")
                                break
                        except:
                            continue
                except:
                    pass

    def _apply(self):
        """APPLY CHANGES - Enable/disable plugins, update menus in REAL TIME."""
        changes = 0

        for pid, var in self.plugin_vars.items():
            was_enabled = self.enabled_plugins.get(pid, False)
            is_enabled = var.get()

            if is_enabled != was_enabled:
                changes += 1
                self.enabled_plugins[pid] = is_enabled

                # Find plugin info
                info = None
                for cat in self.plugins_by_category.values():
                    for p in cat:
                        if p['id'] == pid:
                            info = p
                            break
                    if info:
                        break

                if info:
                    if is_enabled:
                        print(f"✅ Enabling: {info.get('name', pid)}")
                    else:
                        # REAL TIME REMOVAL - Delete from menu NOW
                        self._remove_from_menu(pid, info)

        # Save state
        self._save_enabled()

        # Reload plugins in main app (loads newly enabled ones)
        if hasattr(self.app, '_load_plugins'):
            self.app._load_plugins()

        # Show success message
        if changes > 0:
            self.status_var.set(f"✅ Applied {changes} changes")
            self.action_btn.config(text="✅ DONE", bg="#27ae60")
            self.after(1500, self.destroy)
        else:
            self.status_var.set("⚡ No changes")
            self.after(500, self.destroy)

    def _center_window(self):
        """Center on screen."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


# ────────────────────────────────────────────────────────────
# PLUGIN MANAGER REGISTRATION
# ────────────────────────────────────────────────────────────
def setup_plugin(main_app):
    """Register the plugin manager."""
    return PluginManager(main_app)
