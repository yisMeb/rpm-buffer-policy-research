"""Exploratory repeated-outage sensitivity study; frozen main design is unchanged."""
import csv
import itertools
import sys
from pathlib import Path
import yaml
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data_generator import generate
from src.network_model import outages
from src.simulator import simulate
from src.metrics import calculate
from src.buffer_policies import POLICIES


def main():
    c=yaml.safe_load((ROOT/'config/experiments.yaml').read_text())
    path=ROOT/'results/raw/repeated_outage_runs.csv'
    n=0
    with path.open('w',newline='') as f:
        writer=None
        for capacity,minutes,rate,seed in itertools.product((120,720),(5,15),(1,5),c['seeds']):
            readings=generate(c,'medium',seed,c['outage_start_s'],minutes*60)
            trace=outages(c['outage_start_s'],minutes*60,3)
            for policy in POLICIES:
                r=simulate(readings,trace,policy,capacity,rate,c['observation_s']+c['recovery_s'],c['reconnect_delay_s'])
                row=dict(capacity=capacity,outage_min=minutes,rate=rate,condition='medium',seed=seed,repeats=3,policy=policy,**calculate(r,c['episode_deadlines_s'],c['observation_s']))
                if writer is None:writer=csv.DictWriter(f,fieldnames=row.keys());writer.writeheader()
                writer.writerow(row);n+=1
    table=ROOT/'results/tables/repeated_outage_sensitivity.csv'
    table.parent.mkdir(parents=True,exist_ok=True)
    pd.read_csv(path).groupby(['capacity','outage_min','rate','policy'])[['aoi_mean','delivery_ratio','episode_preservation']].agg(['mean','std']).to_csv(table)
    print('repeated-outage sensitivity:',n,'runs')

if __name__=='__main__':main()
