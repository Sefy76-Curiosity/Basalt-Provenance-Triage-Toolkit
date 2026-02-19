"""
test_evaluate_rule.py
=====================
Unit tests for ClassificationEngine.evaluate_rule().

Every supported operator is tested:
  >  <  >=  <=  ==  between  not_between

Edge cases:
  missing field, None value, non-numeric string, bad operator,
  between with list-format value vs min/max dict format,
  boundary conditions (inclusive/exclusive), floating-point equality.
"""

import pytest
from conftest import make_engine


@pytest.fixture
def engine():
    return make_engine({})


# ---------------------------------------------------------------------------
# Greater-than  >
# ---------------------------------------------------------------------------

class TestGreaterThan:
    def test_above_threshold_is_true(self, engine):
        rule = {"field": "x", "operator": ">", "value": 10}
        assert engine.evaluate_rule({"x": 11}, rule) is True

    def test_at_threshold_is_false(self, engine):
        rule = {"field": "x", "operator": ">", "value": 10}
        assert engine.evaluate_rule({"x": 10}, rule) is False

    def test_below_threshold_is_false(self, engine):
        rule = {"field": "x", "operator": ">", "value": 10}
        assert engine.evaluate_rule({"x": 9}, rule) is False

    def test_large_value(self, engine):
        rule = {"field": "x", "operator": ">", "value": 0}
        assert engine.evaluate_rule({"x": 1_000_000}, rule) is True

    def test_negative_values(self, engine):
        rule = {"field": "x", "operator": ">", "value": -5}
        assert engine.evaluate_rule({"x": -3}, rule) is True
        assert engine.evaluate_rule({"x": -7}, rule) is False


# ---------------------------------------------------------------------------
# Less-than  <
# ---------------------------------------------------------------------------

class TestLessThan:
    def test_below_threshold_is_true(self, engine):
        rule = {"field": "x", "operator": "<", "value": 10}
        assert engine.evaluate_rule({"x": 9}, rule) is True

    def test_at_threshold_is_false(self, engine):
        rule = {"field": "x", "operator": "<", "value": 10}
        assert engine.evaluate_rule({"x": 10}, rule) is False

    def test_above_threshold_is_false(self, engine):
        rule = {"field": "x", "operator": "<", "value": 10}
        assert engine.evaluate_rule({"x": 11}, rule) is False

    def test_isotope_value_negative(self, engine):
        """δ13C values are negative — common in isotope archaeology."""
        rule = {"field": "d13C", "operator": "<", "value": -18.5}
        assert engine.evaluate_rule({"d13C": -20.0}, rule) is True
        assert engine.evaluate_rule({"d13C": -18.5}, rule) is False
        assert engine.evaluate_rule({"d13C": -15.0}, rule) is False


# ---------------------------------------------------------------------------
# Greater-than-or-equal  >=
# ---------------------------------------------------------------------------

class TestGreaterEqual:
    def test_above_is_true(self, engine):
        rule = {"field": "x", "operator": ">=", "value": 40}
        assert engine.evaluate_rule({"x": 50}, rule) is True

    def test_at_boundary_is_true(self, engine):
        rule = {"field": "x", "operator": ">=", "value": 40}
        assert engine.evaluate_rule({"x": 40}, rule) is True

    def test_below_is_false(self, engine):
        rule = {"field": "x", "operator": ">=", "value": 40}
        assert engine.evaluate_rule({"x": 39.9}, rule) is False

    def test_usda_clay_boundary(self, engine):
        """USDA: Clay >= 40% → CLAY classification."""
        rule = {"field": "Clay_pct", "operator": ">=", "value": 40.0}
        assert engine.evaluate_rule({"Clay_pct": 40.0}, rule) is True
        assert engine.evaluate_rule({"Clay_pct": 39.9}, rule) is False


# ---------------------------------------------------------------------------
# Less-than-or-equal  <=
# ---------------------------------------------------------------------------

class TestLessEqual:
    def test_below_is_true(self, engine):
        rule = {"field": "x", "operator": "<=", "value": 7}
        assert engine.evaluate_rule({"x": 6}, rule) is True

    def test_at_boundary_is_true(self, engine):
        rule = {"field": "x", "operator": "<=", "value": 7}
        assert engine.evaluate_rule({"x": 7}, rule) is True

    def test_above_is_false(self, engine):
        rule = {"field": "x", "operator": "<=", "value": 7}
        assert engine.evaluate_rule({"x": 7.1}, rule) is False

    def test_igeo_class0_boundary(self, engine):
        """Igeo ≤ 0 → Class 0: UNPOLLUTED (Müller 1969)."""
        rule = {"field": "Igeo", "operator": "<=", "value": 0.0}
        assert engine.evaluate_rule({"Igeo": 0.0}, rule) is True
        assert engine.evaluate_rule({"Igeo": -1.5}, rule) is True
        assert engine.evaluate_rule({"Igeo": 0.01}, rule) is False


# ---------------------------------------------------------------------------
# Equality  ==
# ---------------------------------------------------------------------------

class TestEquality:
    def test_equal_values(self, engine):
        rule = {"field": "x", "operator": "==", "value": 5}
        assert engine.evaluate_rule({"x": 5}, rule) is True

    def test_slightly_different_triggers_tolerance(self, engine):
        """Engine uses abs(a-b) < 0.0001 tolerance."""
        rule = {"field": "x", "operator": "==", "value": 5.0}
        assert engine.evaluate_rule({"x": 5.00005}, rule) is True
        assert engine.evaluate_rule({"x": 5.001}, rule) is False

    def test_float_precision(self, engine):
        rule = {"field": "x", "operator": "==", "value": 1.0}
        assert engine.evaluate_rule({"x": 1.0}, rule) is True


