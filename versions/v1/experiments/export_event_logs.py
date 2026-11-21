"""Export auditable event logs for a fixed paired representative scenario."""
import csv
import gzip
import sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data_generator import generate
from src.network_model import outages
from src.simulator import simulate
from src.buffer_policies import POLICIES


def main():
    c=yaml.safe_load((ROOT/'config/experiments.yaml').read_text())
    readings=generate(c,'medium',101,c['outage_start_s'],7200)
    trace=outages(c['outage_start_s'],7200,1)
    raw=ROOT/'results/raw'; raw.mkdir(parents=True,exist_ok=True)
    for p in POLICIES:
        r=simulate(readings,trace,p,720,1,c['observation_s']+c['recovery_s'],c['reconnect_delay_s'],True)
        with gzip.open(raw/f'representative_{p}_events.csv.gz','wt',newline='') as f:
            w=csv.writer(f);w.writerow(['time_s','event','measurement_id','queue_size']);w.writerows(r.events)
        with (raw/f'representative_{p}_outcomes.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['measurement_id','acquisition_s','abnormal','episode_id','outcome','delivery_s'])
            delivered={x.id:t for x,t in r.delivered}
            pending={x.id for x in r.pending}
            for x in readings:
                state='delivered' if x.id in delivered else 'pending' if x.id in pending else 'dropped'
                w.writerow([x.id,x.time,x.abnormal,x.episode_id,state,delivered.get(x.id,'')])
    print('exported paired representative event and outcome logs')

if __name__=='__main__':main()
