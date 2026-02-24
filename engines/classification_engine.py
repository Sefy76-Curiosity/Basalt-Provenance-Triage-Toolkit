"""
Classification Engine for Basalt Provenance Triage Toolkit v10.2
Dynamically loads classification schemes from JSON files
Derived fields loaded from engines/derived_fields.json

*** READ-ONLY VERSION ***
Does not modify input samples.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Lazy pandas import — loaded once, avoids repeated import overhead
try:
    import pandas as _pd
except ImportError:
    _pd = None

class ClassificationEngine:
    """
    Dynamic classification engine that loads schemes from JSON files
    """

    DEBUG = False  # Set to True to enable verbose classification logging

    def _log(self, msg):
        """Internal debug logger — only prints when DEBUG is True."""
        if self.DEBUG:
            print(msg)

    def __init__(self, schemes_dir: str = None):
        """Initialize classification engine"""
        if schemes_dir is None:
            # Default to engines/classification/
            base_dir = Path(__file__).parent
            schemes_dir = base_dir / "classification"  # Look in classification subfolder
        self.schemes_dir = Path(schemes_dir)

        self.schemes: Dict[str, Dict[str, Any]] = {}

        # Load derived fields from parent directory
        self.derived_fields_path = Path(__file__).parent / "derived_fields.json"
        self.derived_fields = self._load_derived_fields()

        self.load_all_schemes()

    def _load_derived_fields(self) -> Dict[str, Any]:
        """Load derived field calculations from JSON"""
        if not self.derived_fields_path.exists():
            print(f"⚠️ Derived fields file not found: {self.derived_fields_path}")
            return {"fields": []}

        try:
            with open(self.derived_fields_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded {len(data.get('fields', []))} derived field calculators")
            return data
        except Exception as e:
            print(f"⚠️ Error loading derived fields: {e}")
            return {"fields": []}

    def load_all_schemes(self):
        """Auto-discover and load all JSON classification schemes"""
        self.schemes = {}

        if not self.schemes_dir.exists():
            print(f"⚠️ Classification schemes directory not found: {self.schemes_dir}")
            return

        # Find all JSON files (except _TEMPLATE.json)
        json_files = [f for f in self.schemes_dir.glob("*.json")
                      if not f.name.startswith('_')]

        for json_file in json_files:
            try:
                scheme = self.load_scheme(json_file)
                if scheme:
                    scheme_id = json_file.stem  # filename without .json
                    self.schemes[scheme_id] = scheme
                    print(f"✅ Loaded classification scheme: {scheme['scheme_name']}")
            except Exception as e:
                print(f"⚠️ Error loading {json_file.name}: {e}")

        print(f"\n📊 Total schemes loaded: {len(self.schemes)}")

    def load_scheme(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Load and validate a single classification scheme"""
        with open(filepath, 'r', encoding='utf-8') as f:
            scheme = json.load(f)

        # Validate required fields
        required = ['scheme_name', 'version', 'classifications', 'requires_fields']
        for field in required:
            if field not in scheme:
                raise ValueError(f"Missing required field: {field}")

        return scheme

    def get_available_schemes(self) -> List[Dict[str, str]]:
        """Get list of available classification schemes"""
        schemes_list: List[Dict[str, str]] = []
        for scheme_id, scheme in self.schemes.items():
            schemes_list.append({
                'id': scheme_id,
                'name': scheme['scheme_name'],
                'description': scheme.get('description', ''),
                'icon': scheme.get('icon', '📊'),
                'version': scheme.get('version', '1.0'),
                'field': scheme.get('field', 'General'),
                'category': scheme.get('category', ''),
            })
        return schemes_list

    def _normalize_sample(self, sample: Any) -> Optional[Dict[str, Any]]:
        """
        Internal helper: ensure sample is a dict.
        Accepts plain dict or pandas Series; rejects everything else.
        """
        if _pd is not None and isinstance(sample, _pd.Series):
            return sample.to_dict()

        if isinstance(sample, dict):
            return sample

        # Anything else is invalid for this engine
        return None

    def _compute_derived_fields(self, sample: Dict) -> Dict:
        """
        Compute all derived fields needed for classification schemes
        Loads formulas from derived_fields.json
        """
        fields = self.derived_fields.get('fields', [])
        derived = {}

        for field_def in fields:
            field_name = field_def.get('name')
            requires = field_def.get('requires', [])
            formula = field_def.get('formula', '')

            # Skip if formula is missing
            if not formula or not requires:
                continue

            # Check if we have all required fields
            if all(req in sample for req in requires):
                try:
                    # Create a safe evaluation context with all required values
                    eval_context = {}
                    for req in requires:
                        eval_context[req] = float(sample[req])

                    # Safely evaluate the formula
                    result = eval(formula, {"__builtins__": {}}, eval_context)
                    derived[field_name] = result
                    if self.DEBUG:
                        print(f"    Computed {field_name}: {result:.4f}")

                except Exception as e:
                    if self.DEBUG:
                        print(f"    Warning: Could not compute {field_name}: {e}")
                    derived[field_name] = None
            else:
                # Not all required fields present
                derived[field_name] = None

        return derived

    def _clean_error_fields(self, sample: Dict) -> Dict:
        """Clean up error fields that might have symbols"""
        cleaned = {}
        error_fields = ["Zr_error"]

        for field in error_fields:
            if field in sample and sample[field] is not None:
                try:
                    raw = str(sample[field])
                    raw = raw.replace("±", "").replace("%", "").replace("ppm", "").strip()
                    cleaned[field] = float(raw)
                    if self.DEBUG:
                        print(f"    Cleaned {field}: {cleaned[field]}")
                except:
                    cleaned[field] = None

        return cleaned

    def classify_sample(self, sample: Dict, scheme_id: str) -> Tuple[str, float, str, Dict]:
        """
        Classify a single sample.
        Returns (classification_name, confidence, color, derived_fields)
        Does NOT modify the input sample.
        """
        self._log(f"\n{'='*60}\n>>> CLASSIFY_SAMPLE: {scheme_id} | Sample: {sample.get('Sample_ID', 'Unknown')}\n{'='*60}")

        if scheme_id not in self.schemes:
            self._log(f">>> ERROR: Scheme '{scheme_id}' not found")
            return ("SCHEME_NOT_FOUND", 0.0, "#808080", {})

        sample_norm = self._normalize_sample(sample)
        if sample_norm is None:
            self._log(">>> ERROR: Invalid sample after normalization")
            return ("INVALID_SAMPLE", 0.0, "#808080", {})

        cleaned_errors = self._clean_error_fields(sample_norm)
        derived = self._compute_derived_fields(sample_norm)

        scheme = self.schemes[scheme_id]
        self._log(f"\n>>> SCHEME: {scheme.get('scheme_name')}")

        classifications = scheme.get("classifications") or scheme.get("rules") or []
        self._log(f">>> Found {len(classifications)} classifications in scheme")

        for i, classification in enumerate(classifications):
            name = classification.get("name", "UNNAMED")
            rules = classification.get('rules', [])
            logic = classification.get('logic', 'AND')

            self._log(f"\n>>> Testing classification #{i+1}: {name} | Logic: {logic} | Rules: {len(rules)}")

            # DEFAULT classification (fallback)
            if logic == 'DEFAULT' and not rules:
                self._log(f"    ✓ DEFAULT FALLBACK: {name}")
                confidence = classification.get("confidence_score", 0.0)
                color = classification.get("color", "#A9A9A9")
                return (name, confidence, color, derived)

            def _get_field_value(rule):
                """Return (value, found) for the field referenced by rule."""
                field = rule.get('field', '')
                if field in sample_norm:
                    return sample_norm[field], True
                if field in cleaned_errors:
                    return cleaned_errors[field], True
                if field in derived:
                    return derived[field], True
                return None, False

            if logic == 'OR':
                # Pass if ANY rule matches
                any_passed = False
                for j, rule in enumerate(rules):
                    val, found = _get_field_value(rule)
                    if not found:
                        self._log(f"      Rule {j+1}: {rule.get('field','')} = [MISSING]")
                        continue
                    self._log(f"      Rule {j+1}: {rule.get('field','')} = {val}")
                    if self.evaluate_rule_with_value(val, rule):
                        self._log(f"        ✓ PASSED (OR — stopping early)")
                        any_passed = True
                        break
                    else:
                        self._log(f"        ✗ FAILED")
                if any_passed:
                    self._log(f"    ✓ OR MATCHED! Classification: {name}")
                    confidence = classification.get("confidence_score", 0.0)
                    color = classification.get("color", "#A9A9A9")
                    return (name, confidence, color, derived)

            else:  # AND (default)
                # Pass only if ALL rules match
                all_rules_passed = True
                for j, rule in enumerate(rules):
                    val, found = _get_field_value(rule)
                    if not found:
                        self._log(f"      Rule {j+1}: {rule.get('field','')} = [MISSING]")
                        all_rules_passed = False
                        continue
                    self._log(f"      Rule {j+1}: {rule.get('field','')} = {val}")
                    if self.evaluate_rule_with_value(val, rule):
                        self._log(f"        ✓ PASSED")
                    else:
                        self._log(f"        ✗ FAILED")
                        all_rules_passed = False
                if all_rules_passed:
                    self._log(f"    ✓ ALL RULES PASSED! Classification: {name}")
                    confidence = classification.get("confidence_score", 0.0)
                    color = classification.get("color", "#A9A9A9")
                    return (name, confidence, color, derived)

        self._log("\n>>> No matching classification found")
        return ("UNCLASSIFIED", 0.0, "#A9A9A9", derived)

    def evaluate_rule_with_value(self, sample_value: float, rule: Dict) -> bool:
        """Evaluate a rule using a pre‑extracted value."""
        if sample_value is None:
            return False

        operator = rule.get('operator', '')

        try:
            if operator == '>':
                value = float(rule.get('value', 0))
                return sample_value > value
            elif operator == '<':
                value = float(rule.get('value', 0))
                return sample_value < value
            elif operator == '>=':
                value = float(rule.get('value', 0))
                return sample_value >= value
            elif operator == '<=':
                value = float(rule.get('value', 0))
                return sample_value <= value
            elif operator == '==':
                value = float(rule.get('value', 0))
                return abs(sample_value - value) < 0.0001
            elif operator == 'between':
                if 'min' in rule and 'max' in rule:
                    min_val = float(rule['min'])
                    max_val = float(rule['max'])
                elif isinstance(rule.get('value'), list):
                    min_val, max_val = map(float, rule['value'])
                else:
                    return False
                return min_val <= sample_value <= max_val
            elif operator == 'not_between':
                if 'min' in rule and 'max' in rule:
                    min_val = float(rule['min'])
                    max_val = float(rule['max'])
                elif isinstance(rule.get('value'), list):
                    min_val, max_val = map(float, rule['value'])
                else:
                    return False
                return not (min_val <= sample_value <= max_val)
            else:
                print(f"      Unknown operator: {operator}")
                return False
        except (ValueError, TypeError) as e:
            print(f"      Error evaluating rule: {e}")
            return False

    def classify_all_samples(self, samples: Any, scheme_id: str) -> List[Dict]:
        """
        Classify all samples using ONLY the selected scheme.
        Returns a list of result dictionaries (one per sample) with keys:
            'classification', 'confidence', 'color', 'derived_fields', 'flag_for_review'
        Does NOT modify input samples.
        """
        if scheme_id not in self.schemes:
            print(f"⚠️ Classification scheme not found: {scheme_id}")
            return [{'classification': 'SCHEME_NOT_FOUND', 'confidence': 0.0,
                     'color': '#808080', 'derived_fields': {}, 'flag_for_review': False} for _ in samples]

        scheme = self.schemes[scheme_id]

        # Convert DataFrame → list of dicts
        if _pd is not None and isinstance(samples, _pd.DataFrame):
            samples = samples.to_dict(orient='records')

        if not isinstance(samples, list):
            print("⚠️ 'samples' must be a list of dicts or a pandas DataFrame")
            return []

        results = []
        classified_count = 0

        for i, sample in enumerate(samples):
            classification, confidence, color, derived = self.classify_sample(sample, scheme_id)

            # Build result entry
            result = {
                'classification': classification,
                'confidence': confidence,
                'color': color,
                'derived_fields': derived
            }

            # Add flag for review based on confidence threshold
            flag_uncertain = scheme.get('flag_uncertain', False)
            uncertain_threshold = scheme.get('uncertain_threshold', 0.7)
            if flag_uncertain:
                result['flag_for_review'] = (confidence < uncertain_threshold)
            else:
                result['flag_for_review'] = False

            results.append(result)

            if classification not in ['INSUFFICIENT_DATA', 'UNCLASSIFIED', 'INVALID_SAMPLE']:
                classified_count += 1

        print(f"✅ Classified {classified_count}/{len(samples)} samples using '{scheme['scheme_name']}'")

        return results

    def get_scheme_info(self, scheme_id: str) -> Dict[str, Any]:
        """Get detailed information about a classification scheme"""
        if scheme_id not in self.schemes:
            return {}

        scheme = self.schemes[scheme_id]

        # Count classifications
        num_classifications = len(scheme.get('classifications', []))

        # Get field requirements
        required_fields = scheme.get('requires_fields', [])

        return {
            'id': scheme_id,
            'name': scheme['scheme_name'],
            'version': scheme.get('version', '1.0'),
            'author': scheme.get('author', 'Unknown'),
            'description': scheme.get('description', ''),
            'icon': scheme.get('icon', '📊'),
            'num_classifications': num_classifications,
            'required_fields': required_fields,
            'output_column': scheme.get('output_column_name', 'Classification'),
            'classifications': [c['name'] for c in scheme.get('classifications', []) if isinstance(c, dict)]
        }


