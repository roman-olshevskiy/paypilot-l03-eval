"""Offline HW2 acceptance checks; no stand API or model."""
import importlib.util
import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import generate_golden as G
from loader import load, summarise
from hw2_runtime import PromptGuard
import hw2_capture as capture
import stand


class GoldenContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load(HERE / "sets/golden.jsonl")

    def test_homework_contract(self):
        self.assertEqual(len(self.cases), 35)
        meta = [c["additional_metadata"] for c in self.cases]
        own = [m for m in meta if m["added_in"] == "hw2"]
        self.assertEqual(len(own), 23)
        self.assertEqual(sum(m["oracle"] == "human" for m in own), 5)
        self.assertEqual({m["source"] for m in meta}, {"engine", "complaint", "edge"})
        summary = summarise(self.cases)
        self.assertTrue({1, 2, 3, 4, 7} <= set(summary["ladder_levels"]))
        self.assertEqual(summary["gates"], {"daily": 30, "release": 5})
        for c in self.cases:
            self.assertTrue(c["expected_output"])
            self.assertTrue(c["additional_metadata"]["why_this_level"])
            self.assertEqual(c["context"]["clock"], G.CLOCK)
            if c["additional_metadata"]["oracle"] == "human":
                self.assertEqual(c["additional_metadata"]["runs"], 5)

    def test_engine_expectations_and_complaint_identity(self):
        for c in self.cases:
            m = c["additional_metadata"]
            if m["oracle"] != "engine":
                continue
            self.assertNotIn("...", m["engine_call"], c["id"])
            value = G.evaluate_call(m["engine_call"])
            if "expected_number" in m:
                self.assertAlmostEqual(float(value), float(m["expected_number"]), delta=m["tolerance"])
            elif "expected_flag" in m:
                self.assertIs(value, m["expected_flag"])
            elif m["assertion"] == "not_regex":
                self.assertIs(value, False)
            elif m["assertion"] == "contains":
                self.assertIn(str(value), c["expected_output"])
            elif m["assertion"] == "regex":
                self.assertEqual(value, G.policy.DISPUTE_WINDOWS_DAYS)
        c11 = next(c for c in self.cases if c["id"] == "CMP-C11")
        self.assertEqual(c11["context"]["customer_id"], "CUS-0009")
        self.assertIn("TX-0902", c11["input"])

    def test_not_renamed_kit(self):
        inputs = {c["input"] for c in load(HERE / "sets/l03.jsonl")}
        spec = importlib.util.spec_from_file_location("kit_generator", HERE / "generate_from_engines.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        inputs.update(c["input"] for c in module.fx_cases() + module.limit_cases() + module.dispute_cases())
        for c in self.cases:
            if c["additional_metadata"]["added_in"] == "hw2":
                self.assertNotIn(c["input"], inputs, c["id"])
                self.assertTrue(c["additional_metadata"]["novelty"])
        complaints = {c["additional_metadata"].get("complaint_id") for c in self.cases
                      if c["additional_metadata"]["added_in"] == "hw2"}
        self.assertTrue({"C-01", "C-11", "C-12", "C-14"} <= complaints)

    def test_boundary_and_original_files(self):
        byid = {c["id"]: c for c in self.cases}
        self.assertEqual(byid["FX-006-S"]["additional_metadata"]["expected_number"], 0)
        self.assertEqual(byid["FX-007-S"]["additional_metadata"]["expected_number"], G.policy.FX_SPREAD_PCT["tier2"])
        self.assertEqual(byid["FX-008-S"]["additional_metadata"]["expected_number"], 0)
        self.assertEqual(byid["FX-009-S"]["additional_metadata"]["expected_number"], G.policy.FX_SPREAD_PCT["tier1"])
        baseline = json.loads((HERE / "evidence/kit-baseline-manifest.json").read_text())
        for entry in baseline["files"]:
            self.assertEqual(hashlib.sha256((HERE / entry["path"]).read_bytes()).hexdigest().upper(),
                             entry["sha256"], entry["path"])


class EvidenceGuards(unittest.TestCase):
    def test_prompt_restore_after_failure(self):
        state = {"base": b"Original base\n"}
        with patch("hw2_runtime.read_base", side_effect=lambda: state["base"]), \
             patch("hw2_runtime.write_base", side_effect=lambda value: state.update(base=value)):
            guard = PromptGuard()
            try:
                guard.append("One experimental line.")
                self.assertIn(b"experimental", state["base"])
                raise RuntimeError("Simulated failure")
            except RuntimeError:
                pass
            finally:
                guard.restore()
            self.assertEqual(state["base"], b"Original base\n")

    def test_full_capture_and_state_restoration_after_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            state = {"profile": "lesson-02", "extra": ["D16"], "clock": None}
            response = {"request_id": "offline-test", "answer": "x" * 700,
                        "usage": {"input_tokens": 100, "output_tokens": 50}}
            tree = {"name": "root", "children": [{"name": "llm.call", "attributes": {}}]}
            def api(method, path, *args, **kwargs):
                if path.endswith("clock"):
                    return {"now": "2026-09-15T10:00:00+00:00", "runtime_override": state["clock"]}
                return {"text": "base", "version": "base.v1"}
            def fake_main(argv):
                stand.reset()
                out = stand.chat("Question")
                stand.trace(out["request_id"])
                raise RuntimeError("Simulated runner error")
            with patch.object(capture, "HERE", Path(temp)), \
                 patch.object(stand, "profile", side_effect=lambda: {"profile": state["profile"], "extra_defects": state["extra"]}), \
                 patch.object(stand, "_call", side_effect=api), \
                 patch.object(stand, "set_profile", side_effect=lambda p: state.update(profile=p)), \
                 patch.object(stand, "set_defects", side_effect=lambda d: state.update(extra=d.split(",") if d else [])), \
                 patch.object(stand, "set_clock", side_effect=lambda c: state.update(clock=c)), \
                 patch.object(stand, "health", return_value={"status": "ok"}), \
                 patch.object(stand, "reset", return_value={}), \
                 patch.object(stand, "chat", return_value=response), \
                 patch.object(stand, "trace", return_value=tree), \
                 patch.object(capture.cli, "main", side_effect=fake_main):
                with self.assertRaisesRegex(RuntimeError, "Simulated runner error"):
                    capture.run(["--set", "golden", "--profile", "clean"])
            saved = json.loads(next(Path(temp).glob("evidence/runs/*/captures.json")).read_text())
            self.assertEqual(len(saved[0]["response"]["answer"]), 700)
            self.assertEqual(saved[0]["llm_calls"], 1)
            self.assertEqual(state, {"profile": "lesson-02", "extra": ["D16"], "clock": None})


if __name__ == "__main__":
    unittest.main()
