"""Actual stand readiness test. It never calls /chat or a provider."""
import hashlib
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import stand
from hw2_runtime import PromptGuard, model_configuration

CLOCK = "2026-09-15T10:00:00Z"


class PreflightHW2(unittest.TestCase):
    def test_readiness_reset_clock_and_runtime_guard(self):
        saved_profile = stand.profile()
        saved_clock = stand._call("GET", "/api/_test/clock")
        guard = PromptGuard()
        record = {"before": {"health": stand.health(), "profile": saved_profile, "clock": saved_clock},
                  "model_configuration": model_configuration(),
                  "base_prompt_sha256": guard.sha256}
        try:
            self.assertEqual(record["before"]["health"]["status"], "ok")
            self.assertEqual(record["before"]["health"]["provider"], "anthropic")
            stand.set_profile("clean")
            stand.set_defects("")
            stand.set_clock(CLOCK)
            # Read the prompt and base file, but don't edit it during readiness.
            record["clean_prompt"] = stand._call("GET", "/api/_test/prompt")
            self.assertEqual(stand.profile()["profile"], "clean")
            self.assertEqual(record["clean_prompt"]["overlays"], [])
            stand.reset()
            record["after_reset_clock"] = stand._call("GET", "/api/_test/clock")
            observed = datetime.fromisoformat(record["after_reset_clock"]["now"]).astimezone(timezone.utc)
            self.assertEqual(observed.isoformat(), "2026-09-15T10:00:00+00:00")
            record["customers"] = stand.state("customers")
            record["transactions"] = stand.state("transactions")
            self.assertEqual(len(record["customers"]), 10)
            ids = {row["id"] for row in record["transactions"]}
            self.assertTrue({"TX-0902", "TX-0201", "TX-0402", "TX-0601"} <= ids)
        finally:
            # Only restoration of original bytes, no experimental row.
            guard.restore()
            stand.set_profile(saved_profile["profile"])
            stand.set_defects(",".join(saved_profile.get("extra_defects", [])))
            stand.set_clock(saved_clock.get("runtime_override"))
            record["restored"] = {"profile": stand.profile(), "clock": stand._call("GET", "/api/_test/clock"),
                                  "base_prompt_sha256": hashlib.sha256(guard.original).hexdigest()}
            record["model_calls"] = 0
            out = HERE / "evidence" / "preflight.json"
            out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
