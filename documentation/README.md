# 🔬 Scientific Toolkit v2.0

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/sefy-levy/scientific-toolkit)

> **A comprehensive, modular toolkit for scientific data analysis across geochemistry, archaeology, material science, and more.**

Based on the Basalt Provenance Triage Toolkit v10.2, this open-source platform integrates hardware instruments, advanced analytics, AI assistants, and publication-ready visualizations in one unified interface.

![Scientific Toolkit Interface](docs/images/interface_preview.png)
*Main interface showing data management, classification engines, and real-time analysis*

---

## 🌟 Key Features

### 📊 Multi-Domain Scientific Analysis
- **Geochemistry**: XRF, ICP-MS, LA-ICP-MS data processing with drift correction
- **Archaeology**: Zooarchaeology, stable isotopes, lithic morphometrics, bone diagenesis
- **Material Science**: FTIR, Raman, XRD spectroscopy and powder diffraction
- **Mineralogy**: Normative calculations, mineral identification, phase analysis
- **GIS & Spatial**: 3D visualization, kriging interpolation, Google Earth integration
- **Statistics & ML**: PCA, clustering, classification, uncertainty propagation

### 🔌 80+ Plugins
- **Hardware Integration** (7 unified suites + 19 instruments): Direct acquisition from benchtop XRF, FTIR, digital calipers, GPS, EC meters, and more
- **Software Analytics** (37 plugins): Advanced statistics, machine learning, GIS tools, publication layouts
- **Add-ons** (17 plugins): Visualization libraries, batch processing, demo data generators
- **AI Assistants** (7 providers): ChatGPT, Claude, Gemini, Copilot, DeepSeek, Grok, Ollama

### ⚙️ 37 Classification Systems
Automated classification for volcanic rocks (TAS, AFM), meteorites, soils, ceramics, bone preservation, water quality, REE patterns, stable isotopes, and more.

### 🤖 AI-Powered Workflows
Natural language queries and automated analysis suggestions through integrated AI assistants. Ask questions about your data in plain English.

### 📈 Publication-Ready Outputs
High-quality plots, ternary diagrams, spider diagrams, discrimination plots, contour maps, and statistical reports ready for journals.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager
- (Optional) Virtual environment tool (venv, conda)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sefy-levy/scientific-toolkit.git
cd scientific-toolkit
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the toolkit**
```bash
python Scientific-Toolkit.py
```

### First Launch
On first launch, the toolkit will:
- Initialize the configuration files
- Load available plugins
- Create sample data directories
- Display the splash screen and main interface

---

## 📚 Documentation

### Core Guides
- [**Installation Guide**](docs/INSTALLATION.md) - Detailed setup instructions for all platforms
- [**User Manual**](docs/USER_GUIDE.md) - Comprehensive guide to all features
- [**Plugin Development**](docs/PLUGIN_DEVELOPMENT.md) - Create your own plugins
- [**Troubleshooting**](docs/TROUBLESHOOTING.md) - Common issues and solutions

### Quick References
- [**Supported Instruments**](docs/INSTRUMENTS.md) - Full list of hardware integrations
- [**Classification Systems**](docs/CLASSIFICATIONS.md) - Description of all 37 classification schemes
- [**Data Formats**](docs/DATA_FORMATS.md) - Supported file formats and structures
- [**API Reference**](docs/API.md) - Programming interface documentation

### Video Tutorials
- [Getting Started (5 min)](docs/tutorials/getting-started.md)
- [XRF Data Processing (10 min)](docs/tutorials/xrf-processing.md)
- [Creating Custom Classifications (15 min)](docs/tutorials/custom-classifications.md)

---

## 🔧 Usage Examples

### Load and Analyze Data
```python
# Import your data
df = toolkit.load_data("my_samples.csv")

# Auto-detect and standardize column names
df = toolkit.standardize_columns(df)

# Apply classification
results = toolkit.classify("TAS_diagram", df)

# Generate publication plot
toolkit.plot_tas(df, save_path="tas_plot.png", dpi=300)
```

### Hardware Integration
```python
# Connect to benchtop XRF
xrf = toolkit.connect_instrument("Bruker_XRF")

# Acquire spectrum
spectrum = xrf.acquire(integration_time=30)

# Apply drift correction
corrected = toolkit.apply_drift_correction(spectrum)
```

### AI-Assisted Analysis
```python
# Ask questions about your data
ai = toolkit.get_ai_assistant("Claude")
response = ai.query("What's the most likely source region for these basalts?")

# Get analysis suggestions
suggestions = ai.suggest_analyses(df)
```

---

## 🗂️ Project Structure

