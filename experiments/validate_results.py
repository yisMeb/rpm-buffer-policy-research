"""Validate run-level conservation and complete compressed event logs."""
import csv
import gzip
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'versions/v2/results/raw'


def main():
    runs=pd.read_csv(raw/'main_runs.csv')
    repeated=pd.read_csv(raw/'repeated_outage_runs.csv')
    sensitivity=pd.read_csv(raw/'episode_sensitivity_runs.csv')
    assert len(runs)==19440 and len(repeated)==960 and len(sensitivity)==1920
    for data in (runs,repeated,sensitivity):
        assert ((data.generated-data.delivered-data.dropped-data.pending)==0).all()
        assert (data.network_disconnect_losses+data.overflow_losses+data.no_buffer_losses==data.dropped).all()
    truth=pd.read_csv(raw/'generated_episodes.csv')
    counts=truth.groupby(['condition','seed']).size().rename('truth_count')
    aligned=runs.join(counts,on=['condition','seed'])
    assert (aligned.episode_count==aligned.truth_count.fillna(0)).all()
    expected=iter(runs.itertuples(index=False))
    current=None; delivered=lost=network=overflow=no_buffer=checked=events=0
    with gzip.open(raw/'main_events.csv.gz','rt',newline='') as f:
        for row in csv.DictReader(f):
            key=(int(row['capacity']),int(row['outage_min']),int(row['rate']),row['condition'],int(row['seed']),row['policy'])
            if key!=current:
                if current is not None:
                    assert (delivered==target.delivered and lost==target.dropped and
                            network==target.network_disconnect_losses and overflow==target.overflow_losses and
                            no_buffer==target.no_buffer_losses and target.pending==0), current
                    checked+=1
                target=next(expected)
                assert key==(target.capacity,target.outage_min,target.rate,target.condition,target.seed,target.policy)
                current=key; delivered=lost=network=overflow=no_buffer=0
            delivered+=row['event']=='delivered'
            lost+=row['event'] in ('network_drop','overflow_drop','overflow_evicted','no_buffer_drop')
            network+=row['event']=='network_drop'
            overflow+=row['event'] in ('overflow_drop','overflow_evicted')
            no_buffer+=row['event']=='no_buffer_drop'
            events+=1
    assert (delivered==target.delivered and lost==target.dropped and
            network==target.network_disconnect_losses and overflow==target.overflow_losses and
            no_buffer==target.no_buffer_losses and target.pending==0)
    checked+=1
    assert checked==len(runs)
    assert next(expected,None) is None
    print(f'validated {checked} main runs, {len(repeated)} repeated runs, {len(sensitivity)} episode-sensitivity runs, {events} events')

if __name__=='__main__': main()
