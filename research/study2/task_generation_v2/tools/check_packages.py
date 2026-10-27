"""Packaging checks only: not a Task Evaluator; no task quality verdicts."""
import ast,collections,hashlib,json,pathlib,csv
import jsonschema
R=pathlib.Path(__file__).resolve().parents[1];schema=json.loads((R/'metadata.schema.json').read_text());rows=[]
org={x['name'] for x in json.loads((R/'organization/roster.json').read_text())}
for d in sorted((R/'templates').iterdir()):
 b=json.loads((d/'blueprint.json').read_text());m=json.loads((d/'metadata.json').read_text());jsonschema.validate(m,schema)
 assert len(set(b['candidate_pool']))==b['N'];assert set(b['candidate_pool'])<=org
 assert not list(d.rglob('evaluator.py'))
 ids={x['id'] for x in b['gold_dag']['nodes']};assert len(ids)==len(b['gold_dag']['nodes'])
 done=set()
 while len(done)<len(ids):
  ready={x['id'] for x in b['gold_dag']['nodes'] if set(x['requires'])<=done}-done
  assert ready,'cyclic or missing dependency';done|=ready
 for h in b['hidden_information']:assert h['holder'] in b['candidate_pool']
 for p in d.rglob('*.py'):ast.parse(p.read_text())
 for c in ['R0','R1']:
  assert set(p.name for p in (d/'tac'/('documents_'+c)).glob('*.md'))==set(b['documents'])|{'directory.md'}
 for n in b['documents']:assert (d/'tac/documents_R0'/n).read_bytes()==(d/'tac/documents_R1'/n).read_bytes()
 s=json.loads((d/'simulator/task.json').read_text());assert s['private_records']==b['hidden_information'];assert s['gold_dag']==b['gold_dag']
 assert set(json.loads((d/'tac/scenarios.json').read_text()))==set(b['candidate_pool'])
 for name,sha in json.loads((d/'manifest.json').read_text()).items():assert hashlib.sha256((d/name).read_bytes()).hexdigest()==sha
 rows.append({'task_id':b['task_id'],'class':b['help_class'],'level':b['target_level'],'N':b['N'],'depth':b['dependency_depth'],'score':b['difficulty_score'],'package_checks':'passed'})
assert collections.Counter((r['class'],r['level']) for r in rows)==collections.Counter((c,l) for c in ['Must-help','Optional-help'] for l in ['Low','Medium','High'])
(R/'validation/package_checks.json').write_text(json.dumps({'scope':'schema, references, DAG acyclicity, exports and hashes only; no classification, difficulty, realism or quality acceptance','tasks':rows},indent=2)+'\n')
with (R/'task_matrix.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('6/6 packaging checks passed; no Task Evaluator executed')
