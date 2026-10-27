"""Build both profile variants and verify real OwnCloud deployment. No NPC launch or LLM calls."""
import subprocess,pathlib,json,datetime
R=pathlib.Path(__file__).resolve().parents[1];docker='/Applications/Docker.app/Contents/Resources/bin/docker'
rows=[]
for d in sorted((R/'templates').iterdir()):
 for profile in ['R0','R1']:
  tag='tac-study21-'+d.name+':v01-'+profile.lower()
  log=R/'validation'/('build-'+d.name+'-'+profile+'.log')
  with log.open('w') as f:p=subprocess.run([docker,'build','--platform','linux/amd64','--build-arg','PROFILE='+profile,'-t',tag,str(d/'tac')],stdout=f,stderr=subprocess.STDOUT,timeout=600)
  if p.returncode:raise RuntimeError('Build failed: '+str(log))
  code="""import pathlib,json,runpy
assert not pathlib.Path('/utils/evaluator.py').exists()
assert not pathlib.Path('/utils/eval.py').exists()
s=json.loads(pathlib.Path('/npc/scenarios.json').read_text())
credentials=json.loads(pathlib.Path('/npc/npc_credential.json').read_text())
assert s and all('extra_info' in v and 'strategy_hint' in v for v in s.values())
assert pathlib.Path('/npc/run_multi_npc.py').exists()
assert pathlib.Path('/instruction/task.md').read_text()
assert not pathlib.Path('/workspace/blueprint.json').exists()
pathlib.Path('/workspace/.deployment-write-probe').write_text('ok')
pathlib.Path('/workspace/.deployment-write-probe').unlink()
runpy.run_path('/utils/populate_data.py',run_name='__main__')
"""
  p=subprocess.run([docker,'run','--rm','--platform','linux/amd64','--add-host','the-agent-company.com:host-gateway',tag,'python','-c',code],capture_output=True,text=True,timeout=180)
  # Do not persist arbitrary service responses or credentials.
  if p.returncode:raise RuntimeError('Deployment failed for '+tag+'; inspect locally without exposing credentials. '+p.stderr[-500:])
  digest=subprocess.check_output([docker,'image','inspect','-f','{{.Id}}',tag],text=True).strip()
  rows.append({'task_id':d.name,'profile':profile,'image':tag,'image_id':digest,'build':'passed','owncloud_upload_and_exact_readback':'passed','workspace_writable':True,'npc_scenario_parse':'passed','no_task_evaluator':True,'npc_llm_response_test':'not_run','openhands_execution':'not_run'})
  (R/'validation/deployment_checks.json').write_text(json.dumps({'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Deployment only. No model calls. Shared service task namespaces; fresh isolated service reset still needed before episodes.','variants':rows},indent=2)+'\n')
  print(d.name,profile,'passed',flush=True)
