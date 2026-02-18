# 🔬 Scientific Toolkit v2.0

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://gitlab.com/sefy76/scientific-toolkit)
[![GitLab](https://img.shields.io/badge/GitLab-Repository-orange.svg)](https://gitlab.com/sefy76/scientific-toolkit)

> **Free integrated platform for multi-domain scientific analysis**

Scientific Toolkit combines geochemistry, archaeology, spectroscopy, GIS, statistical analysis, and hardware integration in one free tool. Built for researchers, students, and institutions with limited software budgets.

Based on Basalt Provenance Triage Toolkit v10.2, expanded to cover multiple scientific disciplines.

---

## 🎯 What Is This?

**Scientific Toolkit** is a Python/Tkinter desktop application that integrates tools for:
- Geochemical data analysis and classification
- Archaeological material analysis
- Hardware instrument integration (XRF, FTIR, XRD, GPS, etc.)
- Statistical analysis and machine learning
- GIS visualization and spatial analysis
- Publication-ready figure generation

**Key features:**
- 41 classification engines implementing published methods
- 26 hardware device integrations
- Multiple plotting and visualization options
- Import/export for common data formats
- Template system for journal-specific figures
- Completely free and open source

**Who might find this useful:**
- Students learning geochemistry or archaeology
- Researchers with limited software budgets
- Teaching labs needing multi-topic coverage
- Field scientists needing portable instrument integration
- Museums managing collections and analysis data
- Anyone working across geology and archaeology

**What this is NOT:**
- Not a replacement for specialized commercial tools in single domains
- Not optimized for massive datasets (10,000+ samples)
- Not a web application (desktop only)
- Not a programming language (GUI-based)

---

## 📊 What's Included?

### Classification Engines (41)

Implementations of published classification methods across multiple fields:

**Geochemistry:** TAS volcanic classification (Le Bas et al. 1986), AFM diagrams (Irvine & Baragar 1971), REE patterns (Sun & McDonough 1989), Chemical Index of Alteration, mantle array discrimination, normative calculations

**Archaeology:** Bone collagen QC, bone diagenesis (Ca/P ratios), ceramic firing temperature proxies, glass composition, stable isotope dietary reconstruction

**Environmental:** Geoaccumulation index (Müller 1969, 1981), enrichment factors, soil texture (USDA), soil salinity/sodicity, water hardness

**Sedimentology:** Grain size (Wentworth 1922), Dunham carbonate classification

**Meteoritics:** Chondrite classification, shock stages (Stöffler et al. 1991), weathering grades

See [CITATIONS.md](CITATIONS.md) for complete references.

### Hardware Integrations (26)

Plugins for connecting scientific instruments:
- XRF/pXRF analyzers (Bruker Tracer, Niton, Vanta, benchtop XRF)
- FTIR spectrometers (Bruker, PerkinElmer, Thermo)
- XRD powder diffraction
- ICP-MS data import
- Raman spectrometers
- GPS/GNSS devices (NMEA protocol)
- Digital calipers (USB HID)
- EC meters, ion-selective electrodes
- Magnetic susceptibility meters
- Laser granulometers
- Universal file monitor (works with any device that saves files)

### Software Plugins (28)

Advanced analysis tools:
- LA-ICP-MS data reduction and U-Pb dating
- PCA/LDA/ML Explorer (Random Forest, SVM, t-SNE, clustering)
- Compositional statistics (pyrolite integration)
- Spatial kriging and interpolation
- 3D GIS viewer with terrain
- Google Earth Pro export
- Magma modeling (fractional crystallization, AFC)
- Isotope mixing models
- Literature comparison (published reference matching)
- Advanced normalization schemes
- Publication layout tools

### Visualization Options

- Matplotlib (standard plots)
- Seaborn (statistical visualization)
- Ternary diagrams (three-component)
- GeoP

---

## 💡 Who Is This For?

✅ **Graduate students** working across geology + archaeology  
✅ **University professors** teaching multi-topic courses  
✅ **Museum researchers** managing collections + analysis  
✅ **Field scientists** needing portable instrument integration  
✅ **Developing-world researchers** with limited software budgets  
✅ **Independent researchers** and citizen scientists  
✅ **Small institution labs** without commercial licenses  
✅ **Environmental consultants** needing flexible tools  
✅ **Anyone** who can't afford $8,000/year in software subscriptions  

---

## 📦 What's Included?

### **Core Components**
- **153 files** of production-ready code
- **77,000 lines** across Python, JSON, documentation
- **Modular plugin architecture** - enable only what you need
- **Observer pattern data hub** - all plugins stay synchronized
- **Comprehensive error handling** - professional UX

### **Plugin Categories**

**🔧 Hardware Plugins (26)**
- Unified suites for geochemistry, mineralogy, spectroscopy, zooarchaeology
- Single-device controllers for XRF, FTIR, XRD, GPS, etc.
- Universal file monitor fallback

**💻 Software Plugins (28)**
- Advanced normalization, CIPW norms, isotope mixing
- LA-ICP-MS Pro, geochronology, magma modeling
- PCA/LDA/ML Explorer, kriging, 3D GIS
- Literature comparison, publication layouts

**🎨 Add-on Plugins (17)**
- Matplotlib, Seaborn, Ternary plotters
- ASCII art plots, batch processing
- 6 AI assistants (Claude, ChatGPT, Gemini, DeepSeek, Grok, Ollama)

**🧬 Classification Engines (41)**
- Geochemistry: TAS, AFM, REE, mantle arrays
- Archaeology: bone QC, ceramics, glass, lithics
- Environmental: Igeo, enrichment factors, soil texture
- Meteoritics: chondrites, shock stages, weathering
- Each engine includes citations to source literature

**🎨 Templates (8 categories)**
- Journal styles: Nature, Science, AGU, Elsevier, GSA
- Aesthetic: Color-blind safe, high contrast, B&W print
- Functional: Publication-ready, reviewer-friendly
- Discipline-specific: REE spider, TAS, stable isotopes

---

## 🎓 Academic Use

### **Citation**
If you use Scientific Toolkit in research, please cite:
```
Scientific Toolkit v2.0 (2024-2026)
Free integrated platform for multi-domain scientific analysis
https://gitlab.com/sefy76/scientific-toolkit
License: CC BY-NC-SA 4.0
```

### **Validation**
Classification engines implement published methods with citations:
- Sun & McDonough (1989) - REE normalization
- Le Bas et al. (1986) - TAS classification
- Irvine & Baragar (1971) - AFM diagrams
- Pearce (2008) - Mantle array discrimination
- Stöffler et al. (1991) - Meteorite shock stages
- *[40+ additional references in classification files]*

### **Teaching**
Free for educational use. Example datasets included in `/samples/`

---

## 🛠️ Installation

### **Requirements**
- Python 3.8 or higher
- Operating System: Windows, macOS, or Linux
- Disk space: ~50 MB
- RAM: 2 GB minimum, 4 GB recommended

### **Core Dependencies**
```bash
pip install numpy pandas matplotlib tkinter
```

### **Optional Dependencies**
```bash
# For full functionality
pip install scipy scikit-learn seaborn pillow geopandas rasterio
```

See [detailed installation guide](docs/INSTALLATION.md) for platform-specific instructions.

---

## 📚 Documentation

- **[Installation Guide](INSTALLATION.md)** - Platform-specific setup
- **[Quick Start](QUICK_START.md)** - Get running in 5 minutes
- **[Citations](CITATIONS.md)** - All published methods and references
- **[Plugin Guide](PLUGIN_GUIDE.md)** - How to use plugins
- **[FAQ](FAQ.md)** - Common questions

---

## 🤝 Contributing

Contributions welcome! Ways to help:
- Report bugs via GitLab Issues
- Add new classification engines
- Create hardware plugins for new instruments
- Improve documentation
- Share example workflows

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📊 How This Compares to Other Tools

**GCDkit** (Free, R-based): Focused on igneous petrology and geochemistry. Scientific Toolkit adds archaeology, hardware integration, and GUI accessibility.

**ioGAS** (Commercial, ~$2,000+/year estimated): Professional geochemistry tool for mining industry. More polished UI, but Scientific Toolkit is free and covers archaeology/museums.

**Python/R scripts** (Free): Maximum flexibility, requires programming. Scientific Toolkit provides GUI for non-programmers.

**Commercial archaeology tools** (Varied pricing): Specialized but expensive. Scientific Toolkit integrates multiple capabilities in one free package.

**This toolkit is best for:** Students, teaching labs, budget-constrained researchers, museums, cross-disciplinary projects, field work with portable instruments.

**This toolkit is NOT for:** Large-scale industrial mining operations, users needing enterprise support contracts, datasets exceeding 10,000+ samples.

---

## 🗺️ Current Status & Roadmap

**Current Version: 2.0** (February 2026)

**Stable features:**
- 41 classification engines
- 26 hardware integrations
- Basic statistical analysis
- Publication templates
- Data import/export

**Known limitations:**
- Tkinter UI may look dated on modern systems
- Large datasets (>10,000 samples) may be slow
- No automated testing suite yet
- Documentation could use more examples

**Future plans:**
- Video tutorials
- More classification engines
- Performance optimization for large datasets
- Possible web interface option
- Peer-reviewed methods publication

---

## 📜 License & Disclaimer

**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International**

✅ **Free to use** - research, education, museums, companies, anyone  
✅ **Modify and improve** - adapt to your needs  
✅ **Share with attribution** - credit the original work  
❌ **Cannot sell this software** - don't charge money for the toolkit itself  
❌ **Cannot profit from the code** - don't incorporate it into commercial products you sell  
🔄 **Derivatives must use same license** - keep it free

**In plain English:** Use it freely for your work (even commercial work). Just don't sell the software itself or use the code in products you're selling.

### ⚠️ IMPORTANT DISCLAIMER

**This software is provided "AS IS" without warranty of any kind.**

- **You are responsible for validating all results** - Always verify classifications and calculations are appropriate for your samples
- **Check your data carefully** - Garbage in = garbage out
- **Don't trust blindly** - This is a tool to assist analysis, not replace expert judgment
- **Scientific responsibility is yours** - Verify methods are appropriate for your research
- **Report bugs and issues!** - Help improve the software by testing and reporting problems

**Found a bug? Results don't look right?** → [Report it on GitLab](https://gitlab.com/sefy76/scientific-toolkit/-/issues)

We need users to test thoroughly and report issues. Your feedback makes this better for everyone.

See [LICENSE](LICENSE) for legal details.

---

## 📞 Contact & Support

- **GitLab Issues**: [Report bugs or request features](https://gitlab.com/sefy76/scientific-toolkit/-/issues)
- **Email**: sefy76@protonmail.com

**Need help?** Open an issue on GitLab with:
1. Your operating system
2. Python version
3. Error message or description
4. What you were trying to do

---

## 🙏 Acknowledgments

This toolkit implements published scientific methods developed by researchers worldwide. See [CITATIONS.md](CITATIONS.md) for complete references.

Built with: NumPy, Pandas, Matplotlib, Scikit-learn, and the entire open-source Python scientific computing ecosystem.

Based on Basalt Provenance Triage Toolkit v10.2, expanded for multi-domain use.

---

<p align="center">
  <b>Free software for science</b><br>
  <i>Because research shouldn't require expensive licenses</i>
</p>

<p align="center">
  <a href="QUICK_START.md">Get Started</a> •
  <a href="INSTALLATION.md">Install</a> •
  <a href="CITATIONS.md">Citations</a> •
  <a href="CONTRIBUTING.md">Contribute</a>
</p>
