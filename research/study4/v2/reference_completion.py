"""Private, source-bound reference progress; never an executor observation or answer."""
from dataclasses import dataclass
from decimal import Decimal
import re
import unicodedata

from .contracts import fingerprint, require

VERSION = "study4-reference-completion-3"


class ReferenceUncertain(ValueError):
    """Stop before another paid decision when a release cannot be certified locally."""


# These are field roles, not task IDs or answer values. Their statements qualify
# another released fact; an applicable, affirmative answer need not quote the
# complete register entry.
QUALIFIERS = {
    "effective_date": "applicability of the explicitly requested current mapping",
    "maintenance": "rationale for the explicit backup window and retention",
    "asset_campaign": "creative scope already bound by the requested campaign",
    "license_valid_through": "validity of the explicitly current released asset",
    "quote_release": "version scope of the explicitly approved quote",
    "conflict": "rationale for an explicitly clear replacement date/window",
    "variance": "rationale when the complete resulting plan is released",
}
LABELS = {
    "required_retention_days": ("retention",),
    "certified_on_list": ("certified", "certification"),
    "framework_rate": ("rate", "per word"),
    "partner_rate": ("rate", "per night"),
    "partner_window": ("window", "date", "launch"),
    "extra_channels": ("channel", "blog", "newsletter"),
    "maximum_per_cohort": ("maximum", "cohort", "capacity"),
    "price_per_cohort_usd": ("price", "cost", "cohort"),
    "facilitators_per_cohort": ("facilitator",),
    "cached_benchmarks": ("cached", "cache"),
    "idle_seats": ("idle", "reassign"),
    "panel_credits": ("credit", "panel"),
    "alternative_date": ("date", "clear", "available"),
    "staff": ("staff", "people", "employees"),
}
NEGATIVE = re.compile(
    r"\b(?:cannot|can not|can't|unable|withheld|unconfirmed|unverified|"
    r"not (?:approved|authorized|confirmed|released)|do not have|don't have|"
    r"not yet|pending|hypothetical|guess|example only)\b", re.I)
ATTRIBUTED = re.compile(
    r"\b(?:you (?:said|provided|listed|reported)|your (?:draft|note|claim)|"
    r"from your note|according to your)\b", re.I)
REFUSAL = re.compile(
    r"\b(?:cannot|can't|unable|withhold|declin\w*|before i can|"
    r"please (?:provide|send|supply)|not (?:approved|authorized|confirmed))\b", re.I)


@dataclass(frozen=True)
class CompletionContract:
    node_id: str
    alternatives: tuple
    qualifiers: tuple
    source_sha256: str
    explanation: tuple


def contracts(case):
    bp = case.blueprint
    hidden = {h["id"]: h for h in bp["hidden_information"]}
    output = set(bp["output_contract"]["fields"])
    result = {}
    for node in bp["gold_dag"]["nodes"]:
        records = [hidden[h] for h in node["information_ids"]]
        facts = {k: v for h in records for k, v in h["facts"].items()}
        require(facts, "Reference node has no specified facts")
        descendants = {node["id"]}
        while True:
            expanded = descendants | {n["id"] for n in bp["gold_dag"]["nodes"]
                                      if set(n["requires"]) & descendants}
            if expanded == descendants:
                break
            descendants = expanded
        downstream_context = [c for n in bp["gold_dag"]["nodes"]
                              if n["id"] in descendants - {node["id"]}
                              for hid in n["information_ids"] for c in hidden[hid]["required_context"]]
        # A qualifier used by an output or a later authorization remains
        # obligatory; dropping register recitation must not drop prerequisites.
        qualifiers = tuple(k for k in facts if k in QUALIFIERS and k not in output
                           and facts[k] not in downstream_context)
        required = tuple(k for k in facts if k not in qualifiers)
        alternatives = [required]
        explanations = [(k, "requested output or released input/constraint") for k in required]
        explanations.extend((k, QUALIFIERS[k]) for k in qualifiers)
        # The specification asks for the rate, not for the NPC to do the
        # executor's arithmetic. A complete quote is also sufficient evidence.
        if "framework_rate" in facts and "total_usd" in facts:
            alternatives = [tuple(k for k in required if k != "total_usd"),
                            tuple(k for k in required if k != "framework_rate")]
            explanations.append(("framework_rate|total_usd",
                                 "released unit-rate input OR complete quoted total"))
        for rate, total in (("discount", "annual_usd"), ("discount", "monthly_usd")):
            if rate in facts and total in facts:
                alternatives = [tuple(k for k in a if k != total) for a in alternatives] + [
                    tuple(k for k in a if k != rate) for a in alternatives]
                explanations.append((rate + "|" + total,
                                     "released pricing input OR complete recurring quote"))
        require(all(a for a in alternatives), "Empty completion obligation")
        result[node["id"]] = CompletionContract(
            node["id"], tuple(dict.fromkeys(alternatives)), qualifiers,
            fingerprint({"node": node, "records": records, "output_contract": bp["output_contract"]}),
            tuple(explanations))
    return result


