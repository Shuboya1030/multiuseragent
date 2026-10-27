"""Read saved evidence; posthoc format diagnosis never overwrites frozen scores."""
import json,hashlib,copy
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'runs/tac_haiku_20261026_01'
def load(n):return json.loads((R/n).read_text())
def lines(n):return [json.loads(x) for x in (R/n).read_text().splitlines()]
tr=lines('trace.jsonl');agent=lines('api_io.jsonl');npc=lines('npc_api_io.jsonl');answer=load('answer.json');hist=load('chat_history.json');status=load('status.json')
manifest=load('input_manifest.json');assert all(hashlib.sha256((P/f).read_bytes()).hexdigest()==v for f,v in manifest['files'].items()),'Frozen input changed'
assert len(agent)==14 and len(npc)==3 and status['status']=='finished'
assert not any(e['is_error'] for e in tr)
asks=[x for x in tr if x['tool']=='send_message'];reads=[x for x in tr if x['tool']=='read_messages'];owners=['Wang Fang','Liu Qiang','David Wong'];assert [a['input']['person'] for a in asks]==owners
assert all(reads[i]['turn']<asks[i+1]['turn'] for i in range(2));assert reads[-1]['turn']<next(x['turn'] for x in tr if x['tool']=='write_purchase_request')
for read in reads:
 who=read['input']['person']
 for reply in read['result']:
  assert any(m['_id']==reply['id'] and m['msg']==reply['text'] and m['u']['username']==reply['sender'] for m in hist[who])
assert not any(b.get('type') in ['thinking','redacted_thinking'] for a in agent for b in a['response']['content'])
expected={'vendor':'SecureScan Pro','seats':24,'total_cost_usd':11520,'budget_code':'AI-OPS-26','requirements_revision':'AI-Q4-07','security_review':'conditional-pass','review_id':'SR-2648','controls':['EU-only','zero-retention'],'approved_by':'David Wong','authorization_id':'PO-26-1048'}
canonical=copy.deepcopy(answer);canonical['controls']=[{'EU-only processing':'EU-only'}.get(x,x) for x in canonical['controls']]
diagnosis={'frozen_artifact_checkpoint':load('tac_evaluation.json')['checkpoints'][0]['result'],'difference':{'field':'controls','actual':answer['controls'],'expected':expected['controls']},'posthoc_equivalence_rule':'EU-only processing -> EU-only (only this explicit synonym)','posthoc_canonical_match':canonical==expected,'original_scores_modified':False,'interpretation':'Business content matches after this explicit synonym normalization; not a pre-run scoring rule.'}
(R/'format_diagnosis.json').write_text(json.dumps(diagnosis,indent=2)+'\n')
summary={'input_hashes_verified':len(manifest['files']),'agent_calls':len(agent),'npc_calls':len(npc),'agent_known_input_tokens':sum(a['response']['usage']['input_tokens'] for a in agent),'agent_known_output_tokens':sum(a['response']['usage']['output_tokens'] for a in agent),'npc_known_input_tokens':sum(a['usage']['input_tokens'] for a in npc),'npc_known_output_tokens':sum(a['usage']['output_tokens'] for a in npc),'estimated_cost_usd':sum(a['estimated_cost_usd'] for a in agent+npc),'elapsed_seconds_agent':status['elapsed_s'],'cost_is_invoice':False,'read_before_next_dependency_verified':True,'reply_ids_match_real_server_history':True,'outside_directory_contacts':0,'retries_by_examinee':0,'raw_tac_score':load('tac_evaluation.json')['final_score'],'posthoc_format_diagnosis':diagnosis,'NPC_compliance_scope':'Only three successful-path exchanges observed; rejection/repair behavior remains untested.','not_OpenHands_browser_baseline':True,'formal_R1_ready':False}
(R/'completion_audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
