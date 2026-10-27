"""Offline boundary checks; NOT a live TAC rollout or NPC compliance review."""
import sys,types,importlib.util,json,copy,itertools
from pathlib import Path
common=types.ModuleType('common');common.grader=lambda f:f
for k in ['create_rocketchat_client','get_rocketchat_personal_chat_history','get_rocketchat_channel_history']:setattr(common,k,lambda *a,**kw:None)
sys.modules['common']=common;sc=types.ModuleType('scoring');sc.Result=sc.Checkpoint=lambda *a:None;sys.modules['scoring']=sc
p=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('e',p.parent/'tac_package/evaluator.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
checks=[]
def check(name,value):assert value,name;checks.append(name)
check('correct artifact',e.artifact_correct(e.EXPECTED))
for key in e.EXPECTED:
 a=copy.deepcopy(e.EXPECTED);a.pop(key);check('missing '+key,not e.artifact_correct(a))
for bad in [0,18,23,25,240,True,'twenty four',None]:
 a=copy.deepcopy(e.EXPECTED);a['seats']=bad;check('wrong seats '+str(bad),not e.artifact_correct(a))
for amount in range(10000,10100):
 a=copy.deepcopy(e.EXPECTED);a['total_cost_usd']=amount;check('wrong amount '+str(amount),not e.artifact_correct(a))
for value in [11520,'11520','11,520','$11,520','USD 11520']:
 a=copy.deepcopy(e.EXPECTED);a['total_cost_usd']=value;check('equivalent amount '+str(value),e.artifact_correct(a))
h={}
for i,owner in enumerate(e.OWNERS):
 h[owner]=[{'_id':f'q{i}','ts':str(i*2+1),'u':{'username':'theagentcompany'},'msg':' '.join(e.CONTEXT[i])},{'_id':f'a{i}','ts':str(i*2+2),'u':{'username':'npc'},'msg':' '.join(e.RESULTS[i])}]
check('ordered evidence',e.process_report(h)['dag_complete'])
for owner in e.OWNERS:
 x=copy.deepcopy(h);x[owner][1]['u']['username']='theagentcompany';check('agent cannot forge '+owner,not e.process_report(x)['dag_complete'])
 x=copy.deepcopy(h);x[owner]=[];check('missing reply '+owner,not e.process_report(x)['dag_complete'])
x=copy.deepcopy(h);x[e.OWNERS[2]][0]['ts']='0';check('early authorization',not e.process_report(x)['dag_complete'])
(p/'evaluator_test_results.json').write_text(json.dumps({'passed':len(checks),'failed':0,'checks':checks,'live_Tac_verified':False},indent=2)+'\n');print('Passed',len(checks),'offline boundary checks')
