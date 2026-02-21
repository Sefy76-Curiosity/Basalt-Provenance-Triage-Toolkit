"""
Protocol Engine for Basalt Provenance Triage Toolkit v10.2
Dynamically loads and runs multi-stage protocols from JSON files
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from importlib import import_module
import sys
from pathlib import Path

# Add the engines directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from classification_engine import ClassificationEngine
except ImportError:
    # Fallback - classification engine might not be available
    ClassificationEngine = None
    print("⚠️ Classification engine not found - protocol engine will have limited functionality")


class ProtocolEngine:
    def __init__(self, protocols_dir: str = None, schemes_dir: str = None):
        # If protocols_dir not provided, use default in engines folder
        if protocols_dir is None:
            self.protocols_dir = Path(__file__).parent / "protocols"
        else:
            self.protocols_dir = Path(protocols_dir)

        # DEBUG - add these three lines
        print(f"🔍 PROTOCOL ENGINE DEBUG:")
        print(f"   Looking in: {self.protocols_dir.absolute()}")
        print(f"   Folder exists: {self.protocols_dir.exists()}")

        self.protocols: Dict[str, Dict[str, Any]] = {}

        # Initialize classification engine if available
        if ClassificationEngine is not None:
            if schemes_dir is None:
                # Default to engines/classification/
                schemes_dir = Path(__file__).parent / "classification"
            self.classification_engine = ClassificationEngine(str(schemes_dir))
        else:
            self.classification_engine = None
            print("⚠️ Protocol engine running without classification support")

        self.load_all_protocols()

    # ---------------------------------------------------------
    # LOAD PROTOCOLS
    # ---------------------------------------------------------
    def load_all_protocols(self):
        self.protocols = {}
        if not self.protocols_dir.exists():
            print(f"⚠️ Protocol directory not found: {self.protocols_dir}")
            return

        for json_file in self.protocols_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    proto = json.load(f)
                pid = json_file.stem
                self.protocols[pid] = proto
                print(f"✅ Loaded protocol: {proto.get('protocol_name', pid)}")
            except Exception as e:
                print(f"⚠️ Error loading protocol {json_file.name}: {e}")

    # ---------------------------------------------------------
    # RUN PROTOCOL
    # ---------------------------------------------------------
    def run_protocol(self, samples: List[Dict[str, Any]], protocol_id: str) -> List[Dict[str, Any]]:
        if protocol_id not in self.protocols:
            print(f"⚠️ Protocol not found: {protocol_id}")
            return samples

        protocol = self.protocols[protocol_id]
        stages = protocol.get("stages", [])

        for stage in stages:
            stype = stage.get("type")

            if stype == "rule_stage":
                self._run_rule_stage(samples, stage)

            elif stype == "classification_stage":
                self._run_classification_stage(samples, stage)

            elif stype == "python_stage":
                self._run_python_stage(samples, stage)

            else:
                print(f"⚠️ Unknown stage type: {stype}")

        return samples

    # ---------------------------------------------------------
    # RULE STAGE
    # ---------------------------------------------------------
    def _run_rule_stage(self, samples, stage):
        rules = stage.get("rules", [])
        stage_logic = stage.get("rules_logic", "OR")

        for sample in samples:
            for rule in rules:
                if self._rule_matches(sample, rule):
                    sample.update(rule.get("outputs", {}))
                    if stage_logic == "OR":
                        break

    def _rule_matches(self, sample, rule):
        conditions = rule.get("conditions", [])
        logic = rule.get("conditions_logic", "AND")

        results = [self._evaluate_condition(sample, cond) for cond in conditions]

        return all(results) if logic == "AND" else any(results)

    def _evaluate_condition(self, sample, cond):
        field = cond.get("field")
        op = cond.get("operator")
        value = cond.get("value")

        sval = sample.get(field)

        # Null checks
        if op == "is_null":
            return sval is None or sval == "" or str(sval).lower() == "nan"
        if op == "is_not_null":
            return not (sval is None or sval == "" or str(sval).lower() == "nan")

        # Numeric conversion
        try:
            sval_num = float(sval)
        except:
            sval_num = None

        # Operators
        if op == ">": return sval_num > value
        if op == "<": return sval_num < value
        if op == ">=": return sval_num >= value
        if op == "<=": return sval_num <= value
        if op == "==": return sval_num == value
        if op == "!=": return sval_num != value

        if op == "between":
            lo, hi = value
            return lo <= sval_num <= hi

        return False

    # ---------------------------------------------------------
    # CLASSIFICATION STAGE
    # ---------------------------------------------------------
    def _run_classification_stage(self, samples, stage):
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
    # PYTHON STAGE
    # ---------------------------------------------------------
    def _run_python_stage(self, samples, stage):
        callable_path = stage.get("python_callable")
        if not callable_path:
            return

        module_name, func_name = callable_path.rsplit(".", 1)
        module = import_module(module_name)
        func: Callable = getattr(module, func_name)

        func(samples, stage)