# TEST CODE (if run directly)
if __name__ == '__main__':
    print("=" * 60)
    print("CLASSIFICATION ENGINE TEST")
    print("=" * 60)

    # Initialize engine
    engine = ClassificationEngine()

    # Show available schemes
    print("\n📋 Available Schemes:")
    for scheme in engine.get_available_schemes():
        print(f"   {scheme['icon']} {scheme['name']} (v{scheme['version']})")
        print(f"      {scheme['description']}")

    # Test sample
    test_sample = {
        'Sample_ID': 'TEST_001',
        'Zr_ppm': 165,
        'Nb_ppm': 18,
        'Ti_ppm': 9500,
        'Ba_ppm': 260,
        'Rb_ppm': 15,
        'Cr_ppm': 1800,
        'Ni_ppm': 1400,
        'Wall_Thickness_mm': 3.5
    }

    # Test classification with regional_triage
    print("\n🧪 Testing with sample:", test_sample['Sample_ID'])
    print(f"   Zr: {test_sample['Zr_ppm']}, Nb: {test_sample['Nb_ppm']}")
    print(f"   Zr/Nb ratio: {test_sample['Zr_ppm'] / test_sample['Nb_ppm']:.2f}")

    if 'regional_triage' in engine.schemes:
        classification, confidence, color, derived = engine.classify_sample(test_sample, 'regional_triage')
        print(f"\n🎯 Classification: {classification}")
        print(f"   Confidence: {confidence:.0%}")
        print(f"   Color: {color}")
        print(f"   Derived: {derived}")

    print("\n" + "=" * 60)
