import json, pathlib, html, sys
R = pathlib.Path(__file__).resolve().parents[1]
out = R / 'evaluation' / 'sample_review'
out.mkdir(parents=True, exist_ok=True)
def esc(s): return html.escape(str(s))
def render(tid):
    d = R / 'templates' / tid
    b = json.loads((d / 'blueprint.json').read_text(encoding='utf-8'))
    task = (d / 'tac' / 'task.md').read_text(encoding='utf-8')
    sc = json.loads((d / 'tac' / 'scenarios.json').read_text(encoding='utf-8'))
    p = [f'<h1>{esc(tid)}</h1>',
         f'<p><b>Class:</b> {esc(b["help_class"])} &nbsp; <b>Level:</b> {esc(b["target_level"])} &nbsp; <b>N:</b> {b["N"]} &nbsp; <b>Depth:</b> {b["dependency_depth"]} &nbsp; <b>Features:</b> {b["feature_scores"]} &nbsp; <b>D:</b> {b["difficulty_score"]} &nbsp; <b>Version:</b> {esc(b["version"])}</p>',
         '<h2>1. What the agent sees</h2><h3>task.md</h3>', f'<pre>{esc(task)}</pre>', '<h3>Work packet documents (OwnCloud)</h3>']
    for cond in ('R0', 'R1'):
        p.append(f'<details{" open" if cond=="R1" else ""}><summary><b>{cond} documents</b></summary>')
        for f in sorted((d / 'tac' / f'documents_{cond}').glob('*.md')):
            p.append(f'<h4>{esc(f.name)}</h4><pre>{esc(f.read_text(encoding="utf-8"))}</pre>')
        p.append('</details>')
    p.append('<h2>2. Hidden information (only NPCs know)</h2><table><tr><th>ID</th><th>Holder</th><th>Facts</th><th>Context the agent must supply</th><th>Release rule</th></tr>')
    for h in b['hidden_information']:
        p.append(f'<tr><td>{esc(h["id"])}</td><td>{esc(h["holder"])}</td><td><code>{esc(json.dumps(h["facts"], ensure_ascii=False))}</code></td><td>{esc(h.get("required_context"))}</td><td>{esc(h["release_rule"])}</td></tr>')
    p.append('</table>')
    p.append('<h2>3. Gold path (DAG)</h2><ol>' + ''.join(f'<li><b>{esc(n["id"])}</b> → ask {esc(n["admissible_recipients"])}; requires {esc(n["requires"])}</li>' for n in b['gold_dag']['nodes']) + '</ol>')
    p.append('<h2>4. Reference solutions</h2><table><tr><th>Field</th><th>No-contact (V only)</th><th>Full information</th></tr>')
    nc, fi = b['no_contact_reference'], b['full_information_reference']
    for k in fi:
        diff = ' style="background:#fde2e2"' if nc.get(k) != fi[k] else ''
        p.append(f'<tr{diff}><td>{esc(k)}</td><td>{esc(nc.get(k))}</td><td>{esc(fi[k])}</td></tr>')
    p.append('</table><p><i>Highlighted rows differ.</i></p>')
    p.append(f'<h2>5. Design claims</h2><p><b>Rationale:</b> {esc(b["classification_rationale"])}</p><p><b>Cue:</b> {esc(b.get("cue"))}</p><p><b>Quality:</b> {esc(b.get("quality"))}</p><p><b>Inference evidence:</b></p><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in b['inference_evidence']) + '</ul>')
    p.append('<h2>6. Revisions from evaluator</h2><ul>' + ''.join(f'<li>{esc(r["change"])}</li>' for r in b.get('revision_log', [])) + '</ul>')
    p.append('<h2>7. NPC scenarios (all candidates)</h2><table><tr><th>Name</th><th>extra_info</th><th>strategy_hint</th></tr>')
    for n, v in sc.items():
        p.append(f'<tr><td>{esc(n)}</td><td><pre>{esc(v["extra_info"])}</pre></td><td>{esc(v["strategy_hint"])}</td></tr>')
    p.append('</table>')
    css = '<style>body{font-family:Segoe UI,Arial;max-width:1100px;margin:auto;padding:16px;background:#fafaf8;color:#1d1d1f}pre{white-space:pre-wrap;background:#f0f0ec;padding:8px;border-radius:6px}table{border-collapse:collapse;width:100%;font-size:13px}td,th{border:1px solid #ddd;padding:6px;vertical-align:top}th{background:#eee}</style>'
    page = f'<!doctype html><html><head><meta charset="utf-8"><title>Sample: {esc(tid)}</title>{css}</head><body>' + '\n'.join(p) + '</body></html>'
    (out / f'{tid}.html').write_text(page, encoding='utf-8')
    return out / f'{tid}.html'
for t in sys.argv[1:]: print(render(t))
