"""Steps 2-4: shared fact-ledger executor prompt (A2), capped router (B2), capped router + public what (D2).

Re-runs the 20 tasks that were complete in all four Phase0 arms, with the same frozen tasks, NPC scenarios,
scorer, model (gpt-5.4-mini-2026-03-17) and episode loop as research/study4/v2/phase0.py. Only two things change:
  1. AGENT_PROMPT gains explicit fact-ledger rules (all arms).
  2. B2/D2 router: at most MAX_ASKS_PER_NODE asks per gold node; after that the node is skipped and
     the executor acts alone (no forced re-asking).
Own lightweight caller (not the v2 durable admission); hard USD cap; per-episode JSONL; resumable.
Usage (from repo root): python -m research.study4.v3.step4_run [--limit N] [--cap USD]
"""
import argparse, json, os, time, urllib.request, urllib.error
from decimal import Decimal
from pathlib import Path

from research.study4.v2 import phase0 as P
from research.study4.v2.phase0_admission import decode_response

HERE = Path(__file__).resolve().parent
OUT = HERE / 'step4_episodes.jsonl'
MAX_ASKS_PER_NODE = 2
FACT_RULES = (
    " Fact ledger rules: (1) Before every action, list to yourself the values colleagues have actually "
    "confirmed in replies; a confirmed reply value supersedes any draft, default or older value in workspace "
    "documents. (2) Before asking, include every confirmed value and reference the recipient may need, and "
    "check the recipient's stated prerequisites are met. (3) After a refusal, fix exactly what was named as "
    "missing or wrong before asking again; never resend the same request. (4) Before writing the deliverable, "
    "check every field against confirmed replies, not document drafts.")
P.AGENT_PROMPT = P.AGENT_PROMPT + FACT_RULES
PRICE_IN, PRICE_OUT = Decimal('0.75'), Decimal('4.50')


class Spend:
    def __init__(self, cap):
        self.usd, self.cap, self.calls = Decimal(0), Decimal(str(cap)), 0


class Mini(P.Phase0Mini):
    def __init__(self, slot, spend):
        super().__init__(None, None, slot, None)
        self.spend = spend

    def call(self, mode, observation=None, person=None):
        if self.spend.usd >= self.spend.cap:
            raise RuntimeError('USD cap reached')
        op = 'npc' if mode == 'npc' else ('question' if mode == 'question' else 'ordinary')
        req = P.build_request(mode, observation, person=None if mode == 'npc' else person,
                              history=self.history if mode != 'npc' else None,
                              dialogue=self.dialogues[person] if mode == 'npc' else None)
        raw = post(req)
        ctx = None if mode == 'npc' else {'mode': mode, 'person_id': person}
        res = decode_response(raw, op, observation, ctx, None, 10 ** 9)
        u = res['usage']
        self.spend.usd += (u['input_tokens'] * PRICE_IN + u['output_tokens'] * PRICE_OUT) / 1_000_000
        self.spend.calls += 1
        self.indices[op] += 1
        return {'replayed_without_send': False, **res}


def post(req):
    body = json.dumps(req).encode()
    for attempt in range(5):
        r = urllib.request.Request('https://api.openai.com/v1/responses', body, {
            'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(r, timeout=180) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f'HTTP {e.code}: {e.read()[:300]!r}')
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(10 * (attempt + 1))
    raise RuntimeError('API failed after retries')


def capped_router(case, runtime, asked):
    released = P.reference_released(case, runtime.history)
    for n in case.blueprint['gold_dag']['nodes']:
        if n['id'] in released or not set(n['requires']) <= released or asked.get(n['id'], 0) >= MAX_ASKS_PER_NODE:
            continue
        c = n['admissible_recipients']
        return n['id'], min(c, key=lambda p: (case.costs[p], c.index(p)))
    return None


def episode(case, slot, mini):
    rt = P.Phase0Runtime(case, slot['episode_id'])
    routed, asked = slot['arm'] in {'B2', 'D2'}, {}
    while not rt.terminal:
        route = capped_router(case, rt, asked) if routed else None
        person = route[1] if route else None
        mode = 'question' if person else ('ordinary' if routed else 'native')
        res = mini.call(mode, rt.observe(), person)
        if res['data']['tool'] == 'ask_colleague':
            if route:
                asked[route[0]] = asked.get(route[0], 0) + 1
            rt._event('control_decision', action='ASK', person_id=res['data']['arguments']['person_id'])
            mini.ask(case, rt, res, supplement=slot['arm'] == 'D2')
            mini.ordinary(rt, mini.call('ordinary', rt.observe()))
        else:
            rt._event('control_decision', action='SELF', person_id=None)
            mini.ordinary(rt, res)
    rec = {'slot': slot, 'complete': True, 'workspace': rt.workspace, 'events': P.export_events(rt),
           'progress': rt.progress(), 'model_calls': mini.indices, 'normal_actions': rt.normal_actions,
           'contacts': rt.contacts, 'contact_cost': rt.cost, 'answer': rt.answer, 'asks_per_node': asked}
    rec['official_raw'] = P.score_record(case, rec)
    return rec


def paired_tasks():
    rows = json.load(open(HERE.parent / 'v2/reports/REFERENCE_NPC6_DNS_STOP_20261115.json', encoding='utf-8'))['analysis']['rows']
    arms = {}
    for r in rows:
        arms.setdefault(r['slot']['task_id'], set()).add(r['slot']['arm'])
    return sorted(t for t, a in arms.items() if a >= set('ABCD'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--cap', type=float, default=25.0)
    a = ap.parse_args()
    done = {json.loads(l)['slot']['episode_id'] for l in OUT.open(encoding='utf-8')} if OUT.exists() else set()
    spend = Spend(a.cap)
    slots = [{'task_id': t, 'arm': arm, 'episode_id': f'step4:{t}:{arm}'}
             for t in paired_tasks() for arm in ('A2', 'B2', 'D2')]
    for s in slots[:a.limit]:
        if s['episode_id'] in done:
            continue
        t0 = time.time()
        try:
            rec = episode(P.load_case(s['task_id']), s, Mini(s, spend))
        except Exception as e:
            print(json.dumps({'episode': s['episode_id'], 'error': repr(e)[:300], 'usd': str(spend.usd)}), flush=True)
            if 'USD cap' in repr(e):
                break
            continue
        rec['usd_running_total'] = str(spend.usd)
        with OUT.open('a', encoding='utf-8') as f:
            f.write(json.dumps(rec) + '\n')
        o = rec['official_raw']
        print(json.dumps({'episode': s['episode_id'], 'T': o['T'], 'R': o['R'], 'asks': rec['contacts'],
                          'secs': round(time.time() - t0), 'usd': f'{spend.usd:.3f}'}), flush=True)


if __name__ == '__main__':
    main()
