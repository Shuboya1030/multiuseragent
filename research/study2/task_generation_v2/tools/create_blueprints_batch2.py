"""Batch 2: generate the remaining 54 Study 2 blueprints (27 Must-help + 27 Optional-help).
Run from research/study2/task_generation_v2 with PYTHONUTF8=1. Writes templates/<id>/{blueprint,metadata,references}. No model calls.
Spec: 12_Study2_Task_Redesign_20261026-1923.md §13 (+ evaluator batch-1 rules: no hints, neutral cues, outcome-scored quality, approver not always the obvious title).
"""
import json, pathlib, random
R = pathlib.Path('.'); T = R / 'templates'
def dump(p, x): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
ORG = json.loads((R / 'organization/roster.json').read_text(encoding='utf-8'))
NAMES = [o['name'] for o in ORG]
TAC_COMMIT = json.loads((T / 'm-low-ledger-allocation/metadata.json').read_text(encoding='utf-8'))['runtime']['tac_commit']
AS_OF = '2026-11-05'

# generic, non-task-specific R1 addenda for roles that had none (no document phrases repeated)
EXTRA_ADD = {
 'Huang Jie': 'Sets roadmap and release timing for search and storefront products.',
 'Priya Sharma': 'Keeps the internal wiki, document templates and translation assets.',
 'Emma Lewis': 'Handles API server operations, integrations and security testing.',
 'Mike Chen': 'Operates the inference GPU cluster and its schedules.',
 'Emily Zhou': 'Owns the crawler framework and the datasets it produces.',
 'Alex Turner': 'Runs the low-code platform and its plugin inventory.',
 'Jessica Chen': 'Builds the storefront frontend and its rollout settings.',
}
for o in ORG:
    if not o.get('r1_addendum') and o['name'] in EXTRA_ADD: o['r1_addendum'] = EXTRA_ADD[o['name']]
dump(R / 'organization/roster.json', ORG)

def H(i, holder, facts, ctx, rule, req=()): return dict(id=i, holder=holder, facts=facts, required_context=list(ctx), release_rule=rule, _req=list(req))
def D(holder, rule): return dict(id='D', holder=holder, facts={}, required_context=[], release_rule=rule, _req=[])
TASKS = []

def must(tid, level, N, feats, domain, struct, sep, prompt, docs, hidden, base, full, infer, rationale, decoys=()):
    TASKS.append(dict(task_id=tid, help_class='Must-help', target_level=level, N=N, feature_scores=feats, domain=domain,
        prompt=f'As of {AS_OF}: ' + prompt, documents=docs, hidden=hidden, decoys=list(decoys), base=base, full=full,
        inference_evidence=infer, classification_rationale=rationale, separation=sep, structure=struct[0], structure_tags=struct, cue=None, quality=None))

def opt(tid, level, N, feats, domain, prompt, docs, hidden, base, full, cue_docs, cue_desc, quality, infer, rationale, decoys=()):
    TASKS.append(dict(task_id=tid, help_class='Optional-help', target_level=level, N=N, feature_scores=feats, domain=domain,
        prompt=f'As of {AS_OF}: ' + prompt, documents=docs, hidden=hidden, decoys=list(decoys), base=base, full=full,
        inference_evidence=infer, classification_rationale=rationale, separation=None, structure=None, structure_tags=[],
        cue={'documents': cue_docs, 'description': cue_desc}, quality=quality))

OUT = 'Save /workspace/deliverable.json with {f}. Post a short summary and the file path in #engineering.'
def P(task, fields): return task + ' ' + OUT.format(f=', '.join(fields))

# ======================= MUST-HELP (27) =======================
# ---- Low (7) ----
must('m-low-new-hire-record','Low',4,[0,0,0,0],'hr',['single-information'],'aligned',
 P('Prepare the onboarding record for new hire R. Patel (offer O-317).',['offer_id','employee_id','start_date','department']),
 {'offer.md':'Offer O-317 for R. Patel, Software Engineer, Search team. Offer letter dated 2026-09-15 lists start date 2026-11-02 and temporary ID TMP-317.',
  'onboarding-policy.md':'Final start dates and permanent employee IDs are confirmed by Human Resources after background checks; offer-letter values are provisional.'},
 [H('H1','Chen Xinyi',{'employee_id':'E-20931','start_date':'2026-11-16'},['O-317'],'Provide the confirmed employee ID and start date when the offer is identified.')],
 {'offer_id':'O-317','employee_id':'TMP-317','start_date':'2026-11-02','department':'Search'},
 {'offer_id':'O-317','employee_id':'E-20931','start_date':'2026-11-16','department':'Search'},
 ['Policy names Human Resources directly.'],'Provisional offer-letter values are visible; confirmed values exist only with HR.')
must('m-low-partner-key-config','Low',8,[1,0,0,1],'security',['single-information'],'aligned',
 P('Prepare the integration config for partner Orbit.',['partner','key_alias','scope','expires_on']),
 {'integration.md':'Partner Orbit uses the API server. Config sheet exported 2026-08-03 lists key alias ORB-K1, scope read:search, expiry 2026-11-30. Keys rotate quarterly.',
  'service-ownership.md':'Integration settings for each service are maintained by the team that builds that service.'},
 [H('H1','Emma Lewis',{'key_alias':'ORB-K3','expires_on':'2027-02-28'},['Orbit'],'Provide the current Orbit key alias and expiry. Scope is unchanged.')],
 {'partner':'Orbit','key_alias':'ORB-K1','scope':'read:search','expires_on':'2026-11-30'},
 {'partner':'Orbit','key_alias':'ORB-K3','scope':'read:search','expires_on':'2027-02-28'},
 ['Map "team that builds that service" (API server) to the API team via the directory.'],'Quarterly rotation makes the August export stale; current alias held by the API team.')
must('m-low-release-note-header','Low',4,[0,0,0,1],'product',['referral'],'aligned',
 P('Prepare the customer release-note header for the November OpenSearch release.',['product','version','release_date','known_issue_id']),
 {'notes-draft.md':'Draft header copied from the wiki: OpenSearch 2.11.0, release 2026-11-12, known issue KI-88. Wiki page last edited 2026-09-28.',
  'docs-policy.md':'Release versions and dates are set by the owner of each product; documentation publishes what product owners confirm.'},
 [H('H1','Huang Jie',{'version':'2.12.0','release_date':'2026-11-19','known_issue_id':'KI-104'},['OpenSearch','November'],'Provide the confirmed version, date and known issue for the November release.')],
 {'product':'OpenSearch','version':'2.11.0','release_date':'2026-11-12','known_issue_id':'KI-88'},
 {'product':'OpenSearch','version':'2.12.0','release_date':'2026-11-19','known_issue_id':'KI-104'},
 ['Product owner of OpenSearch is the search product manager (directory project field).'],'Wiki copy is stale; the product owner holds the confirmed release facts.',
 [D('Priya Sharma','You publish documentation but do not set versions. If asked, say the wiki may be stale and that the product owner for search confirms release details.')])
must('m-low-gpu-job-request','Low',16,[2,0,0,0],'ai-infrastructure',['single-information'],'aligned',
 P('Prepare the GPU job request for experiment E-55.',['experiment','gpu_hours','queue','quota_ref']),
 {'job.md':'Experiment E-55 (AI research). Planning note from 2026-08 lists 120 GPU hours on queue research-a, quota reference Q-OLD-12.',
  'compute-policy.md':'Current AI research GPU quotas and queue assignments are kept by the AI research team.'},
 [H('H1','Wang Fang',{'gpu_hours':96,'queue':'research-b','quota_ref':'Q-26-41'},['E-55'],'Provide the current quota, queue and reference for E-55.')],
 {'experiment':'E-55','gpu_hours':120,'queue':'research-a','quota_ref':'Q-OLD-12'},
 {'experiment':'E-55','gpu_hours':96,'queue':'research-b','quota_ref':'Q-26-41'},
 ['AI research team maps to the AI Researcher title.'],'Planning note is outdated; current quota record held by AI research.',
 [D('Mike Chen','You operate the inference cluster but do not allocate research quotas. If asked, say research quotas are kept by the research side of the AI team.')])
must('m-low-customer-mailing','Low',4,[0,1,0,0],'sales',['info-approval'],'aligned',
 P('Prepare the customer mailing request for the Q4 upgrade notice to enterprise accounts.',['segment_id','recipient_count','send_date','authorization_ref']),
 {'mailer.md':'Upgrade notice to enterprise customers, send date 2026-11-12. Last quarter used segment SEG-Q3-ENT (420 recipients) with approval APR-Q3.',
  'mailing-policy.md':'Customer mailings use the current account segment from the Sales Director, who also approves sends to enterprise accounts. Approvals cite the segment and recipient count.'},
 [H('H1','Mark Johnson',{'segment_id':'SEG-Q4-ENT','recipient_count':455},['upgrade','enterprise'],'Provide the current enterprise segment and count.'),
  H('H2','Mark Johnson',{'authorization_ref':'APR-Q4-77'},['SEG-Q4-ENT','455'],'Approve only when the current segment and count are cited.',['H1'])],
 {'segment_id':'SEG-Q3-ENT','recipient_count':420,'send_date':'2026-11-12','authorization_ref':'APR-Q3'},
 {'segment_id':'SEG-Q4-ENT','recipient_count':455,'send_date':'2026-11-12','authorization_ref':'APR-Q4-77'},
 ['Policy names the Sales Director.'],'Last quarter segment/approval are visible but stale; current values and approval held by Sales.')
