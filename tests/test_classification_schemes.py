"""
test_classification_schemes.py
================================
Integration tests that verify classify_sample() produces the correct
scientific classification for each major scheme in Scientific Toolkit.

Each test class corresponds to one published classification scheme and
uses sample values drawn from the original literature references.

Schemes covered:
  - Bone Collagen QC           (DeNiro 1985; van Klinken 1999)
  - Bone Diagenesis / Apatite  (Hedges 2002; Pucéat 2004)
  - Stable Isotope Diet        (Schoeninger et al. 1983; DeNiro 1985)
  - TAS Alkali Series          (Irvine & Baragar 1971)
  - Pearce Mantle Array        (Pearce 2008)
  - Sediment Grain Size        (Wentworth 1922)
  - Water Hardness             (USGS / WQA)
  - Geoaccumulation Index      (Müller 1969)
  - USDA Soil Texture          (USDA Soil Taxonomy 1999)
  - Ceramic Firing Temperature (Tite 2008; Quinn 2013)

Each scheme is tested with:
  (a) a canonical "textbook" sample that clearly falls in one category
  (b) boundary values
  (c) missing/insufficient data → UNCLASSIFIED or fallback label
"""

import pytest
from conftest import make_engine, MOCK_DERIVED_FIELDS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def scheme_from_json(data: dict) -> dict:
    """
    Inject a single hand-crafted scheme into a fresh engine.
    This avoids dependency on real JSON files while testing the
    classification logic faithfully.
    """
    return make_engine(
        {"test_scheme": data},
        MOCK_DERIVED_FIELDS,
    )


def classify(engine, sample: dict, scheme_id: str = "test_scheme"):
    name, confidence, color = engine.classify_sample(sample, scheme_id)
    return name, confidence, color


# ---------------------------------------------------------------------------
# 1.  BONE COLLAGEN QUALITY  —  C:N Ratio
#     Reference: DeNiro (1985); van Klinken (1999)
#     PASS: C:N 2.9–3.6;  FAIL: outside range
# ---------------------------------------------------------------------------

BONE_COLLAGEN_SCHEME = {
    "scheme_name": "Bone Collagen Quality (C:N Standard)",
    "version": "1.1",
    "requires_fields": ["C_N_Ratio"],
    "classifications": [
        {
            "name": "PRESERVED (PASS)",
            "color": "green",
            "confidence_score": 1.0,
            "rules": [{"field": "C_N_Ratio", "operator": "between", "min": 2.9, "max": 3.6}],
            "logic": "AND",
        },
        {
            "name": "DEGRADED / CONTAMINATED",
            "color": "red",
            "confidence_score": 1.0,
            "rules": [{"field": "C_N_Ratio", "operator": "not_between", "min": 2.9, "max": 3.6}],
            "logic": "AND",
        },
    ],
}


class TestBoneCollagenQC:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(BONE_COLLAGEN_SCHEME)

    def test_well_preserved_bone(self, engine):
        """
        Typical archaeological bone in good condition.
        C:N ≈ 3.2 is canonical for preserved collagen.
        """
        name, conf, _ = classify(engine, {"C_N_Ratio": 3.2})
        assert name == "PRESERVED (PASS)"
        assert conf == 1.0

    def test_lower_boundary_preserved(self, engine):
        name, _, _ = classify(engine, {"C_N_Ratio": 2.9})
        assert name == "PRESERVED (PASS)"

    def test_upper_boundary_preserved(self, engine):
        name, _, _ = classify(engine, {"C_N_Ratio": 3.6})
        assert name == "PRESERVED (PASS)"

    def test_degraded_high_cn(self, engine):
        """High C:N (>3.6) → bacterial contamination / humic acid."""
        name, _, _ = classify(engine, {"C_N_Ratio": 4.5})
        assert name == "DEGRADED / CONTAMINATED"

    def test_degraded_low_cn(self, engine):
        """Low C:N (<2.9) → mineral contamination."""
        name, _, _ = classify(engine, {"C_N_Ratio": 2.0})
        assert name == "DEGRADED / CONTAMINATED"

    def test_missing_field_unclassified(self, engine):
        name, _, _ = classify(engine, {"Sample_ID": "broken-sample"})
        assert "UNCLASSIFIED" in name or "DEGRADED" in name