```
scientific-toolkit/
│
├── Scientific-Toolkit.py          # Main entry point
├── data_hub.py                    # Central data management
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── LICENSE                        # CC BY-NC-SA 4.0
│
├── config/                        # Configuration files
│   ├── chemical_elements.json     # Element name variations
│   ├── enabled_plugins.json       # Active plugin list
│   └── scatter_colors.json        # Default plot colors
│
├── engines/                       # Classification & protocol engines
│   ├── classification_engine.py   # Core classification logic
│   ├── protocol_engine.py         # Workflow automation
│   ├── classification/            # 37 classification systems
│   └── protocols/                 # Standard protocols
│
├── plugins/                       # Modular plugin system
│   ├── hardware/                  # Instrument integration (7 suites)
│   ├── software/                  # Analysis tools (37 plugins)
│   ├── add-ons/                   # Extended features (17 plugins)
│   └── other/                     # Specialized tools (19 plugins)
│
├── ui/                            # User interface components
│   ├── left_panel.py              # Data browser
│   ├── center_panel.py            # Main workspace
│   ├── right_panel.py             # Controls & settings
│   └── results_dialog.py          # Results display
│
├── samples/                       # Example datasets
│   ├── master_test_list.csv       # Sample geochemical data
│   └── classifications_master_test.csv
│
└── docs/                          # Documentation
    ├── USER_GUIDE.md              # User manual
    ├── INSTALLATION.md            # Setup guide
    ├── PLUGIN_DEVELOPMENT.md      # Developer docs
    └── tutorials/                 # Video tutorials
```

---

## 🔌 Plugin Ecosystem

### Hardware Plugins (26 total)

**Unified Suites** (7):
- Elemental Geochemistry (XRF, ICP-MS, LA-ICP-MS)
- Mineralogy (XRD, modal analysis)
- Physical Properties (dimensions, density, magnetic susceptibility)
- Solution Chemistry (pH, EC, TDS, ions)
- Spectroscopy (FTIR, Raman, UV-Vis)
- Zooarchaeology (bone measurements, species ID)

**Specialized Instruments** (19):
- Benchtop XRF (Bruker, Thermo, Vanta)
- Portable XRF (Niton, Bruker Tracer)
- FTIR Spectrometers (Bruker, PerkinElmer, Thermo)
- Digital Calipers
- GPS (NMEA)
- EC/pH/Ion Meters
- Magnetic Susceptibility Meter
- Laser Granulometer
- Raman Spectrometer
- XRD Powder Diffraction

### Software Plugins (37)

**Data Processing**:
- Advanced Export, Filter, Normalization
- Data Validation & Quality Control
- Compositional Statistics

**Visualization**:
- Ternary Diagrams
- Spider Diagrams
- Discrimination Plots
- Interactive Contouring
- Publication Layouts

**Statistical Analysis**:
- PCA Explorer (comprehensive)
- Machine Learning
- Advanced Statistics
- Uncertainty Propagation

**Geospatial**:
- GIS 3D Viewer
- Google Earth Integration
- Spatial Kriging
- Quartz GIS Pro

**Domain-Specific**:
- Petro Plot Pro
- Magma Modeling
- LA-ICP-MS Pro
- Isotope Mixing Models
- Zooarchaeology Analytics
- Lithic Morphometrics
- Virtual Microscopy

### Add-on Plugins (17)

**Visualization Libraries**:
- Matplotlib Plotter
- Seaborn Plotter
- Ternary Plotter
- ASCII Plotter
- GeoPandas Plotter
- Missingno Plotter
- NetworkX Plotter
- Pillow Plotter

**AI Assistants**:
- ChatGPT AI
- Claude AI
- Copilot AI
- DeepSeek AI
- Gemini AI
- Grok AI
- Ollama AI (local models)

**Utilities**:
- Batch Processor
- Demo Data Generator

---

## 🛠️ Configuration

### Enabling/Disabling Plugins
Edit `config/enabled_plugins.json`:
```json
{
  "hardware": ["elemental_geochemistry_unified_suite"],
  "software": ["pca_explorer", "machine_learning"],
  "add-ons": ["claude_ai", "matplotlib_plotter"]
}
```

### Custom Element Mapping
Add your lab's naming conventions to `config/chemical_elements.json`:
```json
{
  "Zr": {
    "standard": "Zr_ppm",
    "variations": ["Zr", "Zirconium", "Zr (ppm)", "Zr_conc"]
  }
}
```

### AI Assistant Setup
Store API keys as environment variables:
```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"
```

Or configure in the GUI: **Settings → AI Assistants → Configure Keys**

---

## 📊 Supported Data Formats

### Input Formats
- **CSV** (comma, tab, semicolon delimited)
- **Excel** (.xlsx, .xls)
- **JSON** (structured data)
- **Instrument-specific**: PDZ (Bruker), Vanta XML, Niton CSV, FTIR SPA

### Output Formats
- CSV, Excel, JSON (data)
- PNG, SVG, PDF (plots)
- KML (Google Earth)
- Shapefile (GIS)
- LaTeX tables (publications)

---

