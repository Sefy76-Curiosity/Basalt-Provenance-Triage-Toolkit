"""
test_engine_core.py
====================
Tests for the ClassificationEngine infrastructure:

  - Scheme loading validation (required fields enforced)
  - get_available_schemes() output format
  - _normalize_sample() with dict, pandas Series, invalid types
  - classify_sample() with unknown scheme_id
  - classify_all_samples() batch mode
  - Multi-rule AND / OR logic
  - matches_classification() helper

These tests do NOT depend on real JSON files on disk.
"""

import pytest
from conftest import make_engine, MOCK_SCHEMES, MOCK_DERIVED_FIELDS


# ---------------------------------------------------------------------------
# Engine initialization and scheme listing
# ---------------------------------------------------------------------------

class TestGetAvailableSchemes:
    def test_returns_list(self, engine):
        schemes = engine.get_available_schemes()
        assert isinstance(schemes, list)

    def test_each_entry_has_required_keys(self, engine):
        for entry in engine.get_available_schemes():
            assert "id" in entry
            assert "name" in entry

    def test_scheme_count_matches(self, engine):
        schemes = engine.get_available_schemes()
        assert len(schemes) == len(MOCK_SCHEMES)

    def test_scheme_ids_match_keys(self, engine):
        ids = {s["id"] for s in engine.get_available_schemes()}
        assert ids == set(MOCK_SCHEMES.keys())


# ---------------------------------------------------------------------------
# _normalize_sample()
# ---------------------------------------------------------------------------

class TestNormalizeSample:
    def test_dict_passes_through(self, engine):
        sample = {"x": 1, "y": 2}
        assert engine._normalize_sample(sample) == sample

    def test_pandas_series_converted(self, engine):
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")
        series = pd.Series({"x": 1, "y": 2})
        result = engine._normalize_sample(series)
        assert isinstance(result, dict)
        assert result["x"] == 1

    def test_invalid_type_returns_none(self, engine):
        assert engine._normalize_sample([1, 2, 3]) is None
        assert engine._normalize_sample("string") is None
        assert engine._normalize_sample(42) is None

    def test_empty_dict_accepted(self, engine):
        assert engine._normalize_sample({}) == {}


# ---------------------------------------------------------------------------
# classify_sample() — engine-level errors and control flow
# ---------------------------------------------------------------------------

class TestClassifySampleControlFlow:
    def test_unknown_scheme_returns_error_label(self, engine):
        name, conf, color = engine.classify_sample({"x": 5}, "nonexistent_scheme")
        assert name == "SCHEME_NOT_FOUND"
        assert conf == 0.0

    def test_invalid_sample_type_returns_error(self, engine):
        name, conf, color = engine.classify_sample([1, 2, 3], "mock_threshold")
        assert name == "INVALID_SAMPLE"
        assert conf == 0.0

    def test_no_matching_rule_returns_unclassified(self, engine):
        """
        A scheme where the sample has the required field but no rule fires
        (e.g. a gap in coverage) should return UNCLASSIFIED gracefully.
        """
        gap_scheme = {
            "mock_gap": {
                "scheme_name": "Gap Test",
                "version": "1.0",
                "requires_fields": ["value"],
                "classifications": [
                    {
                        "name": "LOW",
                        "color": "#00FF00",
                        "confidence_score": 0.9,
                        "rules": [{"field": "value", "operator": "<", "value": 10}],
                        "logic": "AND",
                    },
                    {
                        "name": "HIGH",
                        "color": "#FF0000",
                        "confidence_score": 0.9,
                        "rules": [{"field": "value", "operator": ">", "value": 100}],
                        "logic": "AND",
                    },
                    # 10–100 is not covered → UNCLASSIFIED
                ],
            }
        }
        eng = make_engine(gap_scheme)
        name, conf, _ = eng.classify_sample({"value": 50}, "mock_gap")
        assert name == "UNCLASSIFIED"
        assert conf == 0.0

    def test_first_matching_rule_wins(self, engine):
        """
        When multiple rules could match, the FIRST classification in the list
        that passes all its rules is returned.
        """
        # In mock_threshold: HIGH fires first when value > 100.
        # LOW would also fire with <= 100, but value=150 doesn't satisfy that.
        name, _, _ = engine.classify_sample({"value": 150}, "mock_threshold")
        assert name == "HIGH"

    def test_returns_confidence_and_color(self, engine):
        _, conf, color = engine.classify_sample({"value": 150}, "mock_threshold")
        assert isinstance(conf, float)
        assert isinstance(color, str)
        assert 0.0 <= conf <= 1.0

    def test_confidence_zero_for_unclassified(self, engine):
        _, conf, _ = engine.classify_sample({}, "mock_threshold")
        assert conf == 0.0


# ---------------------------------------------------------------------------
# Multi-rule AND logic
# ---------------------------------------------------------------------------

class TestMultiRuleAND:
    def test_both_rules_pass(self, engine):
        """mock_multi_and: x > 5 AND y < 20 → MATCH."""
        name, _, _ = engine.classify_sample({"x": 10, "y": 15}, "mock_multi_and")
        assert name == "MATCH"

    def test_first_rule_fails(self, engine):
        """x = 3 (not > 5) → AND fails → UNCLASSIFIED."""
        name, _, _ = engine.classify_sample({"x": 3, "y": 15}, "mock_multi_and")
        assert name == "UNCLASSIFIED"

    def test_second_rule_fails(self, engine):
        """y = 25 (not < 20) → AND fails → UNCLASSIFIED."""
        name, _, _ = engine.classify_sample({"x": 10, "y": 25}, "mock_multi_and")
        assert name == "UNCLASSIFIED"

    def test_both_rules_fail(self, engine):
        name, _, _ = engine.classify_sample({"x": 2, "y": 30}, "mock_multi_and")
        assert name == "UNCLASSIFIED"


