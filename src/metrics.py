import math
import numpy as np


def aoi_stats(delivered, end):
    """Exact continuous-time mean and quantiles. Initial virtual update at t=0."""
    fresh, prev = 0.0, 0.0
    segments = []
    for item, t in sorted(delivered, key=lambda x: x[1]):
        if t > prev:
            segments.append((prev - fresh, t - fresh, t - prev))
        fresh = max(fresh, item.time)
        prev = t
    if end > prev:
        segments.append((prev - fresh, end - fresh, end - prev))
    if not segments:
        return dict(aoi_mean=0., aoi_median=0., aoi_p95=0., aoi_peak=0.)
    lower = np.fromiter((a for a, _, _ in segments), dtype=float)
    upper = np.fromiter((b for _, b, _ in segments), dtype=float)
    mean = sum((a + b) * d / 2 for a, b, d in segments) / end
    peak = max(b for _, b, _ in segments)
    def quantile(p):
        lo, hi = 0., peak
        for _ in range(30):
            mid = (lo + hi) / 2
            below = np.maximum(0., np.minimum(upper, mid) - lower).sum()
            if below / end < p: lo = mid
            else: hi = mid
        return hi
    return dict(aoi_mean=mean, aoi_median=quantile(.5), aoi_p95=quantile(.95), aoi_peak=peak)


def calculate(result, deadlines=(60, 300, 900), aoi_end=None):
    readings, delivered = result.readings, result.delivered
    by_id = {r.id: t for r, t in delivered}
    abnormal = [r for r in readings if r.abnormal]
    normal = [r for r in readings if not r.abnormal]
    ground_truth = getattr(readings, 'episodes', None)
    groups = {e.id: [] for e in ground_truth} if ground_truth is not None else {}
    onsets = {e.id: e.onset for e in ground_truth} if ground_truth is not None else {}
    for r in readings:
        for episode_id in (r.episode_ids or ((r.episode_id,) if r.episode_id is not None else ())):
            groups.setdefault(episode_id, []).append(r)
            onsets[episode_id] = min(onsets.get(episode_id, r.time), r.time)
    fractions, delays = [], []
    threshold_detected = 0
    for episode_id, group in groups.items():
        threshold_detected += any(r.abnormal for r in group)
        received = [by_id[r.id] for r in group if r.id in by_id]
        fractions.append(len(received) / len(group) if group else 0.)
        if received: delays.append(min(received) - onsets[episode_id])
    ratio = lambda group: sum(r.id in by_id for r in group) / len(group) if group else math.nan
    metrics = dict(generated=len(readings), delivered=len(delivered), dropped=len(result.dropped),
                   pending=len(result.pending), delivery_ratio=ratio(readings),
                   normal_delivery_ratio=ratio(normal), abnormal_delivery_ratio=ratio(abnormal),
                   episode_count=len(groups), episode_threshold_detected_count=threshold_detected,
                   episode_preservation=sum(x > 0 for x in fractions) / len(groups) if groups else math.nan,
                   episode_fraction=float(np.mean(fractions)) if fractions else math.nan,
                   episodes_complete=sum(x == 1 for x in fractions) / len(groups) if groups else math.nan,
                   episodes_lost=sum(x == 0 for x in fractions) / len(groups) if groups else math.nan,
                   episode_delay=float(np.mean(delays)) if delays else math.nan,
                   undetected_episodes=len(groups) - len(delays),
                   latency=float(np.mean([t-r.time for r,t in delivered])) if delivered else math.nan,
                   occupancy_peak=max((n for _, n in result.occupancy), default=0),
                   occupancy_mean=float(np.mean([n for _, n in result.occupancy])) if result.occupancy else 0.,
                   network_disconnect_losses=len(result.network_losses), overflow_losses=len(result.overflow_losses),
                   no_buffer_losses=len(result.no_buffer_losses), total_losses=len(result.dropped)+len(result.pending),
                   recovery_time=result.recovery_time if result.recovery_time is not None else math.nan)
    for deadline in deadlines:
        metrics[f'episode_within_{deadline}s'] = sum(d <= deadline for d in delays) / len(groups) if groups else math.nan
    horizon = result.end if aoi_end is None else aoi_end
    metrics.update(aoi_stats([(r,t) for r,t in delivered if t <= horizon], horizon))
    return metrics