must('m-low-policy-citation','Low',8,[1,0,0,0],'compliance',['single-information'],'aligned',
 P('Prepare the compliance checklist entry citing the remote-work policy.',['policy','version','effective_date','url_slug']),
 {'checklist.md':'Remote-work policy cited as v3.1, effective 2026-01-01, slug remote-work-v3. Checklist copied from last year.',
  'wiki-policy.md':'The Documentation Engineer maintains published policy versions on the wiki.'},
 [H('H1','Priya Sharma',{'version':'v4.0','effective_date':'2026-10-01','url_slug':'remote-work-v4'},['remote-work'],'Provide the current published version, effective date and slug.')],
 {'policy':'remote-work','version':'v3.1','effective_date':'2026-01-01','url_slug':'remote-work-v3'},
 {'policy':'remote-work','version':'v4.0','effective_date':'2026-10-01','url_slug':'remote-work-v4'},
 ['Policy names the Documentation Engineer.'],'Checklist copied from last year; current version held by documentation.')
must('m-low-regression-run','Low',4,[0,0,0,1],'quality',['referral'],'aligned',
 P('Prepare the regression run record for the Colly 3.2 build.',['build','test_plan_id','suite_size','environment']),
 {'build.md':'Colly 3.2 build. Previous run used plan TP-31 (180 cases) on environment staging-1.',
  'testing-policy.md':'Regression plans are owned by cross-team quality; component engineers do not maintain plans.'},
 [H('H1','Liu Qiang',{'test_plan_id':'TP-32','suite_size':214,'environment':'staging-3'},['Colly','3.2'],'Provide the current plan, size and environment for Colly 3.2.')],
 {'build':'Colly 3.2','test_plan_id':'TP-31','suite_size':180,'environment':'staging-1'},
 {'build':'Colly 3.2','test_plan_id':'TP-32','suite_size':214,'environment':'staging-3'},
 ['Cross-team quality maps to the QA engineer.'],'Previous plan is visible; current plan held by QA.',
 [D('Emily Zhou','You build Colly but do not own test plans. If asked, say cross-team quality owns regression plans.')])
# ---- Medium (11) ----
must('m-med-contractor-invoice','Medium',8,[1,1,0,1],'finance',['info-approval'],'aligned',
 P('Prepare the October invoice record for contractor DBX Consulting.',['vendor','hours','amount_usd','authorization_ref']),
 {'invoice.md':'DBX Consulting October invoice, rate USD 150/hour. Timesheet export from 2026-10-20 (partial month) shows 64 hours.',
  'contractor-policy.md':'Contractor hours are confirmed by the project lead who engaged the contractor; that lead approves invoices up to USD 15000. DBX supports the JanusGraph project.'},
 [H('H1','Li Ming',{'hours':88},['DBX','October'],'Provide final October hours.'),
  H('H2','Li Ming',{'authorization_ref':'INV-APR-5521'},['88','13200'],'Approve when final hours and amount are cited.',['H1'])],
 {'vendor':'DBX Consulting','hours':64,'amount_usd':9600,'authorization_ref':'PENDING'},
 {'vendor':'DBX Consulting','hours':88,'amount_usd':13200,'authorization_ref':'INV-APR-5521'},
 ['JanusGraph project lead found via directory project field.'],'Partial timesheet is visible; final hours and approval held by the project lead.')
must('m-med-hiring-requisition','Medium',4,[0,1,2,1],'hr',['conditional','info-approval'],'separated-conditional',
 P('Prepare the requisition record for the Search team backend role R-77.',['role','level','salary_band','signed_by','authorization_ref']),
 {'req-draft.md':'Draft requisition R-77, backend engineer, Search team, level L3, band B3 (drafted 2026-09).',
  'hiring-policy.md':'Level and band are set by the hiring product manager. Requisitions at L5 and above are approved by the CTO; below L5, Human Resources approves. Approvals cite level and band.'},
 [H('H1','Huang Jie',{'level':'L5','salary_band':'B5'},['R-77'],'Provide the confirmed level and band for R-77.'),
  H('H2','Sarah Johnson',{'authorization_ref':'REQ-APR-310'},['L5','B5'],'Approve only with level L5 and band B5 cited.',['H1'])],
 {'role':'backend engineer','level':'L3','salary_band':'B3','signed_by':'Chen Xinyi','authorization_ref':'PENDING'},
 {'role':'backend engineer','level':'L5','salary_band':'B5','signed_by':'Sarah Johnson','authorization_ref':'REQ-APR-310'},
 ['Apply the L5 threshold to the confirmed level to choose CTO vs HR.'],'Draft level points to HR; the confirmed level changes the approver to the CTO.',
 [D('Chen Xinyi','You approve requisitions below L5 only. For L5 or above, say the CTO approves; issue nothing.')])
must('m-med-conference-travel','Medium',8,[1,1,2,1],'finance',['delegation','info-approval'],'separated-delegation',
 P('Prepare the travel request for the AI team attending NeurIPS.',['travelers','total_usd','budget_code','signed_by','authorization_ref']),
 {'trip.md':'Planning estimate (2026-09-05): 2 travelers, USD 6400 total, budget AI-TR-25.',
  'travel-policy.md':'Traveler lists and budgets are confirmed by the AI research budget holder. Conference travel is approved by the Finance Director.',
  'out-of-office.md':'Out of office 2026-10-26 to 2026-11-13: David Wong (Finance Director). Acting finance approver: Chen Xinyi.'},
 [H('H1','Wang Fang',{'travelers':3,'total_usd':9100,'budget_code':'AI-TR-26'},['NeurIPS'],'Provide the confirmed travelers, total and budget code.'),
  H('H2','Chen Xinyi',{'authorization_ref':'TRV-APR-418'},['3','9100','AI-TR-26'],'As acting finance approver, approve only with confirmed travelers, total and budget cited.',['H1'])],
 {'travelers':2,'total_usd':6400,'budget_code':'AI-TR-25','signed_by':'David Wong','authorization_ref':'PENDING'},
 {'travelers':3,'total_usd':9100,'budget_code':'AI-TR-26','signed_by':'Chen Xinyi','authorization_ref':'TRV-APR-418'},
 ['Out-of-office note redirects Finance Director approvals to the acting approver.'],'Planning estimate is stale; the named approver is away.',
 [D('David Wong','You are out of office until 2026-11-13. If contacted, say Chen Xinyi is the acting finance approver; issue nothing.')])
must('m-med-research-data-export','Medium',16,[2,1,0,1],'data',['info-approval'],'aligned',
 P('Prepare the export record for the Colly crawl snapshot requested by a university partner.',['snapshot_id','record_count','contains_personal_data','authorization_ref']),
 {'request.md':'University partner requests the Colly crawl snapshot. Catalog entry from 2026-08 lists snapshot CS-0817, 1200000 records, personal data: no.',
  'data-release-policy.md':'Crawl snapshots are curated and released by the engineer responsible for the crawler framework; releases cite the current snapshot and record count.'},
 [H('H1','Emily Zhou',{'snapshot_id':'CS-1019','record_count':1480000,'contains_personal_data':False},['Colly','snapshot'],'Provide the current snapshot facts.'),
  H('H2','Emily Zhou',{'authorization_ref':'EXP-REL-77'},['CS-1019','1480000'],'Release only with the current snapshot and count cited.',['H1'])],
 {'snapshot_id':'CS-0817','record_count':1200000,'contains_personal_data':False,'authorization_ref':'PENDING'},
 {'snapshot_id':'CS-1019','record_count':1480000,'contains_personal_data':False,'authorization_ref':'EXP-REL-77'},
 ['Crawler framework engineer found via directory project Colly.'],'Catalog entry is stale; current snapshot and release held by the crawler owner.')
must('m-med-flag-rollout','Medium',4,[0,1,1,2],'engineering',['referral','info-approval'],'separated',
 P('Prepare the rollout record that moves the checkout redesign flag to 50%.',['flag_key','current_percentage','target_percentage','authorization_ref']),
 {'rollout.md':'E-commerce checkout redesign. Ticket notes from 2026-09 list flag ui.checkout.v1 at 10%. Target 50%.',
  'flag-ownership.md':'Frontend flags for the e-commerce redesign moved to the frontend team in October; the low-code platform no longer hosts them. Rollouts above 25% need sign-off from the product manager who owns the experience.',
  'product-map.md':'Storefront experience decisions are made by the product manager for search and storefront.'},
 [H('H1','Jessica Chen',{'flag_key':'ui.checkout.v2','current_percentage':20},['checkout'],'Provide the current flag key and percentage.'),
  H('H2','Huang Jie',{'authorization_ref':'FLG-APR-63'},['ui.checkout.v2','50'],'Sign off only with the current flag key and target cited.',['H1'])],
 {'flag_key':'ui.checkout.v1','current_percentage':10,'target_percentage':50,'authorization_ref':'PENDING'},
 {'flag_key':'ui.checkout.v2','current_percentage':20,'target_percentage':50,'authorization_ref':'FLG-APR-63'},
 ['Ownership note: flags moved to frontend team.','Product map: storefront decisions by the search/storefront PM.'],'Ticket notes are stale; flag state and sign-off held by two different colleagues.',
 [D('Alex Turner','The low-code platform hosted flags before October. If asked, say they moved to the frontend team.')])
