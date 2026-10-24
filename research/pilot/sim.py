"""Pilot: role-aware help-seeking in a multi-user text simulator built from TheAgentCompany roles/scenarios.
Colleague replies are rule-based (scenario-constrained) -> deterministic evaluation.
"""
import json, os, re, sys, time, urllib.request, itertools, random

BASE = os.environ['ANTHROPIC_BASE_URL'].rstrip('/'); TOK = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
NPC = {f"{x['first_name']} {x['last_name']}": x for x in json.load(open('tac/npc_definition.json', encoding='utf-8'))}

# ---- scenarios: grounded in TAC tasks; knowledge K, authority A, cost c ----
COST = {'Sarah Johnson': 5, 'David Wong': 3, 'Chen Xinyi': 2, 'Mark Johnson': 3}  # seniority-based; others 1
def c(n): return COST.get(n, 1)

SCEN = {
 'equipment_purchase': dict(  # from admin-check-employees-budget-and-reply-2, extended with approval
  task="Huang Jie needs new equipment. Find out exactly what Huang Jie needs, find Huang Jie's remaining budget, "
       "and obtain approval for the purchase from someone who is authorized to approve departmental purchases. "
       "Submit JSON {\"item\":..., \"remaining_budget\":..., \"approved_by\":...}.",
  people=['Huang Jie', 'Chen Xinyi', 'David Wong', 'Sarah Johnson', 'Li Ming', 'Mark Johnson'],
  K={'Huang Jie': {'item': 'one Meeting Table'},
     'Chen Xinyi': {'remaining_budget': '$1,400'},
     'Li Ming': {}},
  A={'David Wong': 'purchase', 'Sarah Johnson': 'purchase'},
  gold={'item': 'meeting table', 'remaining_budget': '1,400', 'approved_by': ['David Wong', 'Sarah Johnson']},
  struct={'Huang Jie': 'knows: own equipment needs; can approve: nothing',
          'Chen Xinyi': 'knows: employee budgets and expenses; can approve: nothing',
          'David Wong': 'knows: company finances; can approve: departmental purchases',
          'Sarah Johnson': 'knows: technical strategy; can approve: departmental purchases (executive)',
          'Li Ming': 'knows: database project status; can approve: nothing',
          'Mark Johnson': 'knows: sales pipeline; can approve: nothing'}),
 'vendor_quote': dict(  # from admin-get-best-vendor-quote
  task="We need to order a new server. Find out where the vendor quotes are stored and what the server requirements are. "
       "Submit JSON {\"quotes_location\":..., \"min_cpu_cores\":..., \"min_ram_gb\":...}.",
  people=['Emma Lewis', 'Sarah Johnson', 'Mike Chen', 'Alex Turner', 'David Wong'],
  K={'Emma Lewis': {'quotes_location': 'Documents/Administrative Specialist'},
     'Sarah Johnson': {'min_cpu_cores': '28', 'min_ram_gb': '512'},
     'Mike Chen': {'min_cpu_cores': '16 (I think, not sure)'}},  # partial / wrong info distractor
  A={},
  gold={'quotes_location': 'administrative specialist', 'min_cpu_cores': '28', 'min_ram_gb': '512'},
  struct={'Emma Lewis': 'knows: collected vendor quotes and where they are stored; can approve: nothing',
          'Sarah Johnson': 'knows: official technical requirements for infrastructure (owner); can approve: technical purchases',
          'Mike Chen': 'knows: AI team workloads (informal opinions on hardware); can approve: nothing',
          'Alex Turner': 'knows: low-code platform; can approve: nothing',
          'David Wong': 'knows: company finances; can approve: purchases'}),
 'pick_interviewer': dict(  # from hr-pick-interviewer-2
  task="Pick an interviewer for a candidate. Find out who is eligible to interview, then find one who agrees. "
       "Submit JSON {\"interviewer\":...}.",
  people=['Chen Xinyi', 'Mark Johnson', 'Jessica Lee', 'Emily Zhou', 'David Wong', 'Sarah Johnson'],
  K={'Chen Xinyi': {'eligible': 'Mark Johnson, Jessica Lee, Emily Zhou, David Wong'},
     'Mark Johnson': {'availability': 'No, too busy on my project.'},
     'Jessica Lee': {'availability': "No, my stack doesn't match the candidate."},
     'Emily Zhou': {'availability': 'Yes, I will interview.'},
     'David Wong': {'availability': 'No, I am traveling.'}},
  A={},
  gold={'interviewer': 'emily zhou'},
  struct={'Chen Xinyi': 'knows: hiring process and list of eligible interviewers; can approve: nothing',
          'Mark Johnson': 'knows: sales; may interview', 'Jessica Lee': 'knows: marketing; may interview',
          'Emily Zhou': 'knows: web crawler engineering; may interview', 'David Wong': 'knows: finance; may interview',
          'Sarah Johnson': 'knows: technical strategy; can approve: hiring decisions (executive)'}),
}

