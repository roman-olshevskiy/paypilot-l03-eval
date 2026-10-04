"""HW2 generator derived from generate_from_engines.py, kit 8108fc8.
All numeric/flag/deadline expectations are computed offline by clean engines.
Human rubrics are authored here and are not engine-generated expectations.
"""
import argparse
import copy
import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
for root in (Path(os.environ.get("STAND_DIR", "/course")), Path("/course"), HERE.parent / "paypilot-stand"):
    if (root / "app" / "engines").exists():
        sys.path.insert(0, str(root))
        break
from app.engines import disputes, fx, limits, policy
from app import seed

CLOCK = "2026-09-15T10:00:00Z"
AS_OF = date(2026, 9, 15)
CUSTOMERS = {row[0]: {"tier": row[3], "hold": bool(row[4]), "used": row[5]}
             for row in seed.CUSTOMERS}
ACCOUNTS = {row[0]: row for row in seed.ACCOUNTS}
TRANSACTIONS = {row[0]: row for row in seed.TRANSACTIONS}
WHY_NUMERIC = ("A money figure requires a tolerance, not a verbatim sentence. "
               "Level 2 reads the expected tool field and the same number in the answer.")
WHY_FLAG = ("Eligibility is boolean: level 1 verifies the tool result directly. "
            "A polite or plausible answer cannot replace a correct eligibility result.")


def fee_call(amount, currency, kind):
    return f"fx.transfer_fee(policy.to_eur({amount!r}, {currency!r}), {kind!r})"


def transfer_rows(customer):
    accounts = {row[0] for row in seed.ACCOUNTS if row[1] == customer}
    return [{"date": date.fromisoformat(row[2]), "amount_eur": policy.to_eur(row[3], row[4])}
            for row in seed.TRANSACTIONS
            if row[1] in accounts and row[6] == "out" and row[8] == "settled"]


def limit_call(customer):
    rows = transfer_rows(customer)
    literal = "[" + ", ".join(
        "{'date': date(%d, %d, %d), 'amount_eur': %r}" %
        (row["date"].year, row["date"].month, row["date"].day, row["amount_eur"])
        for row in rows) + "]"
    return f"limits.status({CUSTOMERS[customer]['tier']!r}, date(2026, 9, 15), {literal})"


def dispute_call(txid, reason):
    tx = TRANSACTIONS[txid]
    cust = ACCOUNTS[tx[1]][1]
    d = date.fromisoformat(tx[2])
    return (f"disputes.check({reason!r}, date({d.year}, {d.month}, {d.day}), "
            f"{tx[8]!r}, date(2026, 9, 15), compliance_hold={CUSTOMERS[cust]['hold']!r})")


def evaluate_call(expression):
    return eval(expression, {"__builtins__": {}, "date": date, "fx": fx,
                             "limits": limits, "disputes": disputes, "policy": policy, "dict": dict})


def base_case(cid, question, expected, *, assertion, source, failure_mode,
              severity="high", customer=None, call=None, **extra):
    context = {"clock": CLOCK}
    if customer:
        context["customer_id"] = customer
    meta = {"layer": "generation", "oracle": "engine", "assertion": assertion,
            "source": source, "failure_mode": failure_mode, "severity": severity,
            "runs": 1, "gate": "daily", "added_in": "hw2",
            "why_this_level": WHY_NUMERIC if assertion == "tool_grounded_numeric" else WHY_FLAG,
            "origin": "own", "novelty": extra.pop("novelty")}
    if call:
        meta["engine_call"] = call
    meta.update(extra)
    return {"id": cid, "input": question, "expected_output": expected,
            "context": context, "additional_metadata": meta}


