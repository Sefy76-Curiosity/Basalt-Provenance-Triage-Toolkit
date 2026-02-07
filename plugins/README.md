Basalt Provenance Toolkit - Plugins Gallery (v10.1)

This directory contains the modular extensions for the Basalt Provenance Triage Toolkit. These plugins extend the core triage functionality into advanced geochemistry, 3D spatial analysis, and publication-quality reporting.
🧪 Geochemical & Discrimination Modules
Discrimination Diagrams

Implements classical tectonic setting plots to identify the magmatic environment of basalt samples.

    Key Plots: Pearce-Cann (Ti-Zr-Y), Wood (Th-Hf-Ta), and Shervais (Ti-V).

    Utility: Essential for determining if a source is Mid-Ocean Ridge (MORB), Island Arc, or Within-Plate.

Spider & REE Diagrams

Visualizes trace element patterns normalized to standard geological reservoirs.

    Normalization: Primitive Mantle (McDonough & Sun, 1995) and Chondrite.

    Utility: Identifying enrichment/depletion trends and subduction-related "Nb-Ta holes."

Ternary Diagrams

Igneous petrology plots for classification.

    Key Plots: AFM (Alkali-Iron-Magnesium) diagrams to distinguish Tholeiitic from Calc-alkaline suites.

📊 Statistical & Data Modules
Advanced Statistics (SPSS/R)

High-level multivariate statistics without requiring external software.

    Features: Principal Component Analysis (PCA), K-Means Clustering, and Discriminant Function Analysis (DFA).

    Engine: Powered by scikit-learn and scipy.

Literature Comparison

A specialized module to compare your pXRF/ICP-MS data against a built-in database of published Levantine and Egyptian basalt studies (e.g., Hartung, Rosenberg).
Data Validation Wizard

An "IoGAS-style" quality control tool.

    Features: Outlier detection (Z-score), missing value reports, and geochemical consistency checks.

🌍 Spatial & GIS Modules
3D/GIS Viewer

Advanced spatial visualization for excavation mapping.

    Interactive Maps: Generates HTML maps via Folium.

    3D Scatter: Visualizes sample distribution in 3D space using PyVista.

Google Earth Export

Converts sample coordinates and metadata into KML/KMZ files. Includes Tiers for basic plotting and advanced 3D terrain integration.
📝 Utility & Reporting
Report Generator

Automates the creation of formal excavation season reports and IAA (Israel Antiquities Authority) submission drafts in .docx format.
Photo Manager

Links laboratory and field photography directly to the geochemical database for rapid visual reference.
Advanced Export

Generates high-resolution, publication-ready graphics in PDF, EPS, and SVG formats.
🛠 Installation of Dependencies

Most plugins require specific libraries. You can install all of them at once from the root directory:
Bash

pip install -r requirements.txt

Note: If a plugin is missing a requirement, the Plugin Manager will safely disable it and provide installation instructions within the app.

Author: Sefy Levy

License: CC BY-NC-SA 4.0

Archive: Zenodo DOI: 10.5281/zenodo.18499129
