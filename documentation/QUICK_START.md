# 🚀 Quick Start Guide

**Get Scientific Toolkit running in 5 minutes.**

---

## ⚠️ Before You Start

**This software is provided "AS IS" - you are responsible for validating results.**

- Always check that results make sense for your samples
- Verify methods are appropriate for your data type
- Report bugs and issues on GitLab
- Read citations for methods you use

**Found a problem?** → https://gitlab.com/sefy76/scientific-toolkit/-/issues

---

## Prerequisites

✅ Python 3.8 or higher installed  
✅ pip package manager  
✅ 50 MB free disk space  

---

## Installation (3 minutes)

### Step 1: Download

```bash
# Clone the repository
git clone https://gitlab.com/sefy76/scientific-toolkit.git
cd scientific-toolkit
```

Or download ZIP from GitLab and extract.

### Step 2: Install Dependencies

**Minimal installation (core features):**
```bash
pip install numpy pandas matplotlib
```

**Full installation (all features):**
```bash
pip install -r requirements.txt
```

### Step 3: Launch

```bash
python Scientific-Toolkit.py
```

**Windows users:** Double-click `Scientific-Toolkit.py`

---

## First Use (2 minutes)

### Load Sample Data

1. **File → Import Data → CSV**
2. Navigate to `/samples/master_test_list.csv`
3. Click Open

You should see data loaded in the main table.

### Run Your First Classification

1. **Classify → Geochemistry → TAS Volcanic Classification**
2. A results dialog will show rock types for your samples
3. Click "Add to Dataset" to save classifications

### Create Your First Plot

1. Select samples in the table (Ctrl+Click or Shift+Click)
2. **Visualize → Scatter Plot**
3. Choose X-axis: `SiO2_wt%`
4. Choose Y-axis: `Na2O_K2O_wt%` (total alkalis)
5. Click "Plot"

Congratulations! You've created a TAS diagram.

---

## Common First Tasks

### Task 1: Import Your Own Data

**Supported formats:**
- CSV files
- Excel (.xlsx, .xls)
- Tab-delimited text

**Required columns:**
- `Sample_ID` (or will auto-generate)
- Your measurement columns (any naming convention works)

**Import steps:**
1. File → Import Data → Choose format
2. Select your file
3. Data appears in main table

### Task 2: Connect a Hardware Device

**Example: Bruker pXRF**

1. **Hardware → XRF Analyzers → Bruker Tracer Suite**
2. Click "File Monitor" tab
3. Select folder where Bruker saves files
4. Click "Start Monitoring"
5. New measurements auto-import as you collect them

**Supported devices:** 26+ instruments (see Plugin Guide)

### Task 3: Apply a Classification

**Example: Soil Texture**

1. Ensure you have `Sand_%`, `Silt_%`, `Clay_%` columns
2. **Classify → Soil Science → USDA Soil Texture**
3. Results show texture class (e.g., "Loam", "Sandy Clay")
4. Add to dataset

**Available classifications:** 41 engines across all fields

### Task 4: Run Statistical Analysis

**Example: PCA**

1. Select samples with numeric data
2. **Advanced → PCA+LDA Explorer**
3. Choose variables to include
4. Click "Run PCA"
5. Interactive biplot appears with variance explained

### Task 5: Export Publication Figure

1. Create your plot
2. **Plot → Apply Template → Journal Styles → Nature Style**
3. Adjust labels, colors as needed
4. **File → Export → High-Resolution PDF**
5. 300+ DPI publication-ready output

---

## Understanding the Interface

### Main Window Layout

```
┌─────────────────────────────────────────────────┐
│  Menu Bar: File | Classify | Visualize |        │
│           Hardware | Advanced                    │
├─────────┬───────────────────────────┬───────────┤
│  Left   │   Center (Data Table)     │  Right    │
│  Panel  │                           │  Panel    │
│         │   Your samples display    │           │
│ Filters │   here with all columns   │  Stats    │
│ Search  │                           │  Info     │
│         │                           │           │
└─────────┴───────────────────────────┴───────────┘
│  Status Bar: Sample count | Memory | Messages   │
└─────────────────────────────────────────────────┘
```

### Key Controls

- **Ctrl+A**: Select all samples
- **Ctrl+F**: Find/Filter
- **Ctrl+S**: Save project
- **Delete**: Remove selected samples
- **Right-click**: Context menu with quick actions

---

## Example Workflows

### Workflow 1: Geochemistry Analysis (Igneous Rocks)

```
1. Import XRF data (CSV or direct from instrument)
2. Classify → TAS Volcanic Classification
3. Classify → AFM Series (Tholeiitic vs Calc-Alkaline)
4. Classify → REE Patterns (if trace elements available)
5. Visualize → Scatter Plot (SiO2 vs K2O)
6. Apply Template → AGU Style
7. Export → PDF
```

### Workflow 2: Archaeological Bone Analysis

```
1. Import FTIR or ICP-MS data
2. Classify → Bone Collagen QC (check C:N ratios)
3. Classify → Bone Diagenesis (Ca/P ratios)
4. Classify → Trophic Diet (δ13C, δ15N if available)
5. Advanced → PCA Explorer (compare preservation states)
6. Export results to CSV
```

### Workflow 3: Field Work with Portable XRF

