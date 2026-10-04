"""Evidence adapter for the unchanged course runner. No run without explicit --profile."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cli
import runner
import stand

HERE = Path(__file__).resolve().parent
CLOCK = "2026-09-15T10:00:00Z"


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(argv):
    args = cli.parse(argv)
    if not args.profile or args.dry_run:
        raise ValueError("Capture requires an explicit profile and a real eval run")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    folder = HERE / "evidence" / "runs" / (stamp + "-" + args.profile)
    saved_profile = stand.profile()
    saved_clock = stand._call("GET", "/api/_test/clock")
    old_chat, old_trace, old_reset, old_case = stand.chat, stand.trace, stand.reset, runner.run_case
    current = {"case": None}
    responses = {}
    captures = []
    before_reports = set((HERE / "reports").glob("*.json"))
    code = None

    def chat(message, session_id=None):
        response = old_chat(message, session_id)
        responses[response["request_id"]] = {"response": response, "question": message}
        return response

    def trace(request_id):
        tree = old_trace(request_id)
        response = responses[request_id]
        usage = response["response"].get("usage") or stand.usage(tree)
        captures.append({"case_id": current["case"], "request_id": request_id,
                         **response, "trace": tree, "usage": usage,
                         "llm_calls": len(stand.llm_calls(tree)),
                         "llm_call_attributes": stand.llm_calls(tree)})
        return tree

    def reset():
        result = old_reset()
        stand.set_clock(CLOCK)
        clock = stand._call("GET", "/api/_test/clock")
        if datetime.fromisoformat(clock["now"]).astimezone(timezone.utc).isoformat() != "2026-09-15T10:00:00+00:00":
            raise RuntimeError("Clock mismatch after reset")
        return result

    def run_case(case):
        if case.get("context", {}).get("clock", CLOCK) != CLOCK:
            raise ValueError("Unsupported per-case clock in frozen series")
        current["case"] = case["id"]
        return old_case(case)

    stand.chat, stand.trace, stand.reset, runner.run_case = chat, trace, reset, run_case
    try:
        stand.set_defects("")
        stand.set_clock(CLOCK)
        save(folder / "before.json", {"health": stand.health(), "clock": stand._call("GET", "/api/_test/clock"),
             "prompt": stand._call("GET", "/api/_test/prompt")})
        code = cli.main(argv)
        save(folder / "during.json", {"health": stand.health(), "clock": stand._call("GET", "/api/_test/clock"),
             "prompt": stand._call("GET", "/api/_test/prompt")})
        return code
    finally:
        stand.chat, stand.trace, stand.reset, runner.run_case = old_chat, old_trace, old_reset, old_case
        save(folder / "captures.json", captures)
        reports = sorted(set((HERE / "reports").glob("*.json")) - before_reports)
        usage = {"agent_chat_requests": len(captures), "agent_model_calls": sum(c["llm_calls"] for c in captures),
                 "input_tokens": sum(c["usage"].get("input_tokens", 0) for c in captures),
                 "output_tokens": sum(c["usage"].get("output_tokens", 0) for c in captures)}
        save(folder / "manifest.json", {"exit_code": code, "reports": [p.name for p in reports],
             "clock": CLOCK, "usage": usage,
             "files": [{"path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in reports]})
        stand.set_profile(saved_profile["profile"])
        stand.set_defects(",".join(saved_profile.get("extra_defects", [])))
        stand.set_clock(saved_clock.get("runtime_override"))
        save(folder / "restored.json", {"profile": stand.profile(), "clock": stand._call("GET", "/api/_test/clock")})


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