# ---------------------------------------------------------------------------
# 2.  BONE DIAGENESIS (Ca/P apatite alteration)
#     Reference: Hedges 2002; Pucéat 2004
# ---------------------------------------------------------------------------

BONE_DIAGENESIS_SCHEME = {
    "scheme_name": "Bone Diagenesis (Mineral Alteration)",
    "version": "1.1",
    "requires_fields": ["CaO_wt", "P2O5_wt"],
    "classifications": [
        {
            "name": "BIO-APATITE (MODERN/FRESH)",
            "color": "blue",
            "confidence_score": 1.0,
            "rules": [{"field": "CaO_wt/P2O5_wt", "operator": "between", "min": 2.0, "max": 2.3}],
            "logic": "AND",
        },
        {
            "name": "DIAGENETICALLY ALTERED (FOSSILIZED)",
            "color": "orange",
            "confidence_score": 1.0,
            "rules": [{"field": "CaO_wt/P2O5_wt", "operator": ">", "value": 2.3}],
            "logic": "OR",
        },
    ],
}


class TestBoneDiagenesis:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(BONE_DIAGENESIS_SCHEME)

    def test_fresh_bone(self, engine):
        """
        Modern bone: CaO/P2O5 ≈ 2.15 (hydroxyapatite stoichiometry).
        """
        name, _, _ = classify(engine, {"CaO_wt/P2O5_wt": 2.15})
        assert name == "BIO-APATITE (MODERN/FRESH)"

    def test_fossilized_bone(self, engine):
        """
        Diagenetically altered bone: CaO/P2O5 elevated >2.3
        due to calcite infilling and recrystallisation.
        """
        name, _, _ = classify(engine, {"CaO_wt/P2O5_wt": 2.8})
        assert name == "DIAGENETICALLY ALTERED (FOSSILIZED)"

    def test_boundary_at_2_3(self, engine):
        """2.3 is the upper limit of bio-apatite (inclusive)."""
        name, _, _ = classify(engine, {"CaO_wt/P2O5_wt": 2.3})
        assert name == "BIO-APATITE (MODERN/FRESH)"


# ---------------------------------------------------------------------------
# 3.  STABLE ISOTOPE DIETARY RECONSTRUCTION
#     Reference: Schoeninger et al. (1983); DeNiro (1985)
# ---------------------------------------------------------------------------

ISOTOPE_DIET_SCHEME = {
    "scheme_name": "Stable Isotope Diet Classification",
    "version": "1.1",
    "requires_fields": ["d13C", "d15N"],
    "classifications": [
        {
            "name": "C3 TERRESTRIAL DIET",
            "color": "#4CAF50",
            "confidence_score": 0.95,
            "rules": [
                {"field": "d13C", "operator": "<", "value": -18.5},
                {"field": "d15N", "operator": "<", "value": 10.0},
            ],
            "logic": "AND",
        },
        {
            "name": "MIXED C3/C4 OR MARINE INFLUENCE",
            "color": "#FFC107",
            "confidence_score": 0.85,
            "rules": [
                {"field": "d13C", "operator": "between", "min": -18.5, "max": -14.0},
            ],
            "logic": "AND",
        },
        {
            "name": "C4 OR HIGH MARINE DIET",
            "color": "#2196F3",
            "confidence_score": 0.90,
            "rules": [
                {"field": "d13C", "operator": ">", "value": -14.0},
            ],
            "logic": "AND",
        },
    ],
}


