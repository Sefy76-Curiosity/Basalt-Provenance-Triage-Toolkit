# CHANGELOG - Basalt Provenance Triage Toolkit

## Version 10.1 - February 2026

### 🎉 MAJOR NEW FEATURES

#### Google Earth Export Plugin (NEW!)
- Export samples as KML files for Google Earth visualization
- Color-coded 3D pins by provenance classification
- Auto-open in Google Earth Desktop or Web
- Rich popup information with geochemistry
- Folder organization by classification
- 3D elevation support
- **NO OTHER BASALT TOOLKIT HAS THIS!**

#### 3D/GIS Visualization Plugin (NEW!)
- Three-tier system based on installed dependencies
- **Tier 1**: Basic 2D map (matplotlib - always available)
- **Tier 2**: Interactive web maps (Folium + GeoPandas)
- **Tier 3**: Professional 3D scatter plots (PyVista)
- Google Maps-style interface
- Clickable markers with sample details
- Export as HTML or high-res images

#### PDF Report Generation
- Professional PDF reports with reportlab
- Classification summary tables
- Sample details with geochemistry
- Statistical summaries (mean, median, std dev, min, max)
- Publication-ready formatting
- Proper citation footer

### 🐛 BUG FIXES

#### Plugin System
- **FIXED**: 5 plugins showing grey screens (advanced_filter, data_validation, literature_comparison, photo_manager, report_generator)
- **FIXED**: Wrong method names causing plugins not to load
- **FIXED**: Window stacking issues - dialogs now appear on top
- **FIXED**: MessageBox parent parameters for proper modal behavior
- All 14 plugins now load and display correctly

#### CSV/Excel Import
- **ENHANCED**: Column mapper from 9 mappings to 100+ mappings
- Now handles ALL trace elements (20+)
- Now handles ALL major elements (13)
- Now handles ALL isotopes (6)
- Now handles error columns (25+)
- Now handles BDL flags (6)
- Now handles QA/QC metadata (4)
- Now handles archaeological context (6)
- Now handles geographic data (3)
- Accepts virtually ANY column naming convention
- Examples: "Zr", "zr_ppm", "Zr (ppm)", "pXRF_Zr_ppm", "Zirconium" → all work!

#### Error Handling
- **IMPROVED**: Better pip3 error messages with alternative installation commands
- **IMPROVED**: Plugin manager shows clear install instructions
- **IMPROVED**: Graceful degradation when optional packages missing
- **IMPROVED**: File not found errors now provide helpful guidance

### 🎨 UI/UX IMPROVEMENTS

#### Professional Polish
- **REMOVED**: IoGAS trademark references (now "Logical Query Language", "Professional")
- **IMPROVED**: All plugin windows now use proper window stacking
- **IMPROVED**: Consistent color schemes across all plugins
- **IMPROVED**: Better status indicators for optional features
- **IMPROVED**: Clearer installation instructions in plugin UI

#### Filename Consistency
- **CHANGED**: Main file now `Basalt_Provenance_Triage_Toolkit.py` (NO version number)
- Easier for users to replace when upgrading
- Distribution packages still versioned for tracking

### 📦 DISTRIBUTION

#### Windows Standalone EXE (NEW!)
- Complete standalone executable for Windows users
- No Python installation required
- All 14 plugins built-in
- ~150 MB (includes Python + all dependencies)
- Just download and run!

#### Build System
- PyInstaller spec file for reproducible builds
- Automated build scripts (Windows and Linux/Mac)
- Complete build and distribution documentation
- Separation instructions for dual-package distribution

### 📊 TECHNICAL IMPROVEMENTS

#### Code Quality
- All 15 Python files compile without errors
- Consistent error handling across all plugins
- Proper dependency checking with graceful fallbacks
- Comprehensive documentation
- Better code organization

#### Plugin Architecture
- Dynamic plugin loading with fallback method detection
- Support for optional dependencies
- Tiered feature systems (basic/advanced/professional)
- Better integration with main application