must('m-med-new-hire-equipment','Medium',4,[0,1,1,1],'it-procurement',['parallel-join'],'separated',
 P('Prepare the equipment order for the Design team new hire (offer O-402).',['offer_id','start_date','laptop_model','total_usd','authorization_ref']),
 {'order.md':'Offer O-402, UX role. Standard kit list (2025): model S14 at USD 1600. Start date per offer letter 2026-11-09.',
  'equipment-policy.md':'Human Resources confirms start dates. The design lead specifies hardware for design roles. Finance approves orders citing start date and model.'},
 [H('H1','Chen Xinyi',{'start_date':'2026-11-23'},['O-402'],'Provide the confirmed start date.'),
  H('H2','Sophia Rodriguez',{'laptop_model':'P16','total_usd':2900},['O-402','UX'],'Provide the hardware specification for the design role.'),
  H('H3','David Wong',{'authorization_ref':'EQ-APR-209'},['O-402','P16','2900','2026-11-23'],'Approve only with the confirmed start date, model and total cited.',['H1','H2'])],
 {'offer_id':'O-402','start_date':'2026-11-09','laptop_model':'S14','total_usd':1600,'authorization_ref':'PENDING'},
 {'offer_id':'O-402','start_date':'2026-11-23','laptop_model':'P16','total_usd':2900,'authorization_ref':'EQ-APR-209'},
 ['Design lead maps to the UX Designer.'],'Two facts from two colleagues must be joined before Finance approves.')
must('m-med-service-credit','Medium',16,[2,1,0,0],'sales',['info-approval'],'aligned',
 P('Prepare the service credit memo for customer Northwind after the October outage (monthly fee USD 8000).',['customer','credit_percent','credit_usd','authorization_ref']),
 {'memo-draft.md':'Northwind monthly fee USD 8000. Standard SLA table (2024) lists a 5% credit for outages over 60 minutes.',
  'credit-policy.md':'Northwind current contract terms, including credit tiers, are held by the Sales Director, who approves customer credits.'},
 [H('H1','Mark Johnson',{'credit_percent':10},['Northwind'],'Provide the contract credit tier for this outage.'),
  H('H2','Mark Johnson',{'authorization_ref':'CR-APR-902'},['10','800'],'Approve the credit when percent and amount are cited.',['H1'])],
 {'customer':'Northwind','credit_percent':5,'credit_usd':400,'authorization_ref':'PENDING'},
 {'customer':'Northwind','credit_percent':10,'credit_usd':800,'authorization_ref':'CR-APR-902'},
 ['Policy names the Sales Director.'],'Generic SLA table is visible; contract-specific tier and approval held by Sales.')
must('m-med-campaign-spend','Medium',4,[0,1,2,1],'marketing',['conditional','info-approval'],'separated-conditional',
 P('Prepare the purchase request for the Q4 webinar campaign media spend.',['campaign','spend_usd','signed_by','authorization_ref']),
 {'plan.md':'Q4 webinar campaign. Early plan from 2026-09 lists USD 4200 media spend.',
  'spend-policy.md':'Campaign spend is set by marketing. Spend up to USD 5000 is approved by the Sales Director; above that, by the Finance Director.'},
 [H('H1','Jessica Lee',{'spend_usd':7300},['Q4 webinar'],'Provide the current campaign spend.'),
  H('H2','David Wong',{'authorization_ref':'MKT-APR-81'},['7300'],'Approve only with the current spend cited.',['H1'])],
 {'campaign':'Q4 webinar','spend_usd':4200,'signed_by':'Mark Johnson','authorization_ref':'PENDING'},
 {'campaign':'Q4 webinar','spend_usd':7300,'signed_by':'David Wong','authorization_ref':'MKT-APR-81'},
 ['Apply the USD 5000 threshold to the current spend.'],'Early plan falls under the Sales threshold; current spend moves approval to Finance.',
 [D('Mark Johnson','You approve campaign spend up to USD 5000 only. For more, say Finance approves; issue nothing.')])
must('m-med-security-exception','Medium',8,[1,1,1,1],'security',['parallel-join'],'separated',
 P('Prepare the security exception record for giving partner Orbit access to the /v2/test-search endpoint.',['endpoint','risk_rating','business_justification_id','authorization_ref']),
 {'request.md':'Partner Orbit requests access to /v2/test-search. Exception template from 2025 lists risk rating medium.',
  'exception-policy.md':'Risk ratings for API endpoints are assessed by the team that operates the API server. Business justification for partner access is recorded by the product manager of the affected product. The CTO approves exceptions citing both.'},
 [H('H1','Emma Lewis',{'risk_rating':'high'},['/v2/test-search'],'Provide the current risk rating.'),
  H('H2','Huang Jie',{'business_justification_id':'BJ-1188'},['Orbit'],'Provide the business justification record.'),
  H('H3','Sarah Johnson',{'authorization_ref':'SEC-EX-44'},['high','BJ-1188'],'Approve only with the current risk rating and justification cited.',['H1','H2'])],
 {'endpoint':'/v2/test-search','risk_rating':'medium','business_justification_id':'PENDING','authorization_ref':'PENDING'},
 {'endpoint':'/v2/test-search','risk_rating':'high','business_justification_id':'BJ-1188','authorization_ref':'SEC-EX-44'},
 ['API server operator and search PM found via directory.'],'Two independent records must be joined for the approval.')
must('m-med-support-renewal','Medium',8,[1,1,2,1],'it-procurement',['delegation','info-approval'],'separated-delegation',
 P('Prepare the Node-RED enterprise support renewal.',['seats','total_usd','signed_by','authorization_ref']),
 {'renewal.md':'Support seats cost USD 300 each per year. Last year renewed 20 seats.',
  'renewal-policy.md':'Seat counts are confirmed by the low-code platform team. Technical support renewals are approved by the CTO.',
  'leadership-calendar.md':'CTO travelling 2026-11-02 to 2026-11-13 without sign-off access. Designated technical deputy: Zhang Wei.'},
 [H('H1','Alex Turner',{'seats':26},['Node-RED'],'Provide the current seat count.'),
  H('H2','Zhang Wei',{'authorization_ref':'REN-APR-26'},['26','7800'],'As designated deputy, approve only with seats and total cited.',['H1'])],
 {'seats':20,'total_usd':6000,'signed_by':'Sarah Johnson','authorization_ref':'PENDING'},
 {'seats':26,'total_usd':7800,'signed_by':'Zhang Wei','authorization_ref':'REN-APR-26'},
 ['Leadership calendar redirects CTO approvals to the deputy.'],'Last year count is stale; the default approver is away.',
 [D('Sarah Johnson','You are travelling without sign-off access until 2026-11-13. Say Zhang Wei is the designated deputy; issue nothing.')])
must('m-med-log-deletion','Medium',4,[0,1,0,2],'data',['referral','info-approval'],'aligned',
 P('Prepare the deletion request for the Colly 2025 crawl logs.',['dataset','retention_class','delete_after','authorization_ref']),
 {'request.md':'Colly 2025 crawl logs. Data map from 2026-03 lists retention class R2 (12 months).',
  'data-ownership.md':'Retention classes for crawl data are set and approved by the data owner of the crawler. Crawler data ownership moved from the AI inference team to the web crawler team in July 2026.'},
 [H('H1','Emily Zhou',{'retention_class':'R3','delete_after':'2026-12-31'},['Colly','2025 logs'],'Provide the current retention class and deletion date.'),
  H('H2','Emily Zhou',{'authorization_ref':'DEL-APR-12'},['R3','2026-12-31'],'Approve deletion when class and date are cited.',['H1'])],
 {'dataset':'Colly 2025 crawl logs','retention_class':'R2','delete_after':'2026-03-31','authorization_ref':'PENDING'},
 {'dataset':'Colly 2025 crawl logs','retention_class':'R3','delete_after':'2026-12-31','authorization_ref':'DEL-APR-12'},
 ['Ownership moved to the web crawler team.','Crawler data owner = crawler framework engineer.'],'Data map is stale; ownership transfer must be followed.',
 [D('Mike Chen','Your team owned crawl data before July. If asked, say ownership moved to the web crawler team.')])
# ---- High (9) ----
must('m-high-model-release','High',16,[2,2,2,2],'ai-research',['chain3','conditional'],'separated-conditional',
 P('Prepare the release record for model checkpoint Aurora-7B.',['checkpoint','eval_report_id','safety_attestation','release_tier','mandate_reference']),
 {'release.md':'Aurora-7B. Draft from 2026-10-01 cites eval report EV-12, release tier internal, research-lead mandate RES-DRAFT-7.',
  'release-policy.md':'Evaluation reports are produced by the research owner of the model. QA attests safety only against a cited current evaluation report. Public-tier releases need an executive technical mandate citing the attestation; internal-tier releases are within the research lead mandate.',
  'release-tiers.md':'A checkpoint is public tier when its current evaluation report includes external benchmark claims.'},
 [H('H1','Wang Fang',{'eval_report_id':'EV-19','release_tier':'public','external_benchmark_claims':True},['Aurora-7B'],'Provide the current evaluation report ID and note that it includes external benchmark claims.'),
  H('H2','Liu Qiang',{'safety_attestation':'QA-SAF-191'},['EV-19'],'Attest only against EV-19.',['H1']),
  H('H3','Sarah Johnson',{'mandate_reference':'TECH-AUR-7'},['QA-SAF-191','public'],'Issue the mandate only with the attestation and public tier cited.',['H2'])],
 {'checkpoint':'Aurora-7B','eval_report_id':'EV-12','safety_attestation':'PENDING','release_tier':'internal','mandate_reference':'RES-DRAFT-7'},
 {'checkpoint':'Aurora-7B','eval_report_id':'EV-19','safety_attestation':'QA-SAF-191','release_tier':'public','mandate_reference':'TECH-AUR-7'},
 ['Tier rule applied to the current report changes the mandate holder.','Research owner and QA found via directory.'],'Three dependent private records; tier condition changes the approver.')
