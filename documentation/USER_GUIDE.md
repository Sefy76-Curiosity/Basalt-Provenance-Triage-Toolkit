# Scientific Toolkit v2.0 - User Guide

**A comprehensive guide to using Scientific Toolkit for your research**

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Interface Overview](#interface-overview)
4. [Data Management](#data-management)
5. [Classification Systems](#classification-systems)
6. [Working with Plugins](#working-with-plugins)
7. [Visualization](#visualization)
8. [Advanced Features](#advanced-features)
9. [Common Workflows](#common-workflows)
10. [Tips & Best Practices](#tips--best-practices)
11. [FAQ](#faq)

---

## Introduction

### What is Scientific Toolkit?

Scientific Toolkit is a comprehensive, open-source platform for scientific data analysis. It integrates:

- **80+ plugins** for instruments, analysis methods, and AI assistants
- **37 classification systems** for multiple scientific domains
- **Publication-ready visualizations**
- **Multi-domain support**: geochemistry, archaeology, material science, and more

### Who Should Use This?

- **Researchers**: Geologists, archaeologists, material scientists
- **Students**: Graduate students needing data analysis tools
- **Labs**: Research facilities with multiple instruments
- **Museums**: Collections management and analysis

### Key Capabilities

✅ Load and standardize data from CSV, Excel, or instruments  
✅ Auto-detect element names in any format  
✅ Apply 37 different classification systems  
✅ Connect to XRF, ICP-MS, FTIR, and other instruments  
✅ Ask AI assistants questions about your data  
✅ Create publication-quality plots  
✅ Export results in multiple formats  

---

## Getting Started

### First Launch

1. **Start the toolkit**:
   ```bash
   python Scientific-Toolkit.py
   ```

2. **Splash screen** appears showing loading progress

3. **Main window** opens with three panels:
   - **Left**: Data browser and file management
   - **Center**: Main workspace and visualization
   - **Right**: Controls, settings, and results

### Quick Start Workflow

```
Load Data → Standardize Columns → Apply Classification → View Results → Export
```

Let's try with sample data:

1. Click **"Open Data"** in the left panel
2. Navigate to `samples/master_test_list.csv`
3. Click **"Load"**
4. Data appears in the center panel table
5. Go to **"Classifications"** tab in right panel
6. Select **"TAS Diagram"** from dropdown
7. Click **"Run Classification"**
8. Results appear with sample classifications
9. Click **"Plot"** to visualize

**That's it!** You've completed your first analysis.

---

## Interface Overview

### Main Window Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Menu Bar: File | Edit | View | Tools | Plugins | Help       │
├─────────┬────────────────────────────────────────┬───────────┤
│         │                                        │           │
│  Left   │            Center Panel               │   Right   │
│  Panel  │                                        │   Panel   │
│         │  - Data table                          │           │
│  - File │  - Plots                               │  - Filter │
│  browser│  - Maps                                │  - Classify│
│  - Data │  - Analysis results                    │  - Export │
│  list   │                                        │  - Settings│
│         │                                        │           │
└─────────┴────────────────────────────────────────┴───────────┘
│  Status Bar: Ready | 125 samples loaded | 15 elements       │
└──────────────────────────────────────────────────────────────┘
```

### Menu Bar

- **File**: Open, Save, Import, Export, Recent Files
- **Edit**: Undo, Redo, Preferences
- **View**: Toggle panels, Zoom, Themes
- **Tools**: Data validation, Batch processing, Statistics
- **Plugins**: Enable/disable plugins, Configure hardware
- **Help**: User guide, About, Check for updates

### Left Panel

**Data Browser**:
- File explorer for local files
- Recently opened datasets
- Sample data library

**Data Management**:
- Load/unload datasets
- Merge datasets
- Create new columns
- Delete columns

### Center Panel

**Tabs**:
1. **Data Table**: Spreadsheet view of current dataset
2. **Visualizations**: Plots, charts, diagrams
3. **Maps**: GIS and spatial visualization
4. **Results**: Classification and analysis outputs

**Features**:
- Sortable columns (click headers)
- Resizable columns (drag borders)
- Cell selection and copying
- Quick filtering (right-click column)

### Right Panel

**Tabs**:
1. **Filter**: Subset data by conditions
2. **Classify**: Apply classification systems
3. **Export**: Save results and figures
4. **Plugins**: Enable/configure plugins
5. **Settings**: Global preferences

---

## Data Management

### Importing Data

#### From CSV Files

1. Click **File → Open** or press `Ctrl+O`
2. Select your CSV file
3. Configure import settings:
   - Delimiter (comma, tab, semicolon)
   - Decimal separator (. or ,)
   - Skip rows (if header is not first line)
   - Encoding (UTF-8, Latin-1, etc.)
4. Click **Import**

**Supported formats**:
- `.csv` - Comma-separated values
- `.tsv` - Tab-separated values
- `.txt` - Text files with any delimiter

#### From Excel Files

1. Click **File → Open**
2. Select `.xlsx` or `.xls` file
3. Choose worksheet (if multiple sheets)
4. Select data range (or use entire sheet)
5. Click **Import**

#### From Instruments

With hardware plugins enabled:

1. Go to **Plugins → Hardware → [Your Instrument]**
2. Click **Connect**
3. Configure acquisition parameters
4. Click **Acquire** or **Import Recent Data**
5. Data loads automatically

**Supported instruments**:
- Bruker XRF (Tracer, S1, etc.)
- Thermo/Niton pXRF
- Bruker/PerkinElmer/Thermo FTIR
- Generic serial/USB devices

#### Programmatic Import

```python
# Via Python API (if using as library)
from data_hub import DataHub

hub = DataHub()
df = hub.load_csv("my_data.csv")
df = hub.standardize_columns(df)
```

### Column Standardization

The toolkit auto-detects element names in various formats:

**Example**: Zirconium can be named:
- `Zr`, `Zr_ppm`, `Zr (ppm)`, `Zirconium`, `Zr-ppm`, `Zr含量`, `锆`

All are automatically mapped to standard name: `Zr_ppm`

**To standardize manually**:
1. Go to **Edit → Standardize Column Names**
2. Review suggested mappings
3. Adjust if needed
4. Click **Apply**

### Data Validation

Check data quality:

1. Go to **Tools → Data Validation**
2. Select validation rules:
   - Check for missing values
   - Check for negative values (elements should be positive)
   - Check for outliers (>3σ)
   - Check for duplicates
3. Click **Validate**
4. Review flagged issues
5. Fix or flag samples

### Filtering Data

**Quick Filter** (single condition):
1. Right-click column header
2. Select **Filter**
3. Choose condition (>, <, =, contains, etc.)
4. Enter value
5. Apply

**Advanced Filter** (multiple conditions):
1. Go to right panel → **Filter** tab
2. Add conditions:
   - `SiO2_wt% > 45`
   - `TiO2_wt% < 2`
   - `Sample_ID contains "ABC"`
3. Choose **AND** or **OR** logic
4. Click **Apply Filter**
5. Filtered data appears in table

**Clear filter**: Click **Reset Filter** button

### Creating Calculated Columns

Add derived values:

1. Go to **Edit → Add Calculated Column**
2. Enter formula:
   - `Zr/Nb` (simple ratio)
   - `(Na2O + K2O)` (sum)
   - `log10(Ba)` (transform)
3. Name the new column
4. Click **Calculate**

**Supported operations**:
- Arithmetic: `+`, `-`, `*`, `/`, `**` (power)
- Functions: `log10()`, `ln()`, `sqrt()`, `abs()`
- Conditionals: `if(condition, true_value, false_value)`

---

## Classification Systems

### Overview

Classification systems automatically categorize samples based on geochemical or physical properties.

**37 systems available** including:
- TAS (Total Alkali vs Silica) for volcanic rocks
- AFM diagrams for magma series
- REE patterns for source discrimination
- Soil texture classification
- Water hardness classification
- Meteorite classification
- Bone preservation indices

### Using Classifications

**Basic workflow**:

1. Load data with required elements
2. Go to right panel → **Classify** tab
3. Select classification from dropdown
4. Review required columns (shown below dropdown)
5. Click **Run Classification**
6. Results appear in new column

**Example**: TAS Diagram

```
Required columns: SiO2_wt%, Na2O_wt%, K2O_wt%
Your data has: ✓ SiO2_wt%, ✓ Na2O_wt%, ✓ K2O_wt%
Status: Ready to classify
```

Click **Run** → New column `TAS_Classification` appears with:
- Basalt
- Basaltic Andesite
- Andesite
- Dacite
- Rhyolite
- etc.

### Available Classification Systems

#### Geochemistry

1. **TAS Diagram** - Volcanic rock classification
   - Required: SiO2, Na2O, K2O
   - Citation: Le Bas et al. (1986)

2. **AFM Diagram** - Tholeiitic vs Calc-alkaline
   - Required: FeO (total iron), MgO, Na2O+K2O
   - Citation: Irvine & Baragar (1971)

3. **Pearce Mantle Array** - Tectonic setting
   - Required: Zr/Y, Nb/Y
   - Citation: Pearce et al. (1984)

4. **REE Patterns** - Rare earth element classification
   - Required: La, Ce, Pr, Nd, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu
   - Citation: McDonough & Sun (1995)

**Important**: When using these classification systems in publications, cite both this toolkit AND the original scientific papers. See [REFERENCES.md](REFERENCES.md) for complete citations.

#### Archaeology

5. **Bone Diagenesis** - Preservation quality
   - Required: Ca, P, Crystallinity Index

6. **Stable Isotope Diet** - Dietary reconstruction
   - Required: δ13C, δ15N

7. **Lithic Morphometrics** - Stone tool classification
   - Required: Length, Width, Thickness, Weight

#### Material Science

8. **Ceramic Firing Temperature** - Manufacturing conditions
   - Required: Fe2O3, CaO, MgO

9. **Glass Compositional Families** - Glass type
   - Required: Na2O, K2O, CaO, MgO, Al2O3

10. **Meteorite Classification** - Meteorite type
    - Required: Fe, Ni, Si, Mg

#### Environmental

11. **Soil Texture** - USDA classification
    - Required: % Sand, % Silt, % Clay

12. **Water Hardness** - Water quality
    - Required: Ca, Mg

13. **Geoaccumulation Index** - Pollution assessment
    - Required: Element concentrations, background values

### Custom Classifications

Create your own classification system:

1. Go to `engines/classification/`
2. Copy `_TEMPLATE.json`
3. Edit with your rules:

```json
{
  "name": "My Custom Classification",
  "version": "1.0",
  "description": "Classify based on Zr/Nb ratio",
  "required_columns": ["Zr_ppm", "Nb_ppm"],
  "algorithm": "boundaries",
  "regions": [
    {
      "name": "High Zr/Nb",
      "rules": [
        {"column": "Zr_ppm", "operator": ">", "value": 100},
        {"column": "Nb_ppm", "operator": "<", "value": 10}
      ]
    },
    {
      "name": "Low Zr/Nb",
      "rules": [
        {"column": "Zr_ppm", "operator": "<", "value": 100},
        {"column": "Nb_ppm", "operator": ">", "value": 10}
      ]
    }
  ]
}
```

4. Save file
5. Restart toolkit
6. New classification appears in dropdown

---

## Working with Plugins

### Plugin Types

**Hardware** (7 unified suites + 19 instruments):
- Connect to instruments
- Acquire data in real-time
- Import instrument files

**Software** (37 plugins):
- Advanced statistics
- Machine learning
- GIS tools
- Specialized analyses

**Add-ons** (17 plugins):
- Visualization libraries
- AI assistants
- Utilities

### Enabling Plugins

**Method 1: GUI**
1. Go to **Plugins → Manage Plugins**
2. Check boxes to enable
3. Click **Apply**
4. Restart toolkit

**Method 2: Config File**
Edit `config/enabled_plugins.json`:

```json
{
  "hardware": [
    "benchtop_xrf",
    "digital_caliper"
  ],
  "software": [
    "pca_explorer",
    "machine_learning",
    "google_earth"
  ],
  "add-ons": [
    "claude_ai",
    "matplotlib_plotter"
  ]
}
```

### Using Hardware Plugins

**Example: Benchtop XRF**

1. **Enable plugin**: Plugins → Hardware → Benchtop XRF
2. **Connect**: Click **Connect to Instrument**
3. **Configure**:
   - Acquisition time: 30 seconds
   - Beam size: 8mm
   - Filter: Auto
4. **Acquire**:
   - Load sample
   - Click **Acquire Spectrum**
   - Wait for completion
5. **Data appears** in main table

**Supported instruments**:
- XRF (Bruker, Thermo, Niton, Vanta)
- FTIR (Bruker, PerkinElmer, Thermo)
- ICP-MS (Generic)
- Digital calipers
- GPS receivers
- pH/EC meters
- Magnetic susceptibility meters

### Using AI Plugins

**Setup**:
1. Get API keys from providers
2. Set environment variables or enter in GUI
3. Enable AI plugin

**Usage**:
1. Go to **Plugins → AI Assistant → Claude** (or other)
2. **Chat interface** appears
3. Ask questions:
   - "What's the average SiO2 in my basalt samples?"
   - "Which classification should I use for provenance?"
   - "Are there outliers in my data?"
   - "Suggest analyses for this dataset"
4. AI responds with insights and suggestions

**Available AI providers**:
- ChatGPT (OpenAI)
- Claude (Anthropic)
- Gemini (Google)
- Copilot (Microsoft)
- DeepSeek
- Grok (X.AI)
- Ollama (local models)

---

## Visualization

### Creating Plots

**Quick plot**:
1. Select columns to plot
2. Right-click → **Quick Plot**
3. Choose plot type:
   - Scatter
   - Line
   - Bar
   - Histogram
   - Box plot

**Custom plot**:
1. Go to **View → Create Plot**
2. Configure:
   - X-axis: Select column
   - Y-axis: Select column
   - Color by: (optional) Select categorical column
   - Size by: (optional) Select numerical column
   - Plot type: Scatter, line, etc.
3. Click **Generate**

### Plot Types

**Scatter plots**: For X-Y relationships
```
Example: SiO2 vs K2O colored by rock type
```

**Ternary diagrams**: For 3-component systems
```
Example: AFM diagram (FeO-MgO-Alkalis)
```

**Spider diagrams**: For multi-element patterns
```
Example: REE patterns normalized to chondrite
```

**Box plots**: For statistical distributions
```
Example: Zr distribution by source region
```

**Histograms**: For frequency distributions
```
Example: Distribution of SiO2 values
```

**Contour plots**: For spatial data
```
Example: Kriging interpolation of element concentrations
```

**3D plots**: For complex relationships
```
Example: PCA visualization in 3D space
```

### Customizing Plots

**Appearance**:
- Title, axis labels, legend
- Colors, markers, line styles
- Font sizes
- Grid on/off

**Data display**:
- Add error bars
- Show data labels
- Highlight specific samples
- Add trendlines

**Advanced**:
- Multiple Y-axes
- Subplots
- Logarithmic scales
- Custom color maps

### Exporting Figures

1. Right-click plot → **Export**
2. Choose format:
   - PNG (raster, for presentations)
   - SVG (vector, for publications)
   - PDF (vector, for journals)
3. Set resolution (DPI):
   - Screen: 72-96 DPI
   - Print: 300 DPI
   - Publication: 600 DPI
4. Save

---

## Advanced Features

### PCA Analysis

**Principal Component Analysis** for dimensionality reduction:

1. Go to **Plugins → Software → PCA Explorer**
2. Select elements for analysis
3. Click **Run PCA**
4. Results show:
   - Scree plot (variance explained)
   - Loading plot (element contributions)
   - Score plot (sample positions)
   - Biplot (combined)
5. Interpret:
   - PC1 explains most variance
   - Samples cluster by similarity
   - Elements loading together correlate

**Applications**:
- Source discrimination
- Identifying patterns
- Reducing dimensionality
- Quality control

### Machine Learning

**Available algorithms**:
- K-means clustering
- Hierarchical clustering
- Random Forest classification
- Support Vector Machines
- Neural networks

**Workflow**:
1. Prepare data (clean, standardize)
2. Select features (elements)
3. Choose algorithm
4. Train model
5. Evaluate performance
6. Predict new samples

### GIS Integration

**Features**:
- Import GPS coordinates
- Plot on interactive maps
- Kriging interpolation
- Export to Google Earth (KML)
- 3D terrain visualization

**Example**:
1. Load data with Lat/Lon columns
2. Go to **Plugins → GIS 3D Viewer**
3. Select element to visualize
4. Choose interpolation method
5. Generate map
6. Export KML

### Statistical Analysis

**Available tests**:
- Descriptive statistics
- Correlation analysis
- T-tests, ANOVA
- Regression
- Chi-square tests
- Non-parametric tests

**Workflow**:
1. Go to **Tools → Statistics**
2. Select test type
3. Choose variables
4. Set significance level (α = 0.05)
5. Run test
6. Interpret results

---

## Common Workflows

### Workflow 1: XRF Data Processing

**Goal**: Process raw XRF data and classify samples

1. **Import data**:
   - File → Open → Select XRF CSV file
   - Or Plugins → Benchtop XRF → Import Recent

2. **Quality control**:
   - Tools → Data Validation
   - Check for negative values
   - Flag outliers

3. **Drift correction** (if multi-day acquisition):
   - Plugins → pXRF Drift Correction
   - Select standards
   - Apply correction

4. **Standardize columns**:
   - Edit → Standardize Column Names
   - Verify element mappings

5. **Apply classification**:
   - Classify tab → TAS Diagram
   - Run classification

6. **Visualize**:
   - Create TAS plot
   - Color by classification
   - Export at 300 DPI

### Workflow 2: Provenance Analysis

**Goal**: Determine source of archaeological artifacts

1. **Load artifact data**:
   - Must include trace elements (Zr, Nb, Rb, Sr, Y)

2. **Load reference database**:
   - File → Import Reference Data
   - Select known source samples

3. **Apply discriminant analysis**:
   - Plugins → Discrimination Diagrams
   - Select Zr vs Nb, Rb vs Sr, etc.
   - Plot with reference fields

4. **Run PCA**:
   - Include artifacts and references
   - Look for clustering

5. **Statistical comparison**:
   - Tools → Statistics → MANOVA
   - Compare artifact group to each source

6. **Generate report**:
   - Plugins → Report Generator
   - Include plots and statistics
   - Export to PDF

### Workflow 3: Multi-Element Characterization

**Goal**: Complete geochemical characterization

1. **Acquire data** from multiple techniques:
   - XRF for major/trace elements
   - ICP-MS for ultra-trace
   - FTIR for mineralogy

2. **Merge datasets**:
   - Data Management → Merge Datasets
   - Match by Sample_ID

3. **Calculate ratios**:
   - Edit → Add Calculated Column
   - Add: Zr/Nb, La/Yb, Eu/Eu*, etc.

4. **Run all relevant classifications**:
   - TAS, AFM, REE patterns, etc.

5. **Create composite figure**:
   - View → Multi-Panel Plot
   - Add 4-6 discrimination diagrams
   - Standardize colors

6. **Export for publication**:
   - Export each panel at 600 DPI
   - Combine in graphics software

---

## Tips & Best Practices

### Data Management

✅ **Use consistent naming**: Same format across all files  
✅ **Include Sample_ID**: Unique identifier for each sample  
✅ **Document metadata**: Date, location, analyst, method  
✅ **Backup regularly**: Keep copies of raw and processed data  
✅ **Version control**: Date your files (e.g., `data_2026-02-15.csv`)  

### Analysis

✅ **Check data quality first**: Validate before analysis  
✅ **Start simple**: Basic plots before complex statistics  
✅ **Use appropriate classifications**: Check requirements  
✅ **Cross-validate**: Use multiple methods  
✅ **Document decisions**: Keep analysis log  

### Visualization

✅ **Label everything**: Axes, units, legend  
✅ **Use color wisely**: Colorblind-friendly palettes  
✅ **High resolution**: 300+ DPI for publications  
✅ **Consistent style**: Same fonts, sizes across figures  
✅ **Vector formats**: SVG/PDF for scalability  

### Performance

✅ **Filter large datasets**: Work with subsets  
✅ **Close unused plugins**: Reduces memory usage  
✅ **Clear cache**: Tools → Clear Cache  
✅ **Update regularly**: Check for toolkit updates  

---

## FAQ

### General

**Q: Is Scientific Toolkit free?**  
A: Yes! It's open-source under CC BY-NC-SA 4.0. Free for research and education.

**Q: Do I need programming knowledge?**  
A: No. The GUI is designed for non-programmers. Python knowledge helpful for advanced customization.

**Q: Can I use it commercially?**  
A: Commercial use requires special license. Contact sefy76@gmail.com.

**Q: What Python version do I need?**  
A: Python 3.8 or higher. Python 3.10+ recommended.

### Data

**Q: What data formats are supported?**  
A: CSV, Excel (.xlsx, .xls), JSON, and instrument-specific formats (PDZ, Bruker, Niton, etc.).

**Q: How many samples can I load?**  
A: Tested with up to 10,000 samples. Larger datasets may be slow.

**Q: Can I analyze non-geochemical data?**  
A: Yes! The system is flexible. Many features work with any numerical data.

**Q: How do I handle missing values?**  
A: Use Edit → Fill Missing Values. Options: mean, median, interpolation, or delete.

### Classifications

**Q: Which classification should I use?**  
A: Depends on your research question. Check requirements and scientific literature.

**Q: Can samples be unclassified?**  
A: Yes. If data doesn't meet criteria, result will be "Unclassified" or "Indeterminate".

**Q: How accurate are classifications?**  
A: Depends on data quality. Always verify against literature.

### Instruments

**Q: My instrument isn't listed. Can I still use it?**  
A: Yes! Import data as CSV. Or create custom plugin (see PLUGIN_DEVELOPMENT.md).

**Q: Do I need special drivers?**  
A: Some instruments require drivers. See docs/INSTRUMENTS.md.

**Q: Can I connect multiple instruments?**  
A: Yes. Enable multiple hardware plugins.

### AI

**Q: Do AI features require internet?**  
A: Most do, except Ollama (local models).

**Q: Are API keys required?**  
A: Yes, for ChatGPT, Claude, Gemini, etc. Not for Ollama.

**Q: Is my data sent to AI providers?**  
A: Only if you explicitly use AI features. You control what data is shared.

### Troubleshooting

**Q: Toolkit won't start**  
A: Check Python version, dependencies, and see TROUBLESHOOTING.md.

**Q: Import fails**  
A: Verify file format, encoding (try UTF-8), and check for special characters.

**Q: Classification returns all "Unclassified"**  
A: Check required columns exist and contain valid data.

**Q: Plots look wrong**  
A: Verify data types (numerical vs categorical), units, and axis selections.

**Q: Out of memory error**  
A: Filter dataset, close unused plugins, or upgrade RAM.

---

## Getting Help

- 📚 Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 🐛 Report bugs on [GitHub Issues](https://github.com/sefy-levy/scientific-toolkit/issues)
- 💬 Ask questions in [GitHub Discussions](https://github.com/sefy-levy/scientific-toolkit/discussions)
- 📧 Email: sefy76@gmail.com

---

**Happy Analyzing!** 🔬

*User Guide v2.0 | Last updated: February 2026*