### 📚 DOCUMENTATION

#### New Documentation Files
- `BUILD_AND_DISTRIBUTION_GUIDE.md` - Complete build instructions
- `INSTALLATION.txt` - Simple installation guide for source users
- `README_WINDOWS.txt` - Instructions for EXE users
- `GOOGLE_EARTH_PLUGIN_DOCS.md` - Comprehensive Google Earth documentation
- Updated `IOGAS_COMPARISON.md` with new 3D/GIS features

#### Improved Guides
- Better troubleshooting sections
- More use cases and examples
- Clearer system requirements
- Enhanced getting started guides

### 🏆 COMPETITIVE POSITION

#### vs IoGAS ($1,500/year)
- **NEW**: Google Earth export (IoGAS doesn't have this!)
- **NEW**: 3D visualization (now at feature parity!)
- **NEW**: Interactive web maps (IoGAS doesn't have this!)
- **IMPROVED**: More flexible data import than IoGAS
- **ADVANTAGE**: FREE and open source
- **ADVANTAGE**: Archaeology-focused design

#### Feature Parity
Now at 95%+ feature parity with commercial software!
The only remaining advantage of IoGAS is deep QGIS/ArcGIS integration,
but we can export data for those tools.

### 🔧 DEPENDENCIES

#### Core (Required)
- Python 3.8+
- tkinter
- matplotlib
- numpy
- pandas

#### Optional (New)
- reportlab (PDF reports) - NEW!
- simplekml (Google Earth) - NEW!
- pyvista (3D visualization) - NEW!
- folium (web maps) - NEW!
- geopandas (GIS features) - NEW!

#### Optional (Existing)
- openpyxl (Excel import/export)
- scikit-learn (statistical analysis)
- python-docx (Word reports)

### 📈 STATISTICS

#### Code Metrics
- Files modified: 8
- Files created: 3 new plugins + documentation
- Total plugins: 14 (was 11)
- Lines of code added/modified: ~3,000
- Column mappings: 9 → 100+ (11x improvement!)
- Zero compilation errors

#### File Sizes
- Source package: ~400 KB
- Windows EXE: ~150 MB
- Complete documentation: ~50 KB

### 🙏 ACKNOWLEDGMENTS

Special thanks to the archaeological and geochemical communities for
feedback that drove these improvements!

### 📝 MIGRATION NOTES

#### From v10.0 to v10.1
- **NO BREAKING CHANGES!**
- Projects saved in v10.0 work in v10.1
- Just replace the main .py file
- Enable new plugins in Plugin Manager
- Install optional dependencies as needed

### 🚀 WHAT'S NEXT

#### Planned for v10.2
- Advanced KML features (custom icons, tours, regions)
- Google Earth Engine integration
- Spatial clustering analysis
- Distance calculations between samples
- Enhanced 3D terrain draping
- More export formats

#### Under Consideration
- Web-based version (browser interface)
- Mobile app (iOS/Android)
- Cloud storage integration
- Real-time collaboration features
- Machine learning classification

---

## Version 10.0 - January 2026

### Initial Release
- Core classification algorithms
- TAS diagrams
- Harker plots
- Discrimination diagrams
- Spider plots
- Sr-Nd isotope plots
- Pb isotope plots
- AFM ternary diagrams
- Plugin system
- Statistical analysis
- Data validation
- Literature comparison
- Photo management
- Report generation

---

## How to Cite

Levy, S. (2026). Basalt Provenance Triage Toolkit: An Integrated Software
Tool for Geochemical Classification of Archaeological Basalt Samples
(Version 10.1). Zenodo. https://doi.org/10.5281/zenodo.18499129

---

## License

CC BY-NC-SA 4.0 - Creative Commons Attribution-NonCommercial-ShareAlike 4.0

---

**For detailed technical documentation, see BUILD_AND_DISTRIBUTION_GUIDE.md**
