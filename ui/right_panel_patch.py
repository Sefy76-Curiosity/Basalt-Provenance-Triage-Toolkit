"""
PATCH for right_panel.py
========================
Only two small changes are needed in right_panel.py.

CHANGE 1 — After the panel is created inside _load_field_panel(), call
           on_selection_changed() once with the current selection so the
           newly-loaded panel immediately reflects whatever is selected
           in the main table.

Find this block at the end of _load_field_panel() (just before the
self.app.center.set_status line):

            self._active_field_panel = panel_class(panel_container, self.app)
            self._current_field_panel = field_id
            self._back_bar = back_bar
            self._panel_container = panel_container

            self.app.center.set_status(...)

REPLACE with:

            self._active_field_panel = panel_class(panel_container, self.app)
            self._current_field_panel = field_id
            self._back_bar = back_bar
            self._panel_container = panel_container

            # ── NEW: push current selection into the freshly-loaded panel ──
            if hasattr(self._active_field_panel, 'on_selection_changed'):
                current_sel = set(getattr(self.app.center, 'selected_rows', set()))
                self._active_field_panel.on_selection_changed(current_sel)

            self.app.center.set_status(...)


CHANGE 2 — _restore_classification_panel() should clear the active panel
           reference so CenterPanel stops sending it selection events.

Find:
            self._current_field_panel = 'classification'
            self._active_field_panel = None

This is already correct — no change needed here.

--- SUMMARY ---
The only line you need to ADD to right_panel.py is the 4-line block
marked with "── NEW:" above, inserted right after the
self._panel_container = panel_container assignment inside _load_field_panel().

Everything else is handled by:
  • center_panel.py  → _notify_field_panel_selection() (new method)
  • right_panel_spectroscopy.py → on_selection_changed() (replaces polling)
"""

# Minimal diff — only the addition inside _load_field_panel:
DIFF = """
@@ inside RightPanel._load_field_panel(), after self._panel_container = panel_container

+           # Push the current row-selection into the freshly-loaded panel
+           # so it renders immediately without waiting for the next click.
+           if hasattr(self._active_field_panel, 'on_selection_changed'):
+               current_sel = set(getattr(self.app.center, 'selected_rows', set()))
+               self._active_field_panel.on_selection_changed(current_sel)
"""
