# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Basalt Provenance Triage Toolkit v10.1
This creates a standalone Windows executable with all plugins

To build:
    pyinstaller Basalt_Provenance_Toolkit.spec

Output:
    dist/Basalt_Provenance_Toolkit_v10.1.exe (~150 MB)
"""

block_cipher = None

a = Analysis(
    ['Basalt_Provenance_Triage_Toolkit.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('plugins', 'plugins'),  # Include all plugin files
        ('README_PROFESSIONAL.md', '.'),
        ('IOGAS_COMPARISON.md', '.'),
        ('PUBLICATION_CHECKLIST.md', '.'),
    ],
    hiddenimports=[
        # Core imports
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'csv',
        'json',
        
        # Data processing
        'numpy',
        'pandas',
        'openpyxl',
        
        # Plotting
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        
        # Plugin dependencies (optional but include if available)
        'scikit-learn',
        'sklearn.decomposition',
        'sklearn.discriminant_analysis',
        'docx',
        'python-docx',
        'reportlab',
        'reportlab.lib',
        'reportlab.platypus',
        'simplekml',
        'pyvista',
        'folium',
        'geopandas',
        
        # Plugin modules
        'plugins.advanced_export',
        'plugins.advanced_filter',
        'plugins.data_validation',
        'plugins.discrimination_diagrams',
        'plugins.gis_3d_viewer',
        'plugins.google_earth',
        'plugins.literature_comparison',
        'plugins.photo_manager',
        'plugins.plugin_manager',
        'plugins.report_generator',
        'plugins.spider_diagrams',
        'plugins.statistical_analysis',
        'plugins.ternary_diagrams',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'PIL.ImageQt',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Basalt_Provenance_Toolkit_v10.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI only)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon later if desired
)
