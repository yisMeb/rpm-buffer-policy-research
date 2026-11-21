"""Validate run-level conservation and complete compressed event logs."""
import csv
import gzip
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'results/raw'


def main():
    runs=pd.read_csv(raw/'main_runs.csv')
    repeated=pd.read_csv(raw/'repeated_outage_runs.csv')
    assert len(runs)==19440 and len(repeated)==960
    for data in (runs,repeated):
        assert ((data.generated-data.delivered-data.dropped-data.pending)==0).all()
    expected=iter(runs.itertuples(index=False))
    current=None; delivered=lost=checked=events=0
    with gzip.open(raw/'main_events.csv.gz','rt',newline='') as f:
        for row in csv.DictReader(f):
            key=(int(row['capacity']),int(row['outage_min']),int(row['rate']),row['condition'],int(row['seed']),row['policy'])
            if key!=current:
                if current is not None:
                    assert delivered==target.delivered and lost==target.dropped and target.pending==0, current
                    checked+=1
                target=next(expected)
                assert key==(target.capacity,target.outage_min,target.rate,target.condition,target.seed,target.policy)
                current=key; delivered=lost=0
            delivered+=row['event']=='delivered'
            lost+=row['event'] in ('dropped','evicted')
            events+=1
    assert delivered==target.delivered and lost==target.dropped and target.pending==0
    checked+=1
    assert checked==len(runs)
    assert next(expected,None) is None
    print(f'validated {checked} main runs, {len(repeated)} repeated runs, {events} events')

if __name__=='__main__': main()
