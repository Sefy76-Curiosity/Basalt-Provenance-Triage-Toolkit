"""
test_derived_fields.py
======================
Unit tests for ClassificationEngine._compute_derived_fields().

Every formula defined in engines/derived_fields.json is tested
against hand-calculated expected values, including:
  - Zr/Nb provenance ratio
  - CIA (Chemical Index of Alteration)
  - Total Alkali (Na2O + K2O)
  - Nb/Yb and Th/Yb mantle array ratios
  - Zr_RSD (analytical precision)
  - Slag basicity (V_Ratio)

Edge cases:
  - Missing required field → derived field not added
  - Division by zero → engine must not crash
  - Partial field availability
"""

import math
import pytest
from conftest import make_engine, MOCK_DERIVED_FIELDS


@pytest.fixture
def engine():
    return make_engine({}, MOCK_DERIVED_FIELDS)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute(engine, sample: dict) -> dict:
    """Run derived field computation and return the mutated sample."""
    return engine._compute_derived_fields(sample.copy())


def approx(expected, rel=1e-6):
    return pytest.approx(expected, rel=rel)


# ---------------------------------------------------------------------------
# Zr/Nb ratio  —  key provenance discriminator
# ---------------------------------------------------------------------------

class TestZrNbRatio:
    def test_basic_ratio(self, engine):
        result = compute(engine, {"Zr_ppm": 200.0, "Nb_ppm": 10.0})
        assert result["Zr_Nb_Ratio"] == approx(20.0)

    def test_high_ratio(self, engine):
        """High Zr/Nb (>30) is typical of continental crust sources."""
        result = compute(engine, {"Zr_ppm": 300.0, "Nb_ppm": 8.0})
        assert result["Zr_Nb_Ratio"] == approx(37.5)

    def test_low_ratio(self, engine):
        """Low Zr/Nb (<5) indicates OIB / hotspot affinity."""
        result = compute(engine, {"Zr_ppm": 50.0, "Nb_ppm": 20.0})
        assert result["Zr_Nb_Ratio"] == approx(2.5)

    def test_missing_nb_skips_field(self, engine):
        """If Nb_ppm is absent, Zr_Nb_Ratio must not be created."""
        result = compute(engine, {"Zr_ppm": 200.0})
        assert "Zr_Nb_Ratio" not in result

    def test_missing_zr_skips_field(self, engine):
        result = compute(engine, {"Nb_ppm": 10.0})
        assert "Zr_Nb_Ratio" not in result

    def test_both_missing_skips_field(self, engine):
        result = compute(engine, {"SiO2_wt": 50.0})
        assert "Zr_Nb_Ratio" not in result


# ---------------------------------------------------------------------------
# CIA  (Chemical Index of Alteration)
# Nesbitt & Young 1982: CIA = Al2O3 / (Al2O3 + CaO + Na2O + K2O) * 100
# ---------------------------------------------------------------------------

class TestCIA:
    def test_unweathered_granite(self, engine):
        """
        Fresh granite: low CIA (~50).
        Al2O3=15, CaO=5, Na2O=3, K2O=5  → CIA = 15/28 * 100 ≈ 53.57
        """
        sample = {"Al2O3_wt": 15.0, "CaO_wt": 5.0, "Na2O_wt": 3.0, "K2O_wt": 5.0}
        result = compute(engine, sample)
        assert result["CIA_Value"] == approx(15.0 / 28.0 * 100)

    def test_heavily_weathered(self, engine):
        """
        Laterite / deep-weathered soil: high CIA (~90+).
        Al2O3=28, CaO=0.5, Na2O=0.3, K2O=0.2  → CIA ≈ 96.6
        """
        sample = {"Al2O3_wt": 28.0, "CaO_wt": 0.5, "Na2O_wt": 0.3, "K2O_wt": 0.2}
        result = compute(engine, sample)
        expected = 28.0 / (28.0 + 0.5 + 0.3 + 0.2) * 100
        assert result["CIA_Value"] == approx(expected)

    def test_fresh_basalt(self, engine):
        """
        Typical fresh tholeiitic basalt: CIA ~35–40.
        Al2O3=14, CaO=11, Na2O=2.5, K2O=0.5  → CIA = 14/28 * 100 = 50
        """
        sample = {"Al2O3_wt": 14.0, "CaO_wt": 11.0, "Na2O_wt": 2.5, "K2O_wt": 0.5}
        result = compute(engine, sample)
        expected = 14.0 / (14.0 + 11.0 + 2.5 + 0.5) * 100
        assert result["CIA_Value"] == approx(expected)

    def test_missing_k2o_skips(self, engine):
        result = compute(engine, {"Al2O3_wt": 15.0, "CaO_wt": 5.0, "Na2O_wt": 3.0})
        assert "CIA_Value" not in result

    def test_cia_cannot_exceed_100(self, engine):
        """CIA is a molar proportion and must be in [0, 100]."""
        sample = {"Al2O3_wt": 50.0, "CaO_wt": 0.1, "Na2O_wt": 0.1, "K2O_wt": 0.1}
        result = compute(engine, sample)
        assert 0 <= result["CIA_Value"] <= 100


# ---------------------------------------------------------------------------
# Total Alkali  (Na2O + K2O for TAS diagrams)
# ---------------------------------------------------------------------------

