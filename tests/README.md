# Scientific Toolkit — Test Suite

A pytest test suite covering the `ClassificationEngine` core.

## Structure

```
tests/
  conftest.py                        # shared fixtures, mock data
  test_evaluate_rule.py              # unit: all operators + edge cases
  test_derived_fields.py             # unit: Zr/Nb, CIA, TAS alkali, mantle ratios…
  test_classification_schemes.py     # unit: 10 classification schemes (literature values)
  test_engine_core.py                # unit: loading, normalization, batch, OR/AND logic
  test_integration_real_files.py     # integration: real JSON files (auto-skipped if absent)
```

## Running

```bash
# Install pytest (only dependency beyond the project's own requirements)
pip install pytest

# Run all tests from the project root
pytest tests/ -v

# Run only unit tests (no JSON files needed)
pytest tests/ -v -k "not real_engine"

# Run a single file
pytest tests/test_evaluate_rule.py -v

# Run a single class
pytest tests/test_classification_schemes.py::TestBoneCollagenQC -v

# Show slowest tests
pytest tests/ -v --durations=10
```

## Test counts (approximate)

| File                              | Tests |
|-----------------------------------|-------|
| test_evaluate_rule.py             | ~40   |
| test_derived_fields.py            | ~30   |
| test_classification_schemes.py    | ~50   |
| test_engine_core.py               | ~30   |
| test_integration_real_files.py    | ~20   |
| **Total**                         | **~170** |

## Integration tests

`test_integration_real_files.py` loads the actual JSON files from
`engines/classification/` and `engines/more_classifications/`. If those
directories are not present, all tests in that file are **automatically
skipped** — they will never fail, just be skipped.

## Literature references

Classification thresholds used in tests are sourced from:

- **Bone Collagen QC:** DeNiro (1985), van Klinken (1999)
- **Stable Isotope Diet:** Schoeninger et al. (1983), Müldner & Richards (2005)
- **TAS Series:** Irvine & Baragar (1971)
- **Pearce Mantle Array:** Pearce (2008), Hofmann (1988)
- **Wentworth Grain Size:** Wentworth (1922)
- **USDA Soil Texture:** USDA Soil Taxonomy (1999)
- **Geoaccumulation Index:** Müller (1969, 1981)
- **Water Hardness:** USGS Water Science School
- **Ceramic Firing Temp:** Tite (2008), Quinn (2013)
- **CIA:** Nesbitt & Young (1982)
