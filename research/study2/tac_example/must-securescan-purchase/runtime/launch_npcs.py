"""Launch upstream TAC NPCs without printing API keys or login/session tokens."""
import os,json,subprocess
from pathlib import Path
# Upstream prints full LLM key in run_multi_npc; do not invoke that launcher.
for name in json.loads(Path('/npc/scenarios.json').read_text()):
 path=Path('/tmp')/('npc-'+name.replace(' ','-')+'.private.log')
 with path.open('w') as f:
  os.chmod(path,0o600)
  subprocess.Popen(['python_default','/npc/run_one_npc.py','--agent_name',name],env=os.environ.copy(),stdout=f,stderr=f)
print('Launched configured NPC processes; live readiness still requires verification.')