# ---------------------------------------------------------------------------
# Between  (inclusive on both ends)
# ---------------------------------------------------------------------------

class TestBetween:
    def test_in_range_min_max_format(self, engine):
        """between using min/max keys (primary JSON format)."""
        rule = {"field": "score", "operator": "between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"score": 3.2}, rule) is True

    def test_at_lower_bound_inclusive(self, engine):
        rule = {"field": "score", "operator": "between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"score": 2.9}, rule) is True

    def test_at_upper_bound_inclusive(self, engine):
        rule = {"field": "score", "operator": "between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"score": 3.6}, rule) is True

    def test_below_range_is_false(self, engine):
        rule = {"field": "score", "operator": "between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"score": 2.8}, rule) is False

    def test_above_range_is_false(self, engine):
        rule = {"field": "score", "operator": "between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"score": 3.7}, rule) is False

    def test_in_range_list_value_format(self, engine):
        """between using 'value': [min, max] alternative format."""
        rule = {"field": "score", "operator": "between", "value": [2.9, 3.6]}
        assert engine.evaluate_rule({"score": 3.0}, rule) is True

    def test_list_format_out_of_range(self, engine):
        rule = {"field": "score", "operator": "between", "value": [2.9, 3.6]}
        assert engine.evaluate_rule({"score": 4.0}, rule) is False

    def test_bone_collagen_cn_pass(self, engine):
        """Bone Collagen QC: C:N ratio 2.9–3.6 = preserved (DeNiro 1985)."""
        rule = {"field": "C_N_Ratio", "operator": "between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"C_N_Ratio": 3.2}, rule) is True   # typical good bone
        assert engine.evaluate_rule({"C_N_Ratio": 3.6}, rule) is True   # boundary
        assert engine.evaluate_rule({"C_N_Ratio": 4.0}, rule) is False  # degraded

    def test_grain_size_silt_range(self, engine):
        """Wentworth (1922): Silt = 4–63 µm."""
        rule = {"field": "GrainSize_um", "operator": "between", "min": 4.0, "max": 63.0}
        assert engine.evaluate_rule({"GrainSize_um": 30.0}, rule) is True
        assert engine.evaluate_rule({"GrainSize_um": 4.0}, rule) is True
        assert engine.evaluate_rule({"GrainSize_um": 63.0}, rule) is True
        assert engine.evaluate_rule({"GrainSize_um": 3.9}, rule) is False
        assert engine.evaluate_rule({"GrainSize_um": 63.1}, rule) is False


# ---------------------------------------------------------------------------
# Not-between
# ---------------------------------------------------------------------------

class TestNotBetween:
    def test_outside_range_is_true(self, engine):
        rule = {"field": "score", "operator": "not_between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"score": 5.0}, rule) is True
        assert engine.evaluate_rule({"score": 1.0}, rule) is True

    def test_inside_range_is_false(self, engine):
        rule = {"field": "score", "operator": "not_between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"score": 3.2}, rule) is False

    def test_at_boundary_is_false(self, engine):
        """At the boundary it IS between, so not_between → False."""
        rule = {"field": "score", "operator": "not_between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"score": 2.9}, rule) is False
        assert engine.evaluate_rule({"score": 3.6}, rule) is False

    def test_degraded_bone_collagen(self, engine):
        """Degraded bone: C:N outside 2.9–3.6."""
        rule = {"field": "C_N_Ratio", "operator": "not_between", "min": 2.9, "max": 3.6}
        assert engine.evaluate_rule({"C_N_Ratio": 4.5}, rule) is True
        assert engine.evaluate_rule({"C_N_Ratio": 2.0}, rule) is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_missing_field_returns_false(self, engine):
        rule = {"field": "nonexistent", "operator": ">", "value": 0}
        assert engine.evaluate_rule({"other_field": 5}, rule) is False

    def test_none_value_returns_false(self, engine):
        """A None measurement should never cause an exception."""
        rule = {"field": "x", "operator": ">", "value": 0}
        result = engine.evaluate_rule({"x": None}, rule)
        assert result is False

    def test_string_value_returns_false(self, engine):
        """Non-numeric strings in numeric fields must not raise."""
        rule = {"field": "x", "operator": ">", "value": 0}
        result = engine.evaluate_rule({"x": "not-a-number"}, rule)
        assert result is False

    def test_unknown_operator_returns_false(self, engine):
        rule = {"field": "x", "operator": "contains", "value": 5}
        assert engine.evaluate_rule({"x": 5}, rule) is False

    def test_empty_rule_dict_returns_false(self, engine):
        assert engine.evaluate_rule({"x": 5}, {}) is False

    def test_between_missing_bounds_returns_false(self, engine):
        """between without min/max keys and without value list → False."""
        rule = {"field": "x", "operator": "between"}
        assert engine.evaluate_rule({"x": 5}, rule) is False

    def test_zero_value_boundary(self, engine):
        """Zero is a valid scientific measurement."""
        rule = {"field": "Igeo", "operator": "<=", "value": 0.0}
        assert engine.evaluate_rule({"Igeo": 0.0}, rule) is True

    def test_very_small_float(self, engine):
        rule = {"field": "x", "operator": ">", "value": 0.0}
        assert engine.evaluate_rule({"x": 1e-10}, rule) is True

    def test_integer_sample_value_accepted(self, engine):
        """Integer measurements should work the same as floats."""
        rule = {"field": "Clay_pct", "operator": ">=", "value": 40.0}
        assert engine.evaluate_rule({"Clay_pct": 42}, rule) is True
