from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Measurement:
    id: int
    patient_id: str
    time: float
    heart_rate: float
    spo2: float
    temperature: float
    abnormal: bool
    episode_id: int | None


def generate(config, condition, seed, outage_start, outage_duration):
    """Synthetic inputs; episode placement is sampled independently of outage position."""
    rng = np.random.default_rng(seed + {'low': 0, 'medium': 10000, 'high': 20000}[condition])
    end = config['observation_s']
    spec = config['episode_conditions'][condition]
    count = rng.poisson(spec['episodes_per_hour'] * end / 3600)
    episodes = []
    for i in range(count):
        start = float(rng.uniform(0, end - 1))
        duration = float(rng.uniform(*spec['duration_s']))
        episodes.append((start, min(end, start + duration), i + 1, int(rng.integers(0, 3))))
    episodes.sort()
    readings = []
    for i, t in enumerate(range(0, end, config['reporting_interval_s'])):
        active = next((e for e in episodes if e[0] <= t < e[1]), None)
        hr = 72 + 5 * np.sin(t / 240) + rng.normal(0, 2)
        spo2 = 97 + .7 * np.sin(t / 310) + rng.normal(0, .4)
        temp = 36.7 + .2 * np.sin(t / 480) + rng.normal(0, .08)
        if active:
            severity = active[3]
            if severity == 0: hr += 37 + 10 * severity
            elif severity == 1: spo2 -= 8
            else: temp += 2.2
        abnormal = hr > 100 or hr < 50 or spo2 < 92 or temp > 38
        readings.append(Measurement(i, config['patient_id'], float(t), float(hr), float(spo2), float(temp), bool(abnormal), active[2] if active and abnormal else None))
    return readings
