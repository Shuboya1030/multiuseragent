"""Generate publication-style vector figures for Study 2 (v0.4).

Inputs are the trace-recomputed episode metrics. The unit resampled for all
intervals is the workflow template (14 clusters), not the episode row.
Requires ReportLab; exports vector PDF and SVG.
"""
from __future__ import annotations
import json, math, random
from collections import defaultdict
from pathlib import Path
from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Drawing, String, Line, Circle, Rect, Polygon
from reportlab.lib.colors import HexColor, Color

OUT = Path(__file__).resolve().parent
STUDY = OUT.parents[1]
DATA = STUDY / "derived" / "run_level_metrics_all.jsonl"
TASKS = STUDY / "task_blueprints_v0.4.jsonl"
CONDITIONS = ["R0", "R1", "R2"]
LABELS = {"R0": "R0 Names", "R1": "R1 Prose", "R2": "R2 Structured"}
COLORS = {"R0": "#0072B2", "R1": "#E69F00", "R2": "#009E73"}  # Okabe-Ito
MARKERS = {"R0": "circle", "R1": "square", "R2": "triangle"}
MODELS = ["gpt-5.6-terra", "gpt-6-luna"]
MODEL_LABELS = {"gpt-5.6-terra": "Terra", "gpt-6-luna": "Luna", "fixed_model_average": "Average"}
MODEL_COLORS = {"gpt-5.6-terra": "#0072B2", "gpt-6-luna": "#D55E00", "fixed_model_average": "#222222"}
N_BOOT = 20000