def fx_cases():
    """Copy of the kit fx_cases plan, extended with six new amount/customer pairs."""
    out = []
    plan = [
        ("FX-006", "CUS-0007", 1000, "EUR", "USD"),
        ("FX-007", "CUS-0007", 1001, "EUR", "USD"),
        ("FX-008", "CUS-0001", 380, "EUR", "USD"),
        ("FX-009", "CUS-0001", 381, "EUR", "USD"),
        ("FX-010", "CUS-0002", 200, "EUR", "USD"),
        ("FX-011", "CUS-0002", 201, "EUR", "USD"),
    ]
    for cid, customer, amount, frm, to in plan:
        tier, used = CUSTOMERS[customer]["tier"], CUSTOMERS[customer]["used"]
        call = f"fx.quote({amount}, {frm!r}, {to!r}, {tier!r}, allowance_used_eur={used!r})"
        q = evaluate_call(call)
        novelty = f"New {customer}/{amount}{frm} boundary, absent from kit generation plan."
        out.append(base_case(cid,
            f"I'm {customer}. Convert {amount} {frm} to {to}. What is the final amount I receive?",
            f"{q.final_amount:.2f} {to}", assertion="tool_grounded_numeric",
            source="edge", failure_mode="wrong_spread", customer=customer,
            call=call + ".final_amount", tool="quote_fx", field="final_amount",
            expected_number=round(q.final_amount, 2), tolerance=0.02, novelty=novelty))
        # Four obligatory/custom boundary pairs also receive a different observable:
        # the spread field. CUS-0002 already has one amount case on each side.
        if cid in ("FX-006", "FX-007", "FX-008", "FX-009"):
            out.append(base_case(cid + "-S",
                f"I'm {customer}. What spread applies if I convert {amount} {frm} to {to}?",
                f"{q.spread_pct:.2f} percent", assertion="tool_result_numeric",
                source="edge", failure_mode="allowance_boundary", customer=customer,
                call=call + ".spread_pct", tool="quote_fx", field="spread_pct",
                expected_number=q.spread_pct, tolerance=0.001, novelty=novelty +
                " This case checks spread_pct rather than final_amount.",
                why_this_level="Level 2 reads the spread field directly; text wording and total amount are not sufficient."))
    return out


def complaint_cases():
    out = []
    for cid, amount, currency, source, complaint in [
        ("SWF-001", 1000, "EUR", "complaint", "C-01"),
        ("SWF-002", 1000, "USD", "edge", None),
    ]:
        call = fee_call(amount, currency, "swift") + "['total_fee_eur']"
        expected = evaluate_call(call)
        extra = {"complaint_id": complaint} if complaint else {}
        out.append(base_case(cid,
            f"I'm CUS-0001. For a SWIFT transfer of {amount} {currency}, "
            "what is the TOTAL fee in EUR, including the flat and percentage components?",
            f"{expected:.2f} EUR", assertion="numeric", source=source,
            failure_mode="wrong_fee_total", customer="CUS-0001", call=call,
            expected_number=expected, tolerance=0.01,
            novelty="No SWIFT fee case exists in the kit set or unchanged engine generator.",
            why_this_level="Level 2 checks the calculated public fee; no quote_swift tool exists. It does not prove correct component explanations.",
            **extra))
    call = "fx.quote(2000, 'EUR', 'USD', 'tier2', allowance_used_eur=5000.0).final_amount"
    expected = evaluate_call(call)
    out.append(base_case("CMP-C05",
        "I'm CUS-0005. Recalculate a 2000 EUR conversion to USD and state the final amount received after spread.",
        f"{expected:.2f} USD", assertion="tool_grounded_numeric", source="edge",
        failure_mode="wrong_final_amount", customer="CUS-0005", call=call,
        tool="quote_fx", field="final_amount", expected_number=round(expected, 2), tolerance=0.02,
        novelty="New 2000 EUR amount for CUS-0005; original C-05 is 6000 EUR and already represented by kit FX-003, so this is an edge variant, not a new reproduced complaint."))
    for cid, txid, reason, complaint in [
        ("CMP-C11", "TX-0902", "fraud_card_not_present", "C-11"),
        ("CMP-C12", "TX-0201", "duplicate_charge", "C-12"),
    ]:
        call = dispute_call(txid, reason)
        result = evaluate_call(call)
        customer = ACCOUNTS[TRANSACTIONS[txid][1]][1]
        out.append(base_case(cid,
            f"I'm {customer}. Check whether {txid} is eligible for a dispute under {reason}.",
            f"check_dispute_eligibility.eligible = {str(result.eligible).lower()}",
            assertion="tool_result_flag", source="complaint", failure_mode="wrong_window",
            severity="critical", customer=customer, call=call + ".eligible",
            layer="action", tool="check_dispute_eligibility", field="eligible",
            expected_flag=result.eligible, complaint_id=complaint,
            transaction_id=txid, reason_code=reason,
            novelty=("PharmaPlus TX-0902 belongs to CUS-0009 in the complaint and is absent from the kit generator and demo."
                     if complaint == "C-11" else
                     "CloudServe TX-0201 is absent from both kit generator and demo eligibility cases.")))
    windows = policy.DISPUTE_WINDOWS_DAYS
    pattern = "(?is)^" + "".join("(?=.*" + code + ")" for code in windows) + r"(?=.*\b60\b).*"
    out.append(base_case("CMP-C14",
        "I'm CUS-0002. List ALL dispute reason codes using their exact snake_case names, "
        "AND state the dispute window for duplicate_charge in days.",
        ", ".join(windows) + "; duplicate_charge: " + str(windows["duplicate_charge"]) + " days",
        assertion="regex", source="complaint", failure_mode="incomplete_two_part_answer",
        customer="CUS-0002", call="dict(policy.DISPUTE_WINDOWS_DAYS)",
        pattern=pattern, complaint_id="C-14",
        novelty="New two-part completeness case: all reason codes plus the duplicate window; neither kit set nor generator has this combination.",
        why_this_level="Level 3 checks five required literal codes and the computed window in arbitrary order; tone and retrieval correctness remain outside this assertion."))
    return out


