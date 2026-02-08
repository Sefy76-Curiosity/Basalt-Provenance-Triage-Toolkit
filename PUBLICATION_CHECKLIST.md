# ✅ PUBLICATION CHECKLIST - Archaeological Basalt Provenance Studies

**Use this checklist before submitting your manuscript to ensure journal-quality geochemical data reporting.**

---

## 📋 BEFORE YOU START ANALYSIS

### **Data Collection Requirements**

- [ ] **pXRF measurements taken in triplicate** (minimum)
- [ ] **Reference standards measured** (certified basalt standards)
- [ ] **Duplicate samples analyzed** (at least 10% of dataset)
- [ ] **Blank measurements recorded** (background correction)
- [ ] **Instrument metadata documented**:
  - [ ] pXRF make and model (e.g., "Bruker S1 Titan")
  - [ ] Measurement time per spot (e.g., "60 seconds")
  - [ ] Beam settings (voltage, current, filter)
  - [ ] Calibration date
  - [ ] Software version

### **Sample Documentation**

- [ ] **Unique sample IDs assigned**
- [ ] **Archaeological context recorded**:
  - [ ] Site name
  - [ ] Excavation area/square
  - [ ] Stratigraphic layer
  - [ ] Excavation date
  - [ ] Excavator name
- [ ] **Artifact type documented** (vessel wall, tool, core, etc.)
- [ ] **Photos taken** (link to Sample_ID)
- [ ] **Museum accession numbers** (if applicable)

---

## 🔬 DATA QUALITY CHECKS

### **Step 1: Import and Validate**

```
Tools Required:
- Main App: Analysis → Detection Limit (BDL) Handler
- Plugin: Data Validation (optional but recommended)
```

- [ ] **Import pXRF data** with all elements (Zr, Nb, Ba, Rb, Cr, Ni minimum)
- [ ] **Add error columns**:
  - [ ] Zr_ppm_error
  - [ ] Nb_ppm_error
  - [ ] Ba_ppm_error
  - [ ] Rb_ppm_error
  - [ ] Cr_ppm_error
  - [ ] Ni_ppm_error
- [ ] **Flag BDL values**:
  - [ ] Document detection limits for each element
  - [ ] Use DL/2 substitution method (most common)
  - [ ] Mark BDL samples in dedicated columns
- [ ] **Run validation wizard** (if using plugin):
  - [ ] Check for impossible ratios (e.g., Zr < Nb)
  - [ ] Detect outliers
  - [ ] Flag suspicious Cr/Ni ratios

### **Step 2: Add QA/QC Metadata**

- [ ] **Mark sample types**:
  - [ ] Standards (use QC_Sample_Type = "Standard")
  - [ ] Duplicates (use QC_Sample_Type = "Duplicate")
  - [ ] Blanks (use QC_Sample_Type = "Blank")
  - [ ] Unknown artifacts (use QC_Sample_Type = "Unknown")
- [ ] **Set data quality flags**:
  - [ ] Good (measurements within specs)
  - [ ] Suspect (near detection limits, high error)
  - [ ] Bad (exclude from analysis)
- [ ] **Document instrument conditions**:
  - [ ] Fill in Instrument_Model column
  - [ ] Fill in Measurement_Time_sec column

---

## 📊 STATISTICAL ANALYSIS

### **Step 3: Calculate Derived Values**

```
Main App: Analysis Menu
```

- [ ] **Calculate error propagation**:
  - [ ] Zr/Nb ratio errors → Analysis → Calculate Error Propagation
  - [ ] Cr/Ni ratio errors → Analysis → Calculate Error Propagation
  - [ ] Report formula used: σ(A/B) = (A/B) × √[(σA/A)² + (σB/B)²]

- [ ] **Unit conversions** (if reporting wt%):
  - [ ] ppm → wt% → Analysis → Unit Converter
  - [ ] Document oxide factors used (ZrO₂, Nb₂O₅, etc.)
  - [ ] Major elements to 100% → Analysis → Normalize Major Elements

### **Step 4: Classification**

```
Main App: Edit → Classify All
```

- [ ] **Run automatic classification**
- [ ] **Review confidence scores**:
  - [ ] Confidence 5 = accept automatically
  - [ ] Confidence 3-4 = review manually
  - [ ] Confidence 1-2 = flag for further investigation