must('m-high-db-migration','High',16,[2,2,1,1],'service-operations',['chain3'],'separated',
 P('Prepare the RisingWave schema migration record.',['migration_id','downtime_minutes','test_signoff','authorization_ref']),
 {'plan.md':'RisingWave migration plan M-14 (2026-09) estimates 30 minutes downtime.',
  'migration-policy.md':'Migration scripts and downtime estimates are produced by the engineer who develops the streaming database core. Cross-team QA signs off against the current migration ID and downtime. The database project manager approves migrations with under 60 minutes of downtime.'},
 [H('H1','Zhang Wei',{'migration_id':'M-17','downtime_minutes':45},['RisingWave'],'Provide the current migration ID and downtime.'),
  H('H2','Liu Qiang',{'test_signoff':'QA-M17-45'},['M-17','45'],'Sign off only against M-17 and 45 minutes.',['H1']),
  H('H3','Li Ming',{'authorization_ref':'DB-APR-317'},['QA-M17-45'],'Approve only with the QA sign-off cited.',['H2'])],
 {'migration_id':'M-14','downtime_minutes':30,'test_signoff':'PENDING','authorization_ref':'PENDING'},
 {'migration_id':'M-17','downtime_minutes':45,'test_signoff':'QA-M17-45','authorization_ref':'DB-APR-317'},
 ['Streaming core engineer found via directory project RisingWave.'],'Three-step chain; each step cites the previous record.')
must('m-high-customer-data-request','High',16,[2,1,2,2],'legal-privacy',['parallel-join','conditional'],'separated-conditional',
 P("Prepare the response record for Contoso's request for all data about their account.",['account_id','data_categories','record_count','signed_by','authorization_ref']),
 {'request.md':'Contoso requests all records about their account. Old inventory (2026-05): account C-881, categories [usage logs], 12000 records.',
  'privacy-policy.md':'Account identifiers and contract scope are held by the account owner in Sales. Inventories of crawler-derived data are held by the crawler engineer. If the categories include personal data, the CTO approves the release; otherwise the account owner approves.'},
 [H('H1','Mark Johnson',{'account_id':'C-881A'},['Contoso'],'Provide the current account ID. You approve releases only when no personal data is involved; if contact names are included, say the CTO approves.'),
  H('H2','Emily Zhou',{'data_categories':['usage logs','contact names'],'record_count':15400},['Contoso'],'Provide the current inventory for Contoso.'),
  H('H3','Sarah Johnson',{'authorization_ref':'DSR-APR-55'},['C-881A','contact names','15400'],'Approve only with account, categories and count cited.',['H1','H2'])],
 {'account_id':'C-881','data_categories':['usage logs'],'record_count':12000,'signed_by':'Mark Johnson','authorization_ref':'PENDING'},
 {'account_id':'C-881A','data_categories':['usage logs','contact names'],'record_count':15400,'signed_by':'Sarah Johnson','authorization_ref':'DSR-APR-55'},
 ['Join account and inventory; personal-data rule switches approver from Sales to CTO.'],'Old inventory has no personal data; current inventory does, changing the approver.')
must('m-high-payroll-correction','High',8,[1,2,2,2],'hr-finance',['chain3','delegation'],'separated-delegation',
 P('Prepare the payroll correction for Database team on-call hours in October (rate USD 60/hour).',['hours','hr_verification_id','amount_usd','signed_by','authorization_ref']),
 {'correction.md':'Rate USD 60/hour. Preliminary report (2026-10-25) shows 30 on-call hours.',
  'payroll-policy.md':'Final on-call hours are confirmed by the team project manager. Human Resources verifies corrections citing hours. The Finance Director approves payroll corrections citing the HR verification.',
  'out-of-office.md':'David Wong (Finance Director) on leave 2026-11-01 to 2026-11-20; payroll approvals delegated to the CTO.'},
 [H('H1','Li Ming',{'hours':42},['October','on-call'],'Provide final on-call hours.'),
  H('H2','Chen Xinyi',{'hr_verification_id':'HRV-42-10'},['42'],'Verify only with final hours cited.',['H1']),
  H('H3','Sarah Johnson',{'authorization_ref':'PAY-APR-73'},['HRV-42-10','2520'],'As delegated approver, approve only with verification and amount cited.',['H2'])],
 {'hours':30,'hr_verification_id':'PENDING','amount_usd':1800,'signed_by':'David Wong','authorization_ref':'PENDING'},
 {'hours':42,'hr_verification_id':'HRV-42-10','amount_usd':2520,'signed_by':'Sarah Johnson','authorization_ref':'PAY-APR-73'},
 ['Out-of-office note redirects Finance approval to the CTO.','Team project manager found via directory.'],'Three-step chain with a delegated approver.',
 [D('David Wong','You are on leave until 2026-11-20. Say payroll approvals are delegated to the CTO; issue nothing.')])
must('m-high-incident-postmortem','High',16,[2,2,1,2],'service-operations',['chain3','referral'],'separated',
 P('Prepare the customer-facing postmortem record for incident INC-221 (search outage on 2026-10-21).',['incident_id','root_cause_code','duration_minutes','publication_reference']),
 {'draft.md':'Incident INC-221. Initial triage: 35 minutes, root cause RC-NET.',
  'postmortem-policy.md':'The final timeline comes from the engineer whose crawler fed the failing index. If the index pipeline is involved, root cause codes are signed off by the engineer who develops the streaming database core. Customer-facing publication is approved by the product manager of the affected product.'},
 [H('H1','Emily Zhou',{'duration_minutes':52,'index_pipeline_involved':True},['INC-221'],'Provide final duration and note that the index pipeline was involved.'),
  H('H2','Zhang Wei',{'root_cause_code':'RC-IDX-07'},['INC-221','52'],'Sign off root cause only with incident and final duration cited.',['H1']),
  H('H3','Huang Jie',{'publication_reference':'PM-PUB-221'},['RC-IDX-07','52'],'Approve publication only with root cause and duration cited.',['H2'])],
 {'incident_id':'INC-221','root_cause_code':'RC-NET','duration_minutes':35,'publication_reference':'PENDING'},
 {'incident_id':'INC-221','root_cause_code':'RC-IDX-07','duration_minutes':52,'publication_reference':'PM-PUB-221'},
 ['Map crawler, streaming core and affected product to people via directory.'],'Three-step chain; first triage values are wrong.',
 [D('Li Ming','You manage the graph database, not the index pipeline. If asked, say the streaming database engineer signs off index root causes.')])
must('m-high-plugin-purchase','High',16,[2,1,2,2],'it-procurement',['parallel-join','delegation','conditional'],'separated-delegation',
 P('Prepare the purchase record for LowCodeX plugin licenses.',['seats','total_usd','security_review_id','signed_by','authorization_ref']),
 {'quote.md':'LowCodeX plugin: USD 450 per seat per year.','draft.md':'Early request (2026-09) for 18 seats.',
  'purchase-policy.md':'Seat counts are confirmed by the low-code platform team. Plugins that handle customer data need a security review by the team that operates the API server. Purchases over USD 10000 are approved by Finance; otherwise by the CTO.',
  'out-of-office.md':'Finance Director away 2026-11-02 to 2026-11-16; acting finance approver: Chen Xinyi.'},
 [H('H1','Alex Turner',{'seats':28},['LowCodeX'],'Provide the confirmed seat count.'),
  H('H2','Emma Lewis',{'security_review_id':'SR-LCX-4'},['LowCodeX'],'Provide the completed security review ID.'),
  H('H3','Chen Xinyi',{'authorization_ref':'PO-APR-912'},['28','12600','SR-LCX-4'],'As acting finance approver, approve only with seats, total and review cited.',['H1','H2'])],
 {'seats':18,'total_usd':8100,'security_review_id':'PENDING','signed_by':'Sarah Johnson','authorization_ref':'PENDING'},
 {'seats':28,'total_usd':12600,'security_review_id':'SR-LCX-4','signed_by':'Chen Xinyi','authorization_ref':'PO-APR-912'},
 ['Threshold on current amount selects Finance; out-of-office selects acting approver.'],'Draft amount falls under the CTO threshold; current amount and absence change the approver.',
 [D('Sarah Johnson','You approve purchases up to USD 10000 only. For more, say Finance approves; issue nothing.'),D('David Wong','You are away until 2026-11-16. Say Chen Xinyi is the acting finance approver; issue nothing.')])
