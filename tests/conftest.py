"""
conftest.py — shared pytest fixtures for Scientific Toolkit test suite.

Drop this file (and the accompanying test_*.py files) into a `tests/` folder
at the project root, then run:

    pip install pytest
    pytest tests/ -v

Unit fixtures create a fully-functional ClassificationEngine in isolation,
without touching the filesystem.  Integration fixtures load real JSON files and
skip gracefully if the project structure is absent.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path setup – allows `import engines` regardless of cwd
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_engine(schemes: dict, derived_fields: dict = None):
    """
    Return a ClassificationEngine with injected schemes/derived fields.
    No filesystem I/O occurs.
    """
    from engines.classification_engine import ClassificationEngine

    with patch.object(ClassificationEngine, "load_all_schemes", return_value=None), \
         patch.object(ClassificationEngine, "_load_derived_fields",
                      return_value=derived_fields or {"fields": []}):
        eng = ClassificationEngine(schemes_dir="/nonexistent")

    eng.schemes = schemes
    eng.derived_fields = derived_fields or {"fields": []}
    return eng


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_DERIVED_FIELDS = {
    "fields": [
        {
            "name": "ratio_xy",
            "requires": ["x", "y"],
            "formula": "x / y",
        },
        {
            "name": "CIA_Value",
            "requires": ["Al2O3_wt", "CaO_wt", "Na2O_wt", "K2O_wt"],
            "formula": "(Al2O3_wt / (Al2O3_wt + CaO_wt + Na2O_wt + K2O_wt)) * 100",
        },
        {
            "name": "Zr_Nb_Ratio",
            "requires": ["Zr_ppm", "Nb_ppm"],
            "formula": "Zr_ppm / Nb_ppm",
        },
        {
            "name": "Nb_Yb_Ratio",
            "requires": ["Nb_ppm", "Yb_ppm"],
            "formula": "Nb_ppm / Yb_ppm",
        },
        {
            "name": "Th_Yb_Ratio",
            "requires": ["Th_ppm", "Yb_ppm"],
            "formula": "Th_ppm / Yb_ppm",
        },
        {
            "name": "Total_Alkali",
            "requires": ["Na2O_wt", "K2O_wt"],
            "formula": "Na2O_wt + K2O_wt",
        },
        {
            "name": "Zr_RSD",
            "requires": ["Zr_ppm", "Zr_error"],
            "formula": "Zr_error / Zr_ppm",
        },
        {
            "name": "V_Ratio",
            "requires": ["CaO_wt", "MgO_wt", "SiO2_wt", "Al2O3_wt"],
            "formula": "(CaO_wt + MgO_wt) / (SiO2_wt + Al2O3_wt)",
        },
    ]
}

MOCK_SCHEMES = {
    "mock_threshold": {
        "scheme_name": "Mock Threshold",
        "version": "1.0",
        "requires_fields": ["value"],
        "classifications": [
            {
                "name": "HIGH",
                "color": "#FF0000",
                "confidence_score": 0.9,
                "rules": [{"field": "value", "operator": ">", "value": 100}],
                "logic": "AND",
            },
            {
                "name": "LOW",
                "color": "#00FF00",
                "confidence_score": 0.9,
                "rules": [{"field": "value", "operator": "<=", "value": 100}],
                "logic": "AND",
            },
        ],
    },
    "mock_between": {
        "scheme_name": "Mock Between",
        "version": "1.0",
        "requires_fields": ["score"],
        "classifications": [
            {
                "name": "PASS",
                "color": "#00AA00",
                "confidence_score": 1.0,
                "rules": [{"field": "score", "operator": "between", "min": 2.9, "max": 3.6}],
                "logic": "AND",
            },
            {
                "name": "FAIL",
                "color": "#AA0000",
                "confidence_score": 1.0,
                "rules": [{"field": "score", "operator": "not_between", "min": 2.9, "max": 3.6}],
                "logic": "AND",
            },
        ],
    },
    "mock_multi_and": {
        "scheme_name": "Mock Multi AND",
        "version": "1.0",
        "requires_fields": ["x", "y"],
        "classifications": [
            {
                "name": "MATCH",
                "color": "#0000FF",
                "confidence_score": 1.0,
                "rules": [
                    {"field": "x", "operator": ">", "value": 5},
                    {"field": "y", "operator": "<", "value": 20},
                ],
                "logic": "AND",
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    """Isolated engine – mock schemes + mock derived fields."""
    return make_engine(MOCK_SCHEMES, MOCK_DERIVED_FIELDS)


@pytest.fixture
def bare_engine():
    """Engine with no schemes and no derived fields."""
    return make_engine({})


@pytest.fixture
def real_engine():
    """
    Engine loaded from real project JSON files.
    Skipped if the classification directories are not present.
    """
    engines_dir = PROJECT_ROOT / "engines" / "classification"
    more_dir = PROJECT_ROOT / "engines" / "more_classifications"

    if not engines_dir.exists() and not more_dir.exists():
        pytest.skip("Real JSON files not found – integration tests skipped.")

    from engines.classification_engine import ClassificationEngine
    return ClassificationEngine()
