from pathlib import Path
import sys
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'versions/v2/results'
OUT=BASE/'figures'; OUT.mkdir(parents=True,exist_ok=True)
DATA=BASE/'processed/figure_source_data.csv'
COLORS={'P1':'#4c78a8','P2':'#f58518','P3':'#54a24b','P4':'#b279a2'}
LABELS={'P1':'No buffer','P2':'FIFO drop newest','P3':'FIFO drop oldest','P4':'Event aware'}


def font(size):
    p=Path('C:/Windows/Fonts/arial.ttf')
    return ImageFont.truetype(str(p),size) if p.exists() else ImageFont.load_default()


def chart(name,title,xlabel,ylabel,series,scatter=False):
    im=Image.new('RGB',(1200,800),'white'); draw=ImageDraw.Draw(im)
    box=(120,150,1120,680)
    draw.text((120,26),title,fill='#17202a',font=font(27))
    points=[p for values in series.values() for p in values]
    xs=[p[0] for p in points]; ys=[p[1] for p in points if np.isfinite(p[1])]
    if not xs or not ys: return
    xmin,xmax=min(xs),max(xs); ymin,ymax=min(0,min(ys)),max(ys)
    if xmax==xmin:xmax+=1
    if ymax==ymin:ymax+=1
    xpad=(xmax-xmin)*.04; xmin-=xpad; xmax+=xpad
    if ('outage duration' in xlabel.lower() or 'simulation time' in xlabel.lower()) and xmin < 0: xmin=0
    if 'ratio' in ylabel.lower() or 'preservation' in ylabel.lower() or 'episodes with' in ylabel.lower():
        ymin,ymax=0,1.05
    elif 'readings in buffer' in ylabel.lower():
        ymin,ymax=0,ymax*1.08
    else:
        pad=(ymax-ymin)*.08; ymax+=pad; ymin-=pad
    xmap=lambda x:box[0]+(x-xmin)/(xmax-xmin)*(box[2]-box[0])
    ymap=lambda y:box[3]-(y-ymin)/(ymax-ymin)*(box[3]-box[1])
    for i in range(6):
        y=box[3]-(box[3]-box[1])*i/5
        draw.line((box[0],y,box[2],y),fill='#e5e8eb',width=1)
        draw.text((20,y-10),f'{ymin+(ymax-ymin)*i/5:.2f}',fill='#333',font=font(17))
    ticks=((0,1,2) if xlabel.startswith('Model:') else [xmin+(xmax-xmin)*i/5 for i in range(6)])
    for value in ticks:
        x=xmap(value)
        draw.text((x-15,box[3]+8),f'{value:.0f}',fill='#333',font=font(17))
    draw.line((box[0],box[1],box[0],box[3],box[2],box[3]),fill='#222',width=2)
    for key, values in series.items():
        color=COLORS[key]
        values=sorted((x,y,lo,hi) for x,y,lo,hi in values if np.isfinite(y))
        coords=[(xmap(x),ymap(y)) for x,y,_,_ in values]
        if len(coords)>1 and not scatter: draw.line(coords,fill=color,width=4)
        for (x,y,lo,hi),(px,py) in zip(values,coords):
            if np.isfinite(lo) and np.isfinite(hi) and not scatter:
                draw.line((px,ymap(lo),px,ymap(hi)),fill=color,width=2)
            draw.ellipse((px-5,py-5,px+5,py+5),fill=color)
    draw.text((500,735),xlabel,fill='#222',font=font(21))
    draw.text((20,125),ylabel,fill='#222',font=font(18))
    for j,key in enumerate(series):
        xx=120+(j%2)*370; yy=75+(j//2)*26
        draw.rectangle((xx,yy,xx+18,yy+12),fill=COLORS[key])
        draw.text((xx+25,yy-5),LABELS[key],fill='#222',font=font(16))
    im.save(OUT/f'{name}.png',dpi=(180,180))
    im.save(OUT/f'{name}.pdf',resolution=180)


def grouped(d,x,metric,subset=None):
    if subset is not None:d=d.query(subset)
    g=d[d.metric==metric].groupby(['policy',x])[['mean','ci_low','ci_high']].mean().reset_index()
    return {p:[(float(r[x]),float(r['mean']),float(r.ci_low),float(r.ci_high)) for _,r in g[g.policy==p].iterrows()] for p in COLORS}


def main():
    d=pd.read_csv(DATA)
    base='capacity == 720 and rate == 1 and condition == "medium"'
    chart('01_aoi_vs_outage','Information age by outage duration','Outage duration (minutes)','Mean AoI (seconds)',grouped(d,'outage_min','aoi_mean',base))
    chart('02_delivery_vs_outage','Measurement delivery by outage duration','Outage duration (minutes)','Delivery ratio',grouped(d,'outage_min','delivery_ratio',base))
    chart('03_episode_preservation','Abnormal episode preservation','Outage duration (minutes)','Episodes with any reading delivered',grouped(d,'outage_min','episode_preservation',base))
    for deadline in (60,300,900):
        chart(f'03_deadline_{deadline}s',f'Episode delivery within {deadline} seconds',
              'Outage duration (minutes)',f'Episode preservation within {deadline} s',
              grouped(d,'outage_min',f'episode_within_{deadline}s',base))
    chart('04_episode_delay','First abnormal reading delay','Outage duration (minutes)','Delay (seconds; detected episodes)',grouped(d,'outage_min','episode_delay',base))
    occ=BASE/'raw/main_representative_occupancy.csv'
    if occ.exists():
        a=pd.read_csv(occ); series={'P4':[(float(r.time_s/60),float(r.queue_size),float('nan'),float('nan')) for _,r in a.iloc[::10].iterrows()]}
        chart('05_buffer_occupancy','Representative P4 queue occupancy','Simulation time (minutes)','Readings in buffer',series)
    subset=d.query('outage_min > 0 and metric in ["aoi_mean", "episode_preservation"]')
    g=subset.groupby(['policy','metric'])['mean'].mean().unstack()
    series={p:[(float(g.loc[p,'aoi_mean']),float(g.loc[p,'episode_preservation']),float('nan'),float('nan'))] for p in COLORS}
    chart('06_freshness_preservation','Freshness and preservation trade-off','Mean AoI (seconds)','Episode preservation',series,True)
    chart('07_capacity_sensitivity','Sensitivity to buffer capacity at 1/s','Buffer capacity (readings)','Episode preservation',grouped(d,'capacity','episode_preservation','outage_min == 120 and rate == 1 and condition == "medium"'))
    chart('08_rate_sensitivity','Sensitivity to recovery throughput','Service rate (readings/s)','Mean AoI (seconds)',grouped(d,'rate','aoi_mean','outage_min == 120 and capacity == 720 and condition == "medium"'))
    sensitivity_path=BASE/'raw/episode_sensitivity_runs.csv'
    if sensitivity_path.exists():
        alt=pd.read_csv(sensitivity_path)
        baseline=pd.read_csv(BASE/'raw/main_runs.csv')
        alt=alt.query('capacity == 120 and outage_min == 120 and rate == 1')
        baseline=baseline.query('capacity == 120 and outage_min == 120 and rate == 1 and condition == "medium"')
        for metric,name,label in (('episode_preservation','09_episode_model_preservation','Eventual episode preservation'),
                                  ('episode_within_60s','10_episode_model_60s','Episode delivery within 60 s')):
            series={}
            for policy in COLORS:
                values=[]
                for x,frame in ((0,baseline),(1,alt.query('model == "fixed_uniform"')),(2,alt.query('model == "clustered_long"'))):
                    sample=frame[frame.policy==policy][metric].dropna()
                    y=sample.mean(); error=1.96*sample.std()/np.sqrt(len(sample)) if len(sample)>1 else float('nan')
                    values.append((x,float(y),float(y-error),float(y+error)))
                series[policy]=values
            chart(name,'Episode-generation sensitivity','Model: 0 Poisson, 1 fixed, 2 clustered',label,series)
    print('generated',len(list(OUT.glob('*.png'))),'figures in PNG and PDF')

if __name__=='__main__': main()
