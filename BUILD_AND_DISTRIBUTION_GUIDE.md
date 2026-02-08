# 🚀 BUILD AND DISTRIBUTION GUIDE - v10.1

**Package Name:** Basalt Provenance Triage Toolkit v10.1
**Release Date:** February 2026
**Main File:** `Basalt_Provenance_Triage_Toolkit.py` (NO version number!)

---

## 📦 PACKAGE STRUCTURE

This complete package includes EVERYTHING needed for both:
1. **Source distribution** (Python users - all platforms)
2. **Windows EXE** (Windows users without Python)

---

## 🎯 HOW TO SEPARATE FOR DISTRIBUTION

### **Step 1: Create Source Package**

**Contents for:** `Basalt_v10.1_Source.zip`
```
Basalt_v10.1_Source.zip
├── Basalt_Provenance_Triage_Toolkit.py
├── plugins/
│   ├── __init__.py
│   ├── advanced_export.py
│   ├── advanced_filter.py
│   ├── data_validation.py
│   ├── discrimination_diagrams.py
│   ├── gis_3d_viewer.py
│   ├── google_earth.py
│   ├── literature_comparison.py
│   ├── photo_manager.py
│   ├── plugin_manager.py
│   ├── report_generator.py
│   ├── spider_diagrams.py
│   ├── statistical_analysis.py
│   └── ternary_diagrams.py
├── README_PROFESSIONAL.md
├── IOGAS_COMPARISON.md
├── PUBLICATION_CHECKLIST.md
└── INSTALLATION.txt
```

**Target users:**
- Researchers with Python installed
- Linux users
- Mac users
- Developers

**File size:** ~400 KB

---

### **Step 2: Build Windows EXE**

#### **Option A: Build on Windows** (Recommended)

1. Open Command Prompt on Windows
2. Navigate to this folder
3. Double-click: `build_windows_exe.bat`
4. Wait 5-10 minutes
5. Get: `dist/Basalt_Provenance_Toolkit_v10.1.exe`

#### **Option B: Build on Linux/Mac**

```bash
chmod +x build_windows_exe.sh
./build_windows_exe.sh
```

**Output:**
- `dist/Basalt_Provenance_Toolkit_v10.1.exe` (~150 MB)

---

### **Step 3: Create Windows Standalone Package**

**Contents for:** `Basalt_v10.1_Windows_Standalone.zip`
```
Basalt_v10.1_Windows_Standalone.zip
├── Basalt_Provenance_Toolkit_v10.1.exe
├── README_WINDOWS.txt
└── DOUBLE_CLICK_TO_RUN.txt
```

**Target users:**
- Windows users without Python
- "Lazy" users who want one-click
- Non-technical users

**File size:** ~150 MB

---

## 📋 DISTRIBUTION CHECKLIST

### **On GitHub/Zenodo:**

**Primary Download:**
```
📦 Basalt v10.1 - Source Code (400 KB)
   Recommended for: Python users (all platforms)
   Requires: Python 3.8+, pip
   Platforms: Windows, Mac, Linux
```

**Secondary Download:**
```
💻 Basalt v10.1 - Windows Standalone (150 MB)
   Recommended for: Windows users without Python
   Requires: Nothing! Just download and run
   Platforms: Windows 7/8/10/11 (64-bit)
```

---

## 🛠️ TECHNICAL DETAILS

### **PyInstaller Configuration**

The `Basalt_Provenance_Toolkit.spec` file is pre-configured with:
- ✅ All 14 plugins included
- ✅ All documentation embedded
- ✅ Hidden imports for all dependencies
- ✅ UPX compression enabled
- ✅ No console window (GUI only)
- ✅ All optional dependencies included

### **What Gets Bundled in EXE:**

**Always Included:**
- Python 3.x interpreter
- Tkinter (GUI framework)
- NumPy (numerical computing)
- Pandas (data processing)
- Matplotlib (plotting)
- All 14 plugins

**Optionally Included (if installed):**
- scikit-learn (statistical analysis)
- python-docx (Word reports)
- reportlab (PDF reports)
- simplekml (Google Earth)
- PyVista (3D visualization)
- Folium (web maps)
- GeoPandas (GIS)

**Result:** EXE works even if these optional packages aren't on build machine!

---

## 📊 FILE SIZES

| Package | Size | Download Time (10 Mbps) |
|---------|------|-------------------------|
| Source Code | ~400 KB | 0.3 seconds |
| Windows EXE | ~150 MB | 2 minutes |

---

## 🎯 INSTALLATION INSTRUCTIONS

### **For Source Package Users:**

