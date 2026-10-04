"""Explicit real eval orchestration. Discovery skips it unless HW2_RUN_PROFILE is set."""
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from hw2_runtime import PromptGuard
import stand


@unittest.skipUnless(os.environ.get("HW2_RUN_PROFILE"), "Live eval is not authorized by this invocation")
class LiveSuiteHW2(unittest.TestCase):
    def test_live_golden_run_with_captures(self):
        profile = os.environ["HW2_RUN_PROFILE"]
        self.assertIn(profile, ("clean", "lesson-03"))
        line = os.environ.get("HW2_PROMPT_LINE")
        only = os.environ.get("HW2_ONLY")
        guard = PromptGuard()
        snapshot = {"before_sha256": guard.sha256, "profile": profile, "line": line}
        label = os.environ.get("HW2_RUN_LABEL", profile)
        self.assertTrue(label.replace("-", "").replace("_", "").isalnum())
        try:
            if line:
                # Forecast commit proof must exist before applying the experiment.
                proof = json.loads((HERE / "evidence" / "forecast-commit.json").read_text())
                self.assertTrue(proof["commit"])
                self.assertEqual(proof["line"], line)
                guard.append(line)
            snapshot["during_prompt"] = stand._call("GET", "/api/_test/prompt")
            args = ["docker", "compose", "run", "--rm", "-T", "eval", "python",
                    "hw2_capture.py", "--set", "golden", "--profile", profile]
            if only:
                args += ["--only", only]
            result = subprocess.run(args, cwd=HERE, capture_output=True)
            (HERE / "evidence" / (label + ".stdout.txt")).write_bytes(result.stdout)
            (HERE / "evidence" / (label + ".stderr.txt")).write_bytes(result.stderr)
            snapshot["runner_exit_code"] = result.returncode
            self.assertIn(result.returncode, (0, 1), "Runner infrastructure failure")
        finally:
            guard.restore()
            snapshot["after_sha256"] = hashlib.sha256(guard.original).hexdigest()
            snapshot["restored_prompt"] = stand._call("GET", "/api/_test/prompt")
            (HERE / "evidence" / (label + ".prompt-guard.json")).write_text(
                json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
