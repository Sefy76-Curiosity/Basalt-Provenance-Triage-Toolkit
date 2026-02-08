# Basalt Provenance Triage Toolkit v10.2 PRE-RELEASE

## **🚀 THREE-TAB PLUGIN ARCHITECTURE**

This is a pre-release test build with major architectural changes.

---

## **📁 NEW FOLDER STRUCTURE:**

```
plugins/
├── add-ons/           ← UI enhancements
│   ├── demo_data_generator.py
│   └── batch_processor.py
│
├── software/          ← Analysis tools
│   ├── advanced_export.py
│   ├── discrimination_diagrams.py
│   ├── ternary_diagrams.py
│   └── ... (13 plugins)
│
└── hardware/          ← Physical devices
    ├── pxrf_analyzer.py
    ├── digital_caliper.py
    ├── gps_nmea.py
    ├── agilent_ftir.py
    ├── bruker_ftir.py
    ├── thermo_ftir.py
    ├── perkinelmer_ftir.py
    └── file_monitor.py
```

---

## **🔌 NEW PLUGIN MANAGER:**

**Three tabs:**
1. **🎨 UI Add-ons** - Museum import, plotters, demo data, batch processing
2. **📦 Software** - Analysis tools, diagrams, statistics, export
3. **🔌 Hardware** - pXRF, FTIR, GPS, calipers

**Features:**
- ✅ Dynamic plugin discovery (reads from files)
- ✅ Self-describing plugins (PLUGIN_INFO)
- ✅ Per-plugin dependency detection
- ✅ Per-plugin installation
- ✅ Enable/disable any plugin
- ✅ Organized by category

---

## **📊 WHAT'S INCLUDED:**

### **Core:**
- Main application (8,020 lines)
- Classification engine (329 lines)
- 12 classification schemes (JSON)

### **Plugins:**
- **2 UI Add-ons:** Demo data generator, Batch processor
- **13 Software plugins:** All analysis tools
- **8 Hardware plugins:** pXRF (13+ models), FTIR (4 brands), GPS, Caliper

### **Total Support:**
- 35+ hardware device models
- 11+ scientific disciplines
- User-extensible architecture

---

## **🧪 TESTING INSTRUCTIONS:**

### **1. Extract and Run:**
```bash
unzip Basalt_v10.2_PRERELEASE.zip
cd basalt_v10_2_prerelease
python3 Basalt_Provenance_Triage_Toolkit.py
```

### **2. Test Plugin Manager:**
- Click `Tools → 🔌 Manage Plugins`
- You should see 3 tabs:
  - 🎨 UI Add-ons (2 plugins)
  - 📦 Software (13 plugins)
  - 🔌 Hardware (8 plugins)

### **3. Test Add-ons:**
- Enable "Demo Data Generator"
- Apply changes & restart
- Click `Tools → Generate Demo Data`
- Should load 50 samples

### **4. Test Hardware:**
- Go to Hardware tab
- See 8 hardware plugins
- Check dependency status

### **5. Test Classification:**
- Generate demo data
- Click `Tools → 🎯 Classify All`
- Select any scheme
- Verify classification works

---

## **⚠️ KNOWN STATUS:**

### **✅ Working:**
- Plugin Manager (3 tabs)
- Plugin discovery
- Dependency detection
- Demo data generator
- Batch processor
- All 12 classification schemes
- All 8 hardware plugins

### **⚠️ Partial:**
- Museum import (placeholder - needs extraction from main app)
- Matplotlib plotter (needs extraction from main app)

### **🔄 Still in Main App:**
- Museum APIs (~1,000 lines - will move to add-on)
- Plotting code (~300 lines - will move to add-on)
- These will be extracted in next iteration

---

## **🎯 WHAT TO TEST:**

1. **Plugin Manager UI** - Does it show 3 tabs correctly?
2. **Plugin Discovery** - Are all plugins detected?
3. **Dependency Detection** - Does it show missing dependencies?
4. **Enable/Disable** - Can you enable/disable plugins?
5. **Demo Data** - Does demo generator work?
6. **Batch Processor** - Can you process multiple CSVs?
7. **Classification** - Do all 12 schemes work?
8. **Hardware Detection** - Are all 8 hardware plugins shown?

---

## **📝 FEEDBACK NEEDED:**

- Does the 3-tab structure make sense?
- Is plugin organization clear?
- Any issues with plugin discovery?
- Any missing features?

---

## **🚀 NEXT STEPS (for final v10.2):**

1. Extract museum APIs to add-on (~1,000 lines)
2. Extract matplotlib plotter to add-on (~300 lines)
3. Create pillow plotter add-on
4. Create ascii plotter add-on
5. Final testing
6. Documentation

---

**This is a PRE-RELEASE for testing the new architecture!**
**Report any issues before final release!** 🧪