def normalize(text):
    return unicodedata.normalize("NFKC", text).replace("\u2019", "'").casefold()


def clauses(text):
    text = normalize(text).replace("**", "").replace("`", "")
    return [s.strip(" -*\t") for s in re.split(r"\n|(?<=[.!?;])\s+", text) if s.strip()]


def labels(key):
    words = [w for w in key.split("_") if w not in {
        "usd", "id", "ref", "reference", "required", "to", "on", "per", "the", "of"}]
    singulars = [w[:-1] for w in words if w.endswith("s") and len(w) > 3]
    return tuple(dict.fromkeys((key.replace("_", " "), *words, *singulars, *LABELS.get(key, ()))))


def contains(text, value, grader):
    text = normalize(text)
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)) or isinstance(value, str) and re.fullmatch(r"\d+", value):
        return any(Decimal(n.replace(",", "")) == Decimal(str(value)) for n in re.findall(
            r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?!\w|\.\d)", text))
    return all(grader._text_has(text, t) for t in (grader._tokens(value) or grader._words(value)))


def context_present(value, request, public_text, grader):
    if contains(request, value, grader):
        return True
    # A named month for an invoice whose public packet has one year is not a
    # different period merely because it was not written as YYYY-MM.
    match = re.fullmatch(r"(\d{4})-(\d{2})", str(value))
    if match:
        import calendar
        year, month = match.groups()
        years = set(re.findall(r"\b20\d{2}\b", public_text))
        return years == {year} and calendar.month_name[int(month)].casefold() in normalize(request)
    return False


def fact_status(key, value, text, grader, *, single_fact=False):
    """Affirmative field evidence only. Ambiguous speech acts require review."""
    parts = clauses(text)
    evidence, conflict, mentions, attributed_section = False, False, False, False
    grant_heading = False
    for part in parts:
        if ATTRIBUTED.search(part):
            attributed_section = True
        elif re.search(r"\b(?:i|we) (?:can )?(?:confirm|approve|authorize|grant)\b", part):
            attributed_section = False
        if (not NEGATIVE.search(part) and not attributed_section and
                not re.search(r"\b(once|unless|only when|would|if)\b", part) and
                re.search(r"\b(approval|authorization|mandate|sign.?off|attestation)\b", part) and
                re.search(r"\b(is|issued|approved|to use)\b|:\s*$", part)):
            grant_heading = True
        label_text = part.replace("_", " ")
        named = any(re.search(r"\b" + re.escape(label) + r"\b", label_text) for label in labels(key))
        prefix = re.match(r"^([a-z][a-z_ ]+)\s*[:=]", part)
        explicit_field = (prefix is not None and
                          prefix.group(1).strip().replace("_", " ") in
                          (key.replace("_", " "), *LABELS.get(key, ())))
        if isinstance(value, bool):
            explicit = re.search(re.escape(key) + r"\s*[:=]\s*(true|false)\b", part)
            if explicit:
                matched = (explicit.group(1) == "true") is value
            else:
                phrase = key.replace("_", " ")
                has_subject = all(re.search(r"\b" + re.escape(w) + r"\b", part)
                                  for w in phrase.split())
                matched = has_subject and (
                    (value and not re.search(r"\b(no|not|without|false)\b", part)) or
                    (not value and re.search(r"\b(no|not|without|false)\b", part)))
                if key == "contains_personal_data" and value is False:
                    matched = matched or bool(re.search(r"\bno personal data\b", part))
        else:
            matched = contains(part, value, grader)
        if matched:
            mentions = True
            if NEGATIVE.search(part) or attributed_section:
                continue
            if not isinstance(value, bool) and re.search(
                    r"\b(?:not|no|without|non[- ])\s*(?:\w+\s+){0,2}" +
                    re.escape(normalize(str(value))) + r"\b", part):
                continue
            number = isinstance(value, (int, float)) and not isinstance(value, bool)
            unique_identifier = isinstance(value, str) and bool(re.search(r"[a-zA-Z].*\d|\d.*[a-zA-Z]", value))
            if number and not named:
                continue
            if not (named or unique_identifier or single_fact or isinstance(value, list)):
                continue
            if any(word in key for word in ("authorization", "mandate", "signoff", "attestation")):
                denied_grant = any(NEGATIVE.search(p) and re.search(
                    r"\b(approv\w*|authoriz\w*|grant\w*|reference|sign.?off|attest\w*|mandate)\b", p)
                    for p in parts)
                if denied_grant:
                    continue
                if not (grant_heading or re.search(re.escape(key) + r"\s*[:=]", part) or re.search(
                        r"\b(approv\w*|authoriz\w*|issued?|grant\w*|sign.?off|"
                        r"attest\w*|mandate|reference)\b", part)):
                    continue
            evidence = True
        elif explicit_field and not NEGATIVE.search(part):
            # A different explicitly labelled scalar is not silently discarded
            # because an older reply contained the expected value.
            if isinstance(value, (int, float)) and re.search(r"\d", part):
                conflict = True
            elif isinstance(value, str) and re.search(r"[a-z][a-z0-9_.]*[-_]\w*\d", part):
                conflict = True
        elif key in QUALIFIERS and named and (
                NEGATIVE.search(part) or re.search(r"\b(expired|invalid|inapplicable)\b", part)):
            conflict = True
    if conflict:
        return "conflict"
    if evidence:
        return "affirmative"
    if mentions:
        return "unresolved"
    return "absent"


def progress(case, events, grader):
    specs = contracts(case)
    hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
    requests, request_released = {}, {}
    released, values, unresolved = set(), {}, {}
    proof = []
    public_text = case.public.instruction + "\n" + "\n".join(text for _, text in case.public.documents)
    for event in events:
        if event["kind"] == "send_message":
            require(event["message_id"] not in requests, "Duplicate reference request identity")
            requests[event["message_id"]] = event
            request_released[event["message_id"]] = set(released)
            continue
        if event["kind"] != "read_messages":
            continue
        request = requests.get(event.get("in_reply_to"))
        require(request is not None and request["person_id"] == event["person_id"],
                "Reference reply must bind an actual request to the same person")
        before = request_released[event["in_reply_to"]]
        for node in case.blueprint["gold_dag"]["nodes"]:
            nid = node["id"]
            if event["person_id"] not in node["admissible_recipients"] or not set(node["requires"]) <= before:
                continue
            records = [hidden[h] for h in node["information_ids"]]
            if not all(context_present(c, request["content"], public_text, grader)
                       for h in records for c in h["required_context"]):
                continue
            facts = {k: v for h in records for k, v in h["facts"].items()}
            states = values.setdefault(nid, {})
            required_keys = {k for a in specs[nid].alternatives for k in a}
            for context in (c for h in records for c in h["required_context"]):
                identifier = re.fullmatch(r"([A-Za-z][A-Za-z_-]*-)\d[\w.-]*", str(context))
                if identifier:
                    mentioned = re.findall(r"\b" + re.escape(identifier.group(1)) + r"\d[\w.-]*",
                                           event["content"], re.I)
                    if mentioned and not any(normalize(v.rstrip(".-")) == normalize(str(context))
                                             for v in mentioned):
                        unresolved.setdefault(nid, {})["scope"] = "reply explicitly identifies a different record"
            for key, value in facts.items():
                items = list(enumerate(value)) if isinstance(value, list) else [(None, value)]
                statuses = []
                for index, item in items:
                    status = fact_status(key, item, event["content"], grader,
                                         single_fact=isinstance(value, list) or
                                         (len(required_keys) == 1 and key in required_keys))
                    atom = key if index is None else f"{key}[{index}]"
                    if status == "affirmative":
                        states[atom] = event["message_id"]
                    statuses.append(status)
                if isinstance(value, list) and all(f"{key}[{i}]" in states for i in range(len(value))):
                    states[key] = event["message_id"]
                status = ("conflict" if "conflict" in statuses else
                          "unresolved" if "unresolved" in statuses else "absent")
                if status == "conflict":
                    unresolved.setdefault(nid, {})[key] = "conflicting authoritative field statement"
                elif status == "unresolved" and key in required_keys and not REFUSAL.search(
                        normalize(event["content"])):
                    unresolved.setdefault(nid, {})[key] = "value mentioned without affirmative field-bound release"
            blockers = unresolved.get(nid, {})
            valid = [a for a in specs[nid].alternatives if set(a) <= states.keys()
                     and not (set(a) | set(specs[nid].qualifiers) | {"scope"}) & blockers.keys()]
            if valid:
                # Qualifier conflicts remain visible even when literal recitation
                # of the qualifier was not a completion obligation.
                released.add(nid)
                proof.append({"node_id": nid, "reply_message_id": event["message_id"],
                              "request_message_id": request["message_id"],
                              "field_sources": dict(states),
                              "contract_sha256": specs[nid].source_sha256})
            elif blockers:
                released.discard(nid)
    return {"released": released, "proof": proof,
            "unresolved": {n: v for n, v in unresolved.items() if n not in released},
            "field_conflicts_or_ambiguity": unresolved,
            "contracts": specs}


def released(case, events, grader):
    result = progress(case, events, grader)
    if result["unresolved"]:
        raise ReferenceUncertain("Reference release needs source-bound offline review")
    return result["released"]
