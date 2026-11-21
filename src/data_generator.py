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
    episode_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class Episode:
    id: int
    onset: float
    end: float
    severity: int


class SyntheticReadings(list):
    def __init__(self, readings, episodes):
        super().__init__(readings)
        self.episodes = episodes


def generate(config, condition, seed, outage_start, outage_duration, episode_model='poisson_uniform'):
    """Synthetic inputs; episode placement is sampled independently of outage position."""
    rng = np.random.default_rng(seed + {'low': 0, 'medium': 10000, 'high': 20000}[condition])
    end = config['observation_s']
    spec = config['episode_conditions'][condition]
    expected = spec['episodes_per_hour'] * end / 3600
    if episode_model == 'poisson_uniform':
        count = rng.poisson(expected)
    elif episode_model in ('fixed_uniform', 'clustered_long'):
        count = max(1, round(expected))
    else:
        raise ValueError(episode_model)
    episodes = []
    for i in range(count):
        start = float(rng.uniform(0, end - 1) if episode_model != 'clustered_long' else rng.beta(2,2)*(end-1))
        duration = float(rng.uniform(*spec['duration_s'])) * (2 if episode_model == 'clustered_long' else 1)
        episodes.append(Episode(i + 1, start, min(end, start + duration), int(rng.integers(0, 3))))
    episodes.sort(key=lambda e:e.onset)
    readings = []
    for i, t in enumerate(range(0, end, config['reporting_interval_s'])):
        active = [e for e in episodes if e.onset <= t < e.end]
        hr = 72 + 5 * np.sin(t / 240) + rng.normal(0, 2)
        spo2 = 97 + .7 * np.sin(t / 310) + rng.normal(0, .4)
        temp = 36.7 + .2 * np.sin(t / 480) + rng.normal(0, .08)
        for episode in active:
            if episode.severity == 0: hr += 37
            elif episode.severity == 1: spo2 -= 8
            else: temp += 2.2
        abnormal = hr > 100 or hr < 50 or spo2 < 92 or temp > 38
        ids = tuple(e.id for e in active)
        readings.append(Measurement(i, config['patient_id'], float(t), float(hr), float(spo2), float(temp), bool(abnormal), ids[0] if ids else None, ids))
    return SyntheticReadings(readings, episodes)