**Windows:**
```batch
1. Install Python 3.8+ from python.org
2. Unzip the package
3. Open Command Prompt
4. cd to the folder
5. Run: python Basalt_Provenance_Triage_Toolkit.py
```

**Mac/Linux:**
```bash
1. Python is already installed!
2. Unzip the package
3. Open Terminal
4. cd to the folder
5. Run: python3 Basalt_Provenance_Triage_Toolkit.py
```

### **For Windows EXE Users:**

```
1. Download Basalt_v10.1_Windows_Standalone.zip
2. Unzip anywhere
3. Double-click: Basalt_Provenance_Toolkit_v10.1.exe
4. That's it!
```

**No Python needed!**
**No installation needed!**
**Just run!**

---

## 🔧 OPTIONAL: Installing Additional Features

### **After running the app:**

1. Open Plugin Manager (Tools → Plugins)
2. See what's missing
3. Click "Install Dependencies"
4. Restart app

**OR manually:**
```bash
pip install simplekml reportlab python-docx pyvista folium geopandas
```

---

## 🎨 CUSTOMIZATION (For Developers)

### **Want to modify the EXE build?**

Edit: `Basalt_Provenance_Toolkit.spec`

**Common modifications:**
- Change icon: `icon='myicon.ico'`
- Add files: `datas=[('myfile.txt', '.')]`
- Exclude packages: `excludes=['huge_unused_lib']`
- Enable console: `console=True`

---

## ⚠️ IMPORTANT NOTES

### **Filename Consistency:**

**Main Python file:** `Basalt_Provenance_Triage_Toolkit.py`
- NO version number
- Easy to replace when upgrading
- Works on all platforms

**EXE output:** `Basalt_Provenance_Toolkit_v10.1.exe`
- HAS version number
- For distribution tracking
- Windows-specific

**Distribution ZIPs:**
- `Basalt_v10.1_Source.zip`
- `Basalt_v10.1_Windows_Standalone.zip`
- Versioned for clarity

### **Why This Structure?**

1. **Source file** has no version → users can easily replace `Basalt_Provenance_Triage_Toolkit.py` when upgrading

2. **Distribution packages** have versions → users know what they downloaded

3. **EXE** has version → prevents confusion when multiple versions exist

---

## 🐛 TROUBLESHOOTING

### **EXE Build Fails:**

**Error:** "PyInstaller not found"
→ Run: `pip install pyinstaller`

**Error:** "Module not found"
→ Install the module: `pip install <module_name>`

**Error:** "Out of memory"
→ Close other programs, build needs 2-4 GB RAM

**Error:** "Permission denied"
→ Run as Administrator (Windows) or use sudo (Linux)

### **EXE Won't Run:**

**Error:** "Windows Defender blocked this"
→ This is normal for unsigned EXE. Click "More info" → "Run anyway"

**Error:** "Missing DLL"
→ Install Visual C++ Redistributable from Microsoft

**Error:** "Application failed to start"
→ Try running from command prompt to see error message

---

## 📈 DISTRIBUTION STRATEGY

### **Recommended Approach:**

1. **GitHub Releases:**
   - Upload both packages
   - Source as primary
   - EXE as "Assets"

2. **Zenodo:**
   - Upload source for DOI
   - Reference EXE download

3. **Website/Documentation:**
   - Explain difference clearly
   - Guide users to right version
   - Emphasize source is recommended

4. **Social Media:**
   - Highlight Windows EXE for adoption
   - Mention "no Python needed"
   - Show screenshots

---

## 🎯 SUPPORT QUESTIONS (Anticipated)

### **"Which version should I download?"**

→ If you have Python or use Mac/Linux: **Source Code**  
→ If you're on Windows without Python: **Windows Standalone**

### **"Does the EXE need installation?"**

→ No! Just download, unzip, and double-click.

### **"Can I use plugins with the EXE?"**

→ Yes! All 14 plugins are built-in. Just enable them in Plugin Manager.

### **"Why is the EXE so large?"**

→ It includes Python + all libraries. This lets it run without Python installed.

### **"Is the EXE safe?"**

→ Yes! It's built from the same open-source code. Windows may show a warning because it's unsigned.

---

## ✅ FINAL CHECKLIST

Before distributing:
- [ ] Source ZIP created
- [ ] EXE built and tested on Windows
- [ ] EXE ZIP created
- [ ] README files updated
- [ ] GitHub release prepared
- [ ] Zenodo upload ready
- [ ] Download links tested
- [ ] File sizes documented
- [ ] Installation instructions verified
- [ ] Screenshots captured

---

## 🎉 YOU'RE READY!

Both packages are now ready for distribution:
✅ Source for Python users (all platforms)
✅ EXE for Windows users (no Python needed)

**Happy releasing!** 🚀
