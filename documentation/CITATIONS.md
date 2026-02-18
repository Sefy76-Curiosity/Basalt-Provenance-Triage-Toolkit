# 📚 Citations & References

Scientific Toolkit implements published scientific methods. This document provides complete citations for all implemented classification schemes, normalization values, and analytical methods.

**If you use Scientific Toolkit in your research**, please cite both this software and the relevant original publications listed below.

---

## ⚠️ User Responsibility

**IMPORTANT: This software is provided "AS IS" without warranty.**

While we implement published methods as accurately as possible:
- **YOU are responsible for validating results** for your specific samples
- **YOU must verify** the methods are appropriate for your data
- **YOU should cross-check** critical results with other tools or methods
- **YOU must understand** the limitations of each classification scheme

Read the original publications before using any classification engine. Understand what the method does, its assumptions, and its limitations.

**Report bugs and unexpected results:** https://gitlab.com/sefy76/scientific-toolkit/-/issues

---

## How to Cite This Software

```
Levy, S. (2026). Scientific Toolkit v2.0 [Computer software].
Based on Basalt Provenance Triage Toolkit v10.2.
GitLab: https://gitlab.com/sefy76/scientific-toolkit
License: CC BY-NC-SA 4.0
```

**BibTeX:**
```bibtex
@software{levy2026scientific,
  author = {Levy, Sefy},
  title = {Scientific Toolkit v2.0},
  year = {2026},
  note = {Based on Basalt Provenance Triage Toolkit v10.2},
  url = {https://gitlab.com/sefy76/scientific-toolkit},
  license = {CC BY-NC-SA 4.0}
}
```

---

## Geochemistry & Petrology

### TAS Diagram (Total Alkali vs Silica)

