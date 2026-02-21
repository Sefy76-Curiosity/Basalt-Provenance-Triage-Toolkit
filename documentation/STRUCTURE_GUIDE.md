📁 Scientific Toolkit v2.0 - Complete Project Structure
✨ Complete Visual Guide

This document shows the full 153-file structure of Scientific Toolkit v2.0, including all classification engines, protocols, plugins, and enhanced features.
text

scientific-toolkit/
│
├── 📄 Scientific-Toolkit.py                    ← Main application (original)
├── 📄 Scientific-Toolkit-Enhanced.py           ← Main app with productivity features
├── 📄 data_hub.py                              ← Central data management (observer pattern)
├── 📄 color_manager.py                         ← Classification color schemes
├── 📄 update_checker.py                        ← GitLab/GitHub update checker
├── 📄 __init__.py                              ← Package initialization
│
├── 📂 features/                                 ← PRODUCTIVITY FEATURES (6 modules)
│   ├── __init__.py                              ← Package init
│   ├── tooltip_manager.py                       ← Hover tooltips (500ms delay)
│   ├── recent_files_manager.py                  ← Tracks last 10 files
│   ├── macro_recorder.py                        ← Workflow recorder/replay (14 KB)
│   ├── project_manager.py                       ← Project save/load (.stproj)
│   └── script_exporter.py                       ← Python/R script export
│
├── 📂 ui/                                        ← USER INTERFACE (5 files)
│   ├── left_panel.py                             ← Data import, manual entry, hardware buttons
│   ├── center_panel.py                           ← Main data table, plots, status bar
│   ├── right_panel.py                            ← Classification HUD, scheme selection
│   ├── results_dialog.py                         ← Classification results popup
│   ├── all_schemes_detail_dialog.py              ← "Run All" results viewer
│   └── __init__.py                               ← Package init
│
├── 📂 engines/                                    ← SCIENTIFIC ENGINES (2 engines + 120 files)
│   ├── classification_engine.py                   ← Rule-based classification (70 schemes)
│   ├── protocol_engine.py                         ← Multi-stage workflows (50 protocols)
│   ├── derived_fields.json                        ← Calculated field definitions
│   │
│   ├── 📂 classification/                          ← 70 CLASSIFICATION SCHEMES
│   │   ├── afm_irvine–baragar_series.json
│   │   ├── alteration_indices_ishikawa_ccpi.json
│   │   ├── analytical_precision_filter.json
│   │   ├── analytical_quality_control.json
│   │   ├── anhydrous_normalization.json
│   │   ├── au_as_sb_pathfinder.json
│   │   ├── bone_collagen_qc.json
│   │   ├── bone_diagenesis_apatite.json
│   │   ├── bone_trophic_diet.json
│   │   ├── ceramic_firing_temperature_proxies.json
│   │   ├── chemical_index_alteration.json
│   │   ├── chondrite_meteorite.json
│   │   ├── ci_normalized_spider_diagram.json
│   │   ├── copper_alloy_classification.json
│   │   ├── dott_sandstone_classification.json
│   │   ├── dunham_carbonate.json
│   │   ├── enrichment_factor_screening.json
│   │   ├── environmental_pollution_indices.json
│   │   ├── eruption_style_proxy.json
│   │   ├── fao_soil_classification_ph_ec.json
│   │   ├── folk_carbonate_classification.json
│   │   ├── ftir_crystallinity_index.json
│   │   ├── geoaccumulation_index_igeo.json
│   │   ├── glass_compositional_families.json
│   │   ├── igneous_major_oxide_indices.json
│   │   ├── iron_bloom_classification.json
│   │   ├── isotope_provenance_and_diet.json
│   │   ├── jensen_cation_plot.json
│   │   ├── k2o–sio2_volcanic_series.json
│   │   ├── magma_rheology_and_eruption_style.json
│   │   ├── metamorphic_facies.json
│   │   ├── meteorite_petrology_and_groups.json
│   │   ├── meteorite_shock_stage.json
│   │   ├── meteorite_weathering_grade.json
│   │   ├── munsell_color_classification.json
│   │   ├── normative_molar_proportions.json
│   │   ├── ore-grade_multi-element_anomaly_grid.json
│   │   ├── pathfinder_log_transformation.json
│   │   ├── pearce_mantle_array.json
│   │   ├── pearce_zr_y_tectonic.json
│   │   ├── pettijohn_sandstone_classification.json
│   │   ├── piper_diagram_classification.json
│   │   ├── planetary_analog_ratio.json
│   │   ├── provenance_fingerprinting.json
│   │   ├── qapf_mineralogy.json
│   │   ├── rare_earth_element.json
│   │   ├── ree_pattern_named_types.json
│   │   ├── regional_triage.json
│   │   ├── sediment_grain_size.json
│   │   ├── sediment_texture_and_maturity.json
│   │   ├── slag_basicity_index.json
│   │   ├── slag_thermochemical_properties.json
│   │   ├── soil_chemical_properties.json
│   │   ├── soil_salinity_classification_(ec).json
│   │   ├── soil_sodicity_(sar).json
│   │   ├── stable_isotope_diet.json
│   │   ├── stiff_diagram_classification.json
│   │   ├── strontium_mobility_index.json
│   │   ├── tas_full_volcanic_classification.json
│   │   ├── tas_le_bas_classification.json
│   │   ├── tectonic_discrimination_diagrams.json
│   │   ├── total_alkali_vs_silica_(tas_polygons).json
│   │   ├── upb_concordia_qc.json
│   │   ├── usda_soil_texture_classification.json
│   │   ├── usda_soil_texture_triangle_(full).json
│   │   ├── volcanic_series.json
│   │   ├── water_hardness.json
│   │   ├── winchester_floyd_discrimination.json
│   │   ├── zircon_trace_element_thermometry.json
│   │   └── _TEMPLATE.json
│   │
│   └── 📂 protocols/                              ← 50 SCIENTIFIC PROTOCOLS
│       ├── behrensmeyer_weathering_protocol.json
│       ├── epa_sediment_quality_protocol.json
│       ├── folk_shepard_sediment_texture_protocol.json
│       ├── hakanson_ecological_risk_protocol.json
│       ├── iugs_igneous_protocol.json
│       ├── meresha_protocol.json
│       ├── shipman_rose_burning_protocol.json
│       ├── stable_isotope_diet_protocol.json
│       ├── usda_soil_morphology_protocol.json
│       ├── zooarch_fragmentation_breakage_protocol.json
│       └── ... (40+ more)
│
├── 📂 plugins/                                     ← 67 PLUGINS
│   ├── plugin_manager.py                           ← Plugin manager UI (install/enable)
│   ├── plugins.json                                ← Plugin registry
│   ├── plugin_store.json                           ← Remote plugin sources
│   │
│   ├── 📂 software/                                 ← 37 SOFTWARE PLUGINS
│   │   ├── lithic_morphometrics.py
│   │   ├── advanced_export.py
│   │   ├── advanced_normalization.py
│   │   ├── advanced_normative_calculations.py
│   │   ├── advanced_petrogenetic_models.py
│   │   ├── ague_hg_mobility.py
│   │   ├── compositional_stats_pro.py
│   │   ├── data_validation_filter.py
│   │   ├── dating_integration.py
│   │   ├── demo_data_generator.py
│   │   ├── geochemical_explorer.py
│   │   ├── geochem_advanced.py
│   │   ├── geochronology_suite.py
│   │   ├── gis_3d_viewer_pro.py
│   │   ├── google_earth_pro.py
│   │   ├── interactive_contouring.py
│   │   ├── isotope_mixing_models.py
│   │   ├── laicpms_pro.py
│   │   ├── literature_comparison.py
│   │   ├── magma_modeling.py
│   │   ├── museum_import.py
│   │   ├── pca_lda_explorer.py
│   │   ├── petrogenetic_suite.py
│   │   ├── photo_manager.py
│   │   ├── publication_layouts.py
│   │   ├── quartz_gis_pro.py
│   │   ├── report_generator.py
│   │   ├── scripting_console.py
│   │   ├── spatial_kriging.py
│   │   ├── spectral_toolbox.py
│   │   ├── structural_geology.py
│   │   ├── structural_suite.py
│   │   ├── thermobarometry_suite.py
│   │   ├── uncertainty_propagation.py
│   │   ├── virtual_microscopy_pro.py
│   │   └── zooarchaeology_analytics_suite.py
│   │
│   ├── 📂 add-ons/                                  ← 23 ADD-ON PLUGINS
│   │   ├── ascii_plotter.py
│   │   ├── batch_processor.py
│   │   ├── chatgpt_ai.py
│   │   ├── claude_ai.py
│   │   ├── copilot_ai.py
│   │   ├── deepseek_ai.py
│   │   ├── file_console.py
│   │   ├── gemini_ai.py
│   │   ├── geopandas_plotter.py
│   │   ├── geoplot_pro.py
│   │   ├── gis_console.py
│   │   ├── grok_ai.py
│   │   ├── julia_console.py
│   │   ├── matplotlib_plotter.py
│   │   ├── missingno_plotter.py
│   │   ├── ollama_ai.py
│   │   ├── pillow_plotter.py
│   │   ├── python_console.py
│   │   ├── r_console.py
│   │   ├── seaborn_plotter.py
│   │   ├── sql_console.py
│   │   └── ternary_plotter.py
│   │
│   └── 📂 hardware/                                  ← 7 HARDWARE SUITES
│       ├── barcode_scanner_unified_suite.py          ← Zebra, Honeywell, Socket, etc.
│       ├── elemental_geochemistry_unified_suite.py   ← SciAps, Bruker, Olympus, Thermo
│       ├── mineralogy_unified_suite.py               ← RRUFF (5,185 minerals)
│       ├── physical_properties_unified_suite.py      ← AGICO, Bartington, Mitutoyo
│       ├── solution_chemistry_unified_suite.py       ← Mettler, Orion, Hanna, YSI
│       ├── spectroscopy_unified.py                   ← Thermo, Bruker, B&W Tek, Ocean
│       └── zooarchaeology_unified_suite.py           ← Calipers, balances, GNSS
│
├── 📂 config/                                        ← CONFIGURATION (6 files)
│   ├── chemical_elements.json                        ← Column name mappings (58 KB)
│   ├── scatter_colors.json                           ← Classification color schemes
│   ├── user_settings.json                            ← User preferences (auto-created)
│   ├── recent_files.json                             ← Recent files list (auto-created)
│   ├── macros.json                                   ← Saved macros (auto-created)
│   ├── disabled_schemes.json                         ← Disabled classifications
│   └── enabled_plugins.json                          ← Enabled plugins
│
├── 📂 samples/                                        ← SAMPLE DATA (10 files)
│   ├── master_test_list.csv                          ← Master test dataset
│   ├── classifications_master_test.csv               ← Classification test data
│   ├── geochemistry.csv                              ← Geochemistry examples
│   ├── geochemistry_location.csv                     ← Geochemistry with coordinates
│   ├── structural_data.csv                            ← Structural geology data
│   ├── thermobarometry_test_data.csv                  ← Thermobarometry examples
│   ├── geochronology_test_data.csv                    ← U-Pb, Ar-Ar test data
│   ├── bone.csv                                       ← Zooarchaeology data
│   ├── statistical_console.py                         ← Console plugin example
│   └── ... (more)
│
├── 📂 tests/                                          ← TEST SUITE (6 files)
│   ├── conftest.py                                    ← Pytest fixtures
│   ├── test_evaluate_rule.py                          ← Rule evaluation tests
│   ├── test_derived_fields.py                         ← Derived field tests
│   ├── test_classification_schemes.py                 ← Classification tests
│   ├── test_engine_core.py                            ← Engine core tests
│   └── test_integration_real_files.py                 ← Integration tests
│
├── 📂 templates/                                       ← PLOT TEMPLATES (8 files)
│   ├── aesthetic_templates.json                       ← Color-blind, high contrast
│   ├── discipline_templates.json                      ← REE spider, TAS, isotopes
│   ├── functional_templates.json                      ← Publication-ready, reviewer
│   ├── geochem_specialized.json                       ← MORB-normalized, isotope
│   ├── journal_templates.json                         ← Nature, Science, AGU, Elsevier
│   ├── presentation_templates.json                    ← Poster, talk, thesis
│   ├── professional_templates.json                    ← Professional styles
│   └── quick_draft_templates.json                     ← Draft, lab meeting
│
└── 📂 docs/                                            ← DOCUMENTATION (9 files)
    ├── README.md                                       ← Main GitLab landing page
    ├── CITATIONS.md                                    ← 200+ academic citations
    ├── QUICK_START.md                                  ← 5-minute getting started
    ├── INSTALLATION.md                                 ← Complete installation guide
    ├── FAQ.md                                          ← Frequently asked questions
    ├── ENHANCED_FEATURES_README.md                     ← Productivity features guide
    ├── INSTALLATION_GUIDE.md                           ← Quick installation reference
    ├── STRUCTURE_GUIDE.md                              ← This file
    └── DELIVERY_SUMMARY.md                             ← Complete package overview