must('m-high-price-change','High',8,[1,2,2,1],'sales',['chain3','conditional'],'separated-conditional',
 P('Prepare the price change record for the Search Pro plan.',['list_price_usd','discount_percent','margin_check_id','signed_by','authorization_ref']),
 {'draft.md':'Search Pro proposed list price USD 49, discount 15% (draft 2026-09).',
  'pricing-policy.md':'Final price and discount are set by the search product manager. Finance checks margin citing price and discount. Discounts above 20% need CTO approval; otherwise the Sales Director approves, citing the margin check.'},
 [H('H1','Huang Jie',{'list_price_usd':59,'discount_percent':25},['Search Pro'],'Provide the final price and discount.'),
  H('H2','David Wong',{'margin_check_id':'MC-59-25'},['59','25'],'Run margin check only with final price and discount cited.',['H1']),
  H('H3','Sarah Johnson',{'authorization_ref':'PRC-APR-12'},['MC-59-25','25'],'Approve only with margin check and discount cited.',['H2'])],
 {'list_price_usd':49,'discount_percent':15,'margin_check_id':'PENDING','signed_by':'Mark Johnson','authorization_ref':'PENDING'},
 {'list_price_usd':59,'discount_percent':25,'margin_check_id':'MC-59-25','signed_by':'Sarah Johnson','authorization_ref':'PRC-APR-12'},
 ['Apply the 20% discount threshold to the final discount.'],'Draft discount points to Sales; final discount moves approval to the CTO.',
 [D('Mark Johnson','You approve discounts up to 20% only. Above that, say the CTO approves; issue nothing.')])
must('m-high-access-recert','High',16,[2,1,2,2],'security',['parallel-join','delegation'],'separated-delegation',
 P('Prepare the Q4 production access recertification for the API server.',['accounts_to_keep','accounts_to_remove','hr_status_ref','authorization_ref']),
 {'access-list.md':'Snapshot (2026-08): 14 accounts with production access; removals none.',
  'recert-policy.md':'Current access lists come from the team that operates the API server. Human Resources confirms employment status. The CTO approves recertification.',
  'leadership-calendar.md':'CTO travelling 2026-11-02 to 2026-11-13 without sign-off access. Designated technical deputy: Zhang Wei.'},
 [H('H1','Emma Lewis',{'accounts_to_keep':11,'accounts_to_remove':4},['API server','Q4'],'Provide current keep/remove counts.'),
  H('H2','Chen Xinyi',{'hr_status_ref':'HRS-Q4-15'},['API server','Q4'],'Provide the employment status reference.'),
  H('H3','Zhang Wei',{'authorization_ref':'ACC-APR-44'},['11','4','HRS-Q4-15'],'As deputy, approve only with counts and HR reference cited.',['H1','H2'])],
 {'accounts_to_keep':14,'accounts_to_remove':0,'hr_status_ref':'PENDING','authorization_ref':'PENDING'},
 {'accounts_to_keep':11,'accounts_to_remove':4,'hr_status_ref':'HRS-Q4-15','authorization_ref':'ACC-APR-44'},
 ['Join two records; leadership calendar redirects CTO approval.'],'Snapshot is stale; approver is away.',
 [D('Sarah Johnson','You are travelling without sign-off access until 2026-11-13. Say Zhang Wei is the designated deputy; issue nothing.')])
must('m-high-portal-launch','High',16,[2,2,2,2],'product',['chain3','referral','delegation'],'separated-delegation',
 P('Prepare the go/no-go record for launching the API v3 documentation portal.',['docs_build_id','qa_signoff','launch_date','authorization_ref']),
 {'plan.md':'Portal launch planned for 2026-11-12 with docs build DB-301.',
  'launch-policy.md':'Docs builds are produced by the documentation engineer. QA signs off against the current build. Launch approval comes from the product manager of the API portal.',
  'product-map.md':'API portal product decisions belong to the search product manager while the API product role is vacant.',
  'out-of-office.md':'Huang Jie away 2026-11-04 to 2026-11-20; product approvals delegated to Jessica Chen.'},
 [H('H1','Priya Sharma',{'docs_build_id':'DB-318','launch_date':'2026-11-17'},['API v3 portal'],'Provide the current build and launch date.'),
  H('H2','Liu Qiang',{'qa_signoff':'QA-DB318'},['DB-318'],'Sign off only against DB-318.',['H1']),
  H('H3','Jessica Chen',{'authorization_ref':'LCH-APR-3'},['QA-DB318','2026-11-17'],'As delegated product approver, approve only with QA sign-off and date cited.',['H2'])],
 {'docs_build_id':'DB-301','qa_signoff':'PENDING','launch_date':'2026-11-12','authorization_ref':'PENDING'},
 {'docs_build_id':'DB-318','qa_signoff':'QA-DB318','launch_date':'2026-11-17','authorization_ref':'LCH-APR-3'},
 ['Product map → search PM; out-of-office → delegate.'],'Three-step chain; the mapped approver is away.',
 [D('Huang Jie','You are away until 2026-11-20. Say product approvals are delegated to Jessica Chen; issue nothing.'),D('Emma Lewis','You run the API server, not the docs portal. If asked about launch approval, say product decides.')])

# ======================= OPTIONAL-HELP (27) =======================
def Q(dim, base, full, minimum, constraints=()): return {'dimension': dim, 'baseline': base, 'full_information': full, 'minimum_improvement': minimum, 'constraints': list(constraints)}
# ---- Low (7) ----
opt('o-low-team-lunch','Low',4,[0,0,0,0],'facilities',P('Prepare the catering order for the Search team offsite lunch on 2026-11-18 (22 people).',['headcount','menu','vegetarian_meals','total_usd']),
 {'order.md':'22 attendees. Standard menu M1 at USD 25 per person; all meals regular by default. Human Resources keeps the team dietary-needs list.'},
 [H('H1','Chen Xinyi',{'vegetarian_meals':6},['Search team','lunch'],'Provide the dietary count. The standard order remains valid.')],
 {'headcount':22,'menu':'M1','vegetarian_meals':0,'total_usd':550},{'headcount':22,'menu':'M1','vegetarian_meals':6,'total_usd':550},
 ['order.md'],'Explicit: dietary list exists with HR.',Q('dietary_matched_meals',0,6,6),['HR named directly.'],'Standard order valid; dietary info improves fit at no cost.')
opt('o-low-changelog-template','Low',4,[0,0,0,0],'documentation',P('Prepare the API changelog page for v3.4.',['version','template_id','sections']),
 {'changelog.md':'API v3.4 changelog. Template T-2 (2024) has sections Summary and Changes. The Documentation Engineer maintains page templates.'},
 [H('H1','Priya Sharma',{'template_id':'T-5','sections':['Summary','Changes','Migration','Deprecations']},['changelog'],'Provide the current template. T-2 remains acceptable.')],
 {'version':'v3.4','template_id':'T-2','sections':['Summary','Changes']},{'version':'v3.4','template_id':'T-5','sections':['Summary','Changes','Migration','Deprecations']},
 ['changelog.md'],'Explicit: template is from 2024 and maintained by documentation.',Q('required_sections_covered',2,4,2),['Documentation Engineer named.'],'Old template valid; current one covers more sections.')
opt('o-low-demo-shipment','Low',4,[0,1,0,0],'sales',P('Prepare the shipping order for demo hardware to customer Fabrikam.',['customer','carrier','ship_date','delivery_days']),
 {'shipping.md':'Default carrier GroundCo, 6 business days. Ship date 2026-11-12. Fabrikam demo on 2026-11-20. Account owner for Fabrikam: Sales Director.'},
 [H('H1','Mark Johnson',{'carrier':'FastFreight','delivery_days':3},['Fabrikam'],'Provide the carrier Fabrikam receiving accepts at the same price. GroundCo remains valid.')],
 {'customer':'Fabrikam','carrier':'GroundCo','ship_date':'2026-11-12','delivery_days':6},{'customer':'Fabrikam','carrier':'FastFreight','ship_date':'2026-11-12','delivery_days':3},
 ['shipping.md'],'Implicit: 6 business days from 11-12 leaves no buffer before the 11-20 demo.',Q('buffer_business_days_before_demo',0,3,2),['Account owner named.'],'Default carrier arrives just in time; account owner knows a faster equal-price option.')
opt('o-low-staging-region','Low',16,[2,0,0,0],'cloud',P('Prepare the deployment request for the crawler staging cluster.',['region','instance_type','monthly_usd']),
 {'deploy.md':'Default: us-east, std-8, USD 1200/month. The API team manages reserved capacity.'},
 [H('H1','Emma Lewis',{'region':'us-central','monthly_usd':780},['crawler staging'],'Provide the reserved slot. On-demand us-east remains valid.')],
 {'region':'us-east','instance_type':'std-8','monthly_usd':1200},{'region':'us-central','instance_type':'std-8','monthly_usd':780},
 ['deploy.md'],'Explicit: reserved capacity managed by API team.',Q('monthly_usd',1200,780,300),['API team named.'],'On-demand valid; reserved slot cheaper.')
opt('o-low-survey-launch','Low',4,[0,0,1,1],'hr',P('Schedule the employee engagement survey.',['launch_date','close_date','reminder_count']),
 {'survey.md':'Planned launch 2026-11-23, close 2026-12-04, two reminders. Survey windows should avoid weeks with company-wide deadlines; the people team keeps the internal deadline calendar.'},
 [H('H1','Chen Xinyi',{'conflict':'payroll close and benefits enrollment week of 2026-11-23','launch_date':'2026-11-30','close_date':'2026-12-11'},['survey'],'Provide the deadline conflict and a clear window. The planned dates remain allowed.')],
 {'launch_date':'2026-11-23','close_date':'2026-12-04','reminder_count':2},{'launch_date':'2026-11-30','close_date':'2026-12-11','reminder_count':2},
 ['survey.md'],'Explicit pointer to the deadline calendar.',Q('deadline_week_overlaps',1,0,1),['People team maps to HR.'],'Planned dates valid; HR calendar avoids a deadline week.')