- [ ] **Manually review flagged samples**
- [ ] **Document classification criteria** (cite thresholds used)

### **Step 5: Statistical Validation**

```
Required Plugin: Statistical Analysis
Install: Tools → Manage Plugins → Statistical Analysis
```

- [ ] **Run PCA**:
  - [ ] Include all discriminating elements (Zr, Nb, Ba, Rb, Cr, Ni)
  - [ ] Capture ≥70% variance in first 2-3 components
  - [ ] Generate PCA biplot for publication
- [ ] **Run Discriminant Function Analysis (DFA)**:
  - [ ] Test classification accuracy via cross-validation
  - [ ] Aim for ≥75% classification accuracy
  - [ ] Report mean accuracy ± std dev
  - [ ] Include LDA plot showing group separation
- [ ] **Optional: Cluster Analysis**:
  - [ ] Run k-means or hierarchical clustering
  - [ ] Compare to a priori classifications
  - [ ] Include dendrogram if relevant

---

## 📈 VISUALIZATION FOR PUBLICATION

### **Step 6: Create Required Diagrams**

```
Main App: Plots Menu
```

**REQUIRED DIAGRAMS:**

- [ ] **TAS Diagram** (Total Alkali vs Silica):
  - [ ] Plots → TAS Diagram
  - [ ] Shows rock classification (basalt, andesite, etc.)
  - [ ] Color-code by provenance group
  - [ ] Export as high-res PNG (300+ DPI)

- [ ] **Spider Diagram** (Normalized Multi-Element):
  - [ ] Plots → Spider Diagram
  - [ ] Use Primitive Mantle normalization (most common)
  - [ ] Show all provenance groups on one plot
  - [ ] Export as high-res PNG

- [ ] **Discrimination Diagram** (Pearce or Wood):
  - [ ] Plots → Pearce Discrimination Diagrams
  - [ ] Ti-Zr-Y ternary (standard for basalt)
  - [ ] Shows tectonic setting fields (MORB, Arc, WPB, etc.)
  - [ ] Export as high-res PNG

**OPTIONAL BUT RECOMMENDED:**

- [ ] **Harker Variation Diagrams**:
  - [ ] Plots → Harker Variation Diagrams
  - [ ] Major elements vs SiO₂
  - [ ] Shows geochemical trends

- [ ] **Binary Discrimination Plots**:
  - [ ] Custom X vs Y plots (e.g., Zr/Nb vs Cr/Ni)
  - [ ] Use to show provenance-specific fields

---

## 📄 DATA REPORTING

### **Step 7: Prepare Data Tables**

- [ ] **Main Data Table** (Appendix or Supplementary):
  - [ ] Sample_ID
  - [ ] All elements with ± errors (e.g., "125 ± 5 ppm")
  - [ ] BDL flags (note which values below detection)
  - [ ] Classification result
  - [ ] Confidence score

- [ ] **Summary Statistics Table**:
  - [ ] Mean ± std dev for each provenance group
  - [ ] Min/max values
  - [ ] n = sample count

- [ ] **QA/QC Table**:
  - [ ] Reference standard measurements
  - [ ] Duplicate analysis results (% reproducibility)
  - [ ] Detection limits for each element

### **Step 8: Export**

```
Main App: File → Export
OR Plugin: Report Generator
```

- [ ] **Export full dataset** → File → Export pXRF
  - [ ] Include all error columns
  - [ ] Include BDL flags
  - [ ] Include metadata

- [ ] **Generate publication table** → File → Export Pub Table
  - [ ] Formatted for journal style
  - [ ] Significant figures appropriate (e.g., ±0.1 ppm for trace)

- [ ] **Optional: PDF Report** (if using plugin):
  - [ ] Tools → Manage Plugins → Report Generator
  - [ ] One-click automated report
  - [ ] Includes all tables and figures

---

## ✍️ MANUSCRIPT WRITING

### **Step 9: Methods Section**

**REQUIRED INFORMATION:**

- [ ] **Sample description**:
  - [ ] "A total of N basalt artifacts were analyzed..."
  - [ ] Site locations, archaeological context
  - [ ] Artifact types