**Le Bas, M. J., Le Maitre, R. W., Streckeisen, A., & Zanettin, B. (1986).**  
*A chemical classification of volcanic rocks based on the total alkali-silica diagram.*  
Journal of Petrology, 27(3), 745-750.  
DOI: [10.1093/petrology/27.3.745](https://doi.org/10.1093/petrology/27.3.745)

**Le Maitre, R. W., Bateman, P., Dudek, A., Keller, J., Lameyre, J., Le Bas, M. J., ... & Zanettin, B. (1989).**  
*A classification of igneous rocks and glossary of terms.*  
Blackwell Scientific Publications, Oxford.

**Implemented in:**
- `engines/more_classifications/tas_full_volcanic_classification.json`
- `engines/more_classifications/total_alkali_vs_silica_(tas_polygons).json`

---

### AFM Diagram (Alkali-FeO-MgO)

**Irvine, T. N., & Baragar, W. R. A. (1971).**  
*A guide to the chemical classification of the common volcanic rocks.*  
Canadian Journal of Earth Sciences, 8(5), 523-548.  
DOI: [10.1139/e71-055](https://doi.org/10.1139/e71-055)

**Implemented in:**
- `engines/more_classifications/afm_irvine–baragar_series.json`

---

### K₂O-SiO₂ Diagram

**Peccerillo, A., & Taylor, S. R. (1976).**  
*Geochemistry of Eocene calc-alkaline volcanic rocks from the Kastamonu area, Northern Turkey.*  
Contributions to Mineralogy and Petrology, 58(1), 63-81.  
DOI: [10.1007/BF00384745](https://doi.org/10.1007/BF00384745)

**Implemented in:**
- `engines/more_classifications/K₂O–SiO₂_volcanic_series.json`

---

### Pearce Element Ratio Diagrams

**Pearce, J. A. (1968).**  
*A contribution to the theory of variation diagrams.*  
Contributions to Mineralogy and Petrology, 19(2), 142-157.  
DOI: [10.1007/BF00635485](https://doi.org/10.1007/BF00635485)

**Pearce, J. A., & Cann, J. R. (1973).**  
*Tectonic setting of basic volcanic rocks determined using trace element analyses.*  
Earth and Planetary Science Letters, 19(2), 290-300.  
DOI: [10.1016/0012-821X(73)90129-5](https://doi.org/10.1016/0012-821X(73)90129-5)

**Pearce, J. A., Harris, N. B., & Tindle, A. G. (1984).**  
*Trace element discrimination diagrams for the tectonic interpretation of granitic rocks.*  
Journal of Petrology, 25(4), 956-983.  
DOI: [10.1093/petrology/25.4.956](https://doi.org/10.1093/petrology/25.4.956)

**Implemented in:**
- `engines/classification/pearce_mantle_array.json`

---

### Rare Earth Element (REE) Normalization

**Sun, S. S., & McDonough, W. F. (1989).**  
*Chemical and isotopic systematics of oceanic basalts: implications for mantle composition and processes.*  
Geological Society, London, Special Publications, 42(1), 313-345.  
DOI: [10.1144/GSL.SP.1989.042.01.19](https://doi.org/10.1144/GSL.SP.1989.042.01.19)

**McDonough, W. F., & Sun, S. S. (1995).**  
*The composition of the Earth.*  
Chemical Geology, 120(3-4), 223-253.  
DOI: [10.1016/0009-2541(94)00140-4](https://doi.org/10.1016/0009-2541(94)00140-4)

**Boynton, W. V. (1984).**  
*Cosmochemistry of the rare earth elements: meteorite studies.*  
In: Henderson, P. (Ed.), Rare Earth Element Geochemistry. Elsevier, pp. 63-114.

**Implemented in:**
- `engines/more_classifications/rare_earth_element.json`
- REE normalization templates with chondrite values

---

### Chemical Index of Alteration (CIA)

**Nesbitt, H. W., & Young, G. M. (1982).**  
*Early Proterozoic climates and plate motions inferred from major element chemistry of lutites.*  
Nature, 299(5885), 715-717.  
DOI: [10.1038/299715a0](https://doi.org/10.1038/299715a0)

**Implemented in:**
- `engines/classification/chemical_index_alteration.json`

---

### Normative Mineralogy (CIPW Norm)

**Cross, W., Iddings, J. P., Pirsson, L. V., & Washington, H. S. (1902).**  
*A quantitative chemico-mineralogical classification and nomenclature of igneous rocks.*  
Journal of Geology, 10(6), 555-690.

**Implemented in:**
- `engines/classification/normative_molar_proportions.json`
- `plugins/software/advanced_normative_calculations.py`

---

## Archaeology & Bioarchaeology

### Bone Diagenesis and Preservation

**Hedges, R. E. M., Millard, A. R., & Pike, A. W. G. (1995).**  
*Measurements and relationships of diagenetic alteration of bone from three archaeological sites.*  
Journal of Archaeological Science, 22(2), 201-209.  
DOI: [10.1006/jasc.1995.0022](https://doi.org/10.1006/jasc.1995.0022)

**Nielsen-Marsh, C. M., & Hedges, R. E. M. (2000).**  
*Patterns of diagenesis in bone I: the effects of site environments.*  
Journal of Archaeological Science, 27(12), 1139-1150.  
DOI: [10.1006/jasc.1999.0537](https://doi.org/10.1006/jasc.1999.0537)

**Weiner, S., & Bar-Yosef, O. (1990).**  
*States of preservation of bones from prehistoric sites in the Near East: A survey.*  
Journal of Archaeological Science, 17(2), 187-196.  
DOI: [10.1016/0305-4403(90)90058-D](https://doi.org/10.1016/0305-4403(90)90058-D)

**Implemented in:**
- `engines/more_classifications/bone_diagenesis_apatite.json`
- `engines/more_classifications/bone_collagen_qc.json`

---

### Stable Isotope Dietary Reconstruction

**DeNiro, M. J., & Epstein, S. (1978).**  
*Influence of diet on the distribution of carbon isotopes in animals.*  
Geochimica et Cosmochimica Acta, 42(5), 495-506.  
DOI: [10.1016/0016-7037(78)90199-0](https://doi.org/10.1016/0016-7037(78)90199-0)

**DeNiro, M. J., & Epstein, S. (1981).**  
*Influence of diet on the distribution of nitrogen isotopes in animals.*  
Geochimica et Cosmochimica Acta, 45(3), 341-351.  
DOI: [10.1016/0016-7037(81)90244-1](https://doi.org/10.1016/0016-7037(81)90244-1)

**Schoeninger, M. J., & DeNiro, M. J. (1984).**  
*Nitrogen and carbon isotopic composition of bone collagen from marine and terrestrial animals.*  
Geochimica et Cosmochimica Acta, 48(4), 625-639.  
DOI: [10.1016/0016-7037(84)90091-7](https://doi.org/10.1016/0016-7037(84)90091-7)

**Ambrose, S. H., & Norr, L. (1993).**  
*Experimental evidence for the relationship of the carbon isotope ratios of whole diet and dietary protein to those of bone collagen and carbonate.*  
In: Lambert, J. B., & Grupe, G. (Eds.), Prehistoric Human Bone. Springer, pp. 1-37.

**Implemented in:**
- `engines/more_classifications/stable_isotope_diet.json`
- `engines/more_classifications/bone_trophic_diet.json`

---

### FTIR Bone Crystallinity Index

**Weiner, S., & Bar-Yosef, O. (1990).**  
*States of preservation of bones from prehistoric sites in the Near East: A survey.*  
Journal of Archaeological Science, 17(2), 187-196.  
DOI: [10.1016/0305-4403(90)90058-D](https://doi.org/10.1016/0305-4403(90)90058-D)

**Surovell, T. A., & Stiner, M. C. (2001).**  
*Standardizing infra-red measures of bone mineral crystallinity: an experimental approach.*  
Journal of Archaeological Science, 28(6), 633-642.  
DOI: [10.1006/jasc.2000.0633](https://doi.org/10.1006/jasc.2000.0633)

**Implemented in:**
- `engines/more_classifications/ftir_crystallinity_index.json`

---

## Material Science

### Ceramic Firing Temperature

**Maggetti, M. (1982).**  
*Phase analysis and its significance for technology and origin.*  
In: Olin, J. S., & Franklin, A. D. (Eds.), Archaeological Ceramics. Smithsonian Institution Press, pp. 121-133.

**Tite, M. S. (2008).**  
*Ceramic production, provenance and use—a review.*  
Archaeometry, 50(2), 216-231.  
DOI: [10.1111/j.1475-4754.2008.00391.x](https://doi.org/10.1111/j.1475-4754.2008.00391.x)

**Implemented in:**
- `engines/more_classifications/ceramic_firing_temperature_proxies.json`

---

### Glass Compositional Classification

**Henderson, J. (1985).**  
*The raw materials of early glass production.*  
Oxford Journal of Archaeology, 4(3), 267-291.  
DOI: [10.1111/j.1468-0092.1985.tb00248.x](https://doi.org/10.1111/j.1468-0092.1985.tb00248.x)

**Freestone, I. C., Greenwood, R., & Gorin-Rosen, Y. (2002).**  
*Byzantine and Early Islamic glassmaking in the Eastern Mediterranean: production and distribution of primary glass.*  
In: Kordas, G. (Ed.), Hyalos-Vitrum-Glass. AIHV, Athens, pp. 167-174.

**Implemented in:**
- `engines/more_classifications/glass_compositional_families.json`

---

### Slag Basicity Index

**Turkdogan, E. T. (1983).**  
*Physicochemical properties of molten slags and glasses.*  
The Metals Society, London.

**Implemented in:**
- `engines/classification/slag_basicity_index.json`

---

## Environmental Science

### USDA Soil Texture Classification

**Soil Survey Staff. (1951).**  
*Soil Survey Manual.*  
USDA Handbook No. 18. U.S. Department of Agriculture, Washington, DC.

**Soil Survey Division Staff. (1993).**  
*Soil Survey Manual.*  
USDA Handbook No. 18. U.S. Department of Agriculture, Washington, DC.

**USDA Natural Resources Conservation Service. (2017).**  
*Soil Survey Manual.*  
USDA Handbook No. 18. Government Printing Office, Washington, DC.

**Implemented in:**
- `engines/more_classifications/usda_soil_texture_classification.json`
- `engines/more_classifications/usda_soil_texture_triangle_(full).json`

---

### Geoaccumulation Index (Igeo)

**Müller, G. (1969).**  
*Index of geoaccumulation in sediments of the Rhine River.*  
GeoJournal, 2(3), 108-118.

**Müller, G. (1981).**  
*Die Schwermetallbelastung der sedimente des Neckars und seiner Nebenflüsse: eine Bestandsaufnahme.*  
Chemiker Zeitung, 105, 157-164.

**Implemented in:**
- `engines/more_classifications/geoaccumulation_index_igeo.json`

---

### Soil Salinity and Sodicity

**Richards, L. A. (Ed.). (1954).**  
*Diagnosis and improvement of saline and alkali soils.*  
USDA Agriculture Handbook No. 60. U.S. Department of Agriculture, Washington, DC.

**Implemented in:**
- `engines/more_classifications/soil_salinity_classification_(ec).json`
- `engines/more_classifications/soil_sodicity_(sar).json`

---

### Water Hardness Classification

**World Health Organization (WHO). (2011).**  
*Guidelines for drinking-water quality* (4th ed.).  
WHO Press, Geneva, Switzerland.

**Sawyer, C. N., & McCarty, P. L. (1967).**  
*Chemistry for sanitary engineers* (2nd ed.).  
McGraw-Hill, New York.

**Implemented in:**
- `engines/more_classifications/water_hardness.json`

---

### Sediment Grain Size (Wentworth Scale)

**Wentworth, C. K. (1922).**  
*A scale of grade and class terms for clastic sediments.*  
Journal of Geology, 30(5), 377-392.  
DOI: [10.1086/622910](https://doi.org/10.1086/622910)

**Krumbein, W. C., & Sloss, L. L. (1963).**  
*Stratigraphy and sedimentation* (2nd ed.).  
W. H. Freeman, San Francisco.

**Implemented in:**
- `engines/more_classifications/sediment_grain_Size.json`

---

## Meteorites & Planetary Science

### Meteorite Classification

**Weisberg, M. K., McCoy, T. J., & Krot, A. N. (2006).**  
*Systematics and evaluation of meteorite classification.*  
In: Lauretta, D. S., & McSween, H. Y. (Eds.), Meteorites and the Early Solar System II. University of Arizona Press, pp. 19-52.

**Krot, A. N., Keil, K., Scott, E. R. D., Goodrich, C. A., & Weisberg, M. K. (2014).**  
*Classification of meteorites and their genetic relationships.*  
In: Davis, A. M. (Ed.), Treatise on Geochemistry (2nd ed.), Vol. 1. Elsevier, pp. 1-63.  
DOI: [10.1016/B978-0-08-095975-7.00102-9](https://doi.org/10.1016/B978-0-08-095975-7.00102-9)

**Implemented in:**
- `engines/more_classifications/chondrite_meteorite.json`

---

### Meteorite Shock Classification

**Stöffler, D., Keil, K., & Scott, E. R. D. (1991).**  
*Shock metamorphism of ordinary chondrites.*  
Geochimica et Cosmochimica Acta, 55(12), 3845-3867.  
DOI: [10.1016/0016-7037(91)90078-J](https://doi.org/10.1016/0016-7037(91)90078-J)

**Implemented in:**
- `engines/more_classifications/meteorite_shock_stage.json`

---

### Meteorite Weathering

**Wlotzka, F. (1993).**  
*A weathering scale for the ordinary chondrites.*  
Meteoritics, 28(3), 460.

**Rubin, A. E., Trigo-Rodríguez, J. M., Huber, H., & Wasson, J. T. (2007).**  
*Progressive aqueous alteration of CM carbonaceous chondrites.*  
Geochimica et Cosmochimica Acta, 71(9), 2361-2382.  
DOI: [10.1016/j.gca.2007.02.008](https://doi.org/10.1016/j.gca.2007.02.008)

**Implemented in:**
- `engines/more_classifications/meteorite_weathering_grade.json`

---

## Carbonate Classification

### Dunham Classification

**Dunham, R. J. (1962).**  
*Classification of carbonate rocks according to depositional texture.*  
In: Ham, W. E. (Ed.), Classification of Carbonate Rocks—A Symposium. American Association of Petroleum Geologists Memoir 1, pp. 108-121.

**Implemented in:**
- `engines/more_classifications/dunham_carbonate.json`

---

## Statistical Methods

### Enrichment Factor

**Zoller, W. H., Gladney, E. S., & Duce, R. A. (1974).**  
*Atmospheric concentrations and sources of trace metals at the South Pole.*  
Science, 183(4121), 198-200.  
DOI: [10.1126/science.183.4121.198](https://doi.org/10.1126/science.183.4121.198)

**Implemented in:**
- `engines/classification/enrichment_factor_screening.json`

---

### Principal Component Analysis (PCA)

**Pearson, K. (1901).**  
*On lines and planes of closest fit to systems of points in space.*  
The London, Edinburgh, and Dublin Philosophical Magazine and Journal of Science, 2(11), 559-572.  
DOI: [10.1080/14786440109462720](https://doi.org/10.1080/14786440109462720)

**Hotelling, H. (1933).**  
*Analysis of a complex of statistical variables into principal components.*  
Journal of Educational Psychology, 24(6), 417-441.  
DOI: [10.1037/h0071325](https://doi.org/10.1037/h0071325)

**Jolliffe, I. T. (2002).**  
*Principal Component Analysis* (2nd ed.).  
Springer Series in Statistics. Springer, New York.  
DOI: [10.1007/b98835](https://doi.org/10.1007/b98835)

**Implemented in:**
- `plugins/software/pca_lda_explorer.py`

---

## Software & Libraries

### Core Scientific Python Stack

**Harris, C. R., Millman, K. J., van der Walt, S. J., et al. (2020).**  
*Array programming with NumPy.*  
Nature, 585(7825), 357-362.  
DOI: [10.1038/s41586-020-2649-2](https://doi.org/10.1038/s41586-020-2649-2)

**McKinney, W. (2010).**  
*Data structures for statistical computing in Python.*  
Proceedings of the 9th Python in Science Conference, 56-61.  
DOI: [10.25080/Majora-92bf1922-00a](https://doi.org/10.25080/Majora-92bf1922-00a)

**Virtanen, P., Gommers, R., Oliphant, T. E., et al. (2020).**  
*SciPy 1.0: fundamental algorithms for scientific computing in Python.*  
Nature Methods, 17(3), 261-272.  
DOI: [10.1038/s41592-019-0686-2](https://doi.org/10.1038/s41592-019-0686-2)

**Pedregosa, F., Varoquaux, G., Gramfort, A., et al. (2011).**  
*Scikit-learn: Machine learning in Python.*  
Journal of Machine Learning Research, 12, 2825-2830.

---

### Visualization

**Hunter, J. D. (2007).**  
*Matplotlib: A 2D graphics environment.*  
Computing in Science & Engineering, 9(3), 90-95.  
DOI: [10.1109/MCSE.2007.55](https://doi.org/10.1109/MCSE.2007.55)

**Waskom, M. (2021).**  
*seaborn: statistical data visualization.*  
Journal of Open Source Software, 6(60), 3021.  
DOI: [10.21105/joss.03021](https://doi.org/10.21105/joss.03021)

---

### Geospatial

**Jordahl, K., Van den Bossche, J., Fleischmann, M., et al. (2020).**  
*geopandas/geopandas: v0.8.1.*  
Zenodo.  
DOI: [10.5281/zenodo.3946761](https://doi.org/10.5281/zenodo.3946761)

**Gillies, S., et al. (2007–2021).**  
*Shapely: manipulation and analysis of geometric objects.*  
[https://github.com/shapely/shapely](https://github.com/shapely/shapely)

---

## Additional Acknowledgments

Scientific Toolkit builds on decades of scientific method development by researchers worldwide. While we've listed the primary citations for implemented methods above, many classification schemes integrate insights from hundreds of additional publications.

### Open Source Community

This software depends on the Python scientific computing ecosystem, including NumPy, Pandas, Matplotlib, SciPy, Scikit-learn, and many other libraries maintained by volunteer developers worldwide.

### Data Contributors

Sample datasets and test cases have been contributed by researchers who generously shared their data to help validate these implementations.

---

## Reporting Citation Errors

If you notice:
- Missing citations for implemented methods
- Incorrect attributions
- Updated references that should be included

Please open an issue on GitLab: https://gitlab.com/sefy76/scientific-toolkit/-/issues

---

## License Note

While Scientific Toolkit is licensed under CC BY-NC-SA 4.0, the scientific methods implemented are from published literature as cited above. Users must cite the original publications when using specific classification schemes in research, not just this software.

**Example citation in a paper:**

> "Samples were classified using the TAS diagram (Le Bas et al., 1986) as implemented in Scientific Toolkit v2.0 (Levy, 2026)."

This properly credits both the original method developers and the software implementation.

---

<p align="center">
<i>Standing on the shoulders of giants</i>
</p>