opt('o-low-demo-dataset','Low',8,[1,0,1,0],'sales-engineering',P('Prepare the sales demo setup for search relevance.',['dataset_id','document_count','refreshed_on']),
 {'demo.md':'Demo dataset DS-DEMO-2 (420000 documents, refreshed 2025-12-01). Crawl datasets are produced by the crawler framework team.'},
 [H('H1','Emily Zhou',{'dataset_id':'DS-DEMO-5','document_count':610000,'refreshed_on':'2026-10-15'},['demo'],'Provide the latest demo dataset. DS-DEMO-2 remains usable.')],
 {'dataset_id':'DS-DEMO-2','document_count':420000,'refreshed_on':'2025-12-01'},{'dataset_id':'DS-DEMO-5','document_count':610000,'refreshed_on':'2026-10-15'},
 ['demo.md'],'Explicit: dataset age and producing team.',Q('dataset_age_days_at_demo',339,21,200),['Crawler framework team maps to Emily via directory.'],'Old dataset valid; newer crawl improves freshness.')
opt('o-low-press-factsheet','Low',4,[0,1,0,1],'marketing',P('Prepare the press fact sheet for the OpenSearch 2.12 launch.',['headline','exec_quote_id','boilerplate_version']),
 {'factsheet.md':'Boilerplate B-2026 approved. Headline draft: "OpenSearch gets faster". Last release reused exec quote Q-0611 from 2025.','marketing-roles.md':'The Marketing Manager keeps the approved quote library.'},
 [H('H1','Jessica Lee',{'exec_quote_id':'Q-1102','quote_release':'2.12','headline':'OpenSearch 2.12 cuts query latency in half'},['2.12'],'Provide the 2.12-specific approved quote and matching headline. Q-0611 remains approved.')],
 {'headline':'OpenSearch gets faster','exec_quote_id':'Q-0611','boilerplate_version':'B-2026'},{'headline':'OpenSearch 2.12 cuts query latency in half','exec_quote_id':'Q-1102','boilerplate_version':'B-2026'},
 ['factsheet.md'],'Implicit: quote is from 2025 and not release-specific.',Q('release_specific_quote',0,1,1),['Marketing Manager named.'],'Old quote valid; release-specific quote improves accuracy.')
# ---- Medium (11) ----
opt('o-med-license-reuse','Medium',8,[1,1,1,1],'it-procurement',P('Prepare the purchase request for 10 FigmaPro seats for the frontend team.',['seats_to_buy','seats_reassigned','total_usd']),
 {'request.md':'FigmaPro USD 180 per seat per year. Request covers 10 new seats (USD 1800).','license-pool.md':'Company FigmaPro pool: 40 seats; last usage export 2026-06. The design function administers the pool.'},
 [H('H1','Sophia Rodriguez',{'idle_seats':6},['FigmaPro'],'Provide current idle seats that can be reassigned. Buying all 10 remains valid.')],
 {'seats_to_buy':10,'seats_reassigned':0,'total_usd':1800},{'seats_to_buy':4,'seats_reassigned':6,'total_usd':720},
 ['request.md','license-pool.md'],'Implicit: pool usage export is months old.',Q('total_usd',1800,720,500),['Design function maps to the UX Designer.'],'Buying all seats valid; reassigning idle seats cuts cost.')
opt('o-med-offsite-date','Medium',16,[2,1,0,1],'hr',P('Plan the AI team offsite in Toronto.',['date','venue','attendees','calendar_conflicts']),
 {'offsite.md':'Proposed 2026-11-11 (Wednesday), venue Lakeview, 12 attendees. Toronto office calendar not included in this packet. Human Resources maintains regional office calendars.'},
 [H('H1','Chen Xinyi',{'conflict':'Toronto office half-day closure on 2026-11-11','alternative_date':'2026-11-12'},['Toronto','offsite'],'Provide the conflict and a clear date. Lakeview is available both days.')],
 {'date':'2026-11-11','venue':'Lakeview','attendees':12,'calendar_conflicts':0},{'date':'2026-11-12','venue':'Lakeview','attendees':12,'calendar_conflicts':0},
 ['offsite.md'],'Implicit: regional calendar missing.',Q('true_calendar_conflicts',1,0,1),['HR named.'],'Proposed date valid; HR calendar reveals a closure.')
opt('o-med-ab-test-plan','Medium',4,[0,1,1,1],'ai-research',P('Prepare the A/B test plan for the search ranking tweak.',['sample_size','duration_days','compute_usd']),
 {'abtest.md':'Default power calculation assumes metric variance 0.30: 200000 users, 14 days, USD 2800 compute. Variance estimates from earlier ranking experiments are kept by AI research.'},
 [H('H1','Wang Fang',{'variance':0.18,'sample_size':120000,'duration_days':9,'compute_usd':1800},['ranking','variance'],'Provide the measured variance and resulting plan. The default plan remains valid.')],
 {'sample_size':200000,'duration_days':14,'compute_usd':2800},{'sample_size':120000,'duration_days':9,'compute_usd':1800},
 ['abtest.md'],'Implicit: default variance assumption.',Q('compute_usd',2800,1800,500),['AI research maps to AI Researcher.'],'Default plan valid; measured variance shrinks cost.')
opt('o-med-support-macro','Medium',8,[1,1,1,0],'customer-support',P('Update support macro MAC-14 for search indexing delays.',['macro_id','eta_text','workaround']),
 {'macro.md':'MAC-14 currently says "fix expected in a future release" and lists no workaround. Product timelines are set by product managers.'},
 [H('H1','Huang Jie',{'eta_text':'Fixed in 2.12 on 2026-11-19','workaround':'Reindex from the console'},['indexing delay'],'Provide the ETA and workaround. The current macro text remains acceptable.')],
 {'macro_id':'MAC-14','eta_text':'fix expected in a future release','workaround':'none'},{'macro_id':'MAC-14','eta_text':'Fixed in 2.12 on 2026-11-19','workaround':'Reindex from the console'},
 ['macro.md'],'Implicit: vague ETA.',Q('actionable_fields',0,2,2),['Search PM via directory.'],'Vague macro valid; PM provides ETA and workaround.')
opt('o-med-batch-schedule','Medium',16,[2,1,1,1],'ai-infrastructure',P('Schedule the nightly embedding batch job.',['start_utc','gpu_type','monthly_usd']),
 {'batch.md':'Current plan: start 18:00 UTC on A100, USD 3600/month. The inference engineering team operates the GPU cluster.'},
 [H('H1','Mike Chen',{'start_utc':'02:00','discount':0.4,'monthly_usd':2160},['embedding batch'],'Provide the off-peak window and price. 18:00 remains allowed.')],
 {'start_utc':'18:00','gpu_type':'A100','monthly_usd':3600},{'start_utc':'02:00','gpu_type':'A100','monthly_usd':2160},
 ['batch.md'],'Implicit: peak-hour start.',Q('monthly_usd',3600,2160,500),['Inference engineering maps to Mike Chen.'],'Peak schedule valid; off-peak cheaper.')
opt('o-med-brochure-translation','Medium',4,[0,2,0,1],'marketing',P('Prepare the localization quote for the product brochure (French and German).',['vendor','words','total_usd']),
 {'brochure.md':'Brochure: 6000 words, two languages.','vendors.md':'LinguaPro list rate USD 0.12 per word.','marketing-log.md':'September: Marketing Manager renewed the LinguaPro framework agreement.'},
 [H('H1','Jessica Lee',{'framework_rate':0.08,'total_usd':960},['LinguaPro'],'Provide the framework rate. List rate remains valid.')],
 {'vendor':'LinguaPro','words':12000,'total_usd':1440},{'vendor':'LinguaPro','words':12000,'total_usd':960},
 ['vendors.md','marketing-log.md'],'Combine list-rate quote with the framework renewal note.',Q('total_usd',1440,960,300),['Marketing Manager named.'],'List rate valid; framework rate cheaper.')
opt('o-med-backup-window','Medium',4,[0,1,1,2],'service-operations',P('Configure the nightly backup for the JanusGraph cluster.',['window_utc','retention_days','storage_tb']),
 {'backup.md':'Default: 01:00 UTC, 30-day retention, estimated 12 TB. The graph database project keeps maintenance calendars and retention requirements for its clusters.'},
 [H('H1','Li Ming',{'maintenance':'Tuesdays 01:00-02:00 UTC','window_utc':'03:00','required_retention_days':14,'storage_tb':6},['JanusGraph','backup'],'Provide maintenance window and retention requirement. Defaults remain allowed.')],
 {'window_utc':'01:00','retention_days':30,'storage_tb':12},{'window_utc':'03:00','retention_days':14,'storage_tb':6},
 ['backup.md'],'Implicit: defaults not checked against project calendar.',{'dimensions':['maintenance_overlaps','storage_tb'],'baseline':[1,12],'full_information':[0,6],'minimum_improvement':[1,3]},['Graph database project lead via directory.'],'Defaults valid; project info removes overlap and halves storage.')
