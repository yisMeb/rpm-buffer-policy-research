"""Pre-specified Version 2 sensitivity to synthetic episode assumptions."""
import csv
import itertools
import sys
from pathlib import Path
import pandas as pd
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data_generator import generate
from src.network_model import outages
from src.simulator import simulate
from src.metrics import calculate
from src.buffer_policies import POLICIES


def main():
    c=yaml.safe_load((ROOT/'config/experiments_v2.yaml').read_text())
    raw=ROOT/'versions/v2/results/raw'; raw.mkdir(parents=True,exist_ok=True)
    path=raw/'episode_sensitivity_runs.csv'
    n=0
    with path.open('w',newline='') as f:
        writer=None
        for model,capacity,minutes,rate,seed in itertools.product(c['episode_sensitivity_models'],(120,720),(15,120),(1,5),c['seeds']):
            readings=generate(c,'medium',seed,c['outage_start_s'],minutes*60,model)
            trace=outages(c['outage_start_s'],minutes*60,1)
            for policy in POLICIES:
                r=simulate(readings,trace,policy,capacity,rate,c['observation_s']+c['recovery_s'],c['reconnect_delay_s'])
                row=dict(model=model,capacity=capacity,outage_min=minutes,rate=rate,condition='medium',seed=seed,policy=policy,
                         **calculate(r,c['episode_deadlines_s'],c['observation_s']))
                if writer is None:writer=csv.DictWriter(f,fieldnames=row.keys());writer.writeheader()
                writer.writerow(row);n+=1
    d=pd.read_csv(path)
    assert ((d.generated-d.delivered-d.dropped-d.pending)==0).all()
    table=ROOT/'versions/v2/results/tables/episode_generation_sensitivity.csv'
    table.parent.mkdir(parents=True,exist_ok=True)
    d.groupby(['model','capacity','outage_min','rate','policy'])[['aoi_mean','episode_preservation','episode_within_60s','episode_within_300s','episode_within_900s']].agg(['mean','std']).to_csv(table)
    print('episode-generation sensitivity:',n,'runs')

if __name__=='__main__':main()