def load_rows():
    task_by_id = {x["task_id"]: x for x in map(json.loads, TASKS.read_text(encoding="utf-8").splitlines()) if x}
    rows = [json.loads(x) for x in DATA.read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = [r for r in rows if r.get("task_version") == "0.4" and r.get("profile_version") == "profile-0.4"
            and r.get("rep") == 0 and task_by_id.get(r.get("task_id"), {}).get("template_origin") == "previously_seen_template"]
    if len(rows) != 168:
        raise RuntimeError(f"Expected the 168-cell confirmatory set; found {len(rows)} rows.")
    for r in rows:
        r["template"] = r["task_id"].removeprefix("S2_").removesuffix("_aligned").removesuffix("_separated")
        r["total_tokens"] = int(r.get("input_tokens", 0) or 0) + int(r.get("output_tokens", 0) or 0)
    return rows

def mean(xs): return sum(xs) / len(xs) if xs else float("nan")

def cluster_values(rows, condition, metric, model=None, contrast=None):
    by = defaultdict(list)
    for r in rows:
        if model and r["model_id"] != model: continue
        if r["profile_condition"] != condition: continue
        by[r["template"]].append(float(r[metric]))
    return {k: mean(v) for k, v in by.items()}

def boot_mean(values, seed, draws=N_BOOT):
    keys = sorted(values)
    x = [values[k] for k in keys]
    estimate = mean(x)
    rng = random.Random(seed)
    samples = sorted(mean([x[rng.randrange(len(x))] for _ in x]) for _ in range(draws))
    return estimate, samples[int(.025 * draws)], samples[min(draws - 1, int(.975 * draws))]

def summarize_condition(rows, condition, metric, seed, model=None):
    return boot_mean(cluster_values(rows, condition, metric, model=model), seed)

def contrast_values(rows, high, low, model=None):
    a = cluster_values(rows, high, "total_tokens", model=model)
    b = cluster_values(rows, low, "total_tokens", model=model)
    return {k: a[k] - b[k] for k in a.keys() & b.keys()}

def ratio_tokens_per_success(rows, condition):
    # Aggregate ratio, resampled by workflow-template cluster.
    clusters = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        if r["profile_condition"] != condition: continue
        clusters[r["template"]][0] += r["total_tokens"]
        clusters[r["template"]][1] += int(bool(r.get("valid_path_recomputed")))
    keys = sorted(clusters)
    num = sum(clusters[k][0] for k in keys)
    den = sum(clusters[k][1] for k in keys)
    estimate = num / den if den else float("nan")
    rng = random.Random(8181 + CONDITIONS.index(condition))
    samples=[]
    for _ in range(N_BOOT):
        selected=[keys[rng.randrange(len(keys))] for _ in keys]
        n=sum(clusters[k][0] for k in selected); d=sum(clusters[k][1] for k in selected)
        if d: samples.append(n/d)
    samples.sort()
    return estimate, samples[int(.025*len(samples))], samples[min(len(samples)-1,int(.975*len(samples)))]

def c(hexcolor): return HexColor(hexcolor)

def add_text(d, x, y, text, size=8, color="#20242A", anchor="start", font="Helvetica", angle=0):
    d.add(String(x, y, str(text), fontName=font, fontSize=size, fillColor=c(color), textAnchor=anchor, angle=angle))

def line(d, x1, y1, x2, y2, color="#C9CED4", width=.55, dash=None):
    obj=Line(x1,y1,x2,y2,strokeColor=c(color),strokeWidth=width)
    if dash: obj.strokeDashArray=dash
    d.add(obj)

def marker(d, x, y, condition, size=3.3):
    fill=c(COLORS[condition]); stroke=c("#FFFFFF")
    kind=MARKERS[condition]
    if kind=="circle": d.add(Circle(x,y,size,fillColor=fill,strokeColor=stroke,strokeWidth=.7))
    elif kind=="square": d.add(Rect(x-size,y-size,2*size,2*size,fillColor=fill,strokeColor=stroke,strokeWidth=.7))
    else: d.add(Polygon([x,y+size+0.5,x-size-0.5,y-size,x+size+0.5,y-size],fillColor=fill,strokeColor=stroke,strokeWidth=.7))

def error_point(d, x, y, lo, hi, color, width=1.1, cap=3.2):
    line(d,x,y,x,y,color,width)
    d.add(Line(x,lo,x,hi,strokeColor=c(color),strokeWidth=width))
    d.add(Line(x-cap,lo,x+cap,lo,strokeColor=c(color),strokeWidth=width))
    d.add(Line(x-cap,hi,x+cap,hi,strokeColor=c(color),strokeWidth=width))

def save(d, stem):
    renderPDF.drawToFile(d, str(OUT / f"{stem}.pdf"), title=stem.replace("_"," "))
    renderSVG.drawToFile(d, str(OUT / f"{stem}.svg"))

def legend(d, x, y, size=8):
    xx=x
    for cond in CONDITIONS:
        marker(d,xx,y+2,cond,3)
        add_text(d,xx+7,y,LABELS[cond],size=size)
        xx+=82

def panel_means(d, rows, x, title, metric, bounds, ticks, y_label, seed, value_scale=1, fmt=".0f", panel_w=160, y0=55, y1=202):
    left=x+34; right=x+panel_w-9; top=y1; bottom=y0
    add_text(d,(left+right)/2,top+17,title,size=9,anchor="middle",font="Helvetica-Bold")
    ymin,ymax=bounds
    for tick in ticks:
        yy=bottom+(tick-ymin)/(ymax-ymin)*(top-bottom)
        line(d,left,yy,right,yy,"#E4E7EA",.45)
        add_text(d,left-5,yy-2.5,f"{tick:g}",size=8,color="#4D555E",anchor="end")
    line(d,left,bottom,left,top,"#5F6872",.7);line(d,left,bottom,right,bottom,"#5F6872",.7)
    xpos=[left+13, (left+right)/2, right-13]
    for j,cond in enumerate(CONDITIONS):
        est,lo,hi=summarize_condition(rows,cond,metric,seed+j)
        est*=value_scale;lo*=value_scale;hi*=value_scale
        xx=xpos[j]
        yy=bottom+(est-ymin)/(ymax-ymin)*(top-bottom)
        ylo=bottom+(max(ymin,lo)-ymin)/(ymax-ymin)*(top-bottom)
        yhi=bottom+(min(ymax,hi)-ymin)/(ymax-ymin)*(top-bottom)
        error_point(d,xx,yy,ylo,yhi,COLORS[cond])
        marker(d,xx,yy,cond,3.6)
        add_text(d,xx,bottom-15,cond,size=8,anchor="middle",color="#343A40")
        add_text(d,xx, min(top-10,yy+9),format(est,fmt),size=8,anchor="middle",color=COLORS[cond],font="Helvetica-Bold")

def fig1(rows):
    W,H=504,274; d=Drawing(W,H)
    legend(d,116,H-18,8)
    panel_means(d,rows,5,"First contact valid (%)","strict_first_information_step_valid",(0,100),[0,25,50,75,100],"",101,value_scale=100,fmt=".0f")
    panel_means(d,rows,173,"Valid path complete (%)","valid_path_recomputed",(0,100),[0,25,50,75,100],"",201,value_scale=100,fmt=".0f")
    panel_means(d,rows,341,"Total tokens (thousands)","total_tokens",(0,120),[0,30,60,90,120],"",301,value_scale=.001,fmt=".1f")
    add_text(d,W/2,13,"Points show condition means; whiskers show 95% workflow-template bootstrap CIs (14 templates).",size=7,color="#555D66",anchor="middle")
    save(d,"figure_01_profile_effects")

def nice_ticks(ymax):
    if ymax<=1.1:return [0,.25,.5,.75,1]
    step=.5 if ymax<=3 else 1
    top=math.ceil(ymax/step)*step
    return [i*step for i in range(int(top/step)+1)]

def fig2(rows):
    W,H=504,350;d=Drawing(W,H);legend(d,116,H-17,8)
    panels=[
        ("Knowledge misses", "N_knowledge_miss", 0),
        ("Unauthorized approval attempts", "N_auth_recomputed", 7),
        ("Repeated requests", "N_repeat_requests", 13),
        ("Unhelpful requests", "N_unhelpful_recomputed", 19),
    ]
    positions=[(18,183),(263,183),(18,35),(263,35)]
    for (title,metric,seed),(x,ybase) in zip(panels,positions):
        stats=[summarize_condition(rows,cnd,metric,seed+i) for i,cnd in enumerate(CONDITIONS)]
        ymax=max(hi for _,_,hi in stats)
        if ymax==0:ymax=.5
        ticks=nice_ticks(ymax); ymax=ticks[-1]
        left=x+37;right=x+224;bottom=ybase+27;top=ybase+112
        add_text(d,(left+right)/2,top+14,title,size=8.5,anchor="middle",font="Helvetica-Bold")
        for tick in ticks:
            yy=bottom+(tick/ymax)*(top-bottom)
            line(d,left,yy,right,yy,"#E4E7EA",.45)
            add_text(d,left-5,yy-2.5,f"{tick:g}",size=8,color="#4D555E",anchor="end")
        line(d,left,bottom,left,top,"#5F6872",.7);line(d,left,bottom,right,bottom,"#5F6872",.7)
        xpos=[left+24,(left+right)/2,right-24]
        for i,(cond,(est,lo,hi)) in enumerate(zip(CONDITIONS,stats)):
            xx=xpos[i]; yy=bottom+(est/ymax)*(top-bottom)
            ylo=bottom+(max(0,lo)/ymax)*(top-bottom); yhi=bottom+(min(ymax,hi)/ymax)*(top-bottom)
            error_point(d,xx,yy,ylo,yhi,COLORS[cond]);marker(d,xx,yy,cond,3.3)
            add_text(d,xx,bottom-14,cond,size=8,anchor="middle",color="#343A40")
            add_text(d,xx,min(top-9,yy+9),f"{est:.1f}",size=8,anchor="middle",color=COLORS[cond],font="Helvetica-Bold")
        add_text(d,(left+right)/2,ybase+7,"Mean events per episode",size=8,color="#555D66",anchor="middle")
    add_text(d,W/2,11,"Whiskers: 95% workflow-template bootstrap CIs; means average across models and both task alignments.",size=8,color="#555D66",anchor="middle")
    save(d,"figure_02_help_seeking_errors")

def contrast_by_model(rows, high, low, model):
    vals=contrast_values(rows,high,low,model=model)
    return boot_mean(vals,20264100 + MODELS.index(model) + (0 if high=="R1" else 20))

def fig3(rows):
    W,H=504,276;d=Drawing(W,H)
    panels=[
        ("Role facts vs. names (R1 - R0)","R1","R0",-75,5,[-60,-40,-20,0]),
        ("Structured vs. prose (R2 - R1)","R2","R1",-6,6,[-6,-3,0,3,6]),
    ]
    for p,(title,high,low,xmin,xmax,ticks) in enumerate(panels):
        x=12+p*250; left=x+70;right=x+238;top=219;bottom=59
        add_text(d,(left+right)/2,top+22,title,size=8.5,anchor="middle",font="Helvetica-Bold")
        for tick in ticks:
            xx=left+(tick-xmin)/(xmax-xmin)*(right-left)
            line(d,xx,bottom,xx,top,"#E4E7EA",.45)
            add_text(d,xx,bottom-14,f"{tick:g}",size=8,anchor="middle",color="#4D555E")
        zero=left+(0-xmin)/(xmax-xmin)*(right-left)
        line(d,zero,bottom,zero,top,"#6E747B",.75,[3,2])
        line(d,left,bottom,right,bottom,"#5F6872",.7)
        models=["gpt-5.6-terra","gpt-6-luna","fixed-model average"]
        labels=["Terra","Luna","Average"]
        ys=[top-28,top-72,top-116]
        for model,label,y in zip(models,labels,ys):
            if model=="fixed-model average":
                vals=contrast_values(rows,high,low,None)
                est,lo,hi=boot_mean(vals,20264140+(0 if high=="R1" else 30))
                col="#222222"; shape="diamond"
            else:
                est,lo,hi=contrast_by_model(rows,high,low,model)
                col=MODEL_COLORS[model];shape="circle" if model=="gpt-5.6-terra" else "square"
            xx=left+(est/1000-xmin)/(xmax-xmin)*(right-left)
            xl=left+(lo/1000-xmin)/(xmax-xmin)*(right-left);xh=left+(hi/1000-xmin)/(xmax-xmin)*(right-left)
            yy=y
            error_point(d,xx,yy,xl,xh,col,1.1,3)
            if shape=="circle":d.add(Circle(xx,yy,3.5,fillColor=c(col),strokeColor=c("#FFFFFF"),strokeWidth=.6))
            elif shape=="square":d.add(Rect(xx-3.3,yy-3.3,6.6,6.6,fillColor=c(col),strokeColor=c("#FFFFFF"),strokeWidth=.6))
            else:d.add(Polygon([xx,yy+4,xx-4,yy,xx,yy-4,xx+4,yy],fillColor=c(col),strokeColor=c("#FFFFFF"),strokeWidth=.6))
            add_text(d,left-7,yy-2.5,MODEL_LABELS.get(model,label),size=8,anchor="end",color="#343A40")
            add_text(d,min(right-2,max(left+2,xh+4)),yy+6,f"{est/1000:+.1f}",size=8,color=col)
        add_text(d,(left+right)/2,30,"Difference in total tokens per episode (thousands)",size=8,color="#555D66",anchor="middle")
    add_text(d,W/2,12,"Negative values mean fewer tokens in the higher-information condition; intervals resample 14 workflow templates.",size=8,color="#555D66",anchor="middle")
    save(d,"figure_03_token_contrasts")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=load_rows()
    fig1(rows);fig2(rows);fig3(rows)
    print(f"Generated 3 vector figure pairs from {len(rows)} episodes and 14 workflow-template clusters in {OUT}")

if __name__=="__main__":main()