- [ ] **Analytical methods**:
  - [ ] pXRF make/model
  - [ ] Measurement conditions (time, settings)
  - [ ] Elements analyzed
  - [ ] Detection limits reported
  - [ ] Error estimation method

- [ ] **Data processing**:
  - [ ] Software used (cite this toolkit!)
  - [ ] BDL substitution method (e.g., "DL/2")
  - [ ] Unit conversions performed
  - [ ] Normalization procedures

- [ ] **Classification criteria**:
  - [ ] Thresholds used (e.g., "Zr/Nb > 22 for Haddadin Flow")
  - [ ] Reference to established classification schemes
  - [ ] Cite relevant literature

- [ ] **Statistical analysis**:
  - [ ] "PCA was performed using..."
  - [ ] "DFA cross-validation yielded X% accuracy..."
  - [ ] "Groups were statistically distinct (p < 0.05)"

### **Step 10: Results Section**

- [ ] **Report classification results**:
  - [ ] "X% of artifacts classified as Haddadin Flow..."
  - [ ] Confidence scores mentioned
  - [ ] Ambiguous samples discussed

- [ ] **Present statistical outcomes**:
  - [ ] PCA variance explained
  - [ ] DFA accuracy results
  - [ ] Group separation metrics

- [ ] **Reference figures**:
  - [ ] "Figure 1 shows TAS diagram..."
  - [ ] "Figure 2 spider diagram demonstrates..."
  - [ ] "Figure 3 PCA biplot reveals..."

---

## 🔍 PEER REVIEW PREPARATION

### **Step 11: Anticipate Reviewer Questions**

**BE READY TO ANSWER:**

- [ ] "How were detection limits handled?"
  → **Answer**: "BDL values substituted with DL/2 (cite method)"

- [ ] "What are the measurement uncertainties?"
  → **Answer**: "Error bars shown in Table X, calculated via error propagation"

- [ ] "How reproducible are the classifications?"
  → **Answer**: "DFA cross-validation: X% accuracy ± Y%"

- [ ] "Were QA/QC samples analyzed?"
  → **Answer**: "Reference standards and duplicates (Table X)"

- [ ] "How do your data compare to published sources?"
  → **Answer**: "Consistent with [citation] for Haddadin Flow basalt"

- [ ] "Can you show the raw data?"
  → **Answer**: "Supplementary Table includes all measurements with ± errors"

---

## 📚 CITATION

**Don't forget to cite the software!**

```
Levy, S. (2026). Basalt Provenance Triage Toolkit v10.1 Professional: 
An open-source geochemical analysis platform for archaeological basalt 
provenance studies. Available at: [URL/DOI]
```

**And cite relevant methodological papers:**

- Le Bas et al. (1986) for TAS diagram
- McDonough & Sun (1995) for normalization values
- Pearce & Cann (1973) for discrimination diagrams
- Your specific classification scheme (e.g., Haddadin Flow criteria)

---

## ✅ FINAL CHECKLIST

**Before submission:**

- [ ] All figures at 300+ DPI
- [ ] Error bars on all measurements
- [ ] BDL values documented
- [ ] QA/QC data included
- [ ] Statistical validation performed
- [ ] Methods section complete
- [ ] Software cited
- [ ] Supplementary data uploaded
- [ ] Reviewers will be IMPRESSED! 🎉

---

## 🏆 JOURNAL-SPECIFIC REQUIREMENTS

### **Common Archaeology Journals:**

**Journal of Archaeological Science**
- Requires: Full geochemical data in supplementary
- Format: Excel or CSV with metadata
- Figures: 300 DPI minimum, TIFF or PNG

**Archaeometry**
- Requires: Statistical validation (PCA/DFA)
- Format: Detailed methodology
- Figures: Vector preferred (SVG/EPS) or high-res raster

**Geoarchaeology**
- Requires: Geochemical context discussion
- Format: Comparative data (literature values)
- Figures: Clear provenance discrimination

**ALWAYS check journal-specific author guidelines!**

---

**Good luck with your publication!** 📄🏆

If this checklist helps you get published, please:
- ⭐ Star the project
- 💌 Send a thank-you note
- 📧 Share your paper (we love success stories!)

**Happy publishing!** 🎓