📊 File Count Summary
Category	Count
Core Application	6 files
UI Modules	5 files
Engines	2 engines + 120 schemes/protocols
Plugins	67 files
Configuration	6 files
Sample Data	10 files
Tests	6 files
Templates	8 files
Documentation	9 files
Productivity Features	6 files
TOTAL	153 files
🎯 Key Components
1. Productivity Features (features/)

    tooltip_manager.py - Hover tooltips (500ms delay)

    recent_files_manager.py - Tracks last 10 files

    macro_recorder.py - Workflow recorder/replay (14 KB)

    project_manager.py - Save/load projects (.stproj)

    script_exporter.py - Export as Python/R

2. UI Components (ui/)

    left_panel.py - Import, manual entry, hardware buttons

    center_panel.py - Main data table, plots, status

    right_panel.py - Classification HUD, scheme selection

    results_dialog.py - Classification results popup

    all_schemes_detail_dialog.py - "Run All" results

3. Scientific Engines (engines/)

    70 classification schemes - JSON rule-based

    50 protocols - Multi-stage workflows

    derived_fields.json - 20+ calculated fields

4. Plugins (plugins/)

    37 software plugins - Analysis tools

    23 add-on plugins - Plotting, consoles, AI

    7 hardware suites - Device integration

    plugin_manager.py - One-click install/enable

