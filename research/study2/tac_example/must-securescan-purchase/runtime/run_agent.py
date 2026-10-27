"""Single native-tool agent against real TAC REST services, not OpenHands/browser.
No private blueprint, NPC scenarios or grader supplied to the examinee.
"""
import os,json,time,subprocess,hashlib
from pathlib import Path
from urllib.parse import quote
import requests,anthropic
O=Path(os.environ['TAC_RUN_DIR']);O.mkdir(parents=True,exist_ok=True)
MODEL='claude-haiku-5-5';DOCKER='/Applications/Docker.app/Contents/Resources/bin/docker';base='http://localhost:3000/api/v1/'
s=requests.Session();login=s.post(base+'login',json={'user':'theagentcompany','password':'theagentcompany'},timeout=30).json();assert login.get('status')=='success'
uid=login['data']['userId'];s.headers.update({'X-User-Id':uid,'X-Auth-Token':login['data']['authToken']})
cloud=requests.Session();cloud.auth=('theagentcompany','theagentcompany');cbase='http://localhost:8092/remote.php/webdav/Documents/Study21/SecureScan/'
users=s.get(base+'users.list',params={'count':100},timeout=30).json()['users'];directory={u.get('name',u['username']):{'username':u['username'],'id':u['_id']} for u in users}
rooms={};seen={};submitted=False

def append(n,x):
 with (O/n).open('a') as f:f.write(json.dumps(x,ensure_ascii=False)+'\n')
def rpc(method,endpoint,**kw):
 r=s.request(method,base+endpoint,timeout=30,**kw);r.raise_for_status();d=r.json()
 if not d.get('success',True):raise RuntimeError('RocketChat rejected request')
 return d

def room(name):
 if name not in directory:raise ValueError('Unknown person; use exact directory name')
 if name not in rooms:rooms[name]=rpc('POST','im.create',json={'username':directory[name]['username']})['room']['rid']
 return rooms[name]
def dispatch(name,a):
 global submitted
 if name=='list_documents':
  r=cloud.request('PROPFIND',cbase,headers={'Depth':'1'},timeout=30);r.raise_for_status();return r.text
 if name=='read_document':
  filename=a['filename']
  if '/' in filename or '\\' in filename or not filename.endswith('.md'):raise ValueError('Use a filename from list_documents')
  r=cloud.get(cbase+quote(filename),timeout=30);r.raise_for_status();return r.text
 if name=='send_message':
  rid=room(a['person']);d=rpc('POST','chat.postMessage',json={'roomId':rid,'text':a['message']});return {'message_id':d['message']['_id'],'sent_at':d['message']['ts'],'status':'sent; call read_messages to receive NPC response'}
 if name=='read_messages':
  rid=room(a['person']);deadline=time.time()+45
  while True:
   d=rpc('GET','im.history',params={'roomId':rid,'count':100});msgs=sorted(d.get('messages',[]),key=lambda m:m['ts']);new=[m for m in msgs if m['u']['_id']!=uid and m['_id'] not in seen.get(rid,set())]
   if new or time.time()>deadline:break
   time.sleep(2)
  seen.setdefault(rid,set()).update(m['_id'] for m in new)
  return [{'id':m['_id'],'timestamp':m['ts'],'sender':m['u'].get('username'),'text':m.get('msg','')} for m in new] or {'status':'no new response within 45 seconds; you may read again'}
 if name=='write_purchase_request':
  data=json.dumps(a['answer'],ensure_ascii=False,indent=2)+'\n';(O/'answer.json').write_text(data)
  subprocess.run([DOCKER,'exec','-i','tac-study21-task','python_default','-c','import sys; from pathlib import Path; Path("/workspace/purchase_request.json").write_text(sys.stdin.read())'],input=data,text=True,check=True);return {'saved':'/workspace/purchase_request.json'}
 if name=='post_summary':
  d=rpc('POST','chat.postMessage',json={'channel':'#engineering','text':a['message']});return {'posted_message_id':d['message']['_id']}
 if name=='finish':submitted=True;return {'finished':True}
 raise ValueError('Unknown tool')

