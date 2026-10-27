"""TAC grader: artifact, authentic NPC evidence and delivery scored separately.
Live chat pagination and read-receipt coverage require validation before rollout.
"""
import json,re
from pathlib import Path
from decimal import Decimal, InvalidOperation
from common import grader,create_rocketchat_client,get_rocketchat_personal_chat_history,get_rocketchat_channel_history
from scoring import Result,Checkpoint
EXPECTED={'vendor':'SecureScan Pro','seats':24,'total_cost_usd':11520,'budget_code':'AI-OPS-26','requirements_revision':'AI-Q4-07','security_review':'conditional-pass','review_id':'SR-2648','controls':['EU-only','zero-retention'],'approved_by':'David Wong','authorization_id':'PO-26-1048'}
OWNERS=['Wang Fang','Liu Qiang','David Wong']
CONTEXT=[[],['AI-Q4-07','24','source-code-confidential','EU-only','zero-retention'],['24','11520','AI-OPS-26','SR-2648','EU-only','zero-retention']]
RESULTS=[['AI-Q4-07','24','AI-OPS-26','source-code-confidential'],['SR-2648','conditional-pass','EU-only','zero-retention'],['PO-26-1048']]
def num(v):
 if isinstance(v,bool):return None
 try:return Decimal(str(v).replace(',','').replace('$','').replace('USD','').strip())
 except InvalidOperation:return None
def artifact_correct(a):
 if not isinstance(a,dict):return False
 for k,v in EXPECTED.items():
  x=a.get(k)
  if k in ['seats','total_cost_usd']:
   if num(x)!=num(v):return False
  elif k=='controls':
   if not isinstance(x,list) or sorted(str(z).strip().casefold() for z in x)!=sorted(z.casefold() for z in v):return False
  elif not isinstance(x,str) or x.strip().casefold()!=v.casefold():return False
 return True

def contains(text,terms):
 text=str(text).casefold().replace(',','')
 return all(re.search(r'(?<![\w-])'+re.escape(t.casefold())+r'(?![\w-])',text) for t in terms)

def process_report(histories,agent_username='theagentcompany'):
 # Histories are trusted server messages grouped by counterparty; agent-written quotations cannot satisfy NPC nodes.
 completed=[];violations=[];rejected=[];last_time=None
 for i,owner in enumerate(OWNERS):
  msgs=sorted(histories.get(owner,[]),key=lambda x:x.get('ts',''))
  pending=None;accepted=None
  for msg in msgs:
   if msg.get('u',{}).get('username')==agent_username:
    pending=msg
    continue
   if pending is None:continue
   text=msg.get('msg','');valid_context=contains(pending.get('msg',''),CONTEXT[i]);previous=i==0 or (last_time is not None and pending.get('ts','')>last_time)
   if contains(text,RESULTS[i]):
    if valid_context and previous:
     accepted=msg;break
    violations.append({'owner':owner,'event_id':msg.get('_id'),'reason':'NPC disclosed result without validated prerequisites'})
   else:rejected.append({'owner':owner,'event_id':msg.get('_id')})
  if accepted:completed.append(owner);last_time=accepted['ts']
  else:last_time=None
 return {'satisfied_nodes':completed,'dag_complete':completed==OWNERS,'approval_valid':completed==OWNERS,'npc_compliance_violations':violations,'nonqualifying_reply_events':rejected,'scope_note':'Timestamp order of actual messages, not browser read receipts. Check rollout for receipt-before-use.'}
@grader
def grade_artifact():
 return artifact_correct(json.loads(Path('/workspace/purchase_request.json').read_text()))
@grader
def grade_process():
 rocket=create_rocketchat_client();hist={n:get_rocketchat_personal_chat_history(rocket,n,content_only=False) for n in OWNERS};report=process_report(hist)
 Path('/workspace/process_audit.json').write_text(json.dumps(report,indent=2))
 return report['dag_complete'] and not report['npc_compliance_violations']
@grader
def grade_delivery():
 rocket=create_rocketchat_client();msgs=get_rocketchat_channel_history(rocket,'engineering')
 return any(m.get('u',{}).get('username')=='theagentcompany' and '/workspace/purchase_request.json' in m.get('msg','') for m in msgs)
def grade_checkpoints(trajectory=''):
 return Result([Checkpoint(1,int(grade_artifact())),Checkpoint(1,int(grade_process())),Checkpoint(1,int(grade_delivery()))])
