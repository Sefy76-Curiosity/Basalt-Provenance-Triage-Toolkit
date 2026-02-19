"""
test_integration_real_files.py
================================
Integration tests that load the REAL JSON classification files from disk
and verify correct classifications against published reference values.

All tests in this file are automatically SKIPPED if the JSON files are
not present (e.g. during CI without the full project checkout).

Each test documents:
  - The sample values used
  - The expected classification
  - The literature reference justifying those values
"""

import pytest


# ---------------------------------------------------------------------------
# All tests require real JSON files → use the real_engine fixture
# (defined in conftest.py; auto-skips if files not found)
# ---------------------------------------------------------------------------


class TestRealTASClassification:
    """
    Total Alkali vs Silica series (Irvine & Baragar 1971).
    Tests the real JSON file: engines/more_classifications/total_alkali_vs_silica_(tas_polygons).json
    """

    SCHEME = "total_alkali_vs_silica_(tas_polygons)"

    def test_hawaiian_tholeiite_subalkaline(self, real_engine):
        """
        Kilauea summit tholeiite (1959 eruption, Murata & Richter 1966):
        Na2O≈2.33, K2O≈0.51 → Total_Alkali=2.84 → SUBALKALINE
        """
        sample = {
            "Na2O_wt+K2O_wt": 2.84,
            "SiO2_wt": 49.3,
            "Sample_ID": "kilauea-tholeiite",
        }
        name, _, _ = real_engine.classify_sample(sample, self.SCHEME)
        assert name == "SUBALKALINE SERIES", f"Got: {name}"

    def test_canary_islands_phonolite_alkaline(self, real_engine):
        """
        La Palma phonolite (Carracedo et al. 2001):
        Na2O≈9.0, K2O≈5.4 → Total_Alkali=14.4 → ALKALINE
        """
        sample = {
            "Na2O_wt+K2O_wt": 14.4,
            "SiO2_wt": 58.0,
            "Sample_ID": "la-palma-phonolite",
        }
        name, _, _ = real_engine.classify_sample(sample, self.SCHEME)
        assert name == "ALKALINE SERIES", f"Got: {name}"

    def test_boundary_7_0_subalkaline(self, real_engine):
        """Exactly 7.0 → SUBALKALINE (≤7 rule fires first)."""
        sample = {"Na2O_wt+K2O_wt": 7.0, "SiO2_wt": 53.0}
        name, _, _ = real_engine.classify_sample(sample, self.SCHEME)
        assert name == "SUBALKALINE SERIES"


class TestRealBoneCollagen:
    """
    Bone Collagen QC — C:N ratio.
    Tests: engines/more_classifications/bone_collagen_qc.json
    """

    SCHEME = "bone_collagen_qc"

    def test_well_preserved_roman_bone(self, real_engine):
        """
        Roman-period bone from York (van Klinken 1999):
        typical C:N = 3.2 → PRESERVED
        """
        name, _, _ = real_engine.classify_sample(
            {"C_N_Ratio": 3.2, "C_pct": 35.0, "N_pct": 12.9, "Sample_ID": "york-roman-01"},
            self.SCHEME,
        )
        assert name == "PRESERVED (PASS)"

    def test_degraded_pleistocene_bone(self, real_engine):
        """
        Late Pleistocene fossil with diagenetic alteration:
        C:N = 5.8 → DEGRADED / CONTAMINATED
        """
        name, _, _ = real_engine.classify_sample(
            {"C_N_Ratio": 5.8, "C_pct": 12.0, "N_pct": 2.4, "Sample_ID": "pleistocene-01"},
            self.SCHEME,
        )
        assert name == "DEGRADED / CONTAMINATED"


class TestRealGrainSize:
    """
    Wentworth (1922) grain-size classification.
    Tests: engines/more_classifications/sediment_grain_Size.json
    """

    SCHEME = "sediment_grain_Size"

    def test_loess_silt(self, real_engine):
        """Chinese Loess Plateau: modal grain = 25 µm → SILT."""
        name, _, _ = real_engine.classify_sample({"GrainSize_um": 25.0}, self.SCHEME)
        assert "SILT" in name

    def test_beach_sand(self, real_engine):
        """Fine beach sand: 250 µm → SAND."""
        name, _, _ = real_engine.classify_sample({"GrainSize_um": 250.0}, self.SCHEME)
        assert "SAND" in name

    def test_deep_sea_clay(self, real_engine):
        """Pelagic clay: 1.5 µm → CLAY."""
        name, _, _ = real_engine.classify_sample({"GrainSize_um": 1.5}, self.SCHEME)
        assert "CLAY" in name

    def test_fluvial_gravel(self, real_engine):
        """River bar deposit: 5000 µm → GRAVEL."""
        name, _, _ = real_engine.classify_sample({"GrainSize_um": 5000.0}, self.SCHEME)
        assert "GRAVEL" in name