opt('o-med-usability-budget','Medium',8,[1,1,1,1],'design',P('Prepare the budget for 15 usability interviews.',['participants','external_recruits','incentive_total_usd']),
 {'research.md':'Default: recruit all 15 externally at USD 100 each (USD 1500). The design team maintains research panels.'},
 [H('H1','Sophia Rodriguez',{'panel_credits':10},['usability'],'Provide panel credits. External recruiting remains valid.')],
 {'participants':15,'external_recruits':15,'incentive_total_usd':1500},{'participants':15,'external_recruits':5,'incentive_total_usd':500},
 ['research.md'],'Implicit: panels exist.',Q('incentive_total_usd',1500,500,300),['Design team maps to UX Designer.'],'External recruiting valid; panel credits cut cost.')
opt('o-med-partner-crawl','Medium',16,[2,1,1,1],'data',P('Configure the crawl of partner site docs.partner.example.',['rate_limit_rps','user_agent','est_hours']),
 {'crawl.md':'Default polite rate 2 requests/second with agent tac-crawler; estimated 40 hours. Some partners allowlist our crawler; the crawler framework team tracks allowlists.'},
 [H('H1','Emily Zhou',{'rate_limit_rps':10,'user_agent':'tac-crawler-partner','est_hours':8},['docs.partner.example'],'Provide the allowlisted settings. Default remains allowed.')],
 {'rate_limit_rps':2,'user_agent':'tac-crawler','est_hours':40},{'rate_limit_rps':10,'user_agent':'tac-crawler-partner','est_hours':8},
 ['crawl.md'],'Implicit: allowlists exist.',Q('est_hours',40,8,10),['Crawler framework via directory.'],'Default valid; allowlist speeds crawl.')
opt('o-med-renewal-quote','Medium',4,[0,2,1,1],'sales',P('Prepare the renewal quote for customer Litware.',['term_years','annual_usd','total_usd']),
 {'pricing.md':'Standard one-year renewal for Litware: USD 24000.','account-notes.md':'Last quarter Litware procurement asked about three-year budgeting cycles.','commercial-policy.md':'Multi-year commercial terms are set by the account owner.'},
 [H('H1','Mark Johnson',{'term_years':3,'annual_usd':21600,'total_usd':64800},['Litware'],'Provide multi-year terms. One-year renewal remains valid.')],
 {'term_years':1,'annual_usd':24000,'total_usd':24000},{'term_years':3,'annual_usd':21600,'total_usd':64800},
 ['account-notes.md','commercial-policy.md'],'Combine customer interest note with multi-year policy.',Q('annual_usd',24000,21600,1000),['Account owner maps to Sales Director.'],'One-year quote valid; multi-year lowers annual price.')
opt('o-med-browser-matrix','Medium',8,[1,1,2,1],'quality',P('Prepare the browser test matrix for the e-commerce redesign.',['browsers','devices','cell_count']),
 {'matrix.md':'Matrix from 2024: 6 browsers x 4 devices = 24 cells.','test-standards.md':'Supported-browser lists are published per product by whoever owns cross-team testing.','org-notes.md':'Cross-team testing is owned by quality assurance.'},
 [H('H1','Liu Qiang',{'browsers':4,'deprecated':['IE-mode','Legacy Edge']},['e-commerce redesign'],'Provide the current supported list. The 2024 matrix remains acceptable.')],
 {'browsers':6,'devices':4,'cell_count':24},{'browsers':4,'devices':4,'cell_count':16},
 ['matrix.md'],'Implicit: matrix is from 2024.',Q('cell_count',24,16,4),['Two docs map testing ownership to QA.'],'Old matrix valid; current list reduces cells.')
# ---- High (9) ----
opt('o-high-sales-kickoff','High',16,[2,2,2,2],'sales',P('Plan the 2027 sales kickoff for 60 people.',['venue','start_date','nightly_rate_usd','total_usd']),
 {'event.md':'60 attendees, two nights, preferred start 2027-01-20 at Hotel Bayview, standard rate USD 210 per night (total USD 25200).','venue-notes.md':'Bayview is listed as a corporate partner venue.','contracts.md':'Corporate venue agreements belong to contract group COMM.','contract-groups.md':'COMM agreements are kept by whoever leads customer-facing sales.'},
 [H('H1','Mark Johnson',{'partner_rate':165,'valid_dates':'2027-01-26 to 2027-01-28'},['Bayview','kickoff'],'Provide partner rate and valid dates. Standard booking remains valid.')],
 {'venue':'Bayview','start_date':'2027-01-20','nightly_rate_usd':210,'total_usd':25200},{'venue':'Bayview','start_date':'2027-01-26','nightly_rate_usd':165,'total_usd':19800},
 ['event.md','venue-notes.md'],'Combine partner-venue note with standard rate.',Q('total_usd',25200,19800,2000),['Venue agreement → COMM group → sales lead.'],'Standard booking valid; partner rate with date change cuts cost.')
opt('o-high-cloud-budget','High',16,[2,2,1,2],'cloud',P('Prepare the 2027 cloud budget for the API server.',['instance_count','commitment','annual_usd']),
 {'plan.md':'Plan: 12 on-demand instances at USD 300/month (USD 43200/year).','usage.md':'Average utilization last quarter: 35%.','pricing.md':'Committed-use discounts exist. Capacity planning is done by the team that operates the API server.'},
 [H('H1','Emma Lewis',{'instance_count':8,'commitment':'1-year committed','discount':0.3,'annual_usd':20160},['API server','2027'],'Provide rightsized count and commitment. Current plan remains valid.')],
 {'instance_count':12,'commitment':'on-demand','annual_usd':43200},{'instance_count':8,'commitment':'1-year committed','annual_usd':20160},
 ['usage.md','pricing.md'],'Combine low utilization with discount availability.',Q('annual_usd',43200,20160,5000),['API server operator via directory.'],'Plan valid; rightsizing plus commitment halves cost.')
opt('o-high-interview-panel','High',8,[1,2,2,2],'hr',P('Prepare the interview panel plan for six backend candidates.',['panel_size','certified_interviewers','training_cost_usd']),
 {'panel.md':'Four interviewers per loop. Interviewer list attached: 6 names, none marked certified; training costs USD 300 each (USD 1800).','interview-policy.md':'Trained interviewer pools are tracked by the group that runs recruiting.','org-notes.md':'Recruiting is run by the people group.'},
 [H('H1','Chen Xinyi',{'certified_on_list':4},['backend','interviewers'],'Provide how many listed interviewers are certified. Training everyone remains allowed.')],
 {'panel_size':4,'certified_interviewers':0,'training_cost_usd':1800},{'panel_size':4,'certified_interviewers':4,'training_cost_usd':600},
 ['panel.md','interview-policy.md'],'Combine missing certification marks with tracked pools.',Q('training_cost_usd',1800,600,600),['Recruiting → people group → HR.'],'Training all valid; certified pool cuts cost.')
opt('o-high-launch-announcement','High',16,[2,1,2,2],'product',P('Plan the OpenSearch 2.12 launch date and announcement.',['launch_date','channels','partner_co_announce']),
 {'launch.md':'Target 2026-11-19; channels blog and email.','partner-program.md':'Partners may co-announce launches.','product-map.md':'Partner co-launch commitments are owned by the product manager for the product.'},
 [H('H1','Huang Jie',{'partner_window':'2026-11-24','extra_channels':['partner blog','partner newsletter']},['2.12','partner'],'Provide partner co-announce window. Solo launch remains valid.')],
 {'launch_date':'2026-11-19','channels':['blog','email'],'partner_co_announce':False},{'launch_date':'2026-11-24','channels':['blog','email','partner blog','partner newsletter'],'partner_co_announce':True},
 ['partner-program.md'],'Implicit: partner option exists.',Q('announcement_channels',2,4,2),['Product map → search PM.'],'Solo launch valid; partner co-announce doubles reach.')
opt('o-high-stream-cluster','High',16,[2,2,2,1],'data',P('Provision capacity for the new analytics stream.',['cluster','new_nodes','monthly_usd']),
 {'request.md':'New cluster sa-1 with 6 nodes at USD 900 each (USD 5400/month).','infra-report.md':'Existing streaming clusters run below 50% utilization at night.','ownership.md':'Capacity sharing on streaming clusters requires the engineer who develops the streaming database core.'},
 [H('H1','Zhang Wei',{'cluster':'sw-2','new_nodes':2,'monthly_usd':1800},['analytics stream'],'Provide the shared option. A new cluster remains valid.')],
 {'cluster':'sa-1','new_nodes':6,'monthly_usd':5400},{'cluster':'sw-2','new_nodes':2,'monthly_usd':1800},
 ['infra-report.md','ownership.md'],'Combine spare capacity with sharing rule.',Q('monthly_usd',5400,1800,1000),['Streaming core engineer via directory.'],'New cluster valid; sharing cuts cost.')
opt('o-high-security-training','High',8,[1,2,2,2],'security',P('Plan the Q1 security awareness training.',['modules','staff_trained','seat_cost_usd']),
 {'training.md':'Default: full course for all 120 staff at USD 40 each (USD 4800).','policy.md':'Targeted training is allowed when risk data supports it.','results-note.md':'Phishing simulation results are held by the team that runs API security testing.'},
 [H('H1','Emma Lewis',{'failing_groups':['Sales','HR'],'staff':30},['phishing','Q1'],'Provide failing groups and size. Full course remains valid.')],
 {'modules':['full'],'staff_trained':120,'seat_cost_usd':4800},{'modules':['phishing'],'staff_trained':30,'seat_cost_usd':1200},
 ['policy.md','results-note.md'],'Combine targeting rule with existing results.',Q('seat_cost_usd',4800,1200,1000),['API security testing → Emma via directory.'],'Full course valid; targeted course cuts cost.')
