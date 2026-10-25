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
LABELS = {"R0": "Names only", "R1": "Natural-language roles", "R2": "Structured roles"}
COLORS = {"R0": "#667085", "R1": "#007C91", "R2": "#C77700"}
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

def add_text(d, x, y, text, size=9, color="#20242A", anchor="start", font="Times-Roman", angle=0):
    d.add(String(x, y, str(text), fontName=font, fontSize=size, fillColor=c(color), textAnchor=anchor, angle=angle))

def line(d, x1, y1, x2, y2, color="#C9CED4", width=.55, dash=None):
    obj=Line(x1,y1,x2,y2,strokeColor=c(color),strokeWidth=width)
    if dash: obj.strokeDashArray=dash
    d.add(obj)

def marker(d, x, y, condition, size=4):
    fill=c(COLORS[condition]); stroke=c("#FFFFFF")
    d.add(Circle(x,y,size,fillColor=fill,strokeColor=stroke,strokeWidth=.8))

def error_point(d, x, y, lo, hi, color, width=1.1, cap=3.2):
    line(d,x,y,x,y,color,width)
    d.add(Line(x,lo,x,hi,strokeColor=c(color),strokeWidth=width))
    d.add(Line(x-cap,lo,x+cap,lo,strokeColor=c(color),strokeWidth=width))
    d.add(Line(x-cap,hi,x+cap,hi,strokeColor=c(color),strokeWidth=width))

def save(d, stem):
    renderPDF.drawToFile(d, str(OUT / f"{stem}.pdf"), title=stem.replace("_"," "))
    renderSVG.drawToFile(d, str(OUT / f"{stem}.svg"))

def legend(d, x, y, size=10):
    xx=x
    for cond in CONDITIONS:
        marker(d,xx,y+3,cond,3.4)
        add_text(d,xx+8,y,LABELS[cond],size=size)
        xx += {"R0": 105, "R1": 174, "R2": 145}[cond]

def panel_means(d, rows, x, title, metric, bounds, ticks, seed, value_scale=1, panel_w=236, y0=66, y1=268):
    left=x+48; right=x+panel_w-13; top=y1; bottom=y0
    add_text(d,(left+right)/2,top+21,title,size=12,anchor="middle",font="Times-Bold")
    ymin,ymax=bounds
    for tick in ticks:
        yy=bottom+(tick-ymin)/(ymax-ymin)*(top-bottom)
        line(d,left,yy,right,yy,"#E1E4E8",.55)
        add_text(d,left-7,yy-3,f"{tick:g}",size=9,color="#4D555E",anchor="end")
    line(d,left,bottom,left,top,"#56606B",.8);line(d,left,bottom,right,bottom,"#56606B",.8)
    xpos=[left+18, (left+right)/2, right-18]
    for j,cond in enumerate(CONDITIONS):
        est,lo,hi=summarize_condition(rows,cond,metric,seed+j)
        est*=value_scale;lo*=value_scale;hi*=value_scale
        xx=xpos[j]
        yy=bottom+(est-ymin)/(ymax-ymin)*(top-bottom)
        ylo=bottom+(max(ymin,lo)-ymin)/(ymax-ymin)*(top-bottom)
        yhi=bottom+(min(ymax,hi)-ymin)/(ymax-ymin)*(top-bottom)
        error_point(d,xx,yy,ylo,yhi,COLORS[cond],2.0,7)
        marker(d,xx,yy,cond,5.2)
        add_text(d,xx,bottom-18,cond,size=10,anchor="middle",color="#343A40")

def fig1(rows):
    W,H=720,340; d=Drawing(W,H)
    legend(d,168,H-28,10)
    panel_means(d,rows,2,"First-contact validity (%)","strict_first_information_step_valid",(0,105),[0,25,50,75,100],101,value_scale=100)
    panel_means(d,rows,242,"Valid-path completion (%)","valid_path_recomputed",(0,105),[0,25,50,75,100],201,value_scale=100)
    panel_means(d,rows,482,"Total tokens per episode (×1,000)","total_tokens",(0,120),[0,30,60,90,120],301,value_scale=.001)
    add_text(d,W/2,20,"Points = condition means; bars = 95% bootstrap CIs over 14 workflow templates.",size=9,color="#555D66",anchor="middle")
    save(d,"figure_01_profile_effects")

def nice_ticks(ymax):
    if ymax<=1.1:return [0,.25,.5,.75,1]
    step=.5 if ymax<=3 else 1
    top=math.ceil(ymax/step)*step
    return [i*step for i in range(int(top/step)+1)]

