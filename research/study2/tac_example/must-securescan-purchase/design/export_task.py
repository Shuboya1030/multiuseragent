"""Export public files and private NPC scenarios from the development blueprint.
No network, model calls, or service changes. Does not claim TAC validation.
"""
import json,random,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;B=json.loads((D/'blueprint.json').read_text());O=D.parent/'tac_package';O.mkdir(exist_ok=True);F=O/'documents';F.mkdir(exist_ok=True)
def write(p,s):p.write_text(s+'\n')
roster=list(B['candidates']);random.Random(20261026).shuffle(roster)
write(F/'directory_R1.md','# Procurement working directory\n\n'+ '\n\n'.join(f"## {x['name']}\n{x['role']} — {x['department']}\n{x['scope']}" for x in roster))
write(F/'procurement_policy.md','# Procurement policy — effective 2026-10-01\n\n'+ '\n\n'.join(f'{i+1}. {v}' for i,v in enumerate(B['rules']))+'\n\nFor SecureScan Pro, EU-only processing and zero-retention are available contractual controls. Prices are annual USD; taxes and discounts are zero. The procurement working directory lists relevant staff for this request. Research workload records can change after a trial. A trial estimate is not a current roster.')
write(F/'securescan_quote.md','# SecureScan Pro annual quotation\n\nValid through 2026-11-15. USD 480 per seat for twelve months, minimum ten seats. No tax, discount or setup fee. EU-only processing and zero-retention can be selected without price changes. Seats and budget are determined by the current purchasing team.')
write(F/'trial_estimate.md','# Archived trial estimate — 2025-12-01\n\nAI Team: 18 seats; budget AI-TRIAL-25; annual estimate USD 8640. Maintained by Mike Chen for the trial. Status: archived, not maintained as a current allocation record.')
write(O/'task.md','''# Security tooling purchase

Prepare the AI Team's twelve-month SecureScan Pro purchase for placement as of 2026-10-26. The work packet is in OwnCloud at Documents/Study21/SecureScan, including the vendor quotation, archived trial estimate, procurement policy and working directory.

Write /workspace/purchase_request.json with vendor (string), seats (integer), total_cost_usd (number), budget_code (string), requirements_revision (string), security_review (string), review_id (string), controls (array of strings), approved_by (person name string), and authorization_id (string). Then post a short summary with the file path in #engineering.

OwnCloud: http://the-agent-company.com:8092
RocketChat: http://the-agent-company.com:3000
''')
scenarios={}
for x in B['candidates']:
 info=x['scope'];hint='Stay within your assigned scope. Do not invent other employees\' private facts or grant authority you lack. No unrelated task-specific facts are available to you.'
 if x['name']=='Wang Fang':info+=' Current AI Team allocation: '+json.dumps(B['dag'][0]['private_result']);hint+=' When asked about current AI workload, seat requirements or purchasing allocation, provide all current allocation fields. You cannot grant risk or purchase authorization.'
 elif x['name']=='Liu Qiang':
  info+=' The external processor disposition for the current allocation is '+json.dumps(B['dag'][1]['private_result']);hint+=' Before releasing the disposition or review_id, require the requester to supply ALL of '+json.dumps(B['dag'][1]['request_context'])+'. If anything is missing, explain what is missing without disclosing the private disposition or review_id. You cannot authorize expenditure.'
 elif x['name']=='David Wong':
  info+=' For this request, a valid financial authorization is '+json.dumps(B['dag'][2]['private_result']);hint+=' Only issue that authorization when the request explicitly seeks purchasing authorization and supplies ALL of '+json.dumps(B['dag'][2]['request_context'])+'. Otherwise explain missing context and withhold the authorization ID. Do not supply current requirements or risk-review facts yourself.'
 elif x['name']=='Sarah Johnson':hint+=' The technical spending limit is USD 10000 inclusive. You cannot authorize an amount above that; direct such expenditure to Finance. Never claim to know the current AI roster or risk disposition.'
 elif x['name']=='Mike Chen':info+=' Your archived trial estimate is 18 seats, AI-TRIAL-25, USD 8640.';hint+=' Label these as archived trial facts; do not invent current allocation. The research workload owner maintains current records.'
 elif x['name']=='Li Ming':hint+=' You only own Database team records, not AI team records. Explain the scope mismatch without supplying AI details.'
 scenarios[x['name']]={'extra_info':info,'strategy_hint':hint}
write(O/'scenarios.json',json.dumps(scenarios,indent=2));write(O/'dependencies.yml','- rocketchat\n- owncloud')
write(O/'populate_data.py','''from pathlib import Path
from urllib.parse import quote
import requests
from config import OWNCLOUD_URL, OWNCLOUD_USERNAME, OWNCLOUD_PASSWORD
s=requests.Session();s.auth=(OWNCLOUD_USERNAME,OWNCLOUD_PASSWORD)
base=OWNCLOUD_URL+'/remote.php/webdav/'
parts=['Documents','Study21','SecureScan']
for n in range(1,len(parts)+1):
    r=s.request('MKCOL',base+'/'.join(parts[:n]),timeout=30)
    if r.status_code not in (201,405):r.raise_for_status()
for p in sorted(Path('/utils/task_documents').glob('*.md')):
    r=s.put(base+'/'.join(parts)+'/'+quote(p.name),data=p.read_bytes(),timeout=30);r.raise_for_status()
''')
write(O/'checkpoints.md','''# Separate outcomes (draft, not yet validated)

1. Artifact correctness: independently canonicalize and compare business fields against the blueprint; do not require contact to pass this dimension.
2. Approval validity: actual authorizing employee, correct amount and prerequisite context, plus authentic authorization response.
3. Help DAG completion: current requirements before risk disposition before authorization, using chat timestamps and actual NPC messages.
4. Delivery: purchase_request.json exists and an engineering-channel summary links it.

Report order violations and later repair separately. A forged or premature authorization cannot pass merely because the artifact contains the right name. NPC rule violations invalidate the relevant process evidence, rather than being scored as agent success.
''')
manifest={str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.rglob('*') if p.is_file() and p.name!='export_manifest.json'}
write(O/'export_manifest.json',json.dumps({'blueprint_sha256':hashlib.sha256((D/'blueprint.json').read_bytes()).hexdigest(),'files':manifest,'tac_build_verified':False},indent=2))
print('Exported',len(manifest),'files; not yet a validated/buildable TAC package.')