```
1. Hardware → XRF Analyzers → Niton/Vanta Parser
2. Connect USB drive or set file monitor
3. Measurements auto-import as you scan
4. Real-time classification (e.g., provenance)
5. Export daily summary
6. Sync to cloud (manual copy to Dropbox/Drive)
```

### Workflow 4: Soil Survey

```
1. Import field data (texture, EC, GPS coords)
2. Classify → USDA Soil Texture
3. Classify → Soil Salinity (EC-based)
4. Advanced → 3D GIS Viewer
5. Load GPS points + attribute data
6. Export to Google Earth KML
```

---

## Enabling Optional Features

### Enable AI Assistants

1. **Plugins → Add-ons → Claude AI** (or ChatGPT, Gemini, etc.)
2. Enter your API key (get free tier from provider)
3. Ask questions about your data
4. Get interpretation suggestions

**Free option:** Use **Ollama** for fully local AI (no API key needed)

### Enable Advanced Plotting

Already installed with full requirements.txt:
- **Matplotlib Plotter**: Standard plots
- **Seaborn Plotter**: Statistical visualizations
- **Ternary Plotter**: Three-component diagrams
- **GIS Plotter**: Spatial maps

### Enable Hardware Devices

**No additional software needed** - plugins detect instruments via:
- USB serial (XRF, FTIR, GPS, meters)
- File monitoring (universal fallback)

---

## Troubleshooting Quick Fixes

### "Module not found" error
```bash
pip install [module-name]
```

### Data won't import
- Check file encoding (UTF-8 recommended)
- Ensure first row has column headers
- Check for special characters in column names

### Classification returns no results
- Verify required columns exist (check engine documentation)
- Check for numeric data (not text) in measurement columns
- Look for missing values (NaN)

### Plots look wrong
- Try different templates (some optimize for B&W, others for color)
- Check data ranges (outliers can skew axes)
- Use "Auto-scale" button to reset view

### Slow performance
- Large datasets (>10,000 samples)? Enable pagination in settings
- Close unused plugin windows
- Restart application to clear memory

---

## Next Steps

### Learn More
- **[User Guide](USER_GUIDE.md)**: Comprehensive reference
- **[Field Coverage](FIELDS_COVERED.md)**: Explore all 31 fields
- **[Plugin Guide](PLUGIN_GUIDE.md)**: Deep dive into plugins
- **[Classification Engines](CLASSIFICATION_ENGINES.md)**: All 41 engines explained

### Get Help
- **[FAQ](FAQ.md)**: Common questions
- **[Troubleshooting](TROUBLESHOOTING.md)**: Detailed problem solving
- **GitLab Issues**: Ask the community

### Contribute
- Share your workflows
- Request new features
- Report bugs
- Add translations

---

## Tips for Success

✅ **Start small**: Import 10-20 samples to learn the interface  
✅ **Use sample data**: Practice with included datasets  
✅ **One field at a time**: Don't try to learn all 31 fields at once  
✅ **Read classification descriptions**: Hover over engines to see what they do  
✅ **Save often**: Projects save to .toolkit files (JSON format)  
✅ **Explore templates**: Try different journal styles to see preferences  
✅ **Join community**: Share questions and discoveries  

---

## Quick Reference Card

### File Operations
| Action | Menu Path | Shortcut |
|--------|-----------|----------|
| Import CSV | File → Import Data → CSV | Ctrl+O |
| Save Project | File → Save Project | Ctrl+S |
| Export Data | File → Export → CSV | Ctrl+E |

### Classification
| Field | Menu Path |
|-------|-----------|
| Geochemistry | Classify → Geochemistry |
| Archaeology | Classify → Archaeology |
| Soil Science | Classify → Soil Science |
| Meteoritics | Classify → Meteoritics |

### Visualization
| Plot Type | Menu Path |
|-----------|-----------|
| Scatter | Visualize → Scatter Plot |
| Ternary | Visualize → Ternary Diagram |
| 3D | Advanced → 3D GIS Viewer |
| Statistical | Advanced → PCA+LDA Explorer |

### Hardware
| Device Category | Menu Path |
|-----------------|-----------|
| XRF | Hardware → XRF Analyzers |
| FTIR | Hardware → Spectroscopy → FTIR |
| Universal | Hardware → File Monitor |

---

## You're Ready!

You now know enough to:
- ✅ Import data
- ✅ Run classifications
- ✅ Create plots
- ✅ Export results

**Explore at your own pace.** Scientific Toolkit grows with your needs.

---

## 🧪 Help Improve This Software

**Your testing and feedback is essential!**

As you use the toolkit:
- ✅ Verify results make sense for your samples
- ✅ Cross-check important results with other tools
- ✅ Report bugs or unexpected behavior
- ✅ Share what works well (and what doesn't)

**Found an issue?** → [Report on GitLab](https://gitlab.com/sefy76/scientific-toolkit/-/issues)

**Everything working great?** → Star the repository and tell colleagues!

Every bug report and piece of feedback makes this better for the entire scientific community.

---

**Questions?** See [FAQ](FAQ.md) or open an issue on GitLab.

**Want to go deeper?** Continue to [User Guide](USER_GUIDE.md).

<p align="center">
  <a href="README.md">← Back to Main</a> •
  <a href="INSTALLATION.md">Installation Details</a> •
  <a href="USER_GUIDE.md">Full User Guide →</a>
</p>
