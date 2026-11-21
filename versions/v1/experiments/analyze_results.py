import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'results/raw/main_runs.csv'
OUT=ROOT/'results/processed'; TABLES=ROOT/'results/tables'
METRICS=['aoi_mean','aoi_p95','delivery_ratio','normal_delivery_ratio','abnormal_delivery_ratio','episode_preservation','episode_fraction','episodes_complete','episodes_lost','episode_delay','latency','overflow_losses','recovery_time']
KEY=['capacity','outage_min','rate','condition','seed']


def main():
    OUT.mkdir(parents=True,exist_ok=True); TABLES.mkdir(parents=True,exist_ok=True)
    d=pd.read_csv(RAW)
    assert ((d.generated-d.delivered-d.dropped-d.pending)==0).all()
    assert d.pending.max()==0
    assert d.groupby(KEY).policy.nunique().eq(4).all()
    def summary(group):
        return group[METRICS].agg(['mean','std','median',lambda x:x.quantile(.25),lambda x:x.quantile(.75)]).stack().reset_index()
    overall=d.groupby('policy')[METRICS].agg(['mean','std','median']).stack(level=0,future_stack=True).reset_index()
    overall.columns=['policy','metric','mean','sd','median']; overall.to_csv(TABLES/'overall_policy_comparison.csv',index=False)
    scenario=d.groupby(['capacity','outage_min','rate','condition','policy'])[METRICS].agg(['mean','std','count']).stack(level=0,future_stack=True).reset_index()
    scenario.columns=['capacity','outage_min','rate','condition','policy','metric','mean','sd','n']
    scenario['ci_low']=scenario['mean']-1.96*scenario['sd']/np.sqrt(scenario['n'])
    scenario['ci_high']=scenario['mean']+1.96*scenario['sd']/np.sqrt(scenario['n'])
    scenario.to_csv(TABLES/'per_scenario_comparison.csv',index=False)
    stats=d.groupby('policy')[METRICS].agg(['mean','std','median',lambda x:x.quantile(.25),lambda x:x.quantile(.75)]).stack(level=0,future_stack=True).reset_index()
    stats.columns=['policy','metric','mean','sd','median','q25','q75']; stats.to_csv(TABLES/'statistical_summary.csv',index=False)
    sens=d.groupby(['capacity','outage_min','rate','condition','policy'])[['aoi_mean','delivery_ratio','episode_preservation']].mean().reset_index()
    sens.to_csv(TABLES/'sensitivity_analysis.csv',index=False)
    config=yaml.safe_load((ROOT/'config/experiments.yaml').read_text())
    pd.DataFrame([{'parameter':k,'value':json.dumps(v)} for k,v in config.items()]).to_csv(TABLES/'experimental_configuration.csv',index=False)
    rng=np.random.default_rng(2026)
    rows=[]
    for competitor in ('P1','P2','P3'):
        a=d[d.policy=='P4'].set_index(KEY).sort_index()
        b=d[d.policy==competitor].set_index(KEY).sort_index()
        for metric in ('aoi_mean','delivery_ratio','episode_preservation','episode_delay'):
            diff=(a[metric]-b[metric]).dropna()
            if not len(diff): continue
            seed_means=diff.groupby(level='seed').mean().to_numpy()
            boot=np.mean(seed_means[rng.integers(0,len(seed_means),(2000,len(seed_means)))],axis=1)
            rows.append(dict(comparison=f'P4 - {competitor}',metric=metric,n_seed_clusters=len(seed_means),n_paired_cells=len(diff),mean_difference=seed_means.mean(),median_difference=np.median(diff),ci_low=np.quantile(boot,.025),ci_high=np.quantile(boot,.975),relative_to_competitor=seed_means.mean()/b[metric].mean() if b[metric].mean() else np.nan))
    pd.DataFrame(rows).to_csv(TABLES/'paired_differences.csv',index=False)
    scenario.to_csv(OUT/'figure_source_data.csv',index=False)
    print('analyzed',len(d),'runs; tables:',len(list(TABLES.glob('*.csv'))))

if __name__=='__main__': main()