def profile(name, cond):
    if cond == 'R0': return f"- {name}"
    if cond == 'R1': return f"- {name}: {NPC[name]['occupation']}. {NPC[name].get('public_info','')}"
    return f"- {name}: {SCEN_CUR['struct'][name]}; interruption cost: {c(name)}"

def npc_reply(name, msg, sc):
    k = sc['K'].get(name, {}); out = []
    if re.search(r'approv|authori|sign[- ]?off', msg, re.I):
        out.append('Approved.' if name in sc['A'] else "Sorry, I'm not authorized to approve that.")
    if k: out += [f"{key}: {v}" for key, v in k.items()]
    if not out: out.append("Sorry, I don't have that information.")
    return ' '.join(out)

def llm(model, system, msgs):
    body = json.dumps({'model': model, 'max_tokens': 400, 'system': system, 'messages': msgs}).encode()
    req = urllib.request.Request(BASE + '/v1/messages', data=body, headers={'content-type': 'application/json',
          'anthropic-version': '2023-06-01', 'authorization': 'Bearer ' + TOK, 'x-api-key': TOK})
    for i in range(4):
        try: return json.load(urllib.request.urlopen(req, timeout=120))['content'][0]['text']
        except Exception as e: time.sleep(3 * (i + 1)); err = e
    raise err

def run(model, sname, cond, cost_note, max_turns=10):
    global SCEN_CUR; sc = SCEN[sname]; SCEN_CUR = sc
    people = sc['people'][:]; random.shuffle(people)
    sysmsg = ("You are an AI agent working for a software company. You can message colleagues. "
              "Each turn, reply with ONLY one JSON object: {\"action\":\"ask\",\"to\":<exact colleague name>,\"message\":<text>} "
              "or {\"action\":\"submit\",\"answer\":{...}}. Do not invent information you have not been told.\n"
              "Colleagues:\n" + '\n'.join(profile(p, cond) for p in people) +
              ("\nInterrupting colleagues has a cost; senior colleagues are more costly. Avoid unnecessary messages." if cost_note else ''))
    msgs = [{'role': 'user', 'content': 'Task: ' + sc['task']}]; log = []; answer = None
    for _ in range(max_turns):
        out = llm(model, sysmsg, msgs); msgs.append({'role': 'assistant', 'content': out})
        m = re.search(r'\{.*\}', out, re.S)
        try: a = json.loads(m.group(0))
        except Exception: msgs.append({'role': 'user', 'content': 'Invalid. Reply with one JSON object.'}); continue
        if a.get('action') == 'submit': answer = a.get('answer', {}); break
        to = a.get('to', '');
        if to not in sc['people']: msgs.append({'role': 'user', 'content': f'No colleague named {to}.'}); continue
        rep = npc_reply(to, a.get('message', ''), sc); log.append((to, a.get('message', ''), rep))
        msgs.append({'role': 'user', 'content': f'{to} replied: {rep}'})
    return dict(model=model, scen=sname, cond=cond, cost_note=cost_note, log=log, answer=answer)

if __name__ == '__main__':
    random.seed(0); out = []
    models = ['claude-haiku-5-5', 'claude-sonnet-5-5']
    for model, sname, cond, rep in itertools.product(models, SCEN, ['R0', 'R1', 'R2'], range(2)):
        r = run(model, sname, cond, cost_note=(cond == 'R2')); r['rep'] = rep; out.append(r)
        print(model, sname, cond, rep, [x[0] for x in r['log']], r['answer'], flush=True)
    json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
