"""Read-only provider model-directory checks; no inference calls."""
import json,os,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from multimodel_r1_pilot import MODELS,redact,write_json
import multimodel_r1_pilot as engine

def preflight(out):
    engine.SECRETS=[os.environ.get(c['env'],'') for c in MODELS.values()]
    assert all(engine.SECRETS),'Missing configured keys'
    rows=[]
    for p,c in MODELS.items():
        url=c['endpoint'].rsplit('/',1)[0]+'/models' if p=='anthropic' else c['endpoint'].split('/chat/')[0]+'/models'
        headers={'x-api-key':os.environ[c['env']],'anthropic-version':'2023-06-01'} if p=='anthropic' else {'Authorization':'Bearer '+os.environ[c['env']]}
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as resp:
            data=json.load(resp);matches=[x for x in data.get('data',[]) if x.get('id')==c['model'] or x.get('id','').startswith(c['model']+'-')]
            if not matches: raise RuntimeError('Requested model absent from '+p+' directory')
            rows.append({'provider':p,'checked_at':datetime.now(timezone.utc).isoformat(),'endpoint':url,'http_status':resp.status,'requested_model':c['model'],'matching_directory_entries':redact(matches),'response_limits':{k:v for k,v in resp.headers.items() if 'ratelimit' in k.lower() or 'rate-limit' in k.lower()}})
    write_json(out/'model_directory_checks.json',rows)
    print(json.dumps({'model_directory_checks':'passed','providers':len(rows),'inference_calls':0}))
if __name__=='__main__':
    import sys
    preflight(Path(sys.argv[1]))