opt('o-high-docs-localization','High',16,[2,2,2,2],'documentation',P('Plan the Japanese localization of the developer docs.',['words_to_translate','tm_reuse_percent','vendor_cost_usd']),
 {'scope.md':'Developer docs: 80000 words at USD 0.10 per word (USD 8000).','history.md':'Docs were partially localized for a 2025 partner pilot.','assets.md':'Translation memories are kept by whoever maintains the documentation wiki.'},
 [H('H1','Priya Sharma',{'tm_reuse_percent':45},['Japanese','translation memory'],'Provide translation-memory coverage. Full translation remains valid.')],
 {'words_to_translate':80000,'tm_reuse_percent':0,'vendor_cost_usd':8000},{'words_to_translate':44000,'tm_reuse_percent':45,'vendor_cost_usd':4400},
 ['history.md','assets.md'],'Combine 2025 pilot with TM ownership.',Q('vendor_cost_usd',8000,4400,1000),['Wiki maintainer → Documentation Engineer.'],'Full translation valid; TM reuse cuts cost.')
opt('o-high-eval-budget','High',16,[2,2,2,1],'ai-research',P('Plan the benchmark evaluation of Aurora-7B.',['benchmarks_to_run','gpu_hours','cost_usd']),
 {'eval-plan.md':'Full suite of 12 benchmarks, 300 GPU hours at USD 3/hour (USD 900).','notes.md':'Several benchmarks were run on the same base model last month.','ownership.md':'Cached evaluation results are kept by the research owner of each model line.'},
 [H('H1','Wang Fang',{'cached_benchmarks':5},['Aurora-7B','eval'],'Provide cached benchmark count. Full run remains valid.')],
 {'benchmarks_to_run':12,'gpu_hours':300,'cost_usd':900},{'benchmarks_to_run':7,'gpu_hours':170,'cost_usd':510},
 ['notes.md','ownership.md'],'Combine prior runs with caching rule.',Q('cost_usd',900,510,200),['Research owner of model line via directory.'],'Full run valid; cache reuse cuts cost.')
opt('o-high-floor-move','High',8,[1,2,1,2],'facilities',P('Plan desk allocation for the Floor 4 move.',['desks','accessible_desks','move_date']),
 {'move.md':'Floor 4: 40 desks, move on 2026-12-05 (Saturday). Accessibility needs are confidential; aggregate counts may be shared by the custodian of employee accommodations.','building.md':'Elevator maintenance scheduled on 2026-12-05.'},
 [H('H1','Chen Xinyi',{'accessible_desks':3},['Floor 4'],'Provide aggregate accessible-desk count. The plan remains valid without it.')],
 {'desks':40,'accessible_desks':0,'move_date':'2026-12-05'},{'desks':40,'accessible_desks':3,'move_date':'2026-12-12'},
 ['move.md','building.md'],'Combine accessibility note with elevator maintenance on move date.',{'dimensions':['accessibility_conflicts'],'baseline':[2],'full_information':[0],'minimum_improvement':[2]},['Accommodations custodian → HR.'],'Plan valid; HR info plus date change removes conflicts.')

# ======================= post-process (mirrors create_blueprints.py) =======================
for i, b in enumerate(TASKS):
    tid = b['task_id']; d = T / tid; seed = 2026102800 + i
    hidden = b.pop('hidden'); decoys = b.pop('decoys')
    nodes, edges = [], []
    for h in hidden:
        nid = h['id'].lower()
        nodes.append({'id': nid, 'admissible_recipients': [h['holder']], 'information_ids': [h['id']], 'requires': [r.lower() for r in h['_req']]})
        edges += [[r.lower(), nid] for r in h['_req']]
    for k, dz in enumerate(decoys): dz['id'] = f'D{k+1}'
    b['hidden_information'] = [{kk: vv for kk, vv in h.items() if kk != '_req'} for h in hidden] + [{kk: vv for kk, vv in dz.items() if kk != '_req'} for dz in decoys]
    owners = list(dict.fromkeys([h['holder'] for h in b['hidden_information']]))
    rng = random.Random(seed); others = [n for n in NAMES if n not in owners]; rng.shuffle(others)
    pool = owners + others[:b['N'] - len(owners)]; rng.shuffle(pool)
    assert len(pool) == b['N'], (tid, len(owners))
    b['no_contact_reference'] = b.pop('base'); b['full_information_reference'] = b.pop('full')
    b.update(version='0.2.0', instance_seed=seed, candidate_pool=pool, workflow_id=tid.split('-', 2)[-1], workflow_pair_id=None,
             pairing_note='Independent workflow; paired variants deferred.',
             source_spec={'commit': 'local', 'path': '12_Study2_Task_Redesign_20261026-1923.md', 'section': '13'},
             information_boundary='Only documents and task text are public; blueprint, references and scenarios are experimenter/NPC-private.',
             runtime_classification_status='design_proposed_pending_task_evaluator',
             generated_by='tools/create_blueprints_batch2.py (Task Evaluator session, per user request 2026-10-26)')
    b['public_packet_path'] = 'Documents/Study21V2/' + tid
    b['output_contract'] = {'path': '/workspace/deliverable.json', 'format': 'JSON', 'fields': {k: type(v).__name__ for k, v in b['full_information_reference'].items()},
        'equivalences': ['Numeric values may be represented with equivalent decimal precision.', 'JSON object key order is immaterial.', 'UTC times use HH:MM.',
                         'IDs are stable identifiers, not arbitrary paraphrases.', 'List fields are order-insensitive multisets.'], 'grading_implemented': False}
    b['gold_dag'] = {'nodes': nodes, 'edges': edges}
    dep = {}
    for nd in nodes: dep[nd['id']] = 1 + max([dep[x] for x in nd['requires']] or [0])
    b['dependency_depth'] = max(dep.values()); b['difficulty_score'] = sum(b['feature_scores'])
    if b['help_class'] == 'Must-help':
        exp_d = {1: 0, 2: 1, 3: 2}[b['dependency_depth']]
        assert b['feature_scores'][1] == exp_d, (tid, 'depth feature', b['dependency_depth'])
    exp_n = {4: 0, 8: 1, 16: 2}[b['N']]; assert b['feature_scores'][0] == exp_n, (tid, 'N feature')
    D_ = b['difficulty_score']; lvl = 'Low' if D_ <= 2 else ('Medium' if D_ <= 5 else 'High')
    assert lvl == b['target_level'], (tid, D_, b['target_level'])
    if b['help_class'] == 'Must-help' and lvl == 'High': assert b['N'] >= 9 or b['dependency_depth'] >= 3, tid
    dump(d / 'blueprint.json', b)
    meta = {k: b[k] for k in ['task_id', 'version', 'help_class', 'target_level', 'domain', 'N', 'feature_scores', 'difficulty_score', 'dependency_depth', 'instance_seed',
                              'candidate_pool', 'workflow_id', 'workflow_pair_id', 'source_spec', 'output_contract', 'runtime_classification_status']}
    meta.update(feature_names=['candidate_pool', 'dependency_depth', 'knowledge_authority_separation', 'inference_type'] if b['help_class'] == 'Must-help' else ['candidate_pool', 'cue_salience', 'holder_inference', 'integration_effort'],
        separation=b.get('separation') or 'not_applicable', structure=b.get('structure') or 'optional_information', cue=b['cue'], quality=b.get('quality'),
        inference_evidence=b['inference_evidence'], candidate_pool_semantics='relevant directory + configured task NPCs; other TAC accounts remain visible',
        profile_conditions=['R0', 'R1'], default_profile='R1', hidden_information_ids=[h['id'] for h in b['hidden_information']], gold_dag=b['gold_dag'],
        services=['owncloud', 'rocketchat'], npc_backend='official TAC Sotopia LLM NPC; not live-tested',
        runtime={'platform': 'linux/amd64', 'tac_commit': TAC_COMMIT, 'execution_target': 'OpenHands CodeActAgent via TAC; integration not yet executed', 'model': None, 'model_calls': 0},
        verification={'independent_task_evaluator': 'pending', 'human_review': 'pending', 'live_npc_compliance': 'not_tested', 'openhands_rollout': 'not_run'},
        known_limitations=['Structural labels are design claims.', 'LLM NPC prerequisite compliance needs live validation.', 'Single fixed instance.', 'Shared service reset/isolation required before episodes.'])
    dump(d / 'metadata.json', meta)
    dump(d / 'references/no_contact.json', b['no_contact_reference']); dump(d / 'references/full_information.json', b['full_information_reference'])
    (d / 'references/walkthrough.md').write_text('# Design reference (not an evaluation)\n\n' + b['classification_rationale'] + '\n\nFull-information route:\n' +
        ''.join(f"- {nd['id']}: obtain {nd['information_ids']} from {nd['admissible_recipients']}; prerequisites {nd['requires']}.\n" for nd in nodes) +
        '\nInference evidence:\n' + ''.join('- ' + v + '\n' for v in b['inference_evidence']), encoding='utf-8')
print('Created', len(TASKS), 'blueprints')
