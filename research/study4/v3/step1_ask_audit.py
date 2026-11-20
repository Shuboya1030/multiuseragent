"""Step 1: offline audit of every ASK in the 81 Phase0 episodes (no API).

Heuristic labels per ASK (first match wins):
  wrong_person  - recipient is not an admissible recipient of any gold node
  stale_value   - question cites a value token found only in workspace docs, while an earlier reply
                  already supplied a different value token (reply superseded doc draft)
  repeat_refused- same person was asked before and refused, and the question adds no new value token
  refused       - reply is a refusal / asks for missing context (other cases)
  useful        - reply did not refuse
Usage: python step1_ask_audit.py
"""
import gzip, json, re, statistics as st, zipfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent / 'v2'
REC = [json.loads(l) for l in gzip.open(V2 / 'reports/REFERENCE_NPC6_DNS_STOP_20261115.public.jsonl.gz', 'rt', encoding='utf-8')]
SCORE = {r['slot']['episode_id']: r['score'] for r in json.load(open(V2 / 'reports/REFERENCE_NPC6_DNS_STOP_20261115.json', encoding='utf-8'))['analysis']['rows']}
TASKS = zipfile.ZipFile(HERE.parents[1] / 'study2/results/r1_2026_11_02/archives/tasks.zip')
TOK = re.compile(r'\b(?:[A-Z]{1,6}-[A-Z0-9-]*\d[A-Z0-9-]*|\d{1,2}:\d{2}|\d+(?:\.\d+)?%?)\b')
REFUSE = re.compile(r"\b(can.?t|cannot|unable|not able|won.?t|need (?:the|you|a|to)|before I can|please (?:provide|send|confirm)|don.?t (?:hold|have))\b", re.I)


def toks(s): return set(TOK.findall(s or ''))


def blueprint(tid): return json.loads(TASKS.read(f'tasks/{tid}/blueprint.json'))


rows, per_ep = [], []
for r in REC:
    tid, arm = r['slot']['task_id'], r['slot']['arm']
    bp = blueprint(tid)
    admissible = {p for n in bp['gold_dag']['nodes'] for p in n['admissible_recipients']}
    doc_tok = set().union(*(toks(v) for k, v in r['workspace'].items() if k.startswith('/workspace/docs/')))
    ev = r['events']; reply_tok, refused_by, lab_ep = set(), set(), Counter()
    for i, e in enumerate(ev):
        if e['actor'] != 'agent':
            continue
        q, p = e['content'], e['colleague']
        rep = next((x['content'] for x in ev[i + 1:] if x['actor'] == 'npc' and x.get('in_reply_to') == e['message_id']), '')
        qt = toks(q)
        if p not in admissible:
            lab = 'wrong_person'
        elif reply_tok and (qt & (doc_tok - reply_tok)) and (reply_tok - doc_tok):
            lab = 'stale_value'
        elif p in refused_by and not (qt & reply_tok - doc_tok):
            lab = 'repeat_refused'
        elif REFUSE.search(rep):
            lab = 'refused'
        else:
            lab = 'useful'
        if REFUSE.search(rep):
            refused_by.add(p)
        reply_tok |= toks(rep)
        lab_ep[lab] += 1
        rows.append({'task': tid, 'arm': arm, 'person': p, 'label': lab})
    o = SCORE[r['slot']['episode_id']]
    per_ep.append({'task': tid, 'arm': arm, 'T': o['T'], 'R': o['R'], 'asks': sum(lab_ep.values()),
                   'cost': r['contact_cost'], **lab_ep})

# paired 20 tasks
arms_by = defaultdict(set)
for e in per_ep: arms_by[e['task']].add(e['arm'])
full = {t for t, a in arms_by.items() if a >= set('ABCD')}
LABS = ['useful', 'refused', 'repeat_refused', 'stale_value', 'wrong_person']
out = ['# Step 1: ASK audit of 81 Phase0 episodes (offline, heuristic labels)', '',
       f'Paired tasks with all four arms: {len(full)}. Labels are regex/token heuristics (see script docstring), not human review.', '',
       '## ASK labels per arm (20 paired tasks; mean per episode)', '',
       '| Arm | T | R | ASKs | ' + ' | '.join(LABS) + ' |', '|---' * (4 + len(LABS)) + '|']
for a in 'ABCD':
    E = [e for e in per_ep if e['arm'] == a and e['task'] in full]
    out.append(f'| {a} | {st.mean(e["T"] for e in E):.3f} | {st.mean(e["R"] for e in E):.3f} | {st.mean(e["asks"] for e in E):.2f} | '
               + ' | '.join(f'{st.mean(e.get(l, 0) for e in E):.2f}' for l in LABS) + ' |')
tot = Counter(x['label'] for x in rows if x['task'] in full and x['arm'] in 'BD')
n = sum(tot.values())
out += ['', f'## B+D ASKs by label (n={n})', ''] + [f'- {l}: {tot[l]} ({tot[l]/n:.0%})' for l in LABS]
loops = Counter((x['task'], x['arm'], x['person']) for x in rows)
out += ['', '## Longest same-person loops', ''] + [f'- {k[0]} {k[1]} -> {k[2]}: {v} asks' for k, v in loops.most_common(8)]
(HERE / 'STEP1_ASK_AUDIT.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
json.dump(per_ep, open(HERE / 'step1_episodes.json', 'w'), indent=0)
print('\n'.join(out))
