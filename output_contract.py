"""output_contract.py — Layer 3. Deterministic gate on the way out."""

import json, re, sys

ALLOWED_ACTIONS = {"call_carrier", "reassign_load", "flag_for_ops_review",
                   "update_pickup_window", "no_action"}

REQUIRED = {"load_id", "finding_type", "severity", "narrative", "recommended_action"}

# Same family as week3 / benchmark: avoid matching digits inside LOAD_133 / CAR_04.
NUM_RE = re.compile(
    r"(?<![A-Za-z_\d])\d{1,3}(?:,\d{3})*(?:\.\d+)?"
    r"|\d+\.\d+"
    r"|(?<![A-Za-z_\d])\d+(?![A-Za-z_\d])"
)


def _clean_num(text: str) -> str:
    return text.replace(",", "").replace(".", "")


def evidence_strings(evidence: dict) -> set[str]:
    """Exact cleaned string forms of each evidence value (no substring cheating)."""
    strings = set()
    for v in (evidence or {}).values():
        if v is None:
            continue
        strings.add(_clean_num(str(v)))
    return strings

# returns numbers from the narrative that do not exist in evidence 
def _ungrounded_numbers(narrative: str, evidence: dict) -> list[str]:
    allowed = evidence_strings(evidence)
    missing = []
    for num in NUM_RE.findall(narrative or ""):
        if _clean_num(num) not in allowed:
            missing.append(num)
    return missing


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def process_output(final_answer: str) -> dict:
    text = final_answer.strip()
    t = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if t:
        text = t.group(1).strip()
    else:
        # first {...} blob if model added a sentence before it
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("no JSON object in final answer")
        text = text[start : end + 1]
    briefing = json.loads(text)  # fail closed on bad JSON
    items = briefing["findings"] if isinstance(briefing, dict) and "findings" in briefing else briefing
    if not isinstance(items, list):
        raise ValueError("briefing must be a list of finding items")
    return {"findings": items}

def enforce(briefing: dict, findings: list, trace) -> dict:
    # todo, in order:
    violations = []
    keys = {(f.load_id, f.finding_type.value): f for f in findings}

    #  1. schema: every item has load_id, finding_type, severity, narrative, recommended_action
    for item in briefing["findings"]:
        missing = REQUIRED - set(item)
        if missing:
            violations.append(
                f"{(item.get('load_id'), item.get('finding_type'))}: "
                f"missing fields {sorted(missing)}"
            )
            continue

        #  2. finding_type AND severity must match the engine's finding exactly — the model may not upgrade or downgrade either
        key = (item["load_id"], _norm(item["finding_type"]))
        finding_item = keys.get(key)
        if finding_item is None:
            # retry lookup with raw finding_type for clearer error keys
            finding_item = keys.get((item["load_id"], item["finding_type"]))
        if finding_item is None:
            violations.append(f"{(item['load_id'], item['finding_type'])}: No matching engine finding for this key.")
            continue

        if _norm(item["severity"]) != finding_item.severity.value:
            violations.append(
                f"{key}: Severity Mismatch - {item['severity']!r} != {finding_item.severity.value!r}"
            )
        if _norm(item["finding_type"]) != finding_item.finding_type.value:
            violations.append(
                f"{key}: Finding_Type Mismatch - {item['finding_type']!r} != {finding_item.finding_type.value!r}"
            )

        #  3. recommended_action ∈ ALLOWED_ACTIONS
        if item["recommended_action"] not in ALLOWED_ACTIONS:
            violations.append(f"{key}: Allowed_Actions Mismatch - {item['recommended_action']!r} is not an allowed action.")

        #  4. grounding: every number in narrative exists in finding.evidence
        bad = _ungrounded_numbers(item["narrative"], finding_item.evidence)
        if bad:
            violations.append(f"{key}: ungrounded numbers in narrative: {bad}")

    # briefing must cover every engine finding
    seen = {
        (item.get("load_id"), _norm(item.get("finding_type")))
        for item in briefing.get("findings", [])
        if isinstance(item, dict)
    }
    for key in keys:
        if key not in seen:
            violations.append(f"{key}: engine finding missing from briefing")

    #  5. violation → reject with reason, retry ONCE; second → raise loudly

    if not violations:
        return briefing
    msg = "; ".join(violations)
    print(f"Contract rejection: {msg}")
    return None


if __name__ == "__main__":
    from watcher_agent import run_agent, TOOLS, TOOLS_IMPLS, wakeup
    from compliance_engine import scan, FindingType
    from capstone_data import LOADS, EVENTS, CARRIERS, NOW_TS

    show = "--show-context" in sys.argv
    run = run_agent(TOOLS, TOOLS_IMPLS, show, wakeup)
    findings = scan(LOADS, EVENTS, CARRIERS, NOW_TS)

    try:
        briefing = process_output(run["answer"])
    except (ValueError, json.JSONDecodeError) as e:
        raise SystemExit(f"failed to parse agent JSON: {e}") from e

    # First failure raises ContractViolation — wire a real agent retry later.
    enforced = enforce(briefing, findings, trace=None)
    print(json.dumps(enforced, indent=2))