class TestStableIsotopeDiet:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(ISOTOPE_DIET_SCHEME)

    def test_european_medieval_c3_diet(self, engine):
        """
        Medieval English individual: δ13C = -20.5‰, δ15N = 8.5‰
        → Typical C3 terrestrial (wheat, barley, sheep/cattle).
        """
        name, _, _ = classify(engine, {"d13C": -20.5, "d15N": 8.5})
        assert name == "C3 TERRESTRIAL DIET"

    def test_mixed_diet_c4_influence(self, engine):
        """
        New World individual with maize (C4) consumption:
        δ13C = -16.0‰ falls in mixed range.
        """
        name, _, _ = classify(engine, {"d13C": -16.0, "d15N": 9.0})
        assert name == "MIXED C3/C4 OR MARINE INFLUENCE"

    def test_coastal_marine_diet(self, engine):
        """
        Coastal Viking with high marine protein: δ13C = -12.0‰.
        """
        name, _, _ = classify(engine, {"d13C": -12.0, "d15N": 14.0})
        assert name == "C4 OR HIGH MARINE DIET"

    def test_boundary_c3_mixed(self, engine):
        """δ13C exactly at -18.5‰ is the C3/mixed boundary."""
        name, _, _ = classify(engine, {"d13C": -18.5, "d15N": 8.0})
        # At -18.5, the C3 rule (<-18.5) fails; mixed (between -18.5, -14) is inclusive
        assert name == "MIXED C3/C4 OR MARINE INFLUENCE"


# ---------------------------------------------------------------------------
# 4.  TAS ALKALI SERIES
#     Reference: Irvine & Baragar (1971)
#     Alkaline: Na2O+K2O > 7;  Subalkaline: ≤ 7
#     Note: scheme uses pre-computed field "Na2O_wt+K2O_wt"
# ---------------------------------------------------------------------------

TAS_SERIES_SCHEME = {
    "scheme_name": "Total Alkali vs Silica (TAS) Series Classification",
    "version": "1.1",
    "requires_fields": ["SiO2_wt", "Na2O_wt", "K2O_wt"],
    "classifications": [
        {
            "name": "ALKALINE SERIES",
            "color": "#F44336",
            "confidence_score": 0.90,
            "rules": [{"field": "Na2O_wt+K2O_wt", "operator": ">", "value": 7.0}],
            "logic": "AND",
        },
        {
            "name": "SUBALKALINE SERIES",
            "color": "#4CAF50",
            "confidence_score": 0.90,
            "rules": [{"field": "Na2O_wt+K2O_wt", "operator": "<=", "value": 7.0}],
            "logic": "AND",
        },
    ],
}


class TestTASAlkaliSeries:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(TAS_SERIES_SCHEME)

    def test_phonolite_alkaline(self, engine):
        """
        Phonolite: Na2O≈9, K2O≈5 → total alkali=14 → ALKALINE.
        Classic example: Nyiragongo, East African Rift.
        """
        sample = {"Na2O_wt+K2O_wt": 14.0, "SiO2_wt": 57.0}
        name, _, _ = classify(engine, sample)
        assert name == "ALKALINE SERIES"

    def test_tholeiite_subalkaline(self, engine):
        """
        Mid-ocean ridge basalt: Na2O≈2.5, K2O≈0.15 → total=2.65 → SUBALKALINE.
        """
        sample = {"Na2O_wt+K2O_wt": 2.65, "SiO2_wt": 50.0}
        name, _, _ = classify(engine, sample)
        assert name == "SUBALKALINE SERIES"

    def test_boundary_value_7(self, engine):
        """Exactly 7.0 → SUBALKALINE (rule: <= 7.0)."""
        sample = {"Na2O_wt+K2O_wt": 7.0, "SiO2_wt": 55.0}
        name, _, _ = classify(engine, sample)
        assert name == "SUBALKALINE SERIES"

    def test_above_boundary(self, engine):
        sample = {"Na2O_wt+K2O_wt": 7.1, "SiO2_wt": 55.0}
        name, _, _ = classify(engine, sample)
        assert name == "ALKALINE SERIES"

    def test_missing_alkali_field_unclassified(self, engine):
        """Without the total alkali field, neither rule can fire."""
        sample = {"SiO2_wt": 50.0}
        name, _, _ = classify(engine, sample)
        assert name == "UNCLASSIFIED"


# ---------------------------------------------------------------------------
# 5.  PEARCE MANTLE ARRAY  —  Nb/Yb vs Th/Yb
#     Reference: Pearce (2008), Lithos 100
# ---------------------------------------------------------------------------

