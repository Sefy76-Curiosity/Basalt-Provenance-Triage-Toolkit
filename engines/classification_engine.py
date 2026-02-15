"""
Classification Engine for Basalt Provenance Triage Toolkit v10.2
Dynamically loads classification schemes from JSON files
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

        self.schemes_dir = Path(schemes_dir)
        self.schemes: Dict[str, Dict[str, Any]] = {}
        self.load_all_schemes()

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

    def classify_sample(self, sample: Dict, scheme_id: str) -> Tuple[str, float, str]:
        print("\n" + "="*60)
        print(">>> CLASSIFY_SAMPLE CALLED")
        print(f">>> scheme_id = {scheme_id}")
        print("="*60)

        if scheme_id not in self.schemes:
            print(f">>> ERROR: Scheme '{scheme_id}' not found")
            print(f">>> Available schemes: {list(self.schemes.keys())}")
            return ("SCHEME_NOT_FOUND", 0.0, "#808080")

        sample = self._normalize_sample(sample)
        if sample is None:
            print(">>> ERROR: Invalid sample after normalization")
            return ("INVALID_SAMPLE", 0.0, "#808080")

        # Print raw sample data
        print("\n>>> RAW SAMPLE DATA:")
        for key in sorted(sample.keys()):
            if key not in ['Sample_ID', 'Notes']:
                print(f"    {key}: {sample[key]}")

        # Clean Zr_error
        if "Zr_error" in sample:
            try:
                raw = str(sample["Zr_error"])
                raw = raw.replace("±", "").replace("%", "").replace("ppm", "").strip()
                sample["Zr_error"] = float(raw)
                print(f">>> Cleaned Zr_error: {sample['Zr_error']}")
            except:
                sample["Zr_error"] = None

        # Compute Zr_RSD
        if "Zr_ppm" in sample and "Zr_error" in sample:
            try:
                zr = float(sample["Zr_ppm"])
                err = float(sample["Zr_error"])
                if zr != 0:
                    sample["Zr_RSD"] = err / zr
                    print(f">>> Computed Zr_RSD: {sample['Zr_RSD']}")
            except:
                sample["Zr_RSD"] = None

        # Compute Zr_Nb_Ratio
        if "Zr_ppm" in sample and "Nb_ppm" in sample:
            try:
                zr = float(sample["Zr_ppm"])
                nb = float(sample["Nb_ppm"])
                if nb != 0:
                    sample["Zr_Nb_Ratio"] = zr / nb
                    print(f">>> Computed Zr/Nb: {sample['Zr_Nb_Ratio']:.2f}")
            except:
                sample["Zr_Nb_Ratio"] = None

        # Compute Cr_Ni_Ratio
        if "Cr_ppm" in sample and "Ni_ppm" in sample:
            try:
                cr = float(sample["Cr_ppm"])
                ni = float(sample["Ni_ppm"])
                if ni != 0:
                    sample["Cr_Ni_Ratio"] = cr / ni
                    print(f">>> Computed Cr/Ni: {sample['Cr_Ni_Ratio']:.2f}")
            except:
                sample["Cr_Ni_Ratio"] = None
        
        # Compute Ti_V_Ratio (for tectonic discrimination)
        if "Ti_ppm" in sample and "V_ppm" in sample:
            try:
                ti = float(sample["Ti_ppm"])
                v = float(sample["V_ppm"])
                if v != 0:
                    sample["Ti_V_Ratio"] = ti / v
                    print(f">>> Computed Ti/V: {sample['Ti_V_Ratio']:.2f}")
            except:
                sample["Ti_V_Ratio"] = None
        
        # Compute Th_Yb_Ratio (for crustal contamination)
        if "Th_ppm" in sample and "Yb_ppm" in sample:
            try:
                th = float(sample["Th_ppm"])
                yb = float(sample["Yb_ppm"])
                if yb != 0:
                    sample["Th_Yb_Ratio"] = th / yb
                    print(f">>> Computed Th/Yb: {sample['Th_Yb_Ratio']:.2f}")
            except:
                sample["Th_Yb_Ratio"] = None
        
        # Compute Nb_Yb_Ratio (for mantle array)
        if "Nb_ppm" in sample and "Yb_ppm" in sample:
            try:
                nb = float(sample["Nb_ppm"])
                yb = float(sample["Yb_ppm"])
                if yb != 0:
                    sample["Nb_Yb_Ratio"] = nb / yb
                    print(f">>> Computed Nb/Yb: {sample['Nb_Yb_Ratio']:.2f}")
            except:
                sample["Nb_Yb_Ratio"] = None
        
        # Compute Fe_Mn_Ratio (for planetary analogs)
        if "Fe_ppm" in sample and "Mn_ppm" in sample:
            try:
                fe = float(sample["Fe_ppm"])
                mn = float(sample["Mn_ppm"])
                if mn != 0:
                    sample["Fe_Mn_Ratio"] = fe / mn
                    print(f">>> Computed Fe/Mn: {sample['Fe_Mn_Ratio']:.2f}")
            except:
                sample["Fe_Mn_Ratio"] = None
        
        # Compute Ba_Rb_Ratio (if needed)
        if "Ba_ppm" in sample and "Rb_ppm" in sample:
            try:
                ba = float(sample["Ba_ppm"])
                rb = float(sample["Rb_ppm"])
                if rb != 0:
                    sample["Ba_Rb_Ratio"] = ba / rb
                    print(f">>> Computed Ba/Rb: {sample['Ba_Rb_Ratio']:.2f}")
            except:
                sample["Ba_Rb_Ratio"] = None

        # CRITICAL FIX: Make a copy with computed values for rule evaluation
        evaluation_sample = sample.copy()

        scheme = self.schemes[scheme_id]
        print(f"\n>>> SCHEME: {scheme.get('scheme_name')}")

        # Get classifications
        class_list = scheme.get("classifications") or scheme.get("rules") or []
        print(f">>> Found {len(class_list)} classifications in scheme")

        # Try each classification
        for i, classification in enumerate(class_list):
            name = classification.get("name", "UNNAMED")
            print(f"\n>>> Testing classification #{i+1}: {name}")

            rules = classification.get('rules', [])
            print(f"    Found {len(rules)} rules")

            # Print what values we're comparing
            for j, rule in enumerate(rules):
                field = rule.get('field', '')
                if field in evaluation_sample:
                    print(f"      Rule {j+1}: {field} = {evaluation_sample[field]} {rule.get('operator')} {rule.get('value', rule.get('min', '?'))}")
                else:
                    print(f"      Rule {j+1}: {field} = [MISSING]")

            # Check if matches
            if self.matches_classification(evaluation_sample, classification):
                print(f"    ✓ MATCH FOUND!")
                name = classification.get("name") or classification.get("label") or "UNNAMED"
                confidence = classification.get("confidence_score") or classification.get("confidence") or 0.0
                color = classification.get("color", "#A9A9A9")
                return (name, confidence, color)
            else:
                print(f"    ✗ No match")

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
        
        # ✓ FIX: Use confidence_column_name from scheme, not constructed name
        confidence_column = scheme.get('confidence_column_name', 'Auto_Confidence')
        add_confidence = scheme.get('add_confidence_column', True)
        
        # ✓ FIX: Handle flag column if scheme specifies it
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

            # ✓ FIX: Add classification result
            sample[output_column] = classification
            
            # ✓ FIX: Add confidence using correct column name from scheme
            if add_confidence:
                sample[confidence_column] = confidence
            
            # ✓ FIX: Add flag for review based on confidence threshold
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