🔧 Key File Sizes
File	Size
Scientific-Toolkit-Enhanced.py	245 KB
data_hub.py	18 KB
color_manager.py	12 KB
classification_engine.py	18 KB
protocol_engine.py	12 KB
plugin_manager.py	22 KB
macro_recorder.py	14 KB
chemical_elements.json	58 KB
CITATIONS.md	42 KB
FAQ.md	24 KB
🚀 Quick Setup
bash

# Clone repository
git clone https://gitlab.com/sefy76/scientific-toolkit.git
cd scientific-toolkit

# Install dependencies
pip install -r requirements.txt

# Run enhanced version
python Scientific-Toolkit-Enhanced.py

✅ Setup Checklist

    features/ folder exists with 6 files

    ui/ folder exists with 5 files

    engines/ folder exists with 120+ files

    plugins/ folder exists with 67+ files

    config/ folder is writable

    samples/ folder exists with test data

    All dependencies installed (pip install -r requirements.txt)

    Scientific-Toolkit-Enhanced.py runs without errors

🎉 That's It!

Your project is now beautifully organized with:

    ✅ 153 files total

    ✅ 70 classification engines

    ✅ 50 scientific protocols

    ✅ 67 plugins (37 software, 23 add-ons, 7 hardware)

    ✅ 6 productivity features

    ✅ 200+ citations

    ✅ ~77,000 lines of code

Questions? Check INSTALLATION_GUIDE.md for setup or FAQ.md for common questions.

Last updated: February 21, 2026