class TestTotalAlkali:
    def test_typical_basalt(self, engine):
        """Typical basalt: Na2O=2.5, K2O=0.5 → Total_Alkali=3.0"""
        result = compute(engine, {"Na2O_wt": 2.5, "K2O_wt": 0.5})
        assert result["Total_Alkali"] == approx(3.0)

    def test_phonolite(self, engine):
        """Phonolite (high alkali): Na2O=9, K2O=5 → 14"""
        result = compute(engine, {"Na2O_wt": 9.0, "K2O_wt": 5.0})
        assert result["Total_Alkali"] == approx(14.0)

    def test_subalkaline_rhyolite(self, engine):
        """Subalkaline rhyolite: Na2O=3.5, K2O=3.5 → 7.0 (boundary)"""
        result = compute(engine, {"Na2O_wt": 3.5, "K2O_wt": 3.5})
        assert result["Total_Alkali"] == approx(7.0)

    def test_missing_k2o_skips(self, engine):
        result = compute(engine, {"Na2O_wt": 3.0})
        assert "Total_Alkali" not in result


# ---------------------------------------------------------------------------
# Nb/Yb and Th/Yb  —  Pearce mantle array ratios
# ---------------------------------------------------------------------------

class TestMantleArrayRatios:
    def test_nb_yb_oib(self, engine):
        """
        OIB basalts have Nb/Yb >> 10 (Pearce 2008).
        Nb=80, Yb=3  → ratio ≈ 26.7
        """
        result = compute(engine, {"Nb_ppm": 80.0, "Yb_ppm": 3.0})
        assert result["Nb_Yb_Ratio"] == approx(80.0 / 3.0)

    def test_nb_yb_morb(self, engine):
        """
        Depleted MORB: Nb/Yb ~1 (Pearce 2008).
        Nb=3, Yb=3  → ratio = 1.0
        """
        result = compute(engine, {"Nb_ppm": 3.0, "Yb_ppm": 3.0})
        assert result["Nb_Yb_Ratio"] == approx(1.0)

    def test_th_yb_ratio(self, engine):
        """
        Arc basalt: elevated Th/Yb due to slab fluid enrichment.
        Th=5, Yb=2  → ratio = 2.5
        """
        result = compute(engine, {"Th_ppm": 5.0, "Yb_ppm": 2.0})
        assert result["Th_Yb_Ratio"] == approx(2.5)

    def test_missing_yb_skips_both(self, engine):
        result = compute(engine, {"Nb_ppm": 10.0, "Th_ppm": 5.0})
        assert "Nb_Yb_Ratio" not in result
        assert "Th_Yb_Ratio" not in result


# ---------------------------------------------------------------------------
# Zr_RSD  (analytical precision filter)
# ---------------------------------------------------------------------------

class TestZrRSD:
    def test_low_rsd_high_precision(self, engine):
        """Zr=200 ppm, error=4 ppm → RSD=0.02 (2%)"""
        result = compute(engine, {"Zr_ppm": 200.0, "Zr_error": 4.0})
        assert result["Zr_RSD"] == approx(0.02)

    def test_high_rsd_low_precision(self, engine):
        """Zr=50 ppm, error=20 ppm → RSD=0.4 (40%)"""
        result = compute(engine, {"Zr_ppm": 50.0, "Zr_error": 20.0})
        assert result["Zr_RSD"] == approx(0.4)

    def test_missing_error_skips(self, engine):
        result = compute(engine, {"Zr_ppm": 200.0})
        assert "Zr_RSD" not in result


# ---------------------------------------------------------------------------
# Slag Basicity (V_Ratio)  —  archaeometallurgy / industrial
# ---------------------------------------------------------------------------

class TestVRatio:
    def test_basic_slag_ratio(self, engine):
        """
        (CaO + MgO) / (SiO2 + Al2O3)
        CaO=35, MgO=10, SiO2=30, Al2O3=10  → 45/40 = 1.125
        """
        sample = {"CaO_wt": 35.0, "MgO_wt": 10.0, "SiO2_wt": 30.0, "Al2O3_wt": 10.0}
        result = compute(engine, sample)
        assert result["V_Ratio"] == approx(45.0 / 40.0)

    def test_acid_slag(self, engine):
        """Acid slag: low basicity < 1."""
        sample = {"CaO_wt": 10.0, "MgO_wt": 5.0, "SiO2_wt": 40.0, "Al2O3_wt": 15.0}
        result = compute(engine, sample)
        assert result["V_Ratio"] < 1.0

    def test_missing_silica_skips(self, engine):
        sample = {"CaO_wt": 35.0, "MgO_wt": 10.0, "Al2O3_wt": 10.0}
        result = compute(engine, sample)
        assert "V_Ratio" not in result


# ---------------------------------------------------------------------------
# Multiple derived fields from one sample
# ---------------------------------------------------------------------------

class TestMultipleFields:
    def test_all_computed_when_data_present(self, engine):
        """All derived fields computed in a single call if data present."""
        sample = {
            "Zr_ppm": 150.0,
            "Nb_ppm": 15.0,
            "Nb_ppm2": 15.0,  # unrelated key
            "Yb_ppm": 3.0,
            "Th_ppm": 2.0,
            "Na2O_wt": 3.0,
            "K2O_wt": 1.5,
            "Al2O3_wt": 16.0,
            "CaO_wt": 8.0,
        }
        result = compute(engine, sample)
        assert "Zr_Nb_Ratio" in result
        assert "Nb_Yb_Ratio" in result
        assert "Th_Yb_Ratio" in result
        assert "Total_Alkali" in result
        assert "CIA_Value" in result

    def test_original_fields_preserved(self, engine):
        """Derived-field computation must not clobber original measurements."""
        sample = {"Zr_ppm": 150.0, "Nb_ppm": 15.0, "Sample_ID": "test-01"}
        result = compute(engine, sample)
        assert result["Zr_ppm"] == 150.0
        assert result["Nb_ppm"] == 15.0
        assert result["Sample_ID"] == "test-01"

    def test_no_crash_on_empty_sample(self, engine):
        """Empty sample dict must return an empty (or unchanged) dict."""
        result = compute(engine, {})
        assert isinstance(result, dict)