class TestRealWaterHardness:
    """
    Water hardness (USGS).
    Tests: engines/more_classifications/water_hardness.json
    """

    SCHEME = "water_hardness"

    def test_soft_rainwater(self, real_engine):
        name, _, _ = real_engine.classify_sample({"Hardness_mgL": 15.0}, self.SCHEME)
        assert name == "SOFT"

    def test_hard_limestone_aquifer(self, real_engine):
        """Chalk aquifer water: ~150 mg/L → HARD."""
        name, _, _ = real_engine.classify_sample({"Hardness_mgL": 150.0}, self.SCHEME)
        assert name == "HARD"

    def test_very_hard_gypsum(self, real_engine):
        """Gypsum spring: 300 mg/L → VERY HARD."""
        name, _, _ = real_engine.classify_sample({"Hardness_mgL": 300.0}, self.SCHEME)
        assert name == "VERY HARD"


class TestRealIsotopeDiet:
    """
    Stable isotope dietary reconstruction.
    Tests: engines/more_classifications/stable_isotope_diet.json
    """

    SCHEME = "stable_isotope_diet"

    def test_medieval_european_c3(self, real_engine):
        """
        Medieval English individual (Müldner & Richards 2005):
        δ13C = -20.1‰, δ15N = 8.3‰ → C3 TERRESTRIAL DIET
        """
        name, _, _ = real_engine.classify_sample(
            {"d13C": -20.1, "d15N": 8.3},
            self.SCHEME,
        )
        assert "C3" in name

    def test_mesoamerican_maize_diet(self, real_engine):
        """
        Mesoamerican individual with heavy maize (C4) consumption:
        δ13C = -10.5‰ → C4 OR HIGH MARINE DIET
        """
        name, _, _ = real_engine.classify_sample(
            {"d13C": -10.5, "d15N": 9.5},
            self.SCHEME,
        )
        assert "C4" in name or "MARINE" in name


class TestRealUSDAsoil:
    """
    USDA Soil Texture.
    Tests: engines/more_classifications/usda_soil_texture_classification.json
    """

    SCHEME = "usda_soil_texture_classification"

    def test_heavy_clay(self, real_engine):
        name, _, _ = real_engine.classify_sample(
            {"Sand_pct": 10.0, "Silt_pct": 30.0, "Clay_pct": 60.0},
            self.SCHEME,
        )
        assert name == "CLAY"

    def test_desert_sand(self, real_engine):
        name, _, _ = real_engine.classify_sample(
            {"Sand_pct": 92.0, "Silt_pct": 5.0, "Clay_pct": 3.0},
            self.SCHEME,
        )
        assert name == "SAND"


class TestRealPearceMantle:
    """
    Pearce mantle array (Pearce 2008).
    Tests: engines/classification/pearce_mantle_array.json
    """

    SCHEME = "pearce_mantle_array"

    def test_oib_from_ratios(self, real_engine):
        """
        Hawaiian basalt with pre-computed ratios:
        Nb/Yb = 26.7 → PLUME/OIB AFFINITY
        """
        name, _, _ = real_engine.classify_sample(
            {
                "Nb_ppm": 80.0,
                "Yb_ppm": 3.0,
                "Th_ppm": 4.0,
                "Nb_Yb_Ratio": 26.7,
                "Th_Yb_Ratio": 1.33,
            },
            self.SCHEME,
        )
        assert "OIB" in name or "PLUME" in name

    def test_depleted_morb(self, real_engine):
        """
        N-MORB (Hofmann 1988 compilation):
        Nb=2.33, Yb=3.05 → Nb/Yb=0.76;  Th=0.12 → Th/Yb=0.04
        → DEPLETED MORB-LIKE
        """
        name, _, _ = real_engine.classify_sample(
            {
                "Nb_ppm": 2.33,
                "Yb_ppm": 3.05,
                "Th_ppm": 0.12,
                "Nb_Yb_Ratio": 0.76,
                "Th_Yb_Ratio": 0.04,
            },
            self.SCHEME,
        )
        assert "MORB" in name or "DEPLETED" in name
