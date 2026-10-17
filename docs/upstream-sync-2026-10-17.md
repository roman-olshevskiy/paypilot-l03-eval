# Upstream sync — 2026-10-17

Source: sergeytkachenko/paypilot-l03-eval main, b9ee5fb (2 new commits).
Target: roman-olshevskiy/paypilot-l03-eval main, via PR only.

Changes:
- runner uses context.customer_id; stand.chat/dialog forward the separate session identity.
- Demo dispute inputs no longer repeat a customer ID in prose; their context keeps it. The upstream generator and demo/mock sets change accordingly.
- Level-7 judge defaults to claude-haiku-5-5; empty JUDGE_MODEL selects that default.

Compatibility fixes included:
- hw2_capture forwards customer_id to the new chat signature. Without this fix the old wrapper rejects the new keyword before a live run.
- The acceptance test checks the frozen kit manifest against kit_commit 8108fc8, allowing only Git checkout line-ending representation. It no longer asserts that an intentionally updated working copy equals the old kit.
- The offline capture test checks customer_id forwarding. Historical manifest and submitted golden.jsonl are not edited.

Impact on HW2:
- Frozen sets/golden.jsonl, all full answers/traces, reports and $0.55 reconciliation stay byte-for-byte unchanged. Dataset set_hash stays 92f5e7f20c48.
- The original HW2 artifact set was based on kit 8108fc8; code immediately before this sync is e1815e2. Use these snapshots for historical reproduction.
- Upstream demo bytes and the generator output changed, so their hashes need not match historical captures. Do not regenerate the accepted golden to disguise this difference.
- Daily runs exclude the five human/level-7 cases, so changing the judge default does not add judge calls to those already completed runs.
- Own generate_golden.py retains its previous dispute wording. Context already carries customer_id, so the new runner supplies identity without changing golden bytes.
- hw2_runtime.py still targets the original local stand for historical runs. Migrating it to shared, adding remote key headers, and mutating a shared runtime prompt are not part of this sync.

Validation results are recorded in the PR.