# ---------------------------------------------------------------------------
# matches_classification() helper
# ---------------------------------------------------------------------------

class TestMatchesClassification:
    def test_and_logic_all_pass(self, engine):
        classification = {
            "logic": "AND",
            "rules": [
                {"field": "a", "operator": ">", "value": 0},
                {"field": "b", "operator": "<", "value": 10},
            ],
        }
        assert engine.matches_classification({"a": 5, "b": 5}, classification) is True

    def test_and_logic_one_fails(self, engine):
        classification = {
            "logic": "AND",
            "rules": [
                {"field": "a", "operator": ">", "value": 0},
                {"field": "b", "operator": "<", "value": 10},
            ],
        }
        assert engine.matches_classification({"a": 5, "b": 15}, classification) is False

    def test_or_logic_one_passes(self, engine):
        classification = {
            "logic": "OR",
            "rules": [
                {"field": "a", "operator": ">", "value": 100},
                {"field": "b", "operator": "<", "value": 5},
            ],
        }
        # a=5 doesn't satisfy >100 but b=3 satisfies <5 → OR passes
        assert engine.matches_classification({"a": 5, "b": 3}, classification) is True

    def test_or_logic_none_pass(self, engine):
        classification = {
            "logic": "OR",
            "rules": [
                {"field": "a", "operator": ">", "value": 100},
                {"field": "b", "operator": "<", "value": 5},
            ],
        }
        assert engine.matches_classification({"a": 5, "b": 10}, classification) is False

    def test_empty_rules_returns_false(self, engine):
        classification = {"logic": "AND", "rules": []}
        assert engine.matches_classification({"a": 5}, classification) is False

    def test_invalid_input_returns_false(self, engine):
        assert engine.matches_classification({"x": 1}, None) is False
        assert engine.matches_classification({"x": 1}, "not a dict") is False


# ---------------------------------------------------------------------------
# classify_all_samples() — batch mode
# ---------------------------------------------------------------------------

class TestClassifyAllSamples:
    def test_list_of_dicts(self, engine):
        samples = [
            {"value": 50, "Sample_ID": "A"},
            {"value": 150, "Sample_ID": "B"},
        ]
        result = engine.classify_all_samples(samples, "mock_threshold")
        assert isinstance(result, list)
        assert len(result) == 2

    def test_unknown_scheme_returns_unchanged(self, engine):
        samples = [{"value": 50}]
        result = engine.classify_all_samples(samples, "bad_scheme")
        # Engine logs a warning and returns original samples
        assert result == samples

    def test_pandas_dataframe_input(self, engine):
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")
        df = pd.DataFrame([{"value": 50}, {"value": 150}])
        result = engine.classify_all_samples(df, "mock_threshold")
        assert isinstance(result, list)
        assert len(result) == 2

    def test_empty_list(self, engine):
        result = engine.classify_all_samples([], "mock_threshold")
        assert result == []


# ---------------------------------------------------------------------------
# _clean_error_fields()
# ---------------------------------------------------------------------------

class TestCleanErrorFields:
    def test_strips_plus_minus_symbol(self, engine):
        sample = {"Zr_error": "±5.2"}
        result = engine._clean_error_fields(sample)
        assert result["Zr_error"] == pytest.approx(5.2)

    def test_strips_percent(self, engine):
        sample = {"Zr_error": "3.1%"}
        result = engine._clean_error_fields(sample)
        assert result["Zr_error"] == pytest.approx(3.1)

    def test_strips_ppm_unit(self, engine):
        sample = {"Zr_error": "4.0ppm"}
        result = engine._clean_error_fields(sample)
        assert result["Zr_error"] == pytest.approx(4.0)

    def test_numeric_value_unchanged(self, engine):
        sample = {"Zr_error": 5.0}
        result = engine._clean_error_fields(sample)
        assert result["Zr_error"] == pytest.approx(5.0)

    def test_unparseable_becomes_none(self, engine):
        sample = {"Zr_error": "N/A"}
        result = engine._clean_error_fields(sample)
        assert result["Zr_error"] is None


# ---------------------------------------------------------------------------
# Scheme loading validation
# ---------------------------------------------------------------------------

class TestSchemeValidation:
    def test_missing_required_field_raises(self, bare_engine):
        from pathlib import Path
        import tempfile, json, os

        bad_scheme = {
            # scheme_name is missing
            "version": "1.0",
            "classifications": [],
            "requires_fields": [],
        }
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False
        ) as f:
            json.dump(bad_scheme, f)
            fname = f.name

        try:
            with pytest.raises((ValueError, KeyError, Exception)):
                bare_engine.load_scheme(Path(fname))
        finally:
            os.unlink(fname)

    def test_valid_minimal_scheme_loads(self, bare_engine):
        from pathlib import Path
        import tempfile, json, os

        good_scheme = {
            "scheme_name": "Test",
            "version": "1.0",
            "classifications": [],
            "requires_fields": [],
        }
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False
        ) as f:
            json.dump(good_scheme, f)
            fname = f.name

        try:
            result = bare_engine.load_scheme(Path(fname))
            assert result["scheme_name"] == "Test"
        finally:
            os.unlink(fname)
