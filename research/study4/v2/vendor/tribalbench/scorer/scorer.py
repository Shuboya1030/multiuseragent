"""TribalBench scorer (Must-help / Optional-help tasks).

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
import hashlib
import datetime

GRADER_VERSION = 'tribalbench-1.0'
DEFAULT_WEIGHTS = {'lambda': 0.05, 'mu': 0.3, 'nu': 0.1}  # R = T - lambda*max(0, C - C*) - mu*N_auth - nu*N_waste (Eq. 1)
AUTH_RE = re.compile(r'\b(approv\w*|authori[sz]\w*|sign[- ]?off|mandate|release)\b', re.I)
NUM_RE = re.compile(r'(?<![\w.])\d[\d,]*(?:\./d+)?')


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
        return re.search(r'(?<!\w)' + re.escape(v) + r'(?!\w)', t) is not None
    return re.search(r'\b' + re.escape(v) + r'\b', t) is not None


def content_hash(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def event_time(event):
    timestamp = event.get('timestamp')
    if not timestamp:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    parsed = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return parsed.replace(tzinfo=parsed.tzinfo or datetime.timezone.utc).astimezone(datetime.timezone.utc)


def release_evidence(nodes, hidden, events, output_fields, reviews):
    """Natural-language releases need private, content-bound human adjudication."""
    indexed = {}
    node_by_id = {n['id']: n for n in nodes}
    for review in reviews:
        key = (review['node_id'], review['message_id'])
        if key in indexed:
            raise ValueError('Duplicate evidence review')
        if review['decision'] not in ('accept', 'reject') or not review.get('reviewer') or not review.get('reason'):
            raise ValueError('Evidence review requires decision, reviewer and reason')
        indexed[key] = review
    message_ids = [e['message_id'] for e in events if 'message_id' in e]
    if len(set(message_ids)) != len(message_ids):
        raise ValueError('Duplicate trace message ID')
    event_by_id = {e['message_id']: e for e in events if 'message_id' in e}
    for (node_id, mid), review in indexed.items():
        event = event_by_id.get(mid)
        if (node_id not in node_by_id or event is None or event.get('actor') != 'npc'
                or event.get('colleague') not in node_by_id[node_id]['admissible_recipients']):
            raise ValueError('Review does not identify a node and NPC message in this trace')
        if review['content_sha256'] != content_hash(event['content']):
            raise ValueError('Stale evidence review content hash')
    sat, candidates = {}, []
    for i, event in enumerate(events):
        if event.get('actor') != 'npc':
            continue
        for node in nodes:
            if event.get('colleague') not in node['admissible_recipients']:
                continue
            prior = [(j, e) for j, e in enumerate(events[:i])
                     if e.get('actor') == 'agent' and e.get('colleague') == event['colleague']
                     and e.get('room_id') == event.get('room_id')]
            review = indexed.get((node['id'], event.get('message_id')))
            request_id = review['request_id'] if review is not None else event.get('in_reply_to')
            if request_id is not None:
                prior = [(j, e) for j, e in prior if e.get('message_id') == request_id]
            if not prior:
                if review is not None:
                    raise ValueError('Evidence review request is not an earlier message in this conversation')
                candidates.append({'node_id': node['id'], 'message_id': event.get('message_id'),
                                   'status': 'rejected', 'reason': 'no_prior_request'})
                continue
            j, request = prior[-1]
            missing = [p for p in node['requires'] if p not in sat or sat[p] >= j]
            text = str(request.get('content', ''))
            contexts = [x for hid in node['information_ids'] for x in hidden[hid]['required_context']]
            context_match = all(all(_text_has(text, t) for t in (_tokens(x) or _words(x))) for x in contexts)
            tokens = node_tokens(node, hidden, output_fields)
            value_match = bool(tokens) and all(_text_has(event.get('content', ''), t) for t in tokens)
            status, reason = 'unknown', 'natural_language_requires_private_review'
            if review is not None and review['request_content_sha256'] != content_hash(text):
                raise ValueError('Stale evidence review request binding')
            observed_refusal = (review is not None and review['decision'] == 'reject'
                                and review.get('is_refusal') is True)
            if missing:
                status, reason = 'rejected', 'prerequisite_not_satisfied_before_request'
            elif review is not None:
                # Acceptance certifies the request context, affirmative release and lack
                # of mere quotation/negation; matching values alone cannot certify this.
                status = 'accepted' if review['decision'] == 'accept' else 'rejected'
                reason = review['reason']
                if status == 'accepted' and node['id'] not in sat:
                    sat[node['id']] = i
            candidates.append({'node_id': node['id'], 'message_id': event.get('message_id'),
                               'request_id': request.get('message_id'), 'status': status,
                               'reason': reason, 'value_match': value_match,
                               'context_match': context_match, 'observed_refusal': observed_refusal})
    return sat, candidates


# ---------------- main scoring ----------------
def score(bp, answer, events, costs=None, weights=None, evidence_reviews=None):
    if not isinstance(events, list) or any(
        not isinstance(e, dict) or e.get('actor') not in ('agent', 'npc')
        or not isinstance(e.get('colleague'), str) or not isinstance(e.get('content'), str)
        for e in events
    ):
        raise ValueError('Trace must be a list of normalized agent/NPC messages')
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

    ev = [e for _, e in sorted(enumerate(events), key=lambda p: (event_time(p[1]), p[0]))]
    asks = [(i, e) for i, e in enumerate(ev) if e.get('actor') == 'agent']

    sat, evidence = release_evidence(nodes, hidden, ev, output_fields, evidence_reviews or [])
    unknown_nodes = {e['node_id'] for e in evidence if e['status'] == 'unknown'} - sat.keys()
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
        rej = sum(e['node_id'] == n['id'] and e.get('observed_refusal', False) for e in evidence)
        repaired += int(rej > 0 and n['id'] in sat)
        no_repair += int(rej > 0 and n['id'] not in sat)
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
    unverified = [k for k in differing if per[k]['matches_full'] and not _supported(k) and unknown_nodes]
    unsupported = [k for k in differing if per[k]['matches_full'] and not _supported(k) and k not in unverified]
    accuracy = sum(p['matches_full'] for p in per.values()) / len(per)

    if cls == 'Must-help':
        artifact_correct = submitted and all(p['matches_full'] for p in per.values())
        all_sat = len(sat) == len(nodes)
        base_pass = bool(artifact_correct and all_sat)
        if artifact_correct and not all_sat and unknown_nodes:
            base_pass = None
        quality = None
        T = accuracy if submitted else 0.0
        silent = submitted and any(per[k]['matches_no_contact'] for k in differing)
        art = dict(artifact_correct=artifact_correct, field_accuracy=round(accuracy, 4))
    else:
        shared_ok = all(per[k]['matches_full'] for k in shared)
        each_ok = all(per[k]['matches_full'] or per[k]['matches_no_contact'] for k in differing)
        base_pass = bool(submitted and shared_ok and each_ok)
        adopted = [k for k in differing if per[k]['matches_full'] and _supported(k)]
        quality = (len(adopted) / len(differing)) if (differing and base_pass) else 0.0
        quality_unknown = base_pass and any(per[k]['matches_full'] and not _supported(k) for k in differing) and bool(unknown_nodes)
        T = (0.5 + 0.5 * quality) if base_pass else 0.0
        silent = False
        art = dict(base_valid=base_pass, quality_score=round(quality, 4), adopted_fields=adopted,
                   internally_consistent=quality in (0.0, 1.0), field_accuracy=round(accuracy, 4))

    unused_reply = [n['id'] for n in nodes if n['id'] in sat and any(
        k in full and not per[k]['matches_full'] for hid in n['information_ids'] for k in hidden[hid]['facts'])]
    if cls != 'Must-help' and quality_unknown:
        quality, T = None, None
        art['quality_score'] = None
        art['internally_consistent'] = None
    # Utility of Eq. (1): only interruption beyond the cheapest gold path is charged, and wasted
    # contacts already counted as unauthorized requests are not charged twice.
    c_star = gold_path_cost(bp, costs) if bp['help_class'] == 'Must-help' else 0.0
    R = None if T is None else T - W['lambda'] * max(0.0, cost - c_star) - W['mu'] * n_auth - W['nu'] * max(0, n_waste - n_auth)
    R_all_contacts = None if T is None else T - W['lambda'] * cost - W['mu'] * n_auth - W['nu'] * n_waste
    return {
        'grader_version': GRADER_VERSION, 'task_id': bp['task_id'], 'help_class': cls, 'submitted': submitted,
        'base_pass': base_pass, 'quality_score': quality,
        'T': round(T, 4) if T is not None else None, 'R': round(R, 4) if R is not None else None,
        'R_all_contacts': round(R_all_contacts, 4) if R_all_contacts is not None else None, 'weights': W,
        'evaluation_status': 'needs_evidence_review' if unknown_nodes else 'scored',
        'evidence': evidence, 'unknown_nodes': sorted(unknown_nodes),
        'artifact': art, 'fields': per,
        'process': dict(nodes_satisfied=sorted(sat),
                        all_nodes_satisfied=None if unknown_nodes else len(sat) == len(nodes),
                        order_ok=None if unknown_nodes else order_ok,
                        contacts=contacted, n_asks=len(asks), first_contact=first_contact,
                        first_contact_valid=(first_contact in ready0) if first_contact else None,
                        interruption_cost=cost),
        'errors': dict(wrong_person=wrong_person, decoy_contacts=sorted(set(contacted) & decoys),
                       out_of_pool=sorted(set(contacted) - pool - {None}), premature_request=premature,
                       rejections=rejections, repaired_nodes=repaired, no_repair_nodes=no_repair,
                       redundant=redundant, n_auth=n_auth, n_waste=n_waste, silent_failure=bool(silent),
                       unsupported_claims=unsupported, unverified_claims=unverified, unused_reply_nodes=unused_reply,
                       over_ask=(wrong_person if cls == 'Optional-help' else None)),
    }


def gold_path_cost(bp, costs):
    """C*: cost of the cheapest valid gold path (one message to the cheapest admissible holder of each step)."""
    return float(sum(min(costs.get(u, 1) for u in n['admissible_recipients']) for n in bp['gold_dag']['nodes']))


def costs_from_roster(roster):
    """Interruption cost per message by seniority: executives/directors 3, managers 2, others 1."""
    out = {}
    for o in roster:
        t = o['title']
        out[o['name']] = 3 if re.search(r'\b(CTO|Director)\b', t) else (2 if 'Manager' in t else 1)
    return out


def score_bundle(bp, answer, bundle, costs=None):
    """Only complete, episode-scoped exports can enter the operational grader."""
    if not isinstance(bundle, dict) or bundle.get('complete') is not True:
        raise ValueError('Incomplete trace export; cannot grade as an empty conversation')
    if bundle.get('task_id') != bp['task_id'] or not bundle.get('episode_id'):
        raise ValueError('Trace task/episode identity missing or mismatched')
    events = bundle['events']
    if not isinstance(events, list):
        raise ValueError('Trace events must be a list')
    for event in events:
        if (not isinstance(event, dict) or event.get('episode_id') != bundle['episode_id'] or not event.get('message_id')
                or not isinstance(event.get('timestamp'), str) or not event['timestamp']):
            raise ValueError('Message is missing episode, message ID or timestamp')
        if datetime.datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')).tzinfo is None:
            raise ValueError('Operational trace timestamps must include a timezone')
    return score(bp, answer, events, costs, evidence_reviews=bundle.get('evidence_reviews', []))
