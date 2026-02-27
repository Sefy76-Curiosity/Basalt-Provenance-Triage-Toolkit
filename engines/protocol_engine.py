"""
Protocol Engine for Scientific Toolkit v2.0
Dynamically loads and runs multi-stage protocols from JSON files.
FIXED: Removed python_stage to prevent RCE
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from importlib import import_module
import hashlib
import hmac
import os

# Ensure engines directory is on path for imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from classification_engine import ClassificationEngine
except ImportError:
    ClassificationEngine = None
    print("⚠️ Classification engine not found - protocol engine will have limited functionality")


class ProtocolEngine:
    # 🔐 Security: Whitelist of allowed modules and functions
    ALLOWED_MODULES = {
        'math': ['sin', 'cos', 'tan', 'sqrt', 'log', 'log10', 'exp', 'radians', 'degrees'],
        'statistics': ['mean', 'median', 'stdev', 'variance'],
        'numpy': ['mean', 'median', 'std', 'var', 'min', 'max', 'sum'],
    }

    # 🔐 Security: Signature file for trusted protocols
    SIGNATURE_FILE = Path(__file__).parent / "protocols" / "signatures.json"

    def __init__(self, protocols_dir: Optional[str] = None, schemes_dir: Optional[str] = None):
        """
        Initialize the protocol engine.
        """

        # Protocols directory
        if protocols_dir is None:
            self.protocols_dir = current_dir / "protocols"
        else:
            self.protocols_dir = Path(protocols_dir)

        # Load trusted signatures
        self.trusted_signatures = self._load_signatures()

        print("🔍 PROTOCOL ENGINE DEBUG:")
        print(f"   Looking in: {self.protocols_dir.absolute()}")
        print(f"   Folder exists: {self.protocols_dir.exists()}")

        self.protocols: Dict[str, Dict[str, Any]] = {}

        # Classification engine (optional)
        if ClassificationEngine is not None:
            if schemes_dir is None:
                schemes_dir_path = current_dir / "classification"
            else:
                schemes_dir_path = Path(schemes_dir)
            self.classification_engine = ClassificationEngine(str(schemes_dir_path))
        else:
            self.classification_engine = None
            print("⚠️ Protocol engine running without classification support")

        self.load_all_protocols()

    def _load_signatures(self) -> Dict[str, str]:
        """Load HMAC signatures for trusted protocols"""
        if self.SIGNATURE_FILE.exists():
            try:
                with open(self.SIGNATURE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _verify_protocol(self, protocol_id: str, content: str) -> bool:
        """Verify protocol signature if secret key is set"""
        secret_key = os.environ.get('PROTOCOL_SECRET_KEY')
        if not secret_key:
            # No key = trust all local files (default for local use)
            return True

        if protocol_id not in self.trusted_signatures:
            print(f"⚠️ Protocol {protocol_id} has no signature")
            return False

        expected = self.trusted_signatures[protocol_id]
        actual = hmac.new(
            secret_key.encode(),
            content.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(actual, expected)

    # ---------------------------------------------------------
    # LOAD PROTOCOLS
    # ---------------------------------------------------------
    def load_all_protocols(self) -> None:
        """Load all JSON protocol files from the protocols directory."""
        self.protocols = {}
        if not self.protocols_dir.exists():
            print(f"⚠️ Protocol directory not found: {self.protocols_dir}")
            return

        for json_file in self.protocols_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    proto = json.loads(content)

                pid = json_file.stem

                # 🔐 Verify signature if security enabled
                if not self._verify_protocol(pid, content):
                    print(f"⚠️ Protocol {pid} failed signature verification - skipping")
                    continue

                # 🔐 Remove any python_stage entries for security
                if 'stages' in proto:
                    proto['stages'] = [
                        stage for stage in proto['stages']
                        if stage.get('type') != 'python_stage'
                    ]

                self.protocols[pid] = proto
                print(f"✅ Loaded protocol: {proto.get('protocol_name', pid)}")
            except Exception as e:
                print(f"⚠️ Error loading protocol {json_file.name}: {e}")

    # ---------------------------------------------------------
    # RUN PROTOCOL
    # ---------------------------------------------------------
    def run_protocol(self, samples: List[Dict[str, Any]], protocol_id: str) -> List[Dict[str, Any]]:
        """
        Run a protocol (by protocol_id = JSON filename stem) on a list of samples.
        """
        if protocol_id not in self.protocols:
            print(f"⚠️ Protocol not found: {protocol_id}")
            return samples

        protocol = self.protocols[protocol_id]
        stages = protocol.get("stages", [])

        for stage in stages:
            stype = stage.get("type")
            stage_name = stage.get("name", stage.get("id", "unknown"))
            print(f"▶️ Running stage: {stage_name}")

            if stype == "rule_stage":
                self._run_rule_stage(samples, stage)

            elif stype == "classification_stage":
                self._run_classification_stage(samples, stage)

            # 🔐 SECURITY FIX: python_stage removed
            # elif stype == "python_stage":
            #     self._run_python_stage(samples, stage)

            else:
                print(f"⚠️ Unknown stage type: {stype}")

        return samples

    # ---------------------------------------------------------
    # RULE STAGE
    # ---------------------------------------------------------
    def _run_rule_stage(self, samples: List[Dict[str, Any]], stage: Dict[str, Any]) -> None:
        rules = stage.get("rules", [])
        stage_logic = stage.get("rules_logic", "OR").upper()

        for sample in samples:
            for rule in rules:
                if self._rule_matches(sample, rule):
                    outputs = rule.get("outputs", {})
                    self._apply_outputs(sample, outputs)
                    if stage_logic == "OR":
                        break

    def _rule_matches(self, sample: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        conditions = rule.get("conditions", [])
        logic = rule.get("conditions_logic", "AND").upper()

        results = [self._evaluate_condition(sample, cond) for cond in conditions]

        return all(results) if logic == "AND" else any(results)

    def _evaluate_condition(self, sample: Dict[str, Any], cond: Dict[str, Any]) -> bool:
        field = cond.get("field")
        op = cond.get("operator")
        value = cond.get("value")

        sval = sample.get(field)

        # Null checks
        if op == "is_null":
            return sval is None or sval == "" or str(sval).lower() == "nan"
        if op == "is_not_null":
            return not (sval is None or sval == "" or str(sval).lower() == "nan")

        # Equality / inequality: support both numeric and string
        if op in ("==", "!="):
            sval_num, value_num = self._to_float_or_none(sval), self._to_float_or_none(value)
            if sval_num is not None and value_num is not None:
                return sval_num == value_num if op == "==" else sval_num != value_num
            return sval == value if op == "==" else sval != value

        # Numeric operators
        sval_num = self._to_float_or_none(sval)
        value_num = self._to_float_or_none(value)

        if sval_num is None or (op != "between" and value_num is None):
            return False

        if op == ">": return sval_num > value_num
        if op == "<": return sval_num < value_num
        if op == ">=": return sval_num >= value_num
        if op == "<=": return sval_num <= value_num

        if op == "between":
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                return False
            lo, hi = value
            lo_num = self._to_float_or_none(lo)
            hi_num = self._to_float_or_none(hi)
            return lo_num is not None and hi_num is not None and lo_num <= sval_num <= hi_num

        return False

    @staticmethod
    def _to_float_or_none(v: Any) -> Optional[float]:
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _apply_outputs(self, sample: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Apply rule outputs to a sample, supporting copy_field."""
        for key, val in outputs.items():
            if isinstance(val, dict) and "copy_field" in val:
                sample[key] = sample.get(val["copy_field"])
            else:
                sample[key] = val

    # ---------------------------------------------------------
    # CLASSIFICATION STAGE
    # ---------------------------------------------------------
    def _run_classification_stage(self, samples: List[Dict[str, Any]], stage: Dict[str, Any]) -> None:
        if self.classification_engine is None:
            print("⚠️ Cannot run classification stage: classification engine not available")
            return

        scheme_id = stage.get("scheme_id")
        output_map = stage.get("output_mapping", {})

        classified = self.classification_engine.classify_all_samples(
            samples,
            scheme_id=scheme_id,
            output_column="__temp_class"
        )

        for s in classified:
            for src, dst in output_map.items():
                if src in s:
                    s[dst] = s[src]

    # ---------------------------------------------------------
    # PYTHON STAGE - REMOVED FOR SECURITY
    # ---------------------------------------------------------
    # def _run_python_stage(self, samples: List[Dict[str, Any]], stage: Dict[str, Any]) -> None:
    #     callable_path = stage.get("python_callable")
    #     if not callable_path:
    #         return
    #
    #     print(f"      Running Python stage: {callable_path}")
    #
    #     try:
    #         module_name, func_name = callable_path.rsplit(".", 1)
    #         module = import_module(module_name)
    #         func: Callable = getattr(module, func_name)
    #         func(samples, stage)
    #
    #     except (ImportError, AttributeError) as e:
    #         print(f"⚠️ Error in python_stage {callable_path}: {e}")
    #
    #     except Exception as e:
    #         print(f"⚠️ Unexpected error in python_stage: {e}")
