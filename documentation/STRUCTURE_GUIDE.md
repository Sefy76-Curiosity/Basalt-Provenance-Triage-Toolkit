Scientific Toolkit v2.0 - Complete Project Structure
Visual Guide to All Components

This document shows the full structure of Scientific Toolkit v2.0, including all
classification engines, protocols, plugins, field panels, and productivity features.

scientific-toolkit/
│
├── Scientific-Toolkit.py                       ← Main application (ttkbootstrap UI)
├── data_hub.py                                 ← Central data management (observer pattern)
├── color_manager.py                            ← Classification color schemes
├── update_checker.py                           ← GitLab/GitHub update checker
│
├── features/                                   ← PRODUCTIVITY FEATURES
│   ├── __init__.py
│   ├── auto_save.py                            ← Thread-safe auto-save
│   │                                              Race condition fixed, atomic writes,
│   │                                              crash recovery on startup
│   ├── macro_recorder.py                       ← Workflow recorder
│   │                                              Captures 13 action types
│   ├── project_manager.py                      ← Project save/load (.stproj JSON)
│   ├── script_exporter.py                      ← Python/R script export
│   ├── tooltip_manager.py                      ← Hover tooltips (500ms delay)
│   ├── recent_files_manager.py                 ← Tracks last 10 opened files
│   └── settings_manager.py                     ← User settings management
│
├── ui/                                         ← USER INTERFACE
│   ├── __init__.py
│   ├── left_panel.py                           ← Data import, manual entry, hardware buttons
│   ├── center_panel.py                         ← Main data table, plots, status bar,
│   │                                              field panel selection notification
│   ├── right_panel.py                          ← Classification HUD + field panel
│   │                                              switcher, auto-detection logic
│   │
│   ├── ── FIELD PANELS v3.0 (16 domain modules) ──
│   ├── right_panel_archaeology.py              ← Archaeology & archaeometry
│   ├── right_panel_chromatography.py           ← Chromatography / analytical chemistry
│   ├── right_panel_electrochem.py              ← Electrochemistry
│   ├── right_panel_geochemistry.py             ← Geochemistry (TAS + AFM + Mg# embedded)
│   ├── right_panel_geochronology.py            ← Geochronology (U-Pb, Ar-Ar)
│   ├── right_panel_geophysics.py               ← Geophysics surveys
│   ├── right_panel_materials.py                ← Materials characterisation
│   ├── right_panel_meteorology.py              ← Meteorology & environmental
│   ├── right_panel_molecular.py                ← Molecular biology / clinical
│   ├── right_panel_petrology.py                ← Petrology (modal/normative)
│   ├── right_panel_physics.py                  ← Physics & test/measurement
│   ├── right_panel_solution.py                 ← Solution / water chemistry
│   ├── right_panel_spatial.py                  ← GIS & spatial data
│   ├── right_panel_spectroscopy.py             ← Spectroscopy (FTIR, Raman, UV-Vis)
│   ├── right_panel_structural.py               ← Structural geology
│   ├── right_panel_zooarch.py                  ← Zooarchaeology (NISP, MNI)
│   ├── right_panel_patch.py                    ← Selection-sync patch documentation
│   │
│   ├── results_dialog.py                       ← Classification results popup
│   └── all_schemes_detail_dialog.py            ← "Run All Schemes" results viewer
│
├── engines/                                    ← SCIENTIFIC ENGINES
│   ├── classification_engine.py                ← Rule-based classification (70 schemes)
│   ├── protocol_engine.py                      ← Multi-stage workflows (JSON-based)
│   ├── derived_fields.json                     ← Calculated field definitions
│   │
│   ├── classification/                         ← 70 CLASSIFICATION SCHEMES (JSON)
│   │   ├── afm_irvine-baragar_series.json
│   │   ├── alteration_indices_ishikawa_ccpi.json
│   │   ├── analytical_precision_filter.json
│   │   ├── analytical_quality_control.json
│   │   ├── bone_collagen_qc.json
│   │   ├── bone_diagenesis_apatite.json
│   │   ├── bone_trophic_diet.json
│   │   ├── ceramic_firing_temperature_proxies.json
│   │   ├── chemical_index_alteration.json
│   │   ├── chondrite_meteorite.json
│   │   ├── copper_alloy_classification.json
│   │   ├── dott_sandstone_classification.json
│   │   ├── dunham_carbonate.json
│   │   ├── fao_soil_classification_ph_ec.json
│   │   ├── folk_carbonate_classification.json
│   │   ├── ftir_crystallinity_index.json
│   │   ├── geoaccumulation_index_igeo.json
│   │   ├── isoplot_concordance_filter.json
│   │   ├── mantle_reservoir_pb.json
│   │   ├── meteorite_shock_stage.json
│   │   ├── pearce_tectonic_discrimination.json
│   │   ├── ree_eu_anomaly.json
│   │   ├── ree_patterns.json
│   │   ├── sr_nd_isotope_reservoir.json
│   │   ├── tas_volcanic_le_bas.json
│   │   ├── usda_soil_texture.json
│   │   ├── ... [70 total]
│   │   └── _TEMPLATE.json                      ← Template for adding custom schemes
│   │
│   └── protocols/                              ← SCIENTIFIC PROTOCOLS (JSON)
│       ├── behrensmeyer_weathering.json
│       ├── epa_water_quality.json
│       ├── folk_shepard_texture.json
│       ├── hakanson_ecological_risk.json
│       ├── iugs_igneous_classification.json
│       ├── maresha_zooarchaeology.json
│       ├── shipman_rose_burning.json
│       ├── stable_isotope_diet.json
│       ├── usda_soil_morphology.json
│       ├── zooarch_fragmentation_breakage.json
│       └── _TEMPLATE.json
│
├── plugins/                                    ← ALL PLUGINS
│   ├── plugins.json                            ← Plugin registry
│   ├── plugin_store.json                       ← Online plugin store catalog
│   ├── plugin_manager.py                       ← Plugin management UI (v3.0)
│   ├── __init__.py
│   │
│   ├── add-ons/                                ← 25 ADD-ON PLUGINS
│   │   ├── __init__.py
│   │   ├── toolkit_ai.py                       ← Built-in AI assistant v2.2
│   │   │                                          Plugin scanning, scheme lookup,
│   │   │                                          recommendation engine, 100% offline
│   │   ├── statistical_console.py              ← Stats for non-programmers
│   │   │                                          Summary, describe, correlate,
│   │   │                                          groups, t-test (no scipy)
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
│   ├── hardware/                               ← 16 HARDWARE SUITES
│   │   ├── __init__.py
│   │   ├── archaeology_archaeometry_unified_suite.py
│   │   ├── barcode_scanner_unified_suite.py
│   │   ├── chromatography_analytical_unified_suite.py
│   │   ├── clinical_molecular_diagnostics_suite.py
│   │   ├── electrochemistry_unified_suite.py
│   │   ├── elemental_geochemistry_unified_suite.py
│   │   ├── geophysics_unified_suite.py
│   │   ├── materials_characterization_unified_suite.py
│   │   ├── meteorology_environmental_unified_suite.py
│   │   ├── molecular_biology_unified_suite.py
│   │   ├── physical_properties_unified_suite.py
│   │   ├── physics_test_and_measurement_suite.py
│   │   ├── solution_chemistry_unified_suite.py
│   │   ├── spectroscopy_unified_suite.py
│   │   ├── thermal_analysis_calorimetry_unified_suite.py
│   │   └── zooarchaeology_unified_suite.py
│   │
│   └── software/                              ← 37 SOFTWARE PLUGINS
│       ├── __init__.py
│       ├── advanced_normative_calculations.py
│       ├── archaeometry_analysis_suite_ultimate.py
│       ├── chromatography_analysis_suite.py
│       ├── clinical_diagnostics_analysis_suite.py
│       ├── compositional_stats_pro.py
│       ├── dataprep_pro.py
│       ├── electrochemistry_analysis_suite.py
│       ├── geochemical_explorer.py
│       ├── geochronology_suite.py
│       ├── geophysics_analysis_suite.py
│       ├── gis_3d_viewer_pro.py
│       ├── google_earth_pro.py
│       ├── isotope_mixing_models.py
│       ├── la_icpms_pro.py
│       ├── lithic_morphometrics.py
│       ├── materials_science_analysis_suite.py
│       ├── molecular_biology_suite.py
│       ├── museum_import.py
│       ├── pca_lda_explorer.py
│       ├── petrogenetic_modeling_suite.py
│       ├── photo_manager.py
│       ├── publication_layouts.py
│       ├── quartz_gis_pro.py
│       ├── report_generator.py
│       ├── scripting_console.py
│       ├── spatial_kriging.py
│       ├── spectral_toolbox.py
│       ├── spectroscopy_analysis_suite.py
│       ├── thermobarometry_suite.py
│       ├── uncertainty_propagation.py
│       ├── virtual_microscopy_pro.py
│       ├── zooarchaeology_analysis_suite.py
│       └── ... [37 total]
│
├── config/                                    ← CONFIGURATION FILES
│   ├── chemical_elements.json                 ← Column name mappings (58 KB)
│   ├── scatter_colors.json                    ← Classification color schemes
│   ├── user_settings.json                     ← User preferences (auto-created)
│   ├── recent_files.json                      ← Recent files list (auto-created)
│   ├── macros.json                            ← Saved macros (auto-created)
│   ├── disabled_schemes.json                  ← Disabled classification schemes
│   ├── enabled_plugins.json                   ← Plugin enable/disable state
│   ├── plugin_manager_state.json              ← Plugin Manager UI state
│   └── ai_knowledge_cache.json               ← Toolkit AI scan cache
│                                                 (auto-created, 1-hour TTL)
│
├── auto_save/                                 ← AUTO-SAVE DIRECTORY (auto-created)
│   └── recovery.stproj                        ← Crash recovery file (atomic writes)
│
├── samples/                                   ← SAMPLE DATA (30+ files)
│   ├── master_test_list.csv                   ← Master multi-domain test dataset
│   ├── classifications_master_test.csv
│   ├── geochemistry.csv
│   ├── geochemistry_location.csv
│   ├── structural_data.csv
│   ├── thermobarometry_test_data.csv
│   │
│   ├── ── DOMAIN TEST FILES (one per field panel) ──
│   ├── archaeology_test.csv
│   ├── chromatography_test.csv
│   ├── electrochem_test.csv
│   ├── geochemistry_test.csv
│   ├── geochronology_test.csv
│   ├── geophysics_test.csv
│   ├── materials_test.csv
│   ├── meteorology_test.csv
│   ├── molecular_test.csv
│   ├── petrology_test.csv
│   ├── physics_test.csv
│   ├── solution_test.csv
│   ├── spatial_test.csv
│   ├── spectroscopy_test.csv
│   ├── structural_test.csv
│   └── zooarch_test.csv
│
├── templates/                                 ← REPORT/FIGURE TEMPLATES
│   ├── aesthetic_templates.json
│   ├── discipline_templates.json
│   ├── functional_templates.json
│   ├── geochem_specialized.json
│   ├── journal_templates.json
│   ├── presentation_templates.json
│   ├── professional_templates.json
│   └── quick_draft_templates.json
│
├── documentation/                             ← DOCUMENTATION
│   ├── README.md
│   ├── QUICK_START.md
│   ├── INSTALLATION.md
│   ├── ENHANCED_FEATURES_README.md
│   ├── FAQ.md
│   ├── STRUCTURE_GUIDE.md               ← this file
│   ├── DELIVERY_SUMMARY.md
│   ├── INSTALLATION_GUIDE.md
│   ├── CITATIONS.md
│   └── DOCUMENTATION_PACKAGE_README.md
│
├── tests/                                     ← TEST SUITE
│   ├── test_toolkit.py
│   ├── README.md
│   └── test_reports/
│
├── snapshots/                                 ← SAMPLE SCREENSHOTS
│
├── README.md                                  ← Root README
├── LICENSE                                    ← CC BY-NC-SA 4.0
├── index.html                                 ← Web documentation
├── favicon.ico
└── .gitignore

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Data Flow (v2.0)

Hardware / File Import
        ↓
   Left Panel
        ↓
   DataHub   ←────────────────────── Observer pattern
   (single source of truth)          (all panels subscribe)
        ↓                ↓                    ↓
  Center Panel      Right Panel           Toolkit AI
  (main table)      (HUD or Field Panel)  (KnowledgeBase scan)
        ↓                ↓
  Statistical      Classification    Field Panel
  Console tab      results + HUD     (auto-detected,
                                     embedded diagrams,
                                     selection-sync)
        ↓
  Auto-Save (background thread)
  → recovery.stproj (atomic write, thread-safe)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Numbers — Scientific Toolkit v2.0
Category                Count
Classification Engines  70
Scientific Protocols    10
Software Plugins        37
Add-on Plugins          25
Hardware Suites         16
Domain Field Panels     16
Macro Action Types      13
Sample Files            30+
AI Assistants           8 (1 built-in offline + 7 external)
UI Framework            ttkbootstrap

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Adding to the Toolkit

Adding a Classification Scheme
1. Copy engines/classification/_TEMPLATE.json
2. Define required_fields, rules (using >, <, between, in, etc.), and output
3. Save with a descriptive filename
4. Restart — scheme appears in dropdown automatically

Adding a Protocol
1. Copy any existing protocol from engines/protocols/
2. Define stages with conditions and derived field outputs
3. Save as a new JSON file
4. Restart — protocol appears in menu

Adding a Field Panel
1. Create ui/right_panel_[domain].py
2. Subclass FieldPanelBase from right_panel.py
3. Set PANEL_ID, PANEL_NAME, PANEL_ICON, DETECT_COLUMNS
4. Implement refresh() and on_selection_changed(selected_rows)
5. Register in right_panel.py's domain panel registry

Adding a Plugin
1. Create plugins/[category]/[plugin_name].py
2. Define PLUGIN_INFO dict at module level (required for Toolkit AI scanning)
3. Implement create_tab(parent) for add-ons, or the hardware protocol interface
4. Add entry to plugins/plugins.json
5. Restart — plugin appears in Plugin Manager
