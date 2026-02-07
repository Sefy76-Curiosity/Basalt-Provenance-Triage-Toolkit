# Basalt Provenance Triage Toolkit (v10.1) 🌋

**A specialized analytical suite for the geochemical and typological classification of archaeological basalt artifacts.**

---

## 📖 Overview
The **Basalt Provenance Triage Toolkit** is an integrated software environment designed to bridge the gap between raw geochemical data (pXRF, ICP-MS) and archaeological interpretation. Specifically optimized for Early Bronze Age (EBA I) studies in Egypt and the Levant, it allows researchers to perform high-level "triage" on artifacts to assign regional provenance.

### Theoretical Framework
This toolkit is the primary analytical engine for the **Richat-Nile Hypothesis**, exploring climate-forced migration and technological anomalies in Predynastic Egypt.
* **Hypothesis Record:** [10.5281/zenodo.18472417](https://doi.org/10.5281/zenodo.18472417)
* **Software Archive:** [10.5281/zenodo.18518114](https://doi.org/10.5281/zenodo.18518114)

---

## 🚀 Key Modules & Plugins
The software features a modular architecture managed by a dynamic **Plugin Manager**.

### 📊 Geochemical Analysis
* **Literature Comparison:** Instantly compare your samples against a built-in database of published benchmarks (Hartung 2017, Rosenberg, etc.).
* **Discrimination Diagrams:** Generate tectonic setting plots including Pearce-Cann, Wood, and Shervais.
* **Spider/REE Diagrams:** Multi-element normalization against Primitive Mantle (McDonough & Sun) and Chondrite.
* **Ternary Plots:** Classic petrological diagrams (AFM, etc.) using `mpltern`.



### 🌍 Spatial & 3D Visualization
* **3D/GIS Viewer:** Interactive scatter plots and map visualizations without requiring external GIS software.
* **Google Earth Export:** Direct KML/KMZ generation for 3D terrain visualization of sample locations.

### 📈 Advanced Statistics
* **SPSS/R Suite:** Multivariate analysis including PCA (Principal Component Analysis), K-Means Clustering, and ANOVA.
* **Data Validation:** IoGAS-style quality checks, outlier detection, and Z-score analysis.

### 📄 Professional Reporting
* **Report Generator:** Automated generation of excavation season summaries and IAA (Israel Antiquities Authority) submission drafts in `.docx` format.
* **Photo Manager:** Link and organize high-resolution field photography with geochemical records.

---

## 🛠 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Sefy-Levy/Basalt-Provenance-Toolkit.git](https://github.com/Sefy-Levy/Basalt-Provenance-Toolkit.git)
   cd Basalt-Provenance-Toolkit
2. Install dependencies: pip install -r requirements.txt
3. Run the application: python Basalt_Provenance_Triage_Toolkit.py

📂 Repository Structure
    Basalt_Provenance_Triage_Toolkit.py: The main GUI application.
    /plugins: Contains all .py modules for advanced analysis.
    requirements.txt: List of necessary Python libraries.
    sample.csv: Example dataset to test all toolkit features.

📜 Citation & License
If you use this toolkit in your research, please cite:
Sefy Levy (2026). Basalt Provenance Triage Toolkit (Version 10.1). Zenodo. https://doi.org/10.5281/zenodo.18518114
License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).

Author: Sefy Levy
Contact: sefy76@gmail.com
