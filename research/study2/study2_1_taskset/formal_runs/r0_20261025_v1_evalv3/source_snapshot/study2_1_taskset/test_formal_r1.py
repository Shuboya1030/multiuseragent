"""Offline checks for formal scheduling, budget controls and stage metadata."""
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import formal_r1 as formal
import multimodel_r1_pilot as engine

class FormalTests(unittest.TestCase):
    def test_balanced_paired_schedule(self):
        rows=formal.schedule();self.assertEqual(len(rows),180);self.assertEqual(rows,formal.schedule())
        self.assertEqual(len({r['run_id'] for r in rows}),180)
        self.assertTrue(all(v==20 for v in Counter((r['provider'],r['help_need_class']) for r in rows).values()))
        self.assertTrue(all(v==20 for v in Counter((r['provider'],r['provider_position']) for r in rows).values()))
        for task in {r['task_id'] for r in rows}:
            matched=[r for r in rows if r['task_id']==task]
            self.assertEqual(len({r['instance_seed'] for r in matched}),1)
            self.assertEqual(len({r['provider'] for r in matched}),3)
        self.assertTrue(all(r['alignment']=='separated' for r in rows if r['help_need_class']=='must_ask'))

    def test_cost_cache_accounting(self):
        self.assertAlmostEqual(formal.cost('openai',{'prompt_tokens':1000,'completion_tokens':100,'prompt_tokens_details':{'cached_tokens':500}}),(.75*500+.075*500+4.5*100)/1e6)
        self.assertAlmostEqual(formal.cost('anthropic',{'prompt_tokens':1000,'completion_tokens':100,'cache_read_input_tokens':500}),(.1*1000+.01*500+.5*100)/1e6)

    def test_budget_and_unknown_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine.CURRENT_MODEL='openai';engine.CURRENT_RUN_ID='offline';engine.CURRENT_TURN=0
            def fail(*args):raise RuntimeError('offline failure')
            guard=formal.Guard(Path(tmp),0,fail)
            with self.assertRaises(RuntimeError):guard([], 'fake')
            self.assertEqual(guard.charged,0)
            guard=formal.Guard(Path(tmp),1,fail)
            with self.assertRaises(RuntimeError):guard([], 'fake')
            self.assertAlmostEqual(guard.charged,formal.call_reservation('openai'))

    def test_formal_metadata_and_failed_episode_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine.CURRENT_MODEL='openai';engine.SECRETS=['fake-secret'];engine.RUN_TAG='offline'
            def fake(messages,key):
                return {'role':'assistant','content':None,'tool_calls':[{'id':'offline','type':'function','function':{'name':'submit_answer','arguments':json.dumps({'answer':{'end':'14:30','duration':90}})}}]}, {'prompt_tokens':100,'completion_tokens':20},formal.EXPECTED['openai'],'tool_calls','offline-id',0
            with patch.object(engine,'call_model',fake):
                r=engine.run_episode('nohelp-webinar-agenda','not_applicable',1,Path(tmp),'fake-secret',{'run_id':'formal-offline-test','run_type':'confirmatory','collection_stage':'R1','protocol_version':formal.PROTOCOL})
            self.assertEqual(r['run_type'],'confirmatory');self.assertEqual(r['collection_stage'],'R1');self.assertEqual(r['run_id'],'formal-offline-test');self.assertTrue(r['behavior_metrics']['task_success'])
            with patch.object(engine,'call_model',side_effect=RuntimeError('offline API error')):
                r=engine.run_episode('nohelp-webinar-agenda','not_applicable',2,Path(tmp),'fake-secret',{'run_id':'formal-offline-failure','run_type':'confirmatory','collection_stage':'R1','protocol_version':formal.PROTOCOL})
            self.assertEqual(r['status'],'failed');self.assertTrue((Path(tmp)/'episodes/formal-offline-failure/run_record.json').exists())
if __name__=='__main__':unittest.main()
