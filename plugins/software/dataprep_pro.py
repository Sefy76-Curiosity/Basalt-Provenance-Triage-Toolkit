"""
DataPrep Pro v1.3 - Full rewrite for correct Scientific Toolkit integration

Changes from v1.2:
- FIXED: LabelFrame bootstyle= crash (removed entirely)
- FIXED: _apply_updates destructively popped Sample_ID before loop completed
- FIXED: New columns (CLR, normalization) were never reaching DataHub — now uses
         app.import_data_from_plugin() matching quartz_gis_pro pattern exactly
- FIXED: Changed columns now write back via data_hub.update_row() + notify_observers()
- FIXED: app.samples was stale — now always re-read via data_hub.get_all()
- FIXED: status_var created before tk.Tk() window exists (moved into open_window)
- ADDED: Full undo/redo stack with Ctrl+Z / Ctrl+Y
- ADDED: "Apply & Keep Open" button for iterative cleaning
- ADDED: DataHub observer sync on refresh
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "Geology & Geochemistry",
    "id": "dataprep_pro",
    "name": "DataPrep Pro",
    "icon": "🧹",
    "description": "Outlier detection, missing imputation, CLR/ILR transforms, robust normalization",
    "version": "1.3.1",
    "requires": ["numpy", "pandas", "scipy", "scikit-learn"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import KNNImputer
import traceback
from datetime import datetime

try:
    from skbio.stats.composition import clr, ilr
    HAS_SKBIO = True
except ImportError:
    HAS_SKBIO = False

try:
    import pymannkendall as mk
    HAS_MK = True
except ImportError:
    HAS_MK = False


class DataPrepPro:
    """
    Data Preparation Plugin for Scientific Toolkit.

    Reads from app.data_hub on open, exports via app.import_data_from_plugin()
    and app.data_hub.update_row() for in-place edits.
    """

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.df = None
        self.original_df = None
        self.preview_df = None
        self.numeric_columns = []
        self.all_columns = []
        self.outlier_mask = None
        self._undo_stack = []   # list of (df_copy, description)
        self._redo_stack = []
        self.status_var = None  # created in open_window once Tk root exists

    # ------------------------------------------------------------------
    # Import from DataHub
    # ------------------------------------------------------------------

    def _read_from_app(self):
        try:
            samples = self.app.data_hub.get_all()
            if not samples:
                return False
            self.df = pd.DataFrame(samples)
            self.original_df = self.df.copy()
            self.all_columns = list(self.df.columns)
            exclude = {'Sample_ID', 'Notes', 'Date', 'ID', 'Name', 'Code', 'Flag'}
            self.numeric_columns = []
            for col in self.all_columns:
                if any(ex in col for ex in exclude):
                    continue
                try:
                    pd.to_numeric(self.df[col], errors='raise')
                    self.numeric_columns.append(col)
                except (ValueError, TypeError):
                    pass
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Export back to DataHub — the correct pattern
    # ------------------------------------------------------------------

    def _write_to_app(self):
        """
        Push preview_df back into DataHub.
        Returns (rows_written, new_cols_count).

        New columns  → app.import_data_from_plugin()  (same as quartz_gis_pro)
        Changed vals → data_hub.update_row() per row  + notify_observers()
        """
        if self.preview_df is None:
            return 0, 0

        new_cols = [c for c in self.preview_df.columns
                    if c not in self.df.columns and c != '_outlier_flag']
        changed_cols = [c for c in self.df.columns
                        if c in self.preview_df.columns
                        and not self.preview_df[c].equals(self.df[c])]

        rows_written = 0

        # 1. Changed values in existing columns
        if changed_cols:
            all_samples = self.app.data_hub.get_all()
            for pos in range(len(self.preview_df)):
                if pos >= len(self.preview_df):
                    continue
                row = self.preview_df.iloc[pos]
                update = {}
                for col in changed_cols:
                    new_val = row.get(col)
                    if pos < len(self.df):
                        old_val = self.df.iloc[pos].get(col)
                    else:
                        old_val = None
                    if pd.notna(new_val) and str(new_val) != str(old_val):
                        update[col] = new_val
                if update:
                    sid = row.get('Sample_ID')
                    hub_idx = self._find_hub_index(sid, pos)
                    if hub_idx is not None:
                        self.app.data_hub.update_row(hub_idx, update)
                        rows_written += 1
            self.app.data_hub.notify_observers()

        # 2. New columns via import_data_from_plugin (only path that adds column names)
        if new_cols and hasattr(self.app, 'import_data_from_plugin'):
            records = []
            for pos in range(len(self.preview_df)):
                row = self.preview_df.iloc[pos]
                sid = row.get('Sample_ID', f"SAMPLE_{pos}")
                record = {'Sample_ID': sid}
                for col in new_cols:
                    val = row.get(col)
                    if pd.notna(val):
                        record[col] = val
                records.append(record)
            if records:
                self.app.import_data_from_plugin(records)
                rows_written = max(rows_written, len(records))

        # Sync app.samples cache
        self.app.samples = self.app.data_hub.get_all()
        return rows_written, len(new_cols)

    def _find_hub_index(self, sample_id, fallback):
        if sample_id:
            for i, s in enumerate(self.app.data_hub.get_all()):
                if s.get('Sample_ID') == sample_id:
                    return i
        total = len(self.app.data_hub.get_all())
        return fallback if fallback < total else None

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def _push_undo(self, desc="operation"):
        if self.preview_df is not None:
            self._undo_stack.append((self.preview_df.copy(), desc))
        self._redo_stack.clear()
        self._sync_undo_buttons()

    def _undo(self):
        if not self._undo_stack:
            return
        if self.preview_df is not None:
            self._redo_stack.append((self.preview_df.copy(), "redo"))
        self.preview_df, desc = self._undo_stack.pop()
        self.status_var.set(f"↩ Undid: {desc}")
        self._update_preview()
        self._sync_undo_buttons()

    def _redo(self):
        if not self._redo_stack:
            return
        if self.preview_df is not None:
            self._undo_stack.append((self.preview_df.copy(), "undo"))
        self.preview_df, desc = self._redo_stack.pop()
        self.status_var.set(f"↪ Redid: {desc}")
        self._update_preview()
        self._sync_undo_buttons()

    def _sync_undo_buttons(self):
        if hasattr(self, 'undo_btn'):
            self.undo_btn.configure(state=tk.NORMAL if self._undo_stack else tk.DISABLED)
        if hasattr(self, 'redo_btn'):
            self.redo_btn.configure(state=tk.NORMAL if self._redo_stack else tk.DISABLED)

    # ------------------------------------------------------------------
    # Window
    # ------------------------------------------------------------------

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._refresh_ui_data()
            return

        self.window = ttk.Toplevel(self.app.root)
        self.window.title("🧹 DataPrep Pro — Data Preparation")
        self.window.geometry("860x700")
        self.window.minsize(720, 580)
        self.window.transient(self.app.root)

        self.status_var = tk.StringVar(value="Ready")

        self._read_from_app()
        self._create_interface()
        self._center_window()
        self.window.focus_force()

        self.window.bind('<Control-z>', lambda e: self._undo())
        self.window.bind('<Control-y>', lambda e: self._redo())

    def _center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - self.window.winfo_width()) // 2
        y = (self.window.winfo_screenheight() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # UI — main layout
    # ------------------------------------------------------------------

    def _create_interface(self):
        # Header
        header = ttk.Frame(self.window, bootstyle="dark")
        header.pack(fill=X, pady=(0, 3))
        ttk.Label(header, text="🧹", font=("TkDefaultFont", 15),
                  bootstyle="inverse-dark").pack(side=LEFT, padx=8)
        ttk.Label(header, text="DataPrep Pro v1.3",
                  font=("TkDefaultFont", 11, "bold"),
                  bootstyle="inverse-dark").pack(side=LEFT)
        if self.df is not None:
            ttk.Label(header,
                      text=f"  {len(self.df)} samples | {len(self.numeric_columns)} numeric cols",
                      bootstyle="inverse-secondary").pack(side=LEFT, padx=12)
        ttk.Button(header, text="🔄 Refresh", command=self._refresh_ui_data,
                   bootstyle="info").pack(side=RIGHT, padx=8)

        # Notebook
        self.notebook = ttk.Notebook(self.window, bootstyle="dark")
        self.notebook.pack(fill=X, padx=4, pady=4)  # NOT expand — fixed height via tab content
        self._create_outlier_tab()
        self._create_missing_tab()
        self._create_transform_tab()
        self._create_normalization_tab()

        # Preview (label + frame manually — avoids LabelFrame bootstyle crash)
        preview_outer = ttk.Frame(self.window)
        preview_outer.pack(fill=BOTH, expand=True, padx=4, pady=(0, 2))
        ttk.Label(preview_outer, text="📋 Preview  (BEFORE → AFTER)",
                  font=("TkDefaultFont", 9, "bold"),
                  bootstyle="secondary").pack(anchor=W)
        preview_frame = ttk.Frame(preview_outer, bootstyle="dark")
        preview_frame.pack(fill=BOTH, expand=True)

        sel_row = ttk.Frame(preview_frame)
        sel_row.pack(fill=X, pady=2)
        ttk.Label(sel_row, text="Show:", bootstyle="light").pack(side=LEFT, padx=4)
        self.preview_cols_var = tk.StringVar(value="all")
        for txt, val in [("All", "all"), ("Numeric", "numeric"), ("Changed", "changed")]:
            ttk.Radiobutton(sel_row, text=txt, variable=self.preview_cols_var,
                            value=val, bootstyle="primary-toolbutton").pack(side=LEFT, padx=2)
        self.preview_cols_var.trace('w', lambda *_: self._update_preview())

        panels = ttk.Frame(preview_frame)
        panels.pack(fill=BOTH, expand=True)
        for side, label, attr, color in [
            (LEFT,  "BEFORE", "before_tree", "danger"),
            (RIGHT, "AFTER",  "after_tree",  "success"),
        ]:
            pf = ttk.Frame(panels)
            pf.pack(side=side, fill=BOTH, expand=True, padx=2)
            ttk.Label(pf, text=label, font=("TkDefaultFont", 8, "bold"),
                      bootstyle=color).pack(anchor=W)
            # grid so both scrollbars work without fighting pack
            tree_container = ttk.Frame(pf)
            tree_container.pack(fill=BOTH, expand=True)
            tree = ttk.Treeview(tree_container, bootstyle="dark", height=6)
            vsb = ttk.Scrollbar(tree_container, orient=VERTICAL, command=tree.yview,
                                bootstyle="dark-round")
            hsb = ttk.Scrollbar(tree_container, orient=HORIZONTAL, command=tree.xview,
                                bootstyle="dark-round")
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            tree_container.grid_rowconfigure(0, weight=1)
            tree_container.grid_columnconfigure(0, weight=1)
            setattr(self, attr, tree)

        # Footer
        footer = ttk.Frame(self.window, bootstyle="dark")
        footer.pack(fill=X, side=BOTTOM, pady=(2, 0))
        self.status_label = ttk.Label(footer, textvariable=self.status_var, bootstyle="light")
        self.status_label.pack(side=LEFT, padx=8, pady=4)

        self.undo_btn = ttk.Button(footer, text="↩ Undo", command=self._undo,
                                   bootstyle="secondary", width=7, state=tk.DISABLED)
        self.undo_btn.pack(side=LEFT, padx=2)
        self.redo_btn = ttk.Button(footer, text="↪ Redo", command=self._redo,
                                   bootstyle="secondary", width=7, state=tk.DISABLED)
        self.redo_btn.pack(side=LEFT, padx=2)

        ttk.Label(footer, text="  Apply to:", bootstyle="light").pack(side=LEFT, padx=4)
        self.apply_target = tk.StringVar(value="all")
        ttk.Radiobutton(footer, text="All", variable=self.apply_target,
                        value="all", bootstyle="primary-toolbutton").pack(side=LEFT, padx=2)
        ttk.Radiobutton(footer, text="Selected", variable=self.apply_target,
                        value="selected", bootstyle="primary-toolbutton").pack(side=LEFT, padx=2)

        ttk.Button(footer, text="✅ Apply & Close", command=self._apply_and_close,
                   bootstyle="success", width=14).pack(side=RIGHT, padx=6, pady=4)
        ttk.Button(footer, text="💾 Apply & Keep", command=self._apply_and_keep,
                   bootstyle="info", width=14).pack(side=RIGHT, padx=2, pady=4)

        self._update_preview()

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------


    def _make_scrollable_tab(self, notebook, title):
        """Return a scrollable inner frame for a notebook tab."""
        outer = ttk.Frame(notebook, bootstyle="dark")
        notebook.add(outer, text=title)

        canvas = tk.Canvas(outer, bg='#2b2b2b', highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient=VERTICAL, command=canvas.yview,
                            bootstyle="dark-round")
        canvas.configure(yscrollcommand=vsb.set)

        inner = ttk.Frame(canvas, bootstyle="dark")
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_resize(e):
            canvas.itemconfig(win_id, width=e.width)

        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_canvas_resize)

        # Mouse-wheel scrolling
        def _on_wheel(e):
            if e.delta:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            elif e.num == 4:
                canvas.yview_scroll(-1, "units")
            elif e.num == 5:
                canvas.yview_scroll(1, "units")
        canvas.bind("<MouseWheel>", _on_wheel)
        canvas.bind("<Button-4>", _on_wheel)
        canvas.bind("<Button-5>", _on_wheel)
        inner.bind("<MouseWheel>", _on_wheel)
        inner.bind("<Button-4>", _on_wheel)
        inner.bind("<Button-5>", _on_wheel)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)
        return inner

    def _create_outlier_tab(self):
        tab = self._make_scrollable_tab(self.notebook, "📊 Outliers")

        col_frame = ttk.LabelFrame(tab, text="Columns to check")
        col_frame.pack(fill=X, padx=8, pady=6)
        lf = ttk.Frame(col_frame)
        lf.pack(fill=X, pady=4)
        self.outlier_cols_listbox = tk.Listbox(lf, height=4, selectmode=tk.EXTENDED,
                                               bg='#2b2b2b', fg='white', selectbackground='#375a7f')
        sb = ttk.Scrollbar(lf, orient=VERTICAL, command=self.outlier_cols_listbox.yview,
                           bootstyle="dark-round")
        self.outlier_cols_listbox.configure(yscrollcommand=sb.set)
        self._populate_listbox(self.outlier_cols_listbox)
        self.outlier_cols_listbox.pack(side=LEFT, fill=X, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        method_frame = ttk.LabelFrame(tab, text="Detection method")
        method_frame.pack(fill=X, padx=8, pady=6)
        self.outlier_method_var = tk.StringVar(value="iqr")
        ttk.Radiobutton(method_frame, text="IQR (robust)", variable=self.outlier_method_var,
                        value="iqr", bootstyle="primary").pack(anchor=W, pady=2)
        ttk.Radiobutton(method_frame, text="Z-score", variable=self.outlier_method_var,
                        value="zscore", bootstyle="primary").pack(anchor=W, pady=2)

        tf = ttk.Frame(method_frame)
        tf.pack(fill=X, pady=4)
        ttk.Label(tf, text="Threshold:", bootstyle="light").pack(side=LEFT, padx=4)
        self.outlier_threshold_var = tk.DoubleVar(value=1.5)
        thresh_label = ttk.Label(tf, text="1.5", bootstyle="light", width=4)
        ttk.Scale(tf, from_=1.0, to=5.0, orient=HORIZONTAL,
                  variable=self.outlier_threshold_var, bootstyle="primary").pack(
                  side=LEFT, fill=X, expand=True, padx=4)
        thresh_label.pack(side=LEFT)
        self.outlier_threshold_var.trace('w',
            lambda *_: thresh_label.config(text=f"{self.outlier_threshold_var.get():.1f}"))
        ttk.Label(method_frame, text="(IQR multiplier or Z-score std devs)",
                  font=("TkDefaultFont", 8), bootstyle="secondary").pack()

        af = ttk.Frame(tab)
        af.pack(fill=X, padx=8, pady=6)
        for txt, cmd, style in [
            ("🔍 Detect",          self._detect_outliers,         "info"),
            ("🚩 Flag",             self._flag_outliers,           "warning"),
            ("🗑️ Remove",           self._remove_outliers,         "danger"),
            ("🔄 Replace Median",   self._replace_outliers_median, "secondary"),
        ]:
            ttk.Button(af, text=txt, command=cmd, bootstyle=style).pack(side=LEFT, padx=3)

        self.outlier_summary = tk.Text(tab, height=3, wrap=tk.WORD,
                                       bg='#2b2b2b', fg='#ffffff', font=("TkFixedFont", 8))
        self.outlier_summary.pack(fill=X, padx=8, pady=4)
        self.outlier_summary.insert(tk.END, "No outliers detected yet.")
        self.outlier_summary.config(state=tk.DISABLED)

    def _create_missing_tab(self):
        tab = self._make_scrollable_tab(self.notebook, "❓ Missing")

        summary_frame = ttk.LabelFrame(tab, text="Missing Data Summary")
        summary_frame.pack(fill=X, padx=8, pady=6)
        self.missing_summary_text = tk.Text(summary_frame, height=4, wrap=tk.WORD,
                                            bg='#2b2b2b', fg='#ffffff', font=("TkFixedFont", 8))
        self.missing_summary_text.pack(fill=X, padx=2, pady=2)
        self._update_missing_summary()

        col_frame = ttk.LabelFrame(tab, text="Columns to impute")
        col_frame.pack(fill=X, padx=8, pady=6)
        canvas = tk.Canvas(col_frame, bg='#2b2b2b', highlightthickness=0, height=80)
        sb = ttk.Scrollbar(col_frame, orient=VERTICAL, command=canvas.yview, bootstyle="dark-round")
        sf = ttk.Frame(canvas, bootstyle="dark")
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        self.missing_col_vars = {}
        for col in self.numeric_columns:
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(sf, text=col, variable=var, bootstyle="primary").pack(anchor=W)
            self.missing_col_vars[col] = var
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        method_frame = ttk.LabelFrame(tab, text="Imputation method")
        method_frame.pack(fill=X, padx=8, pady=6)
        self.impute_method_var = tk.StringVar(value="median")
        for label, val in [("Mean (simple)", "mean"), ("Median (robust)", "median"),
                            ("Mode (categorical)", "mode"), ("KNN (k-neighbors)", "knn")]:
            ttk.Radiobutton(method_frame, text=label, variable=self.impute_method_var,
                            value=val, bootstyle="primary").pack(anchor=W, pady=1)
        kf = ttk.Frame(method_frame)
        kf.pack(fill=X, pady=3)
        ttk.Label(kf, text="K neighbors:", bootstyle="light").pack(side=LEFT, padx=4)
        self.knn_neighbors = ttk.Spinbox(kf, from_=1, to=20, width=5)
        self.knn_neighbors.delete(0, tk.END)
        self.knn_neighbors.insert(0, "5")
        self.knn_neighbors.pack(side=LEFT)

        af = ttk.Frame(tab)
        af.pack(fill=X, padx=8, pady=6)
        ttk.Button(af, text="🔍 Analyze Missing",
                   command=self._analyze_missing, bootstyle="info").pack(side=LEFT, padx=3)
        ttk.Button(af, text="✨ Impute Values",
                   command=self._impute_missing, bootstyle="success").pack(side=LEFT, padx=3)

    def _create_transform_tab(self):
        tab = self._make_scrollable_tab(self.notebook, "🔄 Transforms")
        if not HAS_SKBIO:
            wf = ttk.Frame(tab, bootstyle="warning")
            wf.pack(fill=X, padx=8, pady=4)
            ttk.Label(wf, text="⚠️ scikit-bio not installed — using fallback.",
                      bootstyle="inverse-warning").pack(pady=2)

        col_frame = ttk.LabelFrame(tab, text="Compositional parts (must be positive)")
        col_frame.pack(fill=X, padx=8, pady=6)
        sf2 = ttk.Frame(col_frame)
        sf2.pack(fill=X, pady=3)
        ttk.Button(sf2, text="Select All",
                   command=lambda: self._select_all_transform(True), bootstyle="info").pack(side=LEFT, padx=2)
        ttk.Button(sf2, text="Clear All",
                   command=lambda: self._select_all_transform(False), bootstyle="secondary").pack(side=LEFT, padx=2)
        canvas = tk.Canvas(col_frame, bg='#2b2b2b', highlightthickness=0, height=100)
        sb = ttk.Scrollbar(col_frame, orient=VERTICAL, command=canvas.yview, bootstyle="dark-round")
        sf = ttk.Frame(canvas, bootstyle="dark")
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        exclude = {'Sample_ID', 'Notes', 'Date', 'Depth', 'Lat', 'Lon', 'Age'}
        self.transform_col_vars = {}
        for col in self.numeric_columns:
            if not any(ex in col for ex in exclude):
                var = tk.BooleanVar(value=False)
                ttk.Checkbutton(sf, text=col, variable=var, bootstyle="primary").pack(anchor=W)
                self.transform_col_vars[col] = var
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        type_frame = ttk.LabelFrame(tab, text="Transform type")
        type_frame.pack(fill=X, padx=8, pady=6)
        self.transform_type_var = tk.StringVar(value="clr")
        for label, val in [("CLR (Centered Log-Ratio)", "clr"),
                            ("ILR (Isometric Log-Ratio)", "ilr"),
                            ("ALR (Additive Log-Ratio)", "alr")]:
            ttk.Radiobutton(type_frame, text=label, variable=self.transform_type_var,
                            value=val, bootstyle="primary").pack(anchor=W, pady=1)
        alr_row = ttk.Frame(type_frame)
        alr_row.pack(fill=X, pady=3)
        ttk.Label(alr_row, text="Reference column:", bootstyle="light").pack(side=LEFT, padx=4)
        self.alr_ref_var = tk.StringVar()
        self.alr_combo = ttk.Combobox(alr_row, textvariable=self.alr_ref_var,
                                      values=self.numeric_columns, width=15, bootstyle="light")
        self.alr_combo.pack(side=LEFT)

        ttk.Button(tab, text="🔄 Apply Transform",
                   command=self._apply_transform, bootstyle="primary", width=20).pack(pady=10)
        info = tk.Text(tab, height=3, wrap=tk.WORD,
                       bg='#2b2b2b', fg='#95a5a6', font=("TkFixedFont", 8))
        info.pack(fill=X, padx=8, pady=4)
        info.insert(tk.END, "CLR: log(x_i / geometric_mean) → '_CLR' columns.\n"
                            "ILR: Orthogonal coordinates for multivariate analysis.\n"
                            "ALR: log(x_i / reference) → '_ALR' columns.")
        info.config(state=tk.DISABLED)

    def _create_normalization_tab(self):
        tab = self._make_scrollable_tab(self.notebook, "📏 Normalization")

        col_frame = ttk.LabelFrame(tab, text="Columns to normalize")
        col_frame.pack(fill=X, padx=8, pady=6)
        lf = ttk.Frame(col_frame)
        lf.pack(fill=X, pady=4)
        self.norm_cols_listbox = tk.Listbox(lf, height=4, selectmode=tk.EXTENDED,
                                            bg='#2b2b2b', fg='white', selectbackground='#375a7f')
        sb = ttk.Scrollbar(lf, orient=VERTICAL, command=self.norm_cols_listbox.yview,
                           bootstyle="dark-round")
        self.norm_cols_listbox.configure(yscrollcommand=sb.set)
        self._populate_listbox(self.norm_cols_listbox)
        self.norm_cols_listbox.pack(side=LEFT, fill=X, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        method_frame = ttk.LabelFrame(tab, text="Method")
        method_frame.pack(fill=X, padx=8, pady=6)
        self.norm_method_var = tk.StringVar(value="geometric")
        for label, val in [("Geometric mean (log-normal data)", "geometric"),
                            ("Standard (z-score)", "zscore"),
                            ("Min-Max (0–1 scale)", "minmax"),
                            ("Robust (IQR-based)", "robust")]:
            ttk.Radiobutton(method_frame, text=label, variable=self.norm_method_var,
                            value=val, bootstyle="primary").pack(anchor=W, pady=1)
        if HAS_MK:
            mf = ttk.Frame(method_frame)
            mf.pack(fill=X, pady=3)
            self.mk_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(mf, text="Apply Mann-Kendall trend test (detrend before normalization)",
                            variable=self.mk_var, bootstyle="primary").pack(anchor=W)

        ttk.Button(tab, text="📏 Apply Normalization",
                   command=self._apply_normalization, bootstyle="success", width=22).pack(pady=10)

    # ------------------------------------------------------------------
    # Preview helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_cell(val):
        if pd.isna(val):
            return "NA"
        if isinstance(val, (int, float)):
            return f"{val:.2e}" if (abs(val) < 0.01 or abs(val) > 1000) else f"{val:.2f}"
        return str(val)[:12]

    def _populate_tree(self, tree, dataframe, cols, max_rows=20):
        tree["columns"] = cols
        tree.delete(*tree.get_children())
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor=CENTER)
        for i in range(min(max_rows, len(dataframe))):
            row = dataframe.iloc[i]
            values = [self._format_cell(row[c]) if c in row.index else "" for c in cols]
            tree.insert("", tk.END, values=values)

    def _populate_listbox(self, lb):
        lb.delete(0, tk.END)
        for col in self.numeric_columns:
            lb.insert(tk.END, col)

    def _update_preview(self):
        if self.df is None:
            return
        try:
            ptype = self.preview_cols_var.get()
            if ptype == "numeric":
                cols = self.numeric_columns[:15]
            elif ptype == "changed" and self.preview_df is not None:
                cols = [c for c in self.preview_df.columns
                        if c not in self.df.columns or
                        not self.preview_df[c].equals(self.df[c])][:15]
            else:
                cols = self.all_columns[:15]
            if not cols:
                cols = self.all_columns[:10]
            self._populate_tree(self.before_tree, self.df, cols)
            self._populate_tree(self.after_tree,
                                self.preview_df if self.preview_df is not None else self.df, cols)
        except Exception:
            pass

    def _update_missing_summary(self):
        if self.df is None:
            return
        try:
            self.missing_summary_text.config(state=tk.NORMAL)
            self.missing_summary_text.delete(1.0, tk.END)
            total = self.df.size
            missing = int(self.df.isna().sum().sum())
            pct = missing / total * 100 if total else 0
            self.missing_summary_text.insert(tk.END,
                f"Total missing: {missing}/{total} ({pct:.1f}%)\n\n")
            miss_cols = self.df.columns[self.df.isna().any()].tolist()
            if miss_cols:
                self.missing_summary_text.insert(tk.END, "Columns with missing data:\n")
                for col in miss_cols[:10]:
                    self.missing_summary_text.insert(tk.END,
                        f"  • {col}: {int(self.df[col].isna().sum())}\n")
                if len(miss_cols) > 10:
                    self.missing_summary_text.insert(tk.END,
                        f"  … and {len(miss_cols)-10} more\n")
            else:
                self.missing_summary_text.insert(tk.END, "No missing values.")
            self.missing_summary_text.config(state=tk.DISABLED)
        except Exception:
            pass

    def _refresh_ui_data(self):
        if self._read_from_app():
            if hasattr(self, 'outlier_cols_listbox'):
                self._populate_listbox(self.outlier_cols_listbox)
            if hasattr(self, 'norm_cols_listbox'):
                self._populate_listbox(self.norm_cols_listbox)
            if hasattr(self, 'alr_combo'):
                self.alr_combo['values'] = self.numeric_columns
            self._update_missing_summary()
            self._update_preview()
            if self.status_var:
                self.status_var.set("✅ Data refreshed")

    # ------------------------------------------------------------------
    # Operations — Outliers
    # ------------------------------------------------------------------

    def _detect_outliers(self):
        sel = self.outlier_cols_listbox.curselection()
        if not sel:
            messagebox.showwarning("No Columns", "Select at least one column.", parent=self.window)
            return
        selected_cols = [self.numeric_columns[i] for i in sel]
        method = self.outlier_method_var.get()
        threshold = self.outlier_threshold_var.get()
        try:
            outlier_mask = pd.Series(False, index=self.df.index)
            details = []
            for col in selected_cols:
                data = pd.to_numeric(self.df[col], errors='coerce')
                if method == "iqr":
                    Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
                    col_out = (data < Q1 - threshold * (Q3 - Q1)) | (data > Q3 + threshold * (Q3 - Q1))
                    details.append(f"{col}: {int(col_out.sum())} (IQR ×{threshold})")
                else:
                    mean, std = data.mean(), data.std()
                    if std > 0 and not pd.isna(std):
                        col_out = np.abs((data - mean) / std) > threshold
                        details.append(f"{col}: {int(col_out.sum())} (Z>{threshold})")
                    else:
                        col_out = pd.Series(False, index=data.index)
                        details.append(f"{col}: constant")
                outlier_mask |= col_out.fillna(False)

            self.outlier_mask = outlier_mask
            self._push_undo("detect outliers")
            self.preview_df = self.df.copy()
            self.preview_df['_outlier_flag'] = outlier_mask

            self.outlier_summary.config(state=tk.NORMAL)
            self.outlier_summary.delete(1.0, tk.END)
            self.outlier_summary.insert(tk.END,
                f"🔍 {int(outlier_mask.sum())} outlier rows detected\n" +
                "\n".join(f"   {d}" for d in details))
            self.outlier_summary.config(state=tk.DISABLED)
            self._update_preview()
            self.status_var.set(f"✅ {int(outlier_mask.sum())} outliers detected")
        except Exception as e:
            self.status_var.set(f"❌ {e}")

    def _flag_outliers(self):
        if self.outlier_mask is None:
            messagebox.showwarning("No Detection", "Run outlier detection first!", parent=self.window)
            return
        flag_col = f"Outlier_Flag_{datetime.now().strftime('%Y%m%d_%H%M')}"
        records = []
        for i, sample in enumerate(self.app.data_hub.get_all()):
            is_out = bool(self.outlier_mask.iloc[i]) if i < len(self.outlier_mask) else False
            records.append({'Sample_ID': sample.get('Sample_ID', f"SAMPLE_{i}"),
                            flag_col: 'OUTLIER' if is_out else ''})
        if records:
            self.app.import_data_from_plugin(records)
            self.app.samples = self.app.data_hub.get_all()
            self.status_var.set(f"✅ Added '{flag_col}'")
            self._refresh_ui_data()

    def _remove_outliers(self):
        if self.outlier_mask is None:
            messagebox.showwarning("No Detection", "Run outlier detection first!", parent=self.window)
            return
        indices = self.outlier_mask[self.outlier_mask].index.tolist()
        if not indices:
            messagebox.showinfo("No Outliers", "No outliers to remove.", parent=self.window)
            return
        if not messagebox.askyesno("Confirm", f"Remove {len(indices)} outlier rows?", parent=self.window):
            return
        self.app.data_hub.delete_rows(indices)
        self.app.samples = self.app.data_hub.get_all()
        self.outlier_mask = None
        self._refresh_ui_data()
        self.status_var.set(f"✅ Removed {len(indices)} rows")

    def _replace_outliers_median(self):
        if self.outlier_mask is None:
            messagebox.showwarning("No Detection", "Run outlier detection first!", parent=self.window)
            return
        sel = self.outlier_cols_listbox.curselection()
        selected_cols = [self.numeric_columns[i] for i in sel]
        out_idx = [i for i in self._get_target_indices()
                   if i < len(self.outlier_mask) and bool(self.outlier_mask.iloc[i])]
        if not out_idx:
            messagebox.showinfo("No Outliers", "No outliers in target rows.", parent=self.window)
            return
        self._push_undo("replace outliers with median")
        self.preview_df = self.df.copy()
        for col in selected_cols:
            median_val = self.df[col].median()
            for i in out_idx:
                if i < len(self.preview_df):
                    self.preview_df.iat[i, self.preview_df.columns.get_loc(col)] = median_val
        self._update_preview()
        self.status_var.set(f"✅ Replaced outliers with median ({len(out_idx)} rows)")

    # ------------------------------------------------------------------
    # Operations — Missing
    # ------------------------------------------------------------------

    def _analyze_missing(self):
        self._update_missing_summary()
        self.status_var.set("✅ Missing data analysis complete")

    def _impute_missing(self):
        selected_cols = [c for c, v in self.missing_col_vars.items() if v.get()]
        if not selected_cols:
            messagebox.showwarning("No Columns", "Select at least one column.", parent=self.window)
            return
        method = self.impute_method_var.get()
        try:
            self._push_undo(f"impute ({method})")
            self.preview_df = self.df.copy()
            count, imputed_cols = 0, []
            for col in selected_cols:
                if col not in self.preview_df.columns:
                    continue
                missing = self.preview_df[col].isna()
                if not missing.any():
                    continue
                if method == "mean":
                    self.preview_df.loc[missing, col] = self.preview_df[col].mean()
                elif method == "median":
                    self.preview_df.loc[missing, col] = self.preview_df[col].median()
                elif method == "mode":
                    mode = self.preview_df[col].mode()
                    if not mode.empty:
                        self.preview_df.loc[missing, col] = mode.iloc[0]
                elif method == "knn":
                    k = int(self.knn_neighbors.get())
                    numeric_data = self.preview_df[self.numeric_columns].copy()
                    imputed_array = KNNImputer(n_neighbors=k).fit_transform(numeric_data)
                    col_idx = self.numeric_columns.index(col)
                    miss_idx = missing[missing].index
                    self.preview_df.loc[miss_idx, col] = imputed_array[miss_idx, col_idx]
                count += int(missing.sum())
                imputed_cols.append(col)
            if imputed_cols:
                flag_col = f"Imputed_{datetime.now().strftime('%Y%m%d')}"
                self.preview_df[flag_col] = ''
                for col in imputed_cols:
                    self.preview_df.loc[self.df[col].isna(), flag_col] = f"Imputed:{col}"
            self._update_preview()
            self.status_var.set(f"✅ Preview: {count} values imputed in {len(imputed_cols)} cols")
        except Exception as e:
            self.status_var.set(f"❌ Imputation failed: {e}")

    # ------------------------------------------------------------------
    # Operations — Transforms
    # ------------------------------------------------------------------

    def _select_all_transform(self, select):
        for var in self.transform_col_vars.values():
            var.set(select)

    def _apply_transform(self):
        selected_cols = [c for c, v in self.transform_col_vars.items() if v.get()]
        if len(selected_cols) < 2:
            messagebox.showwarning("Select Columns", "Select at least 2 parts.", parent=self.window)
            return
        transform = self.transform_type_var.get()
        try:
            self._push_undo(f"{transform.upper()} transform")
            self.preview_df = self.df.copy()
            data = self.preview_df[selected_cols].copy()
            if (data <= 0).any().any():
                pos = data[data > 0].min().min()
                data[data <= 0] = (pos if not pd.isna(pos) else 0.001) * 0.65
                self.status_var.set("⚠️ Replaced zeros/negatives")

            if transform == "clr":
                if HAS_SKBIO:
                    transformed = clr(data.values)
                else:
                    log_data = np.log(data.values)
                    transformed = log_data - np.mean(log_data, axis=1, keepdims=True)
                suffix = "_CLR"
            elif transform == "ilr":
                if HAS_SKBIO:
                    transformed = ilr(data.values)
                else:
                    log_data = np.log(data.values)
                    transformed = (log_data[:, 0:1] - np.mean(log_data[:, 1:], axis=1, keepdims=True)) \
                                  * np.sqrt(len(selected_cols) / (len(selected_cols) + 1))
                suffix = "_ILR"
            else:
                ref = self.alr_ref_var.get()
                if ref not in selected_cols:
                    messagebox.showwarning("Reference", "Select a reference column!", parent=self.window)
                    return
                ri = selected_cols.index(ref)
                ref_vals = np.where(data.values[:, ri:ri+1] == 0, 1e-10, data.values[:, ri:ri+1])
                transformed = np.log(data.values / ref_vals)
                suffix = "_ALR"

            if transformed.ndim == 1:
                self.preview_df[f"{selected_cols[0]}{suffix}"] = transformed
            else:
                for i, col in enumerate(selected_cols):
                    if i < transformed.shape[1]:
                        self.preview_df[f"{col}{suffix}"] = transformed[:, i]
            self._update_preview()
            self.status_var.set(f"✅ {transform.upper()} applied — review in AFTER panel then Apply")
        except Exception as e:
            self.status_var.set(f"❌ Transform failed: {e}")

    # ------------------------------------------------------------------
    # Operations — Normalization
    # ------------------------------------------------------------------

    def _apply_normalization(self):
        sel = self.norm_cols_listbox.curselection()
        if not sel:
            messagebox.showwarning("No Columns", "Select at least one column.", parent=self.window)
            return
        selected_cols = [self.numeric_columns[i] for i in sel]
        method = self.norm_method_var.get()
        apply_mk = HAS_MK and hasattr(self, 'mk_var') and self.mk_var.get()
        try:
            self._push_undo(f"{method} normalization")
            self.preview_df = self.df.copy()
            for col in selected_cols:
                data = pd.to_numeric(self.preview_df[col], errors='coerce')
                valid = ~data.isna()
                if valid.sum() < 2:
                    continue
                vd = data[valid].values
                if apply_mk:
                    try:
                        _, p = stats.kendalltau(np.arange(len(vd)), vd)
                        if p < 0.05:
                            x = np.arange(len(vd))
                            vd = vd - (np.polyfit(x, vd, 1)[0] * x)
                    except Exception:
                        pass

                lm = method
                if lm == "geometric":
                    if np.all(vd > 0):
                        gm = np.exp(np.mean(np.log(vd)))
                        nd, suffix = (vd / gm, "_GMnorm") if gm > 0 else (None, None)
                        if nd is None:
                            lm = "zscore"
                    else:
                        lm = "zscore"

                if lm == "zscore":
                    mean, std = np.mean(vd), np.std(vd)
                    if std > 0:
                        nd, suffix = (vd - mean) / std, "_Znorm"
                    else:
                        continue
                elif lm == "minmax":
                    mn, mx = np.min(vd), np.max(vd)
                    if mx > mn:
                        nd, suffix = (vd - mn) / (mx - mn), "_MMnorm"
                    else:
                        continue
                elif lm == "robust":
                    med = np.median(vd)
                    iqr = np.percentile(vd, 75) - np.percentile(vd, 25)
                    if iqr > 0:
                        nd, suffix = (vd - med) / iqr, "_Rnorm"
                    else:
                        continue

                norm_series = data.copy()
                norm_series[valid] = nd
                self.preview_df[f"{col}{suffix}"] = norm_series

            self._update_preview()
            self.status_var.set(f"✅ {method} normalization applied — review then Apply")
        except Exception as e:
            self.status_var.set(f"❌ Normalization failed: {e}")

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def _get_target_indices(self):
        if self.apply_target.get() == "selected":
            return list(self.app.center.get_selected_indices())
        return list(range(len(self.df)))

    def _do_apply(self):
        if self.preview_df is None:
            messagebox.showinfo("No Changes", "No preview changes to apply.", parent=self.window)
            return None

        # If "selected" mode, only apply changes to target rows
        if self.apply_target.get() == "selected":
            target = self._get_target_indices()
            if target:
                restricted = self.df.copy()
                # copy changed cols in target rows
                for col in self.preview_df.columns:
                    if col in restricted.columns:
                        for i in target:
                            if i < len(self.preview_df):
                                restricted.iat[i, restricted.columns.get_loc(col)] = \
                                    self.preview_df.iat[i, self.preview_df.columns.get_loc(col)]
                # new cols: only target rows get values, rest get None
                for col in self.preview_df.columns:
                    if col not in self.df.columns:
                        restricted[col] = None
                        for i in target:
                            if i < len(self.preview_df):
                                restricted.at[restricted.index[i], col] = \
                                    self.preview_df.at[self.preview_df.index[i], col]
                self.preview_df = restricted

        return self._write_to_app()

    def _apply_and_keep(self):
        result = self._do_apply()
        if result is None:
            return
        rows, new_cols = result
        if rows == 0 and new_cols == 0:
            messagebox.showinfo("No Changes", "Nothing to apply.", parent=self.window)
            return
        if hasattr(self.app, 'macro_recorder') and self.app.macro_recorder:
            self.app.macro_recorder.record_action('dataprep_apply',
                new_cols=new_cols, rows=rows, target=self.apply_target.get())
        self.status_var.set(f"✅ Applied — {rows} rows updated, {new_cols} new cols added")
        self._refresh_ui_data()

    def _apply_and_close(self):
        result = self._do_apply()
        if result is None:
            return
        rows, new_cols = result
        if rows == 0 and new_cols == 0:
            messagebox.showinfo("No Changes", "Nothing to apply.", parent=self.window)
            return
        if hasattr(self.app, 'macro_recorder') and self.app.macro_recorder:
            self.app.macro_recorder.record_action('dataprep_apply',
                new_cols=new_cols, rows=rows, target=self.apply_target.get())
        messagebox.showinfo("Success",
            f"✅ Applied to {rows} rows\nNew columns added: {new_cols}",
            parent=self.window)
        self.window.destroy()


def setup_plugin(main_app):
    """Plugin entry point called by Scientific Toolkit."""
    return DataPrepPro(main_app)