PEARCE_SCHEME = {
    "scheme_name": "Pearce Nb/Yb–Th/Yb Mantle Array",
    "version": "1.1",
    "requires_fields": ["Nb_ppm", "Yb_ppm", "Th_ppm"],
    "classifications": [
        {
            "name": "PLUME/OIB AFFINITY (Nb/Yb > 10)",
            "color": "purple",
            "confidence_score": 1.0,
            "rules": [{"field": "Nb_Yb_Ratio", "operator": ">", "value": 10.0}],
            "logic": "AND",
        },
        {
            "name": "CRUSTAL CONTAMINATION (High Th/Yb)",
            "color": "red",
            "confidence_score": 1.0,
            "rules": [
                {"field": "Th_Yb_Ratio", "operator": ">", "value": 2.0},
                {"field": "Nb_Yb_Ratio", "operator": "<=", "value": 10.0},
            ],
            "logic": "AND",
        },
        {
            "name": "DEPLETED MORB-LIKE",
            "color": "blue",
            "confidence_score": 1.0,
            "rules": [
                {"field": "Nb_Yb_Ratio", "operator": "between", "min": 0.5, "max": 2.0},
                {"field": "Th_Yb_Ratio", "operator": "<", "value": 0.5},
            ],
            "logic": "AND",
        },
        {
            "name": "ENRICHED MORB / TRANSITIONAL",
            "color": "cyan",
            "confidence_score": 1.0,
            "rules": [{"field": "Nb_Yb_Ratio", "operator": "between", "min": 2.0, "max": 10.0}],
            "logic": "AND",
        },
    ],
}


class TestPearceMAntleArray:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(PEARCE_SCHEME)

    def test_oib_plume_basalt(self, engine):
        """
        OIB plume basalt: Nb=80, Yb=3 → Nb/Yb=26.7 > 10.
        Typical Hawaiian tholeiite.
        """
        sample = {"Nb_Yb_Ratio": 26.7, "Th_Yb_Ratio": 1.5}
        name, _, _ = classify(engine, sample)
        assert name == "PLUME/OIB AFFINITY (Nb/Yb > 10)"

    def test_depleted_morb(self, engine):
        """
        Depleted N-MORB: Nb=2, Yb=2.5 → Nb/Yb=0.8; Th=0.2 → Th/Yb=0.08.
        """
        sample = {"Nb_Yb_Ratio": 0.8, "Th_Yb_Ratio": 0.08}
        name, _, _ = classify(engine, sample)
        assert name == "DEPLETED MORB-LIKE"

    def test_arc_crustal_contamination(self, engine):
        """
        Arc basalt with crustal contamination: Nb/Yb=3, Th/Yb=4.
        """
        sample = {"Nb_Yb_Ratio": 3.0, "Th_Yb_Ratio": 4.0}
        name, _, _ = classify(engine, sample)
        assert name == "CRUSTAL CONTAMINATION (High Th/Yb)"

    def test_enriched_morb(self, engine):
        """E-MORB: Nb/Yb=5, Th/Yb=0.3."""
        sample = {"Nb_Yb_Ratio": 5.0, "Th_Yb_Ratio": 0.3}
        name, _, _ = classify(engine, sample)
        assert name == "ENRICHED MORB / TRANSITIONAL"


# ---------------------------------------------------------------------------
# 6.  SEDIMENT GRAIN SIZE  —  Wentworth (1922)
# ---------------------------------------------------------------------------

GRAIN_SIZE_SCHEME = {
    "scheme_name": "Sediment Grain-Size (Wentworth)",
    "version": "1.1",
    "requires_fields": ["GrainSize_um"],
    "classifications": [
        {
            "name": "CLAY (<4 µm)",
            "color": "#3F51B5",
            "confidence_score": 0.95,
            "rules": [{"field": "GrainSize_um", "operator": "<", "value": 4.0}],
            "logic": "AND",
        },
        {
            "name": "SILT (4–63 µm)",
            "color": "#8BC34A",
            "confidence_score": 0.95,
            "rules": [{"field": "GrainSize_um", "operator": "between", "min": 4.0, "max": 63.0}],
            "logic": "AND",
        },
        {
            "name": "SAND (63–2000 µm)",
            "color": "#FFC107",
            "confidence_score": 0.95,
            "rules": [{"field": "GrainSize_um", "operator": "between", "min": 63.0, "max": 2000.0}],
            "logic": "AND",
        },
        {
            "name": "GRAVEL / PEBBLE (>2000 µm)",
            "color": "#795548",
            "confidence_score": 0.95,
            "rules": [{"field": "GrainSize_um", "operator": ">", "value": 2000.0}],
            "logic": "AND",
        },
    ],
}


