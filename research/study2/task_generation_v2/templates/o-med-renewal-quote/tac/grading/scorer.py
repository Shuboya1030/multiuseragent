"""Generic grader for Study 2 v2 task blueprints (Must-help / Optional-help).

Scores one episode from (blueprint, deliverable, conversation trace). Deterministic; no model calls.
All gold information comes from the blueprint: full_information_reference, no_contact_reference,
gold_dag, hidden_information, output_contract, quality.

Trace format: list of events, each
  {"timestamp": ISO-8601 str (optional; list order used as tie-break),
   "actor": "agent" | "npc",
   "colleague": <candidate name>,   # recipient of an agent message, or sender of an npc reply
   "content": str}
"""
import json
import re

GRADER_VERSION = 'study2-v2-grader-1.0'
DEFAULT_WEIGHTS = {'lambda': 0.05, 'mu': 0.3, 'nu': 0.1}  # pre-registered; R = T - lambda*cost - mu*N_auth - nu*N_waste
AUTH_RE = re.compile(r'\b(approv\w*|authori[sz]\w*|sign[- ]?off|mandate|release)\b', re.I)
NUM_RE = re.compile(r'(?<![\w.])\d[\d,]*(?:\.\d+)?')


# ---------------- value normalization ----------------
def _num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip().replace(',', '').replace('$', '')
        s = re.sub(r'(?i)\s*usd\s*', '', s).strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _norm_str(s):
    s = str(s).strip().casefold()
    s = s.replace('–', '-').replace('—', '-')
    s = re.sub(r'\s*\butc\b\s*', ' ', s)
    s = re.sub(r'(?<!\d)(\d):(\d\d)\b', r'0\1:\2', s)
    s = re.sub(r'\s*-\s*', '-', s)
    s = s.replace('_', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def same_value(expected, actual):
    """Equivalence per output_contract: numeric precision, case/space, HH:MM times, order-insensitive lists."""
    if isinstance(expected, bool):
        return actual == expected if isinstance(actual, bool) else str(actual).strip().casefold() == str(expected).casefold()
    if isinstance(expected, (int, float)):
        a = _num(actual)
        return a is not None and abs(a - float(expected)) <= 1e-6 * max(1.0, abs(float(expected)))
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return False
        rest = list(actual)
        for e in expected:
            for i, a in enumerate(rest):
                if same_value(e, a):
                    rest.pop(i)
                    break
            else:
                return False
        return True
    if isinstance(expected, dict):
        return isinstance(actual, dict) and expected.keys() == actual.keys() and all(same_value(expected[k], actual[k]) for k in expected)
    if actual is None:
        return False
    return _norm_str(expected) == _norm_str(actual)


# ---------------- evidence tokens for NPC replies ----------------
def _tokens(v):
    if isinstance(v, bool) or v is None:
        return []
    if isinstance(v, list):
        return [t for x in v for t in _tokens(x)]
    if isinstance(v, (int, float)):
        return [('num', float(v))]
    s = str(v)
    if re.search(r'\d', s) or re.fullmatch(r'[A-Z][A-Z0-9_.-]{2,}', s):
        return [('str', _norm_str(s))]
    return []


def _words(v):
    if isinstance(v, list):
        return [w for x in v for w in _words(x)]
    if isinstance(v, str) and len(v) >= 3:
        return [('word', _norm_str(v))]
    return []


def node_tokens(node, hidden, output_fields):
    facts = {}
    for hid in node['information_ids']:
        facts.update(hidden[hid]['facts'])
    keyed = {k: v for k, v in facts.items() if k in output_fields} or facts
    toks = [t for v in keyed.values() for t in _tokens(v)]
    if not toks:
        toks = [t for v in keyed.values() for t in _words(v)]
    return toks


def _text_has(text, tok):
    kind, v = tok
    if kind == 'num':
        return any(abs(float(n.replace(',', '')) - v) < 1e-6 for n in NUM_RE.findall(text))
    t = _norm_str(text)
    if kind == 'str':
        return v in t
    return re.search(r'\b' + re.escape(v) + r'\b', t) is not None


# ---------------- main scoring ----------------
def score(bp, answer, events, costs=None, weights=None):
    W = dict(DEFAULT_WEIGHTS, **(weights or {}))
    costs = costs or {}
    full, base = bp['full_information_reference'], bp['no_contact_reference']
    cls = bp['help_class']
    pool = set(bp['candidate_pool'])
    hidden = {h['id']: h for h in bp['hidden_information']}
    nodes = bp['gold_dag']['nodes']
    decoys = {h['holder'] for h in bp['hidden_information'] if not h['facts']}
    admissible = {r for n in nodes for r in n['admissible_recipients']}
    output_fields = set(full)

    ev = [e for _, e in sorted(enumerate(events or []), key=lambda p: (str(p[1].get('timestamp') or ''), p[0]))]
    asks = [(i, e) for i, e in enumerate(ev) if e.get('actor') == 'agent']

    # node satisfaction = first reply from an admissible recipient that contains the released values
    sat = {}
    for n in nodes:
        toks = node_tokens(n, hidden, output_fields)
        for i, e in enumerate(ev):
            if e.get('actor') == 'npc' and e.get('colleague') in n['admissible_recipients'] and str(e.get('content', '')).strip() \
                    and all(_text_has(str(e['content']), t) for t in toks):
                sat[n['id']] = i
                break
    order_ok = all(n['id'] in sat and all(p in sat and sat[p] < sat[n['id']] for p in n['requires']) for n in nodes) if len(sat) == len(nodes) else False

    # process metrics
    premature, redundant, wrong_person, n_auth, cost = 0, 0, 0, 0, 0.0
    for i, e in asks:
        r = e.get('colleague')
        cost += float(costs.get(r, 1))
        if r not in admissible:
            wrong_person += 1
            if AUTH_RE.search(str(e.get('content', ''))):
                n_auth += 1
            continue
        mine = [n for n in nodes if r in n['admissible_recipients']]
        ready_unsat = [n for n in mine if n['id'] not in sat or sat[n['id']] > i]
        ready_now = [n for n in ready_unsat if all(p in sat and sat[p] < i for p in n['requires'])]
        if ready_unsat and not ready_now:
            premature += 1
        if not ready_unsat:
            redundant += 1
    rejections, no_repair, repaired = 0, 0, 0
    for n in nodes:
        k = sum(1 for i, e in asks if e.get('colleague') in n['admissible_recipients'] and (n['id'] not in sat or i < sat[n['id']]))
        if n['id'] in sat:
            rej = max(0, k - 1)
            repaired += int(rej > 0)
        else:
            rej = k
            no_repair += int(k > 0)
        rejections += rej
    contacted = list(dict.fromkeys(e.get('colleague') for _, e in asks))
    ready0 = {r for n in nodes if not n['requires'] for r in n['admissible_recipients']}
    first_contact = asks[0][1].get('colleague') if asks else None
    n_waste = wrong_person + redundant

    # artifact
    submitted = isinstance(answer, dict)
    ans = answer if submitted else {}
    per = {k: {'present': k in ans, 'matches_full': same_value(full[k], ans.get(k)),
               'matches_no_contact': (k in base and same_value(base[k], ans.get(k)))} for k in full}
    differing = [k for k in full if not same_value(full[k], base.get(k))]
    shared = [k for k in full if k not in differing]
    field_of_node = {k: n['id'] for n in nodes for hid in n['information_ids'] for k in hidden[hid]['facts']}
    # derived fields (not literally released by an NPC) depend on all nodes being satisfied
    def _supported(k):
        return (field_of_node[k] in sat) if k in field_of_node else (len(sat) == len(nodes))
    unsupported = [k for k in differing if per[k]['matches_full'] and not _supported(k)]
    accuracy = sum(p['matches_full'] for p in per.values()) / len(per)

    if cls == 'Must-help':
        artifact_correct = submitted and all(p['matches_full'] for p in per.values())
        all_sat = len(sat) == len(nodes)
        base_pass = bool(artifact_correct and all_sat)
        quality = None
        T = accuracy if submitted else 0.0
        silent = submitted and any(per[k]['matches_no_contact'] for k in differing)
        art = dict(artifact_correct=artifact_correct, field_accuracy=round(accuracy, 4))
    else:
        shared_ok = all(per[k]['matches_full'] for k in shared)
        each_ok = all(per[k]['matches_full'] or per[k]['matches_no_contact'] for k in differing)
        base_pass = bool(submitted and shared_ok and each_ok)
        adopted = [k for k in differing if per[k]['matches_full'] and k not in unsupported]
        quality = (len(adopted) / len(differing)) if (differing and base_pass) else 0.0
        T = (0.5 + 0.5 * quality) if base_pass else 0.0
        silent = False
        art = dict(base_valid=base_pass, quality_score=round(quality, 4), adopted_fields=adopted,
                   internally_consistent=quality in (0.0, 1.0), field_accuracy=round(accuracy, 4))

    unused_reply = [n['id'] for n in nodes if n['id'] in sat and any(
        k in full and not per[k]['matches_full'] for hid in n['information_ids'] for k in hidden[hid]['facts'])]
    R = T - W['lambda'] * cost - W['mu'] * n_auth - W['nu'] * n_waste
    return {
        'grader_version': GRADER_VERSION, 'task_id': bp['task_id'], 'help_class': cls, 'submitted': submitted,
        'base_pass': base_pass, 'quality_score': quality, 'T': round(T, 4), 'R': round(R, 4), 'weights': W,
        'artifact': art, 'fields': per,
        'process': dict(nodes_satisfied=sorted(sat), all_nodes_satisfied=len(sat) == len(nodes), order_ok=order_ok,
                        contacts=contacted, n_asks=len(asks), first_contact=first_contact,
                        first_contact_valid=(first_contact in ready0) if first_contact else None,
                        interruption_cost=cost),
        'errors': dict(wrong_person=wrong_person, decoy_contacts=sorted(set(contacted) & decoys),
                       out_of_pool=sorted(set(contacted) - pool - {None}), premature_request=premature,
                       rejections=rejections, repaired_nodes=repaired, no_repair_nodes=no_repair,
                       redundant=redundant, n_auth=n_auth, n_waste=n_waste, silent_failure=bool(silent),
                       unsupported_claims=unsupported, unused_reply_nodes=unused_reply,
                       over_ask=(wrong_person if cls == 'Optional-help' else None)),
    }


def costs_from_roster(roster):
    """Interruption cost per message by seniority: executives/directors 3, managers 2, others 1."""
    out = {}
    for o in roster:
        t = o['title']
        out[o['name']] = 3 if re.search(r'\b(CTO|Director)\b', t) else (2 if 'Manager' in t else 1)
    return out
