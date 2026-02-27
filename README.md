# 🔬 Scientific Toolkit v2.0

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://gitlab.com/sefy76/scientific-toolkit)
[![GitLab](https://img.shields.io/badge/GitLab-Repository-orange.svg)](https://gitlab.com/sefy76/scientific-toolkit)

> **Free integrated platform for multi-domain scientific analysis**

Scientific Toolkit combines geochemistry, archaeology, spectroscopy, GIS, statistical analysis, and hardware integration in one free tool. Built for researchers, students, and institutions with limited software budgets.

Based on Basalt Provenance Triage Toolkit v10.2, expanded to cover multiple scientific disciplines.

---

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

    10 scientific protocols for standardized workflows

    48 software plugins for advanced analysis

    22 add-on plugins for plotting, consoles, and AI assistants

    16 hardware suites supporting dozens of device models

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
Total files	153+
Lines of code	~77,000
Classification engines	70
Scientific protocols	10
Software plugins	48
Add-on plugins	22
Hardware suites	16
Hardware device models supported	Dozens across suites
Built-in citations	200+

🧬 Classification Engines (70) & Protocols (10)
Two Engine Architecture

The toolkit features two complementary engines for scientific classification:
Engine	Purpose	Count
Classification Engine	Rule-based classification using JSON schemes	70 schemes
Protocol Engine	Multi-stage workflows with conditional logic	10 protocols

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

Protocol Engine Workflows (10)

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

🔌 Hardware Integration (16 Suites)

Each hardware suite supports multiple device models:
1. Archaeology & Archaeometry Suite

Devices: UAV/GNSS systems, portable XRF, ground-penetrating radar, archaeometry instruments
Protocols: GPS/NMEA, serial, file import

2. Barcode/QR Scanner Suite

Devices: Zebra, Honeywell, Datalogic, Socket, Inateck, Eyoyo (50+ models)
Protocols: USB HID, USB Serial, Bluetooth SPP, Bluetooth LE, Webcam

3. Chromatography & Analytical Suite

Devices: GC, HPLC, IC instruments from Agilent, Thermo, Waters, Shimadzu
Protocols: Serial, Ethernet, file import (.csv, .cdf, .raw)

4. Clinical & Molecular Diagnostics Suite

Devices: PCR, plate readers, sequencers, clinical analyzers
Protocols: Serial, file import, LIMS integration

5. Electrochemistry Suite

Devices: Potentiostats, galvanostats, impedance analyzers (Gamry, BioLogic, Metrohm)
Protocols: USB, Ethernet, proprietary file formats

6. Elemental Geochemistry Suite

Devices: SciAps X-550/X-505, Olympus Vanta/Delta, Bruker S1/Tracer, Thermo Niton, ICP-MS instruments
Protocols: SciAps SDK, CSV parsing, PyVISA, serial communication

7. Geophysics Suite

Devices: Magnetometers, gravimeters, seismographs, GPR, resistivity meters
Protocols: SEG-Y, ASCII, serial, proprietary formats

8. Materials Characterization Suite

Devices: SEM/EDX, XRD, nanoindentation, hardness testers, dilatometers
Protocols: Serial, Ethernet, file import (EMSA, JADE, raw)

9. Meteorology & Environmental Suite

Devices: Weather stations, loggers, air quality monitors (Davis, Vaisala, Campbell)
Protocols: Serial, Modbus, SDI-12, NMEA, Ethernet

10. Molecular Biology Suite

Devices: Spectrophotometers, gel imagers, qPCR systems, fluorometers
Protocols: USB, serial, file import

11. Physical Properties Suite

Devices: AGICO Kappabridge, Bartington MS2/MS3, ZH Instruments, Terraplus KT, Mitutoyo Digimatic calipers, Sylvac Bluetooth calipers, Mahr MarCal, iGaging
Protocols: Serial, HID, Bluetooth LE, Mitutoyo SPC protocol (24-bit decoding)

12. Physics Test & Measurement Suite

Devices: Oscilloscopes, multimeters, power supplies, signal generators (Keysight, Tektronix, Rigol)
Protocols: USB (USBTMC), GPIB, VISA, serial

13. Solution Chemistry Suite

Devices: Mettler Toledo, Thermo Orion, Hanna, Horiba LAQUA, YSI ProDSS, Hach, WTW (45+ models)
Protocols: Serial, HID, Bluetooth

14. Spectroscopy Suite

Devices: Thermo Nicolet, PerkinElmer, Bruker ALPHA, Agilent handheld, B&W Tek Raman, Ocean Optics, Avantes (50+ models)
Protocols: Serial, Ethernet, file import, USB

15. Thermal Analysis & Calorimetry Suite

Devices: DSC, TGA, TMA, DMA instruments (Netzsch, TA Instruments, Mettler Toledo)
Protocols: Serial, Ethernet, proprietary file formats

16. Zooarchaeology Suite

Devices: Mitutoyo calipers, Sylvac Bluetooth, Ohaus balances, Sartorius balances, Mettler Toledo balances, Emlid Reach GNSS, Dino-Lite microscopes
Protocols: HID, Bluetooth, serial, NMEA 0183

💻 Software Plugins (48)
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

GIS & Mapping (3)

    GIS 3D Viewer PRO – 2D maps, 3D terrain, web maps, SRTM

    Google Earth Pro – 3D extrusion, time animation, photo integration

    Quartz GIS Pro – Point-in-polygon, viewshed, attribute tables

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

Discipline-Specific Analysis Suites (14 additional)

    Archaeology & Archaeometry Suite – Comprehensive site analysis and archaeometry

    Barcode Scanner Suite – Barcode/QR workflow integration

    Chromatography Analysis Suite – GC/HPLC/IC data processing

    Clinical Diagnostics Suite – Clinical and diagnostic sample analysis

    Data Prep Pro – Advanced data cleaning and transformation

    Electrochemistry Suite – Electrochemical data analysis

    Geophysics Suite – Geophysical survey data analysis

    Materials Science Suite – Materials characterization analysis

    Meteorology Suite – Atmospheric and climate data analysis

    Molecular Biology Suite – Genomic and proteomic workflows

    Physical Properties Suite – Rock and mineral physical properties

    Physics Test & Measurement Suite – Instrument calibration and analysis

    Solution Chemistry Suite – Aqueous solution chemistry analysis

    Spectroscopy Analysis Suite – Multi-technique spectral data processing
    Thermal Analysis Suite – DSC/TGA/TMA data analysis

Specialized (3)

    Ague Hg Mobility – Mercury speciation, BCR sequential extraction

    Museum Import – Import from Europeana and museum APIs

    Demo Data Generator – Generate test datasets

🎨 Add-on Plugins (22)
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

Scientific Toolkit implements 200+ published methods with complete citations in every plugin.
Every researcher whose method is implemented deserves full credit — the list below covers all 18 disciplines.

Igneous Petrology

    Le Bas, M.J., Le Maitre, R.W., Streckeisen, A., & Zanettin, B. (1986). A chemical classification
    of volcanic rocks based on the total alkali-silica diagram. Journal of Petrology, 27(3), 745-750.

    Irvine, T.N., & Baragar, W.R.A. (1971). A guide to the chemical classification of the common
    volcanic rocks. Canadian Journal of Earth Sciences, 8(5), 523-548.

    Le Maitre, R.W. (Ed.) (2002). Igneous Rocks: A Classification and Glossary of Terms (2nd ed.).
    Cambridge University Press. [IUGS QAPF]

    Winchester, J.A., & Floyd, P.A. (1977). Geochemical discrimination of different magma series and
    their differentiation products using immobile elements. Chemical Geology, 20, 325-343.

    Pearce, J.A., & Norry, M.J. (1979). Petrogenetic implications of Ti, Zr, Y, and Nb variations in
    volcanic rocks. Contributions to Mineralogy and Petrology, 69(1), 33-47.

    Pearce, J.A. (2008). Geochemical fingerprinting of oceanic basalts with applications to ophiolite
    classification. Lithos, 100(1-4), 14-48.

    Jensen, L.S. (1976). A new cation plot for classifying subalkalic volcanic rocks. Ontario Division
    of Mines Miscellaneous Paper 66.

    Boynton, W.V. (1984). Cosmochemistry of the rare earth elements: meteorite studies. In Henderson, P.
    (Ed.), Rare Earth Element Geochemistry, 63-114. Elsevier.

    Sun, S.S., & McDonough, W.F. (1989). Chemical and isotopic systematics of oceanic basalts.
    Geological Society, London, Special Publications, 42(1), 313-345.

    Anders, E., & Grevesse, N. (1989). Abundances of the elements: meteoritic and solar.
    Geochimica et Cosmochimica Acta, 53(1), 197-214.

    Nesbitt, H.W., & Young, G.M. (1982). Early Proterozoic climates and plate motions inferred from
    major element chemistry of lutites. Nature, 299, 715-717.

    Cross, W., Iddings, J.P., Pirsson, L.V., & Washington, H.S. (1902). A quantitative
    chemico-mineralogical classification and nomenclature of igneous rocks. Journal of Geology,
    10(6), 555-690. [CIPW Norm]

    Hutchison, C.S. (1974). Laboratory Handbook of Petrographic Techniques. Wiley.

    Niggli, P. (1936). Die quantitative mineralogische Klassifikation der Eruptivgesteine.
    Schweizerische Mineralogische und Petrographische Mitteilungen, 16, 281-325.

    Rittmann, A. (1973). Stable Mineral Assemblages of Igneous Rocks. Springer.

    Winkler, H.G.F. (1979). Petrogenesis of Metamorphic Rocks (5th ed.). Springer.

    Pandey, B.K., Gupta, A.K., Lal, N., Krishnamurthy, P., & Chabria, T. (2009). CIPW norm calculation
    by matrix algebra. Journal of the Geological Society of India, 73(4), 567-570.

    Verma, S.P., Torres-Alvarado, I.S., & Sotelo-Rodriguez, Z.T. (2002). SINCLAS: standard igneous norm
    and volcanic rock classification system. Computers & Geosciences, 28(5), 711-715.

    Shervais, J.W. (1982). Ti-V plots and the petrogenesis of modern and ophiolitic lavas.
    Earth and Planetary Science Letters, 59(1), 101-118.

Thermobarometry

    Brey, G.P., & Köhler, T. (1990). Geothermobarometry in four-phase lherzolites II.
    Journal of Petrology, 31(6), 1353-1378.

    Putirka, K., Johnson, M., Kinzler, R., Longhi, J., & Walker, D. (2003). Thermobarometry of mafic
    igneous rocks based on clinopyroxene-liquid equilibria. American Mineralogist, 88(10), 1542-1554.

    Putirka, K.D. (2008). Thermometers and barometers for volcanic systems. Reviews in Mineralogy
    and Geochemistry, 69(1), 61-120.

    Nimis, P., & Taylor, W.R. (2000). Single clinopyroxene thermobarometry: a new calibration based
    on Al-in-opx thermometer. Contributions to Mineralogy and Petrology, 139(5), 541-554.

    Waters, L.E., & Lange, R.A. (2015). An updated calibration of the plagioclase-liquid
    hygrometer-thermometer. American Mineralogist, 100(10), 2172-2184.

    Elkins, L.T., & Grove, T.L. (1990). Ternary feldspar experiments and thermodynamic models.
    American Mineralogist, 75(5-6), 544-559.

    Leake, B.E., et al. (1997). Nomenclature of amphiboles. European Journal of Mineralogy, 9(3), 623-651.

    Ridolfi, F., Renzulli, A., & Puerini, M. (2010). Stability and chemical equilibrium of amphibole in
    calc-alkaline magmas. Contributions to Mineralogy and Petrology, 160(1), 45-66.

    Ridolfi, F., & Renzulli, A. (2012). Calcic amphiboles in calc-alkaline and alkaline magmas:
    thermobarometric and chemometric empirical equations. Contributions to Mineralogy and Petrology,
    163(5), 877-895.

    Mutch, E.J.F., Blundy, J.D., Tattitch, B.C., Cooper, F.J., & Brooker, R.A. (2016). An experimental
    study of amphibole stability in low-pressure granitic magmas. Contributions to Mineralogy and
    Petrology, 171(10), 85.

    Putirka, K.D. (2016). Amphibole thermometers and barometers for igneous systems.
    American Mineralogist, 101(4), 841-858.

    Beattie, P. (1993). Olivine-melt and orthopyroxene-melt equilibria. Contributions to Mineralogy
    and Petrology, 115(1), 103-111.

    Holdaway, M.J. (2001). Recalibration of the GASP geobarometer in light of recent garnet and
    plagioclase activity models and versions of the garnet-biotite geothermometer. American Mineralogist,
    86(10), 1117-1129.

    Ravna, E.K. (2000). The garnet-clinopyroxene Fe2+-Mg geothermometer. Journal of Metamorphic
    Geology, 18(2), 211-219.

    Holland, T.J.B., & Powell, R. (1990). An enlarged and updated internally consistent thermodynamic
    dataset. Journal of Metamorphic Geology, 8(1), 89-124.

    Newton, R.C., & Haselton, H.T. (1981). Thermodynamics of the garnet-plagioclase-Al₂SiO₅-quartz
    geobarometer. Advances in Physical Geochemistry, 1, 131-147.

Geochronology

    Wetherill, G.W. (1956). Discordant uranium-lead ages, I. Eos, Transactions American Geophysical
    Union, 37(3), 320-326.

    Tera, F., & Wasserburg, G.J. (1972). U-Th-Pb systematics in three Apollo 14 basalts. Earth and
    Planetary Science Letters, 14(3), 281-304.

    Ludwig, K.R. (2003). User's Manual for Isoplot 3.00. Berkeley Geochronology Center.

    Longerich, H.P., Jackson, S.E., & Günther, D. (1996). Laser ablation inductively coupled plasma
    mass spectrometric transient signal data acquisition and analyte concentration calculation.
    Journal of Analytical Atomic Spectrometry, 11(9), 899-904.

    Fryer, B.J., Jackson, S.E., & Longerich, H.P. (1993). The application of laser ablation
    microprobe-ICP-MS to in situ U-Pb geochronology. Chemical Geology, 109(1-4), 1-8.

    Jackson, S.E., Pearson, N.J., Griffin, W.L., & Belousova, E.A. (2004). The application of
    laser ablation-ICP-MS to in situ U-Pb zircon geochronology. Chemical Geology, 211(1-2), 47-69.

    Wiedenbeck, M., et al. (1995). Three natural zircon standards for U-Th-Pb, Lu-Hf, trace element
    and REE analyses. Geostandards Newsletter, 19(1), 1-23.

    Spencer, C.J., Kirkland, C.L., & Taylor, R.J.M. (2016). Strategies towards statistically robust
    interpretations of in situ U-Pb zircon geochronology. Geoscience Frontiers, 7(4), 581-589.

Isotope Geochemistry

    Faure, G. (1986). Principles of Isotope Geology (2nd ed.). Wiley.

    Albarede, F. (1995). Introduction to Geochemical Modeling. Cambridge University Press.

    York, D. (1966). Least-squares fitting of a straight line. Canadian Journal of Physics, 44(5),
    1079-1086.

    Foreman-Mackey, D., Hogg, D.W., Lang, D., & Goodman, J. (2013). emcee: The MCMC hammer.
    Publications of the Astronomical Society of the Pacific, 125(925), 306-312.

    Vollmer, R. (1976). Rb-Sr and U-Th-Pb systematics of alkaline rocks. Geochimica et Cosmochimica
    Acta, 40(3), 283-295.

    Zindler, A., & Hart, S. (1986). Chemical geodynamics. Annual Review of Earth and Planetary
    Sciences, 14, 493-571.

    Hofmann, A.W. (1997). Mantle geochemistry: the message from oceanic volcanism. Nature, 385, 219-229.

    Salters, V.J.M., & Stracke, A. (2004). Composition of the depleted mantle. Geochemistry,
    Geophysics, Geosystems, 5(5), Q05004.

    Rudnick, R.L., & Gao, S. (2003). Composition of the continental crust. Treatise on Geochemistry,
    3, 1-64.

    McDonough, W.F., & Sun, S.S. (1995). The composition of the Earth. Chemical Geology,
    120(3-4), 223-253.

Sedimentology

    Dunham, R.J. (1962). Classification of carbonate rocks according to depositional texture.
    AAPG Memoir 1, 108-121.

    Folk, R.L. (1959). Practical petrographic classification of limestones. AAPG Bulletin, 43(1), 1-38.

    Folk, R.L. (1962). Spectral subdivision of limestone types. AAPG Memoir 1, 62-84.

    Dott, R.H. (1964). Wacke, graywacke and matrix — what approach to immature sandstone classification?
    Journal of Sedimentary Research, 34(3), 625-632.

    Pettijohn, F.J. (1975). Sedimentary Rocks (3rd ed.). Harper & Row.

    Wentworth, C.K. (1922). A scale of grade and class terms for clastic sediments.
    Journal of Geology, 30(5), 377-392.

    Shepard, F.P. (1954). Nomenclature based on sand-silt-clay ratios. Journal of Sedimentary
    Research, 24(3), 151-158.

    Folk, R.L., & Ward, W.C. (1957). Brazos River bar: a study in the significance of grain size
    parameters. Journal of Sedimentary Research, 27(1), 3-26.

    Blott, S.J., & Pye, K. (2001). GRADISTAT: A grain size distribution and statistics package.
    Earth Surface Processes and Landforms, 26(11), 1237-1248.

    Folk, R.L. (1974). Petrology of Sedimentary Rocks. Hemphill Publishing Company.

    Powers, M.C. (1953). A new roundness scale for sedimentary particles. Journal of Sedimentary
    Research, 23(2), 117-119.

    Weltje, G.J. (1997). End-member modeling of compositional data. Mathematical Geology, 29(4), 503-549.

Environmental Science

    Müller, G. (1969). Index of geoaccumulation in sediments of the Rhine River.
    GeoJournal, 2(3), 108-118.

    Zoller, W.H., Gladney, E.S., & Duce, R.A. (1974). Atmospheric concentrations and sources of
    trace metals at the South Pole. Science, 183(4121), 198-200.

    Hakanson, L. (1980). An ecological risk index for aquatic pollution control.
    Water Research, 14(8), 975-1001.

    Gromet, L.P., Dymek, R.F., Haskin, L.A., & Korotev, R.L. (1984). The "North American shale
    composite". Geochimica et Cosmochimica Acta, 48(12), 2469-2482.

    Taylor, S.R., & McLennan, S.M. (1995). The geochemical evolution of the continental crust.
    Reviews of Geophysics, 33(2), 241-265.

    Perin, G., et al. (1985). Heavy metal speciation in the sediments of Northern Adriatic Sea.
    Environmental Technology Letters, 6(12), 665-674.

    Tessier, A., Campbell, P.G.C., & Bisson, M. (1979). Sequential extraction procedure for the
    speciation of particulate trace metals. Analytical Chemistry, 51(7), 844-851.

    Potts, P.J., & West, M. (Eds.) (2008). Portable X-ray Fluorescence Spectrometry.
    Royal Society of Chemistry.

Soil Science

    USDA Natural Resources Conservation Service (1999). Soil Taxonomy (2nd ed.). USDA Handbook 436.

    FAO (2006). Guidelines for Soil Description (4th ed.). Food and Agriculture Organization of the
    United Nations.

    Brady, N.C., & Weil, R.R. (2016). The Nature and Properties of Soils (15th ed.). Pearson.

    USDA (1954). Diagnosis and Improvement of Saline and Alkali Soils. USDA Agricultural
    Handbook No. 60.

    Munsell Color (2000). Munsell Soil Color Charts. Gretag-Macbeth, New Windsor, NY.

Archaeology & Bioarchaeology

    DeNiro, M.J. (1985). Postmortem preservation and alteration of in vivo bone collagen isotope ratios.
    Nature, 317, 806-809.

    van Klinken, G.J. (1999). Bone collagen quality indicators for palaeodietary and radiocarbon
    measurements. Journal of Archaeological Science, 26(6), 687-695.

    Hedges, R.E.M., Millard, A.R., & Pike, A.W.G. (1995). Measurements and relationships of
    diagenetic alteration of bone from three archaeological sites. Journal of Archaeological
    Science, 22(2), 201-209.

    Schoeninger, M.J., DeNiro, M.J., & Tauber, H. (1983). Stable nitrogen isotope ratios of bone
    collagen reflect marine and terrestrial components of prehistoric human diet. Science,
    220(4604), 1381-1383.

    Weiner, S., & Bar-Yosef, O. (1990). States of preservation of bones from prehistoric sites in
    the Near East. Journal of Archaeological Science, 17(2), 187-196.

    Lee-Thorp, J.A. (2008). On isotopes and old bones. Archaeometry, 50(6), 925-950.

    Behrensmeyer, A.K. (1978). Taphonomic and ecologic information from bone weathering.
    Paleobiology, 4(2), 150-162.

    Shipman, P., & Rose, J. (1984). Cutmark mimics on modern and fossil bovid bones.
    Current Anthropology, 25(1), 116-117.

    von den Driesch, A. (1976). A Guide to the Measurement of Animal Bones from Archaeological Sites.
    Peabody Museum of Archaeology and Ethnology Bulletin 1.

    Grayson, D.K. (1984). Quantitative Zooarchaeology. Academic Press.

    Lyman, R.L. (2008). Quantitative Paleozoology. Cambridge University Press.

    Silver, I.A. (1969). The ageing of domestic animals. In Brothwell, D. & Higgs, E.S. (Eds.),
    Science in Archaeology (2nd ed.), 283-302. Thames and Hudson.

    Grant, A. (1982). The use of tooth wear as a guide to the age of domestic ungulates. In Wilson, B.,
    Grigson, C., & Payne, S. (Eds.), Ageing and Sexing Animal Bones from Archaeological Sites, 91-108.
    British Archaeological Reports.

    Reitz, E.J., & Wing, E.S. (2008). Zooarchaeology (2nd ed.). Cambridge University Press.

    Payne, S., & Bull, G. (1988). Components of variation in measurements of pig bones and teeth.
    Archaeozoologia, 2(1-2), 27-66.

    Stiner, M.C. (1990). The use of mortality patterns in archaeological studies of hominid predatory
    adaptations. Journal of Anthropological Archaeology, 9(4), 305-351.

    Klein, R.G., & Cruz-Uribe, K. (1984). The Analysis of Animal Bones from Archaeological Sites.
    University of Chicago Press.

    Kuhl, F.P., & Giardina, C.R. (1982). Elliptic Fourier features of a closed contour. Computer
    Vision, Graphics and Image Processing, 18(3), 236-258.

    Bookstein, F.L. (1991). Morphometric Tools for Landmark Data. Cambridge University Press.

Meteoritics

    Kallemeyn, G.W., Rubin, A.E., Wang, D., & Wasson, J.T. (1989). Ordinary chondrites: bulk
    compositions, classification, lithophile-element fractionations. Geochimica et Cosmochimica
    Acta, 53(11), 2747-2767.

    Weisberg, M.K., McCoy, T.J., & Krot, A.N. (2006). Systematics and evaluation of meteorite
    classification. In Lauretta, D.S. & McSween, H.Y. Jr. (Eds.), Meteorites and the Early Solar
    System II, 19-52. University of Arizona Press.

    Stöffler, D., Keil, K., & Scott, E.R.D. (1991). Shock metamorphism of ordinary chondrites.
    Geochimica et Cosmochimica Acta, 55(12), 3845-3867.

    Wlotzka, F. (1993). A weathering scale for the ordinary chondrites. Meteoritics, 28(3), 460.

    Clayton, R.N., & Mayeda, T.K. (1996). Oxygen isotope studies of achondrites.
    Geochimica et Cosmochimica Acta, 60(11), 1999-2017.

    Papike, J.J., Karner, J.M., & Shearer, C.K. (2003). Determination of planetary basalt parentage:
    a simple technique using the electron microprobe. American Mineralogist, 88(2-3), 469-472.

Archaeometallurgy

    Pernicka, E. (1999). Trace element fingerprinting of ancient copper: a guide to technology or
    provenance? In Young, S.M.M., et al. (Eds.), Metals in Antiquity, 163-171. BAR International.

    Craddock, P.T. (1978). The composition of the copper alloys used by the Greek, Etruscan and Roman
    civilizations. Journal of Archaeological Science, 5(1), 1-16.

    Scott, D.A. (1991). Metallography and Microstructure of Ancient and Historic Metals.
    The Getty Conservation Institute.

    Buchwald, V.F. (2005). Iron and Steel in Ancient Times. Det Kongelige Danske Videnskabernes Selskab.

    Bachmann, H.G. (1982). The Identification of Slags from Archaeological Sites.
    Institute of Archaeology Occasional Publication 6.

    Urbain, G., Bottinga, Y., & Richet, P. (1982). Viscosity of liquid silica, silicates and
    alumino-silicates. Geochimica et Cosmochimica Acta, 46(6), 1061-1072.

    Turkdogan, E.T. (1983). Physicochemical Properties of Molten Slags and Glasses. The Metals Society.

Hydrogeochemistry

    Piper, A.M. (1944). A graphic procedure in the geochemical interpretation of water-analyses.
    Eos, Transactions American Geophysical Union, 25(6), 914-928.

    Stiff, H.A. (1951). The interpretation of chemical water analysis by means of patterns.
    Journal of Petroleum Technology, 3(10), 15-17.

Provenance & Geochemical Fingerprinting

    Hartung, U. (2017). Egyptian basalt vessels in the southern Levant and Sinai during the 4th
    millennium BC. [Regional sourcing methodology]

    Philip, G., & Williams-Thorpe, O. (2001). A provenance study of basalt objects from Jordan.
    Levant, 33(1), 41-75.

    Williams-Thorpe, O., & Thorpe, R.S. (1993). Geochemistry and trade of eastern Mediterranean
    millstones from the Neolithic to Roman periods. Journal of Archaeological Science, 20(3), 263-320.

    Rosenberg, D., Shimelmitz, R., & Nativ, A. (2016). From tool to refuse: basalt vessel production
    and use. Quaternary International, 409, 86-98.

    Weiner, N., Gadot, Y., & Goren, Y. (2021). New geochemical reference data for basalt provenance
    studies in the southern Levant. Journal of Archaeological Science, 127, 105308.

    Weinstein-Evron, M., Ilani, S., & Kaufman, D. (2007). Late Quaternary basaltic eruptions in the
    Hula Basin, northern Israel. Journal of Volcanology and Geothermal Research, 159(1-3), 261-271.

    Mor, D. (1993). A time-table for the Levant Volcanic Province, according to K-Ar dating in the
    Golan Heights, Israel. Journal of African Earth Sciences, 16(3), 223-234.

Tectonic Discrimination & Petrogenetic Modeling

    Pearce, J.A., & Cann, J.R. (1973). Tectonic setting of basic volcanic rocks determined using trace
    element analyses. Earth and Planetary Science Letters, 19(2), 290-300.

    Pearce, J.A. (1982). Trace element characteristics of lavas from destructive plate boundaries.
    In Thorpe, R.S. (Ed.), Andesites, 525-548. Wiley.

    Meschede, M. (1986). A method of discriminating between different types of mid-ocean ridge basalts
    and continental tholeiites with the Nb-Zr-Y diagram. Chemical Geology, 56(3-4), 207-218.

    Fitton, J.G., Saunders, A.D., Norry, M.J., Hardarson, B.S., & Taylor, R.N. (1997). Thermal and
    chemical structure of the Iceland plume. Earth and Planetary Science Letters, 153(3-4), 197-208.

    DePaolo, D.J. (1981). Trace element and isotopic effects of combined wallrock assimilation and
    fractional crystallization. Earth and Planetary Science Letters, 53(2), 189-202.

    Mysen, B.O. (1988). Structure and Properties of Silicate Melts. Elsevier.

    Dingwell, D.B. (1996). Volcanic dilemma: flow or blow? Science, 273(5278), 1054-1055.

    Papale, P. (1999). Modeling of the solubility of a two-component H₂O+CO₂ fluid in silicate
    liquids. American Mineralogist, 84(4), 477-492.

Compositional Statistics & Spectroscopy

    Aitchison, J. (1982). The statistical analysis of compositional data. Journal of the Royal
    Statistical Society, Series B, 44(2), 139-177.

    Aitchison, J. (1986). The Statistical Analysis of Compositional Data. Chapman and Hall.

    Egozcue, J.J., Pawlowsky-Glahn, V., Mateu-Figueras, G., & Barceló-Vidal, C. (2003). Isometric
    logratio transformations for compositional data analysis. Mathematical Geology, 35(3), 279-300.

    Pawlowsky-Glahn, V., & Egozcue, J.J. (2006). Compositional data and their analysis: an introduction.
    Geological Society, London, Special Publications, 264(1), 1-10.

    Savitzky, A., & Golay, M.J.E. (1964). Smoothing and differentiation of data by simplified least
    squares procedures. Analytical Chemistry, 36(8), 1627-1639.

    Barnes, R.J., Dhanoa, M.S., & Lister, S.J. (1989). Standard normal variate transformation and
    de-trending of near-infrared diffuse reflectance spectra. Applied Spectroscopy, 43(5), 772-777.

    Martens, H., & Næs, T. (1989). Multivariate Calibration. Wiley.

    Tauler, R. (1995). Multivariate curve resolution applied to second order data. Chemometrics and
    Intelligent Laboratory Systems, 30(1), 133-146.

    Eilers, P.H.C., & Boelens, H.F.M. (2005). Baseline correction with asymmetric least squares
    smoothing. Leiden University Medical Centre Report.

Geophysics

    Loke, M.H., & Barker, R.D. (1996). Rapid least-squares inversion of apparent resistivity
    pseudosections by a quasi-Newton method. Geophysical Prospecting, 44(1), 131-152.

    Hinze, W.J., et al. (2005). New standards for reducing gravity data: the North American gravity
    database. Geophysics, 70(4), J25-J32.

    LaFehr, T.R. (1991). Standardization in gravity reduction. Geophysics, 56(8), 1170-1178.

    Reid, A.B., Allsop, J.M., Granser, H., Millet, A.J., & Somerton, I.W. (1990). Magnetic
    interpretation in three dimensions using Euler deconvolution. Geophysics, 55(1), 80-91.

    Caldwell, T.G., Bibby, H.M., & Brown, C. (2004). The magnetotelluric phase tensor.
    Geophysical Journal International, 158(2), 457-469.

    Taner, M.T., Koehler, F., & Sheriff, R.E. (1979). Complex seismic trace analysis.
    Geophysics, 44(6), 1041-1063.

    Marfurt, K.J., Kirlin, R.L., Farmer, S.L., & Bahorich, M.S. (1998). 3-D seismic attributes using
    a semblance-based coherency algorithm. Geophysics, 63(4), 1150-1165.

    Partyka, G., Gridley, J., & Lopez, J. (1999). Interpretational applications of spectral
    decomposition in reservoir characterization. The Leading Edge, 18(3), 353-360.

    Embree, P., Burg, J.P., & Backus, M.M. (1963). Wide-band velocity filtering — the pie-slice
    process. Geophysics, 28(6), 948-974.

    Yilmaz, Ö. (2001). Seismic Data Analysis: Processing, Inversion, and Interpretation of Seismic
    Data (2nd ed.). Society of Exploration Geophysicists.

    Conyers, L.B. (2013). Ground-Penetrating Radar for Archaeology (3rd ed.). AltaMira Press.

    Jol, H.M. (Ed.) (2008). Ground Penetrating Radar: Theory and Applications. Elsevier.

Materials Science

    Brunauer, S., Emmett, P.H., & Teller, E. (1938). Adsorption of gases in multimolecular layers.
    Journal of the American Chemical Society, 60(2), 309-319.

    Oliver, W.C., & Pharr, G.M. (1992). An improved technique for determining hardness and elastic
    modulus using load and displacement sensing indentation experiments. Journal of Materials
    Research, 7(6), 1564-1583.

    Basquin, O.H. (1910). The exponential law of endurance tests. Proceedings of the American Society
    for Testing Materials, 10, 625-630.

    Carreau, P.J. (1972). Rheological equations from molecular network theories. Transactions of the
    Society of Rheology, 16(1), 99-127.

    Ferguson, R.I., & Church, M. (2004). A simple universal equation for grain settling velocity.
    Journal of Sedimentary Research, 74(6), 933-937.

    Stokes, G.G. (1851). On the effect of the internal friction of fluids on the motion of pendulums.
    Transactions of the Cambridge Philosophical Society, 9, 8-106.

Molecular Biology & Clinical Diagnostics

    Livak, K.J., & Schmittgen, T.D. (2001). Analysis of relative gene expression data using real-time
    quantitative PCR and the 2⁻ΔΔCT method. Methods, 25(4), 402-408.

    Ramakers, C., Ruijter, J.M., Deprez, R.H.L., & Moorman, A.F.M. (2003). Assumption-free analysis
    of quantitative real-time PCR data. Neuroscience Letters, 339(1), 62-66.

    Ruijter, J.M., et al. (2009). Amplification efficiency: linking baseline and bias in the analysis
    of quantitative PCR data. Nucleic Acids Research, 37(6), e45.

    Pfaffl, M.W. (2001). A new mathematical model for relative quantification in real-time RT-PCR.
    Nucleic Acids Research, 29(9), e45.

    Hindson, B.J., et al. (2011). High-throughput droplet digital PCR system for absolute quantitation
    of DNA copy number. Analytical Chemistry, 83(22), 8604-8610.

    Ririe, K.M., Rasmussen, R.P., & Wittwer, C.T. (1997). Product differentiation by analysis of DNA
    melting curves during the polymerase chain reaction. Analytical Biochemistry, 245(2), 154-160.

    Herzenberg, L.A., et al. (2006). The history and future of the fluorescence activated cell sorter
    and flow cytometry. Clinical Chemistry, 52(6), 790-791.

    Zhang, J.H., Chung, T.D.Y., & Oldenburg, K.R. (1999). A simple statistical parameter for use in
    evaluation and validation of high throughput screening assays. Journal of Biomolecular Screening,
    4(2), 67-73.

    Meijering, E., Dzyubachyk, O., & Smal, I. (2012). Methods for cell and particle tracking.
    Methods in Enzymology, 504, 183-200.

    Waters, J.C. (2009). Accuracy and precision in quantitative fluorescence microscopy.
    Journal of Cell Biology, 185(7), 1135-1148.

Meteorology

    Allen, R.G., Pereira, L.S., Raes, D., & Smith, M. (1998). Crop evapotranspiration: Guidelines
    for computing crop water requirements. FAO Irrigation and Drainage Paper 56.

    World Meteorological Organization (2018). Guide to Climatological Practices (3rd ed.). WMO No. 100.

    Arguez, A., & Vose, R.S. (2011). The definition of the standard WMO climate normal. Bulletin of
    the American Meteorological Society, 92(6), 699-704.

Chromatography & Analytical Chemistry

    Kováts, E. (1958). Gas-chromatographische Charakterisierung organischer Verbindungen.
    Helvetica Chimica Acta, 41(7), 1915-1932.

    Foley, J.P., & Dorsey, J.G. (1984). Equations for calculation of chromatographic figures of merit
    for ideal and skewed peaks. Analytical Chemistry, 56(14), 2462-2470.

    Ernst, R.R., Bodenhausen, G., & Wokaun, A. (1987). Principles of Nuclear Magnetic Resonance in
    One and Two Dimensions. Clarendon Press.

    International Conference on Harmonisation (1994). Validation of Analytical Procedures.
    ICH Q2(R1).

    United States Pharmacopeia. USP <621> Chromatography. USP–NF.

Electrochemistry

    Bard, A.J., & Faulkner, L.R. (2001). Electrochemical Methods: Fundamentals and Applications
    (2nd ed.). Wiley.

    Orazem, M.E., & Tribollet, B. (2008). Electrochemical Impedance Spectroscopy. Wiley.

Ceramic & Glass Analysis

    Tite, M.S. (2008). Ceramic production, provenance and use — a review. Archaeometry, 50(2), 216-231.

    Sayre, E.V., & Smith, R.W. (1961). Compositional categories of ancient glass. Science, 133(3467),
    1824-1826.

    Freestone, I.C. (2006). Glass provenance and trade. In Killick, D. & Gordon, R.B. (Eds.),
    Handbook of Archaeological Methods. AltaMira Press.

    Lilyquist, C., & Brill, R.H. (1993). Studies in Early Egyptian Glass. Metropolitan Museum of Art.

    Quinn, P.S. (2013). Ceramic Petrography: The Interpretation of Archaeological Pottery and Related
    Artefacts in Thin Section. Archaeopress.

Analytical QA/QC

    Potts, P.J., & West, M. (Eds.) (2008). Portable X-ray Fluorescence Spectrometry: Capabilities
    for In Situ Analysis. Royal Society of Chemistry.

    IUPAC (1997). Compendium of Chemical Terminology (2nd ed.) — "Gold Book". Blackwell Scientific.

    ISO 17025:2017. General requirements for the competence of testing and calibration laboratories.
    International Organization for Standardization.

Statistical & Scientific Software

    Pearson, K. (1901). On lines and planes of closest fit to systems of points in space. The London,
    Edinburgh, and Dublin Philosophical Magazine and Journal of Science, 2(11), 559-572.

    Hotelling, H. (1933). Analysis of a complex of statistical variables into principal components.
    Journal of Educational Psychology, 24(6), 417-441.

    Harris, C.R., et al. (2020). Array programming with NumPy. Nature, 585(7825), 357-362.

    Virtanen, P., et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python.
    Nature Methods, 17(3), 261-272.

    Pedregosa, F., et al. (2011). Scikit-learn: machine learning in Python. Journal of Machine
    Learning Research, 12, 2825-2830.

    Jordahl, K., et al. (2020). geopandas/geopandas: v0.8.1. Zenodo.

    Bezanson, J., Edelman, A., Karpinski, S., & Shah, V.B. (2017). Julia: a fresh approach to
    numerical computing. SIAM Review, 59(1), 65-98.

See documentation/CITATIONS.md for the complete list with DOI links and implementation notes.


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

pip install numpy pandas matplotlib

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
Scientific Toolkit	Free	70 classifications + 10 protocols, 86 plugins, 16 hardware suites	Less polished UI, slower with large datasets

This toolkit is best for: Students, teaching labs, budget-constrained researchers, museums, cross-disciplinary projects, field work with portable instruments.

This toolkit is NOT for: Large-scale industrial mining operations (>10,000 samples), users needing enterprise support.

🗺️ Current Status & Roadmap

Current Version: 2.0 (February 2026)
✅ Stable Features

    70 classification engines (across 2 engines)

    10 scientific protocols for standardized workflows

    48 software plugins (full implementations)

    22 add-on plugins (plotting, consoles, AI)

    16 hardware suites supporting dozens of devices

    Publication templates (Nature, Science, AGU, Elsevier)

    Data import/export (CSV, Excel, JSON, KML)

🚧 Known Limitations

    Tkinter UI may look dated on modern systems

    Large datasets (>10,000 samples) may be slow

    Not all hardware tested on all platforms

    Protocols library currently contains 10 workflows (more planned)

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
Total Files	153+
Lines of Code	~77,000
Classification Engines	70
Scientific Protocols	10
Software Plugins	48
Add-on Plugins	22
Hardware Suites	16
Hardware Device Models	Dozens across suites
AI Assistants	7
Built-in Citations	200+
Journal Templates	8 categories

⬇️ Download Now | ⭐ Star on GitLab | 🐛 Report Bug