class TestSedimentGrainSize:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(GRAIN_SIZE_SCHEME)

    def test_clay(self, engine):
        name, _, _ = classify(engine, {"GrainSize_um": 2.0})
        assert name == "CLAY (<4 µm)"

    def test_silt(self, engine):
        """Loess deposit — 30 µm grain."""
        name, _, _ = classify(engine, {"GrainSize_um": 30.0})
        assert name == "SILT (4–63 µm)"

    def test_fine_sand(self, engine):
        name, _, _ = classify(engine, {"GrainSize_um": 150.0})
        assert name == "SAND (63–2000 µm)"

    def test_gravel(self, engine):
        name, _, _ = classify(engine, {"GrainSize_um": 5000.0})
        assert name == "GRAVEL / PEBBLE (>2000 µm)"

    def test_clay_silt_boundary(self, engine):
        """4.0 µm is the clay/silt boundary (silt lower bound is inclusive)."""
        name, _, _ = classify(engine, {"GrainSize_um": 4.0})
        assert name == "SILT (4–63 µm)"

    def test_silt_sand_boundary(self, engine):
        """63.0 µm is the silt/sand boundary (sand lower bound is inclusive)."""
        name, _, _ = classify(engine, {"GrainSize_um": 63.0})
        assert name == "SAND (63–2000 µm)"


# ---------------------------------------------------------------------------
# 7.  WATER HARDNESS  (USGS / WQA)
# ---------------------------------------------------------------------------

WATER_HARDNESS_SCHEME = {
    "scheme_name": "Water Hardness Classification",
    "version": "1.1",
    "requires_fields": ["Hardness_mgL"],
    "classifications": [
        {
            "name": "SOFT",
            "color": "#4CAF50",
            "confidence_score": 0.95,
            "rules": [{"field": "Hardness_mgL", "operator": "<", "value": 60.0}],
            "logic": "AND",
        },
        {
            "name": "MODERATELY HARD",
            "color": "#FFC107",
            "confidence_score": 0.95,
            "rules": [{"field": "Hardness_mgL", "operator": "between", "min": 60.0, "max": 120.0}],
            "logic": "AND",
        },
        {
            "name": "HARD",
            "color": "#FF9800",
            "confidence_score": 0.95,
            "rules": [{"field": "Hardness_mgL", "operator": "between", "min": 120.0, "max": 180.0}],
            "logic": "AND",
        },
        {
            "name": "VERY HARD",
            "color": "#F44336",
            "confidence_score": 0.95,
            "rules": [{"field": "Hardness_mgL", "operator": ">", "value": 180.0}],
            "logic": "AND",
        },
    ],
}


class TestWaterHardness:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(WATER_HARDNESS_SCHEME)

    def test_soft_water(self, engine):
        """Rainwater / granite catchment: ~20 mg/L."""
        name, _, _ = classify(engine, {"Hardness_mgL": 20.0})
        assert name == "SOFT"

    def test_moderately_hard(self, engine):
        name, _, _ = classify(engine, {"Hardness_mgL": 90.0})
        assert name == "MODERATELY HARD"

    def test_hard_water(self, engine):
        """Limestone aquifer: ~150 mg/L."""
        name, _, _ = classify(engine, {"Hardness_mgL": 150.0})
        assert name == "HARD"

    def test_very_hard(self, engine):
        """Chalk/gypsum aquifer: 250 mg/L."""
        name, _, _ = classify(engine, {"Hardness_mgL": 250.0})
        assert name == "VERY HARD"

    def test_boundary_60(self, engine):
        """60.0 = start of MODERATELY HARD (between is inclusive)."""
        name, _, _ = classify(engine, {"Hardness_mgL": 60.0})
        assert name == "MODERATELY HARD"

    def test_boundary_180(self, engine):
        """180.0 = upper end of HARD range."""
        name, _, _ = classify(engine, {"Hardness_mgL": 180.0})
        assert name == "HARD"


# ---------------------------------------------------------------------------
# 8.  GEOACCUMULATION INDEX  (Müller 1969, 1981)
#     Igeo = log2(Cn / 1.5*Bn)
# ---------------------------------------------------------------------------

