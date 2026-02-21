# 🔬 Scientific Toolkit v2.0

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://gitlab.com/sefy76/scientific-toolkit)
[![GitLab](https://img.shields.io/badge/GitLab-Repository-orange.svg)](https://gitlab.com/sefy76/scientific-toolkit)

> **Free integrated platform for multi-domain scientific analysis**

Scientific Toolkit combines geochemistry, archaeology, spectroscopy, GIS, statistical analysis, and hardware integration in one free tool. Built for researchers, students, and institutions with limited software budgets.

Based on Basalt Provenance Triage Toolkit v10.2, expanded to cover multiple scientific disciplines.

---
    Free integrated platform for multi-domain scientific analysis
    *70 classification engines · 50 protocols · 37 software plugins · 23 add-ons · 7 hardware suites*

Scientific Toolkit combines geochemistry, archaeology, spectroscopy, GIS, statistical analysis, and hardware integration in one free tool. Built for researchers, students, and institutions with limited software budgets.

Based on Basalt Provenance Triage Toolkit v10.2, expanded to cover multiple scientific disciplines.
🎯 What Is This?

Scientific Toolkit is a Python/Tkinter desktop application that integrates tools for:

    Geochemical data analysis and classification

    Archaeological material analysis

    Hardware instrument integration (XRF, FTIR, XRD, GPS, calipers, balances)

    Statistical analysis and machine learning

    GIS visualization and spatial analysis

    Publication-ready figure generation

    Isotope mixing models with Bayesian MCMC inversion

    U-Pb geochronology and detrital provenance

    Normative mineral calculations (CIPW, Hutchison, Niggli, Rittmann)

Key features:

    70 classification engines implementing published methods (across 2 engines: classification + protocol)

    50 scientific protocols for standardized workflows

    37 software plugins for advanced analysis

    23 add-on plugins for plotting, consoles, and AI assistants

    7 hardware suites supporting dozens of device models

    Multiple plotting and visualization options

    Import/export for common data formats

    Template system for journal-specific figures

    Completely free and open source

Who might find this useful:

    Students learning geochemistry or archaeology

    Researchers with limited software budgets

    Teaching labs needing multi-topic coverage

    Field scientists needing portable instrument integration

    Museums managing collections and analysis data

    Anyone working across geology and archaeology

What this is NOT:

    Not a replacement for specialized commercial tools in single domains

    Not optimized for massive datasets (10,000+ samples)

    Not a web application (desktop only)

    Not a programming language (GUI-based)

📊 Current State (February 2026)
Core Statistics
Metric	Count
Total files	153
Lines of code	~77,000
Classification engines	70
Scientific protocols	50
Software plugins	37
Add-on plugins	23
Hardware suites	7
Hardware device models supported	Dozens across suites
Built-in citations	200+
🧬 Classification Engines (70) & Protocols (50)
Two Engine Architecture

The toolkit features two complementary engines for scientific classification:
Engine	Purpose	Count
Classification Engine	Rule-based classification using JSON schemes	70 schemes
Protocol Engine	Multi-stage workflows with conditional logic	50 protocols
Classification Engine Schemes (70)

Geochemistry (20+)

    TAS Volcanic Classification (Le Bas et al. 1986)

    AFM Irvine-Baragar Series (Irvine & Baragar 1971)

    QAPF Mineralogical Classification (IUGS Le Maitre 2002)

    Winchester-Floyd Discrimination (Winchester & Floyd 1977)

    Pearce Zr/Y Tectonic (Pearce & Norry 1979)

    Jensen Cation Plot (Jensen 1976)

    REE Pattern Classification (Boynton 1984; Sun & McDonough 1989)

    REE Named Types (N-MORB, OIB, E-MORB, etc.)

    CI-Normalized Spider Diagram (Anders & Grevesse 1989)

    Pearce Mantle Array (Pearce 2008)

    Chemical Index of Alteration (Nesbitt & Young 1982)

    Normative Molar Proportions (Cross et al. 1902)

    Igneous Major-Oxide Indices

    Magma Rheology and Eruption Style

    Volcanic Series Discrimination

    Total Alkali vs Silica (TAS Polygons)

    K₂O–SiO₂ Volcanic Series

    Pearce Nb/Yb–Th/Yb Mantle Array

    Pearce Zr/Y vs Zr Tectonic

    And many more...

Metamorphic Petrology (5+)

    Metamorphic Facies (Winter 2014; Yardley 1989)

    Zircon Trace Element Thermometry (Watson & Harrison 2005)

    Thermobarometry calculations

Sedimentology (12+)

    Dunham Carbonate Classification (Dunham 1962)

    Dott Sandstone Classification (Dott 1964)

    Folk Carbonate Classification (Folk 1959, 1962)

    Pettijohn Sandstone Classification (Pettijohn 1975)

    Sediment Grain Size (Wentworth 1922)

    Sediment Texture and Maturity (Shepard 1954; Folk 1974)

    Munsell Color Classification

    USDA Soil Texture Classification

    Folk–Shepard Sediment Texture

    Grain-size classification

    Textural maturity indices

Geochronology (3+)

    U-Pb Concordia QC (Wetherill 1956; Tera & Wasserburg 1972)

    Zircon trace element thermometry

    LA-ICP-MS signal processing

Isotope Geochemistry (3+)

    Isotope provenance and diet (Sr, O, Pb)

    Strontium mobility index (Montgomery 2010)

    Stable isotope diet (δ¹³C, δ¹⁵N)

Environmental (8+)

    Geoaccumulation Index (Müller 1969, 1981)

    Enrichment Factor Screening (Zoller et al. 1974)

    Environmental Pollution Indices (Hakanson 1980)

    Hakanson Ecological Risk Protocol

    EPA Sediment Quality Protocol

    Pollution Load Index

    Risk Assessment Code (RAC)

    Contamination Factor (CF)

Soil Science (8+)

    USDA Soil Texture Classification

    USDA Soil Texture Triangle (Full)

    Soil Salinity Classification (EC)

    Soil Sodicity (SAR)

    FAO Soil Classification (pH & EC)

    Soil Chemical Properties

    Soil Salinity (ECe standards)

    Soil morphology

Archaeology & Bioarchaeology (10+)

    Bone Collagen QC (C:N) (DeNiro 1985; van Klinken 1999)

    Bone Diagenesis (Ca/P) (Hedges et al. 1995)

    FTIR Crystallinity Index (Weiner & Bar-Yosef 1990)

    Stable Isotope Diet (δ¹³C, δ¹⁵N) (Schoeninger et al. 1983)

    Bone Trophic Diet (Sr/Ca, Ba/Ca)

    Behrensmeyer Weathering Stages (1978)

    Shipman & Rose Burning Stages (1984)

    Maresha Zooarchaeology Protocol

    Zooarchaeology Fragmentation & Breakage

    Ceramic Firing Temperature Proxies (Tite 2008)

    Glass Compositional Families (Sayre & Smith 1961)

Meteoritics (6+)

    Chondrite Meteorite Classification (Kallemeyn et al. 1989)

    Meteorite Shock Stage (Stöffler et al. 1991)

    Meteorite Weathering Grade (Wlotzka 1993)

    Meteorite Petrology and Groups

    Planetary Analog Ratio (Fe/Mn) (Papike et al. 2003)

    CI-normalized spider diagrams

Archaeometallurgy (5+)

    Copper Alloy Classification (Pernicka 1999; Craddock 1978)

    Slag Basicity Index (Bachmann 1982)

    Slag Thermochemical Properties

    Iron Bloom Classification (Scott 1991; Buchwald 2005)

    Slag V-Ratio classification

Hydrogeochemistry (5+)

    Piper Diagram Water Type (Piper 1944)

    Stiff Diagram Pattern (Stiff 1951)

    Water Hardness Classification

    Stiff diagram classification

    Water chemistry typing

Provenance & Tectonics (5+)

    Provenance Fingerprinting (Hartung 2017; Shervais 1982)

    Tectonic Discrimination Diagrams (Pearce & Cann 1973)

    Regional Triage (Egyptian–Sinai–Levantine)

    Incompatible trace-element fingerprinting

    Basalt provenance triage

Alteration & Weathering (3+)

    Alteration Indices (Ishikawa & CCPI) (Ishikawa et al. 1976)

    Chemical Index of Alteration (Nesbitt & Young 1982)

    Hydrothermal alteration indices

Analytical QA/QC (4+)

    Analytical Precision Filter (RSD) (Potts & West 2008)

    Analytical Quality Control (IUPAC 1997; ISO 17025)

    LOD/LOQ classification

    CRM deviation and drift monitoring

Protocol Engine Workflows (50)

Multi-stage protocols for complex workflows:

    Behrensmeyer Weathering Protocol - Standardized bone weathering stages

    EPA Sediment Quality Protocol - TEL/PEL and ERL/ERM thresholds

    Folk–Shepard Sediment Texture Protocol - Grain-size classification with sorting

    Hakanson Ecological Risk Protocol - CF, Er, and RI thresholds

    IUGS Igneous Protocol - TAS + QAPF combined workflow

    Maresha Zooarchaeology Protocol - Multi-stage faunal analysis

    Shipman & Rose Burning Protocol - Bone burning stages

    Stable Isotope Diet Protocol - δ¹³C + δ¹⁵N interpretation

    USDA Soil Morphology Protocol - Horizons, texture, structure, color

    Zooarchaeology Fragmentation Protocol - Breakage patterns and freshness

    *And 40+ more specialized protocols*

🔌 Hardware Integration (7 Suites)

Each hardware suite supports multiple device models:
1. Barcode/QR Scanner Suite

Devices: Zebra, Honeywell, Datalogic, Socket, Inateck, Eyoyo (50+ models)
Protocols: USB HID, USB Serial, Bluetooth SPP, Bluetooth LE, Webcam
2. Elemental Geochemistry Suite

Devices: SciAps X-550/X-505, Olympus Vanta/Delta, Bruker S1/Tracer, Thermo Niton, ICP-MS instruments
Protocols: SciAps SDK, CSV parsing, PyVISA, serial communication
3. Mineralogy Suite

Devices: Any with RRUFF spectra – 5,185 minerals
Protocols: Spectragryph mirror, custom URL download, local file import
4. Physical Properties Suite

Devices: AGICO Kappabridge, Bartington MS2/MS3, ZH Instruments, Terraplus KT, Mitutoyo Digimatic calipers, Sylvac Bluetooth calipers, Mahr MarCal, iGaging
Protocols: Serial, HID, Bluetooth LE, Mitutoyo SPC protocol (24-bit decoding)
5. Solution Chemistry Suite

Devices: Mettler Toledo, Thermo Orion, Hanna, Horiba LAQUA, YSI ProDSS, Hach, WTW (45+ models)
Protocols: Serial, HID, Bluetooth
6. Spectroscopy Suite

Devices: Thermo Nicolet, PerkinElmer, Bruker ALPHA, Agilent handheld, B&W Tek Raman, Ocean Optics, Avantes (50+ models)
Protocols: Serial, Ethernet, file import, USB
7. Zooarchaeology Suite

Devices: Mitutoyo calipers, Sylvac Bluetooth, Ohaus balances, Sartorius balances, Mettler Toledo balances, Emlid Reach GNSS, Dino-Lite microscopes
Protocols: HID, Bluetooth, serial, NMEA 0183
💻 Software Plugins (37)
Statistical Analysis (6)

    Compositional Stats PRO – CLR/ILR transforms, PCA with robust covariance

    PCA+LDA Explorer Pro – PCA, LDA, PLS-DA, Random Forest, SVM, t-SNE

    Geochemical Explorer – Multivariate analysis, statistical tests

    Uncertainty Propagation – Monte Carlo classification, confidence ellipses

    Interactive Contouring – KDE-based contouring, 2D histogram

    Spatial Kriging – Variogram analysis, interpolation

Geochronology (4)

    Geochronology Suite – U-Pb concordia, Ar-Ar spectra, detrital KDE/MDS

    Dating Integration – Bayesian age-depth with MCMC, calibration curves

    LA-ICP-MS Pro – Signal processing, U-Pb dating, elemental quantification

    U-Pb Concordia QC – Discordance screening, common Pb correction

Petrology (5)

    Advanced Normative Calculations – CIPW, Hutchison, Niggli, Mesonorm, Rittmann

    Advanced Petrogenetic Models – AFC (DePaolo 1981), zone refining

    Magma Modeling – Fractional crystallization, AFC, mixing

    Thermobarometry Suite – Pyroxene, feldspar, amphibole thermobarometry

    Petrogenetic Suite – Complete magma evolution models

Isotope Geochemistry (4)

    Isotope Mixing Models – Binary/ternary mixing, Monte Carlo, Bayesian MCMC inversion

    Literature Comparison – Compare to published datasets

    Advanced Normalization – Lucas-Tooth & Compton for pXRF/ICP

    Stable Isotope Diet – δ¹³C, δ¹⁵N interpretation

GIS & Mapping (5)

    GIS 3D Viewer PRO – 2D maps, 3D terrain, web maps, SRTM

    Google Earth Pro – 3D extrusion, time animation, photo integration

    Quartz GIS – Point-in-polygon, viewshed, attribute tables

    GeoPandas Plotter – Archaeological site mapping

    3D GIS Viewer – Spatial visualization

Archaeology (5)

    Lithic Morphometrics – Elliptical Fourier analysis, edge damage

    Zooarchaeology Analytics – NISP/MNI, taphonomy, aging

    Photo Manager – Link sample photos, organize field photography

    Report Generator – Excavation reports, IAA submissions

    Virtual Microscopy PRO – Petrographic + 3D mesh analysis

Data Processing (5)

    Data Validation Filter – IoGAS-style validation, outlier detection

    Batch Processor – Process multiple files in a directory

    Advanced Export – High-resolution PDF/EPS/SVG export

    Script Export – Export workflows as Python/R scripts

    Macro Recorder – Record and replay user workflows

Specialized (3)

    Ague Hg Mobility – Mercury speciation, BCR sequential extraction

    Museum Import – Import from Europeana and museum APIs

    Demo Data Generator – Generate test datasets

🎨 Add-on Plugins (23)
Plotting & Visualization (9)

    ASCII Plotter – Text-based plots (no graphics)

    Matplotlib Plotter – High-quality scientific plots

    Seaborn Plotter – Statistical visualizations

    Ternary Plotter – Ternary diagrams

    Pillow Plotter – Basic PIL/Pillow plots

    Missingno Plotter – Missing data visualization

    Geoplot Pro – IUGS diagrams, AFC modeling

    Geopandas Plotter – Archaeological site mapping

    Interactive Contouring – Density estimation

Interactive Consoles (6)

    Python Console – Interactive Python

    R Console – Run R code for statistics

    Julia Console – High-performance computing

    SQL Console – SQLite queries

    GIS Console – Spatial analysis with GeoPandas

    File Console – Safe file management

AI Assistants (7)

    Claude AI (Anthropic) – Requires API key

    ChatGPT AI (OpenAI) – Requires API key

    Gemini AI (Google) – Requires API key

    DeepSeek AI – Requires API key

    Grok AI (xAI) – Requires API key

    Copilot AI – Requires API key

    Ollama AI – Free local AI (no API key)

Utilities (1)

    Batch Processor – Process multiple files

🎓 Academic Citations

Scientific Toolkit implements 200+ published methods with complete citations in every plugin. Key references include:
Geochemistry

    Le Bas, M.J., Le Maitre, R.W., Streckeisen, A., & Zanettin, B. (1986). A chemical classification of volcanic rocks based on the total alkali-silica diagram. Journal of Petrology, 27(3), 745-750.

    Irvine, T.N., & Baragar, W.R.A. (1971). A guide to the chemical classification of the common volcanic rocks. Canadian Journal of Earth Sciences, 8(5), 523-548.

    Sun, S.S., & McDonough, W.F. (1989). Chemical and isotopic systematics of oceanic basalts. Geological Society, London, Special Publications, 42(1), 313-345.

    Pearce, J.A. (2008). Geochemical fingerprinting of oceanic basalts with applications to ophiolite classification. Lithos, 100(1-4), 14-48.

Geochronology

    Wetherill, G.W. (1956). Discordant uranium-lead ages, I. Eos, Transactions American Geophysical Union, 37(3), 320-326.

    Tera, F., & Wasserburg, G.J. (1972). U-Th-Pb systematics in three Apollo 14 basalts. Earth and Planetary Science Letters, 14(3), 281-304.

    Ludwig, K.R. (2003). User's Manual for Isoplot 3.00. Berkeley Geochronology Center.

Isotope Geochemistry

    Faure, G. (1986). Principles of Isotope Geology (2nd ed.). Wiley.

    Albarede, F. (1995). Introduction to Geochemical Modeling. Cambridge University Press.

    York, D. (1966). Least-squares fitting of a straight line. Canadian Journal of Physics, 44(5), 1079-1086.

    Foreman-Mackey, D., Hogg, D.W., Lang, D., & Goodman, J. (2013). emcee: The MCMC hammer. Publications of the Astronomical Society of the Pacific, 125(925), 306-312.

Archaeology

    DeNiro, M.J. (1985). Postmortem preservation and alteration of in vivo bone collagen isotope ratios. Nature, 317, 806-809.

    Behrensmeyer, A.K. (1978). Taphonomic and ecologic information from bone weathering. Paleobiology, 4(2), 150-162.

    von den Driesch, A. (1976). A Guide to the Measurement of Animal Bones from Archaeological Sites. Peabody Museum Bulletin 1.

Sedimentology

    Wentworth, C.K. (1922). A scale of grade and class terms for clastic sediments. Journal of Geology, 30(5), 377-392.

    Dunham, R.J. (1962). Classification of carbonate rocks according to depositional texture. AAPG Memoir 1, 108-121.

Environmental

    Müller, G. (1969). Index of geoaccumulation in sediments of the Rhine River. GeoJournal, 2(3), 108-118.

    Hakanson, L. (1980). An ecological risk index for aquatic pollution control. Water Research, 14(8), 975-1001.

Meteoritics

    Stöffler, D., Keil, K., & Scott, E.R.D. (1991). Shock metamorphism of ordinary chondrites. Geochimica et Cosmochimica Acta, 55(12), 3845-3867.

    Weisberg, M.K., McCoy, T.J., & Krot, A.N. (2006). Systematics and evaluation of meteorite classification. Meteorites and the Early Solar System II, 19-52.

Statistical Methods

    Pearson, K. (1901). On lines and planes of closest fit to systems of points in space. The London, Edinburgh, and Dublin Philosophical Magazine and Journal of Science, 2(11), 559-572.

    Hotelling, H. (1933). Analysis of a complex of statistical variables into principal components. Journal of Educational Psychology, 24(6), 417-441.

See CITATIONS.md for the complete list of 200+ references.
💡 Who Is This For?

✅ Graduate students working across geology + archaeology
✅ University professors teaching multi-topic courses
✅ Museum researchers managing collections + analysis
✅ Field scientists needing portable instrument integration
✅ Developing-world researchers with limited software budgets
✅ Independent researchers and citizen scientists
✅ Small institution labs without commercial licenses
✅ Environmental consultants needing flexible tools
✅ Anyone who can't afford $8,000/year in software subscriptions
🛠️ Installation
Requirements

    Python 3.8 or higher

    Operating System: Windows, macOS, or Linux

    Disk space: ~50 MB (core) + optional dependencies

    RAM: 2 GB minimum, 4 GB recommended

Core Dependencies
bash

pip install numpy pandas matplotlib tkinter

Full Installation (all features)
bash

pip install scipy scikit-learn seaborn pillow geopandas rasterio \
            opencv-python pyserial bleak hidapi simplekml \
            folium pyvisa emcee corner joblib reportlab openpyxl

See INSTALLATION.md for platform-specific instructions.
📚 Documentation

    Installation Guide - Platform-specific setup

    Quick Start - Get running in 5 minutes

    Citations - All 200+ published methods and references

    Plugin Guide - How to use plugins

    FAQ - Common questions

    Protocol Guide - Using multi-stage protocols

🤝 Contributing

Contributions welcome! Ways to help:

    Report bugs via GitLab Issues

    Add new classification engines

    Create hardware plugins for new instruments

    Improve documentation

    Share example workflows

See CONTRIBUTING.md for guidelines.
📊 How This Compares to Other Tools
Tool	Cost	Strengths	Weaknesses
GCDkit	Free	Excellent igneous petrology (200+ functions)	R-based, no hardware, archaeology missing
ioGAS	$2,000+/year	Professional, polished UI, mining focus	Expensive, no hardware, archaeology missing
PAST	Free	Excellent statistics (400+ tests)	1990s UI, no hardware, limited geochemistry
Python/R scripts	Free	Maximum flexibility	Requires programming
Scientific Toolkit	Free	70 classifications + 50 protocols, 67 plugins, 7 hardware suites	Less polished UI, slower with large datasets

This toolkit is best for: Students, teaching labs, budget-constrained researchers, museums, cross-disciplinary projects, field work with portable instruments.

This toolkit is NOT for: Large-scale industrial mining operations (>10,000 samples), users needing enterprise support.
🗺️ Current Status & Roadmap

Current Version: 2.0 (February 2026)
✅ Stable Features

    70 classification engines (across 2 engines)

    50 scientific protocols for standardized workflows

    37 software plugins (full implementations)

    23 add-on plugins (plotting, consoles, AI)

    7 hardware suites supporting dozens of devices

    Publication templates (Nature, Science, AGU, Elsevier)

    Data import/export (CSV, Excel, JSON, KML)

🚧 Known Limitations

    Tkinter UI may look dated on modern systems

    Large datasets (>10,000 samples) may be slow

    Documentation is being updated (Feb 2026)

    Not all hardware tested on all platforms

🔮 Future Plans

    Video tutorials

    More classification engines

    Performance optimization for large datasets

    Peer-reviewed methods publication

    Community plugin repository

⚠️ IMPORTANT DISCLAIMER

This software is provided "AS IS" without warranty of any kind.

    You are responsible for validating all results - Always verify classifications and calculations are appropriate for your samples

    Check your data carefully - Garbage in = garbage out

    Don't trust blindly - This is a tool to assist analysis, not replace expert judgment

    Scientific responsibility is yours - Verify methods are appropriate for your research

    Report bugs and issues! - Help improve the software by testing and reporting problems

Found a bug? Results don't look right? → Report it on GitLab

We need users to test thoroughly and report issues. Your feedback makes this better for everyone.
📜 License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International

✅ Free to use - research, education, museums, companies, anyone
✅ Modify and improve - adapt to your needs
✅ Share with attribution - credit the original work
❌ Cannot sell this software - don't charge money for the toolkit itself
❌ Cannot profit from the code - don't incorporate it into commercial products you sell
🔄 Derivatives must use same license - keep it free

In plain English: Use it freely for your work (even commercial work). Just don't sell the software itself or use the code in products you're selling.

See LICENSE for legal details.
📞 Contact & Support

    GitLab Issues: Report bugs or request features

    Email: sefy76@gmail.com

Need help? Open an issue on GitLab with:

    Your operating system

    Python version

    Error message or description

    What you were trying to do

🙏 Acknowledgments

This toolkit implements published scientific methods developed by researchers worldwide. See CITATIONS.md for the complete list of 200+ references.

Built with: NumPy, Pandas, Matplotlib, SciPy, Scikit-learn, Emcee, PySerial, GeoPandas, and the entire open-source Python scientific computing ecosystem.

Hardware protocols based on manufacturer documentation from Mitutoyo, SciAps, Bruker, Thermo, Mettler Toledo, and others.

Based on Basalt Provenance Triage Toolkit v10.2, expanded for multi-domain use.
<p align="center"> <b>Free software for science</b><br> <i>Because research shouldn't require expensive licenses</i> </p><p align="center"> <a href="QUICK_START.md">Get Started</a> • <a href="INSTALLATION.md">Install</a> • <a href="CITATIONS.md">Citations</a> • <a href="CONTRIBUTING.md">Contribute</a> </p>
📊 Quick Stats Summary
Category	Count
Total Files	153
Lines of Code	~77,000
Classification Engines	70
Scientific Protocols	50
Software Plugins	37
Add-on Plugins	23
Hardware Suites	7
Hardware Device Models	Dozens across suites
AI Assistants	7
Built-in Citations	200+
Journal Templates	8 categories

⬇️ Download Now | ⭐ Star on GitLab | 🐛 Report Bug
