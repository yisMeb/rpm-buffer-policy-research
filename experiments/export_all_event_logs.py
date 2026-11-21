"""Re-run the frozen main design and export every simulated delivery/loss event."""
import csv
import gzip
import itertools
import sys
import time
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data_generator import generate
from src.network_model import outages
from src.simulator import simulate
from src.buffer_policies import POLICIES


def main():
    c=yaml.safe_load((ROOT/'config/experiments_v2.yaml').read_text())
    if not c['frozen']:raise RuntimeError('Configuration not frozen')
    path=ROOT/'versions/v2/results/raw/main_events.csv.gz'
    path.parent.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter(); n=0
    with gzip.open(path,'wt',newline='',compresslevel=3) as f:
        w=csv.writer(f)
        w.writerow(['capacity','outage_min','rate','condition','seed','policy','time_s','event','measurement_id','queue_size'])
        for capacity,minutes,rate,condition,seed in itertools.product(c['buffer_capacities'],c['outage_minutes'],c['recovery_rates_per_s'],c['episode_conditions'],c['seeds']):
            readings=generate(c,condition,seed,c['outage_start_s'],minutes*60)
            trace=outages(c['outage_start_s'],minutes*60,c['network_repeats'])
            for policy in POLICIES:
                r=simulate(readings,trace,policy,capacity,rate,c['observation_s']+c['recovery_s'],c['reconnect_delay_s'],True)
                prefix=(capacity,minutes,rate,condition,seed,policy)
                w.writerows((*prefix,*event) for event in r.events)
                n+=1
            if n%2000==0:print(f'event logs: {n} runs',flush=True)
    print(f'event logs: {n} runs in {time.perf_counter()-start:.1f}s')

if __name__=='__main__':main()
