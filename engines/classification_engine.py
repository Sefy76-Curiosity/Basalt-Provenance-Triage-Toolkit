"""
Classification Engine for Basalt Provenance Triage Toolkit v10.2
Dynamically loads classification schemes from JSON files
Derived fields loaded from engines/derived_fields.json
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

class ClassificationEngine:
    """
    Dynamic classification engine that loads schemes from JSON files
    """

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
                'version': scheme.get('version', '1.0')
            })
        return schemes_list

    def _normalize_sample(self, sample: Any) -> Optional[Dict[str, Any]]:
        """
        Internal helper: ensure sample is a dict.
        Accepts plain dict or pandas Series; rejects everything else.
        """
        # Lazy import to avoid hard dependency
        try:
            import pandas as pd  # type: ignore
        except ImportError:
            pd = None

        if pd is not None and isinstance(sample, pd.Series):
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
                    # Note: Using eval is safe here because we control the formulas
                    result = eval(formula, {"__builtins__": {}}, eval_context)

                    # Store the computed value
                    sample[field_name] = result
                    print(f"    Computed {field_name}: {result:.4f}")

                except Exception as e:
                    print(f"    Warning: Could not compute {field_name}: {e}")
                    sample[field_name] = None
            else:
                # Check if this field is critical for any scheme that might run
                # We'll just skip silently for now
                pass

        return sample

    def _clean_error_fields(self, sample: Dict) -> Dict:
        """Clean up error fields that might have symbols"""
        error_fields = ["Zr_error"]

        for field in error_fields:
            if field in sample and sample[field] is not None:
                try:
                    raw = str(sample[field])
                    raw = raw.replace("±", "").replace("%", "").replace("ppm", "").strip()
                    sample[field] = float(raw)
                    print(f"    Cleaned {field}: {sample[field]}")
                except:
                    sample[field] = None

        return sample

    def classify_sample(self, sample: Dict, scheme_id: str) -> Tuple[str, float, str]:
        print("\n" + "="*60)
        print(f">>> CLASSIFY_SAMPLE: {scheme_id}")
        print(f">>> Sample ID: {sample.get('Sample_ID', 'Unknown')}")
        print("="*60)

        if scheme_id not in self.schemes:
            print(f">>> ERROR: Scheme '{scheme_id}' not found")
            return ("SCHEME_NOT_FOUND", 0.0, "#808080")

        sample = self._normalize_sample(sample)
        if sample is None:
            print(">>> ERROR: Invalid sample after normalization")
            return ("INVALID_SAMPLE", 0.0, "#808080")

        # Print ALL sample values for debugging
        print("\n>>> SAMPLE VALUES:")
        for key in sorted(sample.keys()):
            if key not in ['Sample_ID', 'Notes'] and sample[key] is not None:
                print(f"    {key}: {sample[key]}")

        # Clean error fields
        sample = self._clean_error_fields(sample)

        # Compute ALL derived fields from JSON
        print("\n>>> COMPUTING DERIVED FIELDS:")
        sample = self._compute_derived_fields(sample)

        scheme = self.schemes[scheme_id]
        print(f"\n>>> SCHEME: {scheme.get('scheme_name')}")

        # Get classifications
        classifications = scheme.get("classifications") or scheme.get("rules") or []
        print(f">>> Found {len(classifications)} classifications in scheme")

        # Try each classification
        for i, classification in enumerate(classifications):
            name = classification.get("name", "UNNAMED")
            print(f"\n>>> Testing classification #{i+1}: {name}")

            rules = classification.get('rules', [])
            print(f"    Rules: {len(rules)}")

            # Check each rule
            all_rules_passed = True
            for j, rule in enumerate(rules):
                field = rule.get('field', '')
                operator = rule.get('operator', '')

                # Print what we're checking
                if field in sample:
                    val = sample[field]
                    print(f"      Rule {j+1}: {field} = {val}")
                else:
                    print(f"      Rule {j+1}: {field} = [MISSING]")
                    all_rules_passed = False
                    continue

                # Evaluate the rule
                if self.evaluate_rule(sample, rule):
                    print(f"        ✓ PASSED")
                else:
                    print(f"        ✗ FAILED")
                    all_rules_passed = False

            if all_rules_passed:
                print(f"    ✓ ALL RULES PASSED! Classification: {name}")
                confidence = classification.get("confidence_score", 0.0)
                color = classification.get("color", "#A9A9A9")
                return (name, confidence, color)
            else:
                print(f"    ✗ NOT ALL RULES PASSED")

        print("\n>>> No matching classification found")
        return ("UNCLASSIFIED", 0.0, "#A9A9A9")

    def matches_classification(self, sample: Dict, classification: Dict) -> bool:
        """
        Check if sample matches classification rules

        Rules can be:
        - Simple: {"field": "Zr_ppm", "operator": ">", "value": 100}
        - Ratio: {"field": "Zr_ppm/Nb_ppm", "operator": "between", "value": [6, 10]}
        - Compound: {"logic": "AND", "rules": [...]}
        """
        if not isinstance(classification, dict):
            return False

        rules = classification.get('rules', [])
        logic = classification.get('logic', 'AND')

        if not rules:
            return False

        # Evaluate all rules
        results: List[bool] = []
        for rule in rules:
            if not isinstance(rule, dict):
                results.append(False)
                continue
            result = self.evaluate_rule(sample, rule)
            results.append(result)

        # Apply logic
        if logic == 'AND':
            return all(results)
        elif logic == 'OR':
            return any(results)
        else:
            return False

    def evaluate_rule(self, sample: Dict, rule: Dict) -> bool:
        """Evaluate a single classification rule"""
        if not isinstance(rule, dict):
            return False

        field = rule.get('field', '')
        operator = rule.get('operator', '')

        # Get the value from sample
        if field not in sample:
            print(f"      Field '{field}' not in sample")
            return False

        sample_value = sample[field]
        if sample_value is None:
            print(f"      Field '{field}' is None")
            return False

        try:
            sample_value = float(sample_value)
        except (ValueError, TypeError):
            print(f"      Cannot convert '{field}' value '{sample_value}' to float")
            return False

        # Apply operator
        try:
            if operator == '>':
                value = float(rule.get('value', 0))
                result = sample_value > value
                print(f"      {sample_value} > {value} = {result}")
                return result

            elif operator == '<':
                value = float(rule.get('value', 0))
                result = sample_value < value
                print(f"      {sample_value} < {value} = {result}")
                return result

            elif operator == '>=':
                value = float(rule.get('value', 0))
                result = sample_value >= value
                print(f"      {sample_value} >= {value} = {result}")
                return result

            elif operator == '<=':
                value = float(rule.get('value', 0))
                result = sample_value <= value
                print(f"      {sample_value} <= {value} = {result}")
                return result

            elif operator == '==':
                value = float(rule.get('value', 0))
                result = abs(sample_value - value) < 0.0001
                print(f"      {sample_value} == {value} = {result}")
                return result

            elif operator == 'between':
                # Handle both formats: [min, max] or {"min": X, "max": Y}
                if 'min' in rule and 'max' in rule:
                    min_val = float(rule['min'])
                    max_val = float(rule['max'])
                elif isinstance(rule.get('value'), list):
                    min_val, max_val = map(float, rule['value'])
                else:
                    print(f"      Invalid between format")
                    return False

                result = min_val <= sample_value <= max_val
                print(f"      {min_val} <= {sample_value} <= {max_val} = {result}")
                return result

            elif operator == 'not_between':
                if 'min' in rule and 'max' in rule:
                    min_val = float(rule['min'])
                    max_val = float(rule['max'])
                elif isinstance(rule.get('value'), list):
                    min_val, max_val = map(float, rule['value'])
                else:
                    return False

                result = not (min_val <= sample_value <= max_val)
                print(f"      NOT({min_val} <= {sample_value} <= {max_val}) = {result}")
                return result

            else:
                print(f"      Unknown operator: {operator}")
                return False

        except (ValueError, TypeError, KeyError) as e:
            print(f"      Error evaluating rule: {e}")
            return False

    def classify_all_samples(self, samples: Any, scheme_id: str,
                            output_column: str = None) -> List[Dict]:
        """
        Classify all samples using ONLY the selected scheme.
        Removes all default/secondary scheme execution.
        """

        if scheme_id not in self.schemes:
            print(f"⚠️ Classification scheme not found: {scheme_id}")
            return samples

        scheme = self.schemes[scheme_id]

        # Convert DataFrame → list of dicts
        try:
            import pandas as pd  # type: ignore
        except ImportError:
            pd = None

        if pd is not None and isinstance(samples, pd.DataFrame):
            samples = samples.to_dict(orient='records')

        if not isinstance(samples, list):
            print("⚠️ 'samples' must be a list of dicts or a pandas DataFrame")
            return samples

        # Get column names from scheme (respecting JSON configuration)
        if output_column is None:
            output_column = scheme.get('output_column_name', 'Auto_Classification')

        confidence_column = scheme.get('confidence_column_name', 'Auto_Confidence')
        add_confidence = scheme.get('add_confidence_column', True)

        flag_column = scheme.get('flag_column_name', 'Flag_For_Review')
        flag_uncertain = scheme.get('flag_uncertain', False)
        uncertain_threshold = scheme.get('uncertain_threshold', 0.7)

        classified_count = 0

        for i, sample in enumerate(samples):
            normalized = self._normalize_sample(sample)
            if normalized is None:
                if isinstance(sample, dict):
                    sample[output_column] = "INVALID_SAMPLE"
                    if add_confidence:
                        sample[confidence_column] = 0.0
                    if flag_uncertain:
                        sample[flag_column] = True
                continue

            # Run ONLY the selected scheme
            classification, confidence, color = self.classify_sample(normalized, scheme_id)

            # Add classification result
            sample[output_column] = classification

            # Add confidence using correct column name from scheme
            if add_confidence:
                sample[confidence_column] = confidence

            # Add flag for review based on confidence threshold
            if flag_uncertain:
                # Flag samples with confidence below threshold
                sample[flag_column] = (confidence < uncertain_threshold)

            # Store color (for internal use)
            sample['Display_Color'] = color

            if classification not in ['INSUFFICIENT_DATA', 'UNCLASSIFIED', 'INVALID_SAMPLE']:
                classified_count += 1

        print(f"✅ Classified {classified_count}/{len(samples)} samples using '{scheme['scheme_name']}'")

        return samples

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
        classification, confidence, color = engine.classify_sample(test_sample, 'regional_triage')
        print(f"\n🎯 Classification: {classification}")
        print(f"   Confidence: {confidence:.0%}")
        print(f"   Color: {color}")

    print("\n" + "=" * 60)
