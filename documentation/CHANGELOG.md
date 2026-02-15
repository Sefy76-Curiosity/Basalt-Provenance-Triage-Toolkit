# Changelog

All notable changes to Scientific Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Features in development

### Changed
- Improvements to existing features

### Fixed
- Bug fixes

---

## [2.0.0] - 2026-02-15

### 🎉 Major Release - Complete Rewrite

#### Added
- **80+ Plugin System**
  - 7 unified hardware suites (Geochemistry, Mineralogy, Physical Properties, etc.)
  - 37 software analysis plugins
  - 17 add-on plugins
  - 19 specialized instrument plugins
  
- **AI Integration** (7 providers)
  - ChatGPT (OpenAI)
  - Claude (Anthropic)
  - Gemini (Google)
  - Copilot (Microsoft)
  - DeepSeek
  - Grok (X.AI)
  - Ollama (local models)

- **37 Classification Systems**
  - Geochemistry: TAS, AFM, REE patterns, tectonic discrimination
  - Archaeology: Bone diagenesis, stable isotopes, lithic morphometrics
  - Material Science: Ceramic firing, glass composition, meteorite types
  - Environmental: Soil texture, water hardness, pollution indices

- **Advanced Analysis Tools**
  - PCA Explorer (comprehensive principal component analysis)
  - Machine Learning (clustering, classification, prediction)
  - GIS 3D Viewer with kriging interpolation
  - Google Earth integration with KML export
  - Virtual Microscopy for petrographic analysis
  - Magma Modeling for petrogenesis studies
  - Isotope Mixing Models for provenance
  - Zooarchaeology Analytics Suite

- **Visualization Features**
  - Ternary diagrams
  - Spider/radar diagrams
  - Interactive contouring
  - Publication-ready layouts
  - Multiple plot libraries (Matplotlib, Plotly, Seaborn)

- **Data Management**
  - Auto-detection of element names (100+ variations per element)
  - Column standardization engine
  - Data validation and quality control
  - Advanced filtering and subsetting
  - Calculated columns with formulas
  - Merge datasets by Sample_ID

- **Hardware Integration**
  - Real-time instrument acquisition
  - XRF drift correction algorithms
  - Serial/USB/Bluetooth communication
  - FTIR/Raman spectroscopy support
  - GPS integration (NMEA parsing)
  - Digital caliper auto-logging

- **Export Capabilities**
  - CSV, Excel, JSON
  - PNG, SVG, PDF (plots)
  - KML (Google Earth)
  - Shapefile (GIS)
  - LaTeX tables
  - Complete analysis reports

#### Changed
- Complete UI redesign with three-panel layout
- Improved performance for large datasets (tested with 10,000+ samples)
- Modernized codebase (Python 3.8+)
- Enhanced error handling and user feedback
- Splash screen with loading progress

#### Fixed
- All known bugs from v1.x series
- Memory leaks in long-running sessions
- Column name recognition issues
- Export format inconsistencies
- Plugin loading order issues

#### Technical
- 65,098 lines of code
- 204 classes
- 1,875 functions
- Full modular architecture
- JSON-based configuration
- Plugin hot-loading support

---

## [1.x] - Basalt Provenance Triage Toolkit Series

### [10.2] - 2025-12-XX
- Final version before major rewrite
- Focused on basalt provenance analysis
- Foundation for Scientific Toolkit v2.0

### [10.1] - 2025-11-XX
- Improved XRF data processing
- Added more discrimination diagrams

### [10.0] - 2025-10-XX
- Major feature additions
- Performance improvements

### [9.x] - 2025-XX-XX
- Earlier versions
- Iterative improvements

---

## Version History Legend

### Types of Changes
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

### Version Numbering
- **Major.Minor.Patch** (e.g., 2.1.0)
- **Major**: Incompatible API changes
- **Minor**: New features, backwards compatible
- **Patch**: Bug fixes, backwards compatible

---

## Upcoming Features (Roadmap)

### v2.1 (Target: Q2 2026)
- [ ] Web interface (Flask/Django)
- [ ] Database backend (SQLite/PostgreSQL)
- [ ] Real-time collaboration
- [ ] Mobile companion app
- [ ] Automated report generation
- [ ] Enhanced 3D visualization
- [ ] More AI model integrations
- [ ] REST API

### v2.2 (Target: Q3 2026)
- [ ] Cloud deployment option (AWS/Azure/GCP)
- [ ] Multi-user support with permissions
- [ ] Version control for datasets
- [ ] Advanced uncertainty propagation
- [ ] Bayesian statistical methods
- [ ] Time-series analysis tools
- [ ] Enhanced GIS capabilities

### v3.0 (Long-term)
- [ ] R integration for advanced statistics
- [ ] MATLAB bridge
- [ ] Jupyter notebook integration
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] GraphQL API
- [ ] Real-time streaming data support
- [ ] Blockchain for data provenance tracking (experimental)

---

## Contributors

**Lead Developer**: Sefy Levy (sefy76@gmail.com)

**With Thanks To**:
- Gemini (Google AI)
- Copilot (Microsoft)
- ChatGPT (OpenAI)
- Claude (Anthropic)
- DeepSeek
- Mistral AI
- Grok (X.AI)

**Beta Testers**: (Add names as contributions come in)
- [Your name here!]

**Issue Reporters**: (Add names)
- [Your name here!]

**Documentation**: (Add names)
- [Your name here!]

---

## Links
- [GitHub Repository](https://github.com/sefy-levy/scientific-toolkit)
- [Documentation](https://github.com/sefy-levy/scientific-toolkit/docs)
- [Issue Tracker](https://github.com/sefy-levy/scientific-toolkit/issues)
- [Discussions](https://github.com/sefy-levy/scientific-toolkit/discussions)
- [DOI: 10.5281/zenodo.18499129](https://doi.org/10.5281/zenodo.18499129)

---

## Support

If you find this project useful, consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 📝 Improving documentation
- 💝 [Supporting development](https://ko-fi.com/sefy76)

---

*Last Updated: 2026-02-15*
