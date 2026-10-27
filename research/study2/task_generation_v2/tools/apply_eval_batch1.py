"""Apply Task Evaluator batch-1 revisions (task_eval_batch1) to blueprints + roster.
Run from research/study2/task_generation_v2. Edits blueprint.json/roster.json in place; then run tools/export_tasks.py and tools/check_packages.py.
"""
import json, pathlib, re
R = pathlib.Path('.')
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
REV = 'eval-batch1-r1'

# ---- roster: R1 addenda must not echo task-document phrases (F2 / C3) ----
ro = load(R/'organization/roster.json')
add = {
 'Sarah Johnson': 'Sets technical direction and signs off high-risk production changes. Delegates sign-off authority when away.',
 'Li Ming': 'Plans Database team capacity and release resourcing.',
 'Liu Qiang': 'Runs cross-team test sign-offs before production releases.',
 'Zhang Wei': 'Senior engineer on the Streaming DB team; acts as technical deputy for the CTO when designated.',
 'David Wong': 'Owns the general ledger calendar and spending limits above department level.',
 'Wang Fang': 'Tracks AI research project capacity and seat plans.',
 'Jessica Lee': 'Runs campaign planning; creative production is handled with the brand team.',
 'Sophia Rodriguez': 'Leads brand and visual design work, including campaign creative files.',
}
for o in ro:
    if o['name'] in add: o['r1_addendum'] = add[o['name']]
dump(R/'organization/roster.json', ro)

def bp(t): return R/'templates'/t/'blueprint.json'
def note(b, msg):
    b.setdefault('revision_log', []).append({'revision': REV, 'change': msg})
    b['version'] = '0.2.0'

# ---- m-high-service-cutover: CTO on leave -> designated deputy (F2) ----
p = bp('m-high-service-cutover'); b = load(p)
b['documents']['ownership.md'] = ('Operational quality attestations belong to cross-team QA. Executive technical mandates belong to the CTO; '
    'while the CTO is away, the designated technical deputy issues them with the same authority. Each mandate must cite the readiness record and the applicable freeze interval.')
b['documents']['calendar.md'] = ('Regional freeze on 2026-11-06: 02:00-04:00 UTC. All times UTC. The recovery team requires rollback interval of 20 minutes for six or more replicas; otherwise 10 minutes. '
    'Leadership calendar: CTO travelling 2026-11-02 to 2026-11-09 without sign-off access; designated technical deputy for the period is listed in the Engineering out-of-office note.')
b['documents']['engineering-ooo.md'] = 'Engineering out-of-office, week of 2026-11-02: Sarah Johnson (CTO) away; designated technical deputy: Zhang Wei. Emily Zhou away 2026-11-05.'
for h in b['hidden_information']:
    if h['id'] == 'H3':
        h['holder'] = 'Zhang Wei'
        h['release_rule'] = ('As designated technical deputy while the CTO is away, issue the technical mandate only after the current readiness reference and the overlapping freeze interval are supplied. Do not disclose the mandate prematurely.')
for n in b['gold_dag']['nodes']:
    if n['id'] == 'mandate': n['admissible_recipients'] = ['Zhang Wei']
b['hidden_information'].append({'id': 'D1', 'holder': 'Sarah Johnson', 'facts': {},
    'required_context': [], 'release_rule': 'You are travelling without sign-off access until 2026-11-09. If asked for a mandate, say you cannot sign off this week and that Zhang Wei is your designated deputy; issue nothing.'})
if 'Zhang Wei' not in b['candidate_pool']:
    b['candidate_pool'][b['candidate_pool'].index('Emily Zhou')] = 'Zhang Wei'
b['inference_evidence'] = ['Combine current allocation with calendar freeze to determine that an executive mandate is needed.',
    'Combine replica count with recovery policy before the QA request.',
    'Resolve the mandate issuer through the leadership calendar and the out-of-office note (CTO away -> designated deputy).']
b['classification_rationale'] += ' The obvious approver (CTO) is unavailable; the valid issuer is the designated deputy found via two documents.'
note(b, 'F2: CTO on leave; mandate issued by designated deputy Zhang Wei; added engineering-ooo.md; Sarah Johnson redirects without issuing.')
dump(p, b)

