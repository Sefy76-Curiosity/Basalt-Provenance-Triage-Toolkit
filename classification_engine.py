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
            # Default to config/classification_schemes/
            base_dir = Path(__file__).parent
            schemes_dir = base_dir / "config" / "classification_schemes"

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
        print(">>> classify_sample CALLED with scheme_id =", scheme_id)

        if scheme_id not in self.schemes:
            print(">>> SCHEME NOT FOUND. Available:", list(self.schemes.keys()))
            return ("SCHEME_NOT_FOUND", 0.0, "#808080")

        sample = self._normalize_sample(sample)
        if sample is None:
            print(">>> INVALID SAMPLE after normalization")
            return ("INVALID_SAMPLE", 0.0, "#808080")

        # Clean Zr_error
        if "Zr_error" in sample:
            try:
                raw = str(sample["Zr_error"])
                raw = raw.replace("±", "").replace("%", "").replace("ppm", "").strip()
                sample["Zr_error"] = float(raw)
            except:
                sample["Zr_error"] = None

        # Compute Zr_RSD
        if "Zr_ppm" in sample and "Zr_error" in sample:
            try:
                zr = float(sample["Zr_ppm"])
                err = float(sample["Zr_error"])
                if zr != 0:
                    sample["Zr_RSD"] = err / zr
            except:
                sample["Zr_RSD"] = None

        # Compute Zr_Nb_Ratio
        if "Zr_ppm" in sample and "Nb_ppm" in sample:
            try:
                zr = float(sample["Zr_ppm"])
                nb = float(sample["Nb_ppm"])
                if nb != 0:
                    sample["Zr_Nb_Ratio"] = zr / nb
            except:
                sample["Zr_Nb_Ratio"] = None

        # Compute Cr_Ni_Ratio
        if "Cr_ppm" in sample and "Ni_ppm" in sample:
            try:
                cr = float(sample["Cr_ppm"])
                ni = float(sample["Ni_ppm"])
                if ni != 0:
                    sample["Cr_Ni_Ratio"] = cr / ni
            except:
                sample["Cr_Ni_Ratio"] = None

        # 🔥 THE DEBUG PRINTS YOU NEED — GUARANTEED TO RUN
        print("ENGINE Zr_ppm  =", sample.get("Zr_ppm"))
        print("ENGINE Zr_error=", sample.get("Zr_error"))
        print("ENGINE Zr_RSD  =", sample.get("Zr_RSD"))
        print("ENGINE Zr/Nb   =", sample.get("Zr_Nb_Ratio"))
        print("ENGINE Cr/Ni   =", sample.get("Cr_Ni_Ratio"))

        scheme = self.schemes[scheme_id]

        # Apply classification rules (supports both "classifications" and "rules")
        class_list = scheme.get("classifications") or scheme.get("rules") or []

        for classification in class_list:
            if self.matches_classification(sample, classification):
                name = classification.get("name") or classification.get("label") or "UNNAMED"
                confidence = classification.get("confidence_score") or classification.get("confidence") or 0.0
                color = classification.get("color", "#A9A9A9")
                return (name, confidence, color)

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
        value = rule.get('value')

        # Handle ratio fields (e.g., "Zr_Nb_Ratio" or "Cr_Ni_Ratio")
        if '_Ratio' in field:
            ratio_name = field.replace('_Ratio', '')
            elements = ratio_name.split('_')

            if len(elements) == 2:
                numerator_field = f"{elements[0]}_ppm"
                denominator_field = f"{elements[1]}_ppm"

                numerator = sample.get(numerator_field)
                denominator = sample.get(denominator_field)

                try:
                    if numerator is None or denominator is None or float(denominator) == 0:
                        return False
                    sample_value = float(numerator) / float(denominator)
                except (ValueError, TypeError):
                    return False
            else:
                return False

        # Handle explicit ratio fields (e.g., "Zr_ppm/Nb_ppm")
        elif '/' in field:
            try:
                numerator_field, denominator_field = field.split('/')
            except ValueError:
                return False

            numerator = sample.get(numerator_field)
            denominator = sample.get(denominator_field)

            try:
                if numerator is None or denominator is None or float(denominator) == 0:
                    return False
                sample_value = float(numerator) / float(denominator)
            except (ValueError, TypeError):
                return False
        else:
            # Direct field value
            sample_value = sample.get(field)
            if sample_value is None:
                return False
            try:
                sample_value = float(sample_value)
            except (ValueError, TypeError):
                return False

        # Apply operator
        try:
            if operator == '>':
                return sample_value > float(value)
            elif operator == '<':
                return sample_value < float(value)
            elif operator == '>=':
                return sample_value >= float(value)
            elif operator == '<=':
                return sample_value <= float(value)
            elif operator == '==':
                return abs(sample_value - float(value)) < 0.0001
            elif operator == 'between':
                # Handle both formats: [min, max] or {"min": X, "max": Y}
                if isinstance(value, list):
                    min_val, max_val = value[0], value[1]
                else:
                    min_val = rule.get('min', value)
                    max_val = rule.get('max', value)
                return float(min_val) <= sample_value <= float(max_val)
            elif operator == 'not_between':
                if isinstance(value, list):
                    min_val, max_val = value[0], value[1]
                else:
                    min_val = rule.get('min', value)
                    max_val = rule.get('max', value)
                return not (float(min_val) <= sample_value <= float(max_val))
            else:
                return False
        except (ValueError, TypeError, KeyError):
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

        # Output column name
        if output_column is None:
            output_column = scheme.get('output_column_name', 'Classification')

        classified_count = 0

        for i, sample in enumerate(samples):
            normalized = self._normalize_sample(sample)
            if normalized is None:
                if isinstance(sample, dict):
                    sample[output_column] = "INVALID_SAMPLE"
                    sample[f'{output_column}_Confidence'] = 0.0
                    sample[f'{output_column}_Color'] = "#808080"
                continue

            # Run ONLY the selected scheme
            classification, confidence, color = self.classify_sample(normalized, scheme_id)

            sample[output_column] = classification
            sample[f'{output_column}_Confidence'] = confidence
            sample[f'{output_column}_Color'] = color

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
