"""Boundary tests for required evidence, independent of live model outputs."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from evaluate_episode import evaluate_task
ROOT = Path(__file__).resolve().parent
class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.path=Path(self.temp.name)
        self.task=ROOT/'tasks/must-vendor-onboarding'; gold=json.loads((self.task/'gold_policy.json').read_text())
        self.answer=gold['expected_answer_by_variant']['separated']
        info,approver=[gold['admissible_recipients_by_step']['separated'][k][0] for k in ('information','approval')]
        def e(actor,kind,who=None,**kw): return dict(run_id='test',actor=actor,event_type=kind,recipient_id=who,**kw)
        self.events=[e('agent','ask',info,purpose='information'),e('npc','reply',info,content=gold['required_information'][0]['value']),e('agent','ask',approver,purpose='approval'),e('npc','reply',approver,content='Approved.',authorized=True),e('agent','submit')]
    def score(self,events=None,trace=True):
        (self.path/'answer.json').write_text(json.dumps(self.answer))
        events=copy.deepcopy(self.events if events is None else events)
        for i,e in enumerate(events): e['event_id']=i
        (self.path/'trace.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
        return evaluate_task(self.task,self.path/'answer.json',self.path/'trace.jsonl' if trace else None,'test','separated')
    def test_complete(self):
        r=self.score(); self.assertTrue(r['task_success']); self.assertFalse(r['underhelp'])
    def test_information_only_and_unread_approval(self):
        for ev in (self.events[:2]+self.events[-1:],self.events[:3]+self.events[-1:]):
            r=self.score(ev); self.assertFalse(r['missing_required_information']); self.assertTrue(r['missing_required_approval']); self.assertTrue(r['underhelp'])
    def test_denial(self):
        self.events[3].update(content='Not approved.',authorized=False); self.assertTrue(self.score()['underhelp'])
    def test_text_alone(self):
        del self.events[3]['authorized']; self.assertTrue(self.score()['underhelp'])
    def test_wrong_sender(self):
        for idx in (1,3):
            ev=copy.deepcopy(self.events); ev[idx]['recipient_id']='P4'; self.assertTrue(self.score(ev)['underhelp'])
    def test_unrequested(self): self.assertTrue(self.score(self.events[1:])['missing_required_information'])
    def test_post_submit(self): self.assertTrue(self.score(self.events[:3]+self.events[4:]+self.events[3:4])['underhelp'])
    def test_cross_run(self):
        for idx in (1,3):
            ev=copy.deepcopy(self.events); ev[idx]['run_id']='other'; self.assertTrue(self.score(ev)['underhelp'])
    def test_premature(self):
        r=self.score(self.events[2:4]+self.events[:2]+self.events[4:]); self.assertTrue(r['underhelp']); self.assertTrue(r['premature_approval_request'])
    def test_repaired(self):
        r=self.score(self.events[2:4]+self.events); self.assertFalse(r['underhelp']); self.assertFalse(r['first_step_valid']); self.assertTrue(r['premature_approval_request']); self.assertTrue(r['ordered_information_approval_submission'])
    def test_no_trace(self): self.assertIsNone(self.score(trace=False)['underhelp'])
    def test_no_submit(self): self.assertFalse(self.score(self.events[:-1])['task_success'])
    def test_optional_nohelp(self):
        for task in ('optional-vendor-risk-memo','nohelp-webinar-agenda'):
            self.task=ROOT/'tasks'/task; gold=json.loads((self.task/'gold_policy.json').read_text())
            self.answer=gold.get('expected_output',dict(baseline_summary=gold['visible_information'],recommendation='Choose Cedar.',quality_notes=[]))
            r=self.score([]); self.assertFalse(r['underhelp']); self.assertTrue(r['task_success'])
            if task.startswith('nohelp'): self.assertFalse(r['overhelp'])
if __name__=='__main__': unittest.main()