IGEO_SCHEME = {
    "scheme_name": "Geoaccumulation Index",
    "version": "1.1",
    "requires_fields": ["Igeo"],
    "classifications": [
        {
            "name": "Class 0: UNPOLLUTED (Igeo ≤ 0)",
            "color": "#4CAF50",
            "confidence_score": 0.95,
            "rules": [{"field": "Igeo", "operator": "<=", "value": 0.0}],
            "logic": "AND",
        },
        {
            "name": "Class 1: UNPOLLUTED TO MODERATELY POLLUTED",
            "color": "#8BC34A",
            "confidence_score": 0.90,
            "rules": [{"field": "Igeo", "operator": "between", "min": 0.0, "max": 1.0}],
            "logic": "AND",
        },
        {
            "name": "Class 2: MODERATELY POLLUTED",
            "color": "#FFC107",
            "confidence_score": 0.90,
            "rules": [{"field": "Igeo", "operator": "between", "min": 1.0, "max": 2.0}],
            "logic": "AND",
        },
        {
            "name": "Class 3: MODERATELY TO HEAVILY POLLUTED",
            "color": "#FF9800",
            "confidence_score": 0.90,
            "rules": [{"field": "Igeo", "operator": "between", "min": 2.0, "max": 3.0}],
            "logic": "AND",
        },
        {
            "name": "Class 4: HEAVILY POLLUTED",
            "color": "#F44336",
            "confidence_score": 0.90,
            "rules": [{"field": "Igeo", "operator": "between", "min": 3.0, "max": 4.0}],
            "logic": "AND",
        },
        {
            "name": "Class 5: HEAVILY TO EXTREMELY POLLUTED",
            "color": "#9C27B0",
            "confidence_score": 0.90,
            "rules": [{"field": "Igeo", "operator": "between", "min": 4.0, "max": 5.0}],
            "logic": "AND",
        },
        {
            "name": "Class 6: EXTREMELY POLLUTED",
            "color": "#000000",
            "confidence_score": 0.90,
            "rules": [{"field": "Igeo", "operator": ">", "value": 5.0}],
            "logic": "AND",
        },
    ],
}


class TestGeoaccumulationIndex:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(IGEO_SCHEME)

    def test_background_unpolluted(self, engine):
        name, _, _ = classify(engine, {"Igeo": -0.5})
        assert "UNPOLLUTED" in name and "MODERATELY" not in name

    def test_class1_light_enrichment(self, engine):
        name, _, _ = classify(engine, {"Igeo": 0.5})
        assert "Class 1" in name

    def test_class2_moderate(self, engine):
        name, _, _ = classify(engine, {"Igeo": 1.5})
        assert "Class 2" in name

    def test_class3_moderate_heavy(self, engine):
        name, _, _ = classify(engine, {"Igeo": 2.5})
        assert "Class 3" in name

    def test_class6_extreme(self, engine):
        name, _, _ = classify(engine, {"Igeo": 6.0})
        assert "EXTREMELY" in name

    def test_zero_boundary(self, engine):
        """Igeo = 0.0 → Class 0 (≤ 0 fires first)."""
        name, _, _ = classify(engine, {"Igeo": 0.0})
        assert "Class 0" in name


# ---------------------------------------------------------------------------
# 9.  USDA SOIL TEXTURE
#     Reference: USDA Soil Taxonomy (1999)
# ---------------------------------------------------------------------------

USDA_SOIL_SCHEME = {
    "scheme_name": "USDA Soil Texture Classification",
    "version": "1.1",
    "requires_fields": ["Sand_pct", "Silt_pct", "Clay_pct"],
    "classifications": [
        {
            "name": "CLAY",
            "color": "#9C27B0",
            "confidence_score": 0.95,
            "rules": [{"field": "Clay_pct", "operator": ">=", "value": 40.0}],
            "logic": "AND",
        },
        {
            "name": "SAND",
            "color": "#F44336",
            "confidence_score": 0.95,
            "rules": [
                {"field": "Sand_pct", "operator": ">", "value": 85.0},
                {"field": "Clay_pct", "operator": "<", "value": 10.0},
            ],
            "logic": "AND",
        },
        {
            "name": "SILT LOAM",
            "color": "#4CAF50",
            "confidence_score": 0.90,
            "rules": [
                {"field": "Silt_pct", "operator": ">", "value": 50.0},
                {"field": "Clay_pct", "operator": "between", "min": 12.0, "max": 27.0},
            ],
            "logic": "AND",
        },
    ],
}