def fig2(rows):
    W,H=720,470;d=Drawing(W,H);legend(d,168,H-28,10)
    panels=[
        ("Knowledge misses", "N_knowledge_miss", 0),
        ("Unauthorized approval attempts", "N_auth_recomputed", 7),
        ("Repeated requests", "N_repeat_requests", 13),
        ("Unhelpful requests", "N_unhelpful_recomputed", 19),
    ]
    positions=[(18,249),(373,249),(18,48),(373,48)]
    for (title,metric,seed),(x,ybase) in zip(panels,positions):
        stats=[summarize_condition(rows,cnd,metric,seed+i) for i,cnd in enumerate(CONDITIONS)]
        ymax=max(hi for _,_,hi in stats)
        if ymax==0:ymax=.5
        ticks=nice_ticks(ymax); ymax=ticks[-1]
        left=x+55;right=x+337;bottom=ybase+42;top=ybase+158
        add_text(d,(left+right)/2,top+18,title,size=12,anchor="middle",font="Times-Bold")
        for tick in ticks:
            yy=bottom+(tick/ymax)*(top-bottom)
            line(d,left,yy,right,yy,"#E1E4E8",.55)
            add_text(d,left-7,yy-3,f"{tick:g}",size=9,color="#4D555E",anchor="end")
        line(d,left,bottom,left,top,"#56606B",.8);line(d,left,bottom,right,bottom,"#56606B",.8)
        xpos=[left+35,(left+right)/2,right-35]
        for i,(cond,(est,lo,hi)) in enumerate(zip(CONDITIONS,stats)):
            xx=xpos[i]; yy=bottom+(est/ymax)*(top-bottom)
            ylo=bottom+(max(0,lo)/ymax)*(top-bottom); yhi=bottom+(min(ymax,hi)/ymax)*(top-bottom)
            error_point(d,xx,yy,ylo,yhi,COLORS[cond],1.3,4);marker(d,xx,yy,cond,4.2)
            add_text(d,xx,bottom-19,cond,size=10,anchor="middle",color="#343A40")
    add_text(d,W/2,18,"Means average across two fixed models and both task alignments; intervals resample workflow templates.",size=9,color="#555D66",anchor="middle")
    save(d,"figure_02_help_seeking_errors")

def contrast_by_model(rows, high, low, model):
    vals=contrast_values(rows,high,low,model=model)
    return boot_mean(vals,20264100 + MODELS.index(model) + (0 if high=="R1" else 20))

def fig3(rows):
    W,H=720,350;d=Drawing(W,H)
    panels=[
        ("Role facts vs. names (R1 - R0)","R1","R0",-75,5,[-60,-40,-20,0]),
        ("Structured vs. prose (R2 - R1)","R2","R1",-6,6,[-6,-3,0,3,6]),
    ]
    for p,(title,high,low,xmin,xmax,ticks) in enumerate(panels):
        x=8+p*356; left=x+86;right=x+342;top=267;bottom=86
        add_text(d,(left+right)/2,top+25,title,size=12,anchor="middle",font="Times-Bold")
        for tick in ticks:
            xx=left+(tick-xmin)/(xmax-xmin)*(right-left)
            line(d,xx,bottom,xx,top,"#E1E4E8",.55)
            add_text(d,xx,bottom-17,f"{tick:g}",size=9,anchor="middle",color="#4D555E")
        zero=left+(0-xmin)/(xmax-xmin)*(right-left)
        line(d,zero,bottom,zero,top,"#56606B",.85,[4,3])
        line(d,left,bottom,right,bottom,"#56606B",.8)
        models=["gpt-5.6-terra","gpt-6-luna","fixed-model average"]
        labels=["Terra","Luna","Average"]
        ys=[top-42,top-94,top-146]
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
            line(d,xl,yy,xh,yy,col,1.4)
            line(d,xl,yy-4,xl,yy+4,col,1.4)
            line(d,xh,yy-4,xh,yy+4,col,1.4)
            if shape=="circle":d.add(Circle(xx,yy,4.3,fillColor=c(col),strokeColor=c("#FFFFFF"),strokeWidth=.7))
            elif shape=="square":d.add(Rect(xx-4,yy-4,8,8,fillColor=c(col),strokeColor=c("#FFFFFF"),strokeWidth=.7))
            else:d.add(Polygon([xx,yy+5,xx-5,yy,xx,yy-5,xx+5,yy],fillColor=c(col),strokeColor=c("#FFFFFF"),strokeWidth=.7))
            add_text(d,left-9,yy-3,MODEL_LABELS.get(model,label),size=10,anchor="end",color="#343A40")
        add_text(d,(left+right)/2,43,"Difference in tokens per episode (×1,000)",size=10,color="#555D66",anchor="middle")
    add_text(d,W/2,18,"Negative values indicate fewer tokens in the higher-information condition; 95% CIs resample 14 templates.",size=9,color="#555D66",anchor="middle")
    save(d,"figure_03_token_contrasts")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=load_rows()
    fig1(rows);fig2(rows);fig3(rows)
    print(f"Generated 3 vector figure pairs from {len(rows)} episodes and 14 workflow-template clusters in {OUT}")

if __name__=="__main__":main()
