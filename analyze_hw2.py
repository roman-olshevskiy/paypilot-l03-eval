"""Offline analysis of three unchanged course reports and their full captures."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"


def main():
    runs = []
    for folder in sorted((EVIDENCE / "runs").iterdir()):
        manifest_file = folder / "manifest.json"
        if not manifest_file.exists():
            continue
        manifest = json.loads(manifest_file.read_text())
        if len(manifest["reports"]) != 1:
            raise ValueError("Expected exactly one course report per successful invocation")
        path = HERE / "reports" / manifest["reports"][0]
        report = json.loads(path.read_text())
        captures = json.loads((folder / "captures.json").read_text())
        if sum(c["usage"]["input_tokens"] + c["usage"]["output_tokens"] for c in captures) != sum(c["tokens"] for c in report["cases"]):
            raise ValueError("Raw report / capture tokens differ")
        models = sorted({a["gen_ai.request.model"] for c in captures
                         for a in c["llm_call_attributes"] if "gen_ai.request.model" in a})
        if any(not m.startswith("claude-haiku-4-5") for m in models):
            raise ValueError("Pricing model assumption does not match trace")
        row = {"report": path.name, "folder": str(folder.relative_to(HERE)).replace("\\", "/"),
               "profile": report["profile"], "set_hash": report["set_hash"],
               "ran_at": report["ran_at"], "passed": report["passed"], "total": report["total"],
               "failed": [c["id"] for c in report["cases"] if not c["verdict"]["passed"]],
               "tokens": sum(c["tokens"] for c in report["cases"]), "models": models,
               **manifest["usage"]}
        row["cost_estimate_usd"] = (row["input_tokens"] + 5 * row["output_tokens"]) / 1_000_000
        row["raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        runs.append((row, report, captures))
    full = [r for r in runs if r[0]["total"] == 30]
    if len(full) != 3:
        raise ValueError("Exactly three 30-case reports are required")
    if len({r[0]["set_hash"] for r in full}) != 1:
        raise ValueError("Set hashes differ")
    baseline, defect, changed = full
    if [r[0]["profile"] for r in full] != ["clean", "lesson-03", "clean"]:
        raise ValueError("Unexpected ordering of three profiles")
    before = {c["id"]: c["verdict"]["passed"] for c in baseline[1]["cases"]}
    after = {c["id"]: c["verdict"]["passed"] for c in changed[1]["cases"]}
    transitions = [{"id": cid, "baseline": before[cid], "changed": after[cid]}
                   for cid in before if before[cid] != after[cid]]
    proof = json.loads((EVIDENCE / "forecast-commit.json").read_text())
    if proof["committed_at"] >= changed[0]["ran_at"]:
        raise ValueError("Forecast commit must precede third report")
    result = {"set_hash": baseline[0]["set_hash"], "runs": [r[0] for r in runs],
              "transitions": transitions,
              "pass_to_fail": [r["id"] for r in transitions if r["baseline"] and not r["changed"]],
              "fail_to_pass": [r["id"] for r in transitions if not r["baseline"] and r["changed"]],
              "changed_verdicts": len(transitions), "compared_cases": len(before),
              "forecast": proof, "pricing": {"model": "Claude Haiku 4.5", "input_per_million_usd": 1,
                  "output_per_million_usd": 5, "checked_on": "2026-10-04",
                  "source": "https://platform.claude.com/docs/en/about-claude/pricing",
                  "billing_verified": (EVIDENCE / "billing-reconciliation.json").exists(),
                  "billing_verification_scope": "Aggregate monthly increase, rounded to cents",
                  "billing_evidence": "evidence/billing-reconciliation.json"},
              "series_cost_estimate_usd": sum(r[0]["cost_estimate_usd"] for r in full),
              "total_cost_including_controls_usd": sum(r[0]["cost_estimate_usd"] for r in runs)}
    (EVIDENCE / "run-analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
