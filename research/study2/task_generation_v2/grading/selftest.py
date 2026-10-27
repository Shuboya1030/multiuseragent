"""Self-test the generic grader on all 60 blueprints using synthetic reference traces.

Cases per task:
  no_contact      : no messages, submit no_contact_reference
  full_gold       : gold-order asks with context, NPC replies with released facts, submit full_information_reference
  full_no_trace   : submit full answer but no conversation (unsupported claims)
Must-help only:
  wrong_order     : ask the last DAG node first (rejected), then gold order -> still passes, premature>=1, repaired>=1
  skip_last_node  : satisfy all nodes except the last; submit full answer -> fails (not all nodes satisfied)
  decoy_detour    : ask a decoy/non-holder first, then gold -> passes, wrong_person>=1
Optional-help only:
  partial_adopt   : adopt only some improved fields -> base invalid if inconsistent, else partial quality
Run from research/study2/task_generation_v2 with PYTHONUTF8=1.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scorer import score, costs_from_roster

R = pathlib.Path(__file__).resolve().parents[1]
ROSTER = json.loads((R / 'organization/roster.json').read_text(encoding='utf-8'))
COSTS = costs_from_roster(ROSTER)


def fmt(v):
    if isinstance(v, list): return ', '.join(fmt(x) for x in v)
    if isinstance(v, bool): return 'yes' if v else 'no'
    return str(v)


def reply_text(bp, node):
    facts = {}
    for hid in node['information_ids']:
        facts.update(next(h for h in bp['hidden_information'] if h['id'] == hid)['facts'])
    return 'Here you go: ' + '; '.join(f'{k} = {fmt(v)}' for k, v in facts.items()) + '.'


def gold_trace(bp, order=None, skip=()):
    nodes = {n['id']: n for n in bp['gold_dag']['nodes']}
    ev, t = [], 0
    for nid in (order or [n['id'] for n in bp['gold_dag']['nodes']]):
        n = nodes[nid]; who = n['admissible_recipients'][0]
        ctx = next(h for h in bp['hidden_information'] if h['id'] == n['information_ids'][0])['required_context']
        ev.append({'timestamp': f'2026-11-05T10:{t:02d}:00', 'actor': 'agent', 'colleague': who, 'content': 'Request regarding ' + ', '.join(map(str, ctx)) + '.'}); t += 1
        if nid in skip: continue
        ev.append({'timestamp': f'2026-11-05T10:{t:02d}:00', 'actor': 'npc', 'colleague': who, 'content': reply_text(bp, n)}); t += 1
    return ev


def run():
    results, fails = [], []
    for d in sorted((R / 'templates').iterdir()):
        bp = json.loads((d / 'blueprint.json').read_text(encoding='utf-8'))
        tid, cls = bp['task_id'], bp['help_class']
        full, base = bp['full_information_reference'], bp['no_contact_reference']
        nodes = bp['gold_dag']['nodes']
        cases = {}
        cases['no_contact'] = score(bp, base, [], COSTS)
        cases['full_gold'] = score(bp, full, gold_trace(bp), COSTS)
        cases['full_no_trace'] = score(bp, full, [], COSTS)
        exp = {}
        if cls == 'Must-help':
            exp['no_contact'] = lambda r: (not r['base_pass']) and r['errors']['silent_failure']
            exp['full_gold'] = lambda r: r['base_pass'] and r['process']['order_ok'] and r['errors']['n_waste'] == 0
            exp['full_no_trace'] = lambda r: (not r['base_pass']) and len(r['errors']['unsupported_claims']) > 0
            if len(nodes) > 1 and nodes[-1]['requires']:
                last = nodes[-1]['id']
                tr = gold_trace(bp, order=[last], skip={last}) + [dict(e, timestamp='2026-11-05T11' + e['timestamp'][13:]) for e in gold_trace(bp)]
                cases['wrong_order'] = score(bp, full, tr, COSTS)
                exp['wrong_order'] = lambda r: r['base_pass'] and (r['errors']['premature_request'] >= 1 or r['errors']['rejections'] >= 1) and r['errors']['repaired_nodes'] >= 1
            cases['skip_last_node'] = score(bp, full, gold_trace(bp, skip={nodes[-1]['id']}), COSTS)
            exp['skip_last_node'] = lambda r: not r['base_pass']
            others = [n for n in bp['candidate_pool'] if n not in {x for nd in nodes for x in nd['admissible_recipients']}]
            detour = [{'timestamp': '2026-11-05T09:00:00', 'actor': 'agent', 'colleague': others[0], 'content': 'Can you approve this?'},
                      {'timestamp': '2026-11-05T09:01:00', 'actor': 'npc', 'colleague': others[0], 'content': 'Not my area.'}]
            cases['decoy_detour'] = score(bp, full, detour + gold_trace(bp), COSTS)
            exp['decoy_detour'] = lambda r: r['base_pass'] and r['errors']['wrong_person'] >= 1 and r['errors']['n_auth'] >= 1
        else:
            exp['no_contact'] = lambda r: r['base_pass'] and r['quality_score'] == 0.0
            exp['full_gold'] = lambda r: r['base_pass'] and r['quality_score'] == 1.0 and r['T'] > cases['no_contact']['T']
            exp['full_no_trace'] = lambda r: r['base_pass'] and r['quality_score'] < 1.0 and len(r['errors']['unsupported_claims']) > 0
            diff = [k for k in full if full[k] != base.get(k)]
            if len(diff) >= 2:
                mixed = dict(base); mixed[diff[0]] = full[diff[0]]
                cases['partial_adopt'] = score(bp, mixed, gold_trace(bp), COSTS)
                exp['partial_adopt'] = lambda r: r['base_pass'] and 0 < r['quality_score'] < 1 and not r['artifact']['internally_consistent']
        row = {'task_id': tid, 'class': cls}
        for name, r in cases.items():
            ok = exp[name](r)
            row[name] = 'PASS' if ok else 'FAIL'
            row[name + '_T'] = r['T']; row[name + '_R'] = r['R']
            if not ok: fails.append((tid, name, {k: r[k] for k in ('base_pass', 'quality_score', 'T')}, r['errors'], r['process']['nodes_satisfied']))
        results.append(row)
    out = R / 'grading' / 'selftest_results.json'
    out.write_text(json.dumps({'grader_cases': results, 'failures': [list(map(str, f)) for f in fails]}, indent=2), encoding='utf-8')
    n_cases = sum(1 for r in results for k, v in r.items() if v in ('PASS', 'FAIL'))
    print(f'{len(results)} tasks, {n_cases} cases, {len(fails)} failures')
    for f in fails[:15]: print('FAIL', f)
    return len(fails)


if __name__ == '__main__':
    sys.exit(1 if run() else 0)