def limit_cases():
    out = []
    customer = "CUS-0002"
    call = limit_call(customer)
    result = evaluate_call(call)
    for kind in ("daily", "monthly"):
        field = kind + "_remaining_eur"
        value = getattr(result, field)
        out.append(base_case("LIM-HW2-" + kind.upper(),
            f"I'm {customer}. Use check_limits and tell me my remaining {kind.upper()} transfer limit in EUR.",
            f"check_limits.{field} = {value:.2f} EUR",
            assertion="tool_result_numeric", source="engine", failure_mode="daily_as_monthly",
            customer=customer, call=call + "." + field, layer="action",
            tool="check_limits", field=field, expected_number=value, tolerance=0.01,
            novelty="CUS-0002 is absent from the kit limit generator plan (CUS-0010 and CUS-0001).",
            why_this_level="Level 2 checks the correct daily/monthly payload field, not a recomputed answer that can hide D22."))
    return out


def kit_cases():
    source = HERE / "sets" / "l03.jsonl"
    originals = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    out = []
    fx_specs = {
        "FX-004": (2000, "EUR", "USD", "tier2", 0.0),
        "FX-002": (3000, "EUR", "USD", "tier2", 800.0),
        "FX-003": (6000, "EUR", "USD", "tier2", 5000.0),
        "FX-003-S": (6000, "EUR", "USD", "tier2", 5000.0),
        "FX-005": (5000, "GBP", "EUR", "tier3", 15000.0),
    }
    for original in originals:
        if original["id"] in ("CMP-003", "CMP-006"):
            continue
        c = copy.deepcopy(original)
        m = c["additional_metadata"]
        m.update(origin="kit", novelty="Retained kit scenario, not counted as own.")
        c["context"]["clock"] = CLOCK
        cid = c["id"]
        if cid in fx_specs:
            amount, frm, to, tier, used = fx_specs[cid]
            call = f"fx.quote({amount}, {frm!r}, {to!r}, {tier!r}, allowance_used_eur={used!r})"
            field = "spread_pct" if cid.endswith("-S") else "final_amount"
            value = evaluate_call(call + "." + field)
            m["engine_call"] = call + "." + field
            if field == "spread_pct":
                c["expected_output"] = f"{value}%"
            else:
                m["expected_number"] = round(value, 2)
                c["expected_output"] = f"{value:.2f} {to}"
        elif cid.startswith("LIM-"):
            call = limit_call("CUS-0010") + ".monthly_remaining_eur"
            value = evaluate_call(call)
            m.update(engine_call=call, expected_number=round(value, 2))
            c["expected_output"] = f"{value:.2f} EUR"
        elif cid == "DIS-001":
            call = "policy.DISPUTE_WINDOWS_DAYS['duplicate_charge']"
            m["engine_call"] = call
            c["expected_output"] = f"{evaluate_call(call)} days"
        elif cid in ("DIS-002-N", "DIS-006", "DIS-007"):
            txid = c["context"]["transaction_id"]
            reason = c["context"]["reason_code"]
            call = dispute_call(txid, reason) + ".eligible"
            value = evaluate_call(call)
            m["engine_call"] = call
            if m["assertion"] == "tool_result_flag":
                m["expected_flag"] = value
                c["expected_output"] = f"check_dispute_eligibility.eligible = {str(value).lower()}"
        out.append(c)
    return out


