"""Export every generated Version 2 episode, including unsampled episodes."""
import csv
import sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data_generator import generate


def main():
    c=yaml.safe_load((ROOT/'config/experiments_v2.yaml').read_text())
    raw=ROOT/'versions/v2/results/raw'; raw.mkdir(parents=True,exist_ok=True)
    with (raw/'generated_episodes.csv').open('w',newline='') as f:
        w=csv.writer(f)
        w.writerow(['condition','seed','episode_id','onset_s','end_s','severity','sampled_measurements','threshold_abnormal_measurements'])
        for condition in c['episode_conditions']:
            for seed in c['seeds']:
                readings=generate(c,condition,seed,c['outage_start_s'],0)
                for e in readings.episodes:
                    members=[r for r in readings if e.id in r.episode_ids]
                    w.writerow([condition,seed,e.id,e.onset,e.end,e.severity,len(members),sum(r.abnormal for r in members)])
    print('exported Version 2 episode ground truth')

if __name__=='__main__':main()