class TestUSDAsoil:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(USDA_SOIL_SCHEME)

    def test_clay_soil(self, engine):
        """Heavy clay: Sand=10, Silt=30, Clay=60."""
        name, _, _ = classify(engine, {"Sand_pct": 10.0, "Silt_pct": 30.0, "Clay_pct": 60.0})
        assert name == "CLAY"

    def test_clay_boundary_40(self, engine):
        """Exactly 40% clay → CLAY."""
        name, _, _ = classify(engine, {"Sand_pct": 30.0, "Silt_pct": 30.0, "Clay_pct": 40.0})
        assert name == "CLAY"

    def test_sand_soil(self, engine):
        """Desert sand: Sand=92, Clay=3."""
        name, _, _ = classify(engine, {"Sand_pct": 92.0, "Silt_pct": 5.0, "Clay_pct": 3.0})
        assert name == "SAND"

    def test_silt_loam(self, engine):
        """Typical agricultural silt loam: Silt=60, Clay=20."""
        name, _, _ = classify(engine, {"Sand_pct": 20.0, "Silt_pct": 60.0, "Clay_pct": 20.0})
        assert name == "SILT LOAM"


# ---------------------------------------------------------------------------
# 10.  CERAMIC FIRING TEMPERATURE
#      Reference: Tite (2008); Quinn (2013)
# ---------------------------------------------------------------------------

CERAMIC_FIRING_SCHEME = {
    "scheme_name": "Ceramic Firing Temperature Proxies",
    "version": "1.1",
    "requires_fields": ["Fe2O3_pct", "TiO2_pct", "MagSus_10e6_si"],
    "classifications": [
        {
            "name": "LOW-FIRE (<700°C)",
            "color": "#FFC107",
            "confidence_score": 0.85,
            "rules": [
                {"field": "Fe2O3_TiO2_Ratio", "operator": ">", "value": 6.0},
                {"field": "MagSus_10e6_si", "operator": "<", "value": 100.0},
            ],
            "logic": "AND",
        },
        {
            "name": "MID-FIRE (700–900°C)",
            "color": "#4CAF50",
            "confidence_score": 0.80,
            "rules": [
                {"field": "Fe2O3_TiO2_Ratio", "operator": "between", "min": 3.0, "max": 6.0},
            ],
            "logic": "AND",
        },
        {
            "name": "HIGH-FIRE (>900°C)",
            "color": "#F44336",
            "confidence_score": 0.80,
            "rules": [
                {"field": "Fe2O3_TiO2_Ratio", "operator": "<", "value": 3.0},
            ],
            "logic": "AND",
        },
    ],
}


class TestCeramicFiring:
    @pytest.fixture
    def engine(self):
        return scheme_from_json(CERAMIC_FIRING_SCHEME)

    def test_low_fire_pottery(self, engine):
        """
        Neolithic open-air fired pottery: Fe/Ti ratio ~8, low MagSus.
        """
        sample = {"Fe2O3_TiO2_Ratio": 8.0, "MagSus_10e6_si": 60.0}
        name, _, _ = classify(engine, sample)
        assert name == "LOW-FIRE (<700°C)"

    def test_mid_fire_kiln(self, engine):
        """
        Early kiln-fired ware: Fe/Ti ratio ≈ 4.5.
        """
        sample = {"Fe2O3_TiO2_Ratio": 4.5, "MagSus_10e6_si": 200.0}
        name, _, _ = classify(engine, sample)
        assert name == "MID-FIRE (700–900°C)"

    def test_high_fire_stoneware(self, engine):
        """
        High-fired stoneware / terracotta: Fe/Ti ratio < 3.
        """
        sample = {"Fe2O3_TiO2_Ratio": 1.5, "MagSus_10e6_si": 350.0}
        name, _, _ = classify(engine, sample)
        assert name == "HIGH-FIRE (>900°C)"
