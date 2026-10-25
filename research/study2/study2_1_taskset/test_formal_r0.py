"""Offline checks for true paired R0 treatment and metadata."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import formal_r0 as formal
import multimodel_r1_pilot as engine
from instantiate_run import instantiate
class R0Tests(unittest.TestCase):
    def test_exact_pairing_schedule(self):
        old=formal.read(formal.R1_REFERENCE/'schedule.json');new=formal.schedule()
        self.assertEqual(len(new),180)
        self.assertEqual(len({j['run_id'] for j in new}),180)
        for a,b in zip(old,new):
            self.assertEqual({k:v for k,v in a.items() if k not in ('run_id','profile_condition')},{k:v for k,v in b.items() if k not in ('run_id','profile_condition')})
            self.assertEqual(b['profile_condition'],'R0');self.assertNotEqual(a['run_id'],b['run_id'])
    def test_all_templates_visible_treatment(self):
        with tempfile.TemporaryDirectory() as t:
            for j in formal.schedule()[::3]:
                out=Path(t)/j['task_id'];instantiate(formal.ROOT/'tasks'/j['task_id'],out,'offline',j['instance_seed'],'R0',j['alignment'])
                profiles=formal.read(out/'candidate_profiles.json');old=formal.read(formal.R1_REFERENCE/'episodes'/j['run_id'].replace('formal-r0-','formal-r1-',1)/'candidate_profiles.json')
                self.assertEqual(len(profiles),len(old))
                for a,b in zip(profiles,old):
                    self.assertEqual(a['profile'],a['name']+' — '+a['job_title'])
                    self.assertEqual({k:v for k,v in a.items() if k!='profile'},{k:v for k,v in b.items() if k!='profile'})
    def test_engine_r0_metadata_matches_actual_prompt(self):
        with tempfile.TemporaryDirectory() as t:
            engine.CURRENT_MODEL='openai';engine.SECRETS=['offline'];engine.RUN_TAG='offline'
            def fake(messages,key):
                return {'role':'assistant','content':None,'tool_calls':[{'id':'offline','type':'function','function':{'name':'submit_answer','arguments':json.dumps({'answer':{'end':'14:30','duration':90}})}}]}, {'prompt_tokens':10,'completion_tokens':10},formal.EXPECTED['openai'],'tool_calls','offline-id',0
            with patch.object(engine,'call_model',fake):
                rec=engine.run_episode('nohelp-webinar-agenda','not_applicable',1,Path(t),'offline',{'run_id':'formal-r0-offline','run_type':'confirmatory','collection_stage':'R0','profile_condition':'R0','protocol_version':formal.PROTOCOL})
            self.assertEqual(rec['profile_condition'],'R0');self.assertEqual(rec['collection_stage'],'R0')
            ep=Path(t)/'episodes'/rec['run_id']
            self.assertEqual(formal.read(ep/'run_manifest.json')['profile_condition'],'R0')
            for p in formal.read(ep/'candidate_profiles.json'):self.assertEqual(p['profile'],p['name']+' — '+p['job_title'])
if __name__=='__main__':unittest.main()
