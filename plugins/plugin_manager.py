"""
Plugin Manager v10.2 - Three-Tab Architecture
Author: Sefy Levy
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import subprocess
import threading
import importlib.util
import ast
import sys
from pathlib import Path

class PluginManager(tk.Toplevel):
    def __init__(self, parent_app):
        super().__init__(parent_app.root)
        self.app = parent_app
        self.title("Plugin Manager v10.2")
        self.geometry("900x700")

        self.import_mapping = {
            "scikit-learn": "sklearn",
            "umap-learn": "umap",
            "python-docx": "docx",
            "simplekml": "simplekml",
            "pyvista": "pyvista",
            "geopandas": "geopandas",
            "pyserial": "serial",
            "pynmea2": "pynmea2",
            "watchdog": "watchdog",
            "pythonnet": "clr",
            "pywin32": "win32com.client",
            "pillow": "PIL",
            "earthengine-api": "ee",
            "pybaselines": "pybaselines",
            "lmfit": "lmfit"
        }

        self.transient(parent_app.root)
        self.available_plugins = self._discover_plugins()
        self.plugin_vars = {}
        self.enabled_plugins = self._load_enabled_plugins()

        self._create_ui()
        self._center_window()
        self.grab_set()

    def _discover_plugins(self):
        discovered = {}
        
        folders = [
            ("add-on", Path("plugins/add-ons")),
            ("software", Path("plugins/software")),
            ("hardware", Path("plugins/hardware"))
        ]
        
        for folder_type, plugin_dir in folders:
            if not plugin_dir.exists():
                continue

            for py_file in plugin_dir.glob("*.py"):
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue

                try:
                    spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'PLUGIN_INFO'):
                        info = module.PLUGIN_INFO
                        if 'category' not in info:
                            info['category'] = folder_type
                        discovered[info['id']] = info
                except Exception as e:
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Assign):
                                for target in node.targets:
                                    if isinstance(target, ast.Name) and target.id == 'PLUGIN_INFO':
                                        info = ast.literal_eval(node.value)
                                        if 'category' not in info:
                                            info['category'] = folder_type
                                        discovered[info['id']] = info
                    except:
                        pass

        return discovered

    def _check_requirements(self, packages):
        if not packages:
            return (True, [])
        
        missing = []
        for pkg in packages:
            import_name = self.import_mapping.get(pkg, pkg)
            try:
                if importlib.util.find_spec(import_name) is None:
                    missing.append(pkg)
            except:
                missing.append(pkg)
        return (len(missing) == 0, missing)

    def _install_plugin_deps(self, plugin_id, packages):
        win = tk.Toplevel(self)
        win.title("Installing")
        win.geometry("600x400")

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)

        def run():
            cmd = [sys.executable, "-m", "pip", "install"] + packages
            text.insert(tk.END, f"Running: {' '.join(cmd)}\n\n")
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                text.insert(tk.END, line)
                text.see(tk.END)
            p.wait()
            if p.returncode == 0:
                text.insert(tk.END, "\n✅ SUCCESS! Restart app.")
            else:
                text.insert(tk.END, f"\n❌ FAILED")

        threading.Thread(target=run, daemon=True).start()

    def _create_ui(self):
        header = tk.Frame(self, bg="#2196F3", pady=10)
        header.pack(fill=tk.X)
        tk.Label(header, text="🔌 Plugin Manager v10.2", 
                font=("Arial", 14, "bold"), bg="#2196F3", fg="white").pack()

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        addons = {k: v for k, v in self.available_plugins.items() if v.get('category') in ['add-on', 'add-ons']}
        software = {k: v for k, v in self.available_plugins.items() if v.get('category') == 'software'}
        hardware = {k: v for k, v in self.available_plugins.items() if v.get('category') == 'hardware'}

        self._create_tab(notebook, "🎨 UI Add-ons", addons)
        self._create_tab(notebook, "📦 Software", software)
        self._create_tab(notebook, "🔌 Hardware", hardware)

        footer = tk.Frame(self, bg="#E8F5E9", pady=15, relief=tk.RAISED, borderwidth=2)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Button(footer, text="✓ Apply Changes", bg="#4CAF50", fg="white", 
                 font=("Arial", 12, "bold"), width=25, height=2,
                 command=self._apply).pack(pady=5)

    def _create_tab(self, notebook, name, plugins):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=name)
        
        container = tk.Frame(frame)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        if plugins:
            for pid, info in sorted(plugins.items(), key=lambda x: x[1].get('name', '')):
                self._create_row(scroll_frame, pid, info)
        else:
            tk.Label(scroll_frame, text="No plugins", fg="gray").pack(pady=20)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_row(self, parent, pid, info):
        row = tk.Frame(parent, relief=tk.GROOVE, borderwidth=1, pady=8, padx=8)
        row.pack(fill=tk.X, pady=3, padx=5)

        requires = info.get('requires', [])
        met, missing = self._check_requirements(requires)
        
        var = tk.BooleanVar(value=self.enabled_plugins.get(pid, False))
        self.plugin_vars[pid] = var
        
        tk.Checkbutton(row, variable=var, state=tk.NORMAL if met else tk.DISABLED).pack(side=tk.LEFT)

        details = tk.Frame(row)
        details.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        tk.Label(details, text=f"{info.get('icon', '📦')} {info.get('name', pid)}", 
                font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        tk.Label(details, text=info.get('description', ''), fg="#666", 
                font=("Arial", 9)).pack(anchor=tk.W)
        
        if requires:
            if met:
                tk.Label(details, text=f"✓ {', '.join(requires)}", fg="green", 
                        font=("Arial", 8)).pack(anchor=tk.W)
            else:
                tk.Label(details, text=f"⚠ Missing: {', '.join(missing)}", fg="#FF5722", 
                        font=("Arial", 8)).pack(anchor=tk.W)

        action = tk.Frame(row)
        action.pack(side=tk.RIGHT, padx=5)
        
        if not met and requires:
            tk.Button(action, text="Install", bg="#FF9800", fg="white",
                     font=("Arial", 9, "bold"), width=12,
                     command=lambda: self._install_plugin_deps(pid, requires)).pack()
        else:
            tk.Label(action, text="✓ Ready", fg="green", font=("Arial", 10, "bold")).pack()

    def _apply(self):
        enabled = {k: v.get() for k, v in self.plugin_vars.items() if v.get()}
        
        Path("config").mkdir(exist_ok=True)
        with open("config/enabled_plugins.json", "w") as f:
            json.dump(enabled, f, indent=2)

        messagebox.showinfo("Success", f"✅ Saved {len(enabled)} plugins\n\nRestart app to apply.")
        self.destroy()

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _load_enabled_plugins(self):
        path = Path("config/enabled_plugins.json")
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except:
                return {}
        return {}