# ---- m-medium-research-purchase: conditional counted once (F3) ----
p = bp('m-medium-research-purchase'); b = load(p)
b['feature_scores'] = [1, 1, 1, 2]  # N, depth, separation (different people), inference (computed amount + threshold rule)
b['difficulty_score'] = sum(b['feature_scores'])
b['separation'] = 'separated'
b['inference_evidence'] = ['Compute the current annual amount from the current seat count (needs H1) and apply the USD 10000 threshold to select the release owner.']
note(b, 'F3: conditional approval counted under inference only (separation 2->1, inference 1->2); D unchanged at 5.')
dump(p, b)

# ---- o-low-campaign-asset: neutral cue + measurable quality (F1) ----
p = bp('o-low-campaign-asset'); b = load(p)
b['documents']['brief.md'] = ('Campaign Cedar. Headline: Build together. Launch 2026-11-09. Hero asset on file: evergreen-v2.svg (licensed, approved for all launches). '
    'This brief was written 2026-09-20.')
b['documents']['asset-register.md'] = ('Asset register export (2026-09-30): evergreen-v2.svg | campaign: any | license valid through 2027-06-30. '
    'Note: assets produced after the export date are added to the register at the next quarterly export.')
b['documents']['brand-calendar.md'] = 'Brand team production calendar, October 2026: Cedar launch creative (in production, owner: brand design).'
for h in b['hidden_information']:
    h['holder'] = 'Sophia Rodriguez'
    h['facts'] = {'hero_asset': 'cedar-launch-v4.svg', 'asset_campaign': 'Cedar', 'license_valid_through': '2027-12-31'}
    h['release_rule'] = 'Provide the finished Cedar launch asset file name and its register metadata when asked about Cedar creative. The evergreen asset remains valid; no authorization is required.'
for n in b['gold_dag']['nodes']: n['admissible_recipients'] = ['Sophia Rodriguez']
if 'Sophia Rodriguez' not in b['candidate_pool']:
    swap = next(x for x in b['candidate_pool'] if x not in ('Jessica Lee',))
    b['candidate_pool'][b['candidate_pool'].index(swap)] = 'Sophia Rodriguez'
if 'Jessica Lee' not in b['candidate_pool']:
    swap = next(x for x in b['candidate_pool'] if x != 'Sophia Rodriguez')
    b['candidate_pool'][b['candidate_pool'].index(swap)] = 'Jessica Lee'
b['hidden_information'].append({'id': 'D1', 'holder': 'Jessica Lee', 'facts': {}, 'required_context': [],
    'release_rule': 'You plan campaigns but do not hold creative files. If asked for the Cedar asset, say creative files come from the brand design team; give no file name.'})
b['cue'] = {'documents': ['brief.md', 'asset-register.md', 'brand-calendar.md'],
    'description': 'Brief and register predate the October Cedar creative listed in the brand calendar; no statement that a better asset exists or who holds it.'}
b['quality'] = {'dimension': 'campaign_matched_asset', 'check': 'hero_asset metadata campaign == "Cedar" AND license_valid_through >= 2026-11-09 (looked up in the private asset register)',
    'baseline': 0, 'full_information': 1, 'minimum_improvement': 1}
b['feature_scores'] = [0, 1, 1, 0]  # N, cue implicit (needs dates across two docs), holder via brand-calendar owner, copy one value
b['difficulty_score'] = sum(b['feature_scores'])
b['target_level'] = 'Low'
b['inference_evidence'] = ['Notice that brief and register predate the October Cedar creative in the brand calendar.', 'Brand calendar owner "brand design" maps to the UX/brand designer, not the marketing manager.']
b['classification_rationale'] = 'The licensed evergreen asset satisfies the baseline; a newer Cedar-specific asset, held by brand design, improves campaign match measured by register metadata.'
note(b, 'F1: removed explicit "optional asset that improves" hint; cue now implicit via dates; holder moved to brand design (Sophia Rodriguez) with Jessica Lee as plausible decoy; quality scored by register metadata. D 0->2 (still Low).')
dump(p, b)

# ---- o-high-training-schedule: list equivalence (F4) ----
p = bp('o-high-training-schedule'); b = load(p)
eq = b['output_contract']['equivalences']
s = 'List fields are order-insensitive multisets (e.g., cohort_sizes [12,12]).'
if s not in eq: eq.append(s)
note(b, 'F4: cohort_sizes declared order-insensitive.')
dump(p, b)

# ---- refresh derived fields for all edited tasks ----
for t in ['m-high-service-cutover', 'm-medium-research-purchase', 'o-low-campaign-asset', 'o-high-training-schedule']:
    p = bp(t); b = load(p)
    b['runtime_classification_status'] = 'revised_after_evaluator_batch1_pending_reevaluation'
    dump(p, b)
print('applied', REV)
