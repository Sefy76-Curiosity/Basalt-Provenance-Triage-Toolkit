# Scientific Toolkit v2.0

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit)
[![GitLab](https://img.shields.io/badge/GitLab-Repository-orange.svg)](https://gitlab.com/sefy76/scientific-toolkit)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black.svg)](https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit)

> **Free integrated platform for multi-domain scientific analysis**

Scientific Toolkit combines geochemistry, archaeology, spectroscopy, GIS, statistical
analysis, and hardware integration in one free tool. Built for researchers, students,
and institutions with limited software budgets.

Based on Basalt Provenance Triage Toolkit v10.2, expanded to cover multiple scientific
disciplines.

---

## What Is This?

Scientific Toolkit is a Python/ttkbootstrap desktop application that integrates tools for:

- Geochemical data analysis and classification
- Archaeological material analysis
- Hardware instrument integration (XRF, FTIR, XRD, GPS, calipers, balances)
- Statistical analysis and machine learning
- GIS visualization and spatial analysis
- Publication-ready figure generation
- Isotope mixing models with Bayesian MCMC inversion
- U-Pb geochronology and detrital provenance
- Normative mineral calculations (CIPW, Hutchison, Niggli, Rittmann)

**Key features:**

- 70 classification engines implementing published methods
- 10 scientific protocols for standardized multi-stage workflows
- 37 software plugins for advanced analysis
- **25 add-on plugins** including Toolkit AI (built-in, offline) and Statistical Console
- 16 hardware suites supporting dozens of device models
- **16 domain-specific Field Panels** with live embedded diagrams (auto-detected)
- **Toolkit AI v2.2** — built-in AI assistant, no API key, works 100% offline
- **Statistical Console** — plain-language stats for non-programmers (no scipy needed)
- **Macro Recorder** — records and replays 13 action types
- **Thread-safe Auto-Save** — atomic writes, crash recovery on startup
- **Project Save/Load** — complete workspace persistence (.stproj)
- Modern ttkbootstrap UI — consistent theming across all panels
- Import/export for all common data formats
- Template system for journal-specific figures (Nature, Science, AGU, Elsevier)
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

## Current State (March 2026)

### Core Statistics

| Metric | Count |
|---|---|
| Total files | 153+ |
| Lines of code | ~100,000+ |
| Classification engines | 70 |
| Scientific protocols | 10 |
| Software plugins | 37 |
| Add-on plugins | 25 |
| Hardware suites | 16 |
| Domain Field Panels | 16 |
| Macro action types | 13 |
| AI assistants | 8 (1 built-in offline + 7 external) |
| Built-in citations | 200+ |
| Sample test files | 30+ |
| UI framework | ttkbootstrap |

---

## Intelligence Features

### Toolkit AI v2.2 — Built-in, Offline, No API Key

A built-in AI assistant with deep knowledge of the entire toolkit. Unlike external AI
plugins (Claude, ChatGPT, Gemini), Toolkit AI understands the toolkit's own structure.

- Scans every plugin at startup using static AST analysis
- Knows every classification scheme, field panel, and hardware suite
- Recommends plugins based on your data type
- Can trigger one-click plugin installation
- Works 100% offline — no internet, no API key required
- Knowledge cache saved with 1-hour TTL (`config/ai_knowledge_cache.json`)

**Enable:** Advanced → Plugin Manager → Add-ons → Toolkit AI → Enable

### Field Panels v3.0 — 16 Domain-Specific Analysis Panels

The right panel automatically detects your data type and offers to switch to a
domain-specific analysis panel with live embedded diagrams.

| Domain | Auto-Detected Columns |
|---|---|
| Geochemistry | SiO2, TiO2, Al2O3, MgO, CaO, Na2O, K2O |
| Geochronology | U-Pb, Ar-Ar, radiometric fields |
| Petrology | Modal/normative mineralogy |
| Structural Geology | Strike, dip, plunge, azimuth |
| Geophysics | Seismic, gravity, magnetics, ERT |
| Spatial / GIS | Latitude, longitude, UTM |
| Archaeology | Lithic morphometrics, catalogue fields |
| Zooarchaeology | NISP, MNI, taxon, skeletal element |
| Spectroscopy | Wavelength/wavenumber vs intensity |
| Chromatography | Retention time, peak area, m/z |
| Electrochemistry | Potential, current, impedance |
| Materials Science | Stress, strain, hardness |
| Solution Chemistry | pH, conductivity, TDS, alkalinity |
| Molecular Biology | Ct, Cq, melt temperature, qPCR |
| Meteorology | Temperature, humidity, pressure, wind |
| Physics | Time-series, FFT, signal, voltage |

The **Geochemistry Panel** embeds live Matplotlib figures directly in the panel:
TAS diagram (Le Bas et al. 1986), AFM diagram, and Mg# histogram — all updated
instantly as you select rows in the main table.

### Statistical Console — Stats Without Coding

A plain-language statistics terminal running as its own tab in the center panel.

- One-click buttons: Summary, Describe, Correlate, Groups, T-Test
- Text command interface at the prompt for finer control
- No scipy required — uses Python's built-in statistics module
- Dark terminal-style interface with command history (up/down arrows)

**Enable:** Advanced → Plugin Manager → Add-ons → Statistical Console → Enable

---

## Classification Engines (70) & Protocols (10)

### Two Engine Architecture

| Engine | Purpose | Count |
|---|---|---|
| Classification Engine | Rule-based classification using JSON schemes | 70 schemes |
| Protocol Engine | Multi-stage workflows with conditional logic | 10 protocols |

### Classification Engine Schemes (70)

**Geochemistry (20+)**
- TAS Volcanic Classification (Le Bas et al. 1986)
- AFM Irvine-Baragar Series (Irvine & Baragar 1971)
- QAPF Mineralogical Classification (IUGS Le Maitre 2002)
- Winchester-Floyd Discrimination (Winchester & Floyd 1977)
- Pearce Zr/Y Tectonic (Pearce & Norry 1979)
- Jensen Cation Plot (Jensen 1976)
- REE Pattern Classification (Boynton 1984; Sun & McDonough 1989)
- REE Named Types (N-MORB, OIB, E-MORB, etc.)
- CI-Normalized Spider Diagram (Anders & Grevesse 1989)
- Pearce Mantle Array (Pearce 2008)
- Chemical Index of Alteration (Nesbitt & Young 1982)
- Normative Molar Proportions (Cross et al. 1902)
- Igneous Major-Oxide Indices
- Magma Rheology and Eruption Style
- Volcanic Series Discrimination
- K₂O–SiO₂ Volcanic Series
- Pearce Nb/Yb–Th/Yb Mantle Array
- And many more...

**Metamorphic Petrology (5+)**
- Metamorphic Facies (Winter 2014; Yardley 1989)
- Zircon Trace Element Thermometry (Watson & Harrison 2005)
- Thermobarometry calculations

**Sedimentology (12+)**
- Dunham Carbonate Classification (Dunham 1962)
- Dott Sandstone Classification (Dott 1964)
- Folk Carbonate Classification (Folk 1959, 1962)
- Pettijohn Sandstone Classification (Pettijohn 1975)
- Sediment Grain Size (Wentworth 1922)
- Sediment Texture and Maturity (Shepard 1954; Folk 1974)
- Munsell Color Classification
- USDA Soil Texture Classification
- Folk–Shepard Sediment Texture

**Geochronology (3+)**
- U-Pb Concordia QC (Wetherill 1956; Tera & Wasserburg 1972)
- Zircon trace element thermometry
- LA-ICP-MS signal processing

**Isotope Geochemistry (3+)**
- Isotope provenance and diet (Sr, O, Pb)
- Strontium mobility index (Montgomery 2010)
- Stable isotope diet (δ¹³C, δ¹⁵N)

**Environmental (8+)**
- Geoaccumulation Index (Müller 1969, 1981)
- Enrichment Factor Screening (Zoller et al. 1974)
- Environmental Pollution Indices (Hakanson 1980)
- Pollution Load Index
- Risk Assessment Code (RAC)
- Contamination Factor (CF)

**Soil Science (8+)**
- USDA Soil Texture Classification (full triangle)
- Soil Salinity Classification (EC)
- Soil Sodicity (SAR)
- FAO Soil Classification (pH & EC)
- Soil Chemical Properties

**Archaeology & Bioarchaeology (10+)**
- Bone Collagen QC (C:N) (DeNiro 1985; van Klinken 1999)
- Bone Diagenesis (Ca/P) (Hedges et al. 1995)
- FTIR Crystallinity Index (Weiner & Bar-Yosef 1990)
- Stable Isotope Diet (δ¹³C, δ¹⁵N) (Schoeninger et al. 1983)
- Bone Trophic Diet (Sr/Ca, Ba/Ca)
- Behrensmeyer Weathering Stages (1978)
- Shipman & Rose Burning Stages (1984)
- Ceramic Firing Temperature Proxies (Tite 2008)
- Glass Compositional Families (Sayre & Smith 1961)

**Meteoritics (6+)**
- Chondrite Meteorite Classification (Kallemeyn et al. 1989)
- Meteorite Shock Stage (Stöffler et al. 1991)
- Meteorite Weathering Grade (Wlotzka 1993)
- Planetary Analog Ratio Fe/Mn (Papike et al. 2003)

**Archaeometallurgy (5+)**
- Copper Alloy Classification (Pernicka 1999; Craddock 1978)
- Slag Basicity Index (Bachmann 1982)
- Iron Bloom Classification (Scott 1991; Buchwald 2005)

**Hydrogeochemistry (5+)**
- Piper Diagram Water Type (Piper 1944)
- Stiff Diagram Pattern (Stiff 1951)
- Water Hardness Classification

**Provenance & Tectonics (5+)**
- Provenance Fingerprinting (Hartung 2017; Shervais 1982)
- Tectonic Discrimination Diagrams (Pearce & Cann 1973)
- Regional Triage (Egyptian–Sinai–Levantine)
- Basalt provenance triage

**Alteration & Weathering (3+)**
- Alteration Indices (Ishikawa & CCPI) (Ishikawa et al. 1976)
- Chemical Index of Alteration (Nesbitt & Young 1982)

**Analytical QA/QC (4+)**
- Analytical Precision Filter (RSD) (Potts & West 2008)
- Analytical Quality Control (IUPAC 1997; ISO 17025)
- LOD/LOQ classification
- CRM deviation and drift monitoring

### Protocol Engine Workflows (10)

Multi-stage protocols for complex workflows:

- **Behrensmeyer Weathering Protocol** — Standardized bone weathering stages
- **EPA Sediment Quality Protocol** — TEL/PEL and ERL/ERM thresholds
- **Folk–Shepard Sediment Texture Protocol** — Grain-size classification with sorting
- **Hakanson Ecological Risk Protocol** — CF, Er, and RI thresholds
- **IUGS Igneous Protocol** — TAS + QAPF combined workflow
- **Maresha Zooarchaeology Protocol** — Multi-stage faunal analysis
- **Shipman & Rose Burning Protocol** — Bone burning stages
- **Stable Isotope Diet Protocol** — δ¹³C + δ¹⁵N interpretation
- **USDA Soil Morphology Protocol** — Horizons, texture, structure, color
- **Zooarchaeology Fragmentation Protocol** — Breakage patterns and freshness

---

## Hardware Integration (16 Suites)

Each hardware suite supports multiple device models:

**1. Archaeology & Archaeometry Suite**
Devices: UAV/GNSS systems, portable XRF, ground-penetrating radar
Protocols: GPS/NMEA, serial, file import

**2. Barcode/QR Scanner Suite**
Devices: Zebra, Honeywell, Datalogic, Socket, Inateck, Eyoyo (50+ models)
Protocols: USB HID, USB Serial, Bluetooth SPP, Bluetooth LE, Webcam

**3. Chromatography & Analytical Suite**
Devices: GC, HPLC, IC instruments from Agilent, Thermo, Waters, Shimadzu
Protocols: Serial, Ethernet, file import (.csv, .cdf, .raw)

**4. Clinical & Molecular Diagnostics Suite**
Devices: PCR, plate readers, sequencers, clinical analyzers
Protocols: Serial, file import, LIMS integration

**5. Electrochemistry Suite**
Devices: Potentiostats, galvanostats, impedance analyzers (Gamry, BioLogic, Metrohm)
Protocols: USB, Ethernet, proprietary file formats

**6. Elemental Geochemistry Suite**
Devices: SciAps X-550/X-505, Olympus Vanta/Delta, Bruker S1/Tracer, Thermo Niton, ICP-MS
Protocols: SciAps SDK, CSV parsing, PyVISA, serial communication

**7. Geophysics Suite**
Devices: Magnetometers, gravimeters, seismographs, GPR, resistivity meters
Protocols: SEG-Y, ASCII, serial, proprietary formats

**8. Materials Characterization Suite**
Devices: SEM/EDX, XRD, nanoindentation, hardness testers, dilatometers
Protocols: Serial, Ethernet, file import (EMSA, JADE, raw)

**9. Meteorology & Environmental Suite**
Devices: Weather stations, loggers, air quality monitors (Davis, Vaisala, Campbell)
Protocols: Serial, Modbus, SDI-12, NMEA, Ethernet

**10. Molecular Biology Suite**
Devices: Spectrophotometers, gel imagers, qPCR systems, fluorometers
Protocols: USB, serial, file import

**11. Physical Properties Suite**
Devices: AGICO Kappabridge, Bartington MS2/MS3, ZH Instruments, Mitutoyo Digimatic calipers, Sylvac Bluetooth calipers, Mahr MarCal, iGaging
Protocols: Serial, HID, Bluetooth LE, Mitutoyo SPC protocol (24-bit decoding)

**12. Physics Test & Measurement Suite**
Devices: Oscilloscopes, multimeters, power supplies, signal generators (Keysight, Tektronix, Rigol)
Protocols: USB (USBTMC), GPIB, VISA, serial

**13. Solution Chemistry Suite**
Devices: Mettler Toledo, Thermo Orion, Hanna, Horiba LAQUA, YSI ProDSS, Hach, WTW (45+ models)
Protocols: Serial, HID, Bluetooth

**14. Spectroscopy Suite**
Devices: Thermo Nicolet, PerkinElmer, Bruker ALPHA, Agilent handheld, B&W Tek Raman, Ocean Optics, Avantes (50+ models)
Protocols: Serial, Ethernet, file import, USB

**15. Thermal Analysis & Calorimetry Suite**
Devices: DSC, TGA, TMA, DMA instruments (Netzsch, TA Instruments, Mettler Toledo)
Protocols: Serial, Ethernet, proprietary file formats

**16. Zooarchaeology Suite**
Devices: Mitutoyo calipers, Sylvac Bluetooth, Ohaus/Sartorius/Mettler Toledo balances, Emlid Reach GNSS, Dino-Lite microscopes
Protocols: HID, Bluetooth, serial, NMEA 0183

---

## Software Plugins (37)

### Statistical Analysis (6)
- **Compositional Stats PRO** – CLR/ILR transforms, PCA with robust covariance
- **PCA+LDA Explorer Pro** – PCA, LDA, PLS-DA, Random Forest, SVM, t-SNE
- **Geochemical Explorer** – Multivariate analysis, statistical tests
- **Uncertainty Propagation** – Monte Carlo classification, confidence ellipses
- **Interactive Contouring** – KDE-based contouring, 2D histogram
- **Spatial Kriging** – Variogram analysis, interpolation

### Geochronology (4)
- **Geochronology Suite** – U-Pb concordia, Ar-Ar spectra, detrital KDE/MDS
- **Dating Integration** – Bayesian age-depth with MCMC, calibration curves
- **LA-ICP-MS Pro** – Signal processing, U-Pb dating, elemental quantification
- **U-Pb Concordia QC** – Discordance screening, common Pb correction

### Petrology (5)
- **Advanced Normative Calculations** – CIPW, Hutchison, Niggli, Mesonorm, Rittmann
- **Advanced Petrogenetic Models** – AFC (DePaolo 1981), zone refining
- **Magma Modeling** – Fractional crystallization, AFC, mixing
- **Thermobarometry Suite** – Pyroxene, feldspar, amphibole thermobarometry
- **Petrogenetic Suite** – Complete magma evolution models

### Isotope Geochemistry (4)
- **Isotope Mixing Models** – Binary/ternary mixing, Monte Carlo, Bayesian MCMC inversion
- **Literature Comparison** – Compare to published datasets
- **Advanced Normalization** – Lucas-Tooth & Compton for pXRF/ICP
- **Stable Isotope Diet** – δ¹³C, δ¹⁵N interpretation

### GIS & Mapping (3)
- **GIS 3D Viewer PRO** – 2D maps, 3D terrain, web maps, SRTM
- **Google Earth Pro** – 3D extrusion, time animation, photo integration
- **Quartz GIS Pro** – Point-in-polygon, viewshed, attribute tables

### Archaeology (5)
- **Lithic Morphometrics** – Elliptical Fourier analysis, edge damage
- **Zooarchaeology Analytics** – NISP/MNI, taphonomy, aging
- **Photo Manager** – Link sample photos, organize field photography
- **Report Generator** – Excavation reports, IAA submissions
- **Virtual Microscopy PRO** – Petrographic + 3D mesh analysis

### Data Processing (4)
- **Data Prep Pro** – Advanced data cleaning and transformation
- **Batch Processor** – Process multiple files in a directory
- **Script Exporter** – Export workflows as Python/R scripts
- **Museum Import** – Import from Europeana and museum APIs

### Discipline-Specific Analysis Suites (6)
- **Chromatography Analysis Suite** – GC/HPLC/IC data processing
- **Clinical Diagnostics Suite** – Clinical and diagnostic sample analysis
- **Electrochemistry Analysis Suite** – Electrochemical data analysis
- **Materials Science Analysis Suite** – Materials characterization analysis
- **Molecular Biology Suite** – Genomic and proteomic workflows
- **Spectroscopy Analysis Suite** – Multi-technique spectral data processing

---

## Add-on Plugins (25)

### Plotting & Visualization (9)
- **ASCII Plotter** – Text-based plots (no graphics)
- **Matplotlib Plotter** – High-quality scientific plots
- **Seaborn Plotter** – Statistical visualizations
- **Ternary Plotter** – Ternary diagrams
- **Pillow Plotter** – Basic PIL/Pillow plots
- **Missingno Plotter** – Missing data visualization
- **Geoplot Pro** – IUGS diagrams, AFC modeling
- **Geopandas Plotter** – Archaeological site mapping
- **Interactive Contouring** – Density estimation

### Interactive Consoles (6)
- **Python Console** – Interactive Python
- **R Console** – Run R code for statistics
- **Julia Console** – High-performance computing
- **SQL Console** – SQLite queries
- **GIS Console** – Spatial analysis with GeoPandas
- **File Console** – Safe file management

### AI Assistants (8)
- **Toolkit AI** *(built-in)* – No API key, works 100% offline, knows every plugin and scheme
- **Claude AI** (Anthropic) – Requires API key
- **ChatGPT AI** (OpenAI) – Requires API key
- **Gemini AI** (Google) – Requires API key
- **DeepSeek AI** – Requires API key
- **Grok AI** (xAI) – Requires API key
- **Copilot AI** – Requires API key
- **Ollama AI** – Free local AI (no API key, no internet)

### Utilities (2)
- **Statistical Console** – Plain-language stats for non-programmers (Summary, Describe, Correlate, Groups, T-Test — no scipy needed)
- **Batch Processor** – Process multiple files

---

## Productivity Features

### Macro/Workflow Recorder — 13 Action Types

Record any sequence of actions and replay them with one click.

| Action Type | Trigger |
|---|---|
| import_file | CSV/Excel import |
| add_row | Manual row addition |
| classify | Classification scheme run |
| scheme_changed | Scheme dropdown selection |
| run_protocol | Hardware protocol execution |
| sort_by | Column header click |
| tab_switched | Tab change in center notebook |
| generate_plot | Plot generation |
| apply_filter | Filter/search applied |
| delete_selected | Row deletion |
| update_row | DataHub row update |
| prev_page | Pagination — previous page |
| next_page | Pagination — next page |

### Auto-Save — Thread-Safe with Crash Recovery

- Two `threading.Lock` objects prevent race conditions between UI and background threads
- Atomic write pattern: writes to `recovery.tmp` then renames — never partially written
- Crash recovery prompt on startup if unsaved work is detected (< 24h old)
- Auto-saves every 5 minutes to `auto_save/recovery.stproj`

### Project Save/Load

Complete workspace persistence in `.stproj` (JSON) format:
- All sample data, column order, classification results
- Active filters, search terms, pagination position
- Selected classification scheme and active field panel
- Window size and position

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+N | New Project |
| Ctrl+O | Open Project |
| Ctrl+S | Save Project |
| Ctrl+I | Import Data |
| Ctrl+R | Start Recording |
| Ctrl+T | Stop Recording |
| Ctrl+M | Manage Macros |
| Ctrl+A | Select All |
| Ctrl+F | Focus Search |
| F1 | Keyboard Shortcuts Help |
| F5 | Refresh All Panels |

---

## Academic Citations

Scientific Toolkit implements 200+ published methods with complete citations in every plugin.
Every researcher whose method is implemented deserves full credit — the list below covers all 18 disciplines.

**Igneous Petrology**
- Le Bas, M.J., Le Maitre, R.W., Streckeisen, A., & Zanettin, B. (1986). A chemical classification of volcanic rocks based on the total alkali-silica diagram. *Journal of Petrology*, 27(3), 745–750.
- Irvine, T.N., & Baragar, W.R.A. (1971). A guide to the chemical classification of the common volcanic rocks. *Canadian Journal of Earth Sciences*, 8(5), 523–548.
- Le Maitre, R.W. (Ed.) (2002). *Igneous Rocks: A Classification and Glossary of Terms* (2nd ed.). Cambridge University Press. [IUGS QAPF]
- Winchester, J.A., & Floyd, P.A. (1977). Geochemical discrimination of different magma series and their differentiation products using immobile elements. *Chemical Geology*, 20, 325–343.
- Pearce, J.A., & Norry, M.J. (1979). Petrogenetic implications of Ti, Zr, Y, and Nb variations in volcanic rocks. *Contributions to Mineralogy and Petrology*, 69(1), 33–47.
- Pearce, J.A. (2008). Geochemical fingerprinting of oceanic basalts with applications to ophiolite classification. *Lithos*, 100(1–4), 14–48.
- Jensen, L.S. (1976). A new cation plot for classifying subalkalic volcanic rocks. Ontario Division of Mines Miscellaneous Paper 66.
- Boynton, W.V. (1984). Cosmochemistry of the rare earth elements: meteorite studies. In Henderson, P. (Ed.), *Rare Earth Element Geochemistry*, 63–114. Elsevier.
- Sun, S.S., & McDonough, W.F. (1989). Chemical and isotopic systematics of oceanic basalts. *Geological Society, London, Special Publications*, 42(1), 313–345.
- Anders, E., & Grevesse, N. (1989). Abundances of the elements: meteoritic and solar. *Geochimica et Cosmochimica Acta*, 53(1), 197–214.
- Nesbitt, H.W., & Young, G.M. (1982). Early Proterozoic climates and plate motions inferred from major element chemistry of lutites. *Nature*, 299, 715–717.
- Cross, W., Iddings, J.P., Pirsson, L.V., & Washington, H.S. (1902). A quantitative chemico-mineralogical classification and nomenclature of igneous rocks. *Journal of Geology*, 10(6), 555–690. [CIPW Norm]
- Shervais, J.W. (1982). Ti-V plots and the petrogenesis of modern and ophiolitic lavas. *Earth and Planetary Science Letters*, 59(1), 101–118.

**Thermobarometry**
- Brey, G.P., & Köhler, T. (1990). Geothermobarometry in four-phase lherzolites II. *Journal of Petrology*, 31(6), 1353–1378.
- Putirka, K.D. (2008). Thermometers and barometers for volcanic systems. *Reviews in Mineralogy and Geochemistry*, 69(1), 61–120.
- Leake, B.E., et al. (1997). Nomenclature of amphiboles. *European Journal of Mineralogy*, 9(3), 623–651.
- Ridolfi, F., & Renzulli, A. (2012). Calcic amphiboles in calc-alkaline and alkaline magmas. *Contributions to Mineralogy and Petrology*, 163(5), 877–895.

**Geochronology**
- Wetherill, G.W. (1956). Discordant uranium-lead ages, I. *Eos, Transactions American Geophysical Union*, 37(3), 320–326.
- Tera, F., & Wasserburg, G.J. (1972). U-Th-Pb systematics in three Apollo 14 basalts. *Earth and Planetary Science Letters*, 14(3), 281–304.
- Ludwig, K.R. (2003). *User's Manual for Isoplot 3.00*. Berkeley Geochronology Center.
- Jackson, S.E., Pearson, N.J., Griffin, W.L., & Belousova, E.A. (2004). The application of laser ablation-ICP-MS to in situ U-Pb zircon geochronology. *Chemical Geology*, 211(1–2), 47–69.

**Isotope Geochemistry**
- Faure, G. (1986). *Principles of Isotope Geology* (2nd ed.). Wiley.
- Foreman-Mackey, D., Hogg, D.W., Lang, D., & Goodman, J. (2013). emcee: The MCMC hammer. *Publications of the Astronomical Society of the Pacific*, 125(925), 306–312.
- Zindler, A., & Hart, S. (1986). Chemical geodynamics. *Annual Review of Earth and Planetary Sciences*, 14, 493–571.
- McDonough, W.F., & Sun, S.S. (1995). The composition of the Earth. *Chemical Geology*, 120(3–4), 223–253.

**Sedimentology**
- Dunham, R.J. (1962). Classification of carbonate rocks according to depositional texture. *AAPG Memoir 1*, 108–121.
- Dott, R.H. (1964). Wacke, graywacke and matrix. *Journal of Sedimentary Research*, 34(3), 625–632.
- Wentworth, C.K. (1922). A scale of grade and class terms for clastic sediments. *Journal of Geology*, 30(5), 377–392.
- Folk, R.L. (1974). *Petrology of Sedimentary Rocks*. Hemphill Publishing Company.

**Environmental Science**
- Müller, G. (1969). Index of geoaccumulation in sediments of the Rhine River. *GeoJournal*, 2(3), 108–118.
- Hakanson, L. (1980). An ecological risk index for aquatic pollution control. *Water Research*, 14(8), 975–1001.
- Tessier, A., Campbell, P.G.C., & Bisson, M. (1979). Sequential extraction procedure for the speciation of particulate trace metals. *Analytical Chemistry*, 51(7), 844–851.

**Soil Science**
- USDA Natural Resources Conservation Service (1999). *Soil Taxonomy* (2nd ed.). USDA Handbook 436.
- FAO (2006). *Guidelines for Soil Description* (4th ed.). Food and Agriculture Organization.

**Archaeology & Bioarchaeology**
- DeNiro, M.J. (1985). Postmortem preservation and alteration of in vivo bone collagen isotope ratios. *Nature*, 317, 806–809.
- Behrensmeyer, A.K. (1978). Taphonomic and ecologic information from bone weathering. *Paleobiology*, 4(2), 150–162.
- Weiner, S., & Bar-Yosef, O. (1990). States of preservation of bones from prehistoric sites in the Near East. *Journal of Archaeological Science*, 17(2), 187–196.
- Grayson, D.K. (1984). *Quantitative Zooarchaeology*. Academic Press.
- Lyman, R.L. (2008). *Quantitative Paleozoology*. Cambridge University Press.
- Kuhl, F.P., & Giardina, C.R. (1982). Elliptic Fourier features of a closed contour. *Computer Vision, Graphics and Image Processing*, 18(3), 236–258.

**Meteoritics**
- Kallemeyn, G.W., Rubin, A.E., Wang, D., & Wasson, J.T. (1989). Ordinary chondrites: bulk compositions, classification. *Geochimica et Cosmochimica Acta*, 53(11), 2747–2767.
- Stöffler, D., Keil, K., & Scott, E.R.D. (1991). Shock metamorphism of ordinary chondrites. *Geochimica et Cosmochimica Acta*, 55(12), 3845–3867.
- Papike, J.J., Karner, J.M., & Shearer, C.K. (2003). Determination of planetary basalt parentage. *American Mineralogist*, 88(2–3), 469–472.

**Archaeometallurgy**
- Pernicka, E. (1999). Trace element fingerprinting of ancient copper. In Young, S.M.M., et al. (Eds.), *Metals in Antiquity*, 163–171. BAR International.
- Craddock, P.T. (1978). The composition of the copper alloys used by the Greek, Etruscan and Roman civilizations. *Journal of Archaeological Science*, 5(1), 1–16.
- Bachmann, H.G. (1982). *The Identification of Slags from Archaeological Sites*. Institute of Archaeology Occasional Publication 6.

**Hydrogeochemistry**
- Piper, A.M. (1944). A graphic procedure in the geochemical interpretation of water-analyses. *Eos, Transactions American Geophysical Union*, 25(6), 914–928.
- Stiff, H.A. (1951). The interpretation of chemical water analysis by means of patterns. *Journal of Petroleum Technology*, 3(10), 15–17.

**Provenance & Geochemical Fingerprinting**
- Hartung, U. (2017). Egyptian basalt vessels in the southern Levant and Sinai during the 4th millennium BC. [Regional sourcing methodology]
- Philip, G., & Williams-Thorpe, O. (2001). A provenance study of basalt objects from Jordan. *Levant*, 33(1), 41–75.
- Weiner, N., Gadot, Y., & Goren, Y. (2021). New geochemical reference data for basalt provenance studies in the southern Levant. *Journal of Archaeological Science*, 127, 105308.
- Pearce, J.A., & Cann, J.R. (1973). Tectonic setting of basic volcanic rocks determined using trace element analyses. *Earth and Planetary Science Letters*, 19(2), 290–300.
- DePaolo, D.J. (1981). Trace element and isotopic effects of combined wallrock assimilation and fractional crystallization. *Earth and Planetary Science Letters*, 53(2), 189–202.

**Compositional Statistics & Spectroscopy**
- Aitchison, J. (1986). *The Statistical Analysis of Compositional Data*. Chapman and Hall.
- Egozcue, J.J., et al. (2003). Isometric logratio transformations for compositional data analysis. *Mathematical Geology*, 35(3), 279–300.
- Savitzky, A., & Golay, M.J.E. (1964). Smoothing and differentiation of data by simplified least squares procedures. *Analytical Chemistry*, 36(8), 1627–1639.

**Geophysics**
- Loke, M.H., & Barker, R.D. (1996). Rapid least-squares inversion of apparent resistivity pseudosections. *Geophysical Prospecting*, 44(1), 131–152.
- Conyers, L.B. (2013). *Ground-Penetrating Radar for Archaeology* (3rd ed.). AltaMira Press.

**Materials Science**
- Oliver, W.C., & Pharr, G.M. (1992). An improved technique for determining hardness and elastic modulus. *Journal of Materials Research*, 7(6), 1564–1583.
- Brunauer, S., Emmett, P.H., & Teller, E. (1938). Adsorption of gases in multimolecular layers. *Journal of the American Chemical Society*, 60(2), 309–319.

**Molecular Biology & Clinical Diagnostics**
- Livak, K.J., & Schmittgen, T.D. (2001). Analysis of relative gene expression data using real-time quantitative PCR. *Methods*, 25(4), 402–408.
- Pfaffl, M.W. (2001). A new mathematical model for relative quantification in real-time RT-PCR. *Nucleic Acids Research*, 29(9), e45.

**Chromatography & Analytical Chemistry**
- Foley, J.P., & Dorsey, J.G. (1984). Equations for calculation of chromatographic figures of merit. *Analytical Chemistry*, 56(14), 2462–2470.
- International Conference on Harmonisation (1994). Validation of Analytical Procedures. ICH Q2(R1).

**Electrochemistry**
- Bard, A.J., & Faulkner, L.R. (2001). *Electrochemical Methods: Fundamentals and Applications* (2nd ed.). Wiley.
- Orazem, M.E., & Tribollet, B. (2008). *Electrochemical Impedance Spectroscopy*. Wiley.

**Ceramic & Glass Analysis**
- Tite, M.S. (2008). Ceramic production, provenance and use — a review. *Archaeometry*, 50(2), 216–231.
- Sayre, E.V., & Smith, R.W. (1961). Compositional categories of ancient glass. *Science*, 133(3467), 1824–1826.

**Analytical QA/QC**
- Potts, P.J., & West, M. (Eds.) (2008). *Portable X-ray Fluorescence Spectrometry*. Royal Society of Chemistry.
- IUPAC (1997). *Compendium of Chemical Terminology* (2nd ed.) — "Gold Book". Blackwell Scientific.
- ISO 17025:2017. General requirements for the competence of testing and calibration laboratories.

**Statistical & Scientific Software**
- Harris, C.R., et al. (2020). Array programming with NumPy. *Nature*, 585(7825), 357–362.
- Virtanen, P., et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. *Nature Methods*, 17(3), 261–272.
- Pedregosa, F., et al. (2011). Scikit-learn: machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.

See [documentation/CITATIONS.md](documentation/CITATIONS.md) for the complete list with DOI links and implementation notes.

---

## Who Is This For?

- Graduate students working across geology + archaeology
- University professors teaching multi-topic courses
- Museum researchers managing collections + analysis
- Field scientists needing portable instrument integration
- Developing-world researchers with limited software budgets
- Independent researchers and citizen scientists
- Small institution labs without commercial licenses
- Environmental consultants needing flexible tools
- Anyone who can't afford $8,000/year in software subscriptions

---

## Installation

### Requirements

- Python 3.8 or higher (3.10+ recommended)
- Operating System: Windows 10/11, macOS 10.14+, or Linux
- Disk space: ~50 MB (core) + optional dependencies
- RAM: 2 GB minimum, 4 GB recommended

### Minimal Install (core features)

```bash
pip install numpy pandas matplotlib ttkbootstrap
```

### Full Installation (all features)

```bash
pip install -r requirements.txt
```

This installs ~40+ packages including scipy, scikit-learn, geopandas, pyserial,
bleak, hidapi, simplekml, folium, pyvisa, emcee, corner, joblib, reportlab, openpyxl.

> **Note:** `ttkbootstrap` is required for the UI. Install it separately if needed:
> `pip install ttkbootstrap`

### Launch

```bash
python Scientific-Toolkit.py
```

See [INSTALLATION.md](documentation/INSTALLATION.md) for platform-specific instructions
(Windows, macOS, Linux, Docker, Anaconda).

---

## Documentation

| Document | What It Covers |
|---|---|
| [QUICK_START.md](documentation/QUICK_START.md) | Get running in 5 minutes |
| [INSTALLATION.md](documentation/INSTALLATION.md) | Platform-specific setup |
| [ENHANCED_FEATURES_README.md](documentation/ENHANCED_FEATURES_README.md) | All 10 productivity & intelligence features |
| [FAQ.md](documentation/FAQ.md) | Common questions answered |
| [STRUCTURE_GUIDE.md](documentation/STRUCTURE_GUIDE.md) | Complete project structure |
| [CITATIONS.md](documentation/CITATIONS.md) | All 200+ published methods and references |
| [DELIVERY_SUMMARY.md](documentation/DELIVERY_SUMMARY.md) | Complete file inventory |

---

## Contributing

Contributions welcome! Ways to help:

- Report bugs via [GitLab Issues](https://gitlab.com/sefy76/scientific-toolkit/-/issues) or [GitHub Issues](https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit/issues)
- Add new classification engines (JSON files in `engines/classification/`)
- Create hardware plugins for new instruments
- Add new Field Panel domains (subclass `FieldPanelBase`)
- Improve documentation
- Share example workflows and sample data

See CONTRIBUTING.md for guidelines.

---

## How This Compares to Other Tools

| Tool | Cost | Strengths | Weaknesses |
|---|---|---|---|
| GCDkit | Free | Excellent igneous petrology (200+ functions) | R-based, no hardware, no archaeology |
| ioGAS | $2,000+/year | Professional, polished UI, mining focus | Expensive, no hardware, no archaeology |
| PAST | Free | Excellent statistics (400+ tests) | 1990s UI, no hardware, limited geochemistry |
| Python/R scripts | Free | Maximum flexibility | Requires programming |
| **Scientific Toolkit** | **Free** | **70 classifications, 10 protocols, 90+ plugins, 16 hardware suites, 16 Field Panels, Toolkit AI, ttkbootstrap UI** | Slower with large datasets |

**Best for:** Students, teaching labs, budget-constrained researchers, museums, cross-disciplinary projects, field work with portable instruments.

**Not for:** Large-scale industrial operations (>10,000 samples), users needing enterprise support.

---

## Current Status & Roadmap

**Current Version: 2.0 (March 2026)**

### Stable Features

- 70 classification engines (across 2 engines)
- 10 scientific protocols for standardized workflows
- 37 software plugins + 25 add-on plugins (90+ total)
- 16 hardware suites supporting dozens of devices
- 16 domain Field Panels with live embedded diagrams
- Toolkit AI v2.2 — built-in, offline, no API key
- Statistical Console — plain-language stats, no scipy
- Macro Recorder — 13 action types
- Thread-safe Auto-Save with crash recovery
- Project Save/Load (.stproj)
- ttkbootstrap UI — modern theming throughout
- Publication templates (Nature, Science, AGU, Elsevier)
- Data import/export (CSV, Excel, JSON, KML, Shapefile)
- 30+ domain sample test files

### Known Limitations

- Large datasets (>10,000 samples) may be slow
- Not all hardware tested on all platforms
- Manual in-table cell edits not yet replayed in macros (reserved for future release)

### Future Plans

- Video tutorials
- More classification engines
- Performance optimization for large datasets
- Peer-reviewed methods publication
- Community plugin repository

---

## IMPORTANT DISCLAIMER

This software is provided "AS IS" without warranty of any kind.

- **You are responsible for validating all results** — always verify classifications and calculations are appropriate for your samples
- **Check your data carefully** — garbage in = garbage out
- **Don't trust blindly** — this is a tool to assist analysis, not replace expert judgment
- **Scientific responsibility is yours** — verify methods are appropriate for your research
- **Report bugs and issues!** — help improve the software by testing and reporting problems

Found a bug? Results don't look right?
→ [Report it on GitLab](https://gitlab.com/sefy76/scientific-toolkit/-/issues)
→ [Report it on GitHub](https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit/issues)

We need users to test thoroughly and report issues. Your feedback makes this better for everyone.

---

## License

**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International**

- Free to use — research, education, museums, companies, anyone
- Modify and improve — adapt to your needs
- Share with attribution — credit the original work
- Cannot sell this software — don't charge money for the toolkit itself
- Cannot profit from the code — don't incorporate it into commercial products you sell
- Derivatives must use same license — keep it free

In plain English: Use it freely for your work (even commercial work). Just don't sell the software itself or use the code in products you're selling.

See LICENSE for legal details.

---

## Contact & Support

| Channel | Link |
|---|---|
| GitLab Issues | https://gitlab.com/sefy76/scientific-toolkit/-/issues |
| GitHub Issues | https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit/issues |
| GitLab Repository | https://gitlab.com/sefy76/scientific-toolkit |
| GitHub Repository | https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit |
| Email | sefy76@gmail.com |
| DOI | https://doi.org/10.5281/zenodo.18727756 |

When reporting an issue, please include:
- Your operating system
- Python version (`python --version`)
- ttkbootstrap version (`python -c "import ttkbootstrap; print(ttkbootstrap.__version__)"`)
- Full error message (copy-paste)
- What you were trying to do

---

## Acknowledgments

This toolkit implements published scientific methods developed by researchers worldwide.
See [CITATIONS.md](documentation/CITATIONS.md) for the complete list of 200+ references.

Built with: NumPy, Pandas, Matplotlib, ttkbootstrap, SciPy, Scikit-learn, Emcee,
PySerial, GeoPandas, and the entire open-source Python scientific computing ecosystem.

Hardware protocols based on manufacturer documentation from Mitutoyo, SciAps, Bruker,
Thermo, Mettler Toledo, and others.

Based on Basalt Provenance Triage Toolkit v10.2, expanded for multi-domain use.

---

<p align="center">
<b>Free software for science</b><br>
<i>Because research shouldn't require expensive licenses</i>
</p>

<p align="center">
<a href="documentation/QUICK_START.md">Get Started</a> •
<a href="documentation/INSTALLATION.md">Install</a> •
<a href="documentation/CITATIONS.md">Citations</a> •
<a href="https://gitlab.com/sefy76/scientific-toolkit/-/issues">GitLab Issues</a> •
<a href="https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit/issues">GitHub Issues</a>
</p>

---

## Quick Stats Summary

| Category | Count |
|---|---|
| Total Files | 153+ |
| Lines of Code | ~100,000+ |
| Classification Engines | 70 |
| Scientific Protocols | 10 |
| Software Plugins | 37 |
| Add-on Plugins | 25 |
| Hardware Suites | 16 |
| Domain Field Panels | 16 |
| Macro Action Types | 13 |
| AI Assistants | 8 (1 built-in offline + 7 external) |
| Built-in Citations | 200+ |
| Sample Test Files | 30+ |
| Journal Templates | 8 categories |
| UI Framework | ttkbootstrap |

⬇️ [Download on GitLab](https://gitlab.com/sefy76/scientific-toolkit) | ⬇️ [Download on GitHub](https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit) | 🐛 [Report Bug](https://gitlab.com/sefy76/scientific-toolkit/-/issues)