def human_cases():
    plans = [
        ("TON-HW2-001", "CUS-0002",
         "I'm CUS-0002. CloudServe charged me twice. I'm angry and exhausted. Please explain how I can get help with TX-0201 without sending me a wall of policy.",
         "Acknowledge the frustration without blame, explain a concrete supported next step, and avoid guaranteed refund or contact deadlines.",
         "complaint", "C-17"),
        ("TON-HW2-002", "CUS-0004",
         "I'm CUS-0004. Why can't I dispute TX-0402 as a duplicate charge? This feels unfair. Explain it so I can understand.",
         "Explain the relevant refusal in plain language without blaming the customer; give a supported next step and do not promise eligibility or a refund.",
         "edge", None),
        ("TON-HW2-003", "CUS-0006",
         "I'm CUS-0006. I need help with TX-0601, goods not received. Please tell me what I should do next without discussing internal bank processes.",
         "Give a useful supported next step without exposing internal compliance review, accusing the customer, or promising an unconfirmed response time.",
         "edge", None),
        ("TON-HW2-004", "CUS-0001",
         "I'm CUS-0001. I don't understand the SWIFT transfer fee. Explain the difference between the fixed fee and percentage in simple language.",
         "Explain both confirmed components clearly; distinguish the tariff formula from a final fee, ask for missing inputs if needed, and avoid jargon or invented amounts.",
         "edge", None),
        ("TON-HW2-005", "CUS-0007",
         "I'm CUS-0007. I'm upset that converting 1001 EUR costs more than converting 1000 EUR. Explain the allowance without making it sound like my fault.",
         "Explain the whole-conversion allowance rule accurately and respectfully, acknowledge the surprising boundary, and avoid implying only the excess is charged.",
         "edge", None),
    ]
    out = []
    for cid, customer, question, rubric, source, complaint in plans:
        meta = {"layer": "generation", "oracle": "human", "assertion": "judge",
                "source": source, "failure_mode": "tone_and_explanation",
                "severity": "high", "runs": 5, "gate": "release", "added_in": "hw2",
                "why_this_level": "Levels 1-6 cannot judge blame, clarity and the usefulness of a next step across paraphrases; a future calibrated rubric is needed.",
                "rubric": "PASS only if all clauses hold: " + rubric + " FAIL if any clause is violated.",
                "origin": "own", "novelty": "Authored situational rubric absent from kit."}
        if complaint:
            meta["complaint_id"] = complaint
        out.append({"id": cid, "input": question, "expected_output": rubric,
                    "context": {"customer_id": customer, "clock": CLOCK},
                    "additional_metadata": meta})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--manifest")
    args = parser.parse_args()
    cases = kit_cases() + fx_cases() + complaint_cases() + limit_cases() + human_cases()
    content = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    if args.manifest:
        rows = []
        for c in cases:
            m = c["additional_metadata"]
            row = {"id": c["id"], "origin": m["origin"], "added_in": m["added_in"],
                   "source": m["source"], "novelty": m["novelty"]}
            if m.get("engine_call"):
                value = evaluate_call(m["engine_call"])
                row.update(engine_call=m["engine_call"], result=value)
            rows.append(row)
        manifest = {"clock": CLOCK, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "cases": rows, "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
        Path(args.manifest).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"# {len(cases)} cases: {sum(c['additional_metadata']['added_in'] == 'hw2' for c in cases)} own, "
          f"{sum(c['additional_metadata']['oracle'] == 'human' for c in cases)} human", file=sys.stderr)


if __name__ == "__main__":
    main()