## 🤝 Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Ways to Contribute
- 🐛 Report bugs or request features (Issues)
- 📝 Improve documentation
- 🔌 Create new plugins for instruments or analyses
- 🧪 Test with your own data and provide feedback
- 🌍 Add internationalization support
- 🎨 Improve UI/UX design

---

## 📖 Citation

If you use Scientific Toolkit in your research, please cite:

```bibtex
@software{levy2026scientific,
  author = {Levy, Sefy},
  title = {Scientific Toolkit v2.0},
  year = {2026},
  note = {Based on Basalt Provenance Triage Toolkit v10.2},
  url = {https://github.com/sefy-levy/scientific-toolkit},
  doi = {10.5281/zenodo.18499129}
}
```

**APA Format**:
Levy, S. (2026). *Scientific Toolkit v2.0* [Computer software]. Based on Basalt Provenance Triage Toolkit v10.2. https://doi.org/10.5281/zenodo.18499129

### Citing Specific Classification Systems

If you use specific classification systems (TAS, AFM, etc.), **please also cite the original scientific papers**. See [REFERENCES.md](REFERENCES.md) for a complete list of citations for all 37 classification systems implemented in this toolkit.

**Example**:
> "Samples were classified using the TAS diagram (Le Bas et al., 1986) as implemented in Scientific Toolkit v2.0 (Levy, 2026)."

---

## 📜 License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**.

**You are free to**:
- ✅ Share — copy and redistribute the material
- ✅ Adapt — remix, transform, and build upon the material

**Under the following terms**:
- 📝 Attribution — You must give appropriate credit
- 🚫 NonCommercial — Not for commercial use
- 🔄 ShareAlike — Distribute derivatives under the same license

See [LICENSE](LICENSE) for full details.

For commercial licensing inquiries, contact: sefy76@gmail.com

---

## 🙏 Acknowledgments

**Development**: Sefy Levy (2026)

**Implementation with generous help from**:
Gemini • Copilot • ChatGPT • Claude • DeepSeek • Mistral • Grok

**Dedicated to**:
- My beloved **Camila Portes Salles** ❤️
- Special thanks to my sister **Or Levy**
- In loving memory of my mother **Chaya Levy**

**Special Thanks**:
- The open-source scientific community
- Contributors to NumPy, Pandas, Matplotlib, and SciPy
- Beta testers and early adopters
- Everyone who provides feedback and suggestions

---

## 💬 Support & Contact

### Get Help
- 📚 Read the [User Guide](docs/USER_GUIDE.md)
- ❓ Check [Troubleshooting](docs/TROUBLESHOOTING.md)
- 🐛 Report bugs via [GitHub Issues](https://github.com/sefy-levy/scientific-toolkit/issues)
- 💬 Join discussions on [GitHub Discussions](https://github.com/sefy-levy/scientific-toolkit/discussions)

### Contact
- **Email**: sefy76@gmail.com
- **GitHub**: [@sefy-levy](https://github.com/sefy-levy)

### Support Development
If this toolkit has helped your research:

- ⭐ Star this repository
- 🐛 Report issues or suggest features
- 🤝 Contribute code or documentation
- ☕ [Buy me a coffee](https://ko-fi.com/sefy76)
- 💝 [PayPal](https://paypal.me/sefy76)
- 💚 [Liberapay](https://liberapay.com/sefy76)

---

## 🗺️ Roadmap

### v2.1 (Q2 2026)
- [ ] Web interface (Flask/Django)
- [ ] Database backend (SQLite/PostgreSQL)
- [ ] Real-time collaborative features
- [ ] Mobile companion app

### v2.2 (Q3 2026)
- [ ] Cloud deployment option
- [ ] Automated report generation
- [ ] Integration with more AI models
- [ ] Enhanced GIS capabilities

### Future
- [ ] R integration
- [ ] MATLAB bridge
- [ ] Jupyter notebook support
- [ ] REST API

See [ROADMAP.md](ROADMAP.md) for detailed plans.

---

## ⚠️ Disclaimer

This software is provided "as is" without warranty. While extensively tested, users should validate results for their specific applications. Not certified for regulatory compliance.

---

## 📈 Project Stats

![GitHub stars](https://img.shields.io/github/stars/sefy-levy/scientific-toolkit?style=social)
![GitHub forks](https://img.shields.io/github/forks/sefy-levy/scientific-toolkit?style=social)
![GitHub issues](https://img.shields.io/github/issues/sefy-levy/scientific-toolkit)
![GitHub pull requests](https://img.shields.io/github/issues-pr/sefy-levy/scientific-toolkit)

**Lines of Code**: 65,098  
**Files**: 135  
**Classes**: 204  
**Functions**: 1,875  
**Plugins**: 80+  
**Classification Systems**: 37

---

<div align="center">

**Made with ❤️ for the scientific community**

[⬆ Back to Top](#-scientific-toolkit-v20)

</div>
