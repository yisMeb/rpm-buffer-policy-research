"""Paired descriptive comparison of archived Version 1 and corrected Version 2."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
V1=ROOT/'versions/v1/results/raw/main_runs.csv'
V2=ROOT/'versions/v2/results/raw/main_runs.csv'
OUT=ROOT/'versions/v2/results/tables'
KEY=['capacity','outage_min','rate','condition','seed','policy']
METRICS=['aoi_mean','delivery_ratio','abnormal_delivery_ratio','episode_count','episode_preservation',
         'episode_within_60s','episode_within_300s','episode_within_900s','episode_delay',
         'occupancy_mean','occupancy_peak','dropped','pending']


def main():
    a=pd.read_csv(V1).set_index(KEY).sort_index()
    b=pd.read_csv(V2).set_index(KEY).sort_index()
    assert a.index.equals(b.index)
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    rng=np.random.default_rng(2027)
    for policy in ('P1','P2','P3','P4'):
        old=a.xs(policy,level='policy'); new=b.xs(policy,level='policy')
        for metric in METRICS:
            delta=(new[metric]-old[metric]).dropna()
            seed_means=delta.groupby(level='seed').mean().to_numpy()
            boot=np.mean(seed_means[rng.integers(0,len(seed_means),(2000,len(seed_means)))],axis=1)
            rows.append(dict(policy=policy,metric=metric,v1_mean=old[metric].mean(),v2_mean=new[metric].mean(),
                             paired_mean_change=seed_means.mean(),ci_low=np.quantile(boot,.025),ci_high=np.quantile(boot,.975),
                             n_paired_cells=len(delta),n_seed_clusters=len(seed_means)))
    pd.DataFrame(rows).to_csv(OUT/'v1_v2_paired_comparison.csv',index=False)
    trade=[]
    for version,data in ((1,a),(2,b)):
        for metric in ('aoi_mean','episode_preservation','episode_within_60s','episode_within_300s','episode_within_900s','episode_delay'):
            p4=data.xs('P4',level='policy')[metric]
            for competitor in ('P2','P3'):
                other=data.xs(competitor,level='policy')[metric]
                diff=(p4-other).dropna()
                trade.append(dict(version=version,comparison=f'P4 - {competitor}',metric=metric,
                                  paired_mean=diff.groupby(level='seed').mean().mean(),n_paired_cells=len(diff)))
    pd.DataFrame(trade).to_csv(OUT/'policy_tradeoff_by_version.csv',index=False)
    print('compared',len(a),'paired Version 1 and Version 2 runs')

if __name__=='__main__':main()
