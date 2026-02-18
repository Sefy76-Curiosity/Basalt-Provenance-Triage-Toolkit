# 🚀 Quick Installation Guide

## Files Included

You've received 6 new Python modules organized in a `features/` folder, plus 1 enhanced main file:

### New Features Folder (place as features/ subdirectory):
The new modules are organized in a `features/` folder for clean organization:

1. `features/__init__.py` - Package initialization
2. `features/tooltip_manager.py` - Provides hover tooltips
3. `features/recent_files_manager.py` - Tracks recent files  
4. `features/macro_recorder.py` - Records and replays workflows
5. `features/project_manager.py` - Saves/loads complete projects
6. `features/script_exporter.py` - Exports to Python scripts

### Enhanced Main File:
7. `Scientific-Toolkit-Enhanced.py` - Main application with all features

### UI Files (already in your project - unchanged):
Your existing `ui/` folder remains untouched:
- `ui/left_panel.py`
- `ui/center_panel.py`
- `ui/right_panel.py`
- `ui/results_dialog.py`

## Installation Steps

### Option 1: Clean Installation (Recommended)

```bash
# Backup your original
cp Scientific-Toolkit.py Scientific-Toolkit-BACKUP.py

# Create the features folder
mkdir -p features

# Copy new feature modules to features/ folder
cp tooltip_manager.py features/
cp recent_files_manager.py features/
cp macro_recorder.py features/
cp project_manager.py features/
cp script_exporter.py features/
cp __init__.py features/

# Copy enhanced main file
cp Scientific-Toolkit-Enhanced.py ./

# Run the enhanced version
python Scientific-Toolkit-Enhanced.py
```

### Option 2: Run Alongside Original

```bash
# Keep both versions
# Create the features folder
mkdir -p features

# Copy all feature files
cp *.py features/ (just the 5 feature modules + __init__.py)
cp Scientific-Toolkit-Enhanced.py ./

# Run either version:
python Scientific-Toolkit.py          # Original
python Scientific-Toolkit-Enhanced.py  # Enhanced
```

## Directory Structure After Installation

```
your_project/
├── Scientific-Toolkit.py              (original - keep as backup)
├── Scientific-Toolkit-Enhanced.py     (new enhanced version)
├── data_hub.py                        (existing)
├── features/                          (NEW folder for enhanced features)
│   ├── __init__.py                    (package init)
│   ├── tooltip_manager.py             (tooltips system)
│   ├── recent_files_manager.py        (recent files tracking)
│   ├── macro_recorder.py              (workflow recorder)
│   ├── project_manager.py             (project save/load)
│   └── script_exporter.py             (Python export)
├── ui/                                (existing UI folder - unchanged)
│   ├── left_panel.py                  (existing)
│   ├── center_panel.py                (existing)
│   ├── right_panel.py                 (existing)
│   └── results_dialog.py              (existing)
├── config/
│   ├── chemical_elements.json         (existing)
│   ├── scatter_colors.json            (existing)
│   ├── recent_files.json              (auto-created by new features)
│   └── macros.json                    (auto-created by new features)
└── engines/
    └── (your existing engines)
```

## First Launch

1. Launch the enhanced version:
   ```bash
   python Scientific-Toolkit-Enhanced.py
   ```

2. You should see the familiar splash screen

3. Once loaded, press **F1** to see all keyboard shortcuts

4. Try these features immediately:
   - Press **Ctrl+I** to import data
   - Press **Ctrl+R** to start recording a macro
   - Hover over buttons to see tooltips
   - Check **File → Recent Files** menu

## Verification

To verify all features are working:

### ✅ Keyboard Shortcuts:
- Press `F1` → Should show shortcuts dialog
- Press `Ctrl+N` → Should prompt for new project

### ✅ Tooltips:
- Hover over "Import Data" button → Tooltip should appear after 500ms

### ✅ Recent Files:
- Import a file → Check `File → Recent Files` menu

### ✅ Project Save/Load:
- Import some data
- Press `Ctrl+S` → Save as `.stproj` file
- Press `Ctrl+N` → Clear data
- Press `Ctrl+O` → Load the project back

### ✅ Macro Recording:
- Press `Ctrl+R` → Start recording
- Do some actions (import, classify, etc.)
- Press `Ctrl+T` → Stop and save macro
- Press `Ctrl+M` → See saved macro in manager

### ✅ Script Export:
- Set up a workflow
- Go to `File → Export to Python Script`
- Export and check the generated `.py` file

## Troubleshooting

### Import Errors
**Error:** `ModuleNotFoundError: No module named 'features'`

**Solution:** Make sure you have created the `features/` folder and placed all 6 files inside it:
- `features/__init__.py`
- `features/tooltip_manager.py`
- `features/recent_files_manager.py`
- `features/macro_recorder.py`
- `features/project_manager.py`
- `features/script_exporter.py`

The folder structure should be:
```
your_project/
├── Scientific-Toolkit-Enhanced.py
├── features/
│   ├── __init__.py
│   └── (5 feature modules)
└── ui/
    └── (your existing UI files)
```

### Config Directory Not Found
**Error:** Config file warnings in console

**Solution:** The config files will be auto-created. If needed, create manually:
```bash
mkdir -p config
```

### Keyboard Shortcuts Not Working
**Issue:** Key combinations don't respond

**Solution:** 
- Ensure the application window has focus
- Some OS shortcuts may conflict (especially on macOS)
- Check terminal for error messages

### Tooltips Not Appearing
**Issue:** Hovering doesn't show tooltips

**Solution:**
- Wait 500ms for tooltip to appear
- Move mouse completely off the widget then back on
- Check that `tooltip_manager.py` loaded successfully

## Dependencies

The enhanced version requires the same dependencies as the original:

```bash
pip install pandas openpyxl tkinter
```

No additional dependencies needed for the new features!

## Configuration Files

The following files will be auto-created on first use:

### config/recent_files.json
```json
{
  "files": [
    {
      "path": "/path/to/file.csv",
      "name": "file.csv",
      "timestamp": "2026-02-17T10:00:00"
    }
  ]
}
```

### config/macros.json
```json
{
  "My Workflow": [
    {
      "type": "import_file",
      "params": {"filepath": "/path/to/data.csv"},
      "timestamp": "2026-02-17T10:00:00"
    }
  ]
}
```

## Rollback Instructions

If you need to revert to the original version:

```bash
# Simply run the original file
python Scientific-Toolkit.py

# Or remove enhanced files
rm tooltip_manager.py
rm recent_files_manager.py
rm macro_recorder.py
rm project_manager.py
rm script_exporter.py
rm Scientific-Toolkit-Enhanced.py
```

Your data and config files are unaffected.

## Next Steps

1. **Read the full documentation:** See `ENHANCED_FEATURES_README.md`

2. **Try the new features:** Follow the tutorials in the README

3. **Record your first macro:** Automate your common workflows

4. **Save your first project:** Never lose your work again

5. **Export a workflow:** Share with colleagues as Python code

## Support

If you encounter any issues:

1. Check the console output for error messages
2. Verify all files are in the correct locations  
3. Ensure original toolkit was working first
4. Contact: sefy76@gmail.com

---

**Happy analyzing! 🔬**