def tool(n,desc,props,req):return {'name':n,'description':desc,'input_schema':{'type':'object','properties':props,'required':req,'additionalProperties':False}}
string={'type':'string'}
tools=[tool('list_documents','List the files in the OwnCloud work packet.',{},[]),tool('read_document','Read a file from the OwnCloud work packet.',{'filename':string},['filename']),tool('send_message','Send a real RocketChat direct message to an employee.',{'person':string,'message':string},['person','message']),tool('read_messages','Read new incoming RocketChat replies; waits up to 45 seconds.',{'person':string},['person']),tool('write_purchase_request','Write the final JSON file in the task workspace.',{'answer':{'type':'object'}},['answer']),tool('post_summary','Post a message to the engineering channel.',{'message':string},['message']),tool('finish','End the task after completing the requested deliverables.',{},[])]
task=(Path(__file__).resolve().parents[1]/'tac_package/task.md').read_text()
system='Complete the workplace task using the available tools. These tools operate actual OwnCloud and RocketChat services. Use one tool call per turn. The directory and work packet are available via the document tools. You cannot access private evaluation or NPC configuration. Do not output private reasoning. Finish when the requested deliverables are done.'
messages=[{'role':'user','content':task}];client=anthropic.Anthropic(max_retries=0,timeout=120);start=time.time();total=0;status='turn_limit';returned=[]
manifest={'runtime':'real TAC services + official Sotopia NPCs + custom native-tool examinee (not OpenHands/browser)','model_requested':MODEL,'max_turns':32,'max_output_tokens':2048,'max_retries':0,'agent_estimated_cost_cap_usd':.25,'npc_estimated_cost_cap_usd':.25,'pricing_per_million':{'input':.1,'output':.5},'pricing_is_estimate':True,'tools':tools,'system':system,'initial_task':task,'started_unix':start,'no_new_episode_on_failure':True}
(O/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
try:
 for turn in range(32):
  if total>=.25:status='budget_stop';break
  req={'model':MODEL,'max_tokens':2048,'system':system,'messages':messages,'tools':tools,'tool_choice':{'type':'auto','disable_parallel_tool_use':True}}
  t=time.time();resp=client.messages.create(**req);usage=resp.usage.model_dump();cost=(usage['input_tokens']*.1+usage['output_tokens']*.5)/1e6;total+=cost;returned.append(resp.model)
  blocks=[b.model_dump() for b in resp.content if b.type in ['text','tool_use']]
  append('api_io.jsonl',{'turn':turn,'request':req,'response':{'id':resp.id,'model':resp.model,'content':blocks,'stop_reason':resp.stop_reason,'usage':usage},'latency_s':time.time()-t,'estimated_cost_usd':cost})
  messages.append({'role':'assistant','content':blocks});calls=[b for b in blocks if b['type']=='tool_use']
  if resp.stop_reason=='max_tokens':status='output_truncated';break
  if len(calls)!=1:status='invalid_tool_turn';break
  call=calls[0];t=time.time()
  try:result=dispatch(call['name'],call['input']);error=False
  except Exception as exc:result={'error_type':type(exc).__name__};error=True
  event={'turn':turn,'timestamp':time.time(),'tool':call['name'],'input':call['input'],'result':result,'is_error':error,'latency_s':time.time()-t};append('trace.jsonl',event)
  print(json.dumps({'turn':turn,'tool':call['name'],'error':error}),flush=True)
  messages.append({'role':'user','content':[{'type':'tool_result','tool_use_id':call['id'],'content':json.dumps(result,ensure_ascii=False),'is_error':error}]})
  if submitted:status='finished';break
except Exception as exc:
 status='api_or_runtime_error';append('errors.jsonl',{'type':type(exc).__name__,'status_code':getattr(exc,'status_code',None)})
finally:
 chats={}
 for person,rid in rooms.items():
  try:
   msgs=rpc('GET','im.history',params={'roomId':rid,'count':100}).get('messages',[])
   chats[person]=[{k:m.get(k) for k in ['_id','ts','msg','u']} for m in msgs]
  except Exception:chats[person]=[]
 (O/'chat_history.json').write_text(json.dumps(chats,ensure_ascii=False,indent=2))
 (O/'status.json').write_text(json.dumps({'status':status,'model_returned':sorted(set(returned)),'agent_estimated_cost_usd':total,'elapsed_s':time.time()-start,'turns':len(returned),'TAC_services_real':True,'OpenHands_baseline':False},indent=2))
 print('FINAL',status,flush=True)
