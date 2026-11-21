import argparse
import csv
import gzip
import itertools
import json
import sys
import time
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_generator import generate
from src.network_model import outages
from src.simulator import simulate
from src.metrics import calculate
from src.buffer_policies import POLICIES


def run(pilot=False):
    config = yaml.safe_load((ROOT/'config/experiments.yaml').read_text())
    if not config['frozen']: raise RuntimeError('Configuration not frozen')
    seeds = config['pilot_seeds'] if pilot else config['seeds']
    capacities = [120,720] if pilot else config['buffer_capacities']
    durations = [0,30,120] if pilot else config['outage_minutes']
    rates = [1,5] if pilot else config['recovery_rates_per_s']
    conditions = ['low','high'] if pilot else list(config['episode_conditions'])
    suffix = 'pilot' if pilot else 'main'
    raw = ROOT/'results/raw'; raw.mkdir(parents=True, exist_ok=True)
    path = raw/f'{suffix}_runs.csv'
    start = time.perf_counter()
    n = 0
    with path.open('w', newline='') as f:
        writer = None
        for capacity, minutes, rate, condition, seed in itertools.product(capacities, durations, rates, conditions, seeds):
            trace = outages(config['outage_start_s'], minutes*60, config['network_repeats'])
            readings = generate(config, condition, seed, config['outage_start_s'], minutes*60)
            for policy in POLICIES:
                representative = (capacity==720 and minutes==120 and rate==1 and condition=='medium' and seed==101 and policy=='P4')
                result = simulate(readings, trace, policy, capacity, rate,
                                  config['observation_s']+config['recovery_s'], config['reconnect_delay_s'], representative)
                row = dict(policy=policy, capacity=capacity, outage_min=minutes, rate=rate, condition=condition, seed=seed,
                           **calculate(result, config['episode_deadlines_s'], config['observation_s']))
                if writer is None:
                    writer=csv.DictWriter(f, fieldnames=row.keys()); writer.writeheader()
                writer.writerow(row); n+=1
                if representative:
                    with gzip.open(raw/f'{suffix}_representative_events.csv.gz','wt',newline='') as g:
                        w=csv.writer(g); w.writerow(['time_s','event','measurement_id','queue_size']); w.writerows(result.events)
                    with (raw/f'{suffix}_representative_occupancy.csv').open('w',newline='') as g:
                        w=csv.writer(g); w.writerow(['time_s','queue_size']); w.writerows(result.occupancy)
            if n % 1000 == 0: print(f'{suffix}: {n} runs', flush=True)
    runtime = time.perf_counter()-start
    (raw/f'{suffix}_manifest.json').write_text(json.dumps(dict(runs=n, runtime_s=runtime, seeds=seeds, config=str(ROOT/'config/experiments.yaml')),indent=2))
    print(f'{suffix}: {n} runs in {runtime:.1f}s')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--pilot',action='store_true'); args=parser.parse_args()
    run(args.pilot)
