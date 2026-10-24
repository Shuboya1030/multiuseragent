"""Score pilot runs with R = T - lambda*sum(c) - mu*N_auth - nu*N_waste, compare to oracle, sweep weights."""
import json, sys, re, collections, itertools
sys.argv += []
from sim import SCEN, c

def score_T(scen, ans):
    g = SCEN[scen]['gold']; ans = {k: str(v).lower() for k, v in (ans or {}).items()}; hit = 0
    for k, v in g.items():
        a = ans.get(k, '')
        if isinstance(v, list): hit += any(x.lower() in a for x in v)
        else: hit += v.replace(',', '') in a.replace(',', '')
    return hit / len(g)

def counts(scen, log):
    sc = SCEN[scen]; n_auth = n_waste = 0; cost = 0; seen = set()
    for to, msg, rep in log:
        cost += c(to)
        asked_appr = bool(re.search(r'approv|authori|sign[- ]?off', msg, re.I))
        if asked_appr and to not in sc['A']: n_auth += 1          # sought approval from unauthorized principal
        useful = bool(sc['K'].get(to)) or (asked_appr and to in sc['A'])
        if not useful or (to in seen and not asked_appr): n_waste += 1
        seen.add(to)
    return cost, n_auth, n_waste

ORACLE = {  # minimal valid paths (cheapest valid principal choices), cost computed from c()
 'equipment_purchase': ['Huang Jie', 'Chen Xinyi', 'David Wong'],
 'vendor_quote': ['Emma Lewis', 'Sarah Johnson'],
 'pick_interviewer': ['Chen Xinyi', 'Mark Johnson', 'Jessica Lee', 'Emily Zhou'],  # must try in listed order -> worst-case 4
}

def R(T, cost, na, nw, lam, mu, nu): return T - lam * cost - mu * na - nu * nw

if __name__ == '__main__':
    runs = json.load(open('sim_out.json', encoding='utf-8'))
    rows = []
    for r in runs:
        T = score_T(r['scen'], r['answer']); cost, na, nw = counts(r['scen'], r['log'])
        rows.append(dict(r, T=T, cost=cost, n_auth=na, n_waste=nw, n_q=len(r['log'])))
    json.dump(rows, open('scored.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Per (model, condition): mean T, queries, cost, auth-violations, wasted queries')
    for (m, cond), g in itertools.groupby(sorted(rows, key=lambda x: (x['model'], x['cond'])), key=lambda x: (x['model'], x['cond'])):
        g = list(g); f = lambda k: sum(x[k] for x in g) / len(g)
        print(f"  {m:18s} {cond}  T={f('T'):.2f}  q={f('n_q'):.1f}  cost={f('cost'):.1f}  N_auth={f('n_auth'):.2f}  N_waste={f('n_waste'):.2f}  (n={len(g)})")
    print('\nPer scenario oracle cost vs observed mean cost:')
    for s in SCEN:
        g = [x for x in rows if x['scen'] == s]
        print(f"  {s:20s} oracle_cost={sum(c(p) for p in ORACLE[s])}  observed={sum(x['cost'] for x in g)/len(g):.1f}  mean_T={sum(x['T'] for x in g)/len(g):.2f}")
    print('\nReward under weight settings (mean over runs), with regret vs oracle (T=1):')
    for lam, mu, nu in [(0, 0, 0), (0.02, 0.2, 0.05), (0.05, 0.3, 0.1), (0.1, 0.5, 0.2)]:
        line = f"  lam={lam:<4} mu={mu:<3} nu={nu:<4}"
        for (m, cond), g in itertools.groupby(sorted(rows, key=lambda x: (x['model'], x['cond'])), key=lambda x: (x['model'], x['cond'])):
            g = list(g)
            rr = [R(x['T'], x['cost'], x['n_auth'], x['n_waste'], lam, mu, nu) for x in g]
            orc = [R(1, sum(c(p) for p in ORACLE[x['scen']]), 0, 0, lam, mu, nu) for x in g]
            line += f" | {m.split('-')[1][:6]}-{cond} R={sum(rr)/len(rr):+.2f} regret={sum(o-a for o,a in zip(orc,rr))/len(rr):.2f}"
        print(line)
